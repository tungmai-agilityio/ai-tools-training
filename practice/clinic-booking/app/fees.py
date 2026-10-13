"""Money rules. All amounts are integer cents. Percentages round half up."""


def _percent(amount_cents: int, pct: int) -> int:
    return (amount_cents * pct + 50) // 100


def consultation_fee(base_fee_cents: int, insured: bool, duration_minutes: int) -> int:
    fee = base_fee_cents * (duration_minutes // 30)
    return _percent(fee, 80) if insured else fee


def late_cancellation_fee(fee_cents: int) -> int:
    """50% of the consultation fee."""
    return round(fee_cents * 0.5)


def no_show_fee(fee_cents: int) -> int:
    """100% of the consultation fee."""
    return fee_cents
