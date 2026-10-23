from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_user_is_email_verified"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="seller_verification_type",
            field=models.CharField(
                blank=True,
                choices=[("id", "National ID"), ("passport", "Passport")],
                default="",
                max_length=16,
            ),
        ),
    ]
