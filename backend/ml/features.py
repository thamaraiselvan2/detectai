"""
Feature extraction for fake profile detection ML pipeline.
Converts a profile dict into a numeric feature vector.
Reuses all existing risk_engine calculations — no new similarity logic.
"""

import re
import math
import sys
import os

# Make sure risk_engine is importable from this module's location
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from risk_engine.string_metrics import (
    calculate_sequence_similarity,
    calculate_levenshtein_distance,
    detect_suspicious_username_patterns,
    SUSPICIOUS_AFFIXES,
)
from risk_engine.behavior_metrics import analyze_behavior_and_ratios
from risk_engine.bio_analyzer import analyze_bio_and_content, PHISHING_KEYWORDS
from risk_engine.avatar_similarity import are_similar_avatars

# ── Feature names (must match the order of extract_features output) ──────────
FEATURE_NAMES = [
    "username_similarity_max",      # max seq similarity to any protected username
    "username_levenshtein_min",     # min levenshtein to any protected (normalised)
    "name_similarity_max",          # max display-name similarity to any protected
    "bio_similarity_max",           # max bio similarity to any protected
    "follower_following_ratio",     # followers / max(following, 1)
    "account_age_days_norm",        # log1p(account_age_days) / log1p(3650)
    "post_count_norm",              # log1p(posts_count) / log1p(10000)
    "posting_rate",                 # posts / max(account_age_days, 1)
    "avatar_present",               # 1 if has non-default avatar else 0
    "avatar_similarity_max",        # exact avatar reference match to a protected profile
    "has_phishing_keywords",        # 1 if bio contains phishing patterns
    "has_suspicious_username",      # 1 if username matches bot patterns
    "has_suspicious_affix",         # 1 if username contains impersonation affix
    "username_entropy",             # Shannon entropy of username chars (0-1 norm)
    "follower_count_log",           # log1p(followers) / log1p(300_000_000)
    "following_count_log",          # log1p(following) / log1p(10_000)
    "is_verified",                  # 1 if verified badge
    "bio_empty",                    # 1 if no bio provided
    "ip_signal",                    # 0.0–1.0 placeholder (from security layer)
    "device_signal",                # 0.0–1.0 placeholder (from security layer)
]


def _shannon_entropy(s: str) -> float:
    """Normalised Shannon entropy of a string."""
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    h = -sum((cnt / n) * math.log2(cnt / n) for cnt in freq.values())
    max_h = math.log2(max(len(freq), 1))
    return h / max_h if max_h > 0 else 0.0


def _has_suspicious_affix(username: str) -> float:
    """Returns 1.0 if username contains an impersonation affix."""
    u = username.lower()
    for affix in SUSPICIOUS_AFFIXES:
        if re.search(rf'(^{affix}|{affix}$)', u):
            return 1.0
    return 0.0


