from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView

from common.exceptions import EmailDeliveryFailed
from common.transactional_email import EmailDeliveryError
from messaging.models import Review
from messaging.serializers import ReviewSerializer

from .serializers import (
    EmailOrUsernameTokenObtainPairSerializer, EmailVerificationConfirmSerializer,
    MagicLinkConfirmSerializer, MagicLinkRequestSerializer,
    PasswordResetConfirmSerializer, PasswordResetRequestSerializer,
    PublicUserProfileSerializer, RegisterSerializer, UserSerializer,
)
from .email_verification import (
    REQUESTED as EMAIL_VERIFICATION_REQUESTED, confirm_email_verification, request_email_verification,
)
from .magic_link import REQUESTED as MAGIC_LINK_REQUESTED, confirm_magic_link, request_magic_link
from .password_reset import confirm_password_reset, request_password_reset


User = get_user_model()


class AuthAttemptThrottleMixin:
    """Strict per-IP limit for endpoints that check a password or create accounts."""

    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth"


class LoginView(AuthAttemptThrottleMixin, TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenObtainPairSerializer


class LogoutView(TokenBlacklistView):
    """Blacklists the posted refresh token so it can't mint new access tokens."""


class RegisterView(AuthAttemptThrottleMixin, generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        try:
            request_email_verification(user)
        except EmailDeliveryError:
            pass
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user, context={"request": request}).data,
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserProfileView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        return Response(PublicUserProfileSerializer(user, context={"request": request}).data)


class UserReviewsView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ReviewSerializer

    def get_queryset(self):
        user = get_object_or_404(User, pk=self.kwargs["user_id"])
        return Review.objects.select_related(
            "reviewer", "reviewee", "deal__conversation__listing",
        ).filter(reviewee=user)


RESET_REQUESTED = "If an account uses that email, we've sent a link to reset the password."


class PasswordResetRequestView(APIView):
    permission_classes = (permissions.AllowAny,)
    # A stale token in the browser must not block account recovery.
    authentication_classes = ()
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            request_password_reset(serializer.validated_data["email"])
        except EmailDeliveryError as exc:
            raise EmailDeliveryFailed(detail=exc.detail)
        return Response({"detail": RESET_REQUESTED})


class PasswordResetConfirmView(AuthAttemptThrottleMixin, APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        confirm_password_reset(**serializer.validated_data)
        return Response({"detail": "Password updated. Sign in with your new password."})


class MagicLinkRequestView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "magic_link"

    def post(self, request):
        serializer = MagicLinkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            request_magic_link(serializer.validated_data["email"])
        except EmailDeliveryError as exc:
            raise EmailDeliveryFailed(detail=exc.detail)
        return Response({"detail": MAGIC_LINK_REQUESTED})


class MagicLinkConfirmView(AuthAttemptThrottleMixin, APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        serializer = MagicLinkConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access, refresh, user = confirm_magic_link(**serializer.validated_data)
        return Response({
            "access": access,
            "refresh": refresh,
            "user": UserSerializer(user, context={"request": request}).data,
        })


class EmailVerificationRequestView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "email_verification"

    def post(self, request):
        try:
            request_email_verification(request.user)
        except EmailDeliveryError as exc:
            raise EmailDeliveryFailed(detail=exc.detail)
        return Response({"detail": EMAIL_VERIFICATION_REQUESTED})


class EmailVerificationConfirmView(AuthAttemptThrottleMixin, APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = confirm_email_verification(**serializer.validated_data)
        return Response({
            "detail": "Email verified.",
            "user": UserSerializer(user, context={"request": request}).data,
        })
