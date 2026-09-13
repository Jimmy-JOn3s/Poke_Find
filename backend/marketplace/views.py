from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Listing, SavedListing
from .permissions import IsOwnerOrReadOnly
from .serializers import ListingSerializer


class ListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)

    def get_queryset(self):
        queryset = Listing.objects.select_related("seller")
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.filter(Q(status=Listing.Status.ACTIVE) | Q(seller=user))
        else:
            queryset = queryset.filter(status=Listing.Status.ACTIVE)
        query = self.request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(product_name__icontains=query) | Q(set_name__icontains=query)
                | Q(set_code__icontains=query) | Q(card_number__icontains=query)
            )
        for field in ("currency", "condition", "card_language", "rarity", "status"):
            value = self.request.query_params.get(field)
            if value:
                queryset = queryset.filter(**{field: value})
        if minimum := self.request.query_params.get("min_price"):
            queryset = queryset.filter(asking_price__gte=minimum)
        if maximum := self.request.query_params.get("max_price"):
            queryset = queryset.filter(asking_price__lte=maximum)
        return queryset

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    @action(detail=True, methods=("post", "delete"), permission_classes=(permissions.IsAuthenticated,))
    def save(self, request, pk=None):
        listing = self.get_object()
        if request.method == "POST":
            SavedListing.objects.get_or_create(user=request.user, listing=listing)
            return Response({"saved": True})
        SavedListing.objects.filter(user=request.user, listing=listing).delete()
        return Response({"saved": False}, status=status.HTTP_200_OK)

