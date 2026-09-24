from .string_metrics import (
    detect_typosquatting,
    calculate_display_name_similarity,
    calculate_sequence_similarity,
    detect_suspicious_username_patterns
)
from .behavior_metrics import analyze_behavior_and_ratios
from .bio_analyzer import analyze_bio_and_content
from .avatar_similarity import are_similar_avatars


def analyze_demo_profile_similarity(target_profile: dict, demo_profiles: list = None) -> dict:
    """Scores newer demo profiles that closely resemble an older demo profile."""
    demo_profiles = demo_profiles or []
    target_username = (target_profile.get("username") or "").strip().lower()
    target_created_at = target_profile.get("created_at") or ""
    target_age = int(target_profile.get("account_age_days") or 0)
    candidates = []
    strongest = None

    for candidate in demo_profiles:
        candidate_username = (candidate.get("username") or "").strip().lower()
        if not candidate_username or candidate_username == target_username:
            continue

        handle_similarity = calculate_sequence_similarity(target_username, candidate_username)
        display_similarity = calculate_sequence_similarity(
            target_profile.get("display_name") or target_username,
            candidate.get("display_name") or candidate_username
        )
        bio_similarity = calculate_sequence_similarity(
            target_profile.get("bio") or "", candidate.get("bio") or ""
        )
        avatar_similarity = are_similar_avatars(
            target_profile.get("avatar_url"), candidate.get("avatar_url")
        )
        similarity = (
            handle_similarity * 0.55 + display_similarity * 0.2 +
            bio_similarity * 0.2 + (0.05 if avatar_similarity else 0)
        )

        candidate_created_at = candidate.get("created_at") or ""
        candidate_is_older = bool(
            target_created_at and candidate_created_at and target_created_at > candidate_created_at
        )
        if not target_created_at and not candidate_created_at:
            candidate_is_older = target_age < int(candidate.get("account_age_days") or 0)
        candidate_result = {
            "id": candidate.get("id"),
            "username": candidate.get("username"),
            "display_name": candidate.get("display_name"),
            "bio": candidate.get("bio"),
            "avatar_url": candidate.get("avatar_url"),
            "followers_count": candidate.get("followers_count", 0),
            "following_count": candidate.get("following_count", 0),
            "posts_count": candidate.get("posts_count", 0),
            "account_age_days": candidate.get("account_age_days", 0),
            "created_at": candidate_created_at,
            "is_verified": candidate.get("is_verified", 0),
            "avatar_similarity": avatar_similarity,
            "username_similarity": round(handle_similarity, 4),
            "display_name_similarity": round(display_similarity, 4),
            "bio_similarity": round(bio_similarity, 4),
            "similarity_score": round(similarity * 100, 1),
            "is_older": candidate_is_older
        }
        if similarity >= 0.55:
            candidates.append(candidate_result)

        has_profile_match = bio_similarity >= 0.75 or avatar_similarity
        strong_handle_match = handle_similarity >= 0.68
        if similarity >= 0.60 and strong_handle_match and has_profile_match and candidate_is_older:
            if strongest is None or similarity > strongest["similarity"]:
                strongest = {"candidate": candidate_result, "similarity": similarity}

    factors = []
    score_boost = 0
    if strongest:
        older = strongest["candidate"]
        score_boost = 65
        factors = [
            "High similarity to an older profile",
            "The searched profile was created later",
            "Username and bio are highly similar"
        ]
        if older.get("is_verified"):
            score_boost += 10
            factors.append("The older similar profile is verified")

    return {
        "score_boost": score_boost,
        "reasons": factors,
        "similar_profiles": sorted(candidates, key=lambda item: item["similarity_score"], reverse=True)[:5]
    }


def detect_registered_impersonation(new_profile: dict, registered_profiles: list = None) -> dict:
    """Detects a strong match to an older profile registered for protection."""
    similarity = analyze_demo_profile_similarity(new_profile, registered_profiles)
    match = next(
        (candidate for candidate in similarity["similar_profiles"] if candidate.get("is_older")),
        None
    )

    if not match or not similarity["score_boost"]:
        return {"detected": False}

    return {
        "detected": True,
        "new_username": new_profile.get("username"),
        "protected_username": match.get("username"),
        "similarity_score": match.get("similarity_score"),
        "risk_score": min(100, similarity["score_boost"] + 25),
        "classification": "POTENTIAL_IMPERSONATION",
        "reasons": similarity["reasons"]
    }

def classify_risk_level(score: int) -> str:
    """Classifies risk level based on numeric 0-100 score."""
    if score >= 80:
        return "CRITICAL"
    elif score >= 60:
        return "HIGH"
    elif score >= 30:
        return "MEDIUM"
    return "LOW"

def generate_recommendation(risk_level: str, matched_protected: dict = None) -> str:
    """Generates clear, contextual security recommendation."""
    if risk_level == "CRITICAL":
        target = f" targeting @{matched_protected['username']}" if matched_protected else ""
        return f"Severe risk of malicious impersonation{target}. Do not engage, send payments, or click links. Report this profile immediately to platform moderation."
    elif risk_level == "HIGH":
        target = f" related to @{matched_protected['username']}" if matched_protected else ""
        return f"High probability of duplicate identity or spoofing{target}. Exercise caution before interacting or trusting claims."
    elif risk_level == "MEDIUM":
        return "Moderate anomalies detected (e.g. skewed follower ratios or subtle name overlap). Verify identity through alternate verified channels."
    else:
        return "Profile exhibits standard authentic patterns. No significant impersonation signals or behavioral anomalies detected."

