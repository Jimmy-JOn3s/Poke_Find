from django.conf import settings
from django.db import models
from django.db.models import Q

from marketplace.models import Listing
from messaging.models import Message


class ContentReport(models.Model):
    class Category(models.TextChoices):
        LISTING = "listing", "Listing"
        USER = "user", "User"
        MESSAGE = "message", "Message"

    class Reason(models.TextChoices):
        SPAM = "spam", "Spam"
        SCAM = "scam", "Scam or fraud"
        FAKE_LISTING = "fake_listing", "Fake or misleading listing"
        HARASSMENT = "harassment", "Harassment"
        INAPPROPRIATE = "inappropriate", "Inappropriate content"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        REVIEWING = "reviewing", "Reviewing"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_filed",
    )
    category = models.CharField(max_length=16, choices=Category.choices)
    reason = models.CharField(max_length=32, choices=Reason.choices)
    details = models.TextField(blank=True, max_length=2000)
    listing = models.ForeignKey(
        Listing, null=True, blank=True, on_delete=models.CASCADE, related_name="reports",
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="reports_received",
    )
    message = models.ForeignKey(
        Message, null=True, blank=True, on_delete=models.CASCADE, related_name="reports",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    admin_notes = models.TextField(blank=True, max_length=2000)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reports_resolved",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(listing__isnull=False, reported_user__isnull=True, message__isnull=True)
                    | Q(listing__isnull=True, reported_user__isnull=False, message__isnull=True)
                    | Q(listing__isnull=True, reported_user__isnull=True, message__isnull=False)
                ),
                name="report_exactly_one_target",
            ),
            models.UniqueConstraint(
                fields=("reporter", "listing"),
                condition=Q(listing__isnull=False) & Q(status__in=("pending", "reviewing")),
                name="unique_open_listing_report_per_reporter",
            ),
            models.UniqueConstraint(
                fields=("reporter", "reported_user"),
                condition=Q(reported_user__isnull=False) & Q(status__in=("pending", "reviewing")),
                name="unique_open_user_report_per_reporter",
            ),
            models.UniqueConstraint(
                fields=("reporter", "message"),
                condition=Q(message__isnull=False) & Q(status__in=("pending", "reviewing")),
                name="unique_open_message_report_per_reporter",
            ),
        ]

    def __str__(self):
        return f"Report #{self.pk} ({self.category}, {self.status})"
