import os
import statistics
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from marketplace.models import Listing
from messaging.models import Deal

from .seed_demo import Command as SeedDemoCommand

User = get_user_model()

MARKER_SET_CODE = "MI-DEMO"
SAMPLE_CARD = {
    "product_name": "Pikachu ex",
    "set_name": "SV2a 151",
    "set_code": MARKER_SET_CODE,
    "card_number": "025/165",
    "condition": "NM",
    "card_language": "th",
    "rarity": "rare",
    "currency": "THB",
    "description": "Market-intelligence demo: many completed sales of the same card.",
    "image_url": "https://assets.tcgdex.net/th/SV/SV2a/025/high.webp",
}
SALE_COUNT = 25
# Spread final prices around ~2,000 THB so averages are easy to eyeball in the admin panel.
PRICE_PATTERN = [
    Decimal("1780.00"), Decimal("1825.00"), Decimal("1890.00"), Decimal("1910.00"), Decimal("1935.00"),
    Decimal("1950.00"), Decimal("1960.00"), Decimal("1975.00"), Decimal("1980.00"), Decimal("1990.00"),
    Decimal("2000.00"), Decimal("2010.00"), Decimal("2025.00"), Decimal("2040.00"), Decimal("2050.00"),
    Decimal("2065.00"), Decimal("2080.00"), Decimal("2095.00"), Decimal("2110.00"), Decimal("2130.00"),
    Decimal("2150.00"), Decimal("2180.00"), Decimal("2205.00"), Decimal("2230.00"), Decimal("2260.00"),
]


class Command(BaseCommand):
    help = "Seed ~25 completed sales of one card for admin market-intelligence demos (DEBUG only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=SALE_COUNT,
            help=f"Number of completed sales to create (default {SALE_COUNT})",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "seed_market_intelligence only runs with DJANGO_DEBUG=1.",
            )
        password = os.getenv("DEMO_SEED_PASSWORD", "")
        if not password:
            raise CommandError("Set DEMO_SEED_PASSWORD (same as seed_demo).")

        count = max(1, options["count"])
        seller, _ = User.objects.get_or_create(
            username="mi-demo-seller",
            defaults={
                "email": "mi-seller@pokefind.local",
                "display_name": "MI Demo Seller",
                "role": "business",
                "preferred_currency": "THB",
                "is_email_verified": True,
                "is_verified_seller": True,
                "seller_verification_type": "id",
            },
        )
        seller.set_password(password)
        seller.save()

        Listing.objects.filter(set_code=MARKER_SET_CODE).delete()

        buyers = []
        buyer_slots = max(5, min(count, 12))
        for index in range(buyer_slots):
            username = f"mi-demo-buyer-{index + 1:02d}"
            buyer, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"mi-buyer-{index + 1}@pokefind.local",
                    "display_name": f"MI Buyer {index + 1}",
                    "role": "personal",
                    "preferred_currency": "THB",
                },
            )
            buyer.set_password(password)
            buyer.save()
            buyers.append(buyer)

        seeder = SeedDemoCommand()
        prices = (PRICE_PATTERN * ((count // len(PRICE_PATTERN)) + 1))[:count]
        now = timezone.now()

        for index in range(count):
            final_price = prices[index]
            buyer = buyers[index % len(buyers)]
            listing = Listing.objects.create(
                seller=seller,
                asking_price=final_price,
                quantity=1,
                status=Listing.Status.SOLD,
                **SAMPLE_CARD,
            )
            completed_at = now - timedelta(days=index * 2, hours=index % 8)
            deal = seeder._seed_completed_trade(listing, buyer, final_price, SAMPLE_CARD["currency"])
            Deal.objects.filter(pk=deal.pk).update(completed_at=completed_at)

        completed = Deal.objects.filter(
            card_name=SAMPLE_CARD["product_name"],
            card_set=SAMPLE_CARD["set_name"],
            currency=SAMPLE_CARD["currency"],
            status=Deal.Status.COMPLETED,
        )
        sample_prices = [float(row) for row in completed.values_list("final_price", flat=True)]
        avg = statistics.mean(sample_prices) if sample_prices else 0

        self.stdout.write(self.style.SUCCESS(
            f"Market intelligence demo ready: {count} completed sales of "
            f"{SAMPLE_CARD['product_name']} ({SAMPLE_CARD['set_name']}), "
            f"sample average ≈ {avg:.2f} {SAMPLE_CARD['currency']}. "
            f"Open the admin dashboard → Market intelligence.",
        ))