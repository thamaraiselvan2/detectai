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
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from database import query_db, execute_db
from email_utils import send_device_verification_email

security_bp = Blueprint('security_bp', __name__)


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

    ip_address = _get_client_ip(request)
    device_fingerprint = _get_device_fingerprint(request)
    user_agent = request.headers.get("User-Agent", "unknown")[:500]

    # Check if this device is already trusted for this user
    existing_device = query_db(
        "SELECT * FROM trusted_devices WHERE username = ? AND device_fingerprint = ?",
        (username, device_fingerprint), one=True
    )

    device_trust_status = "unknown"
    verification_required = False
    verification_token = None

    if existing_device:
        if existing_device["is_trusted"]:
            device_trust_status = "trusted"
            # Update last_seen
            execute_db(
                "UPDATE trusted_devices SET last_seen = CURRENT_TIMESTAMP WHERE id = ?",
                (existing_device["id"],)
            )
        else:
            device_trust_status = "pending_verification"
            verification_required = True
    else:
        # New device — determine if this is the user's first ever device
        prior_devices = query_db(
            "SELECT COUNT(*) as cnt FROM trusted_devices WHERE username = ?",
            (username,), one=True
        )
        is_first_device = prior_devices["cnt"] == 0

        if is_first_device:
            # Auto-trust first device (registration device)
            execute_db("""
                INSERT OR IGNORE INTO trusted_devices 
                    (username, device_fingerprint, user_agent, ip_address, is_trusted)
                VALUES (?, ?, ?, ?, 1)
            """, (username, device_fingerprint, user_agent, ip_address))
            execute_db("""
                UPDATE trusted_devices SET last_seen = CURRENT_TIMESTAMP, is_trusted = 1
                WHERE username = ? AND device_fingerprint = ?
            """, (username, device_fingerprint))
            device_trust_status = "trusted_first_device"
        else:
            # New secondary device — require email verification
            verification_token = secrets.token_urlsafe(32)
            execute_db("""
                INSERT OR IGNORE INTO trusted_devices
                    (username, device_fingerprint, user_agent, ip_address, is_trusted)
                VALUES (?, ?, ?, ?, 0)
            """, (username, device_fingerprint, user_agent, ip_address))
            device_trust_status = "new_device_verification_required"
            verification_required = True

            # Record with token in login_history
            execute_db("""
                INSERT INTO login_history
                    (username, ip_address, device_fingerprint, user_agent,
                     verification_required, verification_token, verified)
                VALUES (?, ?, ?, ?, 1, ?, 0)
            """, (username, ip_address, device_fingerprint, user_agent, verification_token))

            # Send verification email if the registered profile has an email
            registered = query_db(
                "SELECT email FROM registered_profiles WHERE LOWER(username) = LOWER(?)",
                (username,), one=True
            )
            email_result = {"status": "no_registered_email"}
            if registered and registered.get("email"):
                verify_url = f"http://localhost:5000/api/verify-device?token={verification_token}&username={username}"
                email_result = send_device_verification_email(
                    recipient=registered["email"],
                    username=username,
                    verify_link=verify_url,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            return jsonify({
                "status": "verification_required",
                "message": "New device detected. A verification email has been sent to your registered address.",
                "username": username,
                "device_trust_status": device_trust_status,
                "verification_required": True,
                "email_result": email_result,
                # For demo purposes — expose token so tester can verify without email
                "demo_verify_token": verification_token,
            }), 202

    # Record successful trusted login
    execute_db("""
        INSERT INTO login_history
            (username, ip_address, device_fingerprint, user_agent,
             verification_required, verified)
        VALUES (?, ?, ?, ?, 0, 1)
    """, (username, ip_address, device_fingerprint, user_agent))

    return jsonify({
        "status": "success",
        "message": "Login successful.",
        "username": username,
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
    POST → JSON payload { "token": "...", "username": "..." }
    """
    if request.method == "GET":
        token = request.args.get("token", "").strip()
        username = request.args.get("username", "").strip()
    else:
        data = request.get_json() or {}
        token = data.get("token", "").strip()
        username = data.get("username", "").strip()

    if not token or not username:
        return jsonify({"status": "error", "message": "Token and username are required."}), 400

    # Find pending login history record
    login_record = query_db("""
        SELECT * FROM login_history
        WHERE username = ? AND verification_token = ? AND verified = 0
        ORDER BY login_at DESC LIMIT 1
    """, (username, token), one=True)

    if not login_record:
        return jsonify({"status": "error", "message": "Invalid or expired verification token."}), 400

    # Mark as verified
    execute_db(
        "UPDATE login_history SET verified = 1, verified_at = CURRENT_TIMESTAMP WHERE id = ?",
        (login_record["id"],)
    )

    # Mark device as trusted
    execute_db("""
        UPDATE trusted_devices SET is_trusted = 1, last_seen = CURRENT_TIMESTAMP
        WHERE username = ? AND device_fingerprint = ?
    """, (username, login_record["device_fingerprint"]))

    if request.method == "GET":
        # Browser-friendly HTML response for email link click
        return f"""<!DOCTYPE html>
<html>
<head><title>Device Verified</title>
<style>body{{font-family:sans-serif;text-align:center;padding:60px;background:#0f172a;color:#e2e8f0}}
h1{{color:#22d3ee}}p{{color:#94a3b8}}a{{color:#22d3ee}}</style></head>
<body>
<h1>✓ Device Verified</h1>
<p>Your device has been successfully verified and trusted for account <strong>@{username}</strong>.</p>
<p>You can now close this tab and log in normally.</p>
</body></html>""", 200

    return jsonify({
        "status": "success",
        "message": f"Device successfully verified and trusted for @{username}.",
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
        SELECT id, ip_address, user_agent, login_at, verification_required, verified
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
