import re
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.core.cache import cache
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db import IntegrityError, transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken


from common.transactional_email import EmailDeliveryError, send_transactional_email


User = get_user_model()
_signer = TimestampSigner(salt="pokefind-magic-link")

EMAIL_COOLDOWN_SECONDS = 5 * 60
INVALID_LINK = "This sign-in link is invalid or has expired. Request a new one."
REQUESTED = "If that email is valid, we've sent a sign-in link."
SUBJECTS = {"th": "ลิงก์เข้าสู่ระบบ PokeFind", "en": "Your PokeFind sign-in link"}
BODIES = {
    "th": (
        "เปิดลิงก์นี้ภายใน {minutes} นาทีเพื่อเข้าสู่ระบบ PokeFind:\n{link}\n\n"
        "หากคุณไม่ได้ขอ ไม่ต้องทำอะไร"
    ),
    "en": (
        "Open this link within {minutes} minutes to sign in to PokeFind:\n{link}\n\n"
        "If you didn't ask for this, you can ignore this email."
    ),
}


def _make_token(user) -> str:
    return _signer.sign(str(user.pk))


def _token_valid(user, token: str) -> bool:
    try:
        return _signer.unsign(token, max_age=settings.MAGIC_LINK_TIMEOUT) == str(user.pk)
    except (BadSignature, SignatureExpired):
        return False


def magic_link(user) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{settings.FRONTEND_URL}/#magic_uid={uid}&magic_token={_make_token(user)}"


def _unique_username(email: str) -> str:
    local = email.split("@", 1)[0]
    base = re.sub(r"[^a-zA-Z0-9_-]", "-", local).strip("-") or "trainer"
    base = base[:120]
    candidate = base
    while User.objects.filter(username=candidate).exists():
        candidate = f"{base[:110]}-{secrets.token_hex(3)}"
    return candidate


def _display_name_from_email(email: str) -> str:
    local = email.split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
    return (local.title()[:120] if local else "Trainer")


@transaction.atomic
def _get_or_create_user(email: str) -> User | None:
    """Return an active user for this email, creating one when missing. Inactive accounts are ignored."""
    existing = User.objects.select_for_update().filter(email__iexact=email).first()
    if existing is not None:
        return existing if existing.is_active else None
    username = _unique_username(email)
    try:
        return User.objects.create_user(
            username=username,
            email=email,
            password=None,
            display_name=_display_name_from_email(email),
        )
    except IntegrityError:
        return User.objects.filter(email__iexact=email, is_active=True).first()


def request_magic_link(email: str) -> None:
    normalized = email.strip().lower()
    user = _get_or_create_user(normalized)
    if user is None:
        return
    cooldown_key = f"magic-link-sent:{user.pk}"
    if not cache.add(cooldown_key, True, EMAIL_COOLDOWN_SECONDS):
        return
    language = user.preferred_language if user.preferred_language in BODIES else "en"
    timeout_minutes = settings.MAGIC_LINK_TIMEOUT // 60
    body = BODIES[language].format(link=magic_link(user), minutes=timeout_minutes)
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
def confirm_magic_link(uid: str, token: str) -> tuple[str, str, User]:
    user = _locked_user(uid)
    if user is None or not _token_valid(user, token):
        raise ValidationError({"detail": INVALID_LINK})
    update_last_login(None, user)
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh), user
