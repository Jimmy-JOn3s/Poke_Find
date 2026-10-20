from rest_framework import status

from common.testing import ApiTestCase
from marketplace.models import Listing
from messaging.models import Conversation, Message
from moderation.models import ContentReport


PASSWORD = "a-long-pass-81"


class ReportApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.seller = User.objects.create_user(
            username="seller-r", email="seller-r@example.com", password=PASSWORD, display_name="Seller",
            role="business",
        )
        self.buyer = User.objects.create_user(
            username="buyer-r", email="buyer-r@example.com", password=PASSWORD, display_name="Buyer",
        )
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Pikachu ex", set_name="SV", set_code="SV1",
            card_number="025", condition="NM", card_language="en", rarity="rare",
            asking_price="1000.00", currency="THB", status="active",
        )
        self.conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)
        self.message = Message.objects.create(conversation=self.conversation, author=self.seller, body="Hello buyer")

    def auth(self, user):
        response = self.client.post("/api/auth/login/", {"username": user.email, "password": PASSWORD}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_create_listing_report(self):
        self.auth(self.buyer)
        response = self.client.post("/api/reports/", {
            "category": "listing",
            "reason": "scam",
            "details": "Looks fake",
            "listing_id": self.listing.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(ContentReport.objects.count(), 1)

    def test_cannot_report_own_listing(self):
        self.auth(self.seller)
        response = self.client.post("/api/reports/", {
            "category": "listing",
            "reason": "spam",
            "listing_id": self.listing.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_overview_requires_staff(self):
        self.auth(self.buyer)
        self.assertEqual(self.client.get("/api/admin/overview/").status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_view_overview_and_update_report(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        admin = User.objects.create_user(
            username="admin-r", email="admin-r@example.com", password=PASSWORD, display_name="Admin", is_staff=True,
        )
        ContentReport.objects.create(
            reporter=self.buyer, category="listing", reason="scam", listing=self.listing,
        )
        self.auth(admin)
        overview = self.client.get("/api/admin/overview/")
        self.assertEqual(overview.status_code, status.HTTP_200_OK)
        self.assertEqual(overview.data["reports"]["pending"], 1)
        self.assertGreaterEqual(overview.data["users"]["total"], 3)

        users = self.client.get("/api/admin/users/")
        self.assertEqual(users.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(users.data["count"], 3)

        report_id = ContentReport.objects.first().id
        updated = self.client.patch(f"/api/admin/reports/{report_id}/", {
            "status": "resolved",
            "admin_notes": "Removed listing",
        }, format="json")
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["status"], "resolved")
        self.assertEqual(updated.data["resolved_by_name"], "Admin")
