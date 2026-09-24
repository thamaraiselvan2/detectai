import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage


def get_email_configuration_status():
    """Returns safe configuration diagnostics without exposing credentials."""
    return {
        "MAIL_HOST": bool(os.getenv("MAIL_HOST", "").strip()),
        "MAIL_PORT": bool(os.getenv("MAIL_PORT", "").strip()),
        "MAIL_USERNAME": bool(os.getenv("MAIL_USERNAME", "").strip()),
        "MAIL_PASSWORD": bool(os.getenv("MAIL_PASSWORD", "")),
        "MAIL_FROM": bool(os.getenv("MAIL_FROM", "").strip()),
        "MAIL_USE_TLS": bool(os.getenv("MAIL_USE_TLS", "").strip())
    }


def _smtp_settings():
    """Return SMTP settings without exposing secrets or raising on bad config."""
    host = os.getenv("MAIL_HOST", "").strip()
    username = os.getenv("MAIL_USERNAME", "").strip()
    password = os.getenv("MAIL_PASSWORD", "")
    sender = os.getenv("MAIL_FROM", username).strip()
    try:
        port = int(os.getenv("MAIL_PORT", "587"))
    except (TypeError, ValueError):
        port = 587
    use_tls = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "sender": sender,
        "use_tls": use_tls,
    }


def _send_smtp_message(message, settings):
    """Send a message and return a safe delivery result."""
    smtp = None
    try:
        smtp = smtplib.SMTP(settings["host"], settings["port"], timeout=20)
        smtp.ehlo()
        if settings["use_tls"]:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(settings["username"], settings["password"])
        refused_recipients = smtp.send_message(message)
        smtp.quit()
        if refused_recipients:
            return {"sent": False, "status": "failed", "exception_type": "SMTPRecipientsRefused"}
        return {"sent": True, "status": "sent"}
    except Exception as error:
        if smtp is not None:
            try:
                smtp.quit()
            except Exception:
                pass
        print(f"[EMAIL] SMTP delivery failed: {type(error).__name__}: {error}", flush=True)
        return {"sent": False, "status": "failed", "exception_type": type(error).__name__}


def _safe_signal_lines(signals):
    """Format only detection signals produced by the unified pipeline."""
    if not isinstance(signals, dict):
        return []
    labels = {
        "ml_probability": "ML fake probability",
        "username_similarity": "Username similarity",
        "display_name_similarity": "Display-name similarity",
        "bio_similarity": "Bio similarity",
        "avatar_similarity": "Avatar similarity",
        "account_age_days": "Account age",
        "behavior_score": "Behavior signal score",
        "identity_score": "Identity signal score",
        "llm_semantic_risk": "LLM semantic risk",
    }
    lines = []
    for key, label in labels.items():
        value = signals.get(key)
        if value is None:
            continue
        if key.endswith("_similarity") or key in {"ml_probability", "llm_semantic_risk"}:
            value = f"{float(value):.0%}"
        elif key == "avatar_similarity":
            value = "match" if value else "no match"
        elif key == "account_age_days":
            value = f"{value} days"
        lines.append(f"- {label}: {value}")
    return lines


def send_impersonation_email(
    recipient,
    protected_username,
    new_username,
    risk_score,
    reasons,
    classification="FAKE",
    signals=None,
    detected_at=None,
):
    """Send one safe security alert using SMTP settings from the environment."""
    settings = _smtp_settings()

    if not recipient or "@" not in recipient:
        return {"sent": False, "status": "invalid_recipient", "message": "Registered profile has no valid email address."}
    smtp_config = settings
    print({
        "smtp_host_present": bool(smtp_config["host"]),
        "smtp_port_present": bool(os.getenv("MAIL_PORT", "").strip()),
        "smtp_username_present": bool(smtp_config["username"]),
        "smtp_password_present": bool(smtp_config["password"]),
        "smtp_from_present": bool(smtp_config["sender"]),
        "smtp_tls_present": bool(os.getenv("MAIL_USE_TLS", "").strip())
    }, flush=True)
    if not smtp_config["host"] or not smtp_config["sender"] or not smtp_config["username"] or not smtp_config["password"]:
        return {"sent": False, "status": "not_configured", "message": "Authenticated email delivery is not configured."}

    message = EmailMessage()
    message["Subject"] = "DetectAI Security Alert - Possible Profile Impersonation Detected"
    message["From"] = settings["sender"]
    message["To"] = recipient
    signal_lines = _safe_signal_lines(signals)
    reason_lines = [f"- {str(reason)[:300]}" for reason in (reasons or [])[:8]]
    message.set_content(f"""Hello,

DetectAI detected a potentially suspicious profile associated with your protected account.

Protected account: @{protected_username}
Detected profile: @{new_username}
Classification: {classification}
Risk score: {risk_score}/100
Detected at: {detected_at or datetime.now(timezone.utc).isoformat(timespec="seconds")}

Detection signals:
{chr(10).join(signal_lines) if signal_lines else "- No additional signal detail was available"}

Reasons:
{chr(10).join(reason_lines) if reason_lines else "- No additional reason was recorded"}

Please review this profile in the DetectAI monitoring dashboard.

This email is an automated security notification from DetectAI.
""")
    return _send_smtp_message(message, settings)


def send_device_verification_email(
    recipient,
    username,
    verify_link,
    ip_address="unknown",
    user_agent="unknown",
    deny_link=None,
    network_hint="unknown network",
    device_hint="new browser or device",
):
    """Sends a new-device login verification email using SMTP environment settings."""
    settings = _smtp_settings()

    if not recipient or "@" not in recipient:
        return {"sent": False, "status": "invalid_recipient"}

    if not settings["host"] or not settings["sender"] or not settings["username"] or not settings["password"]:
        # Email not configured — return demo-mode result
        return {"sent": False, "status": "not_configured",
                "message": "SMTP not configured. Set MAIL_HOST, MAIL_USERNAME, MAIL_PASSWORD env vars."}

    message = EmailMessage()
    message["Subject"] = f"[Security Alert] New Device Login for @{username}"
    message["From"] = settings["sender"]
    message["To"] = recipient
    message.set_content(f"""Hello,

A new device has attempted to log in to your account @{username}.

Security event: New untrusted device login
Detected at: {datetime.now(timezone.utc).isoformat(timespec="seconds")}
Approximate network: {network_hint}
Device: {device_hint}
Verification status: Verification is required before this device can be trusted.

If this was you, approve this login request:
{verify_link}

If this was not you, deny this login request:
{deny_link or "Use the security settings in DetectAI to deny this request."}

If you did NOT attempt this login, you can safely ignore this email.
Your account remains protected and the new device will NOT be granted access
until verification is completed.

This is an automated security alert from Fake Profile Detector.
""")
    return _send_smtp_message(message, settings)