"""Explore Studio engine — shared colour validation.

A single validation helper for ``(r, g, b)`` colour tuples used by
the configuration, entity models, and text drawing.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from typing import Any


def _validate_rgb_color(value: Any) -> tuple[int, int, int]:
    """Validate an ``(r, g, b)`` colour tuple and return it.

    Requirements:
    * Must be a tuple of exactly 3 elements.
    * Each element must be an ``int`` in 0–255 (inclusive).
    * Booleans are rejected (they are a subtype of ``int``).

    Returns the tuple unchanged on success.
    """
    if not isinstance(value, tuple):
        raise TypeError(f"colour must be a tuple, got {type(value).__name__}")
    if len(value) != 3:
        raise ValueError(f"colour must have 3 channels, got {len(value)}")
    for i, ch in enumerate(value):
        if isinstance(ch, bool) or not isinstance(ch, int):
            raise TypeError(f"colour[{i}] must be int, got {type(ch).__name__}")
        if not (0 <= ch <= 255):
            raise ValueError(f"colour[{i}] must be 0–255, got {ch}")
    return (value[0], value[1], value[2])  # type: ignore[return-value]
