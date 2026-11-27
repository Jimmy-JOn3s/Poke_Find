"""Request IDs, the access log, and the API's error responses.

Every request gets an ID. It is stamped on each log line written while the request runs, returned in
the X-Request-ID header, and included in 500 responses, so one ID ties a user's report to the access
line, the events and the stack trace.
"""
import logging
import re
import time
import uuid

from django.conf import settings
from django.http import JsonResponse
from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler

from .request_context import current_request_id, request_id_var

access_logger = logging.getLogger("pokefind.access")
logger = logging.getLogger(__name__)

_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
SERVER_ERROR = "Something went wrong on our side. Please try again."


def client_ip(request) -> str:
    """The caller's address, trusting X-Forwarded-For only for the configured number of proxies."""
    num_proxies = settings.REST_FRAMEWORK.get("NUM_PROXIES") or 0
    forwarded = [part.strip() for part in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if part.strip()]
    if num_proxies and forwarded:
        return forwarded[-min(num_proxies, len(forwarded))]
    return request.META.get("REMOTE_ADDR") or "-"


def _api_version(request) -> str:
    match = getattr(request, "resolver_match", None)
    if match is None or not request.path.startswith("/api/"):
        return "-"
    return match.namespace or settings.REST_FRAMEWORK.get("DEFAULT_VERSION", "-")


class RequestLogMiddleware:
    """Assigns the request ID and writes one access-log line per request.

    Only the path is logged, never the query string or body, so tokens and personal data stay out.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.META.get("HTTP_X_REQUEST_ID", "")
        request_id = incoming if _SAFE_REQUEST_ID.match(incoming) else uuid.uuid4().hex[:16]
        token = request_id_var.set(request_id)
        started = time.monotonic()
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            # DRF copies the JWT user onto the Django request, so this is the API user too.
            user = getattr(request, "user", None)
            access_logger.info(
                "%s %s %s %dms user=%s ip=%s version=%s",
                request.method,
                request.path,
                response.status_code,
                (time.monotonic() - started) * 1000,
                user.pk if user is not None and user.is_authenticated else "-",
                client_ip(request),
                _api_version(request),
            )
            return response
        finally:
            request_id_var.reset(token)


def api_exception_handler(exc, context):
    """DRF's handler, plus a log line when a caller is rate-limited.

    Unexpected exceptions return None here: Django then logs the stack trace (django.request) and
    answers through server_error below.
    """
    if isinstance(exc, Throttled):
        request = context.get("request")
        logger.warning(
            "Rate limit hit on %s %s ip=%s",
            getattr(request, "method", "-"), getattr(request, "path", "-"),
            client_ip(request) if request is not None else "-",
        )
    return exception_handler(exc, context)


def server_error(request, *args, **kwargs):
    """500 response. JSON for the API so the app can show a message and quote the request ID."""
    from django.views.defaults import server_error as default_server_error

    if request.path.startswith("/api/"):
        return JsonResponse(
            {"detail": SERVER_ERROR, "code": "server_error", "request_id": current_request_id()}, status=500,
        )
    return default_server_error(request, *args, **kwargs)
