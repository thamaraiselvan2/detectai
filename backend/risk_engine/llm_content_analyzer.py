"""
LLM Content Analyzer for semantic bio/username analysis.

Uses OpenAI or Google Gemini API if configured via environment variables.
Runs alongside (NOT instead of) the existing rule-based bio_analyzer.

Environment variables:
  OPENAI_API_KEY   — enables OpenAI GPT analysis
  GEMINI_API_KEY   — enables Google Gemini analysis (preferred)

Returns structured JSON — never crashes the detection pipeline.
"""

import os
import json
import re


def _provider_prompt(prompt: str) -> dict:
    """Call the configured provider once and return parsed JSON, or None."""
    try:
        if os.getenv("GEMINI_API_KEY", "").strip():
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY").strip())
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            text = response.text.strip()
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            return json.loads(text), "gemini"

        if os.getenv("OPENAI_API_KEY", "").strip():
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY").strip())
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1,
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            return json.loads(text), "openai"
    except Exception as error:
        print(f"[LLM] Provider request failed: {type(error).__name__}: {error}")
    return None


def _analyze_with_gemini(bio: str, username: str, display_name: str) -> dict:
    """Calls Google Gemini API for semantic impersonation analysis."""
    try:
        prompt = f"""You are a cybersecurity analyst specializing in fake profile and impersonation detection.

Analyze the following social media profile for fake/impersonation signals:

Username: {username}
Display Name: {display_name}
Bio: {bio}

Respond ONLY with a valid JSON object (no markdown, no explanation):
{{
    "semantic_risk": <float 0.0-1.0>,
    "phishing_intent_score": <float 0.0-1.0>,
    "impersonation_claim": <true|false>,
    "impersonation_indicators": ["<indicator>"],
    "phishing_indicators": ["<indicator>"],
    "explanation": "<brief evidence-based explanation>"
}}

Guidelines:
- phishing_intent_score: 0.0 = clearly genuine, 1.0 = clear phishing/scam
- semantic_risk must reflect only the supplied username, display name, and bio.
- impersonation_claim: true if bio/username explicitly claims to be a famous person or official account
- Keep explanation factual and concise. Do not invent profile facts."""
        response = _provider_prompt(prompt)
        return _validate_result(response[0]) if response else None

    except Exception as e:
        print(f"[LLM] Gemini analysis failed: {e}")
        return None


def _analyze_with_openai(bio: str, username: str, display_name: str) -> dict:
    """Calls OpenAI API for semantic impersonation analysis."""
    try:
        prompt = f"""You are a cybersecurity analyst specializing in fake profile detection.

Analyze this social media profile:
Username: {username}
Display Name: {display_name}  
Bio: {bio}

Respond ONLY with JSON (no markdown):
{{"semantic_risk": <0.0-1.0>, "phishing_intent_score": <0.0-1.0>, "impersonation_claim": <true|false>, "impersonation_indicators": [], "phishing_indicators": [], "explanation": "<brief evidence-based explanation>"}}
Do not invent profile facts."""
        response = _provider_prompt(prompt)
        return _validate_result(response[0]) if response else None

    except Exception as e:
        print(f"[LLM] OpenAI analysis failed: {e}")
        return None


def _validate_result(result: dict) -> dict:
    """Validates and sanitises LLM response."""
    score = float(result.get("semantic_risk", result.get("phishing_intent_score", 0.0)))
    score = max(0.0, min(1.0, score))
    phishing_score = float(result.get("phishing_intent_score", score))
    phishing_score = max(0.0, min(1.0, phishing_score))
    to_indicators = lambda value: [str(item)[:200] for item in value[:5]] if isinstance(value, list) else []
    explanation = str(result.get("explanation", result.get("rationale", "")))[:500]
    return {
        "semantic_risk": round(score, 3),
        "phishing_intent_score": round(phishing_score, 3),
        "impersonation_claim": bool(result.get("impersonation_claim", False)),
        "impersonation_indicators": to_indicators(result.get("impersonation_indicators", [])),
        "phishing_indicators": to_indicators(result.get("phishing_indicators", [])),
        "explanation": explanation,
        "rationale": explanation,
    }


def _not_configured() -> dict:
    """Returned when no LLM API key is present."""
    return {
        "llm_status": "unavailable",
        "semantic_risk": None,
        "phishing_intent_score": None,
        "impersonation_claim": False,
        "impersonation_indicators": [],
        "phishing_indicators": [],
        "explanation": None,
        "rationale": "LLM content analysis unavailable (no API key set).",
        "llm_used": None,
    }


def analyze_content(bio: str, username: str = "", display_name: str = "") -> dict:
    """
    Main entry point. Analyzes bio/username for semantic impersonation signals.

        Returns structured semantic analysis or ``llm_status=unavailable``.
    Never raises an exception — always returns a safe dict.
    """
    bio = (bio or "").strip()
    username = (username or "").strip()
    display_name = (display_name or "").strip()

    # No meaningful content to analyze
    if not bio and not username:
        return _not_configured()

    # Try Gemini first (preferred — free tier available)
    if os.getenv("GEMINI_API_KEY", "").strip():
        result = _analyze_with_gemini(bio, username, display_name)
        if result:
            result["llm_used"] = "gemini"
            result["llm_status"] = "available"
            return result

    # Fallback to OpenAI
    if os.getenv("OPENAI_API_KEY", "").strip():
        result = _analyze_with_openai(bio, username, display_name)
        if result:
            result["llm_used"] = "openai"
            result["llm_status"] = "available"
            return result

    return _not_configured()


def generate_explanation(signals: dict) -> dict:
    """Generate an explanation from already-computed backend signals only."""
    safe_signals = {
        "classification": signals.get("classification"),
        "risk_score": signals.get("risk_score"),
        "ml_probability": signals.get("ml_probability"),
        "username_similarity": signals.get("username_similarity"),
        "profile_similarity": signals.get("profile_similarity"),
        "avatar_similarity": signals.get("avatar_similarity"),
        "account_age_days": signals.get("account_age_days"),
        "behavioral_signals": signals.get("behavioral_signals", {}),
        "ip_signal": signals.get("ip_signal"),
        "device_signal": signals.get("device_signal"),
        "reasons": signals.get("reasons", []),
    }
    if not (os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip()):
        return {"llm_status": "unavailable", "llm_used": None, "explanation": None}

    prompt = """You explain a fake-profile detection result using only the supplied backend signals.
Do not invent facts, add evidence, or change the classification. Return JSON only:
{"explanation":"<concise evidence-based explanation>"}

Backend signals:
""" + json.dumps(safe_signals, ensure_ascii=True)
    response = _provider_prompt(prompt)
    if not response or not isinstance(response[0], dict):
        return {"llm_status": "unavailable", "llm_used": None, "explanation": None}
    explanation = str(response[0].get("explanation", ""))[:800].strip()
    if not explanation:
        return {"llm_status": "unavailable", "llm_used": None, "explanation": None}
    return {"llm_status": "available", "llm_used": response[1], "explanation": explanation}
