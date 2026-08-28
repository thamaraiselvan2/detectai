import unittest
from unittest.mock import MagicMock, patch
import email_utils
from risk_engine.scoring import (
    analyze_profile_risk,
    analyze_demo_profile_similarity,
    detect_registered_impersonation,
)
from risk_engine.string_metrics import (
    calculate_sequence_similarity,
    calculate_levenshtein_distance,
    detect_typosquatting,
    calculate_display_name_similarity
)
from seed_data import PROTECTED_SEED_PROFILES

class TestRiskEngine(unittest.TestCase):

    def test_string_metrics_typosquat(self):
        # Test 1: Typosquat with prefix/suffix
        res = detect_typosquatting("elonmusk_official", "elonmusk")
        self.assertTrue(res["is_typosquat"])
        self.assertGreaterEqual(res["score_boost"], 35)

        # Test 2: Character homoglyphs (e.g. 0 for o)
        res_homo = detect_typosquatting("el0nmusk", "elonmusk")
        self.assertTrue(res_homo["is_typosquat"])

        # Test 3: Unrelated handle
        res_diff = detect_typosquatting("alex_chen", "elonmusk")
        self.assertFalse(res_diff["is_typosquat"])

    def test_benign_profile_scoring(self):
        profile = {
            "username": "alex_tech_dev",
            "display_name": "Alex Chen",
            "bio": "Full-stack engineer building AI interfaces.",
            "avatar_url": "https://example.com/avatar.jpg",
            "followers_count": 1420,
            "following_count": 390,
            "posts_count": 156,
            "account_age_days": 820,
            "is_verified": False
        }
        res = analyze_profile_risk(profile, PROTECTED_SEED_PROFILES)
        self.assertEqual(res["risk_level"], "LOW")
        self.assertLess(res["risk_score"], 30)

    def test_critical_impersonator_scoring(self):
        profile = {
            "username": "elonmusk_official",
            "display_name": "Elon Musk",
            "bio": "CEO of Tesla & X. Special Crypto Giveaway happening now! Click link below. Free Bitcoin distribution.",
            "avatar_url": "https://example.com/avatar.jpg",
            "followers_count": 14,
            "following_count": 1820,
            "posts_count": 2,
            "account_age_days": 2,
            "is_verified": False
        }
        res = analyze_profile_risk(profile, PROTECTED_SEED_PROFILES)
        self.assertEqual(res["risk_level"], "CRITICAL")
        self.assertGreaterEqual(res["risk_score"], 80)
        self.assertIsNotNone(res["primary_match"])
        self.assertEqual(res["primary_match"]["username"], "elonmusk")
        # Ensure reasons are populated
        self.assertTrue(len(res["factors"]) >= 2)

    def test_authentic_profile_self_scan(self):
        # When scanning the authentic user themselves, risk should remain LOW
        profile = {
            "username": "elonmusk",
            "display_name": "Elon Musk",
            "bio": "CEO of Tesla, SpaceX, xAI & CTO of X. Exploring the universe and accelerating sustainable energy.",
            "avatar_url": "https://example.com/avatar.jpg",
            "followers_count": 180000000,
            "following_count": 640,
            "posts_count": 42100,
            "account_age_days": 5400,
            "is_verified": True
        }
        res = analyze_profile_risk(profile, PROTECTED_SEED_PROFILES)
        self.assertEqual(res["risk_level"], "LOW")
        self.assertLess(res["risk_score"], 20)
        self.assertIsNone(res["primary_match"])

    def test_display_name_lookalike(self):
        profile = {
            "username": "satya_nadella_support",
            "display_name": "Satya Nadella Official Helpdesk",
            "bio": "Microsoft executive help desk. WhatsApp only for account recovery and support desk DM.",
            "avatar_url": "",
            "followers_count": 2,
            "following_count": 940,
            "posts_count": 0,
            "account_age_days": 1,
            "is_verified": False
        }
        res = analyze_profile_risk(profile, PROTECTED_SEED_PROFILES)
        self.assertIn(res["risk_level"], ["HIGH", "CRITICAL"])
        self.assertEqual(res["primary_match"]["username"], "satyanadella")

    def test_newer_similar_demo_profile_is_flagged(self):
        profiles = [
            {
                "username": "Leodas123", "display_name": "Leodas",
                "bio": "Building useful tools for everyone.", "avatar_url": "/old.png",
                "account_age_days": 20, "created_at": "2026-08-01 10:00:00", "is_verified": 0
            },
            {
                "username": "leodas", "display_name": "Leodas",
                "bio": "Building useful tools for everyone.", "avatar_url": "/old.png",
                "account_age_days": 1, "created_at": "2026-08-02 10:00:00", "is_verified": 0
            }
        ]
        result = analyze_demo_profile_similarity(profiles[1], profiles)
        self.assertEqual(result["score_boost"], 65)
        self.assertIn("High similarity to an older profile", result["reasons"])

    def test_older_similar_demo_profile_is_not_flagged(self):
        profiles = [
            {
                "username": "Leodas123", "display_name": "Leodas",
                "bio": "Building useful tools for everyone.", "avatar_url": "/old.png",
                "account_age_days": 20, "created_at": "2026-08-01 10:00:00", "is_verified": 0
            },
            {
                "username": "leodas", "display_name": "Leodas",
                "bio": "Building useful tools for everyone.", "avatar_url": "/old.png",
                "account_age_days": 1, "created_at": "2026-08-02 10:00:00", "is_verified": 0
            }
        ]
        result = analyze_demo_profile_similarity(profiles[0], profiles)
        self.assertEqual(result["score_boost"], 0)

    def test_unrelated_new_demo_profile_is_not_flagged(self):
        profiles = [
            {
                "username": "Leodas123", "display_name": "Leodas",
                "bio": "Building useful tools for everyone.", "avatar_url": "/old.png",
                "account_age_days": 20, "created_at": "2026-08-01 10:00:00", "is_verified": 0
            },
            {
                "username": "garden_notes", "display_name": "Garden Notes",
                "bio": "Growing herbs and sharing recipes.", "avatar_url": "/new.png",
                "account_age_days": 1, "created_at": "2026-08-02 10:00:00", "is_verified": 0
            }
        ]
        result = analyze_demo_profile_similarity(profiles[1], profiles)
        self.assertEqual(result["score_boost"], 0)

    def test_registered_profile_impersonation_detection(self):
        protected = {
            "username": "Leodas123", "display_name": "Leodas",
            "bio": "Building useful tools for everyone.", "avatar_url": "/old.png",
            "account_age_days": 20, "created_at": "2026-08-01 10:00:00"
        }
        new_profile = {
            "username": "leodas", "display_name": "leodas",
            "bio": "Building useful tools for everyone.", "avatar_url": "/new.png",
            "account_age_days": 1, "created_at": "2026-08-02 10:00:00"
        }
        result = detect_registered_impersonation(new_profile, [protected])
        self.assertTrue(result["detected"])
        self.assertEqual(result["protected_username"], "Leodas123")
        self.assertEqual(result["classification"], "POTENTIAL_IMPERSONATION")

    def test_registered_leodas_new2_pattern_is_detected(self):
        protected = {
            "username": "Leodas123", "display_name": "Leodas123",
            "bio": "Original protected profile bio.", "avatar_url": "/old.png",
            "account_age_days": 20, "created_at": "2026-08-01 10:00:00"
        }
        new_profile = {
            "username": "leodas_new2", "display_name": "leodas_new2",
            "bio": "Original protected profile bio.", "avatar_url": "/new.png",
            "account_age_days": 1, "created_at": "2026-08-02 10:00:00"
        }
        result = detect_registered_impersonation(new_profile, [protected])
        self.assertTrue(result["detected"])
        self.assertEqual(result["protected_username"], "Leodas123")

    def test_registered_unrelated_profile_is_not_detected(self):
        protected = {
            "username": "Leodas123", "display_name": "Leodas",
            "bio": "Building useful tools for everyone.", "created_at": "2026-08-01 10:00:00"
        }
        new_profile = {
            "username": "garden_notes", "display_name": "Garden Notes",
            "bio": "Growing herbs and sharing recipes.", "created_at": "2026-08-02 10:00:00"
        }
        result = detect_registered_impersonation(new_profile, [protected])
        self.assertFalse(result["detected"])

    @patch.dict("os.environ", {"MAIL_HOST": "", "MAIL_FROM": ""}, clear=False)
    def test_email_delivery_requires_environment_configuration(self):
        result = email_utils.send_impersonation_email(
            "test@example.com", "Leodas123", "leodas_new2", 90, ["High similarity"]
        )
        self.assertFalse(result["sent"])
        self.assertEqual(result["status"], "not_configured")

    @patch.dict("os.environ", {
        "MAIL_HOST": "smtp.example.test", "MAIL_PORT": "587",
        "MAIL_USERNAME": "sender@example.test", "MAIL_PASSWORD": "secret",
        "MAIL_FROM": "sender@example.test", "MAIL_USE_TLS": "true"
    }, clear=False)
    def test_email_configuration_status_is_safe(self):
        status = email_utils.get_email_configuration_status()
        self.assertTrue(all(status.values()))
        self.assertNotIn("secret", str(status))

    def test_email_delivery_rejects_invalid_recipient(self):
        result = email_utils.send_impersonation_email(
            "invalid-email", "Leodas123", "leodas_new2", 90, ["High similarity"]
        )
        self.assertFalse(result["sent"])
        self.assertEqual(result["status"], "invalid_recipient")

    @patch.dict("os.environ", {
        "MAIL_HOST": "smtp.example.test", "MAIL_PORT": "587",
        "MAIL_USERNAME": "sender@example.test", "MAIL_PASSWORD": "secret",
        "MAIL_FROM": "sender@example.test", "MAIL_USE_TLS": "true"
    }, clear=False)
    @patch("email_utils.smtplib.SMTP")
    def test_email_delivery_uses_authenticated_smtp(self, smtp_class):
        smtp = MagicMock()
        smtp.__enter__.return_value = smtp
        smtp.send_message.return_value = {}
        smtp_class.return_value = smtp

        result = email_utils.send_impersonation_email(
            "recipient@example.test", "Leodas123", "leodas_new2", 90, ["High similarity"]
        )

        self.assertEqual(result, {"sent": True, "status": "sent"})
        smtp_class.assert_called_once_with("smtp.example.test", 587, timeout=20)
        smtp.ehlo.assert_any_call()
        smtp.starttls.assert_called_once_with()
        smtp.login.assert_called_once_with("sender@example.test", "secret")
        smtp.send_message.assert_called_once()
        smtp.quit.assert_called_once_with()

    @patch.dict("os.environ", {
        "MAIL_HOST": "smtp.example.test", "MAIL_PORT": "587",
        "MAIL_USERNAME": "sender@example.test", "MAIL_PASSWORD": "secret",
        "MAIL_FROM": "sender@example.test", "MAIL_USE_TLS": "false"
    }, clear=False)
    @patch("email_utils.smtplib.SMTP")
    def test_refused_smtp_recipient_is_not_reported_as_sent(self, smtp_class):
        smtp = MagicMock()
        smtp.__enter__.return_value = smtp
        smtp.send_message.return_value = {"recipient@example.test": (550, b"rejected")}
        smtp_class.return_value = smtp

        result = email_utils.send_impersonation_email(
            "recipient@example.test", "Leodas123", "leodas_new2", 90, ["High similarity"]
        )

        self.assertFalse(result["sent"])
        self.assertEqual(result["status"], "failed")

if __name__ == "__main__":
    unittest.main()

