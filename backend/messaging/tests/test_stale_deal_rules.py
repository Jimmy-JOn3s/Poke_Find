"""What happens to a deal that sits open too long, for each combination of confirmations.

| Who confirmed      | Result                                                        |
|--------------------|---------------------------------------------------------------|
| both               | completes at once; listing sold                               |
| buyer only         | once overdue: completes; listing sold                         |
| seller only        | once overdue: stays open and reserved, flagged for review     |
| nobody             | once overdue: cancelled; listing back on sale                 |
"""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework import status

from common.testing import ApiTestCase
from marketplace.models import Listing, PriceObservation
from messaging.models import Conversation, Deal, Offer
from messaging.services import confirm_deal, expire_stale_deals, transition_offer
from messaging.stale_deals import StaleOutcome, stale_outcome


PASSWORD = "a-long-pass-81"


@override_settings(STALE_DEAL_DAYS_OPEN=14, STALE_DEAL_DAYS_PARTIAL=7)
class StaleDealRuleTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.seller = User.objects.create_user(
            username="rule-seller", email="rule-seller@example.com", password=PASSWORD, role="business",
        )
        self.buyer = User.objects.create_user(username="rule-buyer", email="rule-buyer@example.com", password=PASSWORD)
        self.staff = User.objects.create_user(
            username="rule-admin", email="rule-admin@example.com", password=PASSWORD, is_staff=True,
        )
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Rule Card", set_name="SV", set_code="R1", card_number="001",
            condition="NM", card_language="en", rarity="rare", asking_price="500.00", currency="THB", status="active",
        )
        self.conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)
        offer = Offer.objects.create(
            conversation=self.conversation, proposer=self.buyer, amount=Decimal("450.00"), currency="THB",
        )
        transition_offer(offer, self.seller, "accept")
        self.deal = Deal.objects.get(conversation=self.conversation, status=Deal.Status.ACCEPTED)

    def auth(self, user):
        response = self.client.post("/api/auth/login/", {"username": user.email, "password": PASSWORD}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def age(self, *, created_days=0, first_confirmed_days=None):
        now = timezone.now()
        fields = {"created_at": now - timedelta(days=created_days)}
        if first_confirmed_days is not None:
            fields["first_confirmed_at"] = now - timedelta(days=first_confirmed_days)
        Deal.objects.filter(pk=self.deal.pk).update(**fields)

    def listing_status(self):
        self.listing.refresh_from_db()
        return self.listing.status

    def fresh_deal(self):
        return Deal.objects.get(pk=self.deal.pk)

    # --- both confirm -------------------------------------------------------------------------

    def test_both_confirming_completes_at_once_and_sells_the_listing(self):
        confirm_deal(self.deal, self.buyer)
        confirm_deal(self.deal, self.seller)
        self.assertEqual(self.fresh_deal().status, Deal.Status.COMPLETED)
        self.assertEqual(self.listing_status(), Listing.Status.SOLD)

    # --- buyer confirms, seller doesn't --------------------------------------------------------

    def test_buyer_only_is_left_alone_before_the_deadline(self):
        confirm_deal(self.deal, self.buyer)
        self.age(created_days=20, first_confirmed_days=6)
        self.assertEqual(expire_stale_deals(), {"completed": 0, "awaiting_buyer": 0, "cancelled": 0})
        self.assertEqual(self.fresh_deal().status, Deal.Status.ACCEPTED)
        self.assertEqual(self.listing_status(), Listing.Status.RESERVED)

    def test_buyer_only_completes_once_overdue_and_the_listing_is_sold(self):
        confirm_deal(self.deal, self.buyer)
        self.age(created_days=20, first_confirmed_days=8)
        self.assertEqual(stale_outcome(self.fresh_deal()), StaleOutcome.COMPLETE)
        self.assertEqual(expire_stale_deals(), {"completed": 1, "awaiting_buyer": 0, "cancelled": 0})
        deal = self.fresh_deal()
        self.assertEqual(deal.status, Deal.Status.COMPLETED)
        self.assertIsNotNone(deal.completed_at)
        # The record stays truthful: the seller never pressed confirm.
        self.assertFalse(deal.seller_confirmed)
        self.assertEqual(self.listing_status(), Listing.Status.SOLD)
        # It is a real sale, so it feeds market price data like any completed deal.
        self.assertTrue(PriceObservation.objects.filter(deal_id=deal.pk).exists())

    def test_an_auto_completed_deal_can_be_reviewed(self):
        confirm_deal(self.deal, self.buyer)
        self.age(created_days=20, first_confirmed_days=8)
        expire_stale_deals()
        self.auth(self.buyer)
        response = self.client.post(f"/api/deals/{self.deal.pk}/review/", {"rating": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

    # --- seller confirms, buyer doesn't --------------------------------------------------------

    def test_seller_only_stays_reserved_once_overdue_and_is_flagged(self):
        confirm_deal(self.deal, self.seller)
        self.age(created_days=20, first_confirmed_days=8)
        self.assertEqual(stale_outcome(self.fresh_deal()), StaleOutcome.AWAIT_BUYER)
        self.assertEqual(expire_stale_deals(), {"completed": 0, "awaiting_buyer": 1, "cancelled": 0})
        self.assertEqual(self.fresh_deal().status, Deal.Status.ACCEPTED)
        self.assertEqual(self.listing_status(), Listing.Status.RESERVED)
        # Running again changes nothing.
        expire_stale_deals()
        self.assertEqual(self.listing_status(), Listing.Status.RESERVED)

    def test_seller_only_overdue_deal_still_completes_when_the_buyer_confirms_late(self):
        confirm_deal(self.deal, self.seller)
        self.age(created_days=20, first_confirmed_days=8)
        expire_stale_deals()
        confirm_deal(self.deal, self.buyer)
        self.assertEqual(self.fresh_deal().status, Deal.Status.COMPLETED)
        self.assertEqual(self.listing_status(), Listing.Status.SOLD)

    def test_staff_can_release_a_seller_only_overdue_deal(self):
        confirm_deal(self.deal, self.seller)
        self.age(created_days=20, first_confirmed_days=8)
        self.auth(self.staff)
        listed = self.client.get("/api/admin/deals/open/?stale=1")
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        row = next(item for item in listed.data["results"] if item["id"] == self.deal.pk)
        self.assertEqual(row["stale_outcome"], StaleOutcome.AWAIT_BUYER)
        response = self.client.post(f"/api/admin/deals/{self.deal.pk}/force-cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.listing_status(), Listing.Status.ACTIVE)

    # --- nobody confirms -----------------------------------------------------------------------

    def test_unconfirmed_deal_is_left_alone_before_the_deadline(self):
        self.age(created_days=13)
        self.assertEqual(expire_stale_deals(), {"completed": 0, "awaiting_buyer": 0, "cancelled": 0})
        self.assertEqual(self.listing_status(), Listing.Status.RESERVED)

    def test_unconfirmed_deal_is_cancelled_once_overdue_and_the_listing_goes_back_on_sale(self):
        self.age(created_days=15)
        self.assertEqual(stale_outcome(self.fresh_deal()), StaleOutcome.CANCEL)
        self.assertEqual(expire_stale_deals(), {"completed": 0, "awaiting_buyer": 0, "cancelled": 1})
        self.assertEqual(self.fresh_deal().status, Deal.Status.CANCELLED)
        self.assertEqual(self.listing_status(), Listing.Status.ACTIVE)

    # --- races and robustness ------------------------------------------------------------------

    def test_a_confirmation_that_lands_mid_run_is_not_cancelled(self):
        self.age(created_days=15)
        overdue = list(Deal.objects.filter(pk=self.deal.pk))
        # The run picked the deal while nobody had confirmed; the buyer confirms before it gets there.
        confirm_deal(self.deal, self.buyer)
        with mock.patch("messaging.stale_deals.stale_open_deals_queryset") as picked:
            picked.return_value.values_list.return_value = [deal.pk for deal in overdue]
            self.assertEqual(expire_stale_deals(), {"completed": 0, "awaiting_buyer": 0, "cancelled": 0})
        deal = self.fresh_deal()
        self.assertEqual(deal.status, Deal.Status.ACCEPTED)
        self.assertTrue(deal.buyer_confirmed)
        self.assertEqual(self.listing_status(), Listing.Status.RESERVED)

    def test_one_broken_deal_does_not_stop_the_others(self):
        # Legacy data: the deal is open but its listing is no longer reserved, so it can't be sold.
        confirm_deal(self.deal, self.buyer)
        self.age(created_days=20, first_confirmed_days=8)
        Listing.objects.filter(pk=self.listing.pk).update(status=Listing.Status.ACTIVE)

        other_listing = Listing.objects.create(
            seller=self.seller, product_name="Other", set_name="SV", set_code="R1", card_number="002",
            condition="NM", card_language="en", rarity="rare", asking_price="300.00", currency="THB", status="active",
        )
        other_conversation = Conversation.objects.create(listing=other_listing, buyer=self.buyer, seller=self.seller)
        other_offer = Offer.objects.create(
            conversation=other_conversation, proposer=self.buyer, amount=Decimal("300.00"), currency="THB",
        )
        transition_offer(other_offer, self.seller, "accept")
        other = Deal.objects.get(conversation=other_conversation)
        Deal.objects.filter(pk=other.pk).update(created_at=timezone.now() - timedelta(days=15))

        with self.assertLogs("messaging.services", "ERROR"):
            self.assertEqual(expire_stale_deals(), {"completed": 0, "awaiting_buyer": 0, "cancelled": 1})
        self.assertEqual(self.fresh_deal().status, Deal.Status.ACCEPTED)
        self.assertEqual(Deal.objects.get(pk=other.pk).status, Deal.Status.CANCELLED)

    def test_admin_release_endpoint_reports_each_outcome(self):
        confirm_deal(self.deal, self.buyer)
        self.age(created_days=20, first_confirmed_days=8)
        self.auth(self.staff)
        response = self.client.post("/api/admin/deals/expire-stale/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"completed": 1, "awaiting_buyer": 0, "cancelled": 0, "released": 0})
