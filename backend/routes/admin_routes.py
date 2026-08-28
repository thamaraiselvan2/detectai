from flask import Blueprint, request, jsonify
import json
from database import query_db, execute_db, init_db
from seed_data import seed_database_if_empty

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    """Aggregates metrics for the security operations & admin dashboard."""
    # 1. Total checks performed
    total_checks = query_db("SELECT COUNT(*) as count FROM check_history", one=True)["count"]

    # 2. Risk level distribution in scan history
    risk_distribution = query_db("""
        SELECT risk_level, COUNT(*) as count
        FROM check_history
        GROUP BY risk_level
    """)
    dist_map = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for row in risk_distribution:
        dist_map[row["risk_level"]] = row["count"]

    # 3. Protected Users count & monitoring count
    protected_stats = query_db("""
        SELECT COUNT(*) as total_protected,
               SUM(CASE WHEN is_monitoring_active = 1 THEN 1 ELSE 0 END) as active_monitored
        FROM protected_profiles
    """, one=True)

    # 4. Alerts stats
    alert_stats = query_db("""
        SELECT COUNT(*) as total_alerts,
               SUM(CASE WHEN status = 'UNREAD' THEN 1 ELSE 0 END) as unread_alerts,
               SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved_alerts
        FROM alerts
    """, one=True)

    # 5. Demo platform profiles count
    demo_count = query_db("SELECT COUNT(*) as count FROM demo_profiles", one=True)["count"]

    # 6. Top targeted protected users
    top_targets = query_db("""
        SELECT p.username, p.display_name, COUNT(a.id) as impersonation_count
        FROM alerts a
        JOIN protected_profiles p ON a.protected_profile_id = p.id
        GROUP BY p.id
        ORDER BY impersonation_count DESC
        LIMIT 5
    """)

    return jsonify({
        "status": "success",
        "stats": {
            "total_checks": total_checks,
            "risk_distribution": dist_map,
            "total_protected_users": protected_stats["total_protected"] or 0,
            "active_monitored_users": protected_stats["active_monitored"] or 0,
            "total_alerts": alert_stats["total_alerts"] or 0,
            "unread_alerts": alert_stats["unread_alerts"] or 0,
            "resolved_alerts": alert_stats["resolved_alerts"] or 0,
            "total_demo_profiles": demo_count,
            "top_impersonated_targets": top_targets
        }
    })

@admin_bp.route('/api/admin/logs', methods=['GET'])
def get_admin_logs():
    """Returns detailed audit history with optional risk_level filter."""
    risk_filter = request.args.get("risk_level", "").strip().upper()
    search = request.args.get("search", "").strip()
    limit = int(request.args.get("limit", 50))

    query = """
        SELECT h.*, p.username as protected_username, p.display_name as protected_display_name
        FROM check_history h
        LEFT JOIN protected_profiles p ON h.matched_protected_id = p.id
        WHERE 1=1
    """
    args = []
    if risk_filter in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        query += " AND h.risk_level = ?"
        args.append(risk_filter)

    if search:
        query += " AND LOWER(h.target_username) LIKE LOWER(?)"
        args.append(f"%{search}%")

    query += " ORDER BY h.created_at DESC LIMIT ?"
    args.append(limit)

    logs = query_db(query, tuple(args))
    parsed_logs = []
    for row in logs:
        entry = dict(row)
        try:
            entry["factors"] = json.loads(entry["factors_json"])
        except Exception:
            entry["factors"] = []
        parsed_logs.append(entry)

    return jsonify({
        "status": "success",
        "logs": parsed_logs
    })

@admin_bp.route('/api/admin/reset-demo', methods=['POST'])
def reset_demo_database():
    """Resets database back to default seed environment."""
    execute_db("DELETE FROM alerts")
    execute_db("DELETE FROM check_history")
    execute_db("DELETE FROM demo_profiles")
    execute_db("DELETE FROM protected_profiles")
    seed_database_if_empty()

    return jsonify({
        "status": "success",
        "message": "Database successfully reset to initial seed state."
    })
