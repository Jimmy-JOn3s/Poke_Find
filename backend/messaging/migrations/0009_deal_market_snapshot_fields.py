from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0008_offer_declined_by_deal"),
    ]

    operations = [
        migrations.AddField(
            model_name="deal",
            name="asking_price",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="deal",
            name="card_language",
            field=models.CharField(blank=True, choices=[("th", "Thai"), ("en", "English"), ("ja", "Japanese")], max_length=2),
        ),
        migrations.AddField(
            model_name="deal",
            name="card_number",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="deal",
            name="quantity",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="deal",
            name="set_code",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="deal",
            name="variant_key",
            field=models.CharField(blank=True, db_index=True, max_length=200),
        ),
    ]