from django.contrib.auth import get_user_model

from common.testing import ApiTestCase


PASSWORD = "a-long-pass-81"


class AdminLoginThrottleTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        get_user_model().objects.create_superuser(username="root", email="root@example.com", password=PASSWORD)

    def test_admin_login_is_rate_limited(self):
        statuses = [
            self.client.post("/admin/login/", {"username": "root", "password": f"wrong-{attempt}"}).status_code
            for attempt in range(11)
        ]
        self.assertEqual(statuses[:10], [200] * 10)
        self.assertEqual(statuses[10], 429)

    def test_admin_login_still_works(self):
        self.assertEqual(self.client.get("/admin/login/").status_code, 200)
        response = self.client.post("/admin/login/", {"username": "root", "password": PASSWORD})
        self.assertEqual(response.status_code, 302)
