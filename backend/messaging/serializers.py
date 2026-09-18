from rest_framework import serializers

from accounts.serializers import UserSerializer
from marketplace.models import Listing
from .models import Conversation, Deal, Message, Offer, Review


class MessageSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "author", "body", "created_at")
        read_only_fields = ("id", "author", "created_at")


class OfferSerializer(serializers.ModelSerializer):
    proposer = UserSerializer(read_only=True)

    class Meta:
        model = Offer
        fields = ("id", "conversation", "proposer", "amount", "currency", "status", "counter_to", "created_at")
        read_only_fields = ("id", "conversation", "proposer", "status", "counter_to", "created_at")

    def validate_currency(self, value):
        conversation = self.context["conversation"]
        if value != conversation.listing.currency:
            raise serializers.ValidationError("Offer currency must match the listing currency")
        return value


class ReviewSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)
    reviewee = UserSerializer(read_only=True)
    listing_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ("id", "deal", "reviewer", "reviewee", "rating", "comment", "listing_name", "created_at")
        read_only_fields = ("id", "reviewer", "reviewee", "listing_name", "created_at")

    def get_listing_name(self, obj):
        return obj.deal.conversation.listing.product_name


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class DealSerializer(serializers.ModelSerializer):
    reviewer_has_reviewed = serializers.SerializerMethodField()
    counterparty_id = serializers.SerializerMethodField()
    counterparty_name = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = (
            "id", "conversation", "accepted_offer", "final_price", "currency", "status",
            "buyer_confirmed", "seller_confirmed", "completed_at", "created_at",
            "reviewer_has_reviewed", "counterparty_id", "counterparty_name",
        )
        read_only_fields = fields

    def _request_user(self):
        request = self.context.get("request")
        return getattr(request, "user", None) if request else None

    def get_reviewer_has_reviewed(self, obj):
        user = self._request_user()
        if not user or not user.is_authenticated:
            return False
        return obj.reviews.filter(reviewer_id=user.id).exists()

    def get_counterparty_id(self, obj):
        user = self._request_user()
        if not user or not user.is_authenticated:
            return None
        conversation = obj.conversation
        if user.id == conversation.buyer_id:
            return conversation.seller_id
        if user.id == conversation.seller_id:
            return conversation.buyer_id
        return None

    def get_counterparty_name(self, obj):
        user = self._request_user()
        if not user or not user.is_authenticated:
            return None
        conversation = obj.conversation
        if user.id == conversation.buyer_id:
            return conversation.seller.display_name
        if user.id == conversation.seller_id:
            return conversation.buyer.display_name
        return None


class ConversationSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    listing_id = serializers.PrimaryKeyRelatedField(source="listing", queryset=Listing.objects.filter(status=Listing.Status.ACTIVE), write_only=True)
    listing = serializers.SerializerMethodField()
    latest_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    deal = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "listing_id", "listing", "buyer", "seller", "latest_message", "unread_count", "deal", "created_at", "updated_at")
        read_only_fields = ("id", "buyer", "seller", "created_at", "updated_at")

    def get_deal(self, obj):
        try:
            return DealSerializer(obj.deal, context=self.context).data
        except Deal.DoesNotExist:
            return None

    def get_listing(self, obj):
        return {"id": obj.listing_id, "product_name": obj.listing.product_name, "asking_price": str(obj.listing.asking_price), "currency": obj.listing.currency}

    def get_unread_count(self, obj):
        user = self.context["request"].user
        read_at = obj.buyer_read_at if user.id == obj.buyer_id else obj.seller_read_at
        messages = obj.messages.exclude(author=user)
        if read_at:
            messages = messages.filter(created_at__gt=read_at)
        return messages.count()

    def get_latest_message(self, obj):
        message = obj.messages.last()
        return MessageSerializer(message).data if message else None

    def create(self, validated_data):
        listing = validated_data["listing"]
        user = self.context["request"].user
        if listing.seller_id == user.id:
            raise serializers.ValidationError("A seller cannot start a buyer conversation on their own listing")
        conversation, _ = Conversation.objects.get_or_create(listing=listing, buyer=user, seller=listing.seller)
        return conversation



class ReadConversationSerializer(serializers.Serializer):
    message_id = serializers.IntegerField(min_value=1)
