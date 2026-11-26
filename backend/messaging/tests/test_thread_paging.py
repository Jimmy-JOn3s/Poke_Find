"""Paging for a conversation's messages and offers is opt-in, so older clients keep the plain list."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext

from common.testing import ApiTestCase
from marketplace.models import Listing
from messaging.models import Conversation, Message, Offer

PASSWORD = "a-long-pass-81"


class ThreadPagingTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.seller = User.objects.create_user(username="p-seller", email="p-seller@example.com", password=PASSWORD)
        self.buyer = User.objects.create_user(username="p-buyer", email="p-buyer@example.com", password=PASSWORD)
        listing = Listing.objects.create(
            seller=self.seller, product_name="Paged Card", set_name="SV", set_code="P1", card_number="001",
            condition="NM", card_language="en", rarity="rare", asking_price="500.00", currency="THB", status="active",
        )
        self.conversation = Conversation.objects.create(listing=listing, buyer=self.buyer, seller=self.seller)
        self.messages = [
            Message.objects.create(conversation=self.conversation, author=self.buyer, body=f"m{number}") for number in range(7)
        ]
        self.offers = [
            Offer.objects.create(
                conversation=self.conversation, proposer=self.buyer, amount=Decimal(100 + number), currency="THB", status="declined",
            ) for number in range(5)
        ]
        self.base = f"/api/v1/conversations/{self.conversation.pk}"
        self.client.force_authenticate(self.buyer)

    def bodies(self, response):
        return [row["body"] for row in response.data["results"]]

    def test_without_limit_the_whole_thread_is_a_plain_list_on_both_api_paths(self):
        for prefix in ("/api/v1", "/api"):
            response = self.client.get(f"{prefix}/conversations/{self.conversation.pk}/messages/")
            self.assertEqual([row["body"] for row in response.data], [f"m{n}" for n in range(7)])
        self.assertEqual(len(self.client.get(f"{self.base}/offers/").data), 5)

    def test_messages_page_from_the_newest_backwards_and_read_oldest_first(self):
        newest = self.client.get(f"{self.base}/messages/?limit=3")
        self.assertEqual(self.bodies(newest), ["m4", "m5", "m6"])
        self.assertIs(newest.data["has_more"], True)
        middle = self.client.get(f"{self.base}/messages/?limit=3&before={newest.data['results'][0]['id']}")
        self.assertEqual(self.bodies(middle), ["m1", "m2", "m3"])
        oldest = self.client.get(f"{self.base}/messages/?limit=3&before={middle.data['results'][0]['id']}")
        self.assertEqual(self.bodies(oldest), ["m0"])
        self.assertIs(oldest.data["has_more"], False)

    def test_a_page_that_ends_exactly_at_the_start_reports_no_more(self):
        response = self.client.get(f"{self.base}/messages/?limit=7")
        self.assertEqual(len(response.data["results"]), 7)
        self.assertIs(response.data["has_more"], False)

    def test_offers_page_newest_first(self):
        first = self.client.get(f"{self.base}/offers/?limit=2")
        self.assertEqual([row["id"] for row in first.data["results"]], [self.offers[4].pk, self.offers[3].pk])
        self.assertIs(first.data["has_more"], True)
        rest = self.client.get(f"{self.base}/offers/?limit=10&before={self.offers[3].pk}")
        self.assertEqual([row["id"] for row in rest.data["results"]], [offer.pk for offer in self.offers[2::-1]])
        self.assertIs(rest.data["has_more"], False)

    def test_bad_paging_values_are_rejected(self):
        for query in ("limit=0", "limit=101", "limit=abc", "limit=5&before=xyz"):
            with self.subTest(query=query):
                self.assertEqual(self.client.get(f"{self.base}/messages/?{query}").status_code, 400)

    def test_a_page_only_contains_this_conversations_messages(self):
        other_listing = Listing.objects.create(
            seller=self.seller, product_name="Other", set_name="SV", set_code="P1", card_number="002",
            condition="NM", card_language="en", rarity="rare", asking_price="500.00", currency="THB", status="active",
        )
        other = Conversation.objects.create(listing=other_listing, buyer=self.buyer, seller=self.seller)
        Message.objects.create(conversation=other, author=self.seller, body="elsewhere")
        self.assertNotIn("elsewhere", self.bodies(self.client.get(f"{self.base}/messages/?limit=100")))

    def test_a_page_costs_the_same_queries_however_long_the_thread_is(self):
        def cost():
            with CaptureQueriesContext(connection) as queries:
                self.client.get(f"{self.base}/messages/?limit=3")
            return len(queries)

        before = cost()
        for number in range(30):
            Message.objects.create(conversation=self.conversation, author=self.seller, body=f"more {number}")
        self.assertEqual(cost(), before)
