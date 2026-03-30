def apply_tax(amount: float, tax_rate: float = 0.07) -> float:
    """Apply tax percentage to a monetary amount."""
    return amount * (1.0 + tax_rate)
