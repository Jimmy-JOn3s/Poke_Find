from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from marketplace.models import Listing, SavedListing
from messaging.models import Conversation, Message, Offer


User = get_user_model()


class Command(BaseCommand):
    help = "Create deterministic PokeFind demo accounts and marketplace data"

    def handle(self, *args, **options):
        seller, _ = User.objects.update_or_create(
            username="demo-seller",
            defaults={
                "email": "seller@pokefind.local", "display_name": "PokeFind BKK",
                "role": "business", "preferred_language": "th", "preferred_currency": "THB",
                "is_verified_seller": True, "location": "Bangkok",
            },
        )
        seller.set_password("PokeFind123!")
        seller.save()
        buyer, _ = User.objects.update_or_create(
            username="demo-buyer",
            defaults={
                "email": "buyer@pokefind.local", "display_name": "Mew Collector",
                "role": "personal", "preferred_language": "en", "preferred_currency": "USD",
                "location": "Chiang Mai",
            },
        )
        buyer.set_password("PokeFind123!")
        buyer.save()

        fixtures = [
            {"product_name": "Charizard ex", "set_name": "Obsidian Flames", "set_code": "SV03", "card_number": "125/108", "condition": "NM", "card_language": "en", "rarity": "ultra", "asking_price": Decimal("5200.00"), "currency": "THB", "description": "Sleeved immediately after opening."},
            {"product_name": "Pikachu AR", "set_name": "Pokemon Card 151", "set_code": "SV2A", "card_number": "173/165", "condition": "NM", "card_language": "ja", "rarity": "rare", "asking_price": Decimal("42.00"), "currency": "USD", "description": "Japanese print, clean edges."},
            {"product_name": "Mew ex SAR", "set_name": "Pokemon Card 151", "set_code": "SV2A", "card_number": "205/165", "condition": "LP", "card_language": "th", "rarity": "secret", "asking_price": Decimal("2100.00"), "currency": "THB", "description": "Thai print with light corner wear."},
        ]
        listings = []
        for fixture in fixtures:
            listing, _ = Listing.objects.update_or_create(
                seller=seller, product_name=fixture["product_name"], card_number=fixture["card_number"],
                defaults={**fixture, "quantity": 1, "status": "active"},
            )
            listings.append(listing)

        SavedListing.objects.get_or_create(user=buyer, listing=listings[0])
        conversation, _ = Conversation.objects.get_or_create(listing=listings[0], buyer=buyer, seller=seller)
        if not conversation.messages.exists():
            Message.objects.create(conversation=conversation, author=buyer, body="Is this card still available?")
            Message.objects.create(conversation=conversation, author=seller, body="Yes, it is available.")
        Offer.objects.get_or_create(
            conversation=conversation, proposer=buyer, amount=Decimal("4800.00"), currency="THB",
            defaults={"status": "pending"},
        )
        self.stdout.write(self.style.SUCCESS("PokeFind demo data is ready"))

