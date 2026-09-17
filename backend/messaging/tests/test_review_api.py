from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from marketplace.models import Listing
from messaging.models import Conversation, Deal, Offer, Review


User = get_user_model()


class ReviewApiTests(APITestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller3", email="seller3@example.com", password="password123", display_name="Seller",
        )
        self.buyer = User.objects.create_user(
            username="buyer3", email="buyer3@example.com", password="password123", display_name="Buyer",
        )
        self.stranger = User.objects.create_user(
            username="stranger3", email="stranger3@example.com", password="password123", display_name="Stranger",
        )
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Charizard", set_name="151", set_code="SV2A",
            card_number="006/165", condition="NM", card_language="ja", rarity="rare",
            asking_price=Decimal("100.00"), currency="THB", quantity=1, status="sold",
        )
        self.conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)
        offer = Offer.objects.create(
            conversation=self.conversation, proposer=self.buyer, amount=Decimal("95.00"),
            currency="THB", status="accepted",
        )
        self.deal = Deal.objects.create(
            conversation=self.conversation, accepted_offer=offer, final_price=offer.amount,
            currency=offer.currency, status="completed", buyer_confirmed=True, seller_confirmed=True,
        )

    def test_participant_can_review_after_completed_deal(self):
        self.client.force_authenticate(self.buyer)
        response = self.client.post(
            f"/api/deals/{self.deal.id}/review/",
            {"rating": 5, "comment": "Great seller!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["rating"], 5)
        self.assertEqual(response.data["reviewee"]["id"], self.seller.id)
        self.assertTrue(Review.objects.filter(deal=self.deal, reviewer=self.buyer).exists())

    def test_cannot_review_twice_or_before_completion(self):
        self.client.force_authenticate(self.buyer)
        self.client.post(f"/api/deals/{self.deal.id}/review/", {"rating": 4}, format="json")
        duplicate = self.client.post(f"/api/deals/{self.deal.id}/review/", {"rating": 3}, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

        other_listing = Listing.objects.create(
            seller=self.seller, product_name="Pikachu", set_name="151", set_code="SV2A",
            card_number="025/165", condition="NM", card_language="ja", rarity="common",
            asking_price=Decimal("10.00"), currency="THB", quantity=1, status="active",
        )
        other_conversation = Conversation.objects.create(
            listing=other_listing, buyer=self.buyer, seller=self.seller,
        )
        other_offer = Offer.objects.create(
            conversation=other_conversation, proposer=self.buyer, amount=Decimal("9.00"),
            currency="THB", status="accepted",
        )
        pending_deal = Deal.objects.create(
            conversation=other_conversation, accepted_offer=other_offer,
            final_price=other_offer.amount, currency="THB", status="accepted",
        )
        early = self.client.post(f"/api/deals/{pending_deal.id}/review/", {"rating": 5}, format="json")
        self.assertEqual(early.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stranger_cannot_review(self):
        self.client.force_authenticate(self.stranger)
        response = self.client.post(f"/api/deals/{self.deal.id}/review/", {"rating": 1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_profile_and_reviews_list(self):
        Review.objects.create(
            deal=self.deal, reviewer=self.buyer, reviewee=self.seller, rating=5, comment="Fast shipping",
        )
        profile = self.client.get(f"/api/auth/users/{self.seller.id}/")
        self.assertEqual(profile.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.data["rating"], 5.0)
        self.assertEqual(profile.data["review_count"], 1)

        reviews = self.client.get(f"/api/auth/users/{self.seller.id}/reviews/")
        self.assertEqual(reviews.status_code, status.HTTP_200_OK)
        self.assertEqual(len(reviews.data["results"]), 1)
        self.assertEqual(reviews.data["results"][0]["comment"], "Fast shipping")

    def test_pending_review_deal_id_for_authenticated_viewer(self):
        self.client.force_authenticate(self.buyer)
        profile = self.client.get(f"/api/auth/users/{self.seller.id}/")
        self.assertEqual(profile.data["pending_review_deal_id"], self.deal.id)

        self.client.post(f"/api/deals/{self.deal.id}/review/", {"rating": 5}, format="json")
        profile = self.client.get(f"/api/auth/users/{self.seller.id}/")
        self.assertIsNone(profile.data["pending_review_deal_id"])
