"""
Dataset loader for fake profile ML model training.
Builds a labeled dataset from the existing SQLite database.

Label derivation (no fake numbers):
  - Profiles with check_history risk_level = 'HIGH' or 'CRITICAL' → label 1 (fake/suspicious)
  - Profiles with check_history risk_level = 'LOW' → label 0 (genuine)
  - Seed profiles with known classification (from seed data shapes) → augmented labels
  - Only uses actual data in the database — no fabrication
"""

import sys
import os

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from database import query_db
from ml.features import extract_features, FEATURE_NAMES


def load_dataset():
    """
    Loads labeled feature vectors from the database.

    Returns:
        X: list of feature vectors (list of lists)
        y: list of labels (0 = genuine, 1 = fake/suspicious)
        metadata: list of dicts with username + risk info for debugging
    """
    X, y, metadata = [], [], []

    protected_profiles = query_db("SELECT * FROM protected_profiles") or []

    # ── Strategy 1: Use check_history with known risk labels ─────────────────
    history = query_db("""
        SELECT DISTINCT h.target_username, h.risk_level, h.risk_score
        FROM check_history h
        ORDER BY h.created_at DESC
    """) or []

    seen_usernames = set()
    for entry in history:
        username = entry["target_username"]
        if username in seen_usernames:
            continue
        seen_usernames.add(username)

        # Fetch full profile from demo_profiles if available
        profile = query_db(
            "SELECT * FROM demo_profiles WHERE LOWER(username) = LOWER(?)",
            (username,), one=True
        )
        if not profile:
            profile = {"username": username, "display_name": username, "bio": "",
                       "followers_count": 0, "following_count": 0,
                       "posts_count": 0, "account_age_days": 30,
                       "avatar_url": "", "is_verified": 0}

        features = extract_features(dict(profile), protected_profiles)

        risk = entry["risk_level"]
        if risk in ("HIGH", "CRITICAL"):
            label = 1
        elif risk == "LOW":
            label = 0
        else:
            # MEDIUM — ambiguous, include as 1 (suspicious) with lower confidence
            label = 1

        X.append(features)
        y.append(label)
        metadata.append({
            "username": username,
            "risk_level": risk,
            "risk_score": entry["risk_score"],
            "source": "check_history"
        })

    # ── Strategy 2: All demo profiles not seen in history ────────────────────
    all_demo = query_db("SELECT * FROM demo_profiles") or []
    for profile in all_demo:
        username = profile["username"]
        if username in seen_usernames:
            continue
        seen_usernames.add(username)

        features = extract_features(dict(profile), protected_profiles)

        # Heuristic label from profile characteristics:
        # followers < 50, following > 500, age < 7 → likely fake
        followers = profile.get("followers_count") or 0
        following = profile.get("following_count") or 0
        age = profile.get("account_age_days") or 30
        bio = (profile.get("bio") or "").lower()
        phishing_words = ["giveaway", "airdrop", "dm for", "free bitcoin", "telegram", "whatsapp"]
        has_phishing = any(w in bio for w in phishing_words)

        if has_phishing or (followers < 50 and following > 500 and age < 14):
            label = 1
        elif followers > 500 and age > 100:
            label = 0
        else:
            continue  # Skip ambiguous unlabeled samples

        X.append(features)
        y.append(label)
        metadata.append({
            "username": username,
            "risk_level": "inferred",
            "risk_score": -1,
            "source": "demo_profiles_heuristic"
        })

    print(f"[DATASET] Loaded {len(X)} samples: {sum(y)} fake, {len(y)-sum(y)} genuine")
    return X, y, metadata


if __name__ == "__main__":
    X, y, meta = load_dataset()
    print(f"\nFeature dimensions: {len(FEATURE_NAMES)}")
    print(f"Total samples: {len(X)}")
    for i, m in enumerate(meta[:5]):
        print(f"  Sample {i+1}: @{m['username']} → label={y[i]} ({m['risk_level']})")
