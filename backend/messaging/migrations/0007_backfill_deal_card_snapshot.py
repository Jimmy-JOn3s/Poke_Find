from django.db import migrations


def backfill_card_snapshot(apps, schema_editor):
    """Copy card name, set and condition from each deal's listing onto the deal itself,
    so older completed deals carry the same immutable record new deals now capture."""
    Deal = apps.get_model("messaging", "Deal")
    deals = Deal.objects.select_related("conversation__listing").all()
    for deal in deals:
        listing = getattr(deal.conversation, "listing", None)
        if listing is None:
            continue
        deal.card_name = listing.product_name
        deal.card_set = listing.set_name
        deal.condition = listing.condition
        deal.save(update_fields=["card_name", "card_set", "condition"])


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0006_deal_card_name_deal_card_set_deal_condition"),
    ]

    operations = [
        migrations.RunPython(backfill_card_snapshot, migrations.RunPython.noop),
    ]
