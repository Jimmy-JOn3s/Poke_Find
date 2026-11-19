from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from marketplace.models import Listing
from messaging.models import Deal, Message

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


class AdminReportSellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "display_name", "email", "role")
        read_only_fields = fields


class AdminReportListingSerializer(serializers.ModelSerializer):
    seller = AdminReportSellerSerializer(read_only=True)

    class Meta:
        model = Listing
        fields = (
            "id", "seller", "product_name", "set_name", "set_code", "card_number",
            "condition", "card_language", "rarity", "asking_price", "currency",
            "quantity", "description", "image_url", "photo", "status", "created_at",
        )
        read_only_fields = fields


class AdminReportUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "display_name", "email", "role", "is_verified_seller", "date_joined")
        read_only_fields = fields


class AdminReportMessageSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.display_name", read_only=True)
    author_id = serializers.IntegerField(read_only=True)
    conversation_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "body", "author_id", "author_name", "conversation_id", "created_at")
        read_only_fields = fields


class AdminCompletedDealSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="conversation.buyer.display_name", read_only=True)
    seller_name = serializers.CharField(source="conversation.seller.display_name", read_only=True)
    listing_id = serializers.IntegerField(source="conversation.listing_id", read_only=True)
    listing_product_name = serializers.CharField(source="conversation.listing.product_name", read_only=True)
    listing_image_url = serializers.CharField(source="conversation.listing.image_url", read_only=True)
    listing_photo = serializers.ImageField(source="conversation.listing.photo", read_only=True)
    listing_card_number = serializers.CharField(source="conversation.listing.card_number", read_only=True)

    class Meta:
        model = Deal
        fields = (
            "id", "listing_id", "status", "final_price", "currency",
            "card_name", "card_set", "condition",
            "listing_product_name", "listing_image_url", "listing_photo", "listing_card_number",
            "buyer_name", "seller_name",
            "buyer_confirmed", "seller_confirmed", "completed_at", "created_at",
        )
        read_only_fields = fields


class AdminContentReportSerializer(ContentReportSerializer):
    target_detail = serializers.SerializerMethodField()

    class Meta(ContentReportSerializer.Meta):
        fields = ContentReportSerializer.Meta.fields + ("target_detail",)

    def get_target_detail(self, obj):
        listing = None
        message = None
        user = None

        if obj.listing_id:
            listing = obj.listing
        elif obj.reported_user_id:
            user = obj.reported_user
        elif obj.message_id:
            message = obj.message
            listing = message.conversation.listing

        return {
            "listing": AdminReportListingSerializer(listing).data if listing else None,
            "message": AdminReportMessageSerializer(message).data if message else None,
            "user": AdminReportUserSerializer(user).data if user else None,
        }


class AdminReportActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("hide_listing", "deactivate_user", "remove_message"))
    mark_resolved = serializers.BooleanField(required=False, default=True)
    admin_notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)


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
