"""Shared layout of the illustrated S02 Moon Meadow.

The trusted scenery art (``scripts/build_trusted_art.py``) is painted from
these positions, and the runtime ambience animates the same positions, so a
twinkle lands on a painted star, a glint on a painted crystal, and a flame
flicker on a painted shrine brazier. Everything here is static scenery: no
value is read from, or written to, any entity.

Gameplay landmarks (start pad, Compass clearing, Lantern shrine, and the trail
between them) come from ``_classroom_environment`` so the illustrated meadow
and the procedural fallback always agree.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from typing import Final

from engine.rendering._classroom_environment import (
    _CLEARING_CENTER,
    _SHRINE_CENTER,
    _START_CENTER,
    _TRAIL_SEGMENTS,
)

__all__ = [
    "BRIGHT_STARS",
    "CLEARING_CENTER",
    "CRYSTAL_CLUSTERS",
    "HORIZON",
    "MOON",
    "POND",
    "SHRINE_CENTER",
    "SHRINE_FLAMES",
    "START_CENTER",
    "TRAIL_SEGMENTS",
]

START_CENTER: Final = _START_CENTER
CLEARING_CENTER: Final = _CLEARING_CENTER
SHRINE_CENTER: Final = _SHRINE_CENTER
TRAIL_SEGMENTS: Final = _TRAIL_SEGMENTS

#: Where the meadow meets the distant hills.
HORIZON: Final = 178

#: The big moon, tucked into the top-right corner clear of the HUD rows.
MOON: Final = (926.0, 62.0, 50.0)

#: Painted bright stars (x, y); the runtime twinkles exactly these.
BRIGHT_STARS: Final = (
    (452.0, 28.0),
    (612.0, 14.0),
    (738.0, 36.0),
    (816.0, 122.0),
    (560.0, 128.0),
    (905.0, 142.0),
    (338.0, 146.0),
    (688.0, 150.0),
)

#: Painted crystal clusters (x, ground y, scale, hue); ``hue`` 0 is cyan and
#: 1 is violet. The runtime adds a glint at each cluster's tallest tip.
CRYSTAL_CLUSTERS: Final = (
    (858.0, 436.0, 1.2, 0.0),
    (602.0, 206.0, 0.75, 1.0),
    (36.0, 432.0, 0.95, 1.0),
    (398.0, 212.0, 0.6, 0.0),
    (752.0, 246.0, 0.85, 0.0),
    (318.0, 600.0, 0.8, 1.0),
)

#: Warm crystal braziers (bowl rim x, y) on the ends of the shrine's lintel.
SHRINE_FLAMES: Final = ((84.0, 351.0), (242.0, 351.0))

#: A small moonlit pond (cx, cy, rx, ry) west of the Compass clearing.
POND: Final = (82.0, 300.0, 62.0, 22.0)


def crystal_tip(cluster: tuple[float, float, float, float]) -> tuple[float, float]:
    """The tallest painted tip of one crystal cluster."""
    x, y, scale, _ = cluster
    return (x + 1.0 * scale, y - 34.0 * scale)
