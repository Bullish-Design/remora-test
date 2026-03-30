from src.api.orders import create_order
from src.models.order import OrderRequest
from src.utils.money import format_usd


def test_demo_order_smoke() -> None:
    summary = create_order(OrderRequest(user_tier="gold", item_prices=[10.0, 20.0], tax_rate=0.1))
    assert summary.subtotal == 30.0
    assert round(summary.discount, 2) == 4.5
    assert summary.total == 28.05
    assert format_usd(summary.total) == "$28.05"
