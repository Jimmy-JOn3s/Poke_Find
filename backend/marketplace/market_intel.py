from __future__ import annotations

from django.conf import settings

from marketplace.models import Listing, PriceObservation
from marketplace.variant_key import compute_variant_key


def listing_snapshot_fields(listing: Listing) -> dict:
    variant_key = compute_variant_key(
        card_language=listing.card_language,
        set_code=listing.set_code,
        card_number=listing.card_number,
        condition=listing.condition,
    )
    return {
        "card_name": listing.product_name,
        "card_set": listing.set_name,
        "set_code": listing.set_code or "",
        "card_number": listing.card_number or "",
        "card_language": listing.card_language,
        "condition": listing.condition,
        "asking_price": listing.asking_price,
        "quantity": listing.quantity,
        "variant_key": variant_key,
    }


def record_price_observation(deal) -> PriceObservation | None:
    from messaging.models import Deal

    if deal.status != Deal.Status.COMPLETED or deal.completed_at is None:
        return None
    variant_key = (deal.variant_key or "").strip()
    if not variant_key:
        return None
    asking_price = deal.asking_price if deal.asking_price is not None else deal.final_price
    observation, _ = PriceObservation.objects.update_or_create(
        deal_id=deal.pk,
        defaults={
            "variant_key": variant_key,
            "card_language": deal.card_language,
            "set_code": deal.set_code or "",
            "card_number": deal.card_number or "",
            "condition": deal.condition,
            "card_name": deal.card_name or "",
            "card_set": deal.card_set or "",
            "asking_price": asking_price,
            "final_price": deal.final_price,
            "currency": deal.currency,
            "quantity": deal.quantity,
            "traded_at": deal.completed_at,
        },
    )
    return observation


def variant_market_summary(*, variant_key: str, currency: str | None = None) -> dict:
    min_sales = int(getattr(settings, "MARKET_PRICE_MIN_SALES", 20))
    qs = PriceObservation.objects.filter(variant_key=variant_key)
    if currency:
        qs = qs.filter(currency=currency)
    count = qs.count()
    return {
        "variant_key": variant_key,
        "currency": currency,
        "completed_sales": count,
        "min_sales_for_recommendation": min_sales,
        "sufficient_data": count >= min_sales,
        "recommendation": None,
    }