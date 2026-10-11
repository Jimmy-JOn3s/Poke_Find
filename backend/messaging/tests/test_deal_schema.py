from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from common.testing import ApiTestCase
from marketplace.models import Listing
from messaging.models import Conversation, Deal, Offer


User = get_user_model()


class DealSchemaTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.seller = User.objects.create_user(username="seller-d", email="seller-d@example.com", password="pw", display_name="S")
        self.buyer = User.objects.create_user(username="buyer-d", email="buyer-d@example.com", password="pw", display_name="B")
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Pikachu", condition="NM", card_language="ja", rarity="rare",
            asking_price=Decimal("10.00"), currency="THB", quantity=1, status="reserved",
        )
        self.conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)

    def make_deal(self, amount, status=Deal.Status.ACCEPTED):
        offer = Offer.objects.create(
            conversation=self.conversation, proposer=self.buyer, amount=Decimal(amount), currency="THB", status="accepted",
        )
        return Deal.objects.create(
            conversation=self.conversation, accepted_offer=offer, final_price=offer.amount, currency="THB", status=status,
        )

    def test_database_allows_only_one_live_deal_per_conversation(self):
        self.make_deal("10.00")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_deal("9.00")

    def test_cancelled_deal_does_not_block_a_new_one_and_is_hidden(self):
        self.make_deal("10.00", status=Deal.Status.CANCELLED)
        live = self.make_deal("9.00")
        self.client.force_authenticate(self.buyer)
        data = self.client.get(f"/api/conversations/{self.conversation.id}/").data
        self.assertEqual(data["deal"]["id"], live.id)

    def test_conversation_with_only_cancelled_deals_reports_no_deal(self):
        self.make_deal("10.00", status=Deal.Status.CANCELLED)
        self.client.force_authenticate(self.buyer)
        self.assertIsNone(self.client.get(f"/api/conversations/{self.conversation.id}/").data["deal"])
