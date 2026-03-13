from dataclasses import dataclass


@dataclass(frozen=True)
class OrderRequest:
    user_tier: str
    item_prices: list[float]
    tax_rate: float = 0.07


@dataclass(frozen=True)
class OrderSummary:
    subtotal: float
    discount: float
    total: float
