from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, MeView, RegisterView, UserProfileView, UserReviewsView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("users/<int:user_id>/", UserProfileView.as_view(), name="user-profile"),
    path("users/<int:user_id>/reviews/", UserReviewsView.as_view(), name="user-reviews"),
]
