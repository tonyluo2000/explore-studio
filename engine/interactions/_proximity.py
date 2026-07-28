"""Explore Studio engine — proximity detection.

Provides a pure helper that determines whether two rectangles are near
each other based on center-to-center squared Euclidean distance.

Ownership: Engine team.  Internal module — not part of the Student API.
"""

from __future__ import annotations

import math
from typing import Any


def _validate_interaction_range(value: Any, name: str = "interaction_range") -> float:
    """Validate an interaction range value.

    Returns the value as a ``float``.  Rejects:

    * Booleans (treated as non-numeric);
    * non-numeric types (strings, ``None``, etc.);
    * zero and negative values;
    * ``NaN``;
    * positive infinity;
    * negative infinity.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be int or float, got {type(value).__name__}")
    f = float(value)
    if math.isnan(f):
        raise ValueError(f"{name} must be finite, got NaN")
    if math.isinf(f):
        raise ValueError(f"{name} must be finite, got {'inf' if f > 0 else '-inf'}")
    if f <= 0:
        raise ValueError(f"{name} must be positive, got {f}")
    return f


def _center_distance_sq(
    ax: float,
    ay: float,
    aw: float,
    ah: float,
    bx: float,
    by: float,
    bw: float,
    bh: float,
) -> float:
    """Return the squared Euclidean distance between two rectangle centers.

    Positions *(ax, ay)* and *(bx, by)* are the top-left corners;
    *(aw, ah)* and *(bw, bh)* are the dimensions.

    No integer truncation — all inputs are treated as floats so that
    fractional character coordinates are preserved.
    """
    acx = float(ax) + float(aw) / 2.0
    acy = float(ay) + float(ah) / 2.0
    bcx = float(bx) + float(bw) / 2.0
    bcy = float(by) + float(bh) / 2.0
    dx = acx - bcx
    dy = acy - bcy
    return dx * dx + dy * dy


# ------------------------------------------------------------------
# Public helper
# ------------------------------------------------------------------


def is_near(
    ax: float,
    ay: float,
    aw: float,
    ah: float,
    bx: float,
    by: float,
    bw: float,
    bh: float,
    range_sq: float,
) -> bool:
    """Return ``True`` when two rectangles are within *range_sq*.

    Uses center-to-center **squared** Euclidean distance with an
    **inclusive** boundary::

        distance² ≤ range_sq   →  True
        distance² > range_sq    →  False

    Args:
        ax: Left-edge x of rectangle A.
        ay: Top-edge y of rectangle A.
        aw: Width of rectangle A.
        ah: Height of rectangle A.
        bx: Left-edge x of rectangle B.
        by: Top-edge y of rectangle B.
        bw: Width of rectangle B.
        bh: Height of rectangle B.
        range_sq: Squared interaction range (must be positive, finite).
    """
    return _center_distance_sq(ax, ay, aw, ah, bx, by, bw, bh) <= range_sq
