from src.services.pricing import compute_total


def test_compute_total_rounds_floating_point_artifacts() -> None:
    assert compute_total([0.1, 0.2]) == 0.3


def test_compute_total_empty_input() -> None:
    assert compute_total([]) == 0.0


def test_compute_total_regular_values() -> None:
    assert compute_total([10.0, 20.55, 3.1]) == 33.65
