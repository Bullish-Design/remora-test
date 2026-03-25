from src.services.tax import apply_tax


def test_apply_tax_default_rate() -> None:
    assert apply_tax(100.0) == 107.0


def test_apply_tax_custom_rate() -> None:
    assert apply_tax(80.0, 0.0825) == 86.6
