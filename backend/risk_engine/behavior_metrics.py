def analyze_behavior_and_ratios(profile: dict) -> dict:
    """
    Analyzes follower/following ratios, post activity, and profile completeness.
    Returns score contributions and explanation factors.
    """
    followers = int(profile.get("followers_count") or profile.get("follower_count") or 0)
    following = int(profile.get("following_count") or 0)
    posts = int(profile.get("posts_count") or 0)
    account_age_days = int(profile.get("account_age_days") or 30)
    avatar_url = profile.get("avatar_url") or ""
    is_verified = bool(profile.get("is_verified", False))

    reasons = []
    score_boost = 0

    # 1. Extreme Follower-to-Following Asymmetry
    # Spam/bot profiles often follow thousands while having almost zero followers
    if following > 200:
        ratio = followers / max(following, 1)
        if ratio < 0.01 and followers < 25:
            score_boost += 20
            reasons.append(f"Severely distorted follower ratio ({followers} followers vs {following} following - {round(ratio, 4)}:1), typical of mass-follow bot scripts")
        elif ratio < 0.05 and followers < 50:
            score_boost += 15
            reasons.append(f"High following-to-follower disproportion ({followers} followers vs {following} following)")
        elif ratio < 0.10 and followers < 100:
            score_boost += 10
            reasons.append(f"Skewed following/follower ratio ({followers} followers vs {following} following)")

    # 2. Activity Vacuum (Following many accounts with zero posts)
    if posts == 0 and following >= 100:
        score_boost += 10
        reasons.append(f"Zero published posts despite actively following {following} accounts")
    elif posts == 0 and account_age_days > 60:
        score_boost += 5
        reasons.append("Aged account with zero historical post activity")

    # 3. Account Freshness / Disposable Profile Flag
    if account_age_days <= 3:
        score_boost += 10
        reasons.append(f"Newly registered account ({account_age_days} days old)")
    elif account_age_days <= 14:
        score_boost += 5
        reasons.append(f"Recent account creation date ({account_age_days} days old)")

    # 4. Avatar Presence
    has_default_avatar = not avatar_url or "default" in avatar_url.lower() or avatar_url.strip() == ""
    if has_default_avatar:
        score_boost += 10
        reasons.append("Default or missing profile avatar")

    return {
        "score_boost": min(score_boost, 35),
        "reasons": reasons,
        "metrics": {
            "followers": followers,
            "following": following,
            "posts": posts,
            "ratio": round(followers / max(following, 1), 4) if following else followers,
            "account_age_days": account_age_days,
            "has_avatar": not has_default_avatar
        }
    }
