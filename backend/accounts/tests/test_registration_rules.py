from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from common.testing import ApiTestCase


User = get_user_model()


class RegistrationRulesTests(ApiTestCase):
    def register(self, **overrides):
        payload = {
            "username": "trainer", "email": "Trainer@Example.com",
            "password": "a-long-pass-81", "display_name": "Trainer",
        }
        payload.update(overrides)
        return self.client.post("/api/auth/register/", payload, format="json")

    def test_email_is_stored_lowercase(self):
        response = self.register()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(User.objects.get().email, "trainer@example.com")

    def test_case_variant_duplicate_email_is_rejected(self):
        self.register()
        duplicate = self.register(username="someone-else", email="TRAINER@example.COM")
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("email", duplicate.data)

    def test_database_rejects_case_variant_duplicates(self):
        User.objects.create_user(username="a", email="dup@example.com", password="x")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(username="b", email="DUP@example.com", password="x")

    def test_weak_passwords_are_rejected(self):
        for password in ("12345678", "password", "trainer123"):
            response = self.register(password=password)
            self.assertEqual(response.status_code, 400, password)
            self.assertIn("password", response.data)

    def test_login_by_email_ignores_letter_case(self):
        self.register()
        response = self.client.post(
            "/api/auth/login/", {"username": "TRAINER@example.com", "password": "a-long-pass-81"}, format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_registration_race_returns_400_not_500(self):
        with mock.patch.object(type(User.objects), "create_user", side_effect=IntegrityError("duplicate key")):
            response = self.register()
        self.assertEqual(response.status_code, 400)
