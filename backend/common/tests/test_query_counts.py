"""List endpoints must cost the same number of queries however many rows they return (no N+1)."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from common.testing import ApiTestCase
from marketplace.models import Listing, SavedListing
from messaging.models import Conversation, Deal, Message, Offer, Review
from messaging.services import confirm_deal, transition_offer

PASSWORD = "a-long-pass-81"


class ListQueryCountTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.User = User
        self.seller = User.objects.create_user(
            username="q-seller", email="q-seller@example.com", password=PASSWORD, role="business", display_name="Seller",
        )
        self.made = 0

    def add_rows(self, count):
        """Each row: a buyer with an open deal and a completed, reviewed deal, chat messages, and a saved listing."""
        for index in range(self.made, self.made + count):
            buyer = self.User.objects.create_user(
                username=f"q-buyer{index}", email=f"q-buyer{index}@example.com", password=PASSWORD, display_name=f"Buyer {index}",
            )
            for kind in ("open", "done"):
                listing = Listing.objects.create(
                    seller=self.seller, product_name=f"Card {index} {kind}", set_name="SV", set_code="Q1",
                    card_number=f"{index}{kind}", condition="NM", card_language="en", rarity="rare",
                    asking_price="500.00", currency="THB", status="active",
                )
                conversation = Conversation.objects.create(listing=listing, buyer=buyer, seller=self.seller)
                for number in range(3):
                    Message.objects.create(conversation=conversation, author=buyer, body=f"message {number}")
                offer = Offer.objects.create(conversation=conversation, proposer=buyer, amount=Decimal("450"), currency="THB")
                transition_offer(offer, self.seller, "accept")
                if kind == "done":
                    deal = Deal.objects.get(conversation=conversation)
                    confirm_deal(deal, buyer)
                    confirm_deal(deal, self.seller)
                    Review.objects.create(deal=deal, reviewer=self.seller, reviewee=buyer, rating=5)
            free = Listing.objects.create(
                seller=buyer, product_name=f"Free {index}", set_name="SV", set_code="Q2", card_number=str(index),
                condition="NM", card_language="en", rarity="rare", asking_price="100.00", currency="THB", status="active",
            )
            SavedListing.objects.create(user=self.seller, listing=free)
        self.made += count

    def queries_for(self, path):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(path)
        self.assertEqual(response.status_code, 200, path)
        return len(queries), response.data["results"]

    def assert_flat(self, path):
        self.client.force_authenticate(self.seller)
        self.add_rows(2)
        small, small_rows = self.queries_for(path)
        self.add_rows(5)
        large, large_rows = self.queries_for(path)
        self.assertGreater(len(large_rows), len(small_rows), "the second request must return more rows")
        self.assertEqual(large, small, f"{path} ran {small} queries for {len(small_rows)} rows but {large} for {len(large_rows)}")
        return large_rows

    def test_inbox_query_count_does_not_grow_with_conversations(self):
        self.assert_flat("/api/v1/conversations/")

    def test_deals_query_count_does_not_grow_with_deals(self):
        self.assert_flat("/api/v1/deals/")

    def test_listings_query_count_does_not_grow_for_a_signed_in_user(self):
        self.assert_flat("/api/v1/listings/")

    def test_saved_listings_query_count_does_not_grow(self):
        self.assert_flat("/api/v1/listings/saved/")


class ListValuesTests(ApiTestCase):
    """The bulk-loaded values must equal what the per-row code returned."""

    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.seller = User.objects.create_user(username="v-seller", email="v-seller@example.com", password=PASSWORD, display_name="Seller")
        self.buyer = User.objects.create_user(username="v-buyer", email="v-buyer@example.com", password=PASSWORD, display_name="Buyer")
        self.listings = [
            Listing.objects.create(
                seller=self.seller, product_name=f"Card {n}", set_name="SV", set_code="V1", card_number=str(n),
                condition="NM", card_language="en", rarity="rare", asking_price="500.00", currency="THB", status="active",
            ) for n in range(3)
        ]
        self.conversations = [Conversation.objects.create(listing=item, buyer=self.buyer, seller=self.seller) for item in self.listings]

    def say(self, conversation, author, body):
        return Message.objects.create(conversation=conversation, author=author, body=body)

    def inbox(self, user):
        self.client.force_authenticate(user)
        return {row["id"]: row for row in self.client.get("/api/v1/conversations/").data["results"]}

    def test_inbox_unread_counts_and_latest_messages(self):
        first, second, empty = self.conversations
        self.say(first, self.buyer, "one"); self.say(first, self.buyer, "two"); self.say(first, self.seller, "reply")
        self.say(second, self.buyer, "old")
        Conversation.objects.filter(pk=second.pk).update(seller_read_at=timezone.now())
        newest = self.say(second, self.buyer, "new")

        seller_view = self.inbox(self.seller)
        self.assertEqual(seller_view[first.pk]["unread_count"], 2)       # own reply is not unread
        self.assertEqual(seller_view[first.pk]["latest_message"]["body"], "reply")
        self.assertEqual(seller_view[second.pk]["unread_count"], 1)      # only the one after reading
        self.assertEqual(seller_view[second.pk]["latest_message"]["id"], newest.pk)
        self.assertEqual(seller_view[empty.pk]["unread_count"], 0)
        self.assertIsNone(seller_view[empty.pk]["latest_message"])

        buyer_view = self.inbox(self.buyer)
        self.assertEqual(buyer_view[first.pk]["unread_count"], 1)        # the seller's reply
        self.assertEqual(buyer_view[second.pk]["unread_count"], 0)

        # A single conversation (no list) reports the same numbers.
        self.client.force_authenticate(self.seller)
        detail = self.client.get(f"/api/v1/conversations/{first.pk}/").data
        self.assertEqual((detail["unread_count"], detail["latest_message"]["body"]), (2, "reply"))

    def test_marking_read_returns_the_updated_unread_count(self):
        conversation = self.conversations[0]
        last = [self.say(conversation, self.buyer, text) for text in ("a", "b")][-1]
        self.client.force_authenticate(self.seller)
        response = self.client.post(f"/api/v1/conversations/{conversation.pk}/read/", {"message_id": last.pk}, format="json")
        self.assertEqual(response.data["unread_count"], 0)

    def test_is_saved_is_per_user_in_lists_and_detail(self):
        saved, other, _ = self.listings
        SavedListing.objects.create(user=self.buyer, listing=saved)
        self.client.force_authenticate(self.buyer)
        rows = {row["id"]: row["is_saved"] for row in self.client.get("/api/v1/listings/").data["results"]}
        self.assertEqual((rows[saved.pk], rows[other.pk]), (True, False))
        self.assertIs(self.client.get(f"/api/v1/listings/{saved.pk}/").data["is_saved"], True)
        self.assertEqual([row["id"] for row in self.client.get("/api/v1/listings/saved/").data["results"]], [saved.pk])
        self.client.force_authenticate(self.seller)
        rows = {row["id"]: row["is_saved"] for row in self.client.get("/api/v1/listings/").data["results"]}
        self.assertIs(rows[saved.pk], False)
        self.client.force_authenticate(None)
        self.assertIs(self.client.get("/api/v1/listings/").data["results"][0]["is_saved"], False)

    def test_deal_list_reports_who_has_reviewed(self):
        offer = Offer.objects.create(conversation=self.conversations[0], proposer=self.buyer, amount=Decimal("450"), currency="THB")
        transition_offer(offer, self.seller, "accept")
        deal = Deal.objects.get(conversation=self.conversations[0])
        confirm_deal(deal, self.buyer); confirm_deal(deal, self.seller)
        Review.objects.create(deal=deal, reviewer=self.buyer, reviewee=self.seller, rating=4)
        for user, expected in ((self.buyer, True), (self.seller, False)):
            self.client.force_authenticate(user)
            self.assertIs(self.client.get("/api/v1/deals/").data["results"][0]["reviewer_has_reviewed"], expected)
