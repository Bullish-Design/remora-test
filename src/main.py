from src.api.orders import create_order
from src.models.order import OrderRequest
from src.utils.money import format_usd


if __name__ == "__main__":
    request = OrderRequest(user_tier="gold", item_prices=[10.0, 20.0, 5.0])
    summary = create_order(request)
    print(
        {
            "subtotal": format_usd(summary.subtotal),
            "discount": format_usd(summary.discount),
            "total": format_usd(summary.total),
        }
    )
