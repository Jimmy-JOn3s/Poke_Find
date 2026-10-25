from django.db import migrations


def backfill_card_snapshot(apps, schema_editor):
    """Copy card name, set and condition from each deal's listing onto the deal itself,
    using current listing values; historical listing values cannot be recovered."""
    Deal = apps.get_model("messaging", "Deal")
    database = schema_editor.connection.alias
    deals = Deal.objects.using(database).select_related("conversation__listing")
    for deal in deals.iterator(chunk_size=1000):
        listing = getattr(deal.conversation, "listing", None)
        if listing is None:
            continue
        deal.card_name = listing.product_name
        deal.card_set = listing.set_name
        deal.condition = listing.condition
        deal.save(using=database, update_fields=["card_name", "card_set", "condition"])


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0006_deal_card_name_deal_card_set_deal_condition"),
    ]

    operations = [
        migrations.RunPython(backfill_card_snapshot, migrations.RunPython.noop),
    ]
