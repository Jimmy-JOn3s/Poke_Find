from django.core.management.base import BaseCommand

from marketplace.market_intel import record_price_observation
from messaging.models import Deal


class Command(BaseCommand):
    help = "Record the price observation for completed deals that are missing one (safe to re-run)"

    def handle(self, *args, **options):
        missing = Deal.objects.filter(status=Deal.Status.COMPLETED, price_observation__isnull=True)
        recorded = sum(1 for deal in missing.iterator() if record_price_observation(deal) is not None)
        self.stdout.write(self.style.SUCCESS(f"Recorded {recorded} missing price observation(s)."))
