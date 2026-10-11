from django.contrib import admin
from django.http import HttpResponse
from rest_framework.throttling import SimpleRateThrottle


class AdminLoginThrottle(SimpleRateThrottle):
    """The API login's per-IP limit (the `auth` rate), counted separately for the Django admin."""

    scope = "auth"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": "admin-login", "ident": self.get_ident(request)}


def throttled_admin_login(request, extra_context=None):
    """Django's admin login, with password attempts rate-limited like /api/auth/login/."""
    if request.method == "POST" and not AdminLoginThrottle().allow_request(request, None):
        return HttpResponse("Too many sign-in attempts. Try again in a minute.", status=429, content_type="text/plain")
    return admin.site.login(request, extra_context)
