from django.db import migrations, models
from django.db.models.functions import Lower


def lowercase_emails(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    # Find every case-variant duplicate before changing anything: lower-casing one row of a pair
    # would hit the existing case-sensitive unique index and fail with a raw IntegrityError.
    ids_by_email = {}
    for user_id, email in User.objects.values_list("id", "email"):
        ids_by_email.setdefault(email.strip().lower(), []).append(user_id)
    duplicates = {email: ids for email, ids in ids_by_email.items() if len(ids) > 1}
    if duplicates:
        details = "; ".join(f"{email}: users {ids}" for email, ids in sorted(duplicates.items()))
        raise RuntimeError(
            "Some accounts share an email in different letter case. Merge or change them in the admin, "
            f"then run migrate again. {details}"
        )
    for user_id, email in User.objects.values_list("id", "email"):
        normalized = email.strip().lower()
        if email != normalized:
            User.objects.filter(pk=user_id).update(email=normalized)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.RunPython(lowercase_emails, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(Lower("email"), name="unique_user_email_ci"),
        ),
    ]
