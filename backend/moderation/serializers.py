from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from marketplace.models import Listing
from messaging.models import Message

from .models import ContentReport


User = get_user_model()


class ReportCreateSerializer(serializers.ModelSerializer):
    listing_id = serializers.IntegerField(required=False, allow_null=True)
    reported_user_id = serializers.IntegerField(required=False, allow_null=True)
    message_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = ContentReport
        fields = ("category", "reason", "details", "listing_id", "reported_user_id", "message_id")

    def validate(self, attrs):
        category = attrs["category"]
        listing_id = attrs.pop("listing_id", None)
        reported_user_id = attrs.pop("reported_user_id", None)
        message_id = attrs.pop("message_id", None)

        targets = [listing_id, reported_user_id, message_id]
        if sum(value is not None for value in targets) != 1:
            raise serializers.ValidationError("Provide exactly one of listing_id, reported_user_id, or message_id.")

        request = self.context["request"]
        reporter = request.user

        if category == ContentReport.Category.LISTING:
            if listing_id is None:
                raise serializers.ValidationError({"listing_id": "Required for listing reports."})
            listing = Listing.objects.filter(pk=listing_id).first()
            if listing is None:
                raise serializers.ValidationError({"listing_id": "Listing not found."})
            if listing.seller_id == reporter.id:
                raise serializers.ValidationError({"listing_id": "You cannot report your own listing."})
            attrs["listing"] = listing
        elif category == ContentReport.Category.USER:
            if reported_user_id is None:
                raise serializers.ValidationError({"reported_user_id": "Required for user reports."})
            reported_user = User.objects.filter(pk=reported_user_id).first()
            if reported_user is None:
                raise serializers.ValidationError({"reported_user_id": "User not found."})
            if reported_user.id == reporter.id:
                raise serializers.ValidationError({"reported_user_id": "You cannot report yourself."})
            attrs["reported_user"] = reported_user
        elif category == ContentReport.Category.MESSAGE:
            if message_id is None:
                raise serializers.ValidationError({"message_id": "Required for message reports."})
            message = Message.objects.select_related("conversation").filter(pk=message_id).first()
            if message is None:
                raise serializers.ValidationError({"message_id": "Message not found."})
            if not message.conversation.has_participant(reporter):
                raise serializers.ValidationError({"message_id": "You can only report messages in your conversations."})
            attrs["message"] = message
        else:
            raise serializers.ValidationError({"category": "Invalid category."})

        return attrs

    def create(self, validated_data):
        return ContentReport.objects.create(reporter=self.context["request"].user, **validated_data)


class ReportReporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "display_name", "email", "role")


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "display_name", "email", "role", "is_staff", "is_verified_seller", "date_joined")
        read_only_fields = fields


class ContentReportSerializer(serializers.ModelSerializer):
    reporter = ReportReporterSerializer(read_only=True)
    target = serializers.SerializerMethodField()
    resolved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ContentReport
        fields = (
            "id", "category", "reason", "details", "status", "admin_notes",
            "reporter", "target", "resolved_by_name", "resolved_at", "created_at", "updated_at",
        )
        read_only_fields = fields

    def get_target(self, obj):
        if obj.listing_id:
            return {"kind": "listing", "id": obj.listing_id, "label": obj.listing.product_name}
        if obj.reported_user_id:
            return {"kind": "user", "id": obj.reported_user_id, "label": obj.reported_user.display_name}
        if obj.message_id:
            preview = (obj.message.body[:80] + "…") if len(obj.message.body) > 80 else obj.message.body
            return {"kind": "message", "id": obj.message_id, "label": preview}
        return None

    def get_resolved_by_name(self, obj):
        return obj.resolved_by.display_name if obj.resolved_by_id else None


class AdminReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentReport
        fields = ("status", "admin_notes")

    def validate_status(self, value):
        allowed = {choice for choice, _ in ContentReport.Status.choices}
        if value not in allowed:
            raise serializers.ValidationError("Invalid status.")
        return value

    def update(self, instance, validated_data):
        new_status = validated_data.get("status", instance.status)
        if new_status in {ContentReport.Status.RESOLVED, ContentReport.Status.DISMISSED}:
            if instance.status not in {ContentReport.Status.RESOLVED, ContentReport.Status.DISMISSED}:
                instance.resolved_by = self.context["request"].user
                instance.resolved_at = timezone.now()
        elif instance.status in {ContentReport.Status.RESOLVED, ContentReport.Status.DISMISSED}:
            instance.resolved_by = None
            instance.resolved_at = None
        return super().update(instance, validated_data)
