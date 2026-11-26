import logging
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from marketplace.market_intel import listing_snapshot_fields, record_price_observation
from marketplace.models import Listing
from .models import Conversation, Deal, Offer, Review

logger = logging.getLogger(__name__)


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
        conversation=conversation,
        accepted_offer=offer,
        final_price=offer.amount,
        currency=offer.currency,
        **listing_snapshot_fields(listing),
    )
    logger.info(
        "Deal %s opened: listing=%s buyer=%s seller=%s price=%s %s",
        deal.pk, listing.pk, conversation.buyer_id, conversation.seller_id, deal.final_price, deal.currency,
    )
    Offer.objects.filter(
        conversation__listing_id=listing.pk, status=Offer.Status.PENDING,
    ).update(status=Offer.Status.DECLINED, declined_by_deal=deal, updated_at=timezone.now())
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
    # A double-tap or retry would otherwise leave two identical pending offers; the listing lock serializes the check.
    if Offer.objects.filter(
        conversation=conversation, proposer=proposer, amount=amount, currency=currency, status=Offer.Status.PENDING,
    ).exists():
        raise ValidationError("You already have a pending offer for this amount")
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
    after = Deal.objects.filter(pk=deal.pk).values("buyer_confirmed", "seller_confirmed").first()
    if after and after["buyer_confirmed"] ^ after["seller_confirmed"]:
        Deal.objects.filter(pk=deal.pk, first_confirmed_at__isnull=True).update(first_confirmed_at=timezone.now())
    logger.info("Deal %s confirmed by user=%s (%s)", deal.pk, actor.id, flag)
    _complete_deal(deal.pk, conversation.listing_id, buyer_confirmed=True, seller_confirmed=True)
    return Deal.objects.select_related("conversation").get(pk=deal.pk)


def _complete_deal(deal_pk: int, listing_id: int, **confirmations) -> bool:
    """Complete the open deal if its confirmation flags still equal `confirmations`, sell the listing, record the sale."""
    if not Deal.objects.filter(pk=deal_pk, status=Deal.Status.ACCEPTED, **confirmations).update(
        status=Deal.Status.COMPLETED, completed_at=timezone.now(),
    ):
        return False
    if not _move_listing(listing_id, Listing.Status.RESERVED, Listing.Status.SOLD):
        raise ValidationError("The listing is not reserved for this deal")
    logger.info("Deal %s completed: listing=%s sold", deal_pk, listing_id)
    _record_sale(deal_pk)
    return True


def _record_sale(deal_pk: int) -> None:
    """Record the sale for market data. A failure here must not undo the user's completed deal."""
    try:
        # The savepoint keeps a database error from poisoning the surrounding transaction.
        with transaction.atomic():
            record_price_observation(Deal.objects.get(pk=deal_pk))
    except Exception:
        logger.exception(
            "Deal %s completed but its price observation was not recorded; "
            "run `manage.py backfill_price_observations`", deal_pk,
        )


def _release_listing_after_cancel(deal: Deal, conversation: Conversation) -> None:
    if not Deal.objects.filter(conversation__listing_id=conversation.listing_id, status__in=LIVE_DEAL_STATUSES).exists():
        if _move_listing(conversation.listing_id, Listing.Status.RESERVED, Listing.Status.ACTIVE):
            Offer.objects.filter(
                declined_by_deal=deal, status=Offer.Status.DECLINED,
            ).update(status=Offer.Status.PENDING, declined_by_deal=None, updated_at=timezone.now())


@transaction.atomic
def _cancel_accepted_deal(deal: Deal, *, require_unconfirmed: bool) -> Deal:
    conversation = Conversation.objects.get(pk=deal.conversation_id)
    lock_listing(conversation.listing_id)
    queryset = Deal.objects.filter(pk=deal.pk, status=Deal.Status.ACCEPTED)
    if require_unconfirmed:
        queryset = queryset.filter(buyer_confirmed=False, seller_confirmed=False)
    cancelled = queryset.update(
        status=Deal.Status.CANCELLED,
        buyer_confirmed=False,
        seller_confirmed=False,
        first_confirmed_at=None,
    )
    if not cancelled:
        if require_unconfirmed:
            raise ValidationError("Only an open deal that nobody has confirmed yet can be cancelled")
        raise ValidationError("This deal is no longer open")
    _release_listing_after_cancel(deal, conversation)
    logger.info("Deal %s cancelled: listing=%s forced=%s", deal.pk, conversation.listing_id, not require_unconfirmed)
    return Deal.objects.select_related("conversation").get(pk=deal.pk)


@transaction.atomic
def cancel_deal(deal: Deal, actor) -> Deal:
    conversation = Conversation.objects.get(pk=deal.conversation_id)
    if not conversation.has_participant(actor):
        raise PermissionDenied("Only deal participants may cancel")
    return _cancel_accepted_deal(deal, require_unconfirmed=True)


@transaction.atomic
def force_cancel_deal(deal: Deal) -> Deal:
    return _cancel_accepted_deal(deal, require_unconfirmed=False)


@transaction.atomic
def _settle_stale_deal(deal_pk: int) -> str | None:
    from .stale_deals import StaleOutcome, stale_outcome

    listing_id = Deal.objects.filter(pk=deal_pk).values_list("conversation__listing_id", flat=True).first()
    if listing_id is None:
        return None
    lock_listing(listing_id)
    # Decide again under the lock: a confirmation may have landed since the deal was picked.
    deal = Deal.objects.get(pk=deal_pk)
    outcome = stale_outcome(deal)
    if outcome == StaleOutcome.COMPLETE:
        completed = _complete_deal(deal_pk, listing_id, buyer_confirmed=True, seller_confirmed=False)
        return outcome if completed else None
    if outcome == StaleOutcome.CANCEL:
        _cancel_accepted_deal(deal, require_unconfirmed=True)
    # AWAIT_BUYER changes nothing: the listing stays reserved until the buyer confirms or staff step in.
    return outcome


def expire_stale_deals() -> dict[str, int]:
    """Settle every overdue open deal and report how many were completed, left waiting, cancelled, or failed.

    A deal that raises is logged and skipped so it can't block the rest, but it is counted in "failed":
    callers must surface that number, otherwise an outage looks like "nothing was overdue".
    """
    from .stale_deals import StaleOutcome, stale_open_deals_queryset

    counts = {StaleOutcome.COMPLETE: 0, StaleOutcome.AWAIT_BUYER: 0, StaleOutcome.CANCEL: 0}
    failed = 0
    for deal_pk in list(stale_open_deals_queryset().values_list("pk", flat=True)):
        # One transaction per deal, so a deal with inconsistent data can't undo or block the rest.
        try:
            outcome = _settle_stale_deal(deal_pk)
        except Exception:  # not only ValidationError: a database error on one deal must not stop the batch
            logger.exception("Could not settle stale deal %s", deal_pk)
            failed += 1
            continue
        if outcome:
            counts[outcome] += 1
            logger.info("Stale deal %s settled: %s", deal_pk, outcome)
    return {
        "completed": counts[StaleOutcome.COMPLETE],
        "awaiting_buyer": counts[StaleOutcome.AWAIT_BUYER],
        "cancelled": counts[StaleOutcome.CANCEL],
        "failed": failed,
    }


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
