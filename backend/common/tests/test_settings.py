import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase


BACKEND_DIR = Path(__file__).resolve().parents[2]
CONFIG_PREFIXES = ("DJANGO_", "POSTGRES_", "CORS_", "EMAIL_", "DEFAULT_FROM_EMAIL", "FRONTEND_URL", "REDIS_URL")
PROBE = (
    "import config.settings as s; "
    "print(s.DEBUG, s.DATABASES['default']['ENGINE'], "
    "getattr(s, 'SECURE_SSL_REDIRECT', None), getattr(s, 'SESSION_COOKIE_SECURE', None))"
)
BASE = {
    "DJANGO_SECRET_KEY": "test-only-" + "x" * 50,
    "DJANGO_PASSWORD_PEPPER": "test-pepper-" + "p" * 40,
    "DJANGO_ALLOWED_HOSTS": "api.example.com",
    "CORS_ALLOWED_ORIGINS": "https://app.example.com",
    "FRONTEND_URL": "https://app.example.com",
}
POSTGRES = {"POSTGRES_DB": "pokefind", "POSTGRES_USER": "app", "POSTGRES_PASSWORD": "pw", "POSTGRES_HOST": "db"}
EMAIL = {"EMAIL_HOST": "smtp.example.com", "DEFAULT_FROM_EMAIL": "PokeFind <no-reply@example.com>"}


def load_settings(**variables: str) -> subprocess.CompletedProcess:
    """Import the settings module in a fresh interpreter that sees only the given config variables."""
    env = {key: value for key, value in os.environ.items() if not key.startswith(CONFIG_PREFIXES)}
    env.update({"DJANGO_ENV_FILE": os.devnull, **variables})
    return subprocess.run([sys.executable, "-c", PROBE], cwd=BACKEND_DIR, env=env, capture_output=True, text=True)


def without_key(values: dict[str, str], name: str) -> dict[str, str]:
    return {key: value for key, value in values.items() if key != name}


def without(name: str) -> dict[str, str]:
    return without_key(BASE, name)


class SettingsFromEnvironmentTests(SimpleTestCase):
    def test_secret_key_has_no_fallback(self):
        result = load_settings(**without("DJANGO_SECRET_KEY"), DJANGO_DEBUG="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", result.stderr)

    def test_allowed_hosts_and_cors_have_no_fallback(self):
        for name in ("DJANGO_ALLOWED_HOSTS", "CORS_ALLOWED_ORIGINS"):
            result = load_settings(**without(name), DJANGO_DEBUG="1")
            self.assertNotEqual(result.returncode, 0, name)
            self.assertIn(name, result.stderr)

    def test_debug_is_off_by_default_and_then_postgres_is_required(self):
        result = load_settings(**BASE)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("POSTGRES_DB", result.stderr)

    def test_postgres_password_has_no_fallback(self):
        result = load_settings(**BASE, **without_key(POSTGRES, "POSTGRES_PASSWORD"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("POSTGRES_PASSWORD", result.stderr)

    def test_production_turns_on_https_protections(self):
        result = load_settings(**BASE, **POSTGRES, **EMAIL)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ["False", "django.db.backends.postgresql", "True", "True"])

    def test_debug_mode_allows_sqlite(self):
        result = load_settings(**BASE, DJANGO_DEBUG="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split()[:2], ["True", "django.db.backends.sqlite3"])

    def test_password_pepper_is_required_and_long(self):
        for variables in (without("DJANGO_PASSWORD_PEPPER"), {**BASE, "DJANGO_PASSWORD_PEPPER": "too-short"}):
            result = load_settings(**variables, DJANGO_DEBUG="1")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("DJANGO_PASSWORD_PEPPER", result.stderr)

    def test_frontend_url_is_required_and_https_in_production(self):
        missing = load_settings(**without("FRONTEND_URL"), DJANGO_DEBUG="1")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("FRONTEND_URL", missing.stderr)
        plain_http = load_settings(**{**BASE, "FRONTEND_URL": "http://app.example.com"}, **POSTGRES, **EMAIL)
        self.assertNotEqual(plain_http.returncode, 0)
        self.assertIn("https", plain_http.stderr)

    def test_production_requires_an_email_server(self):
        result = load_settings(**BASE, **POSTGRES)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("EMAIL_HOST", result.stderr)

    def test_smtp_requires_a_from_address(self):
        result = load_settings(**BASE, EMAIL_HOST="smtp.example.com", DJANGO_DEBUG="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DEFAULT_FROM_EMAIL", result.stderr)
