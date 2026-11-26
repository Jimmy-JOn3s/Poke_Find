from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from accounts.admin_login import throttled_admin_login


def health(_request):
    return JsonResponse({"status": "ok"})


# Version 1 of the API. A breaking change gets its own list (api_v2_patterns) mounted at
# /api/v2/ and added to REST_FRAMEWORK["ALLOWED_VERSIONS"]; v1 keeps serving existing clients.
api_v1_patterns = [
    path("health/", health),
    path("auth/", include("accounts.urls")),
    path("", include("marketplace.urls")),
    path("", include("messaging.urls")),
    path("", include("moderation.urls")),
]

urlpatterns = [
    # Must come before admin.site.urls so it replaces the admin's own (unthrottled) login view.
    path("admin/login/", throttled_admin_login),
    path("admin/", admin.site.urls),
    # The namespace is what sets request.version (NamespaceVersioning).
    path("api/v1/", include((api_v1_patterns, "api"), namespace="v1")),
    # Unversioned paths predate versioning. They stay pinned to v1 for clients already deployed
    # against them, and never move to a newer version.
    path("api/", include(api_v1_patterns)),
]

handler500 = "common.request_log.server_error"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

