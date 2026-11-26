import logging
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import path
from rest_framework.response import Response
from rest_framework.views import APIView

from common.request_context import RequestIdFilter, current_request_id
from common.testing import ApiTestCase
from config.urls import handler500, urlpatterns as real_urlpatterns  # noqa: F401  (handler500 is read by Django)


class BoomView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request):
        raise RuntimeError("boom")


class RequestIdEchoView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request):
        return Response({"request_id": current_request_id()})


urlpatterns = [
    path("api/v1/_boom/", BoomView.as_view()),
    path("api/v1/_echo/", RequestIdEchoView.as_view()),
    *real_urlpatterns,
]


class AccessLogTests(ApiTestCase):
    def test_every_request_writes_one_access_line(self):
        with self.assertLogs("pokefind.access", level="INFO") as logs:
            response = self.client.get("/api/v1/listings/?q=secret-search")
        self.assertEqual(len(logs.records), 1)
        line = logs.records[0].getMessage()
        self.assertRegex(line, r"^GET /api/v1/listings/ 200 \d+ms user=- ip=\S+ version=v1$")
        self.assertNotIn("secret-search", line)
        self.assertTrue(response["X-Request-ID"])

    def test_unversioned_path_is_logged_as_v1(self):
        with self.assertLogs("pokefind.access", level="INFO") as logs:
            self.client.get("/api/health/")
        self.assertIn("version=v1", logs.records[0].getMessage())

    def test_access_line_names_the_signed_in_user(self):
        user = get_user_model().objects.create_user(username="ash", email="ash@example.com", password="pikachu-12345")
        self.client.force_authenticate(user)
        with self.assertLogs("pokefind.access", level="INFO") as logs:
            self.client.get("/api/v1/auth/me/")
        self.assertIn(f"user={user.pk} ", logs.records[0].getMessage())

    def test_a_safe_incoming_request_id_is_kept_and_an_unsafe_one_replaced(self):
        kept = self.client.get("/api/v1/health/", HTTP_X_REQUEST_ID="trace-12345678")
        self.assertEqual(kept["X-Request-ID"], "trace-12345678")
        replaced = self.client.get("/api/v1/health/", HTTP_X_REQUEST_ID="bad id\twith spaces")
        self.assertRegex(replaced["X-Request-ID"], r"^[0-9a-f]{16}$")

    def test_log_records_carry_the_request_id_only_during_the_request(self):
        record = logging.LogRecord("x", logging.INFO, __file__, 1, "m", None, None)
        RequestIdFilter().filter(record)
        self.assertEqual(record.request_id, "-")


@override_settings(ROOT_URLCONF=__name__)
class ErrorResponseTests(ApiTestCase):
    def test_request_id_is_available_inside_the_view(self):
        response = self.client.get("/api/v1/_echo/")
        self.assertEqual(response.json()["request_id"], response["X-Request-ID"])

    def test_unexpected_error_is_logged_and_answered_as_json_with_the_request_id(self):
        self.client.raise_request_exception = False
        with self.assertLogs("django.request", level="ERROR") as logs:
            response = self.client.get("/api/v1/_boom/")
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["code"], "server_error")
        self.assertEqual(body["request_id"], response["X-Request-ID"])
        self.assertNotIn("boom", response.content.decode())
        self.assertIsNotNone(logs.records[0].exc_info)

    def test_rate_limited_request_is_logged(self):
        with mock.patch("rest_framework.throttling.AnonRateThrottle.allow_request", return_value=False), \
                mock.patch("rest_framework.throttling.AnonRateThrottle.wait", return_value=1):
            with self.assertLogs("common.request_log", level="WARNING") as logs:
                response = self.client.get("/api/v1/listings/")
        self.assertEqual(response.status_code, 429)
        self.assertIn("Rate limit hit on GET /api/v1/listings/", logs.records[0].getMessage())
