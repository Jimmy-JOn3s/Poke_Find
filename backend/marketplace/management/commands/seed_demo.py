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

        # Card images from TCGdex (https://tcgdex.dev). Thai-print art uses the JP SV2a assets.
        fixtures = [
            # English print, English listing title
            {
                "product_name": "Charizard ex",
                "set_name": "Obsidian Flames",
                "set_code": "SV03",
                "card_number": "125/197",
                "condition": "NM",
                "card_language": "en",
                "rarity": "ultra",
                "asking_price": Decimal("5200.00"),
                "currency": "THB",
                "description": "English print, sleeved immediately after opening.",
                "image_url": "https://assets.tcgdex.net/en/sv/sv03/125/high.webp",
            },
            {
                "product_name": "Pikachu",
                "set_name": "151",
                "set_code": "SV3.5",
                "card_number": "173/165",
                "condition": "NM",
                "card_language": "en",
                "rarity": "rare",
                "asking_price": Decimal("890.00"),
                "currency": "THB",
                "description": "English Illustration Rare from the 151 set.",
                "image_url": "https://assets.tcgdex.net/en/sv/sv03.5/173/high.webp",
            },
            {
                "product_name": "Gardevoir ex",
                "set_name": "Scarlet & Violet",
                "set_code": "SV01",
                "card_number": "245/198",
                "condition": "NM",
                "card_language": "en",
                "rarity": "ultra",
                "asking_price": Decimal("1450.00"),
                "currency": "THB",
                "description": "English double rare, stored in a binder.",
                "image_url": "https://assets.tcgdex.net/en/sv/sv01/245/high.webp",
            },
            # Thai print, English listing title (seller typed the name in English)
            {
                "product_name": "Pikachu AR",
                "set_name": "Pokemon Card 151",
                "set_code": "SV2A",
                "card_number": "173/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "rare",
                "asking_price": Decimal("680.00"),
                "currency": "THB",
                "description": "Thai print Illustration Rare. Seller listed using the English card name.",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/173/high.webp",
            },
            {
                "product_name": "Mew ex SAR",
                "set_name": "Pokemon Card 151",
                "set_code": "SV2A",
                "card_number": "205/165",
                "condition": "LP",
                "card_language": "th",
                "rarity": "secret",
                "asking_price": Decimal("2100.00"),
                "currency": "THB",
                "description": "Thai print with light corner wear. Listed in English.",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/205/high.webp",
            },
            # Thai print, Thai listing title
            {
                "product_name": "พิคาชู AR",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "173/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "rare",
                "asking_price": Decimal("720.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย สภาพดีมาก ลงขายเป็นชื่อภาษาไทย",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/173/high.webp",
            },
            {
                "product_name": "มิว ex SAR",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "205/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "secret",
                "asking_price": Decimal("2350.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Special Art Rare สภาพเกือบมินต์",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/205/high.webp",
            },
            {
                "product_name": "ลิซาร์ดอน ex",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "006/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "ultra",
                "asking_price": Decimal("890.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Double Rare แพ็คใส่ทันทีหลังเปิด",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/006/high.webp",
            },
            {
                "product_name": "ฮิโตคาเงะ AR",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "168/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "rare",
                "asking_price": Decimal("420.00"),
                "currency": "THB",
                "description": "การ์ด Illustration Rare พิมพ์ไทย ขอบคม ไม่มีรอยขีด",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/168/high.webp",
            },
            {
                "product_name": "คาบิกอน AR",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "181/165",
                "condition": "LP",
                "card_language": "th",
                "rarity": "rare",
                "asking_price": Decimal("1150.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย สภาพเล่นเบา มุมมีรอยเล็กน้อย",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/181/high.webp",
            },
            {
                "product_name": "มิวทู AR",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "183/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "rare",
                "asking_price": Decimal("580.00"),
                "currency": "THB",
                "description": "การ์ด Illustration Rare พิมพ์ไทย เก็บในซองใส",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/183/high.webp",
            },
            {
                "product_name": "มิวทู",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "150/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "rare",
                "asking_price": Decimal("95.00"),
                "currency": "THB",
                "description": "การ์ด Rare พิมพ์ไทย เหมาะสำหรับสะสมเซต 151",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/150/high.webp",
            },
            {
                "product_name": "การูรา ex",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "192/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "ultra",
                "asking_price": Decimal("650.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Ultra Rare สภาพดีมาก",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/192/high.webp",
            },
            {
                "product_name": "คาเม็กซ์ ex SAR",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "202/165",
                "condition": "M",
                "card_language": "th",
                "rarity": "secret",
                "asking_price": Decimal("4800.00"),
                "currency": "THB",
                "description": "การ์ด Special Art Rare พิมพ์ไทย สภาพมินต์ เก็บในคลิป",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/202/high.webp",
            },
            {
                "product_name": "อีวุย",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "133/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "common",
                "asking_price": Decimal("35.00"),
                "currency": "THB",
                "description": "การ์ด Common พิมพ์ไทย ราคาถูก เหมาะเริ่มสะสม",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/133/high.webp",
            },
            # Japanese print, English listing title
            {
                "product_name": "Pikachu AR",
                "set_name": "Pokemon Card 151",
                "set_code": "SV2A",
                "card_number": "173/165",
                "condition": "NM",
                "card_language": "ja",
                "rarity": "rare",
                "asking_price": Decimal("42.00"),
                "currency": "USD",
                "description": "Japanese print, clean edges. Listed in English.",
                "image_url": "https://assets.tcgdex.net/ja/SV/SV2a/173/high.webp",
            },
        ]
        listings = []
        for fixture in fixtures:
            listing, _ = Listing.objects.update_or_create(
                seller=seller,
                product_name=fixture["product_name"],
                card_number=fixture["card_number"],
                card_language=fixture["card_language"],
                defaults={**fixture, "quantity": 1, "status": "active"},
            )
            listings.append(listing)

        keep_ids = [listing.id for listing in listings]
        Listing.objects.filter(seller=seller).exclude(id__in=keep_ids).delete()

        SavedListing.objects.get_or_create(user=buyer, listing=listings[0])
        conversation, _ = Conversation.objects.get_or_create(listing=listings[0], buyer=buyer, seller=seller)
        if not conversation.messages.exists():
            Message.objects.create(conversation=conversation, author=buyer, body="Is this card still available?")
            Message.objects.create(conversation=conversation, author=seller, body="Yes, it is available.")
        Offer.objects.get_or_create(
            conversation=conversation, proposer=buyer, amount=Decimal("4800.00"), currency="THB",
            defaults={"status": "pending"},
        )
        self.stdout.write(self.style.SUCCESS(f"PokeFind demo data is ready ({len(listings)} listings)"))
