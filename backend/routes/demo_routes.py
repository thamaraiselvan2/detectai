import os
import uuid
import base64
import json
from flask import Blueprint, request, jsonify, current_app, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from database import query_db, execute_db
from risk_engine.scoring import analyze_profile_risk, detect_registered_impersonation
from email_utils import send_impersonation_email
from config import MONITORING_ALERT_THRESHOLD

demo_bp = Blueprint('demo_bp', __name__)


def mask_email(email):
    """Masks the local part of an email address for safe application logs."""
    if not email or "@" not in email:
        return "<invalid or empty>"
    local, domain = email.split("@", 1)
    visible = local[:2] if len(local) > 2 else local[:1]
    return visible + ("*" * max(2, len(local) - len(visible))) + "@" + domain

@demo_bp.route('/api/social/create-account', methods=['POST'])
def create_social_account():
    """
    Creates a new demo social media account for the Demo Social Network.
    Accepts multipart/form-data or JSON with profile_picture, username, password, bio.
    Hashes the password and stores the avatar image in local static uploads directory.
    Saves to the same demo_profiles table.
    """
    print("=== DEMO SOCIAL CREATE ACCOUNT REQUEST RECEIVED ===", flush=True)
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    # Determine if request is multipart/form-data or json
    if request.is_json:
        data = request.get_json() or {}
        username = data.get("username", "").strip().lstrip('@')
        password = data.get("password", "").strip()
        bio = data.get("bio", "").strip()
        pic_data = data.get("profile_picture") or data.get("profile_image") or ""
        pic_file = None
    else:
        username = request.form.get("username", "").strip().lstrip('@')
        password = request.form.get("password", "").strip()
        bio = request.form.get("bio", "").strip()
        pic_file = request.files.get("profile_picture") or request.files.get("profile_image") or request.files.get("avatar")
        pic_data = ""

    print({
        "username": username,
        "email_exists": bool(request.form.get("email") or data.get("email") if request.is_json else request.form.get("email")),
        "bio_exists": bool(bio)
    }, flush=True)
    current_app.logger.info("Demo Social account creation request received for @%s", username or "<empty>")

    # 1. Validation
    if not pic_file and not pic_data:
        return jsonify({"status": "error", "message": "Profile picture is required."}), 400

    if not username:
        return jsonify({"status": "error", "message": "Username is required."}), 400

    if not password:
        return jsonify({"status": "error", "message": "Password is required."}), 400

    if not bio:
        return jsonify({"status": "error", "message": "Bio is required."}), 400

    # Check username uniqueness in demo_profiles
    existing = query_db("SELECT id FROM demo_profiles WHERE LOWER(username) = LOWER(?)", (username,), one=True)
    if existing:
        return jsonify({"status": "error", "message": f"Username '@{username}' is already used. Please choose another username."}), 409

    # 2. Process and save profile image
    avatar_url = ""
    try:
        if pic_file and pic_file.filename:
            orig_filename = secure_filename(pic_file.filename)
            ext = os.path.splitext(orig_filename)[1].lower()
            if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                ext = '.png'
            unique_name = f"avatar_{uuid.uuid4().hex[:12]}{ext}"
            filepath = os.path.join(upload_dir, unique_name)
            pic_file.save(filepath)
            avatar_url = f"/static/uploads/{unique_name}"
        elif pic_data:
            # Handle base64 data URI
            if "base64," in pic_data:
                header, base64_str = pic_data.split("base64,", 1)
                ext = ".png"
                if "jpeg" in header or "jpg" in header:
                    ext = ".jpg"
                elif "gif" in header:
                    ext = ".gif"
                elif "webp" in header:
                    ext = ".webp"
                unique_name = f"avatar_{uuid.uuid4().hex[:12]}{ext}"
                filepath = os.path.join(upload_dir, unique_name)
                with open(filepath, "wb") as fh:
                    fh.write(base64.b64decode(base64_str))
                avatar_url = f"/static/uploads/{unique_name}"
            else:
                avatar_url = pic_data
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to process profile picture: {str(e)}"}), 500

    # 3. Hash password securely
    hashed_password = generate_password_hash(password)

    # 4. Insert into same demo_profiles table
    profile_id, _ = execute_db("""
        INSERT INTO demo_profiles (username, display_name, password, bio, avatar_url, followers_count, following_count, posts_count, account_age_days, is_verified)
        VALUES (?, ?, ?, ?, ?, 0, 0, 0, 1, 0)
    """, (username, username, hashed_password, bio, avatar_url))

    created_at = query_db("SELECT created_at FROM demo_profiles WHERE id = ?", (profile_id,), one=True)["created_at"]
    new_profile = {
        "id": profile_id,
        "username": username,
        "display_name": username,
        "bio": bio,
        "avatar_url": avatar_url,
        "followers_count": 0,
        "following_count": 0,
        "posts_count": 0,
        "account_age_days": 1,
        "is_verified": 0,
        "created_at": created_at
    }

    registered_profiles = query_db("""
        SELECT r.id, r.username, r.email, r.original_profile_id, r.registered_at,
               d.display_name, d.bio, d.avatar_url, d.followers_count,
               d.following_count, d.posts_count, d.account_age_days,
               d.created_at, d.is_verified
        FROM registered_profiles r
        JOIN demo_profiles d ON d.id = r.original_profile_id
    """)
    monitoring_detection = detect_registered_impersonation(new_profile, registered_profiles)
    current_app.logger.info(
        "Impersonation detection for @%s: detected=%s protected=%s risk_score=%s",
        username,
        monitoring_detection.get("detected", False),
        monitoring_detection.get("protected_username", "<none>"),
        monitoring_detection.get("risk_score", 0)
    )
    email_delivery = {"attempted": False, "sent": False, "status": "not_detected"}
    if monitoring_detection.get("detected"):
        matched_registered = next(
            (profile for profile in registered_profiles
             if profile.get("username", "").lower() == monitoring_detection["protected_username"].lower()),
            None
        )
        registered_id = matched_registered.get("id") if matched_registered else None
        if registered_id:
            current_app.logger.info(
                "Confirmed impersonation matched registered profile @%s; recipient=%s",
                matched_registered.get("username"),
                mask_email(matched_registered.get("email"))
            )
            existing_alert = query_db(
                "SELECT id, email_status FROM impersonation_alerts WHERE registered_profile_id = ? AND demo_profile_id = ?",
                (registered_id, profile_id),
                one=True
            )
            if existing_alert:
                email_delivery = {"attempted": False, "sent": existing_alert["email_status"] == "SENT", "status": "duplicate"}
                current_app.logger.info("Duplicate impersonation alert skipped for alert %s", existing_alert["id"])
            else:
                alert_id, _ = execute_db("""
                    INSERT INTO impersonation_alerts
                        (registered_profile_id, demo_profile_id, risk_score, classification, reasons_json)
                    VALUES (?, ?, ?, ?, ?)
                """, (registered_id, profile_id, monitoring_detection["risk_score"], monitoring_detection["classification"], json.dumps(monitoring_detection["reasons"])))
                current_app.logger.info("Impersonation alert %s created for demo profile @%s", alert_id, username)
                email_delivery = {"attempted": True, "sent": False, "status": "pending"}
                print("=== IMPERSONATION EMAIL FUNCTION CALLED ===", flush=True)
                delivery = send_impersonation_email(
                    matched_registered.get("email"),
                    monitoring_detection["protected_username"],
                    monitoring_detection["new_username"],
                    monitoring_detection["risk_score"],
                    monitoring_detection["reasons"]
                )
                print(f"=== EMAIL RESULT: {delivery.get('status', 'unknown')} ===", flush=True)
                email_delivery.update({"sent": delivery["sent"], "status": delivery["status"]})
                execute_db(
                    "UPDATE impersonation_alerts SET email_status = ?, emailed_at = CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE NULL END WHERE id = ?",
                    ("SENT" if delivery["sent"] else "FAILED", 1 if delivery["sent"] else 0, alert_id)
                )
                if not delivery["sent"]:
                    current_app.logger.error(
                        "SMTP EMAIL FAILED alert_id=%s exception_type=%s exception_message=%s recipient=%s",
                        alert_id,
                        delivery.get("exception_type", "EmailDeliveryError"),
                        delivery.get("message", delivery["status"]),
                        mask_email(matched_registered.get("email"))
                    )
                else:
                    current_app.logger.info("Impersonation email accepted by SMTP for alert %s", alert_id)
        else:
            current_app.logger.error("Detection matched @%s but no registered recipient record was found", monitoring_detection.get("protected_username", "<unknown>"))

    return jsonify({
        "status": "success",
        "message": "Account Created Successfully",
        "sub_message": "Your demo profile has been added to the social network.",
        "profile": new_profile,
        "monitoring_detection": monitoring_detection,
        "email_delivery": email_delivery
    }), 201

