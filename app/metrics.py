from collections import Counter

COUNTERS = Counter()


def incr(name: str) -> None:
    COUNTERS[name] += 1


def snapshot() -> dict[str, int]:
    return dict(COUNTERS)
