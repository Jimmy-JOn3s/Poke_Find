import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0010_backfill_deal_market_snapshots"),
        ("marketplace", "0002_listing_image_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="PriceObservation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("variant_key", models.CharField(db_index=True, max_length=200)),
                ("card_language", models.CharField(choices=[("th", "Thai"), ("en", "English"), ("ja", "Japanese")], max_length=2)),
                ("set_code", models.CharField(blank=True, db_index=True, max_length=40)),
                ("card_number", models.CharField(blank=True, db_index=True, max_length=40)),
                ("condition", models.CharField(choices=[("M", "Mint"), ("NM", "Near mint"), ("LP", "Lightly played"), ("MP", "Moderately played"), ("HP", "Heavily played")], max_length=2)),
                ("card_name", models.CharField(blank=True, max_length=180)),
                ("card_set", models.CharField(blank=True, max_length=180)),
                ("asking_price", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ("final_price", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ("currency", models.CharField(choices=[("THB", "Thai baht"), ("USD", "US dollar")], max_length=3)),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("traded_at", models.DateTimeField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("deal", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="price_observation", to="messaging.deal")),
            ],
            options={
                "ordering": ("-traded_at",),
                "indexes": [models.Index(fields=["variant_key", "currency"], name="marketplace_varian_c1e0a0_idx")],
            },
        ),
    ]