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


def _analyze_with_gemini(bio: str, username: str, display_name: str) -> dict:
    """Calls Google Gemini API for semantic impersonation analysis."""
    try:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""You are a cybersecurity analyst specializing in fake profile and impersonation detection.

Analyze the following social media profile for fake/impersonation signals:

Username: {username}
Display Name: {display_name}
Bio: {bio}

Respond ONLY with a valid JSON object (no markdown, no explanation):
{{
  "phishing_intent_score": <float 0.0-1.0>,
  "impersonation_claim": <true|false>,
  "rationale": "<brief 1-2 sentence explanation>"
}}

Guidelines:
- phishing_intent_score: 0.0 = clearly genuine, 1.0 = clear phishing/scam
- impersonation_claim: true if bio/username explicitly claims to be a famous person or official account
- Keep rationale factual and concise"""

        response = model.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown code fences if present
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        result = json.loads(text)
        return _validate_result(result)

    except Exception as e:
        print(f"[LLM] Gemini analysis failed: {e}")
        return None


def _analyze_with_openai(bio: str, username: str, display_name: str) -> dict:
    """Calls OpenAI API for semantic impersonation analysis."""
    try:
        import openai
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return None

        client = openai.OpenAI(api_key=api_key)
        prompt = f"""You are a cybersecurity analyst specializing in fake profile detection.

Analyze this social media profile:
Username: {username}
Display Name: {display_name}  
Bio: {bio}

Respond ONLY with JSON (no markdown):
{{"phishing_intent_score": <0.0-1.0>, "impersonation_claim": <true|false>, "rationale": "<brief>"}}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.1
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        result = json.loads(text)
        return _validate_result(result)

    except Exception as e:
        print(f"[LLM] OpenAI analysis failed: {e}")
        return None


def _validate_result(result: dict) -> dict:
    """Validates and sanitises LLM response."""
    score = float(result.get("phishing_intent_score", 0.0))
    score = max(0.0, min(1.0, score))
    return {
        "phishing_intent_score": round(score, 3),
        "impersonation_claim": bool(result.get("impersonation_claim", False)),
        "rationale": str(result.get("rationale", ""))[:500],
    }


def _not_configured() -> dict:
    """Returned when no LLM API key is present."""
    return {
        "phishing_intent_score": 0.0,
        "impersonation_claim": False,
        "rationale": "LLM content analysis not configured (no API key set).",
        "llm_used": None,
    }


def analyze_content(bio: str, username: str = "", display_name: str = "") -> dict:
    """
    Main entry point. Analyzes bio/username for semantic impersonation signals.

    Returns:
        {
          "phishing_intent_score": float,   # 0.0–1.0
          "impersonation_claim": bool,
          "rationale": str,
          "llm_used": str | None
        }
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
            return result

    # Fallback to OpenAI
    if os.getenv("OPENAI_API_KEY", "").strip():
        result = _analyze_with_openai(bio, username, display_name)
        if result:
            result["llm_used"] = "openai"
            return result

    return _not_configured()
