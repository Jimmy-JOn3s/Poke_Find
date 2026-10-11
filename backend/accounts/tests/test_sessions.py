from django.contrib.auth import get_user_model

from common.testing import ApiTestCase


User = get_user_model()
PASSWORD = "a-long-pass-81"


class SessionSecurityTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        User.objects.create_user(username="ash", email="ash@example.com", password=PASSWORD, display_name="Ash")

    def login(self, password=PASSWORD, **headers):
        return self.client.post(
            "/api/auth/login/", {"username": "ash@example.com", "password": password}, format="json", **headers,
        )

    def test_login_is_rate_limited(self):
        statuses = [self.login(password=f"wrong-{attempt}").status_code for attempt in range(11)]
        self.assertEqual(statuses[:10], [401] * 10)
        self.assertEqual(statuses[10], 429)

    def test_spoofed_forwarded_for_header_does_not_reset_the_limit(self):
        for attempt in range(10):
            self.login(password=f"wrong-{attempt}", HTTP_X_FORWARDED_FOR=f"10.0.0.{attempt}")
        self.assertEqual(self.login(HTTP_X_FORWARDED_FOR="10.0.0.99").status_code, 429)

    def test_refresh_rotates_and_the_old_refresh_token_stops_working(self):
        refresh = self.login().data["refresh"]
        rotated = self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(rotated.status_code, 200)
        self.assertNotEqual(rotated.data["refresh"], refresh)
        reused = self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(reused.status_code, 401)

    def test_logout_blacklists_the_refresh_token(self):
        refresh = self.login().data["refresh"]
        self.assertEqual(self.client.post("/api/auth/logout/", {"refresh": refresh}, format="json").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json").status_code, 401)
