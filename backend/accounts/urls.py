from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView, LogoutView, MagicLinkConfirmView, MagicLinkRequestView, MeView, PasswordResetConfirmView,
    PasswordResetRequestView, RegisterView, UserProfileView, UserReviewsView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("magic-link/", MagicLinkRequestView.as_view(), name="magic-link"),
    path("magic-link/confirm/", MagicLinkConfirmView.as_view(), name="magic-link-confirm"),
    path("me/", MeView.as_view(), name="me"),
    path("users/<int:user_id>/", UserProfileView.as_view(), name="user-profile"),
    path("users/<int:user_id>/reviews/", UserReviewsView.as_view(), name="user-reviews"),
]
