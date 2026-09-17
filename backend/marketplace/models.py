from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Listing(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        RESERVED = "reserved", "Reserved"
        SOLD = "sold", "Sold"
        HIDDEN = "hidden", "Hidden"

    class CardLanguage(models.TextChoices):
        THAI = "th", "Thai"
        ENGLISH = "en", "English"
        JAPANESE = "ja", "Japanese"

    class Condition(models.TextChoices):
        MINT = "M", "Mint"
        NEAR_MINT = "NM", "Near mint"
        LIGHTLY_PLAYED = "LP", "Lightly played"
        MODERATELY_PLAYED = "MP", "Moderately played"
        HEAVILY_PLAYED = "HP", "Heavily played"

    class Rarity(models.TextChoices):
        COMMON = "common", "Common"
        UNCOMMON = "uncommon", "Uncommon"
        RARE = "rare", "Rare"
        ULTRA = "ultra", "Ultra rare"
        SECRET = "secret", "Secret rare"

    class Currency(models.TextChoices):
        THB = "THB", "Thai baht"
        USD = "USD", "US dollar"

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings")
    product_name = models.CharField(max_length=180, db_index=True)
    set_name = models.CharField(max_length=180, blank=True, db_index=True)
    set_code = models.CharField(max_length=40, blank=True, db_index=True)
    card_number = models.CharField(max_length=40, blank=True, db_index=True)
    condition = models.CharField(max_length=2, choices=Condition.choices)
    card_language = models.CharField(max_length=2, choices=CardLanguage.choices)
    rarity = models.CharField(max_length=16, choices=Rarity.choices)
    asking_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=Currency.choices)
    quantity = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, max_length=500)
    photo = models.ImageField(upload_to="listings/", blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.product_name} ({self.currency} {self.asking_price})"


class SavedListing(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_listing_links")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("user", "listing"), name="unique_saved_listing")]

