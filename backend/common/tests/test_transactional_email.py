from unittest import mock

from django.test import SimpleTestCase, override_settings

from common.exceptions import EMAIL_DELIVERY_FAILED
from common.transactional_email import EmailDeliveryError, send_transactional_email


class TransactionalEmailTests(SimpleTestCase):
    @override_settings(RESEND_API_KEY="", DEFAULT_FROM_EMAIL="PokeFind <no-reply@example.com>")
    @mock.patch("common.transactional_email.send_mail")
    def test_without_resend_uses_django_mail(self, send_mail):
        send_transactional_email(to=["a@example.com"], subject="Hi", body="Hello")
        send_mail.assert_called_once_with("Hi", "Hello", "PokeFind <no-reply@example.com>", ["a@example.com"], fail_silently=False)

    @override_settings(RESEND_API_KEY="re_test", DEFAULT_FROM_EMAIL="PokeFind <no-reply@example.com>")
    @mock.patch("resend.Emails.send")
    def test_with_resend_uses_the_api(self, resend_send):
        send_transactional_email(to=["a@example.com"], subject="Hi", body="Hello")
        resend_send.assert_called_once_with({
            "from": "PokeFind <no-reply@example.com>",
            "to": ["a@example.com"],
            "subject": "Hi",
            "text": "Hello",
        })

    @override_settings(RESEND_API_KEY="", DEFAULT_FROM_EMAIL="PokeFind <no-reply@example.com>")
    @mock.patch("common.transactional_email.send_mail", side_effect=OSError("SMTP down"))
    def test_failures_raise_email_delivery_error_without_leaking_the_cause(self, send_mail):
        with self.assertRaises(EmailDeliveryError) as ctx, self.assertLogs("common.transactional_email", "ERROR"):
            send_transactional_email(to=["a@example.com"], subject="Hi", body="Hello")
        self.assertEqual(ctx.exception.detail, EMAIL_DELIVERY_FAILED)
        send_mail.assert_called_once()

    @override_settings(DEBUG=True, RESEND_API_KEY="", DEFAULT_FROM_EMAIL="PokeFind <no-reply@example.com>")
    @mock.patch("common.transactional_email.send_mail", side_effect=OSError("SMTP down"))
    def test_debug_failures_show_the_cause(self, send_mail):
        with self.assertRaises(EmailDeliveryError) as ctx, self.assertLogs("common.transactional_email", "ERROR"):
            send_transactional_email(to=["a@example.com"], subject="Hi", body="Hello")
        self.assertIn("SMTP down", ctx.exception.detail)
