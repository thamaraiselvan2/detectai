from flask import Blueprint, request, jsonify
from database import query_db, execute_db
from risk_engine.detector import detect_profile
from config import MONITORING_ALERT_THRESHOLD, EMAIL_CONFIG

monitor_bp = Blueprint('monitor_bp', __name__)

@monitor_bp.route('/monitor-username', methods=['POST'])
@monitor_bp.route('/api/monitor-username', methods=['POST'])
def monitor_username():
    """
    Executes a surveillance cycle. Scans demo profiles against monitored protected users
    and generates security alerts for any detected impersonation attempts.
    Payload (optional): { "username": "elonmusk" } or {} (runs for all active monitored users).
    """
    data = request.get_json() or {}
    target_username = data.get("username", "").strip()

    if target_username:
        protected_list = query_db("""
            SELECT * FROM protected_profiles WHERE LOWER(username) = LOWER(?) AND is_monitoring_active = 1
        """, (target_username,))
    else:
        protected_list = query_db("""
            SELECT * FROM protected_profiles WHERE is_monitoring_active = 1
        """)

    if not protected_list:
        return jsonify({
            "status": "success",
            "message": "No active monitored profiles found for surveillance.",
            "new_alerts_count": 0,
            "alerts": []
        })

    demo_profiles = query_db("SELECT * FROM demo_profiles")
    existing_alerts = query_db("SELECT protected_profile_id, demo_profile_id FROM alerts")
    existing_alert_pairs = set((a["protected_profile_id"], a["demo_profile_id"]) for a in existing_alerts)

    new_alerts = []

    for prot in protected_list:
        for demo in demo_profiles:
            # Skip if identical authentic account
            if demo["username"].lower() == prot["username"].lower():
                continue

            # Run the same unified detection pipeline, including optional LLM analysis.
            analysis = detect_profile(
                demo,
                [prot],
                demo_profiles=demo_profiles,
                use_llm=True,
            )

            if analysis["risk_score"] >= MONITORING_ALERT_THRESHOLD and analysis["primary_match"]:
                pair_key = (prot["id"], demo["id"])
                if pair_key not in existing_alert_pairs:
                    reason_summary = "; ".join([f["description"] for f in analysis["factors"][:3]])
                    alert_id, _ = execute_db("""
                        INSERT INTO alerts (protected_profile_id, demo_profile_id, risk_score, risk_level, reason_summary, status)
                        VALUES (?, ?, ?, ?, ?, 'UNREAD')
                    """, (prot["id"], demo["id"], analysis["risk_score"], analysis["risk_level"], reason_summary))

                    existing_alert_pairs.add(pair_key)
                    new_alerts.append({
                        "alert_id": alert_id,
                        "protected_username": prot["username"],
                        "target_demo_username": demo["username"],
                        "risk_score": analysis["risk_score"],
                        "risk_level": analysis["risk_level"],
                        "reason": reason_summary
                    })

    return jsonify({
        "status": "success",
        "message": f"Surveillance cycle completed. {len(new_alerts)} new impersonation alerts flagged.",
        "new_alerts_count": len(new_alerts),
        "alerts": new_alerts
    })

@monitor_bp.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Returns all impersonation alerts with rich context on both identities."""
    status_filter = request.args.get("status")
    query = """
        SELECT a.*,
               p.username as protected_username,
               p.display_name as protected_display_name,
               p.email as protected_email,
               p.avatar_url as protected_avatar_url,
               d.username as demo_username,
               d.display_name as demo_display_name,
               d.bio as demo_bio,
               d.avatar_url as demo_avatar_url,
               d.followers_count as demo_followers_count,
               d.following_count as demo_following_count,
               d.posts_count as demo_posts_count
        FROM alerts a
        JOIN protected_profiles p ON a.protected_profile_id = p.id
        JOIN demo_profiles d ON a.demo_profile_id = d.id
    """
    args = ()
    if status_filter:
        query += " WHERE a.status = ?"
        args = (status_filter.upper(),)

    query += " ORDER BY a.created_at DESC"
    alerts = query_db(query, args)

    return jsonify({
        "status": "success",
        "alerts": alerts
    })

@monitor_bp.route('/api/alerts/<int:alert_id>/status', methods=['PATCH'])
def update_alert_status(alert_id):
    """Updates status of an alert (e.g., ACKNOWLEDGED, RESOLVED, UNREAD)."""
    data = request.get_json() or {}
    new_status = data.get("status", "RESOLVED").upper()

    if new_status not in ["UNREAD", "ACKNOWLEDGED", "RESOLVED"]:
        return jsonify({"status": "error", "message": "Invalid status."}), 400

    _, count = execute_db("UPDATE alerts SET status = ? WHERE id = ?", (new_status, alert_id))
    if count == 0:
        return jsonify({"status": "error", "message": "Alert not found."}), 404

    return jsonify({
        "status": "success",
        "alert_id": alert_id,
        "new_status": new_status,
        "message": f"Alert status updated to {new_status}."
    })

@monitor_bp.route('/api/alerts/<int:alert_id>/dispatch-email', methods=['POST'])
def dispatch_email_alert(alert_id):
    """Simulates sending an immediate email notification to the protected user."""
    alert = query_db("""
        SELECT a.*, p.email, p.username as protected_username, d.username as demo_username
        FROM alerts a
        JOIN protected_profiles p ON a.protected_profile_id = p.id
        JOIN demo_profiles d ON a.demo_profile_id = d.id
        WHERE a.id = ?
    """, (alert_id,), one=True)

    if not alert:
        return jsonify({"status": "error", "message": "Alert not found."}), 404

    execute_db("UPDATE alerts SET email_dispatched = 1 WHERE id = ?", (alert_id,))

    return jsonify({
        "status": "success",
        "message": f"Security alert email successfully dispatched to {alert['email']}.",
        "email_details": {
            "recipient": alert["email"],
            "subject": f"[SECURITY ALERT] Impersonator Detected for @{alert['protected_username']}",
            "flagged_account": f"@{alert['demo_username']}",
            "risk_score": alert["risk_score"],
            "risk_level": alert["risk_level"],
            "reasons": alert["reason_summary"]
        }
    })
