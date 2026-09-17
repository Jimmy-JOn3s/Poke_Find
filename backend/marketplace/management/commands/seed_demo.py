from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from marketplace.models import Listing, SavedListing
from messaging.models import Conversation, Deal, Message, Offer, Review


User = get_user_model()

# TCGdex Thai scans for SV2a currently cover cards 001–020 only.
_SV2A_THAI_IMAGE_IDS = frozenset(f"{index:03d}" for index in range(1, 21))


def _sv2a_image(local_id: str, *, thai_print: bool) -> str:
    """Return a TCGdex high-res webp URL for SV2a cards."""
    card_id = local_id.split("/")[0]
    if thai_print:
        if card_id not in _SV2A_THAI_IMAGE_IDS:
            raise ValueError(f"No Thai TCGdex scan for SV2a card {card_id}")
        return f"https://assets.tcgdex.net/th/SV/SV2a/{card_id}/high.webp"
    return f"https://assets.tcgdex.net/ja/SV/SV2a/{card_id}/high.webp"


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

        # Card images from TCGdex (https://tcgdex.dev). Thai-print SV2a cards prefer th scans when available.
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
            # Thai print, Thai listing title (TCGdex th scans exist for SV2a 001–020 only)
            {
                "product_name": "ฟุชิกิดาเนะ",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "001/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "common",
                "asking_price": Decimal("28.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย สภาพดีมาก เก็บในซองใส",
                "image_url": _sv2a_image("001", thai_print=True),
            },
            {
                "product_name": "ฟุชิกิโซ",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "002/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "uncommon",
                "asking_price": Decimal("35.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Uncommon ขอบคม",
                "image_url": _sv2a_image("002", thai_print=True),
            },
            {
                "product_name": "ฟุชิกิบานะex",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "003/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "ultra",
                "asking_price": Decimal("320.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Double Rare ขอบคม",
                "image_url": _sv2a_image("003", thai_print=True),
            },
            {
                "product_name": "ฮิโตคาเงะ",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "004/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "common",
                "asking_price": Decimal("22.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Common สภาพดี",
                "image_url": _sv2a_image("004", thai_print=True),
            },
            {
                "product_name": "ลิซาร์โดะ",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "005/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "uncommon",
                "asking_price": Decimal("45.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Uncommon เก็บในซองใส",
                "image_url": _sv2a_image("005", thai_print=True),
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
                "image_url": _sv2a_image("006", thai_print=True),
            },
            {
                "product_name": "เซนิกาเมะ",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "007/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "common",
                "asking_price": Decimal("20.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Common ราคาถูก",
                "image_url": _sv2a_image("007", thai_print=True),
            },
            {
                "product_name": "คาเม็กซ์ex",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "009/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "ultra",
                "asking_price": Decimal("780.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Double Rare สภาพดีมาก",
                "image_url": _sv2a_image("009", thai_print=True),
            },
            {
                "product_name": "บัตเตอร์ฟรี",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "012/165",
                "condition": "LP",
                "card_language": "th",
                "rarity": "uncommon",
                "asking_price": Decimal("40.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Uncommon สภาพเล่นเบา",
                "image_url": _sv2a_image("012", thai_print=True),
            },
            {
                "product_name": "สเปียร์",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "015/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "rare",
                "asking_price": Decimal("65.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Rare ขอบคม",
                "image_url": _sv2a_image("015", thai_print=True),
            },
            {
                "product_name": "ป็อปโปะ",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "016/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "common",
                "asking_price": Decimal("18.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Common เหมาะเริ่มสะสม",
                "image_url": _sv2a_image("016", thai_print=True),
            },
            {
                "product_name": "พีเจียต",
                "set_name": "โปเกมอนการ์ด 151",
                "set_code": "SV2A",
                "card_number": "018/165",
                "condition": "NM",
                "card_language": "th",
                "rarity": "rare",
                "asking_price": Decimal("58.00"),
                "currency": "THB",
                "description": "การ์ดพิมพ์ไทย Rare เก็บในซองใส",
                "image_url": _sv2a_image("018", thai_print=True),
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
                "image_url": _sv2a_image("173", thai_print=False),
            },
            {
                "product_name": "Mew ex SAR",
                "set_name": "Pokemon Card 151",
                "set_code": "SV2A",
                "card_number": "205/165",
                "condition": "NM",
                "card_language": "ja",
                "rarity": "secret",
                "asking_price": Decimal("185.00"),
                "currency": "USD",
                "description": "Japanese Special Art Rare, pulled and sleeved immediately.",
                "image_url": _sv2a_image("205", thai_print=False),
            },
            {
                "product_name": "Charizard ex",
                "set_name": "Pokemon Card 151",
                "set_code": "SV2A",
                "card_number": "006/165",
                "condition": "NM",
                "card_language": "ja",
                "rarity": "ultra",
                "asking_price": Decimal("12.00"),
                "currency": "USD",
                "description": "Japanese double rare from the 151 set.",
                "image_url": _sv2a_image("006", thai_print=False),
            },
            {
                "product_name": "Blastoise ex SAR",
                "set_name": "Pokemon Card 151",
                "set_code": "SV2A",
                "card_number": "202/165",
                "condition": "LP",
                "card_language": "ja",
                "rarity": "secret",
                "asking_price": Decimal("95.00"),
                "currency": "USD",
                "description": "Japanese print with light corner wear.",
                "image_url": _sv2a_image("202", thai_print=False),
            },
            {
                "product_name": "Mewtwo AR",
                "set_name": "Pokemon Card 151",
                "set_code": "SV2A",
                "card_number": "183/165",
                "condition": "NM",
                "card_language": "ja",
                "rarity": "rare",
                "asking_price": Decimal("28.00"),
                "currency": "USD",
                "description": "Japanese Illustration Rare, stored in a binder.",
                "image_url": _sv2a_image("183", thai_print=False),
            },
            {
                "product_name": "Snorlax AR",
                "set_name": "Pokemon Card 151",
                "set_code": "SV2A",
                "card_number": "181/165",
                "condition": "NM",
                "card_language": "ja",
                "rarity": "rare",
                "asking_price": Decimal("55.00"),
                "currency": "USD",
                "description": "Japanese Illustration Rare Kabigon art. Listed in English.",
                "image_url": _sv2a_image("181", thai_print=False),
            },
            {
                "product_name": "Zapdos ex",
                "set_name": "Pokemon Card 151",
                "set_code": "SV2A",
                "card_number": "194/165",
                "condition": "NM",
                "card_language": "ja",
                "rarity": "ultra",
                "asking_price": Decimal("38.00"),
                "currency": "USD",
                "description": "Japanese ultra rare from the 151 set.",
                "image_url": _sv2a_image("194", thai_print=False),
            },
            {
                "product_name": "Venusaur ex",
                "set_name": "Pokemon Card 151",
                "set_code": "SV2A",
                "card_number": "198/165",
                "condition": "M",
                "card_language": "ja",
                "rarity": "ultra",
                "asking_price": Decimal("22.00"),
                "currency": "USD",
                "description": "Japanese ultra rare, mint condition.",
                "image_url": _sv2a_image("198", thai_print=False),
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

        trader_one, _ = User.objects.update_or_create(
            username="demo-trader1",
            defaults={
                "email": "trader1@pokefind.local", "display_name": "Card Hunter TH",
                "role": "personal", "preferred_language": "th", "preferred_currency": "THB",
                "location": "Bangkok",
            },
        )
        trader_one.set_password("PokeFind123!")
        trader_one.save()
        trader_two, _ = User.objects.update_or_create(
            username="demo-trader2",
            defaults={
                "email": "trader2@pokefind.local", "display_name": "TCG Explorer",
                "role": "personal", "preferred_language": "en", "preferred_currency": "USD",
                "location": "Phuket",
            },
        )
        trader_two.set_password("PokeFind123!")
        trader_two.save()

        review_count = self._seed_reviews(seller, buyer, trader_one, trader_two, listings)
        self.stdout.write(self.style.SUCCESS(
            f"PokeFind demo data is ready ({len(listings)} listings, {review_count} reviews)",
        ))

    def _seed_completed_trade(self, listing, trade_buyer, final_price, currency):
        listing.status = Listing.Status.SOLD
        listing.save(update_fields=("status",))
        conversation, _ = Conversation.objects.get_or_create(
            listing=listing, buyer=trade_buyer, seller=listing.seller,
        )
        offer, _ = Offer.objects.update_or_create(
            conversation=conversation,
            proposer=trade_buyer,
            amount=final_price,
            currency=currency,
            defaults={"status": Offer.Status.ACCEPTED},
        )
        if offer.status != Offer.Status.ACCEPTED:
            offer.status = Offer.Status.ACCEPTED
            offer.save(update_fields=("status", "updated_at"))
        deal, _ = Deal.objects.update_or_create(
            conversation=conversation,
            defaults={
                "accepted_offer": offer,
                "final_price": final_price,
                "currency": currency,
                "status": Deal.Status.COMPLETED,
                "buyer_confirmed": True,
                "seller_confirmed": True,
                "completed_at": timezone.now(),
            },
        )
        if deal.status != Deal.Status.COMPLETED:
            deal.status = Deal.Status.COMPLETED
            deal.buyer_confirmed = True
            deal.seller_confirmed = True
            deal.completed_at = timezone.now()
            deal.save(update_fields=("status", "buyer_confirmed", "seller_confirmed", "completed_at"))
        return deal

    def _seed_review(self, deal, reviewer, reviewee, rating, comment):
        Review.objects.update_or_create(
            deal=deal,
            reviewer=reviewer,
            defaults={"reviewee": reviewee, "rating": rating, "comment": comment},
        )

    def _seed_reviews(self, seller, buyer, trader_one, trader_two, listings):
        trades = [
            {
                "listing": listings[1],
                "buyer": trader_one,
                "final_price": Decimal("850.00"),
                "currency": "THB",
                "reviews": [
                    (trader_one, seller, 5, "ส่งเร็วมาก การ์ดตรงตามที่โฆษณา แนะนำร้านนี้เลย"),
                    (seller, trader_one, 5, "ลูกค้าดี โอนเงินตรงเวลา ขอบคุณครับ"),
                ],
            },
            {
                "listing": listings[2],
                "buyer": trader_two,
                "final_price": Decimal("1400.00"),
                "currency": "THB",
                "reviews": [
                    (trader_two, seller, 4, "Smooth transaction. Card arrived well protected."),
                    (seller, trader_two, 5, "Great buyer, easy to deal with."),
                ],
            },
            {
                "listing": listings[3],
                "buyer": buyer,
                "final_price": Decimal("26.00"),
                "currency": "THB",
                "reviews": [
                    (buyer, seller, 5, "Perfect for my Thai collection. Fast meetup in Bangkok."),
                    (seller, buyer, 4, "Pleasant buyer, would trade again."),
                ],
            },
            {
                "listing": listings[14],
                "buyer": trader_two,
                "final_price": Decimal("40.00"),
                "currency": "USD",
                "reviews": [
                    (trader_two, seller, 5, "Japanese Pikachu AR was mint. Shipped internationally without issues."),
                ],
            },
            {
                "listing": listings[15],
                "buyer": trader_one,
                "final_price": Decimal("175.00"),
                "currency": "USD",
                "reviews": [
                    (trader_one, seller, 5, "Mew ex SAR สวยมาก แพ็คดีมาก จะซื้ออีกแน่นอน"),
                ],
            },
        ]
        review_count = 0
        for trade in trades:
            deal = self._seed_completed_trade(
                trade["listing"], trade["buyer"], trade["final_price"], trade["currency"],
            )
            for reviewer, reviewee, rating, comment in trade["reviews"]:
                self._seed_review(deal, reviewer, reviewee, rating, comment)
                review_count += 1
        return review_count
