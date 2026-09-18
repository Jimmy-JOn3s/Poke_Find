from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from marketplace.models import Listing
from messaging.models import Conversation, Deal, Message, Offer


User = get_user_model()


class DealFlowApiTests(APITestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username="seller2", email="seller2@example.com", password="password123", display_name="Seller")
        self.buyer = User.objects.create_user(username="buyer", email="buyer@example.com", password="password123", display_name="Buyer")
        self.stranger = User.objects.create_user(username="stranger", email="stranger@example.com", password="password123", display_name="Stranger")
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Pikachu AR", set_name="151", set_code="SV2A",
            card_number="173/165", condition="NM", card_language="ja", rarity="rare",
            asking_price=Decimal("42.00"), currency="USD", quantity=1, status="active",
        )
        self.conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)

    def test_only_participants_can_read_or_message(self):
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.get(f"/api/conversations/{self.conversation.id}/").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.post(f"/api/conversations/{self.conversation.id}/messages/", {"body": "hi"}).status_code, status.HTTP_404_NOT_FOUND)

    def test_offer_currency_must_match_listing_and_seller_accept_creates_deal(self):
        self.client.force_authenticate(self.buyer)
        mismatch = self.client.post(f"/api/conversations/{self.conversation.id}/offers/", {"amount": "39.00", "currency": "THB"}, format="json")
        self.assertEqual(mismatch.status_code, status.HTTP_400_BAD_REQUEST)
        created = self.client.post(f"/api/conversations/{self.conversation.id}/offers/", {"amount": "39.00", "currency": "USD"}, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.seller)
        accepted = self.client.post(f"/api/offers/{created.data['id']}/accept/")
        self.assertEqual(accepted.status_code, status.HTTP_200_OK)
        self.assertEqual(accepted.data["status"], Offer.Status.ACCEPTED)
        self.assertTrue(Deal.objects.filter(accepted_offer_id=created.data["id"]).exists())

    def test_both_parties_complete_deal_and_persist_final_price(self):
        offer = Offer.objects.create(
            conversation=self.conversation, proposer=self.buyer, amount=Decimal("40.00"), currency="USD", status="accepted"
        )
        deal = Deal.objects.create(
            conversation=self.conversation, accepted_offer=offer, final_price=offer.amount, currency=offer.currency
        )
        self.client.force_authenticate(self.buyer)
        first = self.client.post(f"/api/deals/{deal.id}/confirm-completion/")
        self.assertEqual(first.data["status"], "accepted")

        self.client.force_authenticate(self.seller)
        second = self.client.post(f"/api/deals/{deal.id}/confirm-completion/")
        self.assertEqual(second.data["status"], "completed")
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.SOLD)

    def test_unread_counts_are_per_participant_and_only_mark_loaded_messages(self):
        first = Message.objects.create(conversation=self.conversation, author=self.seller, body="Hello")
        second = Message.objects.create(conversation=self.conversation, author=self.seller, body="Still available")
        Message.objects.create(conversation=self.conversation, author=self.buyer, body="Thanks")
        url = f"/api/conversations/{self.conversation.id}/"
        self.client.force_authenticate(self.buyer)
        self.assertEqual(self.client.get(url).data["unread_count"], 2)
        read = self.client.post(url + "read/", {"message_id": first.id})
        self.assertEqual(read.status_code, status.HTTP_200_OK)
        self.assertEqual(read.data["unread_count"], 1)
        self.client.post(url + "read/", {"message_id": second.id})
        self.client.post(url + "read/", {"message_id": first.id})
        self.assertEqual(self.client.get(url).data["unread_count"], 0)
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.client.get(url).data["unread_count"], 1)

    def test_read_requires_participant_and_message_from_same_conversation(self):
        message = Message.objects.create(conversation=self.conversation, author=self.seller, body="Hello")
        url = f"/api/conversations/{self.conversation.id}/read/"
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.post(url, {"message_id": message.id}).status_code, status.HTTP_404_NOT_FOUND)
        other = Conversation.objects.create(listing=self.listing, buyer=self.stranger, seller=self.seller)
        foreign_message = Message.objects.create(conversation=other, author=self.seller, body="Private")
        self.client.force_authenticate(self.buyer)
        self.assertEqual(self.client.post(url, {"message_id": foreign_message.id}).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.post(url, {}).status_code, status.HTTP_400_BAD_REQUEST)
