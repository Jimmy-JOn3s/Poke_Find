from django.contrib import admin

from .models import Listing, SavedListing


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("product_name", "seller", "asking_price", "currency", "status", "created_at")
    list_filter = ("status", "currency", "card_language", "condition", "rarity")
    search_fields = ("product_name", "set_name", "set_code", "card_number", "seller__username")


admin.site.register(SavedListing)
