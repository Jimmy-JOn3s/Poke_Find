from django.db import migrations


def _variant_key(card_language, set_code, card_number, condition) -> str:
    return ":".join([
        (card_language or "").strip().lower(),
        (set_code or "").strip().lower(),
        (card_number or "").strip().lower(),
        (condition or "").strip().upper(),
    ])


def backfill_market_snapshots(apps, schema_editor):
    Deal = apps.get_model("messaging", "Deal")
    database = schema_editor.connection.alias
    deals = Deal.objects.using(database).select_related("conversation__listing")
    for deal in deals.iterator(chunk_size=500):
        listing = getattr(deal.conversation, "listing", None)
        if listing is None:
            continue
        deal.card_name = listing.product_name
        deal.card_set = listing.set_name
        deal.set_code = listing.set_code or ""
        deal.card_number = listing.card_number or ""
        deal.card_language = listing.card_language
        deal.condition = listing.condition
        deal.asking_price = listing.asking_price
        deal.quantity = listing.quantity or 1
        deal.variant_key = _variant_key(
            listing.card_language, listing.set_code, listing.card_number, listing.condition,
        )
        deal.save(
            using=database,
            update_fields=[
                "card_name",
                "card_set",
                "set_code",
                "card_number",
                "card_language",
                "condition",
                "asking_price",
                "quantity",
                "variant_key",
            ],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0009_deal_market_snapshot_fields"),
    ]

    operations = [
        migrations.RunPython(backfill_market_snapshots, migrations.RunPython.noop),
    ]