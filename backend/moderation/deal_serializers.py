from rest_framework import serializers

from messaging.models import Deal
from messaging.stale_deals import is_deal_stale, stale_outcome


class AdminOpenDealSerializer(serializers.ModelSerializer):
    listing_id = serializers.IntegerField(source="conversation.listing_id", read_only=True)
    listing_name = serializers.CharField(source="conversation.listing.product_name", read_only=True)
    buyer_name = serializers.CharField(source="conversation.buyer.display_name", read_only=True)
    seller_name = serializers.CharField(source="conversation.seller.display_name", read_only=True)
    is_stale = serializers.SerializerMethodField()
    stale_outcome = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = (
            "id", "listing_id", "listing_name", "final_price", "currency", "status",
            "card_name", "card_set", "buyer_confirmed", "seller_confirmed",
            "first_confirmed_at", "created_at",
            "buyer_name", "seller_name", "is_stale", "stale_outcome",
        )
        read_only_fields = fields

    def get_is_stale(self, obj):
        return is_deal_stale(obj)

    def get_stale_outcome(self, obj):
        return stale_outcome(obj)
