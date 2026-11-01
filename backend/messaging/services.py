from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from marketplace.models import Listing
from .models import Conversation, Deal, Offer, Review


# Concurrency rules for the deal flow:
# 1. Every write locks the listing row first (lock_listing). One lock order everywhere means requests
#    on the same listing run one at a time on PostgreSQL and can never deadlock each other.
# 2. Every status change is also a conditional UPDATE whose row count is checked, so a stale read can
#    never win, even where row locks don't exist (SQLite, used only in development).

LIVE_DEAL_STATUSES = (Deal.Status.ACCEPTED, Deal.Status.COMPLETED)


def lock_listing(listing_id: int) -> Listing:
    listing = Listing.objects.select_for_update().filter(pk=listing_id).first()
    if listing is None:
        raise ValidationError("This listing is no longer available")
    return listing


def _move_listing(listing_id: int, expected: str, new: str) -> bool:
    return bool(Listing.objects.filter(pk=listing_id, status=expected).update(status=new, updated_at=timezone.now()))


def _claim_pending_offer(offer: Offer, new_status: str) -> None:
    claimed = Offer.objects.filter(pk=offer.pk, status=Offer.Status.PENDING).update(
        status=new_status, updated_at=timezone.now(),
    )
    if not claimed:
        raise ValidationError("Offer is no longer pending")
    offer.status = new_status


def _open_deal_for_listing(listing: Listing, conversation: Conversation, offer: Offer) -> Deal:
    if Deal.objects.filter(conversation=conversation, status__in=LIVE_DEAL_STATUSES).exists():
        raise ValidationError("This conversation already has an open deal")
    if not _move_listing(listing.pk, Listing.Status.ACTIVE, Listing.Status.RESERVED):
        raise ValidationError("This listing is no longer available")
    deal = Deal.objects.create(
        conversation=conversation, accepted_offer=offer, final_price=offer.amount, currency=offer.currency,
        card_name=listing.product_name, card_set=listing.set_name, condition=listing.condition,
    )
    Offer.objects.filter(
        conversation__listing_id=listing.pk, status=Offer.Status.PENDING,
    ).update(status=Offer.Status.DECLINED, updated_at=timezone.now())
    return deal


def ensure_listing_accepts_offers(listing: Listing) -> None:
    if listing.status != Listing.Status.ACTIVE:
        raise ValidationError("This listing is not accepting offers")


@transaction.atomic
def place_offer(conversation: Conversation, proposer, amount: Decimal, currency: str) -> Offer:
    # Holding the listing lock means an accept can't run between this check and the insert,
    # so no offer can slip past the "decline other pending offers" sweep below.
    listing = lock_listing(conversation.listing_id)
    ensure_listing_accepts_offers(listing)
    return Offer.objects.create(conversation=conversation, proposer=proposer, amount=amount, currency=currency)


@transaction.atomic
def transition_offer(offer: Offer, actor, action: str, amount: Decimal | None = None) -> Offer:
    listing = lock_listing(offer.conversation.listing_id)
    offer = Offer.objects.select_related("conversation").filter(pk=offer.pk).first()
    if offer is None:
        raise ValidationError("This offer no longer exists")
    conversation = offer.conversation
    if not conversation.has_participant(actor):
        raise PermissionDenied("Only conversation participants may act on an offer")
    if offer.proposer_id == actor.id:
        raise PermissionDenied("You cannot respond to your own offer")
    if offer.status != Offer.Status.PENDING:
        raise ValidationError("Offer is no longer pending")
    if action == "accept":
        _claim_pending_offer(offer, Offer.Status.ACCEPTED)
        _open_deal_for_listing(listing, conversation, offer)
        return offer
    if action == "decline":
        _claim_pending_offer(offer, Offer.Status.DECLINED)
        return offer
    if action == "counter":
        if amount is None or amount <= 0:
            raise ValidationError("Counter amount must be positive")
        ensure_listing_accepts_offers(listing)
        _claim_pending_offer(offer, Offer.Status.COUNTERED)
        return Offer.objects.create(
            conversation=conversation, proposer=actor, amount=amount, currency=offer.currency, counter_to=offer,
        )
    raise ValidationError("Unsupported offer action")


@transaction.atomic
def seller_reserve_listing(conversation: Conversation, seller, amount: Decimal) -> Deal:
    if seller.id != conversation.seller_id:
        raise PermissionDenied("Only the seller may reserve this listing for the buyer")
    if conversation.live_deal() is not None:
        raise ValidationError("This conversation already has an open deal")
    listing = lock_listing(conversation.listing_id)
    ensure_listing_accepts_offers(listing)
    if amount <= 0:
        raise ValidationError("Reservation price must be positive")
    offer = Offer.objects.create(
        conversation=conversation,
        proposer=seller,
        amount=amount,
        currency=listing.currency,
        status=Offer.Status.ACCEPTED,
    )
    return _open_deal_for_listing(listing, conversation, offer)


@transaction.atomic
def confirm_deal(deal: Deal, actor) -> Deal:
    conversation = Conversation.objects.get(pk=deal.conversation_id)
    if not conversation.has_participant(actor):
        raise PermissionDenied("Only deal participants may confirm completion")
    lock_listing(conversation.listing_id)
    if Deal.objects.filter(pk=deal.pk, status=Deal.Status.COMPLETED).exists():
        return Deal.objects.select_related("conversation").get(pk=deal.pk)
    # Set only the caller's own flag, so two confirmations can't overwrite each other.
    flag = "buyer_confirmed" if actor.id == conversation.buyer_id else "seller_confirmed"
    if not Deal.objects.filter(pk=deal.pk, status=Deal.Status.ACCEPTED).update(**{flag: True}):
        raise ValidationError("This deal is no longer open")
    completed = Deal.objects.filter(
        pk=deal.pk, status=Deal.Status.ACCEPTED, buyer_confirmed=True, seller_confirmed=True,
    ).update(status=Deal.Status.COMPLETED, completed_at=timezone.now())
    if completed and not _move_listing(conversation.listing_id, Listing.Status.RESERVED, Listing.Status.SOLD):
        raise ValidationError("The listing is not reserved for this deal")
    return Deal.objects.select_related("conversation").get(pk=deal.pk)


@transaction.atomic
def cancel_deal(deal: Deal, actor) -> Deal:
    conversation = Conversation.objects.get(pk=deal.conversation_id)
    if not conversation.has_participant(actor):
        raise PermissionDenied("Only deal participants may cancel")
    lock_listing(conversation.listing_id)
    cancelled = Deal.objects.filter(
        pk=deal.pk, status=Deal.Status.ACCEPTED, buyer_confirmed=False, seller_confirmed=False,
    ).update(status=Deal.Status.CANCELLED)
    if not cancelled:
        raise ValidationError("Only an open deal that nobody has confirmed yet can be cancelled")
    # Put the card back on sale unless another live deal still holds it (possible only with legacy data).
    if not Deal.objects.filter(conversation__listing_id=conversation.listing_id, status__in=LIVE_DEAL_STATUSES).exists():
        _move_listing(conversation.listing_id, Listing.Status.RESERVED, Listing.Status.ACTIVE)
    return Deal.objects.select_related("conversation").get(pk=deal.pk)


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
