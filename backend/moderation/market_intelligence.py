from decimal import Decimal

from django.db.models import Avg, Count, Sum

from messaging.models import Deal

from .serializers import AdminCompletedDealSerializer


def platform_market_intelligence():
    completed = Deal.objects.filter(
        status=Deal.Status.COMPLETED,
        completed_at__isnull=False,
    ).select_related(
        "conversation",
        "conversation__buyer",
        "conversation__seller",
        "conversation__listing",
    )

    revenue_by_currency = {
        row["currency"]: str(row["total"] or Decimal("0"))
        for row in completed.values("currency").annotate(total=Sum("final_price"))
    }

    top_cards = list(
        completed.values("card_name", "card_set", "currency")
        .annotate(sold=Count("id"), revenue=Sum("final_price"), avg_price=Avg("final_price"))
        .order_by("-sold", "-revenue")[:10]
    )
    for row in top_cards:
        row["revenue"] = str(row["revenue"] or Decimal("0"))
        row["avg_price"] = str(row["avg_price"] or Decimal("0"))
        row["name"] = row.pop("card_name") or "—"

    recent = completed.order_by("-completed_at")[:30]
    transactions = AdminCompletedDealSerializer(recent, many=True).data

    return {
        "completed_deals": completed.count(),
        "revenue_by_currency": revenue_by_currency,
        "top_cards": top_cards,
        "recent_transactions": transactions,
    }