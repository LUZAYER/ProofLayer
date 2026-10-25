"""Wilson score 95% confidence interval computation for binomial proportions."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class ConfidenceInterval:
    rate: float
    ci_lower: float
    ci_upper: float
    successes: int
    total: int


def wilson_score_interval(successes: int, total: int, z: float = 1.95996) -> ConfidenceInterval:
    """Calculate the Wilson score confidence interval (default 95% confidence)."""
    if total == 0:
        return ConfidenceInterval(rate=0.0, ci_lower=0.0, ci_upper=0.0, successes=0, total=0)

    p = successes / total
    z2 = z * z
    denom = 1 + z2 / total
    center = (p + z2 / (2 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1 - p) / total) + (z2 / (4 * total * total)))

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    return ConfidenceInterval(
        rate=round(p, 4),
        ci_lower=round(lower, 4),
        ci_upper=round(upper, 4),
        successes=successes,
        total=total,
    )
