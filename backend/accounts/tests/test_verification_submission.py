from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from accounts.verification_models import VerificationSubmission
from common.testing import ApiTestCase

User = get_user_model()


def tiny_png(name="id.png"):
    buffer = BytesIO()
    Image.new("RGB", (8, 8), color="white").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


@override_settings(MEDIA_ROOT="/tmp/pokefind-test-media", PRIVATE_MEDIA_ROOT="/tmp/pokefind-test-private")
class VerificationSubmissionTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="seller", email="seller@test.local", password="strong-pass-123",
            display_name="Seller", is_email_verified=True,
        )
        self.staff = User.objects.create_user(
            username="admin", email="admin@test.local", password="strong-pass-123",
            display_name="Admin", is_staff=True, is_email_verified=True,
        )
        self.client.force_authenticate(self.user)

    def test_user_can_submit_pending_verification(self):
        response = self.client.post(
            "/api/auth/verification-submission/",
            {"document_type": "id", "id_document": tiny_png()},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(VerificationSubmission.objects.filter(user=self.user, status="pending").count(), 1)

    def test_cannot_submit_while_pending(self):
        self.client.post(
            "/api/auth/verification-submission/",
            {"document_type": "passport", "id_document": tiny_png("a.png")},
            format="multipart",
        )
        again = self.client.post(
            "/api/auth/verification-submission/",
            {"document_type": "passport", "id_document": tiny_png("b.png")},
            format="multipart",
        )
        self.assertEqual(again.status_code, 400)

    def test_staff_approve_sets_seller_badge(self):
        created = self.client.post(
            "/api/auth/verification-submission/",
            {"document_type": "passport", "id_document": tiny_png()},
            format="multipart",
        )
        submission_id = created.data["id"]
        self.client.force_authenticate(self.staff)
        reviewed = self.client.post(
            f"/api/admin/verifications/{submission_id}/review/",
            {"action": "approve", "admin_notes": "Looks good"},
            format="json",
        )
        self.assertEqual(reviewed.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified_seller)
        self.assertEqual(self.user.seller_verification_type, User.SellerVerificationType.PASSPORT)

    def test_staff_can_download_id_document(self):
        created = self.client.post(
            "/api/auth/verification-submission/",
            {"document_type": "id", "id_document": tiny_png()},
            format="multipart",
        )
        submission_id = created.data["id"]
        self.client.force_authenticate(self.staff)
        file_response = self.client.get(f"/api/admin/verifications/{submission_id}/file/id_document/")
        self.assertEqual(file_response.status_code, 200)
        self.assertTrue(file_response["Content-Type"].startswith("image/"))

    def test_non_staff_cannot_list_admin_verifications(self):
        self.client.force_authenticate(self.user)
        denied = self.client.get("/api/admin/verifications/")
        self.assertEqual(denied.status_code, 403)
