import io
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from messaging.models import Deal

from marketplace.models import Listing


@override_settings(DEBUG=True)
class SeedMarketIntelligenceTests(TestCase):
    def test_creates_grouped_completed_sales(self):
        with mock.patch.dict(os.environ, {"DEMO_SEED_PASSWORD": "a-demo-pass-123"}):
            call_command("seed_market_intelligence", "--count=25", stdout=io.StringIO())

        self.assertEqual(Listing.objects.filter(set_code="MI-DEMO").count(), 25)
        grouped = Deal.objects.filter(
            card_name="Pikachu ex",
            card_set="SV2a 151",
            status=Deal.Status.COMPLETED,
        )
        self.assertEqual(grouped.count(), 25)
        self.assertTrue(get_user_model().objects.filter(username="mi-demo-seller").exists())