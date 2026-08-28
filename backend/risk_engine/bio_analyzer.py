import re
from .string_metrics import calculate_sequence_similarity

PHISHING_KEYWORDS = [
    r'crypto\s*giveaway',
    r'free\s*(bitcoin|eth|crypto|airdrop|giftcard|tokens)',
    r'\b(airdrop|airdrops)\b',
    r'dm\s*for\s*(promo|collab|invest|details|recovery|vip)',
    r'\bwhatsapp\b',
    r'\btelegram\b',
    r'guaranteed\s*(returns|profit|income|payout)',
    r'official\s*backup\s*account',
    r'backup\s*(page|account)',
    r'click\s*link\s*below',
    r'send\s*\$?\d+\s*to\s*receive',
    r'support\s*desk\s*dm',
    r'binance\s*support',
    r'meta\s*verified\s*agent'
]

def analyze_bio_and_content(target_bio: str, protected_bio: str = None, is_verified: bool = False) -> dict:
    """
    Analyzes bio text for phishing/scam patterns, false verification claims,
    and bio duplication against an authentic protected profile.
    """
    bio = (target_bio or "").strip()
    reasons = []
    score_boost = 0

    if not bio:
        return {
            "score_boost": 5,
            "reasons": ["Empty bio description"],
            "matches": []
        }

    # 1. Phishing & Scam Keyword Patterns
    matched_patterns = []
    for pattern in PHISHING_KEYWORDS:
        if re.search(pattern, bio, re.IGNORECASE):
            matched = re.search(pattern, bio, re.IGNORECASE).group(0)
            matched_patterns.append(matched)

    if matched_patterns:
        points = min(len(matched_patterns) * 12, 35)
        score_boost += points
        reasons.append(f"Bio contains suspicious/phishing trigger keywords: {', '.join(set(matched_patterns))}")

    # 2. False claim of verification / official badge in text
    if not is_verified:
        if re.search(r'(verified\s*account|official\s*page|ceo\s*official)', bio, re.IGNORECASE):
            score_boost += 15
            reasons.append("Unverified profile explicitly claiming 'verified/official' status in bio")

    # 3. Direct Bio Plagiarism / Duplication against protected account
    if protected_bio and len(protected_bio.strip()) >= 15:
        sim = calculate_sequence_similarity(bio, protected_bio)
        if sim >= 0.85:
            score_boost += 25
            reasons.append(f"Bio is {round(sim * 100, 1)}% identical to the protected account's bio (suspected text cloning)")
        elif sim >= 0.65:
            score_boost += 15
            reasons.append(f"Bio closely resembles ({round(sim * 100, 1)}%) the authentic protected account bio")

    return {
        "score_boost": min(score_boost, 35),
        "reasons": reasons,
        "matched_keywords": matched_patterns
    }
