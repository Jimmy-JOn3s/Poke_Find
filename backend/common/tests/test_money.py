from decimal import Decimal
from django.test import SimpleTestCase
from common.money import convert_money


class MoneyTests(SimpleTestCase):
    def test_converts_thb_to_usd_with_decimal_rounding(self):
        self.assertEqual(convert_money(Decimal("1000.00"), "THB", "USD", Decimal("35")), Decimal("28.57"))

    def test_converts_usd_to_thb_and_preserves_same_currency(self):
        self.assertEqual(convert_money(Decimal("10.25"), "USD", "THB", Decimal("35")), Decimal("358.75"))
        self.assertEqual(convert_money(Decimal("10.25"), "USD", "USD", Decimal("35")), Decimal("10.25"))

