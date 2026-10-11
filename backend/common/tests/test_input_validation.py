import io
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from common.testing import ApiTestCase
from marketplace.models import Listing
from messaging.models import Conversation, Offer


User = get_user_model()


def png_upload(name="image.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, "PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class InputValidationTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.seller = User.objects.create_user(username="seller-v", email="seller-v@example.com", password="pw", display_name="S")
        self.buyer = User.objects.create_user(username="buyer-v", email="buyer-v@example.com", password="pw", display_name="B")
        self.listing = Listing.objects.create(
            seller=self.seller, product_name="Eevee", condition="NM", card_language="en", rarity="common",
            asking_price=Decimal("50.00"), currency="THB", quantity=1, status="active",
        )
        self.conversation = Conversation.objects.create(listing=self.listing, buyer=self.buyer, seller=self.seller)

    def test_bad_price_filters_return_400(self):
        for query in ("min_price=abc", "max_price=NaN", "min_price=-1", "max_price=Infinity"):
            self.assertEqual(self.client.get(f"/api/listings/?{query}").status_code, 400, query)
        self.assertEqual(self.client.get("/api/listings/?min_price=10&max_price=60").status_code, 200)

    def test_zero_offer_is_rejected(self):
        self.client.force_authenticate(self.buyer)
        response = self.client.post(
            f"/api/conversations/{self.conversation.id}/offers/", {"amount": "0", "currency": "THB"}, format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_bad_counter_amounts_return_400(self):
        offer = Offer.objects.create(conversation=self.conversation, proposer=self.buyer, amount=Decimal("40.00"), currency="THB")
        self.client.force_authenticate(self.seller)
        for amount in ("NaN", "Infinity", "abc", "0", "1234567890123.00"):
            response = self.client.post(f"/api/offers/{offer.id}/counter/", {"amount": amount}, format="json")
            self.assertEqual(response.status_code, 400, amount)
        self.assertEqual(Offer.objects.get(pk=offer.pk).status, Offer.Status.PENDING)

    @override_settings(MAX_UPLOAD_BYTES=10)
    def test_uploads_over_the_limit_are_rejected(self):
        self.client.force_authenticate(self.seller)
        avatar = self.client.patch("/api/auth/me/", {"avatar": png_upload()}, format="multipart")
        self.assertEqual(avatar.status_code, 400)
        self.assertIn("too large", str(avatar.data["avatar"]))
        photo = self.client.patch(f"/api/listings/{self.listing.id}/", {"photo": png_upload()}, format="multipart")
        self.assertEqual(photo.status_code, 400)
        self.assertIn("too large", str(photo.data["photo"]))

    def test_uploads_under_the_limit_are_accepted(self):
        self.client.force_authenticate(self.seller)
        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.patch("/api/auth/me/", {"avatar": png_upload()}, format="multipart")
        self.assertEqual(response.status_code, 200, response.data)
