from decimal import Decimal
from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection

from common.testing import ApiTestCase
from marketplace.models import Listing
from messaging.models import Conversation, Deal, Offer


User = get_user_model()


class DealPriceDataMigrationTests(ApiTestCase):
    def test_backfill_populates_legacy_deal_snapshot(self):
        seller = User.objects.create_user(username="seller-migration", email="seller-migration@example.com", password="pw")
        buyer = User.objects.create_user(username="buyer-migration", email="buyer-migration@example.com", password="pw")
        listing = Listing.objects.create(
            seller=seller, product_name="Charizard ex", set_name="Obsidian Flames",
            condition="NM", card_language="en", rarity="rare",
            asking_price=Decimal("8000.00"), currency="THB",
        )
        conversation = Conversation.objects.create(listing=listing, buyer=buyer, seller=seller)
        offer = Offer.objects.create(
            conversation=conversation, proposer=buyer, amount=Decimal("7500.00"),
            currency="THB", status=Offer.Status.ACCEPTED,
        )
        deal = Deal.objects.create(
            conversation=conversation, accepted_offer=offer, final_price=offer.amount, currency=offer.currency,
        )
        migration = import_module("messaging.migrations.0007_backfill_deal_card_snapshot")
        migration.backfill_card_snapshot(apps, SimpleNamespace(connection=connection))
        deal.refresh_from_db()
        self.assertEqual(deal.card_name, "Charizard ex")
        self.assertEqual(deal.card_set, "Obsidian Flames")
        self.assertEqual(deal.condition, "NM")
        self.assertEqual(deal.final_price, Decimal("7500.00"))
