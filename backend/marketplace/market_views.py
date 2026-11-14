from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from marketplace.market_intel import variant_market_summary
from marketplace.models import Listing
from marketplace.variant_key import variant_key_from_parts


class VariantMarketView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        variant_key = (request.query_params.get("variant_key") or "").strip()
        if not variant_key:
            language = (request.query_params.get("card_language") or "").strip().lower()
            set_code = (request.query_params.get("set_code") or "").strip()
            card_number = (request.query_params.get("card_number") or "").strip()
            condition = (request.query_params.get("condition") or "").strip().upper()
            missing = [
                name for name, value in (
                    ("card_language", language),
                    ("set_code", set_code),
                    ("card_number", card_number),
                    ("condition", condition),
                ) if not value
            ]
            if missing:
                return Response(
                    {
                        "detail": "Provide variant_key or card_language, set_code, card_number, and condition.",
                        "missing": missing,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if language not in {choice[0] for choice in Listing.CardLanguage.choices}:
                return Response({"detail": "Invalid card_language."}, status=status.HTTP_400_BAD_REQUEST)
            if condition not in {choice[0] for choice in Listing.Condition.choices}:
                return Response({"detail": "Invalid condition."}, status=status.HTTP_400_BAD_REQUEST)
            variant_key = variant_key_from_parts(language, set_code, card_number, condition)

        currency = (request.query_params.get("currency") or "").strip().upper() or None
        if currency and currency not in {choice[0] for choice in Listing.Currency.choices}:
            return Response({"detail": "Invalid currency."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(variant_market_summary(variant_key=variant_key, currency=currency))