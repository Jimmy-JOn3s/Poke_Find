from decimal import Decimal

from django.db.models import Case, Count, F, OuterRef, Q, Subquery, When
from rest_framework import serializers

from accounts.serializers import PublicUserSerializer
from marketplace.models import Listing
from .models import Conversation, Deal, Message, Offer, Review


class MessageSerializer(serializers.ModelSerializer):
    author = PublicUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "author", "body", "created_at")
        read_only_fields = ("id", "author", "created_at")


class OfferSerializer(serializers.ModelSerializer):
    proposer = PublicUserSerializer(read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

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
    reviewer = PublicUserSerializer(read_only=True)
    reviewee = PublicUserSerializer(read_only=True)
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


class CounterOfferSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))


class SellerReserveSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"), required=False)


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
        # all() reads the prefetched reviews when the view loaded them (a deal has at most two),
        # where filter() would query once per deal in a list.
        return any(review.reviewer_id == user.id for review in obj.reviews.all())

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


class ConversationListSerializer(serializers.ListSerializer):
    """Loads the latest message and unread count for the whole page in two queries, not two per row."""

    def to_representation(self, data):
        conversations = list(data)
        self.child.preload(conversations)
        return super().to_representation(conversations)


class ConversationSerializer(serializers.ModelSerializer):
    buyer = PublicUserSerializer(read_only=True)
    seller = PublicUserSerializer(read_only=True)
    listing_id = serializers.PrimaryKeyRelatedField(source="listing", queryset=Listing.objects.filter(status=Listing.Status.ACTIVE), write_only=True)
    listing = serializers.SerializerMethodField()
    latest_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    deal = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "listing_id", "listing", "buyer", "seller", "latest_message", "unread_count", "deal", "created_at", "updated_at")
        read_only_fields = ("id", "buyer", "seller", "created_at", "updated_at")
        list_serializer_class = ConversationListSerializer

    def preload(self, conversations):
        """Called for a list. Single conversations skip this and fall back to per-object queries."""
        user = self.context["request"].user
        ids = [conversation.pk for conversation in conversations]
        newest = Message.objects.filter(conversation=OuterRef("pk")).order_by("-created_at", "-pk").values("pk")[:1]
        newest_ids = Conversation.objects.filter(pk__in=ids).annotate(newest_id=Subquery(newest)).values("newest_id")
        self._latest_messages = {
            message.conversation_id: message
            for message in Message.objects.filter(pk__in=newest_ids).select_related("author")
        }
        read_at = Case(
            When(conversation__buyer=user, then=F("conversation__buyer_read_at")),
            default=F("conversation__seller_read_at"),
        )
        unread = (
            Message.objects.filter(conversation__in=ids).exclude(author=user).annotate(read_at=read_at)
            .filter(Q(read_at__isnull=True) | Q(created_at__gt=F("read_at")))
            .values("conversation_id").annotate(total=Count("pk"))
        )
        self._unread_counts = {row["conversation_id"]: row["total"] for row in unread}

    def get_deal(self, obj):
        deal = obj.live_deal()
        return DealSerializer(deal, context=self.context).data if deal else None

    def get_listing(self, obj):
        return {
            "id": obj.listing_id,
            "product_name": obj.listing.product_name,
            "asking_price": str(obj.listing.asking_price),
            "currency": obj.listing.currency,
            "status": obj.listing.status,
        }

    def get_unread_count(self, obj):
        if hasattr(self, "_unread_counts"):
            return self._unread_counts.get(obj.pk, 0)
        user = self.context["request"].user
        read_at = obj.buyer_read_at if user.id == obj.buyer_id else obj.seller_read_at
        messages = obj.messages.exclude(author=user)
        if read_at:
            messages = messages.filter(created_at__gt=read_at)
        return messages.count()

    def get_latest_message(self, obj):
        if hasattr(self, "_latest_messages"):
            message = self._latest_messages.get(obj.pk)
        else:
            message = obj.messages.order_by("-created_at", "-pk").first()
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
