from django.core.management.base import BaseCommand

from messaging.services import expire_stale_deals


class Command(BaseCommand):
    help = "Cancel accepted deals past the stale threshold and return listings to active"

    def handle(self, *args, **options):
        count = expire_stale_deals()
        self.stdout.write(self.style.SUCCESS(f"Released {count} stale deal(s)."))