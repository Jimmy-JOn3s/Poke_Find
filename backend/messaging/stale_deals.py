from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .models import Deal


def stale_deal_days_open() -> int:
    return int(getattr(settings, "STALE_DEAL_DAYS_OPEN", 14))


def stale_deal_days_partial() -> int:
    return int(getattr(settings, "STALE_DEAL_DAYS_PARTIAL", 7))


def is_deal_stale(deal: Deal, *, now=None) -> bool:
    now = now or timezone.now()
    if deal.status != Deal.Status.ACCEPTED:
        return False
    partial = deal.buyer_confirmed ^ deal.seller_confirmed
    if partial:
        anchor = deal.first_confirmed_at or deal.created_at
        return anchor <= now - timedelta(days=stale_deal_days_partial())
    if deal.buyer_confirmed or deal.seller_confirmed:
        return False
    return deal.created_at <= now - timedelta(days=stale_deal_days_open())


def stale_open_deals_queryset():
    now = timezone.now()
    open_cutoff = now - timedelta(days=stale_deal_days_open())
    partial_cutoff = now - timedelta(days=stale_deal_days_partial())
    both_confirmed = Q(buyer_confirmed=True, seller_confirmed=True)
    neither = Q(buyer_confirmed=False, seller_confirmed=False)
    exactly_one = (Q(buyer_confirmed=True, seller_confirmed=False) | Q(buyer_confirmed=False, seller_confirmed=True))
    return (
        Deal.objects.filter(status=Deal.Status.ACCEPTED)
        .exclude(both_confirmed)
        .filter(
            Q(neither, created_at__lte=open_cutoff)
            | Q(
                exactly_one,
                first_confirmed_at__lte=partial_cutoff,
            )
            | Q(
                exactly_one,
                first_confirmed_at__isnull=True,
                created_at__lte=partial_cutoff,
            ),
        )
        .select_related(
            "conversation",
            "conversation__listing",
            "conversation__buyer",
            "conversation__seller",
        )
    )