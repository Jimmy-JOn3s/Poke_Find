import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("marketplace", "0002_listing_image_url"),
        ("messaging", "0005_align_listing_status_with_deals"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(choices=[
                    ("listing", "Listing"), ("user", "User"), ("message", "Message"),
                ], max_length=16)),
                ("reason", models.CharField(choices=[
                    ("spam", "Spam"),
                    ("scam", "Scam or fraud"),
                    ("fake_listing", "Fake or misleading listing"),
                    ("harassment", "Harassment"),
                    ("inappropriate", "Inappropriate content"),
                    ("other", "Other"),
                ], max_length=32)),
                ("details", models.TextField(blank=True, max_length=2000)),
                ("status", models.CharField(choices=[
                    ("pending", "Pending"),
                    ("reviewing", "Reviewing"),
                    ("resolved", "Resolved"),
                    ("dismissed", "Dismissed"),
                ], db_index=True, default="pending", max_length=16)),
                ("admin_notes", models.TextField(blank=True, max_length=2000)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("listing", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                    related_name="reports", to="marketplace.listing",
                )),
                ("message", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                    related_name="reports", to="messaging.message",
                )),
                ("reported_user", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                    related_name="reports_received", to=settings.AUTH_USER_MODEL,
                )),
                ("reporter", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="reports_filed", to=settings.AUTH_USER_MODEL,
                )),
                ("resolved_by", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="reports_resolved", to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddConstraint(
            model_name="contentreport",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("listing__isnull", False), ("reported_user__isnull", True), ("message__isnull", True),
                ) | models.Q(
                    ("listing__isnull", True), ("reported_user__isnull", False), ("message__isnull", True),
                ) | models.Q(
                    ("listing__isnull", True), ("reported_user__isnull", True), ("message__isnull", False),
                ),
                name="report_exactly_one_target",
            ),
        ),
        migrations.AddConstraint(
            model_name="contentreport",
            constraint=models.UniqueConstraint(
                condition=models.Q(("listing__isnull", False), ("status__in", ("pending", "reviewing"))),
                fields=("reporter", "listing"),
                name="unique_open_listing_report_per_reporter",
            ),
        ),
        migrations.AddConstraint(
            model_name="contentreport",
            constraint=models.UniqueConstraint(
                condition=models.Q(("reported_user__isnull", False), ("status__in", ("pending", "reviewing"))),
                fields=("reporter", "reported_user"),
                name="unique_open_user_report_per_reporter",
            ),
        ),
        migrations.AddConstraint(
            model_name="contentreport",
            constraint=models.UniqueConstraint(
                condition=models.Q(("message__isnull", False), ("status__in", ("pending", "reviewing"))),
                fields=("reporter", "message"),
                name="unique_open_message_report_per_reporter",
            ),
        ),
    ]
