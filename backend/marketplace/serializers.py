from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import Listing


class ListingSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = (
            "id", "seller", "product_name", "set_name", "set_code", "card_number",
            "condition", "card_language", "rarity", "asking_price", "currency",
            "quantity", "description", "photo", "status", "is_saved", "created_at", "updated_at",
        )
        read_only_fields = ("id", "seller", "is_saved", "created_at", "updated_at")

    def get_is_saved(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.saved_by.filter(user=request.user).exists())

