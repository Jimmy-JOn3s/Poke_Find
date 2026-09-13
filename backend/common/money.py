from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")


def convert_money(amount: Decimal, source: str, target: str, usd_to_thb: Decimal) -> Decimal:
    """Convert THB/USD without binary floating-point loss."""
    if source not in {"THB", "USD"} or target not in {"THB", "USD"}:
        raise ValueError("Unsupported currency")
    if usd_to_thb <= 0:
        raise ValueError("Exchange rate must be positive")
    if source == target:
        converted = amount
    elif source == "USD":
        converted = amount * usd_to_thb
    else:
        converted = amount / usd_to_thb
    return converted.quantize(CENT, rounding=ROUND_HALF_UP)

