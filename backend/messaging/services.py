from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from marketplace.models import Listing
from .models import Deal, Offer, Review


@transaction.atomic
def transition_offer(offer: Offer, actor, action: str, amount: Decimal | None = None) -> Offer:
    offer = Offer.objects.select_for_update().select_related("conversation").get(pk=offer.pk)
    if not offer.conversation.has_participant(actor):
        raise PermissionDenied("Only conversation participants may act on an offer")
    if offer.status != Offer.Status.PENDING:
        raise ValidationError("Offer is no longer pending")
    if action in {"accept", "decline"} and actor.id != offer.conversation.seller_id:
        raise PermissionDenied("Only the seller may accept or decline")
    if action == "accept":
        offer.status = Offer.Status.ACCEPTED
        offer.save(update_fields=("status", "updated_at"))
        Deal.objects.get_or_create(
            conversation=offer.conversation,
            defaults={"accepted_offer": offer, "final_price": offer.amount, "currency": offer.currency},
        )
        return offer
    if action == "decline":
        offer.status = Offer.Status.DECLINED
        offer.save(update_fields=("status", "updated_at"))
        return offer
    if action == "counter":
        if amount is None or amount <= 0:
            raise ValidationError("Counter amount must be positive")
        offer.status = Offer.Status.COUNTERED
        offer.save(update_fields=("status", "updated_at"))
        return Offer.objects.create(
            conversation=offer.conversation, proposer=actor, amount=amount,
            currency=offer.currency, counter_to=offer,
        )
    raise ValidationError("Unsupported offer action")


@transaction.atomic
def confirm_deal(deal: Deal, actor) -> Deal:
    deal = Deal.objects.select_for_update().select_related("conversation__listing").get(pk=deal.pk)
    if not deal.conversation.has_participant(actor):
        raise PermissionDenied("Only deal participants may confirm completion")
    if actor.id == deal.conversation.buyer_id:
        deal.buyer_confirmed = True
    if actor.id == deal.conversation.seller_id:
        deal.seller_confirmed = True
    fields = ["buyer_confirmed", "seller_confirmed"]
    if deal.buyer_confirmed and deal.seller_confirmed:
        deal.status = Deal.Status.COMPLETED
        deal.completed_at = timezone.now()
        fields.extend(("status", "completed_at"))
        Listing.objects.filter(pk=deal.conversation.listing_id).update(status=Listing.Status.SOLD)
    deal.save(update_fields=fields)
    return deal


@transaction.atomic
def create_review(deal: Deal, reviewer, rating: int, comment: str = "") -> Review:
    deal = Deal.objects.select_for_update().select_related("conversation").get(pk=deal.pk)
    conversation = deal.conversation
    if not conversation.has_participant(reviewer):
        raise PermissionDenied("Only deal participants may leave a review")
    if deal.status != Deal.Status.COMPLETED:
        raise ValidationError("Reviews are only allowed after a completed deal")
    if reviewer.id == conversation.buyer_id:
        reviewee_id = conversation.seller_id
    elif reviewer.id == conversation.seller_id:
        reviewee_id = conversation.buyer_id
    else:
        raise PermissionDenied("Only deal participants may leave a review")
    if Review.objects.filter(deal=deal, reviewer=reviewer).exists():
        raise ValidationError("You have already reviewed this transaction")
    return Review.objects.create(
        deal=deal,
        reviewer=reviewer,
        reviewee_id=reviewee_id,
        rating=rating,
        comment=comment.strip(),
    )

