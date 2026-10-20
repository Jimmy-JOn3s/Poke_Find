from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from accounts.admin_login import throttled_admin_login


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    # Must come before admin.site.urls so it replaces the admin's own (unthrottled) login view.
    path("admin/login/", throttled_admin_login),
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("marketplace.urls")),
    path("api/", include("messaging.urls")),
    path("api/", include("moderation.urls")),
]

