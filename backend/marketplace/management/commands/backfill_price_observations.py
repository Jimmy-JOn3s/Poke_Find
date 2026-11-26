import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from marketplace.market_intel import record_price_observation
from messaging.models import Deal

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Record the price observation for completed deals that are missing one (safe to re-run)"

    def handle(self, *args, **options):
        missing = Deal.objects.filter(status=Deal.Status.COMPLETED, price_observation__isnull=True)
        recorded = failed = 0
        # The primary keys are read up front: writing while iterating the same query is unsafe on some databases.
        for deal_pk in list(missing.values_list("pk", flat=True)):
            try:
                # One transaction per deal, so a deal that still can't be recorded doesn't block the rest.
                with transaction.atomic():
                    if record_price_observation(Deal.objects.get(pk=deal_pk)) is not None:
                        recorded += 1
            except Exception:
                failed += 1
                logger.exception("Could not backfill the price observation for deal %s", deal_pk)
        summary = f"Recorded {recorded} missing price observation(s)."
        if failed:
            raise CommandError(f"{summary} {failed} deal(s) still failed; see the error log.")
        self.stdout.write(self.style.SUCCESS(summary))
