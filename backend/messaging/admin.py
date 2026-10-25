from django.contrib import admin

from .models import Conversation, Deal, Message, Offer


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    """Completed-deal records are the raw Thai Market Price data: price, card, condition, date."""

    list_display = (
        "id", "status", "card_name", "card_set", "condition",
        "final_price", "currency", "completed_at",
    )
    list_filter = ("status", "currency", "condition")
    search_fields = ("card_name", "card_set")
    date_hierarchy = "completed_at"
    ordering = ("-completed_at",)
    readonly_fields = ("card_name", "card_set", "condition", "final_price", "currency", "completed_at")


admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Offer)
