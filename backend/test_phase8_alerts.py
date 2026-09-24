import os
import unittest
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse
from unittest.mock import MagicMock, patch

import email_utils
from app import app
from database import execute_db, query_db
from routes import monitor_routes
from werkzeug.security import generate_password_hash


class TestPhase8Alerts(unittest.TestCase):
    def _device_fixture(self, suffix):
        username = f"phase8_login_{suffix}"
        demo_id = execute_db(
            "INSERT INTO demo_profiles (username, display_name, password, bio, account_age_days) VALUES (?, ?, ?, ?, ?)",
            (username, "Phase 8 Login", generate_password_hash("Phase8-pass"), "Login test", 100),
        )[0]
        protected_id = execute_db(
            "INSERT INTO protected_profiles (username, display_name, email, bio, is_monitoring_active) VALUES (?, ?, ?, ?, 0)",
            (username, "Phase 8 Login", "owner@example.test", "Login test"),
        )[0]
        return username, demo_id, protected_id

    def _cleanup_device_fixture(self, username, demo_id, protected_id):
        execute_db("DELETE FROM login_history WHERE username = ?", (username,))
        execute_db("DELETE FROM trusted_devices WHERE username = ?", (username,))
        execute_db("DELETE FROM protected_profiles WHERE id = ?", (protected_id,))
        execute_db("DELETE FROM demo_profiles WHERE id = ?", (demo_id,))

    def test_smtp_not_configured_is_non_fatal(self):
        with patch.dict(os.environ, {
            "MAIL_HOST": "", "MAIL_USERNAME": "", "MAIL_PASSWORD": "", "MAIL_FROM": ""
        }, clear=False):
            result = email_utils.send_impersonation_email(
                "owner@example.test", "leodas", "leodass_tech", 75,
                ["Username similarity to @leodas: 96%"],
                classification="FAKE",
                signals={"ml_probability": 0.84, "avatar_similarity": True},
            )
        self.assertEqual(result["status"], "not_configured")
        self.assertFalse(result["sent"])

    @patch.dict(os.environ, {
        "MAIL_HOST": "smtp.example.test", "MAIL_PORT": "587",
        "MAIL_USERNAME": "sender@example.test", "MAIL_PASSWORD": "secret",
        "MAIL_FROM": "sender@example.test", "MAIL_USE_TLS": "true"
    }, clear=False)
    @patch("email_utils.smtplib.SMTP")
    def test_mock_impersonation_email_contains_safe_evidence(self, smtp_class):
        smtp = MagicMock()
        smtp.send_message.return_value = {}
        smtp_class.return_value = smtp

        result = email_utils.send_impersonation_email(
            "owner@example.test", "leodas", "leodass_tech", 75,
            ["Username similarity to @leodas: 96%"],
            classification="FAKE",
            signals={
                "ml_probability": 0.84,
                "username_similarity": 0.9565,
                "avatar_similarity": True,
                "account_age_days": 1,
                "llm_semantic_risk": None,
            },
        )

        self.assertEqual(result["status"], "sent")
        message = smtp.send_message.call_args.args[0]
        body = message.get_content()
        self.assertEqual(message["To"], "owner@example.test")
        self.assertIn("@leodas", body)
        self.assertIn("@leodass_tech", body)
        self.assertIn("75/100", body)
        self.assertIn("84%", body)
        self.assertNotIn("secret", body)
        self.assertNotIn("device_fingerprint", body)
        self.assertNotIn("192.168.", body)

    @patch.dict(os.environ, {
        "MAIL_HOST": "smtp.example.test", "MAIL_PORT": "587",
        "MAIL_USERNAME": "sender@example.test", "MAIL_PASSWORD": "secret",
        "MAIL_FROM": "sender@example.test", "MAIL_USE_TLS": "true"
    }, clear=False)
    @patch("email_utils.smtplib.SMTP", side_effect=OSError("connection refused"))
    def test_smtp_failure_is_reported_without_raising(self, _smtp_class):
        result = email_utils.send_impersonation_email(
            "owner@example.test", "leodas", "leodass_tech", 75, ["High similarity"]
        )
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["sent"])

    @patch.dict(os.environ, {
        "MAIL_HOST": "smtp.example.test", "MAIL_PORT": "587",
        "MAIL_USERNAME": "sender@example.test", "MAIL_PASSWORD": "secret",
        "MAIL_FROM": "sender@example.test", "MAIL_USE_TLS": "true"
    }, clear=False)
    @patch("email_utils.smtplib.SMTP")
    def test_new_device_email_excludes_network_and_device_secrets(self, smtp_class):
        smtp = MagicMock()
        smtp.send_message.return_value = {}
        smtp_class.return_value = smtp

        result = email_utils.send_device_verification_email(
            "owner@example.test", "leodas",
            "https://localhost/verify-device?token=test-token",
            ip_address="192.168.1.44",
            user_agent="private-device-agent",
        )

        self.assertEqual(result["status"], "sent")
        body = smtp.send_message.call_args.args[0].get_content()
        self.assertIn("New untrusted device login", body)
        self.assertNotIn("192.168.1.44", body)
        self.assertNotIn("private-device-agent", body)

    @patch.object(monitor_routes, "execute_db")
    @patch.object(monitor_routes, "send_impersonation_email", return_value={"sent": False, "status": "not_configured"})
    def test_monitor_dispatch_returns_not_configured(self, _send, execute_db):
        alert = {
            "id": 17,
            "email": "owner@example.test",
            "protected_username": "leodas",
            "demo_username": "leodass_tech",
            "classification": "FAKE",
            "risk_score": 75,
            "created_at": "2026-09-24 12:00:00",
            "reason_summary": "High username similarity",
            "evidence_json": '{"ml_probability": 0.84}',
            "email_status": "skipped",
        }
        result = monitor_routes._dispatch_alert_email(alert)
        self.assertEqual(result["status"], "not_configured")
        execute_db.assert_called_once()

    @patch.object(monitor_routes, "execute_db")
    @patch.object(monitor_routes, "send_impersonation_email", return_value={"sent": True, "status": "sent"})
    def test_monitor_dispatch_prevents_sent_duplicate(self, send_email, execute_db):
        alert = {
            "id": 18,
            "email": "owner@example.test",
            "protected_username": "leodas",
            "demo_username": "leodass_tech",
            "classification": "FAKE",
            "risk_score": 75,
            "reason_summary": "High username similarity",
            "evidence_json": "{}",
            "email_status": "sent",
        }
        result = monitor_routes._dispatch_alert_email(alert)
        self.assertEqual(result["status"], "duplicate")
        send_email.assert_not_called()
        execute_db.assert_not_called()

    def test_monitor_email_gate_uses_unified_classification(self):
        protected = {"id": 91, "username": "protected_user", "is_monitoring_active": 1}
        demo = {"id": 92, "username": "detected_user"}
        alert_row = {
            "id": 301,
            "email": "owner@example.test",
            "protected_username": "protected_user",
            "demo_username": "detected_user",
            "classification": "FAKE",
            "risk_score": 75,
            "risk_level": "HIGH",
            "reason_summary": "Actual detection reason",
            "evidence_json": "{}",
            "email_status": "skipped",
            "created_at": "2026-09-24 12:00:00",
        }
        for classification in ("REAL", "SUSPICIOUS", "FAKE"):
            with self.subTest(classification=classification):
                analysis = {
                    "classification": classification,
                    "risk_score": 10 if classification == "REAL" else 50 if classification == "SUSPICIOUS" else 75,
                    "risk_level": "LOW" if classification == "REAL" else "MEDIUM" if classification == "SUSPICIOUS" else "HIGH",
                    "primary_match": {"username": "protected_user"},
                    "factors": [{"description": "Actual detection reason"}],
                    "signals": {"ml_probability": 0.8},
                }

                def fake_query(query, args=(), one=False):
                    if "FROM protected_profiles" in query:
                        return [protected]
                    if "SELECT * FROM demo_profiles" in query:
                        return [demo]
                    if "SELECT protected_profile_id" in query:
                        return []
                    return alert_row

                with patch.object(monitor_routes, "query_db", side_effect=fake_query), \
                        patch.object(monitor_routes, "execute_db", return_value=(301, 1)), \
                        patch.object(monitor_routes, "detect_profile", return_value=analysis), \
                        patch.object(monitor_routes, "send_impersonation_email", return_value={"sent": True, "status": "sent"}) as send_email:
                    response = app.test_client().post("/api/monitor-username", json={"username": "protected_user"})

                if classification == "REAL":
                    self.assertEqual(response.get_json()["new_alerts_count"], 0)
                    send_email.assert_not_called()
                else:
                    self.assertEqual(response.get_json()["new_alerts_count"], 1)
                    send_email.assert_called_once()

    def test_trusted_device_allows_login_without_email(self):
        username, demo_id, protected_id = self._device_fixture("trusted")
        try:
            with patch("routes.security_routes.send_device_verification_email") as send_email:
                with app.test_client() as client:
                    response = client.post(
                        "/api/demo-login",
                        json={"username": username, "password": "Phase8-pass"},
                        headers={"User-Agent": "trusted-device"},
                    )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["status"], "success")
            send_email.assert_not_called()
        finally:
            self._cleanup_device_fixture(username, demo_id, protected_id)

    def test_unknown_device_approve_deny_expiry_and_reuse(self):
        username, demo_id, protected_id = self._device_fixture("authorization")
        try:
            captured = {}

            def capture_email(**kwargs):
                captured.update(kwargs)
                return {"sent": True, "status": "sent"}

            with patch("routes.security_routes.send_device_verification_email", side_effect=capture_email):
                with app.test_client() as client:
                    first = client.post(
                        "/api/demo-login", json={"username": username, "password": "Phase8-pass"},
                        headers={"User-Agent": "device-a"},
                    )
                    pending = client.post(
                        "/api/demo-login", json={"username": username, "password": "Phase8-pass"},
                        headers={"User-Agent": "device-b"},
                    )
                    self.assertEqual(first.get_json()["status"], "success")
                    self.assertEqual(pending.status_code, 202)
                    self.assertEqual(pending.get_json()["email_result"]["status"], "sent")
                    token = parse_qs(urlparse(captured["verify_link"]).query)["token"][0]

                    approved = client.get(f"/api/device-authorization/approve?token={token}")
                    reused = client.get(f"/api/device-authorization/approve?token={token}")
                    completed = client.post(
                        "/api/demo-login", json={"username": username, "password": "Phase8-pass"},
                        headers={"User-Agent": "device-b"},
                    )
                    self.assertEqual(approved.status_code, 200)
                    self.assertEqual(approved.get_json()["decision"], "approved")
                    self.assertEqual(reused.status_code, 400)
                    self.assertEqual(completed.get_json()["status"], "success")

                    denied_capture = {}

                    def capture_denial(**kwargs):
                        denied_capture.update(kwargs)
                        return {"sent": True, "status": "sent"}

                    with patch("routes.security_routes.send_device_verification_email", side_effect=capture_denial):
                        denied_pending = client.post(
                            "/api/demo-login", json={"username": username, "password": "Phase8-pass"},
                            headers={"User-Agent": "device-c"},
                        )
                    denied_token = parse_qs(urlparse(denied_capture["deny_link"]).query)["token"][0]
                    denied = client.get(f"/api/device-authorization/deny?token={denied_token}")
                    denied_reuse = client.get(f"/api/device-authorization/deny?token={denied_token}")
                    self.assertEqual(denied_pending.status_code, 202)
                    self.assertEqual(denied.get_json()["decision"], "denied")
                    self.assertEqual(denied_reuse.status_code, 400)

                    expired_capture = {}

                    def capture_expiry(**kwargs):
                        expired_capture.update(kwargs)
                        return {"sent": True, "status": "sent"}

                    with patch("routes.security_routes.send_device_verification_email", side_effect=capture_expiry):
                        client.post(
                            "/api/demo-login", json={"username": username, "password": "Phase8-pass"},
                            headers={"User-Agent": "device-d"},
                        )
                    expired_token = parse_qs(urlparse(expired_capture["verify_link"]).query)["token"][0]
                    execute_db(
                        "UPDATE login_history SET verification_expires_at = ? WHERE username = ? AND authorization_status = 'PENDING'",
                        (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1), username),
                    )
                    expired = client.get(f"/api/device-authorization/approve?token={expired_token}")
                    self.assertEqual(expired.status_code, 400)
        finally:
            self._cleanup_device_fixture(username, demo_id, protected_id)

    def test_smtp_unavailable_keeps_unknown_device_blocked(self):
        username, demo_id, protected_id = self._device_fixture("offline")
        try:
            with patch("routes.security_routes.send_device_verification_email", return_value={"sent": False, "status": "not_configured"}):
                with app.test_client() as client:
                    client.post(
                        "/api/demo-login", json={"username": username, "password": "Phase8-pass"},
                        headers={"User-Agent": "device-a"},
                    )
                    pending = client.post(
                        "/api/demo-login", json={"username": username, "password": "Phase8-pass"},
                        headers={"User-Agent": "device-b"},
                    )
            self.assertEqual(pending.status_code, 202)
            self.assertEqual(pending.get_json()["status"], "verification_required")
            self.assertEqual(pending.get_json()["email_result"]["status"], "not_configured")
        finally:
            self._cleanup_device_fixture(username, demo_id, protected_id)


if __name__ == "__main__":
    unittest.main()
