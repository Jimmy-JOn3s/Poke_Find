from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from marketplace.models import Listing


class Conversation(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="conversations")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buying_conversations")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="selling_conversations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("listing", "buyer", "seller"), name="unique_listing_conversation")]
        ordering = ("-updated_at",)

    def has_participant(self, user):
        return user.is_authenticated and user.id in {self.buyer_id, self.seller_id}


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messages")
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)


class Offer(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        COUNTERED = "countered", "Countered"

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="offers")
    proposer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="offers")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=Listing.Currency.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    counter_to = models.OneToOneField("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="counter_offer")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)


class Deal(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = "accepted", "Accepted"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE, related_name="deal")
    accepted_offer = models.OneToOneField(Offer, on_delete=models.PROTECT, related_name="deal")
    final_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Listing.Currency.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACCEPTED)
    buyer_confirmed = models.BooleanField(default=False)
    seller_confirmed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

