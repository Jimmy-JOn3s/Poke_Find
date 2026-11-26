from django.core.management.base import BaseCommand, CommandError

from messaging.services import expire_stale_deals


class Command(BaseCommand):
    help = (
        "Settle overdue open deals: complete buyer-confirmed ones, cancel unconfirmed ones, "
        "and leave seller-only ones reserved for staff review"
    )

    def handle(self, *args, **options):
        counts = expire_stale_deals()
        summary = (
            f"Completed {counts['completed']}, cancelled {counts['cancelled']}; "
            f"{counts['awaiting_buyer']} still waiting on the buyer (left reserved for review)."
        )
        if counts["failed"]:
            # A non-zero exit lets cron or a scheduler alert on it; the details are in the error log.
            raise CommandError(f"{summary} {counts['failed']} deal(s) could not be settled; see the error log.")
        self.stdout.write(self.style.SUCCESS(summary))
