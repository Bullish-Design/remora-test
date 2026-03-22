def compute_total(item_prices: list[float]) -> float:
    subtotal = sum(item_prices)
    # Guard against tiny floating artifacts
    return round(subtotal, 2)
# demo trigger 1774215119
# demo trigger 1774215673
