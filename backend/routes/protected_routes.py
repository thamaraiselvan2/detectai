from flask import Blueprint, request, jsonify
import re
from database import query_db, execute_db

protected_bp = Blueprint('protected_bp', __name__)

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
        (username,),
        one=True
    )
    if not original_profile:
        return jsonify({
            "status": "not_found",
            "message": f"Profile '@{username}' was not found in the demo profiles."
        }), 404
    original_profile = dict(original_profile)

    existing_protected = query_db(
        """SELECT id, username, email FROM protected_profiles
           WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)""",
        (username, email),
        one=True
    )
    existing_legacy = query_db(
        """SELECT id, username, email FROM registered_profiles
           WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)""",
        (username, email),
        one=True
    )
    if existing_protected or existing_legacy:
        existing = existing_protected or existing_legacy
        if existing["username"].lower() == username.lower():
            message = f"Username '@{username}' is already registered for protection."
        else:
            message = "That email address is already used for a registered profile."
        return jsonify({"status": "error", "message": message}), 409

    display_name = data.get("display_name", "").strip() or original_profile["display_name"]
    bio = data.get("bio", "").strip() or original_profile.get("bio", "")
    avatar_url = data.get("avatar_url", "").strip() or original_profile.get("avatar_url", "")
    follower_count = int(data.get("follower_count") or original_profile.get("followers_count") or 0)

    protected_id, _ = execute_db("""
        INSERT INTO protected_profiles
            (username, display_name, email, bio, avatar_url, follower_count, is_monitoring_active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    """, (username, display_name, email, bio, avatar_url, follower_count))

    # Keep the legacy association for the existing Demo Social alert workflow.
    registered_id, _ = execute_db("""
        INSERT INTO registered_profiles (username, email, original_profile_id)
        VALUES (?, ?, ?)
    """, (username, email, original_profile["id"]))
    registered_record = query_db(
        "SELECT id, username, email, original_profile_id, registered_at FROM registered_profiles WHERE id = ?",
        (registered_id,),
        one=True
    )
    registered_record = dict(registered_record)

    return jsonify({
        "status": "success",
        "message": f"Profile '@{username}' successfully registered for protection.",
        "registered_profile": {
            **registered_record,
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
