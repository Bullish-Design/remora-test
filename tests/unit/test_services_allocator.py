from src.services.fulfillment.allocator import choose_warehouse


def test_choose_warehouse_east_coast() -> None:
    assert choose_warehouse("02139") == "east-coast"


def test_choose_warehouse_west_coast() -> None:
    assert choose_warehouse("94107") == "west-coast"


def test_choose_warehouse_central_default() -> None:
    assert choose_warehouse("60601") == "central"
