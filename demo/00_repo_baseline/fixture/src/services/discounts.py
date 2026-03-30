def discount_for_tier(tier: str, subtotal: float) -> float:
    """Return discount amount based on account tier."""
    normalized = tier.lower().strip()
    if normalized == "gold":
        return subtotal * 0.15
    if normalized == "silver":
        return subtotal * 0.05
    return 0.0
