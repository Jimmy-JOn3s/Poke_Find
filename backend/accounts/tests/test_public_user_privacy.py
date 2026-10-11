from decimal import Decimal

from django.contrib.auth import get_user_model

from common.testing import ApiTestCase
from marketplace.models import Listing
from messaging.models import Conversation, Deal, Message, Offer, Review


User = get_user_model()
PRIVATE_FIELDS = {"email", "username", "preferred_language", "preferred_currency"}


class PublicUserPrivacyTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.seller = User.objects.create_user(
            username="seller-p", email="seller@private.example", password="pw", display_name="Seller",
        )
        self.buyer = User.objects.create_user(
            username="buyer-p", email="buyer@private.example", password="pw", display_name="Buyer",
        )
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Mew ex", condition="NM", card_language="ja", rarity="rare",
            asking_price=Decimal("100.00"), currency="THB", quantity=1, status="active",
        )
        self.conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)

    def assertPublic(self, user_json):
        self.assertEqual(PRIVATE_FIELDS & set(user_json), set(), user_json)

    def test_anonymous_listing_feed_hides_private_fields(self):
        response = self.client.get("/api/listings/")
        self.assertPublic(response.data["results"][0]["seller"])

    def test_chat_participants_authors_and_proposers_hide_private_fields(self):
        Message.objects.create(conversation=self.conversation, author=self.seller, body="Still available")
        Offer.objects.create(conversation=self.conversation, proposer=self.buyer, amount=Decimal("90.00"), currency="THB")
        self.client.force_authenticate(self.buyer)
        base = f"/api/conversations/{self.conversation.id}/"
        conversation = self.client.get(base).data
        self.assertPublic(conversation["buyer"])
        self.assertPublic(conversation["seller"])
        self.assertPublic(conversation["latest_message"]["author"])
        self.assertPublic(self.client.get(base + "messages/").data[0]["author"])
        self.assertPublic(self.client.get(base + "offers/").data[0]["proposer"])

    def test_public_reviews_hide_private_fields(self):
        offer = Offer.objects.create(
            conversation=self.conversation, proposer=self.buyer, amount=Decimal("90.00"), currency="THB", status="accepted",
        )
        deal = Deal.objects.create(
            conversation=self.conversation, accepted_offer=offer, final_price=offer.amount, currency="THB",
            status="completed", buyer_confirmed=True, seller_confirmed=True,
        )
        Review.objects.create(deal=deal, reviewer=self.buyer, reviewee=self.seller, rating=5)
        review = self.client.get(f"/api/auth/users/{self.seller.id}/reviews/").data["results"][0]
        self.assertPublic(review["reviewer"])
        self.assertPublic(review["reviewee"])

    def test_me_still_returns_your_own_email(self):
        self.client.force_authenticate(self.seller)
        self.assertEqual(self.client.get("/api/auth/me/").data["email"], "seller@private.example")
