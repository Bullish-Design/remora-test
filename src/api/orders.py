from src.models.order import OrderRequest, OrderSummary
from src.services.discounts import discount_for_tier
from src.services.pricing import compute_total
from src.services.tax import apply_tax


def create_order(request: OrderRequest) -> OrderSummary:
    """Create an order summary with tier discount and tax."""
    subtotal = compute_total(request.item_prices)
    discount = discount_for_tier(request.user_tier, subtotal)
    taxed_total = apply_tax(subtotal - discount, request.tax_rate)
    return OrderSummary(
        subtotal=subtotal,
        discount=discount,
        total=round(taxed_total, 2),
    )
