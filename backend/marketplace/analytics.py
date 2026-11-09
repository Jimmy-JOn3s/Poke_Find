from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from accounts.models import User
from accounts.serializers import user_review_stats
from marketplace.models import Listing
from messaging.models import Deal


def business_analytics(user: User) -> dict:
    stats = user_review_stats(user)
    listing_counts = {
        row["status"]: row["count"]
        for row in Listing.objects.filter(seller=user).values("status").annotate(count=Count("id"))
    }
    active_deals = Deal.objects.filter(
        conversation__seller=user, status=Deal.Status.ACCEPTED,
    ).count()

    completed = Deal.objects.filter(
        conversation__seller=user, status=Deal.Status.COMPLETED, completed_at__isnull=False,
    ).select_related("conversation__buyer")

    revenue_by_currency: dict[str, str] = {}
    for row in completed.values("currency").annotate(total=Sum("final_price")):
        revenue_by_currency[row["currency"]] = str(row["total"] or Decimal("0"))

    transactions = completed.count()
    chart_currency = user.preferred_currency
    six_months_ago = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=180)

    monthly_raw = (
        completed.filter(completed_at__gte=six_months_ago, currency=chart_currency)
        .annotate(month=TruncMonth("completed_at"))
        .values("month")
        .annotate(revenue=Sum("final_price"), transactions=Count("id"))
        .order_by("month")
    )
    monthly_index = {row["month"].date().isoformat(): row for row in monthly_raw if row["month"]}
    monthly = []
    cursor = six_months_ago
    now = timezone.now()
    while cursor <= now:
        key = cursor.date().replace(day=1).isoformat()
        bucket = monthly_index.get(key)
        monthly.append({
            "month": key,
            "revenue": str(bucket["revenue"] if bucket else Decimal("0")),
            "transactions": bucket["transactions"] if bucket else 0,
            "currency": chart_currency,
        })
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year + 1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month + 1)
        cursor = cursor.replace(day=1)
    monthly = monthly[-6:]

    top_cards = list(
        completed.values("card_name", "currency")
        .annotate(sold=Count("id"), revenue=Sum("final_price"))
        .order_by("-sold", "-revenue")[:5]
    )
    for row in top_cards:
        row["revenue"] = str(row["revenue"] or Decimal("0"))
        row["name"] = row.pop("card_name") or "—"

    recent_sales = []
    for deal in completed.order_by("-completed_at")[:8]:
        recent_sales.append({
            "card_name": deal.card_name or "—",
            "buyer_name": deal.conversation.buyer.display_name,
            "price": str(deal.final_price),
            "currency": deal.currency,
            "completed_at": deal.completed_at.isoformat(),
        })

    return {
        "revenue_by_currency": revenue_by_currency,
        "chart_currency": chart_currency,
        "transactions": transactions,
        "deals_active": active_deals,
        "listings": {
            "active": listing_counts.get(Listing.Status.ACTIVE, 0),
            "reserved": listing_counts.get(Listing.Status.RESERVED, 0),
            "sold": listing_counts.get(Listing.Status.SOLD, 0),
            "total": sum(listing_counts.values()),
        },
        "rating": stats["rating"],
        "review_count": stats["review_count"],
        "total_sold": stats["total_sold"],
        "monthly": monthly,
        "top_cards": top_cards,
        "recent_sales": recent_sales,
    }
