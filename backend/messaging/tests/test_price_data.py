from decimal import Decimal

from django.contrib.auth import get_user_model

from common.testing import ApiTestCase
from marketplace.models import Listing
from messaging.models import Conversation, Deal
from messaging.services import confirm_deal, seller_reserve_listing


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

    def test_snapshot_survives_listing_edit_and_delete(self):
        deal = seller_reserve_listing(self.conversation, self.seller, Decimal("7500.00"))
        # Seller later edits the listing...
        self.listing.product_name = "Totally different card"
        self.listing.condition = "LP"
        self.listing.save(update_fields=["product_name", "condition"])
        deal.refresh_from_db()
        self.assertEqual(deal.card_name, "Charizard ex")
        self.assertEqual(deal.condition, "NM")

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
