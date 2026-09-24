from flask import Blueprint, request, jsonify
import re
from database import query_db, execute_db

protected_bp = Blueprint('protected_bp', __name__)


def register_profile_for_protection(username, email, original_profile=None):
    """Create the existing protected and legacy registration records together."""
    if not original_profile:
        original_profile = query_db(
            "SELECT * FROM demo_profiles WHERE LOWER(username) = LOWER(?)",
            (username,), one=True
        )
    if not original_profile:
        return None, f"Profile '@{username}' was not found in the demo profiles."

    existing_protected = query_db(
        """SELECT id, username, email FROM protected_profiles
           WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)""",
        (username, email), one=True
    )
    existing_legacy = query_db(
        """SELECT id, username, email FROM registered_profiles
           WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)""",
        (username, email), one=True
    )
    if existing_protected or existing_legacy:
        existing = existing_protected or existing_legacy
        if existing["username"].lower() == username.lower():
            message = f"Username '@{username}' is already registered for protection."
        else:
            message = "That email address is already used for a registered profile."
        return None, message

    display_name = original_profile.get("display_name") or username
    bio = original_profile.get("bio", "")
    avatar_url = original_profile.get("avatar_url", "")
    follower_count = int(original_profile.get("followers_count") or 0)
    protected_id, _ = execute_db("""
        INSERT INTO protected_profiles
            (username, display_name, email, bio, avatar_url, follower_count, is_monitoring_active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    """, (username, display_name, email, bio, avatar_url, follower_count))
    registered_id, _ = execute_db("""
        INSERT INTO registered_profiles (username, email, original_profile_id)
        VALUES (?, ?, ?)
    """, (username, email, original_profile["id"]))
    return {"protected_id": protected_id, "registered_id": registered_id, "email": email}, None


@protected_bp.route('/register-user', methods=['POST'])
@protected_bp.route('/api/register-user', methods=['POST'])
def register_user():
    """
    Registers an existing demo profile in the protected identity registry.
    Demo account credentials remain owned by demo_profiles and are not created
    by this application-level registration endpoint.
    """
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()

    if not username or not email:
        return jsonify({"status": "error", "message": "Username and email are required."}), 400

    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return jsonify({"status": "error", "message": "Please provide a valid email address."}), 400

    original_profile = query_db(
        "SELECT * FROM demo_profiles WHERE LOWER(username) = LOWER(?)",
        (username,), one=True
    )
    if not original_profile:
        return jsonify({
            "status": "not_found",
            "message": f"Profile '@{username}' was not found in the demo profiles."
        }), 404
    original_profile = dict(original_profile)
    registration, registration_error = register_profile_for_protection(username, email, original_profile)
    if registration_error:
        return jsonify({"status": "error", "message": registration_error}), 409

    protected_id = registration["protected_id"]
    registered_id = registration["registered_id"]
    registered_record = query_db(
        "SELECT id, username, email, original_profile_id, registered_at FROM registered_profiles WHERE id = ?",
        (registered_id,), one=True
    )
    return jsonify({
        "status": "success",
        "message": f"Profile '@{username}' successfully registered for protection.",
        "registered_profile": {
            **dict(registered_record),
            "original_profile": original_profile
        },
        "protected_profile_id": protected_id,
        "registered_username": username,
        "registered_profile_id": registered_id
    }), 201

@protected_bp.route('/api/protected-users', methods=['GET'])
def get_protected_users():
    """Lists all registered protected profiles with their monitoring state and alert counts."""
    users = query_db("""
        SELECT p.*,
               COUNT(a.id) as total_alerts,
               SUM(CASE WHEN a.status = 'UNREAD' THEN 1 ELSE 0 END) as unread_alerts
        FROM protected_profiles p
        LEFT JOIN alerts a ON p.id = a.protected_profile_id
        GROUP BY p.id
        ORDER BY p.created_at DESC
    """)
    return jsonify({
        "status": "success",
        "protected_users": users
    })

@protected_bp.route('/api/protected-users/<int:user_id>/monitoring', methods=['PATCH'])
def toggle_monitoring(user_id):
    """Toggles continuous monitoring on/off for a protected user."""
    data = request.get_json() or {}
    active_state = 1 if data.get("active", True) else 0

    _, count = execute_db("""
        UPDATE protected_profiles SET is_monitoring_active = ? WHERE id = ?
    """, (active_state, user_id))

    if count == 0:
        return jsonify({"status": "error", "message": "Protected user not found."}), 404

    return jsonify({
        "status": "success",
        "is_monitoring_active": active_state,
        "message": f"Monitoring {'activated' if active_state else 'deactivated'}."
    })

@protected_bp.route('/api/protected-users/<int:user_id>', methods=['DELETE'])
def delete_protected_user(user_id):
    """Removes a user from the protected identity vault."""
    execute_db("DELETE FROM alerts WHERE protected_profile_id = ?", (user_id,))
    _, count = execute_db("DELETE FROM protected_profiles WHERE id = ?", (user_id,))
    if count == 0:
        return jsonify({"status": "error", "message": "Protected user not found."}), 404

    return jsonify({
        "status": "success",
        "message": "Protected identity successfully removed."
    })
