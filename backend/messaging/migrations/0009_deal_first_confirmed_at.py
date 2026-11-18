from django.db import migrations, models
from django.db.models import F, Q


def backfill_first_confirmed_at(apps, schema_editor):
    Deal = apps.get_model("messaging", "Deal")
    partial = Deal.objects.filter(status="accepted").filter(
        Q(buyer_confirmed=True) | Q(seller_confirmed=True),
    )
    partial.filter(first_confirmed_at__isnull=True).update(first_confirmed_at=F("created_at"))


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0008_offer_declined_by_deal"),
    ]

    operations = [
        migrations.AddField(
            model_name="deal",
            name="first_confirmed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_first_confirmed_at, migrations.RunPython.noop),
    ]