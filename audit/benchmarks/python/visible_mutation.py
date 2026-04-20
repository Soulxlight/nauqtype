from dataclasses import dataclass


@dataclass
class Counter:
    value: int


def bump(counter):
    counter.value += 1

