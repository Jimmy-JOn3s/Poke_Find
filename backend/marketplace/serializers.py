from django.db import transaction
from rest_framework import serializers

from accounts.serializers import PublicUserSerializer
from .models import Listing


# Owners choose these; "reserved" and "sold" are only set by the deal flow (messaging.services).
OWNER_SETTABLE_STATUSES = {Listing.Status.DRAFT, Listing.Status.ACTIVE, Listing.Status.HIDDEN}
DEAL_LOCKED_STATUSES = {Listing.Status.RESERVED, Listing.Status.SOLD}
DEAL_LOCKED_FIELDS = ("status", "asking_price", "currency", "quantity")


class ListingSerializer(serializers.ModelSerializer):
    seller = PublicUserSerializer(read_only=True)
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = (
            "id", "seller", "product_name", "set_name", "set_code", "card_number",
            "condition", "card_language", "rarity", "asking_price", "currency",
            "quantity", "description", "image_url", "photo", "status", "is_saved", "created_at", "updated_at",
        )
        read_only_fields = ("id", "seller", "is_saved", "created_at", "updated_at")

    def get_is_saved(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.saved_by.filter(user=request.user).exists())

    def validate_status(self, value):
        # No exception for "unchanged": comparing with a possibly stale instance could re-apply a
        # reservation that a concurrent cancel just released. Clients editing other fields omit status.
        if value not in OWNER_SETTABLE_STATUSES:
            raise serializers.ValidationError("Reserved and sold are set automatically by the deal flow.")
        return value

    def update(self, instance, validated_data):
        with transaction.atomic():
            # Re-read under a row lock so we never overwrite a status the deal flow just changed.
            listing = Listing.objects.select_for_update().get(pk=instance.pk)
            if listing.status in DEAL_LOCKED_STATUSES:
                changed = [
                    field for field in DEAL_LOCKED_FIELDS
                    if field in validated_data and validated_data[field] != getattr(listing, field)
                ]
                if changed:
                    raise serializers.ValidationError(
                        {field: "This can't change while the card is reserved or sold." for field in changed}
                    )
            for field, value in validated_data.items():
                setattr(listing, field, value)
            # Write only the edited columns so concurrent deal-flow updates to others survive.
            listing.save(update_fields=[*validated_data, "updated_at"])
        return listing
