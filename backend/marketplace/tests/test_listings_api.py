from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from marketplace.models import Listing


User = get_user_model()


class ListingApiTests(APITestCase):
    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller", email="seller@example.com", password="password123",
            display_name="Bangkok Cards",
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="password123",
            display_name="Other Seller",
        )
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Charizard ex", set_name="Obsidian Flames",
            set_code="SV03", card_number="125/108", condition="NM", card_language="en",
            rarity="ultra", asking_price=Decimal("5200.00"), currency="THB", quantity=1,
            description="Sleeved immediately", status="active",
        )

    def test_public_list_only_returns_active_and_supports_filters(self):
        Listing.objects.create(
            seller=self.seller, product_name="Pikachu", set_name="151", set_code="SV2A",
            card_number="025", condition="M", card_language="ja", rarity="rare",
            asking_price=Decimal("35.00"), currency="USD", quantity=1, status="draft",
        )
        response = self.client.get("/api/listings/?q=char&currency=THB&condition=NM")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["product_name"], "Charizard ex")

    def test_authenticated_seller_can_create_and_only_owner_can_edit(self):
        self.client.force_authenticate(self.seller)
        response = self.client.post("/api/listings/", {
            "product_name": "Mew ex", "set_name": "151", "set_code": "SV2A",
            "card_number": "205/165", "condition": "LP", "card_language": "th",
            "rarity": "secret", "asking_price": "2100.00", "currency": "THB",
            "quantity": 1, "description": "Thai print", "status": "active",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["seller"]["display_name"], "Bangkok Cards")

        self.client.force_authenticate(self.other)
        forbidden = self.client.patch(f"/api/listings/{self.listing.id}/", {"asking_price": "1.00"}, format="json")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

    def test_save_action_is_idempotent_and_can_unsave(self):
        self.client.force_authenticate(self.other)
        first = self.client.post(f"/api/listings/{self.listing.id}/save/")
        second = self.client.post(f"/api/listings/{self.listing.id}/save/")
        removed = self.client.delete(f"/api/listings/{self.listing.id}/save/")
        self.assertEqual(first.data, {"saved": True})
        self.assertEqual(second.data, {"saved": True})
        self.assertEqual(removed.data, {"saved": False})
