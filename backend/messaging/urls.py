from rest_framework.routers import DefaultRouter

from .views import ConversationViewSet, DealViewSet, OfferViewSet


router = DefaultRouter()
router.register("conversations", ConversationViewSet, basename="conversation")
router.register("offers", OfferViewSet, basename="offer")
router.register("deals", DealViewSet, basename="deal")
urlpatterns = router.urls