def analyze_profile_risk(target_profile: dict, protected_profiles: list = None) -> dict:
    """
    Master risk scoring function. Evaluates a target profile against behavioral baselines
    and all registered protected identities.

    Returns an explainable breakdown of the score, contributing factors, risk level,
    matched protected profile, and recommendations.
    """
    protected_profiles = protected_profiles or []
    target_username = target_profile.get("username", "").strip()
    target_display_name = target_profile.get("display_name", "").strip()
    target_bio = target_profile.get("bio", "").strip()
    is_verified = bool(target_profile.get("is_verified", False))

    factors = []
    total_score = 0

    # 1. Behavioral & Social Metric Analysis
    behavior_res = analyze_behavior_and_ratios(target_profile)
    if behavior_res["score_boost"] > 0:
        total_score += behavior_res["score_boost"]
        for r in behavior_res["reasons"]:
            factors.append({
                "category": "Behavioral & Engagement",
                "points": round(behavior_res["score_boost"] / max(len(behavior_res["reasons"]), 1)),
                "severity": "medium" if behavior_res["score_boost"] > 15 else "low",
                "description": r
            })

    # 2. Standalone Bio Phishing & Scam Keywords Check
    bio_res_standalone = analyze_bio_and_content(target_bio, is_verified=is_verified)
    if bio_res_standalone["score_boost"] > 0:
        total_score += bio_res_standalone["score_boost"]
        for r in bio_res_standalone["reasons"]:
            factors.append({
                "category": "Bio & Phishing Indicators",
                "points": bio_res_standalone["score_boost"],
                "severity": "high" if "phishing" in r.lower() or "trigger" in r.lower() else "medium",
                "description": r
            })

    # 3. Suspicious Username Bot Pattern Check (Standalone)
    user_pattern_res = detect_suspicious_username_patterns(target_username)
    if user_pattern_res["is_suspicious"]:
        total_score += user_pattern_res["score_boost"]
        for r in user_pattern_res["reasons"]:
            factors.append({
                "category": "Username Patterns",
                "points": user_pattern_res["score_boost"],
                "severity": "medium",
                "description": r
            })

    # 3. Protected Identity Impersonation Analysis
    best_match_protected = None
    highest_impersonation_score = 0
    impersonation_factors = []
    similar_candidates = []

    for prot in protected_profiles:
        prot_username = prot.get("username", "").strip()
        prot_display_name = prot.get("display_name", "").strip()
        prot_bio = prot.get("bio", "").strip()

        # Skip if exact same account (e.g. checking the authentic user themselves)
        if target_username.lower() == prot_username.lower():
            # If the user is the authentic protected user, note that it's the verified holder
            continue

        match_score = 0
        match_reasons = []

        # Check Username Typosquatting / Homoglyphs / Affixes
        typo_res = detect_typosquatting(target_username, prot_username)
        if typo_res["is_typosquat"] and typo_res["score_boost"] > 0:
            match_score += typo_res["score_boost"]
            match_reasons.extend(typo_res["reasons"])

        # Check Display Name Duplication
        dn_res = calculate_display_name_similarity(target_display_name, prot_display_name)
        if dn_res["is_similar"] and dn_res["score_boost"] > 0:
            match_score += dn_res["score_boost"]
            match_reasons.extend(dn_res["reasons"])

        # Check Bio Cloning
        if prot_bio:
            bio_clone_res = analyze_bio_and_content(target_bio, protected_bio=prot_bio, is_verified=is_verified)
            # Only add the clone points (skip standalone keyword points already accounted for)
            for r in bio_clone_res["reasons"]:
                if "identical" in r.lower() or "resembles" in r.lower():
                    match_score += 20
                    match_reasons.append(r)

        if match_score > 0:
            candidate_entry = {
                "protected_id": prot.get("id"),
                "username": prot_username,
                "display_name": prot_display_name,
                "email": prot.get("email"),
                "avatar_url": prot.get("avatar_url"),
                "similarity_score": min(match_score, 60),
                "reasons": match_reasons
            }
            similar_candidates.append(candidate_entry)

            if match_score > highest_impersonation_score:
                highest_impersonation_score = match_score
                best_match_protected = candidate_entry
                impersonation_factors = match_reasons

    # Add Impersonation Factors to master list
    if highest_impersonation_score > 0 and best_match_protected:
        capped_impersonation_pts = min(highest_impersonation_score, 50)
        total_score += capped_impersonation_pts
        for reason in impersonation_factors:
            factors.append({
                "category": "Identity Impersonation & Typosquatting",
                "points": round(capped_impersonation_pts / max(len(impersonation_factors), 1)),
                "severity": "critical" if capped_impersonation_pts >= 35 else "high",
                "description": f"{reason} (Targeting authentic user @{best_match_protected['username']})"
            })

    # Sort similar candidates by similarity score
    similar_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)

    # 4. Final Score Normalization (0-100)
    final_score = max(0, min(100, total_score))
    risk_level = classify_risk_level(final_score)
    recommendation = generate_recommendation(risk_level, best_match_protected)

    # If no factors were found, add a clean profile factor
    if not factors:
        factors.append({
            "category": "Baseline Assessment",
            "points": 0,
            "severity": "low",
            "description": "Standard account parameters with normal follower distribution and unique handle"
        })

    return {
        "risk_score": final_score,
        "risk_level": risk_level,
        "primary_match": best_match_protected,
        "similar_profiles": similar_candidates[:5],
        "factors": factors,
        "recommendation": recommendation,
        "behavior_metrics": behavior_res["metrics"]
    }
