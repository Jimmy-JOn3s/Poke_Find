from django.core.exceptions import PermissionDenied as DjangoPermissionDenied, ValidationError as DjangoValidationError
from django.db.models import Prefetch, Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Conversation, Deal, Offer
from .serializers import (
    ConversationSerializer, CounterOfferSerializer, DealSerializer, MessageSerializer, OfferSerializer,
    ReadConversationSerializer, ReviewCreateSerializer, ReviewSerializer, SellerReserveSerializer,
)
from .services import cancel_deal, confirm_deal, create_review, place_offer, seller_reserve_listing, transition_offer


def call_service(func, *args):
    """Run a service function and turn Django's errors into DRF's 403/400 responses."""
    try:
        return func(*args)
    except DjangoPermissionDenied as exc:
        raise PermissionDenied(str(exc)) from exc
    except DjangoValidationError as exc:
        raise ValidationError(exc.messages) from exc


THREAD_PAGE_MAX = 100


def thread_page(request, queryset):
    """Opt-in paging for a conversation's messages or offers, newest first.

    ?limit=N returns the newest N rows; ?before=<id> continues with rows older than that id.
    Returns (rows, has_more), or None when the client sent no limit: clients written before paging
    existed keep getting the whole thread as a plain list.
    """
    if "limit" not in request.query_params:
        return None
    try:
        limit = int(request.query_params["limit"])
        before = int(request.query_params["before"]) if "before" in request.query_params else None
    except ValueError:
        raise ValidationError({"detail": "limit and before must be whole numbers."})
    if not 1 <= limit <= THREAD_PAGE_MAX:
        raise ValidationError({"limit": f"Choose a limit between 1 and {THREAD_PAGE_MAX}."})
    queryset = queryset.order_by("-pk")
    if before is not None:
        queryset = queryset.filter(pk__lt=before)
    rows = list(queryset[:limit + 1])  # one extra row answers "is there more?" without a COUNT
    return rows[:limit], len(rows) > limit


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        deals = Deal.objects.select_related("conversation__buyer", "conversation__seller").prefetch_related("reviews")
        return Conversation.objects.select_related("listing", "buyer", "seller").prefetch_related(
            Prefetch("deals", queryset=deals),
        ).filter(Q(buyer=self.request.user) | Q(seller=self.request.user))

    @action(detail=True, methods=("post",))
    def read(self, request, pk=None):
        conversation = self.get_object()
        serializer = ReadConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = conversation.messages.filter(pk=serializer.validated_data["message_id"]).first()
        if message is None:
            raise ValidationError({"message_id": "Message does not belong to this conversation"})
        field = "buyer_read_at" if request.user.id == conversation.buyer_id else "seller_read_at"
        # Mark only messages already displayed, and never move the read time backwards.
        Conversation.objects.filter(pk=conversation.pk).filter(
            Q(**{f"{field}__isnull": True}) | Q(**{f"{field}__lt": message.created_at})
        ).update(**{field: message.created_at})
        conversation.refresh_from_db()
        return Response(self.get_serializer(conversation).data)

    @action(detail=True, methods=("get", "post"))
    def messages(self, request, pk=None):
        conversation = self.get_object()
        if request.method == "GET":
            messages = conversation.messages.select_related("author")
            page = thread_page(request, messages)
            if page is None:
                return Response(MessageSerializer(messages, many=True).data)
            rows, has_more = page
            # Oldest first within the page, the order a chat is read in.
            return Response({"results": MessageSerializer(rows[::-1], many=True).data, "has_more": has_more})
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(conversation=conversation, author=request.user)
        # The inbox is ordered by updated_at, so a new message must move the thread to the top.
        Conversation.objects.filter(pk=conversation.pk).update(updated_at=message.created_at)
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=("get", "post"))
    def offers(self, request, pk=None):
        conversation = self.get_object()
        if request.method == "GET":
            offers = conversation.offers.select_related("proposer")
            page = thread_page(request, offers)
            if page is None:
                return Response(OfferSerializer(offers, many=True).data)
            rows, has_more = page
            return Response({"results": OfferSerializer(rows, many=True).data, "has_more": has_more})
        serializer = OfferSerializer(data=request.data, context={"conversation": conversation})
        serializer.is_valid(raise_exception=True)
        offer = call_service(
            place_offer, conversation, request.user,
            serializer.validated_data["amount"], serializer.validated_data["currency"],
        )
        return Response(OfferSerializer(offer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=("post",))
    def reserve(self, request, pk=None):
        conversation = self.get_object()
        serializer = SellerReserveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data.get("amount")
        if amount is None:
            amount = conversation.listing.asking_price
        deal = call_service(seller_reserve_listing, conversation, request.user, amount)
        return Response(
            DealSerializer(deal, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class OfferViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Offer.objects.select_related("conversation", "proposer").filter(
            Q(conversation__buyer=self.request.user) | Q(conversation__seller=self.request.user)
        )

    def _transition(self, request, action_name, amount=None):
        offer = call_service(transition_offer, self.get_object(), request.user, action_name, amount)
        return Response(OfferSerializer(offer).data)

    @action(detail=True, methods=("post",))
    def accept(self, request, pk=None):
        return self._transition(request, "accept")

    @action(detail=True, methods=("post",))
    def decline(self, request, pk=None):
        return self._transition(request, "decline")

    @action(detail=True, methods=("post",))
    def counter(self, request, pk=None):
        serializer = CounterOfferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._transition(request, "counter", serializer.validated_data["amount"])


class DealViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DealSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Deal.objects.select_related(
            "conversation__buyer", "conversation__seller",
        ).prefetch_related("reviews").filter(
            Q(conversation__buyer=self.request.user) | Q(conversation__seller=self.request.user)
        )

    @action(detail=True, methods=("post",), url_path="confirm-completion")
    def confirm_completion(self, request, pk=None):
        deal = call_service(confirm_deal, self.get_object(), request.user)
        return Response(DealSerializer(deal, context={"request": request}).data)

    @action(detail=True, methods=("post",))
    def cancel(self, request, pk=None):
        deal = call_service(cancel_deal, self.get_object(), request.user)
        return Response(DealSerializer(deal, context={"request": request}).data)

    @action(detail=True, methods=("post",), url_path="review")
    def review(self, request, pk=None):
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deal = self.get_object()
        created = call_service(
            create_review, deal, request.user,
            serializer.validated_data["rating"], serializer.validated_data.get("comment", ""),
        )
        review = deal.reviews.select_related(
            "reviewer", "reviewee", "deal__conversation__listing",
        ).get(pk=created.pk)
        return Response(
            ReviewSerializer(review, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
