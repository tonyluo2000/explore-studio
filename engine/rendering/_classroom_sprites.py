"""Original procedural sprites for the four S02 classroom examples.

This is intentionally a narrow identity allow-list, not the future generic
Explorer Package ``asset_id`` pipeline. Unknown identities return ``False`` so
the Trail can retain its rectangle rendering contract.
"""

from __future__ import annotations

import logging
import math
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


_SHADOW: Color = (22, 30, 38)
_WHITE: Color = (255, 255, 255)
_NEEDLE: Color = (222, 64, 70)


def _mix(color: Color, target: Color, amount: float) -> Color:
    return tuple(
        round(channel + (target_channel - channel) * amount)
        for channel, target_channel in zip(color, target, strict=True)
    )  # type: ignore[return-value]


def ellipse_points(
    center_x: int,
    center_y: int,
    radius_x: int,
    radius_y: int,
    segments: int = 32,
) -> tuple[tuple[int, int], ...]:
    """Return a closed ellipse outline that never leaves its radii."""
    return tuple(
        (
            center_x + round(radius_x * math.cos(math.tau * index / segments)),
            center_y + round(radius_y * math.sin(math.tau * index / segments)),
        )
        for index in range(segments)
    )


class _Box:
    """Map whole-number percentages onto one entity's rendering bounds."""

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.small = min(width, height)

    def px(self, x_part: int) -> int:
        return self.x + self.width * x_part // 100

    def py(self, y_part: int) -> int:
        return self.y + self.height * y_part // 100

    def point(self, x_part: int, y_part: int) -> tuple[int, int]:
        return self.px(x_part), self.py(y_part)

    def radius(self, part: int) -> int:
        return max(1, self.small * part // 100)

    def rect(
        self,
        renderer: _SpriteRenderer,
        left: int,
        top: int,
        right: int,
        bottom: int,
        color: Color,
    ) -> None:
        x = self.px(left)
        y = self.py(top)
        renderer.draw_rect(x, y, max(1, self.px(right) - x), max(1, self.py(bottom) - y), color)

    def polygon(
        self,
        renderer: _SpriteRenderer,
        points: tuple[tuple[int, int], ...],
        color: Color,
    ) -> None:
        renderer.draw_polygon(tuple(self.point(px, py) for px, py in points), color)

    def shadow(self, renderer: _SpriteRenderer, x_part: int, width_part: int) -> None:
        renderer.draw_polygon(
            ellipse_points(
                self.px(x_part),
                self.py(95),
                self.width * width_part // 100,
                max(1, self.height * 4 // 100),
            ),
            _SHADOW,
        )


def _stroke(width: int, height: int) -> int:
    return max(1, min(width, height) // 30)


def _sparkle(renderer: _SpriteRenderer, x: int, y: int, size: int, color: Color) -> None:
    inner = max(1, size // 3)
    renderer.draw_polygon(
        (
            (x, y - size),
            (x + inner, y - inner),
            (x + size, y),
            (x + inner, y + inner),
            (x, y + size),
            (x - inner, y + inner),
            (x - size, y),
            (x - inner, y - inner),
        ),
        color,
    )


def _draw_nova(
    renderer: _SpriteRenderer,
    x: int,
    y: int,
    width: int,
    height: int,
    accent: Color,
) -> None:
    """Draw a helmeted explorer with a backpack, filling most of its bounds.

    The silhouette spans 12-79% horizontally so Pixel, standing to Nova's
    right at the S02 start, stays visible beside rather than behind Nova.
    """
    box = _Box(x, y, width, height)
    outline = _mix(accent, (24, 28, 42), 0.78)
    shade = _mix(accent, (24, 28, 42), 0.35)
    highlight = _mix(accent, _WHITE, 0.45)
    pack = (136, 144, 164)
    shell = (234, 238, 246)
    visor = (105, 213, 235)

    box.shadow(renderer, 47, 32)
    box.rect(renderer, 12, 40, 32, 76, outline)
    box.rect(renderer, 15, 43, 30, 73, pack)
    box.rect(renderer, 17, 50, 28, 54, outline)
    renderer.draw_line(*box.point(22, 41), *box.point(33, 32), outline, _stroke(width, height) + 1)
    box.rect(renderer, 30, 72, 47, 98, outline)
    box.rect(renderer, 51, 72, 68, 98, outline)
    box.rect(renderer, 32, 72, 45, 89, shade)
    box.rect(renderer, 53, 72, 66, 89, shade)
    box.rect(renderer, 26, 40, 72, 79, outline)
    box.rect(renderer, 29, 43, 69, 76, accent)
    box.rect(renderer, 29, 68, 69, 72, shade)
    box.rect(renderer, 68, 45, 79, 71, outline)
    box.rect(renderer, 70, 47, 77, 68, shade)
    box.polygon(renderer, ((49, 47), (57, 55), (49, 63), (41, 55)), highlight)
    head_x, head_y = box.point(49, 24)
    renderer.draw_circle(head_x, head_y, box.radius(23), outline)
    renderer.draw_circle(head_x, head_y, box.radius(20), shell)
    box.rect(renderer, 33, 15, 67, 34, outline)
    box.rect(renderer, 35, 17, 65, 32, visor)
    box.rect(renderer, 39, 19, 46, 23, _WHITE)
    renderer.draw_circle(*box.point(33, 10), box.radius(4), accent)


def _draw_pixel(
    renderer: _SpriteRenderer,
    x: int,
    y: int,
    width: int,
    height: int,
    accent: Color,
) -> None:
    """Draw a friendly treaded robot with a screen face and bright eyes.

    Pixel is drawn smaller than the player and to the right of its bounds so
    that, beside Nova at the S02 start, both silhouettes stay separate.
    """
    box = _Box(x, y, width, height)
    outline = _mix(accent, (18, 25, 54), 0.72)
    panel = _mix(accent, _WHITE, 0.38)
    screen = (18, 26, 52)
    eye = (132, 255, 244)
    bulb = (255, 168, 96)
    line_width = _stroke(width, height)

    box.shadow(renderer, 64, 28)
    renderer.draw_line(*box.point(64, 20), *box.point(64, 10), outline, line_width + 1)
    renderer.draw_circle(*box.point(64, 8), box.radius(5), bulb)
    box.rect(renderer, 34, 30, 94, 44, outline)
    box.rect(renderer, 38, 19, 90, 55, outline)
    box.rect(renderer, 41, 22, 87, 52, accent)
    box.rect(renderer, 45, 26, 83, 48, screen)
    renderer.draw_circle(*box.point(56, 36), box.radius(5), eye)
    renderer.draw_circle(*box.point(72, 36), box.radius(5), eye)
    renderer.draw_line(*box.point(58, 44), *box.point(70, 44), eye, line_width)
    box.rect(renderer, 60, 55, 68, 58, outline)
    renderer.draw_line(*box.point(44, 64), *box.point(37, 76), outline, line_width + 1)
    renderer.draw_line(*box.point(84, 64), *box.point(91, 76), outline, line_width + 1)
    box.rect(renderer, 43, 57, 85, 85, outline)
    box.rect(renderer, 46, 60, 82, 82, panel)
    renderer.draw_circle(*box.point(64, 70), box.radius(5), bulb)
    box.rect(renderer, 39, 84, 89, 96, outline)
    for wheel in (48, 64, 80):
        renderer.draw_circle(*box.point(wheel, 90), box.radius(4), panel)


def _draw_moon_compass(
    renderer: _SpriteRenderer,
    x: int,
    y: int,
    width: int,
    height: int,
    accent: Color,
) -> None:
    """Draw a thick student-colored ring around a legible compass face."""
    box = _Box(x, y, width, height)
    face = _mix(accent, _WHITE, 0.86)
    outline = _mix(accent, (24, 20, 52), 0.78)
    sparkle = _mix(accent, _WHITE, 0.72)
    center_x = box.px(50)
    center_y = box.py(45)
    radius = max(3, box.small * 45 // 100)
    ring = max(2, box.small // 10)
    tick = max(1, radius // 7)

    box.shadow(renderer, 50, 30)
    _sparkle(renderer, *box.point(9, 22), box.radius(10), sparkle)
    _sparkle(renderer, *box.point(90, 70), box.radius(8), sparkle)
    renderer.draw_circle(center_x, center_y, radius, outline)
    renderer.draw_circle(center_x, center_y, max(1, radius - 2), accent)
    renderer.draw_circle(center_x, center_y, max(1, radius - ring), outline)
    renderer.draw_circle(center_x, center_y, max(1, radius - ring - 1), face)
    inner = max(1, radius - ring - 1)
    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        renderer.draw_line(
            center_x + dx * inner,
            center_y + dy * inner,
            center_x + dx * (inner - tick),
            center_y + dy * (inner - tick),
            outline,
            2,
        )
    needle = max(2, inner - tick - 1)
    half_width = max(2, radius // 6)
    renderer.draw_polygon(
        (
            (center_x, center_y - needle),
            (center_x + half_width, center_y),
            (center_x - half_width, center_y),
        ),
        _NEEDLE,
    )
    renderer.draw_polygon(
        (
            (center_x, center_y + needle),
            (center_x - half_width, center_y),
            (center_x + half_width, center_y),
        ),
        outline,
    )
    renderer.draw_circle(center_x, center_y, max(1, radius // 9), _WHITE)


def _draw_crystal_lantern(
    renderer: _SpriteRenderer,
    x: int,
    y: int,
    width: int,
    height: int,
    accent: Color,
) -> None:
    """Draw a framed lantern inside a layered glow that fills its bounds."""
    box = _Box(x, y, width, height)
    night = (38, 46, 60)
    frame = _mix(accent, (76, 47, 22), 0.68)
    frame_dark = _mix(frame, (20, 16, 12), 0.35)
    glass = _mix(accent, _WHITE, 0.45)
    core = (255, 250, 188)
    ray = _mix(accent, _WHITE, 0.3)
    center_x = box.px(50)
    center_y = box.py(50)
    halo = max(2, box.small // 2)

    renderer.draw_circle(center_x, center_y, halo, _mix(accent, night, 0.6))
    renderer.draw_circle(center_x, center_y, max(1, halo * 4 // 5), _mix(accent, night, 0.36))
    for index in range(8):
        angle = math.tau * index / 8 + math.tau / 16
        renderer.draw_line(
            center_x + round(halo * 0.84 * math.cos(angle)),
            center_y + round(halo * 0.84 * math.sin(angle)),
            center_x + round((halo - 1) * math.cos(angle)),
            center_y + round((halo - 1) * math.sin(angle)),
            ray,
            2,
        )
    _sparkle(renderer, *box.point(8, 18), box.radius(9), core)
    _sparkle(renderer, *box.point(92, 22), box.radius(8), core)
    _sparkle(renderer, *box.point(10, 82), box.radius(6), ray)
    _sparkle(renderer, *box.point(90, 80), box.radius(6), ray)
    renderer.draw_line(*box.point(40, 15), *box.point(44, 4), frame, 2)
    renderer.draw_line(*box.point(44, 4), *box.point(56, 4), frame, 2)
    renderer.draw_line(*box.point(56, 4), *box.point(60, 15), frame, 2)
    box.polygon(renderer, ((27, 25), (73, 25), (62, 13), (38, 13)), frame)
    box.rect(renderer, 28, 24, 72, 80, frame)
    box.rect(renderer, 32, 28, 68, 76, glass)
    box.polygon(renderer, ((50, 30), (61, 52), (50, 74), (39, 52)), core)
    box.polygon(renderer, ((50, 40), (54, 52), (50, 64), (46, 52)), accent)
    box.rect(renderer, 23, 79, 77, 88, frame)
    box.rect(renderer, 31, 88, 69, 94, frame_dark)
    renderer.draw_circle(*box.point(50, 52), box.radius(3), _WHITE)


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
