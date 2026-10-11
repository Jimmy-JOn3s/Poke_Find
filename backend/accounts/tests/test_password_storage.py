from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.test import override_settings

from common.testing import ApiTestCase


User = get_user_model()
PASSWORD = "a-long-pass-81"


class PasswordStorageTests(ApiTestCase):
    def test_new_passwords_use_peppered_argon2id(self):
        encoded = make_password(PASSWORD)
        self.assertTrue(encoded.startswith("argon2_peppered$argon2id$"), encoded)
        self.assertTrue(check_password(PASSWORD, encoded))
        self.assertFalse(check_password(PASSWORD + "x", encoded))

    def test_each_hash_gets_its_own_salt(self):
        self.assertNotEqual(make_password(PASSWORD), make_password(PASSWORD))

    def test_a_hash_is_useless_without_the_pepper(self):
        encoded = make_password(PASSWORD)
        with override_settings(PASSWORD_PEPPER="a-different-pepper-" + "y" * 30):
            self.assertFalse(check_password(PASSWORD, encoded))

    def test_old_pbkdf2_hashes_still_log_in_and_are_upgraded(self):
        user = User.objects.create(
            username="legacy", email="legacy@example.com", password=make_password(PASSWORD, hasher="pbkdf2_sha256"),
        )
        response = self.client.post(
            "/api/auth/login/", {"username": "legacy@example.com", "password": PASSWORD}, format="json",
        )
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.password.startswith("argon2_peppered$"), user.password)
