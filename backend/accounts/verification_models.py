import uuid
from pathlib import Path

from django.conf import settings
from django.db import models

from .storage import private_media_storage


def _verification_upload_path(instance, filename: str) -> str:
    ext = Path(filename).suffix.lower() or ".bin"
    return f"verification/{instance.user_id}/{uuid.uuid4().hex}{ext}"


class VerificationSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class DocumentType(models.TextChoices):
        ID = "id", "National ID"
        PASSPORT = "passport", "Passport"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_submissions",
    )
    document_type = models.CharField(max_length=16, choices=DocumentType.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    id_document = models.ImageField(
        upload_to=_verification_upload_path,
        storage=private_media_storage,
    )
    selfie = models.ImageField(
        upload_to=_verification_upload_path,
        storage=private_media_storage,
        blank=True,
    )
    admin_notes = models.TextField(max_length=2000, blank=True)
    rejection_reason = models.TextField(max_length=1000, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verification_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user",),
                condition=models.Q(status="pending"),
                name="one_pending_verification_per_user",
            ),
        ]

    def __str__(self):
        return f"Verification #{self.pk} ({self.user_id}) — {self.status}"
