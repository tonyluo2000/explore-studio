"""Original procedural sprites for the four S02 classroom examples.

This is intentionally a narrow identity allow-list, not the future generic
Explorer Package ``asset_id`` pipeline. Unknown identities return ``False`` so
the Trail can retain its rectangle rendering contract.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Protocol

Color = tuple[int, int, int]

_LOGGER = logging.getLogger("explore-studio.rendering.classroom-sprites")

NOVA_QUALIFIED_ID = "nova-character:nova"
PIXEL_QUALIFIED_ID = "pixel-companion:pixel"
MOON_COMPASS_QUALIFIED_ID = "moon-compass:compass"
CRYSTAL_LANTERN_QUALIFIED_ID = "crystal-lantern:lantern"


class _SpriteRenderer(Protocol):
    def draw_rect(self, x: int, y: int, width: int, height: int, color: Color) -> None: ...

    def draw_circle(self, center_x: int, center_y: int, radius: int, color: Color) -> None: ...

    def draw_line(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        color: Color,
        width: int = 1,
    ) -> None: ...

    def draw_polygon(self, points: tuple[tuple[int, int], ...], color: Color) -> None: ...


SpriteDrawer = Callable[[_SpriteRenderer, int, int, int, int, Color], None]


def _mix(color: Color, target: Color, amount: float) -> Color:
    return tuple(
        round(channel + (target_channel - channel) * amount)
        for channel, target_channel in zip(color, target, strict=True)
    )  # type: ignore[return-value]


def _point(
    x: int,
    y: int,
    width: int,
    height: int,
    x_part: int,
    y_part: int,
) -> tuple[int, int]:
    return x + width * x_part // 100, y + height * y_part // 100


def _stroke(width: int, height: int) -> int:
    return max(1, min(width, height) // 16)


def _draw_nova(
    renderer: _SpriteRenderer,
    x: int,
    y: int,
    width: int,
    height: int,
    accent: Color,
) -> None:
    """Draw a helmeted explorer with a backpack and forward chest marker."""
    outline = _mix(accent, (24, 28, 42), 0.72)
    highlight = _mix(accent, (255, 255, 255), 0.38)
    visor = (105, 213, 235)
    line_width = _stroke(width, height)

    renderer.draw_rect(
        x + width * 12 // 100,
        y + height * 43 // 100,
        width * 22 // 100,
        height * 34 // 100,
        outline,
    )
    renderer.draw_rect(
        x + width * 31 // 100,
        y + height * 70 // 100,
        width * 15 // 100,
        height * 26 // 100,
        outline,
    )
    renderer.draw_rect(
        x + width * 56 // 100,
        y + height * 70 // 100,
        width * 15 // 100,
        height * 26 // 100,
        outline,
    )
    renderer.draw_rect(
        x + width * 25 // 100,
        y + height * 41 // 100,
        width * 52 // 100,
        height * 39 // 100,
        accent,
    )
    head_x, head_y = _point(x, y, width, height, 53, 24)
    renderer.draw_circle(head_x, head_y, max(2, min(width, height) * 21 // 100), outline)
    renderer.draw_circle(head_x, head_y, max(1, min(width, height) * 17 // 100), highlight)
    renderer.draw_rect(
        x + width * 39 // 100,
        y + height * 17 // 100,
        width * 30 // 100,
        max(1, height * 14 // 100),
        visor,
    )
    renderer.draw_line(
        x + width * 42 // 100,
        y + height * 34 // 100,
        x + width * 65 // 100,
        y + height * 34 // 100,
        outline,
        line_width,
    )
    renderer.draw_polygon(
        (
            _point(x, y, width, height, 40, 50),
            _point(x, y, width, height, 65, 60),
            _point(x, y, width, height, 40, 70),
        ),
        highlight,
    )


def _draw_pixel(
    renderer: _SpriteRenderer,
    x: int,
    y: int,
    width: int,
    height: int,
    accent: Color,
) -> None:
    """Draw a friendly wheeled robot with antenna and two bright eyes."""
    outline = _mix(accent, (18, 25, 54), 0.72)
    panel = _mix(accent, (255, 255, 255), 0.32)
    eye = (132, 255, 244)
    line_width = _stroke(width, height)

    renderer.draw_line(
        x + width // 2,
        y + height * 17 // 100,
        x + width // 2,
        y + height * 6 // 100,
        outline,
        line_width,
    )
    renderer.draw_circle(
        x + width // 2,
        y + height * 5 // 100,
        max(1, min(width, height) * 4 // 100),
        eye,
    )
    renderer.draw_rect(
        x + width * 17 // 100,
        y + height * 17 // 100,
        width * 66 // 100,
        height * 40 // 100,
        outline,
    )
    renderer.draw_rect(
        x + width * 22 // 100,
        y + height * 22 // 100,
        width * 56 // 100,
        height * 30 // 100,
        accent,
    )
    renderer.draw_circle(
        x + width * 37 // 100,
        y + height * 36 // 100,
        max(1, min(width, height) * 6 // 100),
        eye,
    )
    renderer.draw_circle(
        x + width * 63 // 100,
        y + height * 36 // 100,
        max(1, min(width, height) * 6 // 100),
        eye,
    )
    renderer.draw_rect(
        x + width * 28 // 100,
        y + height * 58 // 100,
        width * 44 // 100,
        height * 28 // 100,
        panel,
    )
    renderer.draw_line(
        x + width * 38 // 100,
        y + height * 69 // 100,
        x + width * 62 // 100,
        y + height * 69 // 100,
        outline,
        line_width,
    )
    renderer.draw_circle(
        x + width * 31 // 100,
        y + height * 88 // 100,
        max(1, min(width, height) * 8 // 100),
        outline,
    )
    renderer.draw_circle(
        x + width * 69 // 100,
        y + height * 88 // 100,
        max(1, min(width, height) * 8 // 100),
        outline,
    )


def _draw_moon_compass(
    renderer: _SpriteRenderer,
    x: int,
    y: int,
    width: int,
    height: int,
    accent: Color,
) -> None:
    """Draw a ringed compass face with a high-contrast north/south needle."""
    face = _mix(accent, (255, 255, 255), 0.82)
    outline = _mix(accent, (24, 20, 52), 0.72)
    center_x = x + width // 2
    center_y = y + height // 2
    radius = max(2, min(width, height) * 44 // 100)
    line_width = _stroke(width, height)

    renderer.draw_circle(center_x, center_y, radius, outline)
    renderer.draw_circle(center_x, center_y, max(1, radius - line_width), accent)
    renderer.draw_circle(center_x, center_y, max(1, radius - line_width * 2), face)
    renderer.draw_line(
        center_x,
        center_y - radius + line_width,
        center_x,
        center_y + radius - line_width,
        outline,
        line_width,
    )
    renderer.draw_line(
        center_x - radius + line_width,
        center_y,
        center_x + radius - line_width,
        center_y,
        outline,
        line_width,
    )
    renderer.draw_polygon(
        (
            (center_x, center_y - radius + line_width),
            (center_x + max(2, radius // 4), center_y + max(1, radius // 5)),
            (center_x, center_y),
        ),
        accent,
    )
    renderer.draw_polygon(
        (
            (center_x, center_y + radius - line_width),
            (center_x - max(2, radius // 4), center_y - max(1, radius // 5)),
            (center_x, center_y),
        ),
        outline,
    )
    renderer.draw_circle(center_x, center_y, max(1, line_width), (255, 255, 255))


def _draw_crystal_lantern(
    renderer: _SpriteRenderer,
    x: int,
    y: int,
    width: int,
    height: int,
    accent: Color,
) -> None:
    """Draw a framed lantern around a layered warm crystal glow."""
    frame = _mix(accent, (76, 47, 22), 0.68)
    glow = _mix(accent, (255, 255, 255), 0.42)
    core = (255, 250, 188)
    line_width = _stroke(width, height)
    center_x = x + width // 2
    center_y = y + height * 58 // 100

    renderer.draw_line(
        x + width * 25 // 100,
        y + height * 25 // 100,
        x + width * 31 // 100,
        y + height * 8 // 100,
        frame,
        line_width,
    )
    renderer.draw_line(
        x + width * 31 // 100,
        y + height * 8 // 100,
        x + width * 69 // 100,
        y + height * 8 // 100,
        frame,
        line_width,
    )
    renderer.draw_line(
        x + width * 69 // 100,
        y + height * 8 // 100,
        x + width * 75 // 100,
        y + height * 25 // 100,
        frame,
        line_width,
    )
    renderer.draw_rect(
        x + width * 25 // 100,
        y + height * 24 // 100,
        width * 50 // 100,
        max(1, height * 8 // 100),
        frame,
    )
    renderer.draw_circle(
        center_x,
        center_y,
        max(2, min(width, height) * 27 // 100),
        glow,
    )
    renderer.draw_circle(
        center_x,
        center_y,
        max(1, min(width, height) * 17 // 100),
        core,
    )
    renderer.draw_line(
        x + width * 25 // 100,
        y + height * 28 // 100,
        x + width * 25 // 100,
        y + height * 88 // 100,
        frame,
        line_width,
    )
    renderer.draw_line(
        x + width * 75 // 100,
        y + height * 28 // 100,
        x + width * 75 // 100,
        y + height * 88 // 100,
        frame,
        line_width,
    )
    renderer.draw_line(
        x + width * 25 // 100,
        y + height * 88 // 100,
        x + width * 75 // 100,
        y + height * 88 // 100,
        frame,
        line_width,
    )
    renderer.draw_polygon(
        (
            _point(x, y, width, height, 50, 36),
            _point(x, y, width, height, 61, 58),
            _point(x, y, width, height, 50, 78),
            _point(x, y, width, height, 39, 58),
        ),
        accent,
    )
    renderer.draw_circle(center_x, center_y, max(1, line_width), core)


_SPRITE_DRAWERS: dict[str, SpriteDrawer] = {
    NOVA_QUALIFIED_ID: _draw_nova,
    PIXEL_QUALIFIED_ID: _draw_pixel,
    MOON_COMPASS_QUALIFIED_ID: _draw_moon_compass,
    CRYSTAL_LANTERN_QUALIFIED_ID: _draw_crystal_lantern,
}


def draw_classroom_sprite(
    renderer: _SpriteRenderer,
    qualified_id: str | None,
    x: int,
    y: int,
    width: int,
    height: int,
    color: Color,
) -> bool:
    """Draw one allow-listed sprite and report whether it completed safely."""
    drawer = _SPRITE_DRAWERS.get(qualified_id) if qualified_id is not None else None
    if drawer is None:
        return False
    try:
        drawer(renderer, x, y, width, height, color)
    except Exception:
        _LOGGER.exception("Procedural sprite failed for %s; using rectangle fallback", qualified_id)
        return False
    return True
