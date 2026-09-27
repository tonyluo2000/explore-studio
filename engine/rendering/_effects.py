"""Small capability-aware drawing helpers for cosmetic effects.

The Trail renderer exposes soft lights, soft shadows, rounded panels, and text
measurement. Simple recording or rectangle-only renderers (tests, fallbacks)
may not. Each helper here quietly skips an effect its renderer cannot draw, so
decoration can never turn into a failure or a stray rectangle.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import math

Color = tuple[int, int, int]


def supports(renderer: object, *names: str) -> bool:
    """Return True when *renderer* provides every named drawing method."""
    return all(callable(getattr(renderer, name, None)) for name in names)


def mix(color: Color, target: Color, amount: float) -> Color:
    amount = max(0.0, min(1.0, amount))
    return (
        round(color[0] + (target[0] - color[0]) * amount),
        round(color[1] + (target[1] - color[1]) * amount),
        round(color[2] + (target[2] - color[2]) * amount),
    )


def glow(renderer: object, x: float, y: float, radius: int, color: Color, intensity: float) -> None:
    """Add a soft light when the renderer supports it; otherwise do nothing."""
    if radius > 0 and intensity > 0.02 and supports(renderer, "draw_glow"):
        renderer.draw_glow(round(x), round(y), radius, color, min(1.0, intensity))  # type: ignore[attr-defined]


def soft_shadow(
    renderer: object, x: float, y: float, radius_x: int, radius_y: int, alpha: int = 110
) -> None:
    """Blend a grounded shadow when the renderer supports it."""
    if radius_x > 0 and radius_y > 0 and supports(renderer, "draw_soft_ellipse"):
        renderer.draw_soft_ellipse(  # type: ignore[attr-defined]
            round(x), round(y), radius_x, radius_y, (6, 10, 16), alpha
        )


def sparkle(renderer: object, x: float, y: float, size: float, color: Color) -> None:
    """Draw a four-point star."""
    if size < 1:
        return
    inner = max(1.0, size / 3)
    cx, cy = round(x), round(y)
    renderer.draw_polygon(  # type: ignore[attr-defined]
        (
            (cx, round(cy - size)),
            (round(cx + inner), round(cy - inner)),
            (round(cx + size), cy),
            (round(cx + inner), round(cy + inner)),
            (cx, round(cy + size)),
            (round(cx - inner), round(cy + inner)),
            (round(cx - size), cy),
            (round(cx - inner), round(cy - inner)),
        ),
        color,
    )


def ellipse_ring(
    renderer: object,
    x: float,
    y: float,
    radius_x: float,
    radius_y: float,
    color: Color,
    width: int = 2,
    segments: int = 28,
) -> None:
    """Draw an ellipse outline from line segments."""
    points = [
        (
            round(x + radius_x * math.cos(math.tau * index / segments)),
            round(y + radius_y * math.sin(math.tau * index / segments)),
        )
        for index in range(segments)
    ]
    for start, end in zip(points, points[1:] + points[:1], strict=True):
        renderer.draw_line(start[0], start[1], end[0], end[1], color, width)  # type: ignore[attr-defined]


def ease_out(progress: float) -> float:
    progress = max(0.0, min(1.0, progress))
    return 1 - (1 - progress) ** 3
