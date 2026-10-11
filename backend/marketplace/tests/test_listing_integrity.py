from decimal import Decimal

from django.contrib.auth import get_user_model

from common.testing import ApiTestCase
from marketplace.models import Listing
from marketplace.serializers import ListingSerializer
from messaging.models import Conversation, Deal, Offer


User = get_user_model()


class ListingIntegrityTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.seller = User.objects.create_user(username="seller-l", email="seller-l@example.com", password="pw", display_name="S")
        self.buyer = User.objects.create_user(username="buyer-l", email="buyer-l@example.com", password="pw", display_name="B")
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Lugia", condition="NM", card_language="en", rarity="rare",
            asking_price=Decimal("500.00"), currency="THB", quantity=1, status="active",
        )
        self.url = f"/api/listings/{self.listing.id}/"
        self.client.force_authenticate(self.seller)

    def patch(self, data):
        return self.client.patch(self.url, data, format="json")

    def reserve(self):
        Listing.objects.filter(pk=self.listing.pk).update(status=Listing.Status.RESERVED)

    def test_owner_cannot_mark_a_listing_reserved_or_sold(self):
        for value in ("reserved", "sold"):
            self.assertEqual(self.patch({"status": value}).status_code, 400, value)

    def test_owner_can_hide_and_reactivate(self):
        self.assertEqual(self.patch({"status": "hidden"}).status_code, 200)
        self.assertEqual(self.patch({"status": "active"}).status_code, 200)

    def test_reserved_listing_keeps_status_and_price_but_description_can_change(self):
        self.reserve()
        self.assertEqual(self.patch({"status": "active"}).status_code, 400)
        self.assertEqual(self.patch({"asking_price": "1.00"}).status_code, 400)
        ok = self.patch({"description": "Sleeved since opening", "asking_price": "500.00"})
        self.assertEqual(ok.status_code, 200, ok.data)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.RESERVED)
        self.assertEqual(self.listing.description, "Sleeved since opening")

    def test_an_edit_does_not_overwrite_a_reservation_made_meanwhile(self):
        serializer = ListingSerializer(self.listing, data={"description": "New text"}, partial=True)
        serializer.is_valid(raise_exception=True)
        self.reserve()  # the deal flow reserves the card after the edit request loaded it
        serializer.save()
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, Listing.Status.RESERVED)

    def test_listing_with_a_deal_cannot_be_deleted(self):
        conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)
        offer = Offer.objects.create(
            conversation=conversation, proposer=self.buyer, amount=Decimal("500.00"), currency="THB", status="accepted",
        )
        Deal.objects.create(conversation=conversation, accepted_offer=offer, final_price=offer.amount, currency="THB")
        self.reserve()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Listing.objects.filter(pk=self.listing.pk).exists())

    def test_listing_without_deals_can_be_deleted(self):
        self.assertEqual(self.client.delete(self.url).status_code, 204)
