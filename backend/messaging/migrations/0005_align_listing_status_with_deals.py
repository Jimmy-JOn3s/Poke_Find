from django.db import migrations


LIVE_DEAL_STATUSES = ("accepted", "completed")


def align_listing_status_with_deals(apps, schema_editor):
    """Before this release a listing could get several live deals, and accepting never changed its
    status. Restore the invariant: at most one live deal per listing, with the listing RESERVED while
    that deal is open and SOLD once it is completed."""
    Deal = apps.get_model("messaging", "Deal")
    Listing = apps.get_model("marketplace", "Listing")
    deals_by_listing = {}
    rows = Deal.objects.filter(status__in=LIVE_DEAL_STATUSES).values_list("conversation__listing_id", "id", "status")
    for listing_id, deal_id, status in rows:
        deals_by_listing.setdefault(listing_id, []).append((deal_id, status))
    conflicts = {listing_id: deals for listing_id, deals in deals_by_listing.items() if len(deals) > 1}
    if conflicts:
        details = "; ".join(
            f"listing {listing_id}: deals {[deal_id for deal_id, _ in deals]}"
            for listing_id, deals in sorted(conflicts.items())
        )
        raise RuntimeError(
            "These listings were promised or sold to more than one buyer. Decide which deal stands, set the "
            f"others to 'cancelled' in the Django admin (Messaging > Deals), then run migrate again. {details}"
        )
    for listing_id, [(_, status)] in deals_by_listing.items():
        Listing.objects.filter(pk=listing_id).update(status="sold" if status == "completed" else "reserved")


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0002_listing_image_url"),
        ("messaging", "0004_deal_conversation_fk"),
    ]

    operations = [migrations.RunPython(align_listing_status_with_deals, migrations.RunPython.noop)]
