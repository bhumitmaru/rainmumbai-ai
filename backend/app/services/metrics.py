"""Pure (numpy-free) evaluation metrics shared across the app."""

from __future__ import annotations

import math

DIRECTION_LABELS = ("Increase", "No Change", "Decrease")


def mae(pairs: list[tuple[float, float]]) -> float | None:
    if not pairs:
        return None
    return round(sum(abs(p - a) for p, a in pairs) / len(pairs), 4)


def rmse(pairs: list[tuple[float, float]]) -> float | None:
    if not pairs:
        return None
    return round(math.sqrt(sum((p - a) ** 2 for p, a in pairs) / len(pairs)), 4)


def direction_accuracy(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    return round(sum(1 for p, a in pairs if p == a) / len(pairs), 4)


def direction_f1(pairs: list[tuple[str, str]]) -> float | None:
    """Macro-F1 across Increase / No Change / Decrease."""
    if not pairs:
        return None
    f1s: list[float] = []
    for label in DIRECTION_LABELS:
        tp = sum(1 for p, a in pairs if p == label and a == label)
        fp = sum(1 for p, a in pairs if p == label and a != label)
        fn = sum(1 for p, a in pairs if p != label and a == label)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        f1s.append(f1)
    return round(sum(f1s) / len(DIRECTION_LABELS), 4)
