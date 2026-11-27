from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status

from common.testing import ApiTestCase
from marketplace.models import Listing, PriceObservation
from messaging.models import Conversation, Deal, Offer


User = get_user_model()


class VariantMarketApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.seller = User.objects.create_user(
            username="seller-mk", email="seller-mk@example.com", password="pw", display_name="S",
        )
        self.buyer = User.objects.create_user(
            username="buyer-mk", email="buyer-mk@example.com", password="pw", display_name="B",
        )
        self.listing = Listing.objects.create(
            seller=self.seller,
            product_name="Pikachu",
            set_name="Base",
            set_code="BASE",
            card_number="58/102",
            condition="NM",
            card_language="en",
            rarity="common",
            asking_price=Decimal("500.00"),
            currency="THB",
            quantity=1,
            status="sold",
        )
        self.variant_key = "en:base:58/102:NM"

    def _completed_deal(self, final_price: str):
        conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)
        offer = Offer.objects.create(
            conversation=conversation,
            proposer=self.buyer,
            amount=Decimal(final_price),
            currency="THB",
            status=Offer.Status.ACCEPTED,
        )
        deal = Deal.objects.create(
            conversation=conversation,
            accepted_offer=offer,
            final_price=Decimal(final_price),
            currency="THB",
            card_name=self.listing.product_name,
            card_set=self.listing.set_name,
            set_code=self.listing.set_code,
            card_number=self.listing.card_number,
            card_language=self.listing.card_language,
            condition=self.listing.condition,
            asking_price=self.listing.asking_price,
            quantity=1,
            variant_key=self.variant_key,
            status=Deal.Status.COMPLETED,
            buyer_confirmed=True,
            seller_confirmed=True,
            completed_at=timezone.now(),
        )
        PriceObservation.objects.create(
            deal=deal,
            variant_key=self.variant_key,
            card_language="en",
            set_code="BASE",
            card_number="58/102",
            condition="NM",
            asking_price=Decimal("500.00"),
            final_price=Decimal(final_price),
            currency="THB",
            quantity=1,
            traded_at=deal.completed_at,
        )

    def test_variant_key_query_returns_counts_without_recommendation(self):
        self._completed_deal("480.00")
        response = self.client.get(f"/api/market/variant/?variant_key={self.variant_key}&currency=THB")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["completed_sales"], 1)
        self.assertEqual(response.data["min_sales_for_recommendation"], 20)
        self.assertFalse(response.data["sufficient_data"])
        self.assertIsNone(response.data["recommendation"])

    def test_parts_query_builds_variant_key(self):
        response = self.client.get(
            "/api/market/variant/?card_language=en&set_code=BASE&card_number=58/102&condition=NM",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["variant_key"], self.variant_key)