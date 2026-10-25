from decimal import Decimal
from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models.deletion import ProtectedError

from common.testing import ApiTestCase
from marketplace.models import Listing
from messaging.models import Conversation, Deal
from messaging.services import confirm_deal, place_offer, seller_reserve_listing, transition_offer


User = get_user_model()


class DealPriceDataSnapshotTests(ApiTestCase):
    """A completed deal keeps its own price, card, condition and date, independent of the listing."""

    def setUp(self):
        super().setUp()
        self.seller = User.objects.create_user(
            username="seller-pd", email="seller-pd@example.com", password="pw", display_name="S",
        )
        self.buyer = User.objects.create_user(
            username="buyer-pd", email="buyer-pd@example.com", password="pw", display_name="B",
        )
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Charizard ex", set_name="Obsidian Flames",
            condition="NM", card_language="en", rarity="rare",
            asking_price=Decimal("8000.00"), currency="THB", quantity=1, status="active",
        )
        self.conversation = Conversation.objects.create(
            listing=self.listing, buyer=self.buyer, seller=self.seller,
        )

    def test_deal_snapshots_card_and_condition_on_creation(self):
        deal = seller_reserve_listing(self.conversation, self.seller, Decimal("7500.00"))
        self.assertEqual(deal.card_name, "Charizard ex")
        self.assertEqual(deal.card_set, "Obsidian Flames")
        self.assertEqual(deal.condition, "NM")
        self.assertEqual(str(deal.final_price), "7500.00")

    def test_snapshot_survives_listing_edit(self):
        deal = seller_reserve_listing(self.conversation, self.seller, Decimal("7500.00"))
        # Seller later edits the listing...
        self.listing.product_name = "Totally different card"
        self.listing.condition = "LP"
        self.listing.set_name = "Different set"
        self.listing.asking_price = Decimal("9000.00")
        self.listing.currency = "USD"
        self.listing.save(update_fields=["product_name", "condition", "set_name", "asking_price", "currency"])
        deal.refresh_from_db()
        self.assertEqual(deal.card_name, "Charizard ex")
        self.assertEqual(deal.condition, "NM")
        self.assertEqual(deal.card_set, "Obsidian Flames")
        self.assertEqual(deal.final_price, Decimal("7500.00"))
        self.assertEqual(deal.currency, "THB")

    def test_accepted_offer_captures_current_listing_and_agreed_price(self):
        offer = place_offer(self.conversation, self.buyer, Decimal("7200.00"), "THB")
        # Acceptance must read the locked listing, even when the caller has a cached conversation.
        self.conversation.listing
        Listing.objects.filter(pk=self.listing.pk).update(condition="LP")
        transition_offer(offer, self.seller, "accept")
        deal = Deal.objects.get(accepted_offer=offer)
        self.assertEqual(deal.condition, "LP")
        self.assertEqual(deal.card_name, "Charizard ex")
        self.assertEqual(deal.card_set, "Obsidian Flames")
        self.assertEqual(deal.final_price, Decimal("7200.00"))
        self.assertEqual(deal.currency, "THB")

    def test_traded_listing_deletion_is_protected(self):
        deal = seller_reserve_listing(self.conversation, self.seller, Decimal("7500.00"))
        with self.assertRaises(ProtectedError):
            self.listing.delete()
        self.assertTrue(Deal.objects.filter(pk=deal.pk).exists())

    def test_admin_cannot_edit_price_snapshot(self):
        deal_admin = admin.site._registry[Deal]
        fields = {"card_name", "card_set", "condition", "final_price", "currency", "completed_at"}
        self.assertTrue(fields.issubset(deal_admin.get_readonly_fields(None)))

    def test_backfill_populates_legacy_deal_snapshot(self):
        deal = seller_reserve_listing(self.conversation, self.seller, Decimal("7500.00"))
        Deal.objects.filter(pk=deal.pk).update(card_name="", card_set="", condition="")
        migration = import_module("messaging.migrations.0007_backfill_deal_card_snapshot")
        migration.backfill_card_snapshot(apps, SimpleNamespace(connection=connection))
        deal.refresh_from_db()
        self.assertEqual(deal.card_name, "Charizard ex")
        self.assertEqual(deal.card_set, "Obsidian Flames")
        self.assertEqual(deal.condition, "NM")
        self.assertEqual(deal.final_price, Decimal("7500.00"))

    def test_completed_deal_record_is_intact(self):
        deal = seller_reserve_listing(self.conversation, self.seller, Decimal("7500.00"))
        confirm_deal(deal, self.buyer)
        confirm_deal(deal, self.seller)
        deal.refresh_from_db()
        self.assertEqual(deal.status, Deal.Status.COMPLETED)
        self.assertIsNotNone(deal.completed_at)
        # The four columns the price dataset is built from:
        self.assertEqual(deal.card_name, "Charizard ex")
        self.assertEqual(deal.condition, "NM")
        self.assertEqual(str(deal.final_price), "7500.00")
        self.assertEqual(deal.currency, "THB")
        completed_at = deal.completed_at
        confirm_deal(deal, self.buyer)
        deal.refresh_from_db()
        self.assertEqual(deal.completed_at, completed_at)
