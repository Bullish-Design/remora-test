from src.api.orders import create_order
from src.models.order import OrderRequest


def test_create_order_applies_discount_tax_and_rounding() -> None:
    summary = create_order(OrderRequest(user_tier="gold", item_prices=[10.0, 20.0, 5.0], tax_rate=0.07))
    assert summary.subtotal == 35.0
    assert summary.discount == 5.25
    assert summary.total == 31.83