def extract_features(
    profile: dict,
    protected_profiles: list = None,
    ip_signal: float = 0.0,
    device_signal: float = 0.0,
) -> list:
    """
    Converts a profile dict into a flat numeric feature vector.

    Args:
        profile: dict with keys username, display_name, bio, followers_count,
                 following_count, posts_count, account_age_days, avatar_url,
                 is_verified
        protected_profiles: list of protected profile dicts for similarity features
        ip_signal: 0.0–1.0, higher = more suspicious (from security layer)
        device_signal: 0.0–1.0, higher = more suspicious (from security layer)

    Returns:
        List of floats in the order defined by FEATURE_NAMES
    """
    protected_profiles = protected_profiles or []
    username = (profile.get("username") or "").strip().lower()
    display_name = (profile.get("display_name") or "").strip()
    bio = (profile.get("bio") or "").strip()
    avatar_url = (profile.get("avatar_url") or "").strip()
    followers = int(profile.get("followers_count") or profile.get("follower_count") or 0)
    following = int(profile.get("following_count") or 0)
    posts = int(profile.get("posts_count") or 0)
    age_days = int(profile.get("account_age_days") or 1)
    is_verified = 1.0 if profile.get("is_verified") else 0.0

    # ── Similarity features (vs. protected profiles) ──────────────────────────
    username_sim_max = 0.0
    levenshtein_min_norm = 0.0  # 1.0 = identical; 0.0 also means no comparison target
    name_sim_max = 0.0
    bio_sim_max = 0.0
    avatar_similarity_max = 0.0

    for prot in protected_profiles:
        pu = (prot.get("username") or "").strip().lower()
        pn = (prot.get("display_name") or "").strip()
        pb = (prot.get("bio") or "").strip()
        pa = (prot.get("avatar_url") or "").strip()

        if not pu or pu == username:
            continue

        u_sim = calculate_sequence_similarity(username, pu)
        username_sim_max = max(username_sim_max, u_sim)

        lev = calculate_levenshtein_distance(username, pu)
        max_len = max(len(username), len(pu), 1)
        lev_norm = 1.0 - min(lev / max_len, 1.0)  # 1 = very similar
        levenshtein_min_norm = max(levenshtein_min_norm, lev_norm)

        n_sim = calculate_sequence_similarity(display_name.lower(), pn.lower())
        name_sim_max = max(name_sim_max, n_sim)

        if pb:
            b_sim = calculate_sequence_similarity(bio.lower(), pb.lower())
            bio_sim_max = max(bio_sim_max, b_sim)

        if are_similar_avatars(avatar_url, pa):
            avatar_similarity_max = 1.0

    # ── Behavioral features ────────────────────────────────────────────────────
    behavior = analyze_behavior_and_ratios(profile)
    ratio = behavior["metrics"]["ratio"]
    # Normalise ratio: 0 = very spammy (0 followers, many following), 1 = healthy
    ratio_norm = min(ratio / max(ratio, 1.0), 1.0) if ratio <= 1.0 else 1.0

    age_norm = math.log1p(age_days) / math.log1p(3650)
    post_norm = math.log1p(posts) / math.log1p(10000)
    posting_rate = posts / max(age_days, 1)
    posting_rate_norm = min(posting_rate / 10.0, 1.0)

    has_avatar = 1.0 if (avatar_url and "default" not in avatar_url.lower()) else 0.0

    follower_log = math.log1p(followers) / math.log1p(300_000_000)
    following_log = math.log1p(following) / math.log1p(10_000)

    # ── Bio & username pattern features ───────────────────────────────────────
    bio_result = analyze_bio_and_content(bio, is_verified=bool(profile.get("is_verified")))
    has_phishing = 1.0 if bio_result.get("matched_keywords") else 0.0
    bio_empty = 1.0 if not bio else 0.0

    pattern_result = detect_suspicious_username_patterns(username)
    has_suspicious_username = 1.0 if pattern_result["is_suspicious"] else 0.0

    has_affix = _has_suspicious_affix(username)
    entropy = _shannon_entropy(username)

    return [
        round(username_sim_max, 4),
        round(levenshtein_min_norm, 4),
        round(name_sim_max, 4),
        round(bio_sim_max, 4),
        round(ratio_norm, 4),
        round(min(age_norm, 1.0), 4),
        round(post_norm, 4),
        round(posting_rate_norm, 4),
        round(has_avatar, 4),
        round(avatar_similarity_max, 4),
        round(has_phishing, 4),
        round(has_suspicious_username, 4),
        round(has_affix, 4),
        round(entropy, 4),
        round(min(follower_log, 1.0), 4),
        round(min(following_log, 1.0), 4),
        round(is_verified, 4),
        round(bio_empty, 4),
        round(min(max(ip_signal, 0.0), 1.0), 4),
        round(min(max(device_signal, 0.0), 1.0), 4),
    ]


def build_feature_dict(profile: dict, protected_profiles: list = None, **kwargs) -> dict:
    """Returns features as a named dict (useful for debugging/explainability)."""
    values = extract_features(profile, protected_profiles, **kwargs)
    return dict(zip(FEATURE_NAMES, values))


if __name__ == "__main__":
    # Quick smoke test
    test_profile = {
        "username": "elonmusk_official",
        "display_name": "Elon Musk",
        "bio": "CEO of Tesla & X. Free Bitcoin giveaway! Click link below.",
        "followers_count": 14,
        "following_count": 1820,
        "posts_count": 2,
        "account_age_days": 2,
        "is_verified": 0,
        "avatar_url": "https://example.com/avatar.jpg",
    }
    test_protected = [{
        "username": "elonmusk",
        "display_name": "Elon Musk",
        "bio": "CEO of Tesla, SpaceX, xAI & CTO of X.",
    }]
    features = extract_features(test_profile, test_protected)
    for name, val in zip(FEATURE_NAMES, features):
        print(f"  {name:35s}: {val}")
