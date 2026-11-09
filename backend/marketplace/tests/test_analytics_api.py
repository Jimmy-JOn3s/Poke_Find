from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status

from common.testing import ApiTestCase
from marketplace.models import Listing
from messaging.models import Conversation, Deal, Offer

User = get_user_model()


class BusinessAnalyticsApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.seller = User.objects.create_user(
            username="shop", email="shop@test.local", password="strong-pass-123",
            display_name="Shop", role=User.Role.BUSINESS, preferred_currency="THB",
            is_email_verified=True, is_verified_seller=True,
        )
        self.buyer = User.objects.create_user(
            username="buyer", email="buyer@test.local", password="strong-pass-123",
            display_name="Buyer",
        )
        self.personal = User.objects.create_user(
            username="person", email="person@test.local", password="strong-pass-123",
            display_name="Person", role=User.Role.PERSONAL,
        )
        listing = Listing.objects.create(
            seller=self.seller, product_name="Pikachu", set_name="151", set_code="SV",
            card_number="025", condition="NM", card_language="en", rarity="rare",
            asking_price=Decimal("1000"), currency="THB", quantity=1, status="sold",
        )
        conversation = Conversation.objects.create(listing=listing, buyer=self.buyer, seller=self.seller)
        offer = Offer.objects.create(
            conversation=conversation, proposer=self.buyer, amount=Decimal("900"), currency="THB", status="accepted",
        )
        Deal.objects.create(
            conversation=conversation, accepted_offer=offer, final_price=Decimal("900"), currency="THB",
            card_name="Pikachu", status=Deal.Status.COMPLETED,
            buyer_confirmed=True, seller_confirmed=True,
            completed_at=timezone.now(),
        )

    def test_personal_user_forbidden(self):
        self.client.force_authenticate(self.personal)
        response = self.client.get("/api/analytics/me/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_business_user_gets_summary(self):
        self.client.force_authenticate(self.seller)
        response = self.client.get("/api/analytics/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["transactions"], 1)
        self.assertEqual(response.data["revenue_by_currency"]["THB"], "900.00")
        self.assertEqual(len(response.data["recent_sales"]), 1)
