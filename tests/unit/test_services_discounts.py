from src.services.discounts import discount_for_tier


def test_gold_discount() -> None:
    assert discount_for_tier("gold", 200.0) == 30.0


def test_silver_discount_with_whitespace_and_case() -> None:
    assert discount_for_tier("  SILVER ", 100.0) == 5.0


def test_unknown_tier_discount_is_zero() -> None:
    assert discount_for_tier("bronze", 100.0) == 0.0
