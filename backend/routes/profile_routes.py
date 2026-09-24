from flask import Blueprint, request, jsonify
import json
from database import query_db, execute_db
from risk_engine.detector import detect_profile

profile_bp = Blueprint('profile_bp', __name__)


@profile_bp.route('/check-profile', methods=['POST'])
@profile_bp.route('/api/check-profile', methods=['POST'])
def check_profile():
    """
    Analyzes a target profile for fake signals, spam footprint, and impersonation.
    Accepts:
      - Option A: { "username": "elonmusk_official" } -> Looks up in demo_profiles or scans standalone.
      - Option B: Full profile object { "username", "display_name", "bio", "followers_count", ... }
    """
    data = request.get_json() or {}
    username = data.get("username", "").strip().lstrip('@')

    if not username:
        return jsonify({"status": "error", "message": "Username is required."}), 400

    # Prototype thresholds: 0-39 REAL, 40-69 SUSPICIOUS, 70-100 FAKE.
    target_profile = None
    demo_record = query_db("SELECT * FROM demo_profiles WHERE LOWER(username) = LOWER(?)", (username,), one=True)
    if demo_record:
        target_profile = dict(demo_record)
    elif len(data.keys()) <= 2 or data.get("demo_only", False):
        # Username was entered for demo check but not found in existing demo data
        return jsonify({
            "status": "not_found",
            "found_in_demo": False,
            "message": "Profile not found in demo data."
        }), 200

    if not target_profile:
        # Build profile from request payload or defaults
        target_profile = {
            "username": username,
            "display_name": data.get("display_name") or username,
            "bio": data.get("bio", ""),
            "avatar_url": data.get("avatar_url", ""),
            "followers_count": int(data.get("followers_count") or data.get("follower_count") or 0),
            "following_count": int(data.get("following_count") or 0),
            "posts_count": int(data.get("posts_count") or 0),
            "account_age_days": int(data.get("account_age_days") or 30),
            "is_verified": bool(data.get("is_verified", False))
        }

    # 2. Fetch all registered protected accounts
    protected_profiles = query_db("SELECT * FROM protected_profiles")
    demo_profiles = query_db("""
         SELECT id, username, display_name, bio, avatar_url, followers_count,
             following_count, posts_count, account_age_days, is_verified, created_at
        FROM demo_profiles
    """)

    # 3. Execute Unified Detection Pipeline (rule-based + ML + LLM + explainability)
    analysis = detect_profile(
        target_profile,
        protected_profiles,
        demo_profiles=demo_profiles,
        ip_signal=0.0,    # will be non-zero when called from security-aware context
        device_signal=0.0,
        use_llm=True,
    )

    # 4. Record Scan in check_history audit table
    matched_id = analysis["primary_match"]["protected_id"] if analysis["primary_match"] else None
    factors_json_str = json.dumps(analysis["factors"])

    execute_db("""
        INSERT INTO check_history (target_username, matched_protected_id, risk_score, risk_level, factors_json, recommendation)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        target_profile["username"],
        matched_id,
        analysis["risk_score"],
        analysis["risk_level"],
        factors_json_str,
        analysis["recommendation"]
    ))

    return jsonify({
        "status": "success",
        "found_in_demo": bool(demo_record),
        "username": target_profile["username"],
        "classification": "FAKE" if analysis["risk_score"] >= 70 else "SUSPICIOUS" if analysis["risk_score"] >= 40 else "REAL",
        "risk_score": analysis["risk_score"],
        "risk_level": analysis["risk_level"],
        "reasons": [factor["description"] for factor in analysis["factors"]],
        "profile": target_profile,
        "similar_profiles": analysis.get("similar_profiles", []),
        "analysis": analysis,
        # New enrichment fields (backward-compatible — consumers can ignore)
        "ml_result": analysis.get("ml_result"),
        "llm_result": analysis.get("llm_result"),
        "explanation": analysis.get("explanation"),
    })

@profile_bp.route('/api/check-history', methods=['GET'])
def get_check_history():
    """Returns recent scan history with pagination."""
    limit = int(request.args.get("limit", 20))
    history = query_db("""
        SELECT h.*, p.username as protected_username, p.display_name as protected_display_name
        FROM check_history h
        LEFT JOIN protected_profiles p ON h.matched_protected_id = p.id
        ORDER BY h.created_at DESC
        LIMIT ?
    """, (limit,))

    # Parse factors_json for each entry
    results = []
    for item in history:
        entry = dict(item)
        try:
            entry["factors"] = json.loads(entry["factors_json"])
        except Exception:
            entry["factors"] = []
        results.append(entry)

    return jsonify({
        "status": "success",
        "history": results
    })
