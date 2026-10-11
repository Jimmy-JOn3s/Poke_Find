from decimal import Decimal

from django.contrib.auth import get_user_model

from common.testing import ApiTestCase
from marketplace.models import Listing
from messaging.models import Conversation, Deal, Offer
from messaging.services import confirm_deal


User = get_user_model()


class DealIntegrityTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.seller = User.objects.create_user(username="seller-i", email="seller-i@example.com", password="pw", display_name="S")
        self.buyer = User.objects.create_user(username="buyer-i", email="buyer-i@example.com", password="pw", display_name="B1")
        self.buyer_two = User.objects.create_user(username="buyer-j", email="buyer-j@example.com", password="pw", display_name="B2")
        self.stranger = User.objects.create_user(username="stranger-i", email="stranger-i@example.com", password="pw", display_name="X")
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Mew ex", condition="NM", card_language="ja", rarity="rare",
            asking_price=Decimal("500.00"), currency="THB", quantity=1, status="active",
        )
        self.conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)
        self.conversation_two = Conversation.objects.create(listing=self.listing, buyer=self.buyer_two, seller=self.seller)

    def as_user(self, user):
        self.client.force_authenticate(user)
        return self.client

    def offer(self, user, conversation, amount="500.00"):
        return self.as_user(user).post(
            f"/api/conversations/{conversation.id}/offers/", {"amount": amount, "currency": "THB"}, format="json",
        )

    def accept(self, offer_id):
        return self.as_user(self.seller).post(f"/api/offers/{offer_id}/accept/")

    def live_deal(self, conversation):
        return Deal.objects.exclude(status=Deal.Status.CANCELLED).get(conversation=conversation)

    def listing_status(self):
        self.listing.refresh_from_db()
        return self.listing.status

    def test_accepting_reserves_the_listing_and_declines_competing_offers(self):
        first = self.offer(self.buyer, self.conversation).data["id"]
        second = self.offer(self.buyer_two, self.conversation_two).data["id"]
        self.assertEqual(self.accept(first).status_code, 200)
        self.assertEqual(self.listing_status(), Listing.Status.RESERVED)
        self.assertEqual(Offer.objects.get(pk=second).status, Offer.Status.DECLINED)
        self.assertEqual(self.accept(second).status_code, 400)
        self.assertEqual(Deal.objects.count(), 1)

    def test_a_listing_cannot_be_sold_twice(self):
        self.accept(self.offer(self.buyer, self.conversation).data["id"])
        self.assertEqual(self.offer(self.buyer_two, self.conversation_two).status_code, 400)
        deal = self.live_deal(self.conversation)
        self.as_user(self.buyer).post(f"/api/deals/{deal.id}/confirm-completion/")
        self.as_user(self.seller).post(f"/api/deals/{deal.id}/confirm-completion/")
        self.assertEqual(self.listing_status(), Listing.Status.SOLD)
        self.assertEqual(Deal.objects.filter(status=Deal.Status.COMPLETED).count(), 1)

    def test_offers_after_a_deal_are_rejected(self):
        self.accept(self.offer(self.buyer, self.conversation).data["id"])
        self.assertEqual(self.offer(self.buyer, self.conversation, "10.00").status_code, 400)

    def test_cancel_reopens_the_listing_and_allows_a_new_deal(self):
        self.accept(self.offer(self.buyer, self.conversation).data["id"])
        deal = self.live_deal(self.conversation)
        cancelled = self.as_user(self.buyer).post(f"/api/deals/{deal.id}/cancel/")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.data["status"], "cancelled")
        self.assertEqual(self.listing_status(), Listing.Status.ACTIVE)
        again = self.offer(self.buyer, self.conversation, "450.00").data["id"]
        self.assertEqual(self.accept(again).status_code, 200)
        self.assertEqual(self.live_deal(self.conversation).accepted_offer_id, again)

    def test_cannot_cancel_once_someone_confirmed(self):
        self.accept(self.offer(self.buyer, self.conversation).data["id"])
        deal = self.live_deal(self.conversation)
        self.as_user(self.buyer).post(f"/api/deals/{deal.id}/confirm-completion/")
        self.assertEqual(self.as_user(self.seller).post(f"/api/deals/{deal.id}/cancel/").status_code, 400)
        self.assertEqual(self.listing_status(), Listing.Status.RESERVED)

    def test_stranger_cannot_cancel(self):
        self.accept(self.offer(self.buyer, self.conversation).data["id"])
        deal = self.live_deal(self.conversation)
        self.assertEqual(self.as_user(self.stranger).post(f"/api/deals/{deal.id}/cancel/").status_code, 404)

    def test_confirming_a_completed_deal_changes_nothing(self):
        self.accept(self.offer(self.buyer, self.conversation).data["id"])
        deal = self.live_deal(self.conversation)
        self.as_user(self.buyer).post(f"/api/deals/{deal.id}/confirm-completion/")
        self.as_user(self.seller).post(f"/api/deals/{deal.id}/confirm-completion/")
        completed_at = Deal.objects.get(pk=deal.pk).completed_at
        again = self.as_user(self.buyer).post(f"/api/deals/{deal.id}/confirm-completion/")
        self.assertEqual(again.status_code, 200)
        self.assertEqual(Deal.objects.get(pk=deal.pk).completed_at, completed_at)

    def test_confirmations_work_from_a_stale_copy_of_the_deal(self):
        self.accept(self.offer(self.buyer, self.conversation).data["id"])
        stale = self.live_deal(self.conversation)
        confirm_deal(stale, self.buyer)
        result = confirm_deal(stale, self.seller)  # `stale` still says buyer_confirmed=False
        self.assertEqual(result.status, Deal.Status.COMPLETED)
        self.assertTrue(result.buyer_confirmed and result.seller_confirmed)
