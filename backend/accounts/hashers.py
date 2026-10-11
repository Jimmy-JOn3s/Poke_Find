import hashlib
import hmac

from django.conf import settings
from django.contrib.auth.hashers import Argon2PasswordHasher
from django.utils.encoding import force_bytes


class PepperedArgon2PasswordHasher(Argon2PasswordHasher):
    """Argon2id over HMAC-SHA256(pepper, password).

    Django adds a random salt per user, and Argon2id makes every guess slow and memory-hungry. The pepper
    (DJANGO_PASSWORD_PEPPER) is a secret key that never touches the database, so a stolen database alone
    can't be cracked. Changing or losing the pepper invalidates every password hashed with it.
    """

    algorithm = "argon2_peppered"

    @staticmethod
    def _pepper(password):
        return hmac.new(force_bytes(settings.PASSWORD_PEPPER), force_bytes(password), hashlib.sha256).hexdigest()

    def encode(self, password, salt):
        return super().encode(self._pepper(password), salt)

    def verify(self, password, encoded):
        return super().verify(self._pepper(password), encoded)
