from src.utils.money import format_usd


def test_format_usd_positive() -> None:
    assert format_usd(12.345) == "$12.35"


def test_format_usd_negative() -> None:
    assert format_usd(-1.2) == "$-1.20"
