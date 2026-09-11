"""Statistical spending-anomaly detection: Z-score and IQR, both fully
transparent — every flagged value comes with the number that got it
flagged, so "why was this flagged?" always has a concrete answer.

This module says "unusual", never "fraudulent". A statistical outlier is
a fact about a number's position in a distribution; fraud is a claim
about intent and legitimacy that this code has no way to assess. A large
legitimate purchase (a flight, a deposit) will trigger these flags, and
that's correct behavior for an *anomaly* detector — the distinction
matters enough that conflating the two in the UI would actively mislead
a user into treating a false positive as an accusation.
"""

from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass(frozen=True)
class AnomalyFlag:
    index: int
    value: float
    reason: str


def zscore_anomalies(values: list[float], threshold: float = 2.5) -> list[AnomalyFlag]:
    """Flags values more than `threshold` standard deviations from the
    mean. Assumes an approximately normal distribution — spending data is
    often right-skewed (many small transactions, a few large ones), which
    is exactly what IQR below handles better. Z-score is included because
    it's the more commonly known method and works fine for roughly
    symmetric distributions (e.g. a single category's routine spending).
    """
    if len(values) < 2:
        return []
    avg = mean(values)
    std = pstdev(values)
    if std == 0:
        return []

    flags = []
    for i, v in enumerate(values):
        z = (v - avg) / std
        if abs(z) > threshold:
            direction = "above" if z > 0 else "below"
            flags.append(
                AnomalyFlag(
                    index=i,
                    value=v,
                    reason=(
                        f"{v:.2f} is {abs(z):.1f} standard deviations {direction} "
                        f"the average of {avg:.2f}"
                    ),
                )
            )
    return flags


def iqr_anomalies(values: list[float], k: float = 1.5) -> list[AnomalyFlag]:
    """Flags values outside [Q1 - k*IQR, Q3 + k*IQR] — the classic
    "boxplot outlier" rule. More robust than Z-score to skewed
    distributions and to the outliers themselves inflating the mean/std
    used to detect them (Z-score's known weakness: one huge transaction
    drags the mean toward itself, potentially masking other outliers).
    """
    if len(values) < 4:
        return []
    sorted_values = sorted(values)
    n = len(sorted_values)
    q1 = sorted_values[n // 4]
    q3 = sorted_values[(3 * n) // 4]
    iqr = q3 - q1
    if iqr == 0:
        return []

    lower = q1 - k * iqr
    upper = q3 + k * iqr

    flags = []
    for i, v in enumerate(values):
        if v < lower or v > upper:
            flags.append(
                AnomalyFlag(
                    index=i,
                    value=v,
                    reason=(
                        f"{v:.2f} falls outside the typical range "
                        f"({lower:.2f} to {upper:.2f}, based on this category's usual spread)"
                    ),
                )
            )
    return flags
