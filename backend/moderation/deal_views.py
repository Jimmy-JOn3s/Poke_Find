from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from messaging.models import Deal
from messaging.services import expire_stale_deals, force_cancel_deal

from .deal_serializers import AdminOpenDealSerializer
from .permissions import IsStaffUser


class AdminOpenDealListView(generics.ListAPIView):
    permission_classes = (IsStaffUser,)
    serializer_class = AdminOpenDealSerializer

    def get_queryset(self):
        queryset = Deal.objects.filter(status=Deal.Status.ACCEPTED).select_related(
            "conversation",
            "conversation__listing",
            "conversation__buyer",
            "conversation__seller",
        )
        stale_only = self.request.query_params.get("stale", "").strip().lower()
        if stale_only in {"1", "true", "yes"}:
            from messaging.stale_deals import stale_open_deals_queryset

            return stale_open_deals_queryset()
        return queryset.order_by("-created_at")


class AdminForceCancelDealView(APIView):
    permission_classes = (IsStaffUser,)

    def post(self, request, pk):
        deal = Deal.objects.select_related(
            "conversation", "conversation__listing", "conversation__buyer", "conversation__seller",
        ).filter(pk=pk).first()
        if deal is None:
            raise Http404
        try:
            cancelled = force_cancel_deal(deal)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc
        deal = Deal.objects.select_related(
            "conversation", "conversation__listing", "conversation__buyer", "conversation__seller",
        ).get(pk=cancelled.pk)
        return Response({"status": "cancelled", "deal_id": deal.pk, "listing_id": deal.conversation.listing_id})


class AdminExpireStaleDealsView(APIView):
    permission_classes = (IsStaffUser,)

    def post(self, request):
        counts = expire_stale_deals()
        # "released" is kept for older clients: it counts listings put back on sale.
        return Response({**counts, "released": counts["cancelled"]})