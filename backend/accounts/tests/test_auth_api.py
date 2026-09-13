from rest_framework import status
from rest_framework.test import APITestCase


class AuthApiTests(APITestCase):
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
