def compute_variant_key(
    *,
    card_language: str,
    set_code: str,
    card_number: str,
    condition: str,
) -> str:
    """Stable key for grouping comparable card sales (language, set, number, condition)."""
    return ":".join([
        (card_language or "").strip().lower(),
        (set_code or "").strip().lower(),
        (card_number or "").strip().lower(),
        (condition or "").strip().upper(),
    ])


def variant_key_from_parts(
    card_language: str,
    set_code: str,
    card_number: str,
    condition: str,
) -> str:
    return compute_variant_key(
        card_language=card_language,
        set_code=set_code,
        card_number=card_number,
        condition=condition,
    )