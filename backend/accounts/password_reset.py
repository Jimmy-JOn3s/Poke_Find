import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


logger = logging.getLogger(__name__)
User = get_user_model()

EMAIL_COOLDOWN_SECONDS = 5 * 60
INVALID_LINK = "This reset link is invalid or has expired. Ask for a new one."
SUBJECTS = {"th": "ตั้งรหัสผ่าน PokeFind ใหม่", "en": "Reset your PokeFind password"}
BODIES = {
    "th": (
        "มีคำขอตั้งรหัสผ่านใหม่สำหรับบัญชี PokeFind ของคุณ\n\n"
        "เปิดลิงก์นี้ภายใน {minutes} นาทีเพื่อตั้งรหัสผ่านใหม่:\n{link}\n\n"
        "หากคุณไม่ได้ขอ ไม่ต้องทำอะไร รหัสผ่านเดิมยังใช้ได้"
    ),
    "en": (
        "Someone asked to reset the password for your PokeFind account.\n\n"
        "Open this link within {minutes} minutes to choose a new password:\n{link}\n\n"
        "If it wasn't you, ignore this email; your password stays the same."
    ),
}


def reset_link(user) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    # The fragment (#...) never reaches a server or a Referer header, so the token stays in the browser.
    return f"{settings.FRONTEND_URL}/#reset_uid={uid}&reset_token={token}"


def request_password_reset(email: str) -> None:
    """Email a reset link if an active account uses this address. Callers answer the same way either way."""
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None or not user.has_usable_password():
        return
    # At most one email per account per cooldown, so nobody can flood someone else's inbox.
    cooldown_key = f"password-reset-sent:{user.pk}"
    if not cache.add(cooldown_key, True, EMAIL_COOLDOWN_SECONDS):
        return
    language = user.preferred_language if user.preferred_language in BODIES else "en"
    body = BODIES[language].format(link=reset_link(user), minutes=settings.PASSWORD_RESET_TIMEOUT // 60)
    try:
        send_mail(SUBJECTS[language], body, None, [user.email])
    except Exception:
        # A 500 here would reveal that the account exists; log it and let the user try again.
        cache.delete(cooldown_key)
        logger.exception("Could not send the password-reset email for user %s", user.pk)


def _locked_user(uid: str):
    try:
        user_id = urlsafe_base64_decode(uid).decode()
    except ValueError:  # bad base64 or not UTF-8 (UnicodeDecodeError is a ValueError)
        return None
    if not user_id.isdecimal():  # not isdigit(): it accepts "²", which int() rejects
        return None
    return User.objects.select_for_update().filter(pk=int(user_id), is_active=True).first()


@transaction.atomic
def confirm_password_reset(uid: str, token: str, new_password: str) -> None:
    # The row lock makes two requests with the same link run one after the other. The second one then fails
    # the token check, because the token is bound to the password hash the first one just changed.
    user = _locked_user(uid)
    if user is None or not default_token_generator.check_token(user, token):
        raise ValidationError({"detail": INVALID_LINK})
    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        raise ValidationError({"new_password": list(exc.messages)}) from exc
    user.set_password(new_password)
    user.save(update_fields=["password"])
    # Sign out every device. The password fingerprint in each token already ends them (CHECK_REVOKE_TOKEN);
    # blacklisting as well keeps them dead even if that setting is ever turned off.
    open_tokens = OutstandingToken.objects.filter(user=user, blacklistedtoken__isnull=True)
    BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=token) for token in open_tokens], ignore_conflicts=True,
    )
