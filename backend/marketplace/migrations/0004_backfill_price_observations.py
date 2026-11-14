from decimal import Decimal

from django.db import migrations


def backfill_price_observations(apps, schema_editor):
    Deal = apps.get_model("messaging", "Deal")
    PriceObservation = apps.get_model("marketplace", "PriceObservation")
    database = schema_editor.connection.alias
    completed = Deal.objects.using(database).filter(
        status="completed",
        completed_at__isnull=False,
    ).exclude(variant_key="").iterator(chunk_size=500)

    for deal in completed:
        asking = deal.asking_price if deal.asking_price is not None else Decimal("0.00")
        PriceObservation.objects.using(database).update_or_create(
            deal_id=deal.pk,
            defaults={
                "variant_key": deal.variant_key,
                "card_language": deal.card_language or "en",
                "set_code": deal.set_code or "",
                "card_number": deal.card_number or "",
                "condition": deal.condition or "NM",
                "card_name": deal.card_name or "",
                "card_set": deal.card_set or "",
                "asking_price": asking,
                "final_price": deal.final_price,
                "currency": deal.currency,
                "quantity": deal.quantity or 1,
                "traded_at": deal.completed_at,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0003_priceobservation"),
    ]

    operations = [
        migrations.RunPython(backfill_price_observations, migrations.RunPython.noop),
    ]