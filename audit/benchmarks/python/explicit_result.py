def parse_flag(text: str) -> bool:
    """Parse yes into True or raise ValueError."""
    if text == "yes":
        return True
    raise ValueError("expected yes")
