from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Listing, SavedListing
from .permissions import IsOwnerOrReadOnly
from .serializers import ListingSerializer


def _price_param(request, name):
    raw = request.query_params.get(name)
    if not raw:
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        value = None
    if value is None or not value.is_finite() or value < 0:
        raise ValidationError({name: "Enter a valid non-negative number."})
    return value


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
        if (minimum := _price_param(self.request, "min_price")) is not None:
            queryset = queryset.filter(asking_price__gte=minimum)
        if (maximum := _price_param(self.request, "max_price")) is not None:
            queryset = queryset.filter(asking_price__lte=maximum)
        return queryset

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    def perform_destroy(self, instance):
        with transaction.atomic():
            # Same lock order as the deal flow (listing first), so an offer can't be accepted between the
            # check and the delete, and the two can't deadlock.
            listing = Listing.objects.select_for_update().get(pk=instance.pk)
            if listing.conversations.filter(deals__isnull=False).exists():
                raise ValidationError("This listing has deals and can't be deleted. Hide it instead.")
            listing.delete()

    @action(detail=True, methods=("post", "delete"), permission_classes=(permissions.IsAuthenticated,))
    def save(self, request, pk=None):
        listing = self.get_object()
        if request.method == "POST":
            SavedListing.objects.get_or_create(user=request.user, listing=listing)
            return Response({"saved": True})
        SavedListing.objects.filter(user=request.user, listing=listing).delete()
        return Response({"saved": False}, status=status.HTTP_200_OK)

