"""
Security routes — device trust management and IP/device login signals.

Endpoints:
  POST /api/demo-login          — authenticate demo account, check device trust
  GET  /api/device-status/<u>  — return device trust state for a username
    POST /api/verify-device       — token verification → mark device trusted
"""

import hashlib
import secrets
import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from database import query_db, execute_db
from email_utils import send_device_verification_email

security_bp = Blueprint('security_bp', __name__)
VERIFICATION_TOKEN_MINUTES = 15


def _get_client_ip(req) -> str:
    """Extracts real client IP, handling common proxy headers."""
    forwarded = req.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return req.remote_addr or "unknown"


def _get_device_fingerprint(req) -> str:
    """
    Creates a device fingerprint from User-Agent + /24 IP subnet.
    NOT using exact IP so multiple NAT'd users share same subnet without
    being treated as identical individuals.
    """
    user_agent = req.headers.get("User-Agent", "unknown")
    ip = _get_client_ip(req)
    # /24 subnet: first 3 octets only (e.g., 192.168.1.x → 192.168.1)
    subnet = ".".join(ip.split(".")[:3]) if "." in ip else ip
    raw = f"{user_agent}|{subnet}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@security_bp.route('/api/demo-login', methods=['POST'])
def demo_login():
    """
    Authenticates a demo profile account.
    Records login in login_history.
    Checks if device is trusted — if new, sends verification email.
    """
    data = request.get_json() or {}
    username = data.get("username", "").strip().lstrip("@")
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required."}), 400

    # Fetch profile
    profile = query_db(
        "SELECT * FROM demo_profiles WHERE LOWER(username) = LOWER(?)",
        (username,), one=True
    )
    if not profile:
        return jsonify({"status": "error", "message": f"Account '@{username}' not found."}), 404

    if not profile.get("password"):
        return jsonify({"status": "error", "message": "This account has no password set (seed data). Use social create-account."}), 400

    if not check_password_hash(profile["password"], password):
        return jsonify({"status": "error", "message": "Incorrect password."}), 401

    registration = query_db(
        "SELECT email FROM registered_profiles WHERE LOWER(username) = LOWER(?)",
        (username,), one=True
    )
    if not registration:
        registration = query_db(
            "SELECT email FROM protected_profiles WHERE LOWER(username) = LOWER(?)",
            (username,), one=True
        )
    registered_email = registration.get("email") if registration else None

    ip_address = _get_client_ip(request)
    device_fingerprint = _get_device_fingerprint(request)
    user_agent = request.headers.get("User-Agent", "unknown")[:500]

    # Check if this device is already trusted for this user
    existing_device = query_db(
        "SELECT * FROM trusted_devices WHERE username = ? AND device_fingerprint = ?",
        (username, device_fingerprint), one=True
    )

    device_trust_status = "unknown"

    def request_device_verification(existing_login_id=None):
        verification_token = secrets.token_urlsafe(32)
        verification_expires_at = datetime.utcnow() + timedelta(minutes=VERIFICATION_TOKEN_MINUTES)

        if existing_login_id:
            execute_db("""
                UPDATE login_history
                SET account_id = ?, username = ?, registered_email = ?, ip_address = ?,
                    device_fingerprint = ?, user_agent = ?, login_at = CURRENT_TIMESTAMP,
                    verification_token = ?, verification_expires_at = ?, verified = 0,
                    verification_required = 1, verified_at = NULL
                WHERE id = ?
            """, (profile["id"], username, registered_email, ip_address, device_fingerprint,
                  user_agent, verification_token, verification_expires_at, existing_login_id))
        else:
            execute_db("""
                INSERT INTO login_history
                    (account_id, username, registered_email, ip_address, device_fingerprint, user_agent,
                     verification_required, verification_token, verification_expires_at, verified)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, 0)
            """, (profile["id"], username, registered_email, ip_address, device_fingerprint,
                  user_agent, verification_token, verification_expires_at))

        email_result = {"status": "no_registered_email"}
        if registered_email:
            verify_url = f"http://localhost:5000/api/verify-device?token={verification_token}"
            email_result = send_device_verification_email(
                recipient=registered_email,
                username=username,
                verify_link=verify_url,
                ip_address=ip_address,
                user_agent=user_agent
            )

        if email_result.get("sent"):
            message = "New device detected. A verification email was sent to your registered email."
        elif email_result.get("status") == "not_configured":
            message = "New device detected. Email delivery is not configured; verification is required."
        else:
            message = "New device detected. Verification is required before this device can be trusted."

        return jsonify({
            "status": "verification_required",
            "message": message,
            "account_id": profile["id"],
            "username": username,
            "device_trust_status": "new_device_verification_required",
            "verification_required": True,
            "email_result": email_result,
        }), 202

    if existing_device and existing_device["is_trusted"]:
        device_trust_status = "trusted"
        execute_db(
            "UPDATE trusted_devices SET last_seen = CURRENT_TIMESTAMP WHERE id = ?",
            (existing_device["id"],)
        )
    elif existing_device:
        pending_login = query_db("""
            SELECT id FROM login_history
            WHERE username = ? AND device_fingerprint = ?
              AND verification_required = 1 AND verified = 0
              AND verification_expires_at > CURRENT_TIMESTAMP
            ORDER BY login_at DESC LIMIT 1
        """, (username, device_fingerprint), one=True)
        if pending_login:
            return jsonify({
                "status": "verification_required",
                "message": "New device detected. Complete the verification email before logging in.",
                "account_id": profile["id"],
                "username": username,
                "device_trust_status": "pending_verification",
                "verification_required": True,
                "email_result": {"status": "already_sent"},
            }), 202

        expired_login = query_db("""
            SELECT id FROM login_history
            WHERE username = ? AND device_fingerprint = ?
              AND verification_required = 1 AND verified = 0
            ORDER BY login_at DESC LIMIT 1
        """, (username, device_fingerprint), one=True)
        return request_device_verification(expired_login["id"] if expired_login else None)
    else:
        prior_devices = query_db(
            "SELECT COUNT(*) as cnt FROM trusted_devices WHERE username = ?",
            (username,), one=True
        )
        if prior_devices["cnt"] == 0:
            execute_db("""
                INSERT OR IGNORE INTO trusted_devices
                    (account_id, username, device_fingerprint, user_agent, ip_address, is_trusted)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (profile["id"], username, device_fingerprint, user_agent, ip_address))
            execute_db("""
                UPDATE trusted_devices SET account_id = ?, last_seen = CURRENT_TIMESTAMP, is_trusted = 1
                WHERE username = ? AND device_fingerprint = ?
            """, (profile["id"], username, device_fingerprint))
            device_trust_status = "trusted_first_device"
        else:
            execute_db("""
                INSERT OR IGNORE INTO trusted_devices
                    (account_id, username, device_fingerprint, user_agent, ip_address, is_trusted)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (profile["id"], username, device_fingerprint, user_agent, ip_address))
            return request_device_verification()

    # Record successful trusted login
    execute_db("""
        INSERT INTO login_history
            (account_id, username, registered_email, ip_address, device_fingerprint, user_agent,
             verification_required, verified)
        VALUES (?, ?, ?, ?, ?, ?, 0, 1)
    """, (profile["id"], username, registered_email, ip_address, device_fingerprint, user_agent))

    return jsonify({
        "status": "success",
        "message": "Login successful.",
        "account_id": profile["id"],
        "username": username,
        "registered_email": registered_email,
        "device_trust_status": device_trust_status,
        "verification_required": False,
        "profile": {
            "id": profile["id"],
            "username": profile["username"],
            "display_name": profile["display_name"],
            "bio": profile["bio"],
            "avatar_url": profile["avatar_url"],
            "followers_count": profile["followers_count"],
            "following_count": profile["following_count"],
            "posts_count": profile["posts_count"],
            "account_age_days": profile["account_age_days"],
            "is_verified": profile["is_verified"],
        }
    })


