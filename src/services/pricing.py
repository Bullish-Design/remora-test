def compute_total(item_prices: list[float]) -> float:
    """Calculate subtotal from item prices."""
    return round(sum(item_prices), 2)
