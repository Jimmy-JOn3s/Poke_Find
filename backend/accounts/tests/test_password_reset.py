import re
from datetime import datetime, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import override_settings
from rest_framework_simplejwt.tokens import RefreshToken

from common.testing import ApiTestCase


User = get_user_model()
OLD_PASSWORD = "a-long-pass-81"
NEW_PASSWORD = "brand-new-pass-92"
LINK = re.compile(r"https://app\.example\.com/#reset_uid=(?P<uid>[^&\s]+)&reset_token=(?P<token>\S+)")


@override_settings(FRONTEND_URL="https://app.example.com")
class PasswordResetTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="misty", email="misty@example.com", password=OLD_PASSWORD, display_name="Misty",
        )

    def request_reset(self, email="misty@example.com"):
        return self.client.post("/api/auth/password-reset/", {"email": email}, format="json")

    def link_from_email(self):
        match = LINK.search(mail.outbox[-1].body)
        self.assertIsNotNone(match, mail.outbox[-1].body)
        return match["uid"], match["token"]

    def confirm(self, uid, token, password=NEW_PASSWORD):
        return self.client.post(
            "/api/auth/password-reset/confirm/", {"uid": uid, "token": token, "new_password": password}, format="json",
        )

    def test_known_email_gets_one_link_to_the_web_app(self):
        response = self.request_reset("MISTY@Example.com")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["misty@example.com"])
        self.link_from_email()

    def test_unknown_inactive_and_passwordless_accounts_get_the_same_answer_and_no_email(self):
        known = self.request_reset().data
        mail.outbox.clear()
        User.objects.create_user(username="ghost", email="ghost@example.com", password=None)
        User.objects.create_user(username="gone", email="gone@example.com", password=OLD_PASSWORD, is_active=False)
        for email in ("nobody@example.com", "ghost@example.com", "gone@example.com"):
            response = self.request_reset(email)
            self.assertEqual((response.status_code, response.data), (200, known), email)
        self.assertEqual(mail.outbox, [])

    def test_repeat_requests_send_one_email_per_cooldown(self):
        self.request_reset()
        self.request_reset()
        self.assertEqual(len(mail.outbox), 1)

    def test_a_failed_send_returns_an_error_and_can_be_retried(self):
        with mock.patch("accounts.password_reset.send_transactional_email", side_effect=OSError("SMTP down")), \
                self.assertLogs("common.transactional_email", "ERROR"):
            failed = self.request_reset()
        self.assertEqual(failed.status_code, 503)
        self.assertEqual(failed.data["code"], "email_delivery_failed")
        self.request_reset()
        self.assertEqual(len(mail.outbox), 1)

    def test_a_failed_send_for_an_unknown_email_still_looks_successful(self):
        known = self.request_reset("nobody@example.com").data
        with mock.patch("accounts.password_reset.send_transactional_email", side_effect=OSError("SMTP down")):
            failed = self.request_reset("nobody@example.com")
        self.assertEqual((failed.status_code, failed.data), (200, known))

    def test_reset_changes_the_password(self):
        self.request_reset()
        response = self.confirm(*self.link_from_email())
        self.assertEqual(response.status_code, 200, response.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))
        self.assertFalse(self.user.check_password(OLD_PASSWORD))

    def test_a_link_works_only_once(self):
        self.request_reset()
        uid, token = self.link_from_email()
        self.confirm(uid, token)
        self.assertEqual(self.confirm(uid, token, "another-new-pass-73").status_code, 400)

    def test_tampered_and_garbage_links_are_rejected(self):
        self.request_reset()
        uid, token = self.link_from_email()
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
        huge_id = "OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5OTk5"  # base64("99…9"), beyond any integer column
        bad_links = (
            (uid, tampered), ("garbage", token), ("%%%", token), ("OTk5OTk", token),
            ("wrI", token),  # base64("²"): str.isdigit() accepts it but int() doesn't
            (huge_id, token),
        )
        for bad_uid, bad_token in bad_links:
            response = self.confirm(bad_uid, bad_token)
            self.assertEqual(response.status_code, 400, (bad_uid, bad_token))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_expired_links_are_rejected(self):
        self.request_reset()
        uid, token = self.link_from_email()
        later = datetime.now() + timedelta(minutes=61)
        with mock.patch.object(PasswordResetTokenGenerator, "_now", return_value=later):
            self.assertEqual(self.confirm(uid, token).status_code, 400)

    def test_weak_new_password_is_rejected_and_the_old_one_still_works(self):
        self.request_reset()
        response = self.confirm(*self.link_from_email(), password="12345678")
        self.assertEqual(response.status_code, 400)
        self.assertIn("new_password", response.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_reset_signs_out_every_device(self):
        refresh = str(RefreshToken.for_user(self.user))
        self.request_reset()
        self.confirm(*self.link_from_email())
        self.assertEqual(self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json").status_code, 401)

    def test_a_stale_session_token_does_not_block_recovery(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")
        self.assertEqual(self.request_reset().status_code, 200)
        self.assertEqual(self.confirm(*self.link_from_email()).status_code, 200)

    def test_reset_requests_are_rate_limited_per_ip(self):
        statuses = [self.request_reset(f"user{i}@example.com").status_code for i in range(11)]
        self.assertEqual(statuses[:10], [200] * 10)
        self.assertEqual(statuses[10], 429)

    def test_signing_in_invalidates_an_earlier_reset_link(self):
        self.request_reset()
        uid, token = self.link_from_email()
        login = self.client.post(
            "/api/auth/login/", {"username": "misty@example.com", "password": OLD_PASSWORD}, format="json",
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(self.confirm(uid, token).status_code, 400)
