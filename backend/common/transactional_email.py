import logging

from django.conf import settings
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """Raised when Resend, SMTP, or the console mail backend fails to send."""

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


def _delivery_failure_detail(exc: Exception) -> str:
    from common.exceptions import EMAIL_DELIVERY_FAILED

    ResendAPIError = None
    try:
        from resend.exceptions import ResendError as ResendAPIError
    except ImportError:
        pass

    if ResendAPIError is not None and isinstance(exc, ResendAPIError):
        text = (getattr(exc, "message", None) or str(exc)).strip()
        lowered = text.lower()
        if "only send testing emails to your own" in lowered:
            return (
                "Resend test mode only allows sending to the email on your Resend account. "
                "Use that address for testing, or verify a domain at resend.com/domains and "
                "set DEFAULT_FROM_EMAIL to an address on that domain."
            )
        if settings.DEBUG and text:
            return text
    if settings.DEBUG:
        return str(exc).strip() or EMAIL_DELIVERY_FAILED
    return EMAIL_DELIVERY_FAILED


def send_transactional_email(*, to: list[str], subject: str, body: str) -> None:
    """Deliver a plain-text email via Resend when configured, otherwise Django's email backend."""
    try:
        if settings.RESEND_API_KEY:
            import resend

            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": to,
                "subject": subject,
                "text": body,
            })
            return
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL or None, to, fail_silently=False)
    except Exception as exc:
        logger.exception("Transactional email failed for recipients %s", to)
        raise EmailDeliveryError(_delivery_failure_detail(exc)) from exc
