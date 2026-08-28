import difflib
import re

# Common homoglyphs / character substitutions used in typosquatting & impersonation
HOMOGLYPH_MAP = {
    '0': 'o', 'o': '0',
    '1': 'l', 'l': '1', 'i': '1', '1': 'i',
    'm': 'rn', 'rn': 'm',
    'w': 'vv', 'vv': 'w',
    '5': 's', 's': '5',
    '3': 'e', 'e': '3',
    '8': 'b', 'b': '8',
    '@': 'a', 'a': '@'
}

SUSPICIOUS_AFFIXES = [
    'official', 'real', 'the', 'verified', 'support', 'help', 'team',
    'service', 'admin', 'desk', 'secure', 'direct', 'vip', 'claim', 'org'
]

def calculate_sequence_similarity(str1: str, str2: str) -> float:
    """Returns normalized SequenceMatcher ratio between 0.0 and 1.0."""
    if not str1 or not str2:
        return 0.0
    s1 = str1.strip().lower()
    s2 = str2.strip().lower()
    return difflib.SequenceMatcher(None, s1, s2).ratio()

def calculate_levenshtein_distance(str1: str, str2: str) -> int:
    """Computes Levenshtein edit distance between two strings."""
    s1 = (str1 or "").strip().lower()
    s2 = (str2 or "").strip().lower()
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j],      # deletion
                                   dp[i][j - 1],      # insertion
                                   dp[i - 1][j - 1])  # substitution
    return dp[m][n]

def normalize_username_noise(username: str) -> str:
    """Strips separators, numbers, and common impersonation affixes to find the root identity."""
    u = username.lower().strip()
    u = re.sub(r'[_.\-]', '', u)
    for affix in SUSPICIOUS_AFFIXES:
        u = re.sub(r'^' + affix, '', u)
        u = re.sub(affix + r'$', '', u)
    u = re.sub(r'\d+$', '', u)
    return u

def detect_typosquatting(target_user: str, protected_user: str) -> dict:
    """
    Analyzes whether target_user is attempting typosquatting or character mimickry
    against protected_user.
    """
    t = target_user.lower().strip()
    p = protected_user.lower().strip()

    if t == p:
        return {
            "is_typosquat": False,
            "exact_match": True,
            "score_boost": 0,
            "reasons": []
        }

    reasons = []
    score_boost = 0

    # 1. Check SequenceMatcher baseline
    seq_sim = calculate_sequence_similarity(t, p)
    lev_dist = calculate_levenshtein_distance(t, p)

    # 2. Check root stripping
    t_clean = normalize_username_noise(t)
    p_clean = normalize_username_noise(p)

    if t_clean == p_clean and len(p_clean) >= 3:
        score_boost += 35
        reasons.append(f"Root name '{t_clean}' is identical after removing punctuation/affixes/numbers")

    # 3. Check for Suspicious Affixes (e.g., elonmusk_official, real_elonmusk)
    for affix in SUSPICIOUS_AFFIXES:
        pattern1 = f"^{affix}[_.]?{p}$"
        pattern2 = f"^{p}[_.]?{affix}$"
        if re.match(pattern1, t) or re.match(pattern2, t):
            score_boost += 40
            reasons.append(f"Prepended or appended impersonation keyword '{affix}' to authentic handle '@{p}'")
            break

    # 4. Trailing digits check on protected root (e.g. elonmusk1, elonmusk_99)
    if re.match(r'^' + re.escape(p) + r'[_.]?\d+$', t):
        score_boost += 35
        reasons.append(f"Appended trailing numbers to authentic handle '@{p}'")

    # 5. Homoglyph / Character substitution check
    # Check if substituting homoglyphs yields the protected username
    t_sub = t
    for k, v in HOMOGLYPH_MAP.items():
        t_sub = t_sub.replace(k, v)
    p_sub = p
    for k, v in HOMOGLYPH_MAP.items():
        p_sub = p_sub.replace(k, v)

    if (t_sub == p or t == p_sub or t_sub == p_sub) and t != p:
        score_boost += 40
        reasons.append(f"Character homoglyph substitution detected (e.g., 0/o, 1/l, rn/m)")

    # 6. Small Levenshtein distance on short strings
    if lev_dist <= 2 and len(p) >= 4 and not reasons:
        score_boost += 30
        reasons.append(f"Username is within {lev_dist} edit distance of protected handle '@{p}'")
    elif seq_sim >= 0.85 and not reasons:
        score_boost += 25
        reasons.append(f"High username string similarity ({round(seq_sim * 100, 1)}%) to '@{p}'")

    return {
        "is_typosquat": score_boost > 0,
        "exact_match": False,
        "seq_similarity": round(seq_sim, 3),
        "levenshtein_distance": lev_dist,
        "score_boost": min(score_boost, 45),
        "reasons": reasons
    }

def calculate_display_name_similarity(name1: str, name2: str) -> dict:
    """Analyzes similarity between two display names."""
    n1 = (name1 or "").strip().lower()
    n2 = (name2 or "").strip().lower()

    if not n1 or not n2:
        return {"is_similar": False, "score_boost": 0, "reasons": []}

    if n1 == n2:
        return {
            "is_similar": True,
            "exact_match": True,
            "similarity": 1.0,
            "score_boost": 20,
            "reasons": [f"Display name '{name1}' is an exact match to protected name '{name2}'"]
        }

    sim = calculate_sequence_similarity(n1, n2)
    reasons = []
    score_boost = 0

    if sim >= 0.88:
        score_boost = 15
        reasons.append(f"Display name has {round(sim * 100, 1)}% resemblance to protected name '{name2}'")
    elif set(n1.split()) == set(n2.split()) and len(n1.split()) > 1:
        score_boost = 15
        reasons.append(f"Display name contains same words as protected name '{name2}' in reordered sequence")

    return {
        "is_similar": score_boost > 0,
        "exact_match": False,
        "similarity": round(sim, 3),
        "score_boost": score_boost,
        "reasons": reasons
    }

def detect_suspicious_username_patterns(username: str) -> dict:
    """Analyzes username for generic automated bot / phishing patterns."""
    u = (username or "").lower().strip()
    reasons = []
    score_boost = 0

    bot_keywords = [r'_bot\d*$', r'^bot_', r'profit_bot', r'crypto_profit', r'airdrop', r'giveaway', r'free_?crypto', r'support_?desk']
    for pat in bot_keywords:
        if re.search(pat, u):
            score_boost += 15
            reasons.append(f"Username handle matches automated spam/bot pattern ('{pat}')")
            break

    # Excessive trailing random numbers (e.g., user98741235)
    if re.search(r'[a-z]+[0-9]{5,}$', u):
        score_boost += 10
        reasons.append("Username contains high entropy randomized trailing digit sequence")

    return {
        "is_suspicious": score_boost > 0,
        "score_boost": min(score_boost, 20),
        "reasons": reasons
    }

