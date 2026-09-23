"""
Unified detection orchestrator for fake profile analysis.

This is the single function both instant-check and monitoring routes call.
Combines:
  1. Existing rule-based risk engine (analyze_profile_risk)
  2. ML model prediction (if trained)
  3. LLM semantic analysis (if configured)
  4. Plain-language explainability output

Both profile_routes.py and monitor_routes.py call detect_profile() — same pipeline.
"""

from .scoring import analyze_profile_risk, generate_recommendation

# ML pipeline — graceful fallback if not available
try:
    import sys, os
    _BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _BACKEND not in sys.path:
        sys.path.insert(0, _BACKEND)
    from ml.features import extract_features
    from ml.predictor import predict as ml_predict, get_model_info
    _ML_AVAILABLE = True
except Exception:
    _ML_AVAILABLE = False

from .llm_content_analyzer import analyze_content as llm_analyze


def detect_profile(
    target_profile: dict,
    protected_profiles: list = None,
    ip_signal: float = 0.0,
    device_signal: float = 0.0,
    use_llm: bool = True,
) -> dict:
    """
    Master detection function — call this from both instant-check and monitoring.

    Args:
        target_profile: dict with username, display_name, bio, followers_count, etc.
        protected_profiles: list of protected profile dicts to compare against
        ip_signal: 0.0–1.0 IP suspicion score from security layer
        device_signal: 0.0–1.0 device suspicion score from security layer
        use_llm: whether to invoke LLM analysis (set False for monitoring to save cost)

    Returns:
        Enriched result dict that is backward-compatible with the existing API response.
    """
    protected_profiles = protected_profiles or []

    # ── Step 1: Existing Rule-Based Risk Engine ────────────────────────────────
    analysis = analyze_profile_risk(target_profile, protected_profiles)
    risk_score = analysis["risk_score"]
    risk_level = analysis["risk_level"]
    factors = analysis.get("factors", [])

    # ── Step 2: Security Signals (IP + Device) ────────────────────────────────
    security_boost = 0
    security_factors = []

    if device_signal > 0.7:
        security_boost += 10
        security_factors.append({
            "category": "Device Security",
            "points": 10,
            "severity": "high",
            "description": f"Login from unrecognized/unverified device (signal: {device_signal:.2f})"
        })
    elif device_signal > 0.4:
        security_boost += 5
        security_factors.append({
            "category": "Device Security",
            "points": 5,
            "severity": "medium",
            "description": f"New device detected for this account (signal: {device_signal:.2f})"
        })

    if ip_signal > 0.6:
        security_boost += 5
        security_factors.append({
            "category": "Network Signal",
            "points": 5,
            "severity": "medium",
            "description": f"IP address pattern flagged as potentially suspicious (signal: {ip_signal:.2f})"
        })

    if security_factors:
        risk_score = min(100, risk_score + security_boost)
        factors.extend(security_factors)

    # ── Step 3: ML Model Prediction ───────────────────────────────────────────
    ml_result = None
    if _ML_AVAILABLE:
        try:
            feature_vector = extract_features(
                target_profile, protected_profiles,
                ip_signal=ip_signal, device_signal=device_signal
            )
            ml_result = ml_predict(feature_vector)
        except Exception as e:
            print(f"[DETECTOR] ML prediction failed (non-fatal): {e}")

    # If ML score is high, blend a small boost into risk_score
    if ml_result and ml_result.get("ml_probability") is not None:
        ml_prob = ml_result["ml_probability"]
        if ml_prob >= 0.75:
            ml_boost = int((ml_prob - 0.5) * 20)  # max +10 pts at prob=1.0
            risk_score = min(100, risk_score + ml_boost)
            factors.append({
                "category": "ML Model Signal",
                "points": ml_boost,
                "severity": "medium",
                "description": f"Machine learning model flagged this profile ({ml_prob:.0%} fake probability)"
            })

    # ── Step 4: LLM Semantic Analysis ─────────────────────────────────────────
    llm_result = None
    if use_llm:
        try:
            llm_result = llm_analyze(
                bio=target_profile.get("bio", ""),
                username=target_profile.get("username", ""),
                display_name=target_profile.get("display_name", ""),
            )
            if llm_result and llm_result.get("phishing_intent_score", 0) > 0.6:
                llm_boost = int(llm_result["phishing_intent_score"] * 15)
                risk_score = min(100, risk_score + llm_boost)
                factors.append({
                    "category": "LLM Semantic Analysis",
                    "points": llm_boost,
                    "severity": "high" if llm_result["phishing_intent_score"] > 0.8 else "medium",
                    "description": f"AI semantic analysis detected suspicious content: {llm_result.get('rationale', '')}"
                })
            if llm_result and llm_result.get("impersonation_claim"):
                risk_score = min(100, risk_score + 10)
                factors.append({
                    "category": "LLM Semantic Analysis",
                    "points": 10,
                    "severity": "high",
                    "description": "AI detected explicit impersonation claim in bio or display name"
                })
        except Exception as e:
            print(f"[DETECTOR] LLM analysis failed (non-fatal): {e}")

    # ── Step 5: Recalculate risk level after all boosts ───────────────────────
    if risk_score >= 80:
        risk_level = "CRITICAL"
    elif risk_score >= 60:
        risk_level = "HIGH"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    recommendation = generate_recommendation(risk_level, analysis.get("primary_match"))

    # ── Step 6: Plain-Language Explanation ────────────────────────────────────
    explanation = _build_explanation(
        risk_level, risk_score, factors, ml_result, llm_result,
        device_signal, ip_signal, analysis.get("primary_match")
    )

    # Return enriched result — backward-compatible (same top-level keys as before)
    return {
        # ── Existing keys (unchanged format) ──────────────────────────────────
        "risk_score": risk_score,
        "risk_level": risk_level,
        "primary_match": analysis.get("primary_match"),
        "similar_profiles": analysis.get("similar_profiles", []),
        "factors": factors,
        "recommendation": recommendation,
        "behavior_metrics": analysis.get("behavior_metrics", {}),
        # ── New enrichment keys ────────────────────────────────────────────────
        "ml_result": ml_result,
        "llm_result": llm_result,
        "explanation": explanation,
        "security_signals": {
            "ip_signal": ip_signal,
            "device_signal": device_signal,
        }
    }