@demo_bp.route('/api/demo-profiles', methods=['GET'])
def get_demo_profiles():
    """Lists profiles in the demo social network sandbox."""
    search = request.args.get("search", "").strip()
    if search:
        profiles = query_db("""
            SELECT * FROM demo_profiles
            WHERE LOWER(username) LIKE LOWER(?) OR LOWER(display_name) LIKE LOWER(?)
            ORDER BY created_at DESC
        """, (f"%{search}%", f"%{search}%"))
    else:
        profiles = query_db("SELECT * FROM demo_profiles ORDER BY created_at DESC")

    return jsonify({
        "status": "success",
        "profiles": profiles
    })

@demo_bp.route('/api/demo-profiles', methods=['POST'])
def create_demo_profile():
    """
    Creates a new profile in the demo sandbox network.
    Automatically analyzes the newly created profile against all monitored accounts
    and generates an alert if it impersonates any protected user!
    """
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    display_name = data.get("display_name", "").strip()

    if not username or not display_name:
        return jsonify({"status": "error", "message": "Username and display name are required."}), 400

    # Ensure uniqueness in demo profiles
    existing = query_db("SELECT id FROM demo_profiles WHERE LOWER(username) = LOWER(?)", (username,), one=True)
    if existing:
        return jsonify({"status": "error", "message": f"Demo handle '@{username}' is already taken in sandbox."}), 409

    bio = data.get("bio", "").strip()
    avatar_url = data.get("avatar_url", "").strip()
    followers_count = int(data.get("followers_count") or 0)
    following_count = int(data.get("following_count") or 0)
    posts_count = int(data.get("posts_count") or 0)
    account_age_days = int(data.get("account_age_days") or 1)
    is_verified = 1 if data.get("is_verified", False) else 0

    profile_id, _ = execute_db("""
        INSERT INTO demo_profiles (username, display_name, bio, avatar_url, followers_count, following_count, posts_count, account_age_days, is_verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, display_name, bio, avatar_url, followers_count, following_count, posts_count, account_age_days, is_verified))

    new_profile = {
        "id": profile_id,
        "username": username,
        "display_name": display_name,
        "bio": bio,
        "avatar_url": avatar_url,
        "followers_count": followers_count,
        "following_count": following_count,
        "posts_count": posts_count,
        "account_age_days": account_age_days,
        "is_verified": is_verified
    }

    # Auto-Surveillance check against monitored protected users
    monitored_users = query_db("SELECT * FROM protected_profiles WHERE is_monitoring_active = 1")
    analysis = analyze_profile_risk(new_profile, monitored_users)
    
    alert_created = False
    alert_id = None
    if analysis["risk_score"] >= MONITORING_ALERT_THRESHOLD and analysis["primary_match"]:
        prot_id = analysis["primary_match"]["protected_id"]
        reason_summary = "; ".join([f["description"] for f in analysis["factors"][:3]])
        alert_id, _ = execute_db("""
            INSERT INTO alerts (protected_profile_id, demo_profile_id, risk_score, risk_level, reason_summary, status)
            VALUES (?, ?, ?, ?, ?, 'UNREAD')
        """, (prot_id, profile_id, analysis["risk_score"], analysis["risk_level"], reason_summary))
        alert_created = True

    return jsonify({
        "status": "success",
        "message": f"Demo profile '@{username}' created successfully.",
        "profile": new_profile,
        "immediate_analysis": analysis,
        "alert_triggered": alert_created,
        "alert_id": alert_id
    }), 201

@demo_bp.route('/api/demo-profiles/<int:profile_id>', methods=['DELETE'])
def delete_demo_profile(profile_id):
    """Deletes a profile from the demo sandbox."""
    _, count = execute_db("DELETE FROM demo_profiles WHERE id = ?", (profile_id,))
    if count == 0:
        return jsonify({"status": "error", "message": "Profile not found."}), 404

    return jsonify({
        "status": "success",
        "message": "Demo profile removed from sandbox."
    })
