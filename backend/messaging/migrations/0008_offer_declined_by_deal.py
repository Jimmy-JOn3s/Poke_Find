import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0007_backfill_deal_card_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="offer",
            name="declined_by_deal",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="superseded_offers",
                to="messaging.deal",
            ),
        ),
    ]