def _build_explanation(
    risk_level: str,
    risk_score: int,
    factors: list,
    ml_result: dict,
    llm_result: dict,
    device_signal: float,
    ip_signal: float,
    primary_match: dict,
) -> dict:
    """Generates a human-readable explanation without exposing raw ML internals."""

    verdict_map = {
        "CRITICAL": "Very likely fake / impersonation",
        "HIGH":     "Likely fake or suspicious",
        "MEDIUM":   "Moderately suspicious",
        "LOW":      "Appears genuine"
    }
    verdict = verdict_map.get(risk_level, "Unknown")

    # Top 3 human-readable reasons from factor list
    top_reasons = []
    for factor in sorted(factors, key=lambda f: f.get("points", 0), reverse=True)[:4]:
        desc = factor.get("description", "")
        if desc and desc not in top_reasons:
            top_reasons.append(desc)
    top_reasons = top_reasons[:3]

    # Device note
    device_note = None
    if device_signal > 0.4:
        device_note = "New device detected. Verification email sent to registered address."

    # ML confidence note (shown only if model is available)
    ml_confidence = None
    if ml_result and ml_result.get("ml_probability") is not None:
        ml_confidence = ml_result["ml_probability"]

    # LLM note
    llm_note = None
    if llm_result and llm_result.get("llm_used") and llm_result.get("rationale"):
        if llm_result.get("phishing_intent_score", 0) > 0.3:
            llm_note = llm_result["rationale"]

    # Targeted profile note
    target_note = None
    if primary_match:
        target_note = f"Targeting protected account @{primary_match.get('username', '')}"

    return {
        "verdict": verdict,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "top_reasons": top_reasons,
        "device_note": device_note,
        "ml_confidence": ml_confidence,
        "llm_note": llm_note,
        "target_note": target_note,
    }
