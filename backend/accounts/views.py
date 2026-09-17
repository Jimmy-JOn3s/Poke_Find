from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from messaging.models import Review
from messaging.serializers import ReviewSerializer

from .serializers import (
    EmailOrUsernameTokenObtainPairSerializer, PublicUserProfileSerializer,
    RegisterSerializer, UserSerializer,
)


User = get_user_model()


class LoginView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
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
