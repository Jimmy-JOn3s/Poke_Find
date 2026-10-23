from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_image_file_extension
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Q
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import get_md5_hash_password

from common.validators import validate_upload_size
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
            "bio", "is_email_verified", "is_verified_seller", "seller_verification_type", "is_staff", "date_joined",
        )
        read_only_fields = (
            "id", "username", "email", "is_email_verified", "is_verified_seller",
            "seller_verification_type", "is_staff", "date_joined",
        )
        extra_kwargs = {"avatar": {"validators": [validate_image_file_extension, validate_upload_size]}}


class PublicUserSerializer(serializers.ModelSerializer):
    """What other people may see about a user. Never add email, username or preferences here:
    usernames are generated from the email address, so they leak it too."""

    class Meta:
        model = User
        fields = (
            "id", "display_name", "role", "avatar", "location",
            "is_email_verified", "is_verified_seller", "seller_verification_type",
        )
        read_only_fields = fields


class PublicUserProfileSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    total_sold = serializers.SerializerMethodField()
    pending_review_deal_id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "display_name", "role", "avatar", "location", "bio",
            "is_email_verified", "is_verified_seller", "seller_verification_type",
            "date_joined", "rating", "review_count", "total_sold",
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
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = (
            "username", "email", "password", "display_name", "role",
            "preferred_language", "preferred_currency",
        )

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate(self, attrs):
        candidate = User(
            username=attrs.get("username", ""), email=attrs.get("email", ""),
            display_name=attrs.get("display_name", ""),
        )
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        # Two sign-ups can pass validation at the same moment; the database constraint decides.
        try:
            with transaction.atomic():
                return User.objects.create_user(**validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"detail": "An account with this username or email already exists."}
            ) from exc


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identifier = attrs.get(self.username_field, "")
        if "@" in identifier:
            match = User.objects.filter(email__iexact=identifier).only("username").first()
            if match:
                attrs[self.username_field] = match.username
        return super().validate(attrs)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)
    new_password = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)


class MagicLinkRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class MagicLinkConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)


class EmailVerificationConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)


class RevocationCheckingRefreshSerializer(TokenRefreshSerializer):
    """Refuses refresh tokens issued before the account's password last changed, or for deleted accounts.

    SimpleJWT checks the password fingerprint only when an access token is used, so without this a stale
    refresh token would keep minting access tokens that are rejected right away.
    """

    def validate(self, attrs):
        token = RefreshToken(attrs["refresh"])
        user = User.objects.filter(**{jwt_settings.USER_ID_FIELD: token.get(jwt_settings.USER_ID_CLAIM)}).first()
        if user is None or token.get(jwt_settings.REVOKE_TOKEN_CLAIM) != get_md5_hash_password(user.password):
            raise InvalidToken("This session has ended. Sign in again.")
        return super().validate(attrs)
