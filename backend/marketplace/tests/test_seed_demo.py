import io
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings


class SeedDemoCommandTests(TestCase):
    def test_refuses_to_run_outside_debug(self):
        with override_settings(DEBUG=False), mock.patch.dict(os.environ, {"DEMO_SEED_PASSWORD": "a-demo-pass-123"}):
            with self.assertRaisesMessage(CommandError, "DJANGO_DEBUG=1"):
                call_command("seed_demo")

    @override_settings(DEBUG=True)
    def test_requires_the_password_from_the_environment(self):
        with mock.patch.dict(os.environ, {"DEMO_SEED_PASSWORD": ""}):
            with self.assertRaisesMessage(CommandError, "DEMO_SEED_PASSWORD"):
                call_command("seed_demo")

    @override_settings(DEBUG=True)
    def test_demo_accounts_use_the_configured_password(self):
        with mock.patch.dict(os.environ, {"DEMO_SEED_PASSWORD": "a-demo-pass-123"}):
            call_command("seed_demo", stdout=io.StringIO())
        seller = get_user_model().objects.get(username="demo-seller")
        self.assertTrue(seller.check_password("a-demo-pass-123"))
