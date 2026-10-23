from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import ValidationError

from common.transactional_email import EmailDeliveryError, send_transactional_email


User = get_user_model()
_signer = TimestampSigner(salt="pokefind-email-verify")

EMAIL_COOLDOWN_SECONDS = 5 * 60
INVALID_LINK = "This verification link is invalid or has expired. Request a new one."
REQUESTED = "If your account needs verification, we've sent a link to your email."
SUBJECTS = {"th": "ยืนยันอีเมล PokeFind", "en": "Verify your PokeFind email"}
BODIES = {
    "th": (
        "ยืนยันที่อยู่อีเมลของคุณโดยเปิดลิงก์นี้ภายใน {minutes} นาที:\n{link}\n\n"
        "หากคุณไม่ได้สมัคร ไม่ต้องทำอะไร"
    ),
    "en": (
        "Confirm your email by opening this link within {minutes} minutes:\n{link}\n\n"
        "If you didn't create an account, you can ignore this email."
    ),
}


def _make_token(user) -> str:
    return _signer.sign(str(user.pk))


def _token_valid(user, token: str) -> bool:
    try:
        return _signer.unsign(token, max_age=settings.MAGIC_LINK_TIMEOUT) == str(user.pk)
    except (BadSignature, SignatureExpired):
        return False


def verification_link(user) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{settings.FRONTEND_URL}/#verify_uid={uid}&verify_token={_make_token(user)}"


def request_email_verification(user) -> None:
    """Email a verification link when the address is not verified yet."""
    if user.is_email_verified:
        return
    cooldown_key = f"email-verify-sent:{user.pk}"
    if not cache.add(cooldown_key, True, EMAIL_COOLDOWN_SECONDS):
        return
    language = user.preferred_language if user.preferred_language in BODIES else "en"
    timeout_minutes = settings.MAGIC_LINK_TIMEOUT // 60
    body = BODIES[language].format(link=verification_link(user), minutes=timeout_minutes)
    try:
        send_transactional_email(to=[user.email], subject=SUBJECTS[language], body=body)
    except EmailDeliveryError:
        cache.delete(cooldown_key)
        raise


def _locked_user(uid: str):
    try:
        user_id = urlsafe_base64_decode(uid).decode()
    except ValueError:
        return None
    if not user_id.isdecimal():
        return None
    return User.objects.select_for_update().filter(pk=int(user_id), is_active=True).first()


@transaction.atomic
def confirm_email_verification(uid: str, token: str) -> User:
    user = _locked_user(uid)
    if user is None or not _token_valid(user, token):
        raise ValidationError({"detail": INVALID_LINK})
    if not user.is_email_verified:
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
    return user
