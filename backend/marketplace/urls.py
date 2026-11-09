from django.urls import path
from rest_framework.routers import DefaultRouter

from .analytics_views import BusinessAnalyticsView
from .views import ListingViewSet


router = DefaultRouter()
router.register("listings", ListingViewSet, basename="listing")
urlpatterns = router.urls + [
    path("analytics/me/", BusinessAnalyticsView.as_view(), name="analytics-me"),
]

