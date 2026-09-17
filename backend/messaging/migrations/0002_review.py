import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField(validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(5),
                ])),
                ("comment", models.TextField(blank=True, max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("deal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="messaging.deal")),
                ("reviewee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews_received", to=settings.AUTH_USER_MODEL)),
                ("reviewer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews_given", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddConstraint(
            model_name="review",
            constraint=models.UniqueConstraint(fields=("deal", "reviewer"), name="unique_review_per_deal_reviewer"),
        ),
    ]
