from dataclasses import dataclass


@dataclass
class Counter:
    value: int


def bump(counter: Counter) -> None:
    """Increment a counter in place."""
    counter.value += 1
