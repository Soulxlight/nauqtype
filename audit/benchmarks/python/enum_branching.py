from enum import Enum, auto


class Flag(Enum):
    ENABLED = auto()
    DISABLED = auto()


def score(flag: Flag) -> int:
    """Map a flag to a numeric score."""
    match flag:
        case Flag.ENABLED:
            return 1
        case Flag.DISABLED:
            return 0
