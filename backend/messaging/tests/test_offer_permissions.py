from decimal import Decimal

from django.contrib.auth import get_user_model

from common.testing import ApiTestCase
from marketplace.models import Listing
from messaging.models import Conversation, Deal


User = get_user_model()


class OfferPermissionTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.seller = User.objects.create_user(username="seller-o", email="seller-o@example.com", password="pw", display_name="S")
        self.buyer = User.objects.create_user(username="buyer-o", email="buyer-o@example.com", password="pw", display_name="B")
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Charizard", condition="NM", card_language="en", rarity="rare",
            asking_price=Decimal("40.00"), currency="USD", quantity=1, status="active",
        )
        self.conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)

    def offer_by(self, user, amount="40.00"):
        self.client.force_authenticate(user)
        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/offers/", {"amount": amount, "currency": "USD"}, format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        return response.data["id"]

    def test_seller_cannot_accept_their_own_offer(self):
        offer_id = self.offer_by(self.seller, "99999.00")
        self.assertEqual(self.client.post(f"/api/offers/{offer_id}/accept/").status_code, 403)
        self.assertFalse(Deal.objects.exists())

    def test_buyer_cannot_accept_their_own_offer(self):
        offer_id = self.offer_by(self.buyer)
        self.assertEqual(self.client.post(f"/api/offers/{offer_id}/accept/").status_code, 403)

    def test_buyer_can_accept_the_sellers_offer(self):
        offer_id = self.offer_by(self.seller)
        self.client.force_authenticate(self.buyer)
        self.assertEqual(self.client.post(f"/api/offers/{offer_id}/accept/").status_code, 200)
        self.assertTrue(Deal.objects.filter(accepted_offer_id=offer_id).exists())

    def test_proposer_cannot_decline_or_counter_their_own_offer(self):
        offer_id = self.offer_by(self.buyer)
        self.assertEqual(self.client.post(f"/api/offers/{offer_id}/decline/").status_code, 403)
        self.assertEqual(
            self.client.post(f"/api/offers/{offer_id}/counter/", {"amount": "30.00"}, format="json").status_code, 403,
        )
