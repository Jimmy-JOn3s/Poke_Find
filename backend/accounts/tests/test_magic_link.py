import re
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from rest_framework_simplejwt.tokens import RefreshToken

from common.testing import ApiTestCase


User = get_user_model()
LINK = re.compile(r"https://app\.example\.com/#magic_uid=(?P<uid>[^&\s]+)&magic_token=(?P<token>\S+)")


@override_settings(FRONTEND_URL="https://app.example.com")
class MagicLinkTests(ApiTestCase):
    def request_link(self, email="new@example.com"):
        return self.client.post("/api/auth/magic-link/", {"email": email}, format="json")

    def link_from_email(self):
        match = LINK.search(mail.outbox[-1].body)
        self.assertIsNotNone(match, mail.outbox[-1].body)
        return match["uid"], match["token"]

    def confirm(self, uid, token):
        return self.client.post("/api/auth/magic-link/confirm/", {"uid": uid, "token": token}, format="json")

    def test_new_email_creates_a_user_and_sends_a_link(self):
        self.assertFalse(User.objects.filter(email="new@example.com").exists())
        response = self.request_link()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        user = User.objects.get(email="new@example.com")
        self.assertFalse(user.has_usable_password())
        uid, token = self.link_from_email()
        confirmed = self.confirm(uid, token)
        self.assertEqual(confirmed.status_code, 200, confirmed.data)
        self.assertIn("access", confirmed.data)
        self.assertEqual(confirmed.data["user"]["email"], "new@example.com")

    def test_existing_user_gets_a_link_without_duplicating_the_account(self):
        user = User.objects.create_user(
            username="ash", email="ash@example.com", password="a-long-pass-81", display_name="Ash",
        )
        self.request_link("ASH@Example.com")
        self.assertEqual(User.objects.filter(email__iexact="ash@example.com").count(), 1)
        confirmed = self.confirm(*self.link_from_email())
        self.assertEqual(confirmed.status_code, 200)
        self.assertEqual(confirmed.data["user"]["id"], user.id)

    def test_inactive_accounts_get_the_same_answer_and_no_email(self):
        User.objects.create_user(
            username="gone", email="gone@example.com", password="a-long-pass-81", is_active=False,
        )
        response = self.request_link("gone@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(mail.outbox, [])

    def test_repeat_requests_send_one_email_per_cooldown(self):
        self.request_link()
        self.request_link()
        self.assertEqual(len(mail.outbox), 1)

    def test_a_failed_send_returns_an_error_and_can_be_retried(self):
        with mock.patch("accounts.magic_link.send_transactional_email", side_effect=OSError("down")), \
                self.assertLogs("common.transactional_email", "ERROR"):
            failed = self.request_link()
        self.assertEqual(failed.status_code, 503)
        self.assertEqual(failed.data["code"], "email_delivery_failed")
        self.request_link()
        self.assertEqual(len(mail.outbox), 1)

    def test_a_bad_token_is_rejected(self):
        self.request_link()
        uid, _ = self.link_from_email()
        response = self.confirm(uid, "not-a-valid-token")
        self.assertEqual(response.status_code, 400)
