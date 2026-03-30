def choose_warehouse(postal_code: str) -> str:
    """Very simple warehouse allocation logic for demo purposes."""
    if postal_code.startswith(("0", "1", "2", "3")):
        return "east-coast"
    if postal_code.startswith(("7", "8", "9")):
        return "west-coast"
    return "central"
