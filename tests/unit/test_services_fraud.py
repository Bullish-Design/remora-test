from src.services.fraud import risk_score


def test_gold_risk_score_reduced_with_floor() -> None:
    assert risk_score(10.0, "gold") == 0.0
    assert risk_score(100.0, "gold") == 0.8


def test_non_gold_risk_score_capped_at_one() -> None:
    assert risk_score(30.0, "silver") == 0.3
    assert risk_score(200.0, "silver") == 1.0
