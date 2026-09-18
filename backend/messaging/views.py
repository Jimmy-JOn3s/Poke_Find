from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied, ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Conversation, Deal, Offer
from .serializers import (
    ConversationSerializer, DealSerializer, MessageSerializer, OfferSerializer,
    ReadConversationSerializer, ReviewCreateSerializer, ReviewSerializer,
)
from .services import confirm_deal, create_review, transition_offer


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ("get", "post", "head", "options")

    def get_queryset(self):
        return Conversation.objects.select_related(
            "listing", "buyer", "seller", "deal__conversation__buyer", "deal__conversation__seller",
        ).prefetch_related("deal__reviews").filter(
            Q(buyer=self.request.user) | Q(seller=self.request.user)
        )

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
            return Response(MessageSerializer(conversation.messages.select_related("author"), many=True).data)
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(conversation=conversation, author=request.user)
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=("get", "post"))
    def offers(self, request, pk=None):
        conversation = self.get_object()
        if request.method == "GET":
            return Response(OfferSerializer(conversation.offers.select_related("proposer"), many=True).data)
        serializer = OfferSerializer(data=request.data, context={"conversation": conversation})
        serializer.is_valid(raise_exception=True)
        offer = serializer.save(conversation=conversation, proposer=request.user)
        return Response(OfferSerializer(offer).data, status=status.HTTP_201_CREATED)


class OfferViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Offer.objects.select_related("conversation", "proposer").filter(
            Q(conversation__buyer=self.request.user) | Q(conversation__seller=self.request.user)
        )

    def _transition(self, request, action_name, pk, amount=None):
        try:
            offer = transition_offer(self.get_object(), request.user, action_name, amount)
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(str(exc)) from exc
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc
        return Response(OfferSerializer(offer).data)

    @action(detail=True, methods=("post",))
    def accept(self, request, pk=None):
        return self._transition(request, "accept", pk)

    @action(detail=True, methods=("post",))
    def decline(self, request, pk=None):
        return self._transition(request, "decline", pk)

    @action(detail=True, methods=("post",))
    def counter(self, request, pk=None):
        try:
            amount = Decimal(str(request.data.get("amount")))
        except (InvalidOperation, TypeError):
            raise ValidationError({"amount": "Enter a valid amount"})
        return self._transition(request, "counter", pk, amount)


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
        try:
            deal = confirm_deal(self.get_object(), request.user)
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(str(exc)) from exc
        return Response(DealSerializer(deal, context={"request": request}).data)

    @action(detail=True, methods=("post",), url_path="review")
    def review(self, request, pk=None):
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deal = self.get_object()
        try:
            created = create_review(
                deal,
                request.user,
                serializer.validated_data["rating"],
                serializer.validated_data.get("comment", ""),
            )
        except DjangoPermissionDenied as exc:
            raise PermissionDenied(str(exc)) from exc
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc
        review = deal.reviews.select_related(
            "reviewer", "reviewee", "deal__conversation__listing",
        ).get(pk=created.pk)
        return Response(
            ReviewSerializer(review, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

