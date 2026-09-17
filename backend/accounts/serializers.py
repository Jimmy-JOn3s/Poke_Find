from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from messaging.models import Deal, Review


User = get_user_model()


def user_review_stats(user):
    stats = Review.objects.filter(reviewee=user).aggregate(avg_rating=Avg("rating"), review_count=Count("id"))
    total_sold = Deal.objects.filter(
        conversation__seller=user, status=Deal.Status.COMPLETED,
    ).count()
    avg = stats["avg_rating"]
    return {
        "rating": round(float(avg), 1) if avg is not None else 0,
        "review_count": stats["review_count"] or 0,
        "total_sold": total_sold,
    }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id", "username", "email", "display_name", "role",
            "preferred_language", "preferred_currency", "avatar", "location",
            "bio", "is_verified_seller", "date_joined",
        )
        read_only_fields = ("id", "username", "email", "is_verified_seller", "date_joined")


class PublicUserProfileSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    total_sold = serializers.SerializerMethodField()
    pending_review_deal_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "display_name", "role", "avatar", "location", "bio",
            "is_verified_seller", "date_joined", "rating", "review_count", "total_sold",
            "pending_review_deal_id",
        )
        read_only_fields = fields

    def _stats(self, obj):
        if not hasattr(obj, "_profile_stats"):
            obj._profile_stats = user_review_stats(obj)
        return obj._profile_stats

    def get_rating(self, obj):
        return self._stats(obj)["rating"]

    def get_review_count(self, obj):
        return self._stats(obj)["review_count"]

    def get_total_sold(self, obj):
        return self._stats(obj)["total_sold"]

    def get_pending_review_deal_id(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated or request.user.id == obj.id:
            return None
        deal = (
            Deal.objects.filter(status=Deal.Status.COMPLETED)
            .filter(
                Q(conversation__buyer=request.user, conversation__seller=obj)
                | Q(conversation__seller=request.user, conversation__buyer=obj)
            )
            .exclude(reviews__reviewer=request.user)
            .order_by("-completed_at")
            .first()
        )
        return deal.id if deal else None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "username", "email", "password", "display_name", "role",
            "preferred_language", "preferred_currency",
        )

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identifier = attrs.get(self.username_field, "")
        if "@" in identifier:
            match = User.objects.filter(email__iexact=identifier).only("username").first()
            if match:
                attrs[self.username_field] = match.username
        return super().validate(attrs)
