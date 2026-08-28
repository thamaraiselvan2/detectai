import os
import smtplib
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


def send_impersonation_email(recipient, protected_username, new_username, risk_score, reasons):
    """Send one security email using SMTP settings supplied through the environment."""
    host = os.getenv("MAIL_HOST", "").strip()
    username = os.getenv("MAIL_USERNAME", "").strip()
    password = os.getenv("MAIL_PASSWORD", "")
    sender = os.getenv("MAIL_FROM", username).strip()
    port = int(os.getenv("MAIL_PORT", "587"))
    use_tls = os.getenv("MAIL_USE_TLS", "true").lower() == "true"

    if not recipient or "@" not in recipient:
        return {"sent": False, "status": "invalid_recipient", "message": "Registered profile has no valid email address."}
    smtp_config = {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "sender": sender,
        "use_tls": use_tls
    }
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
    message["Subject"] = "Potential Fake Profile Detected"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(f"""Hello,

A new social media profile has been detected that appears to closely resemble your protected profile.

Protected profile:
{protected_username}

New profile detected:
{new_username}

Reason:
{' '.join(reasons)}

Risk score:
{risk_score}

Please review this profile and take appropriate action if necessary.

This is an automated security alert from Fake Profile Detector.
""")

    smtp = None
    try:
        smtp = smtplib.SMTP(host, port, timeout=20)
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(username, password)
        refused_recipients = smtp.send_message(message)
        smtp.quit()
        if refused_recipients:
            return {
                "sent": False,
                "status": "failed",
                "exception_type": "SMTPRecipientsRefused",
                "message": f"SMTP refused recipient(s): {', '.join(refused_recipients)}"
            }
        return {"sent": True, "status": "sent"}
    except (OSError, smtplib.SMTPException) as error:
        if smtp is not None:
            try:
                smtp.quit()
            except (OSError, smtplib.SMTPException):
                pass
        return {
            "sent": False,
            "status": "failed",
            "exception_type": type(error).__name__,
            "message": str(error)
        }