def risk_score(amount: float, user_tier: str) -> float:
    base = amount / 100.0
    if user_tier.lower().strip() == "gold":
        return max(0.0, base - 0.2)
    return min(1.0, base)
