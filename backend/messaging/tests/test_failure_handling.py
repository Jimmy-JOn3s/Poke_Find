"""Failures in side work must be logged, and must not take the user's action down with them."""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import DatabaseError
from django.test import override_settings
from django.utils import timezone

from common.testing import ApiTestCase
from marketplace.models import Listing, PriceObservation
from messaging.models import Conversation, Deal, Offer
from messaging.services import confirm_deal, expire_stale_deals, transition_offer


PASSWORD = "a-long-pass-81"


@override_settings(STALE_DEAL_DAYS_OPEN=14, STALE_DEAL_DAYS_PARTIAL=7)
class FailureHandlingTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.seller = User.objects.create_user(
            username="fail-seller", email="fail-seller@example.com", password=PASSWORD, role="business",
        )
        self.buyer = User.objects.create_user(username="fail-buyer", email="fail-buyer@example.com", password=PASSWORD)

    def open_deal(self, number: str) -> Deal:
        listing = Listing.objects.create(
            seller=self.seller, product_name=f"Card {number}", set_name="SV", set_code="F1", card_number=number,
            condition="NM", card_language="en", rarity="rare", asking_price="500.00", currency="THB", status="active",
        )
        conversation = Conversation.objects.create(listing=listing, buyer=self.buyer, seller=self.seller)
        offer = Offer.objects.create(conversation=conversation, proposer=self.buyer, amount=Decimal("450.00"), currency="THB")
        transition_offer(offer, self.seller, "accept")
        return Deal.objects.get(conversation=conversation)

    def test_deal_still_completes_when_the_price_record_fails_and_backfill_repairs_it(self):
        deal = self.open_deal("001")
        confirm_deal(deal, self.buyer)
        with mock.patch("messaging.services.record_price_observation", side_effect=DatabaseError("down")):
            with self.assertLogs("messaging.services", level="ERROR") as logs:
                confirm_deal(deal, self.seller)
        deal.refresh_from_db()
        self.assertEqual(deal.status, Deal.Status.COMPLETED)
        self.assertEqual(Listing.objects.get(pk=deal.conversation.listing_id).status, Listing.Status.SOLD)
        self.assertFalse(PriceObservation.objects.filter(deal=deal).exists())
        self.assertIn(f"Deal {deal.pk} completed but its price observation was not recorded", logs.output[0])

        call_command("backfill_price_observations", stdout=mock.Mock())
        self.assertTrue(PriceObservation.objects.filter(deal=deal).exists())

    def test_one_broken_deal_does_not_stop_the_stale_batch(self):
        broken, healthy = self.open_deal("002"), self.open_deal("003")
        Deal.objects.update(created_at=timezone.now() - timedelta(days=30))
        from messaging import services
        settle = services._settle_stale_deal

        def flaky(deal_pk):
            if deal_pk == broken.pk:
                raise DatabaseError("row went missing")
            return settle(deal_pk)

        with mock.patch("messaging.services._settle_stale_deal", side_effect=flaky):
            with self.assertLogs("messaging.services", level="INFO") as logs:
                counts = expire_stale_deals()
        self.assertEqual(counts["cancelled"], 1)
        healthy.refresh_from_db()
        broken.refresh_from_db()
        self.assertEqual(healthy.status, Deal.Status.CANCELLED)
        self.assertEqual(broken.status, Deal.Status.ACCEPTED)
        self.assertTrue(any(f"Could not settle stale deal {broken.pk}" in line for line in logs.output))

    def test_deal_lifecycle_is_logged(self):
        with self.assertLogs("messaging.services", level="INFO") as logs:
            deal = self.open_deal("004")
            confirm_deal(deal, self.buyer)
            confirm_deal(deal, self.seller)
        text = "\n".join(logs.output)
        self.assertIn(f"Deal {deal.pk} opened", text)
        self.assertIn(f"Deal {deal.pk} confirmed by user={self.buyer.pk} (buyer_confirmed)", text)
        self.assertIn(f"Deal {deal.pk} completed", text)
