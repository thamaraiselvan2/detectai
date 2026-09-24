from datetime import datetime, timezone
import json
from flask import Blueprint, request, jsonify
from database import query_db, execute_db
from email_utils import send_impersonation_email
from risk_engine.detector import detect_profile
from config import MONITORING_ALERT_THRESHOLD, EMAIL_CONFIG

monitor_bp = Blueprint('monitor_bp', __name__)


def _safe_email_status(result):
    """Expose only the supported delivery state to API consumers."""
    status = (result or {}).get("status", "failed")
    return status if status in {"sent", "not_configured", "failed", "skipped", "duplicate"} else "failed"


def _dispatch_alert_email(alert):
    """Attempt delivery without allowing email errors to affect monitoring."""
    if alert.get("email_status") == "sent":
        return {"status": "duplicate", "sent": False}
    try:
        signals = json.loads(alert.get("evidence_json") or "{}")
        result = send_impersonation_email(
            recipient=alert.get("email"),
            protected_username=alert.get("protected_username"),
            new_username=alert.get("demo_username"),
            risk_score=alert.get("risk_score"),
            reasons=(alert.get("reason_summary") or "").split("; "),
            classification=alert.get("classification", "FAKE"),
            signals=signals,
            detected_at=alert.get("created_at") or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
    except Exception as error:
        print(f"[MONITOR] Alert email failed (non-fatal): {type(error).__name__}: {error}", flush=True)
        result = {"status": "failed", "sent": False}
    status = _safe_email_status(result)
    execute_db(
        "UPDATE alerts SET email_status = ?, email_dispatched = ?, email_sent_at = CASE WHEN ? = 'sent' THEN CURRENT_TIMESTAMP ELSE email_sent_at END WHERE id = ?",
        (status, 1 if status == "sent" else 0, status, alert["id"]),
    )
    return {"status": status, "sent": status == "sent"}


def _alert_with_email_status(alert, email_status):
    return {
        "alert_id": alert["id"],
        "protected_username": alert["protected_username"],
        "target_demo_username": alert["demo_username"],
        "classification": alert.get("classification", "FAKE"),
        "risk_score": alert["risk_score"],
        "risk_level": alert["risk_level"],
        "reason": alert["reason_summary"],
        "email_status": email_status,
    }

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
    existing_alerts = query_db("""
        SELECT protected_profile_id, demo_profile_id, risk_score, risk_level, reason_summary
        FROM alerts
    """)
    existing_alert_pairs = {
        (a["protected_profile_id"], a["demo_profile_id"]):
        (a["risk_score"], a["risk_level"], a["reason_summary"])
        for a in existing_alerts
    }

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

            if (
                analysis.get("classification") in {"SUSPICIOUS", "FAKE"}
                and analysis["risk_score"] >= MONITORING_ALERT_THRESHOLD
                and analysis["primary_match"]
            ):
                pair_key = (prot["id"], demo["id"])
                reason_summary = "; ".join([f["description"] for f in analysis["factors"][:8]])
                event_signature = (analysis["risk_score"], analysis["risk_level"], reason_summary)
                if existing_alert_pairs.get(pair_key) != event_signature:
                    evidence_json = json.dumps(analysis.get("signals", {}), ensure_ascii=True)
                    alert_id, _ = execute_db("""
                        INSERT INTO alerts (protected_profile_id, demo_profile_id, alert_type, classification,
                            risk_score, risk_level, reason_summary, evidence_json, status, email_status)
                        VALUES (?, ?, 'impersonation', ?, ?, ?, ?, ?, 'UNREAD', 'skipped')
                      """, (prot["id"], demo["id"], analysis["classification"], analysis["risk_score"],
                          analysis["risk_level"], reason_summary, evidence_json))

                    existing_alert_pairs[pair_key] = event_signature
                    alert = query_db("""
                        SELECT a.*, p.email, p.username as protected_username, d.username as demo_username
                        FROM alerts a
                        JOIN protected_profiles p ON a.protected_profile_id = p.id
                        JOIN demo_profiles d ON a.demo_profile_id = d.id
                        WHERE a.id = ?
                    """, (alert_id,), one=True)
                    delivery = _dispatch_alert_email(alert)
                    new_alerts.append(_alert_with_email_status(alert, delivery["status"]))

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
    """Manually retry or dispatch an alert email without affecting detection."""
    alert = query_db("""
        SELECT a.*, p.email, p.username as protected_username, d.username as demo_username
        FROM alerts a
        JOIN protected_profiles p ON a.protected_profile_id = p.id
        JOIN demo_profiles d ON a.demo_profile_id = d.id
        WHERE a.id = ?
    """, (alert_id,), one=True)

    if not alert:
        return jsonify({"status": "error", "message": "Alert not found."}), 404

    if alert.get("email_status") == "sent":
        email_status = "duplicate"
    else:
        email_status = _dispatch_alert_email(alert)["status"]

    return jsonify({
        "status": "success",
        "message": f"Security alert email status: {email_status}.",
        "alert": {
            "triggered": True,
            "type": alert.get("alert_type", "impersonation"),
            "email_status": email_status,
        },
        "email_details": {
            "recipient": alert["email"] if email_status == "sent" else None,
            "subject": f"[SECURITY ALERT] Impersonator Detected for @{alert['protected_username']}",
            "flagged_account": f"@{alert['demo_username']}",
            "risk_score": alert["risk_score"],
            "risk_level": alert["risk_level"],
            "classification": alert.get("classification", "FAKE"),
            "reasons": alert["reason_summary"],
            "email_status": email_status,
        }
    })
