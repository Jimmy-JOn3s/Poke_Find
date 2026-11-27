from rest_framework import status
from common.testing import ApiTestCase


class AuthApiTests(ApiTestCase):
    def test_register_returns_tokens_and_bilingual_preferences(self):
        response = self.client.post("/api/auth/register/", {
            "username": "mai",
            "email": "mai@example.com",
            "password": "strong-pass-123",
            "display_name": "ใหม่",
            "role": "personal",
            "preferred_language": "th",
            "preferred_currency": "THB",
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["preferred_language"], "th")
        self.assertEqual(response.data["user"]["preferred_currency"], "THB")

    def test_me_requires_authentication_and_validates_preferences(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_accepts_email_as_the_identifier(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_user(
            username="email-user", email="email-user@example.com", password="strong-pass-123", display_name="Email User"
        )
        response = self.client.post("/api/auth/login/", {
            "username": "email-user@example.com", "password": "strong-pass-123",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_register_reports_when_the_verification_email_could_not_be_sent(self):
        from unittest import mock

        from common.transactional_email import EmailDeliveryError

        payload = {
            "username": "misty", "email": "misty@example.com", "password": "a-long-pass-81",
            "display_name": "Misty", "role": "personal",
        }
        sent = self.client.post("/api/v1/auth/register/", payload, format="json")
        self.assertEqual(sent.status_code, 201, sent.data)
        self.assertIs(sent.data["verification_email_sent"], True)

        payload.update(username="brock", email="brock@example.com")
        with mock.patch("accounts.views.request_email_verification", side_effect=EmailDeliveryError("down")):
            with self.assertLogs("accounts.views", level="WARNING") as logs:
                failed = self.client.post("/api/v1/auth/register/", payload, format="json")
        self.assertEqual(failed.status_code, 201, failed.data)
        self.assertIs(failed.data["verification_email_sent"], False)
        self.assertIn("access", failed.data)
        self.assertIn("verification email could not be sent", logs.output[0])

    def test_failed_login_is_logged_without_the_identifier(self):
        with self.assertLogs("accounts.views", level="WARNING") as logs:
            response = self.client.post(
                "/api/v1/auth/login/", {"username": "nobody@example.com", "password": "wrong-pass-123"}, format="json",
            )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Login failed", logs.output[0])
        self.assertNotIn("nobody@example.com", logs.output[0])
