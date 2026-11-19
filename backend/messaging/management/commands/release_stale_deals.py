from django.core.management.base import BaseCommand

from messaging.services import expire_stale_deals


class Command(BaseCommand):
    help = (
        "Settle overdue open deals: complete buyer-confirmed ones, cancel unconfirmed ones, "
        "and leave seller-only ones reserved for staff review"
    )

    def handle(self, *args, **options):
        counts = expire_stale_deals()
        self.stdout.write(self.style.SUCCESS(
            f"Completed {counts['completed']}, cancelled {counts['cancelled']}; "
            f"{counts['awaiting_buyer']} still waiting on the buyer (left reserved for review)."
        ))