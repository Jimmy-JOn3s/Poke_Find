from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.test import override_settings
from django.utils import timezone
from rest_framework import status

from common.testing import ApiTestCase
from marketplace.models import Listing
from messaging.models import Conversation, Deal, Offer
from messaging.services import confirm_deal, expire_stale_deals, force_cancel_deal, transition_offer
from messaging.stale_deals import is_deal_stale


PASSWORD = "a-long-pass-81"


class StaleDealTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.seller = User.objects.create_user(
            username="stale-seller", email="stale-seller@example.com", password=PASSWORD, display_name="Seller",
            role="business",
        )
        self.buyer = User.objects.create_user(
            username="stale-buyer", email="stale-buyer@example.com", password=PASSWORD, display_name="Buyer",
        )
        self.staff = User.objects.create_user(
            username="stale-admin", email="stale-admin@example.com", password=PASSWORD, display_name="Admin", is_staff=True,
        )
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Test Card", set_name="SV", set_code="T1",
            card_number="001", condition="NM", card_language="en", rarity="rare",
            asking_price="500.00", currency="THB", status="active",
        )
        self.conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)

    def auth(self, user):
        response = self.client.post("/api/auth/login/", {"username": user.email, "password": PASSWORD}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def open_deal(self):
        offer = Offer.objects.create(
            conversation=self.conversation, proposer=self.buyer, amount=Decimal("450.00"), currency="THB",
        )
        transition_offer(offer, self.seller, "accept")
        self.listing.refresh_from_db()
        return Deal.objects.get(conversation=self.conversation, status=Deal.Status.ACCEPTED)

    @override_settings(STALE_DEAL_DAYS_OPEN=7, STALE_DEAL_DAYS_PARTIAL=3)
    def test_force_cancel_after_one_confirm_releases_listing(self):
        deal = self.open_deal()
        confirm_deal(deal, self.buyer)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.RESERVED)
        self.auth(self.buyer)
        self.assertEqual(self.client.post(f"/api/deals/{deal.id}/cancel/").status_code, 400)
        force_cancel_deal(deal)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.ACTIVE)
        deal.refresh_from_db()
        self.assertEqual(deal.status, Deal.Status.CANCELLED)

    @override_settings(STALE_DEAL_DAYS_PARTIAL=3)
    def test_expire_stale_partial_deal(self):
        deal = self.open_deal()
        confirm_deal(deal, self.buyer)
        Deal.objects.filter(pk=deal.pk).update(first_confirmed_at=timezone.now() - timedelta(days=4))
        self.assertTrue(is_deal_stale(Deal.objects.get(pk=deal.pk)))
        self.assertEqual(expire_stale_deals(), {"completed": 1, "awaiting_buyer": 0, "cancelled": 0, "failed": 0})
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.SOLD)

    @override_settings(STALE_DEAL_DAYS_OPEN=10)
    def test_admin_force_cancel_endpoint(self):
        deal = self.open_deal()
        confirm_deal(deal, self.buyer)
        self.auth(self.staff)
        response = self.client.post(f"/api/admin/deals/{deal.id}/force-cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.ACTIVE)