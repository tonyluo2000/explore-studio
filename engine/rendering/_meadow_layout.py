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

import math
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
    "LANDER",
    "LANDER_BEACON",
    "MOON",
    "PAD_CHEVRONS",
    "PAD_LIGHTS",
    "POND",
    "POND_GLINTS",
    "SHOOTING_STAR_PATHS",
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

#: The painted landing pad's rim lights (12, clockwise from the east) and the
#: three teal chevrons that point from the pad toward the trail.
PAD_LIGHTS: Final = tuple(
    (
        START_CENTER[0] + 104.0 * math.cos(index * math.tau / 12),
        START_CENTER[1] + 2.0 + 36.0 * math.sin(index * math.tau / 12),
    )
    for index in range(12)
)
PAD_CHEVRONS: Final = tuple((x, START_CENTER[1] + 1.0) for x in (435.0, 417.0, 399.0))

#: The parked lander's base (x, ground y) and the red beacon on its antenna.
LANDER: Final = (676.0, 372.0)
LANDER_BEACON: Final = (LANDER[0] - 6.0, LANDER[1] - 85.0)

#: Glints on the pond's painted moon reflection.
POND_GLINTS: Final = ((97.0, 288.0), (103.0, 294.0), (100.0, 300.0), (99.0, 306.0), (103.0, 312.0))

#: Shooting-star paths (x0, y0, dx, dy, length) in the open sky between the
#: HUD rows and the moon, so a streak never crosses mission text.
SHOOTING_STAR_PATHS: Final = (
    (640.0, 16.0, -0.94, 0.34, 150.0),
    (840.0, 20.0, -0.92, 0.38, 110.0),
    (520.0, 12.0, -0.96, 0.28, 140.0),
)


def crystal_tip(cluster: tuple[float, float, float, float]) -> tuple[float, float]:
    """The tallest painted tip of one crystal cluster."""
    x, y, scale, _ = cluster
    return (x + 1.0 * scale, y - 34.0 * scale)
