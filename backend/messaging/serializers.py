from rest_framework import serializers

from accounts.serializers import UserSerializer
from marketplace.models import Listing
from .models import Conversation, Deal, Message, Offer


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


class DealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deal
        fields = (
            "id", "conversation", "accepted_offer", "final_price", "currency", "status",
            "buyer_confirmed", "seller_confirmed", "completed_at", "created_at",
        )
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    listing_id = serializers.PrimaryKeyRelatedField(source="listing", queryset=Listing.objects.filter(status=Listing.Status.ACTIVE), write_only=True)
    listing = serializers.SerializerMethodField()
    latest_message = serializers.SerializerMethodField()
    deal = DealSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ("id", "listing_id", "listing", "buyer", "seller", "latest_message", "deal", "created_at", "updated_at")
        read_only_fields = ("id", "buyer", "seller", "created_at", "updated_at")

    def get_listing(self, obj):
        return {"id": obj.listing_id, "product_name": obj.listing.product_name, "asking_price": str(obj.listing.asking_price), "currency": obj.listing.currency}

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

