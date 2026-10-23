import re
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from rest_framework import status

from common.testing import ApiTestCase


User = get_user_model()
VERIFY_LINK = re.compile(
    r"https://app\.example\.com/#verify_uid=(?P<uid>[^&\s]+)&verify_token=(?P<token>\S+)"
)


@override_settings(FRONTEND_URL="https://app.example.com")
class EmailVerificationTests(ApiTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mai",
            email="mai@example.com",
            password="strong-pass-123",
            display_name="Mai",
        )

    def link_from_email(self):
        match = VERIFY_LINK.search(mail.outbox[-1].body)
        self.assertIsNotNone(match, mail.outbox[-1].body)
        return match["uid"], match["token"]

    def test_register_sends_a_verification_email(self):
        response = self.client.post("/api/auth/register/", {
            "username": "new-trainer",
            "email": "new@example.com",
            "password": "strong-pass-123",
            "display_name": "New",
            "role": "personal",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["user"]["is_email_verified"])
        self.assertEqual(len(mail.outbox), 1)
        user = User.objects.get(email="new@example.com")
        uid, token = self.link_from_email()
        confirmed = self.client.post("/api/auth/email-verification/confirm/", {"uid": uid, "token": token}, format="json")
        self.assertEqual(confirmed.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)

    def test_authenticated_user_can_request_a_verification_email(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/auth/email-verification/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_confirm_marks_the_user_verified(self):
        self.client.force_authenticate(self.user)
        self.client.post("/api/auth/email-verification/", {}, format="json")
        uid, token = self.link_from_email()
        confirmed = self.client.post("/api/auth/email-verification/confirm/", {"uid": uid, "token": token}, format="json")
        self.assertEqual(confirmed.status_code, 200)
        self.assertTrue(confirmed.data["user"]["is_email_verified"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_magic_link_confirm_also_verifies_email(self):
        response = self.client.post("/api/auth/magic-link/", {"email": "magic@example.com"}, format="json")
        self.assertEqual(response.status_code, 200)
        body = mail.outbox[-1].body
        magic = re.search(
            r"#magic_uid=(?P<uid>[^&\s]+)&magic_token=(?P<token>\S+)", body
        )
        self.assertIsNotNone(magic)
        confirmed = self.client.post("/api/auth/magic-link/confirm/", {
            "uid": magic["uid"], "token": magic["token"],
        }, format="json")
        self.assertEqual(confirmed.status_code, 200)
        self.assertTrue(confirmed.data["user"]["is_email_verified"])

    def test_unverified_user_cannot_create_a_listing(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/listings/", {
            "product_name": "Pikachu",
            "set_name": "Base",
            "set_code": "BS",
            "card_number": "58",
            "condition": "NM",
            "card_language": "en",
            "rarity": "rare",
            "asking_price": "100.00",
            "currency": "THB",
            "quantity": 1,
            "description": "",
            "status": "active",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_verified_user_can_create_a_listing(self):
        self.user.is_email_verified = True
        self.user.save(update_fields=["is_email_verified"])
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/listings/", {
            "product_name": "Pikachu",
            "set_name": "Base",
            "set_code": "BS",
            "card_number": "58",
            "condition": "NM",
            "card_language": "en",
            "rarity": "rare",
            "asking_price": "100.00",
            "currency": "THB",
            "quantity": 1,
            "description": "",
            "status": "active",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_a_failed_send_returns_an_error(self):
        self.client.force_authenticate(self.user)
        with mock.patch("accounts.email_verification.send_transactional_email", side_effect=OSError("down")), \
                self.assertLogs("common.transactional_email", "ERROR"):
            failed = self.client.post("/api/auth/email-verification/", {}, format="json")
        self.assertEqual(failed.status_code, 503)
        self.assertEqual(failed.data["code"], "email_delivery_failed")