@security_bp.route('/api/verify-device', methods=['GET', 'POST'])
def verify_device():
    """
    Verifies a device via token from email link.
    GET  → browser-friendly (from email link click)
    POST → JSON payload { "token": "..." }
    """
    if request.method == "GET":
        token = request.args.get("token", "").strip()
    else:
        data = request.get_json() or {}
        token = data.get("token", "").strip()

    if not token:
        return jsonify({"status": "error", "message": "Verification token is required."}), 400

    # Find pending login history record
    login_record = query_db("""
        SELECT * FROM login_history
        WHERE verification_token = ? AND verified = 0
          AND verification_expires_at > CURRENT_TIMESTAMP
        ORDER BY login_at DESC LIMIT 1
    """, (token,), one=True)

    if not login_record:
        return jsonify({"status": "error", "message": "Invalid or expired verification token."}), 400

    # Mark as verified
    execute_db(
        "UPDATE login_history SET verified = 1, verified_at = CURRENT_TIMESTAMP WHERE id = ?",
        (login_record["id"],)
    )

    # Mark device as trusted
    execute_db("""
        UPDATE trusted_devices SET account_id = ?, is_trusted = 1, last_seen = CURRENT_TIMESTAMP
        WHERE username = ? AND device_fingerprint = ?
    """, (login_record["account_id"], login_record["username"], login_record["device_fingerprint"]))

    username = login_record["username"]

    if request.method == "GET":
        # Browser-friendly HTML response for email link click
        return f"""<!DOCTYPE html>
<html>
<head><title>Device Verified</title>
<style>body{{font-family:sans-serif;text-align:center;padding:60px;background:#0f172a;color:#e2e8f0}}
h1{{color:#22d3ee}}p{{color:#94a3b8}}a{{color:#22d3ee}}</style></head>
<body>
<h1>✓ Device Verified Successfully</h1>
<p>Your device has been successfully verified and trusted for account <strong>@{username}</strong>.</p>
<p>You can now close this tab and log in normally.</p>
</body></html>""", 200

    return jsonify({
        "status": "success",
        "message": f"Device verified successfully. This device is now trusted for @{username}.",
        "username": username
    })


@security_bp.route('/api/device-status/<username>', methods=['GET'])
def get_device_status(username):
    """Returns the device trust state for a given username from the current request."""
    device_fingerprint = _get_device_fingerprint(request)
    device = query_db(
        "SELECT * FROM trusted_devices WHERE username = ? AND device_fingerprint = ?",
        (username, device_fingerprint), one=True
    )

    all_devices = query_db(
        "SELECT id, device_fingerprint, ip_address, first_seen, last_seen, is_trusted FROM trusted_devices WHERE username = ?",
        (username,)
    )

    return jsonify({
        "status": "success",
        "username": username,
        "current_device_trusted": bool(device and device["is_trusted"]),
        "device_fingerprint": device_fingerprint,
        "all_devices": all_devices or []
    })


@security_bp.route('/api/login-history/<username>', methods=['GET'])
def get_login_history(username):
    """Returns login history for a username (for admin/demo purposes)."""
    limit = int(request.args.get("limit", 20))
    history = query_db("""
        SELECT id, account_id, username, registered_email, ip_address,
               device_fingerprint, user_agent, login_at,
               verification_required, verified
        FROM login_history
        WHERE username = ?
        ORDER BY login_at DESC
        LIMIT ?
    """, (username, limit))
    return jsonify({
        "status": "success",
        "username": username,
        "history": history or []
    })
