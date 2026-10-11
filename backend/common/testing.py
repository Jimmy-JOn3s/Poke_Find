from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class ApiTestCase(APITestCase):
    """APITestCase with a private in-memory cache that starts every test with empty rate-limit counters.

    Subclasses that override setUp must call super().setUp().
    """

    def setUp(self):
        super().setUp()
        cache.clear()
