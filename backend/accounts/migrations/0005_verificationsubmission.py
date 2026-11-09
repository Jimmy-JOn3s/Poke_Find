import accounts.verification_models
import accounts.storage
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_user_seller_verification_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="VerificationSubmission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("document_type", models.CharField(choices=[("id", "National ID"), ("passport", "Passport")], max_length=16)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=16)),
                ("id_document", models.ImageField(storage=accounts.storage.private_media_storage, upload_to=accounts.verification_models._verification_upload_path)),
                ("selfie", models.ImageField(blank=True, storage=accounts.storage.private_media_storage, upload_to=accounts.verification_models._verification_upload_path)),
                ("admin_notes", models.TextField(blank=True, max_length=2000)),
                ("rejection_reason", models.TextField(blank=True, max_length=1000)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="verification_reviews", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="verification_submissions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddConstraint(
            model_name="verificationsubmission",
            constraint=models.UniqueConstraint(condition=models.Q(("status", "pending")), fields=("user",), name="one_pending_verification_per_user"),
        ),
    ]
