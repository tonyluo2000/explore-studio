"""Backdrop for the S02 Classroom Trail: the illustrated Moon Meadow.

Like the S02 sprites, this is a narrow allow-list rather than a world or tile
engine: only the M02 mission receives the backdrop, and every other Trail keeps
its plain cleared frame. The backdrop is static scenery. It reads no entity
state, so it can never move, resize, or hide the authoritative x/y of any
entity; it only decorates the canonical S02 start, discovery clearing, and
Lantern shrine and connects them with one visible trail.

When the renderer can draw trusted art, the backdrop is the course-owned
illustrated plate ``scenery/moon-meadow`` (see ``scripts/build_trusted_art.py``),
drawn with one opaque blit. If that plate is missing, fails its digest, or
cannot be decoded, the original procedural backdrop below is drawn instead.
"""

from __future__ import annotations

import logging
import math
from typing import Final

from engine.rendering._classroom_sprites import Color, _SpriteRenderer, ellipse_points

_LOGGER = logging.getLogger("explore-studio.rendering.classroom-environment")

#: Matches ``explore.curriculum.MISSION_02_ID`` without importing the course
#: layer into the engine.
S02_MISSION_ID: Final = "create-a-classroom-object"

_WIDTH: Final = 960
_HEIGHT: Final = 640
_SKY_HEIGHT: Final = 150

_SKY: Final[Color] = (17, 19, 34)
_STAR: Final[Color] = (122, 132, 176)
_STAR_BRIGHT: Final[Color] = (226, 230, 255)
_MOON: Final[Color] = (226, 222, 196)
_RIDGE_FAR: Final[Color] = (27, 33, 54)
_RIDGE_NEAR: Final[Color] = (33, 45, 58)
_GROUND: Final[Color] = (40, 57, 66)
_GROUND_DARK: Final[Color] = (34, 49, 58)
_GROUND_LIGHT: Final[Color] = (47, 66, 73)
_SPECK: Final[Color] = (58, 78, 84)
_GRASS: Final[Color] = (66, 104, 90)
_ROCK: Final[Color] = (72, 80, 96)
_ROCK_LIGHT: Final[Color] = (98, 106, 122)
_CRATER_RIM: Final[Color] = (55, 73, 80)
_CRATER_FLOOR: Final[Color] = (31, 44, 53)
_CRYSTAL: Final[Color] = (120, 196, 214)
_CRYSTAL_LIGHT: Final[Color] = (186, 236, 244)
_PATH_EDGE: Final[Color] = (76, 76, 92)
_PATH: Final[Color] = (122, 112, 126)
_PATH_MARK: Final[Color] = (206, 194, 166)
_PAD_RIM: Final[Color] = (84, 102, 116)
_PAD: Final[Color] = (60, 76, 90)
_PAD_RING: Final[Color] = (104, 132, 142)
_FLAG: Final[Color] = (226, 112, 82)
_CLEARING: Final[Color] = (52, 74, 78)
_PLAZA_RIM: Final[Color] = (112, 100, 104)
_PLAZA: Final[Color] = (88, 80, 90)
_PLAZA_GLOW: Final[Color] = (122, 106, 80)
_PLAZA_GLOW_CORE: Final[Color] = (150, 128, 76)
_STONE: Final[Color] = (112, 104, 124)
_STONE_SHADE: Final[Color] = (80, 74, 92)
_GEM: Final[Color] = (250, 214, 96)

_START_CENTER: Final = (505, 382)
_CLEARING_CENTER: Final = (282, 222)
_SHRINE_CENTER: Final = (160, 500)

Point = tuple[int, int]


def _lcg_points(
    seed: int,
    count: int,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> tuple[Point, ...]:
    """Deterministic scatter without touching global random state."""
    state = seed
    points: list[Point] = []
    for _ in range(count):
        state = (state * 1103515245 + 12345) % 2**31
        px = left + state % (right - left)
        state = (state * 1103515245 + 12345) % 2**31
        py = top + state % (bottom - top)
        points.append((px, py))
    return tuple(points)


def _bezier(
    p0: Point, p1: Point, p2: Point, p3: Point, t: float
) -> tuple[float, float, float, float]:
    """Return a cubic Bezier point and its tangent at *t*."""
    u = 1 - t
    x = u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0]
    y = u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]
    dx = 3 * u * u * (p1[0] - p0[0]) + 6 * u * t * (p2[0] - p1[0]) + 3 * t * t * (p3[0] - p2[0])
    dy = 3 * u * u * (p1[1] - p0[1]) + 6 * u * t * (p2[1] - p1[1]) + 3 * t * t * (p3[1] - p2[1])
    return x, y, dx, dy


# Start -> Moon Compass clearing -> Crystal Lantern shrine.
_TRAIL_SEGMENTS: Final = (
    (_START_CENTER, (400, 384), (372, 248), _CLEARING_CENTER),
    (_CLEARING_CENTER, (176, 262), (236, 420), _SHRINE_CENTER),
)
_TRAIL_POINTS: Final = tuple(
    (round(x), round(y))
    for segment in _TRAIL_SEGMENTS
    for step in range(41)
    for x, y, _, _ in (_bezier(*segment, step / 40),)
)
_CHEVRONS: Final = ((0, 0.42), (0, 0.66), (1, 0.34), (1, 0.52), (1, 0.7))

#: The Trail HUD writes four text rows at the top-left; stars stay out of them
#: so the sky reads as a quiet backing for mission text.
_HUD_TEXT_ROWS: Final = ((14, 46), (50, 80), (80, 110), (110, 140))
_HUD_TEXT_RIGHT: Final = 890
_STARS: Final = tuple(
    (x, y)
    for x, y in _lcg_points(7, 140, 6, 6, _WIDTH - 6, _SKY_HEIGHT - 12)
    if x >= _HUD_TEXT_RIGHT or not any(top <= y <= bottom for top, bottom in _HUD_TEXT_ROWS)
)
_SPECKS: Final = _lcg_points(29, 150, 4, _SKY_HEIGHT + 14, _WIDTH - 4, _HEIGHT - 4)
_GROUND_PATCHES: Final = (
    (140, 230, 120, 46, _GROUND_LIGHT),
    (700, 300, 170, 60, _GROUND_LIGHT),
    (840, 560, 150, 50, _GROUND_DARK),
    (430, 560, 190, 46, _GROUND_DARK),
    (60, 610, 120, 40, _GROUND_LIGHT),
    (560, 200, 120, 34, _GROUND_DARK),
    (860, 200, 110, 36, _GROUND_DARK),
)
_CRATERS: Final = ((770, 236, 52, 20), (870, 452, 44, 17), (650, 520, 46, 17), (70, 330, 34, 13))
_ROCKS: Final = (
    (704, 168, 9),
    (916, 318, 11),
    (384, 486, 8),
    (40, 590, 10),
    (262, 604, 8),
    (602, 454, 7),
    (822, 372, 8),
    (440, 196, 7),
)
_GRASS_TUFTS: Final = (
    (360, 300),
    (212, 380),
    (330, 430),
    (640, 262),
    (720, 420),
    (920, 250),
    (560, 610),
    (28, 470),
    (300, 520),
    (780, 610),
    (470, 250),
)
_CRYSTAL_CLUSTERS: Final = ((46, 420), (282, 470), (892, 396), (596, 176))
_CLEARING_STONES: Final = tuple(
    (
        round(_CLEARING_CENTER[0] + 90 * math.cos(angle)),
        round(_CLEARING_CENTER[1] + 52 * math.sin(angle)),
    )
    for angle in (math.tau * index / 10 + 0.3 for index in range(10))
)


def _ellipse(renderer: _SpriteRenderer, cx: int, cy: int, rx: int, ry: int, color: Color) -> None:
    renderer.draw_polygon(ellipse_points(cx, cy, rx, ry), color)


def _ellipse_outline(
    renderer: _SpriteRenderer, cx: int, cy: int, rx: int, ry: int, color: Color
) -> None:
    points = ellipse_points(cx, cy, rx, ry)
    for start, end in zip(points, points[1:] + points[:1], strict=True):
        renderer.draw_line(start[0], start[1], end[0], end[1], color, 2)


def _draw_sky(renderer: _SpriteRenderer) -> None:
    renderer.draw_rect(0, 0, _WIDTH, _SKY_HEIGHT + 20, _SKY)
    for index, (x, y) in enumerate(_STARS):
        if index % 7 == 0:
            renderer.draw_circle(x, y, 2, _STAR_BRIGHT)
        else:
            renderer.draw_rect(x, y, 2, 2, _STAR)
    renderer.draw_circle(914, 42, 20, _MOON)
    renderer.draw_circle(922, 36, 17, _SKY)
    far = [(0, _SKY_HEIGHT + 20)]
    for x in range(0, _WIDTH + 1, 40):
        far.append((x, _SKY_HEIGHT - 8 + round(8 * math.sin(x / 70) + 5 * math.sin(x / 23))))
    far.append((_WIDTH, _SKY_HEIGHT + 20))
    renderer.draw_polygon(tuple(far), _RIDGE_FAR)
    near = [(0, _SKY_HEIGHT + 24)]
    for x in range(0, _WIDTH + 1, 32):
        near.append((x, _SKY_HEIGHT + 4 + round(6 * math.sin(x / 55 + 1.7))))
    near.append((_WIDTH, _SKY_HEIGHT + 24))
    renderer.draw_polygon(tuple(near), _RIDGE_NEAR)


def _draw_ground(renderer: _SpriteRenderer) -> None:
    renderer.draw_rect(0, _SKY_HEIGHT + 12, _WIDTH, _HEIGHT - _SKY_HEIGHT - 12, _GROUND)
    for cx, cy, rx, ry, color in _GROUND_PATCHES:
        _ellipse(renderer, cx, cy, rx, ry, color)
    for x, y in _SPECKS:
        renderer.draw_rect(x, y, 2, 2, _SPECK)
    for cx, cy, rx, ry in _CRATERS:
        _ellipse(renderer, cx, cy, rx, ry, _CRATER_RIM)
        _ellipse(renderer, cx, cy + 2, rx - 6, ry - 4, _CRATER_FLOOR)
    for x, y, size in _ROCKS:
        renderer.draw_polygon(
            (
                (x - size, y + size // 2),
                (x - size // 2, y - size),
                (x + size, y - size // 2),
                (x + size, y + size // 2),
            ),
            _ROCK,
        )
        renderer.draw_polygon(
            ((x - size // 2, y - size), (x + size, y - size // 2), (x + size // 3, y)),
            _ROCK_LIGHT,
        )
    for x, y in _GRASS_TUFTS:
        renderer.draw_line(x, y, x - 5, y - 9, _GRASS, 2)
        renderer.draw_line(x, y, x, y - 12, _GRASS, 2)
        renderer.draw_line(x, y, x + 5, y - 9, _GRASS, 2)
    for x, y in _CRYSTAL_CLUSTERS:
        renderer.draw_polygon(((x - 8, y), (x - 5, y - 14), (x - 2, y)), _CRYSTAL)
        renderer.draw_polygon(((x - 3, y), (x + 1, y - 22), (x + 5, y)), _CRYSTAL_LIGHT)
        renderer.draw_polygon(((x + 4, y), (x + 8, y - 12), (x + 10, y)), _CRYSTAL)


def _draw_trail(renderer: _SpriteRenderer) -> None:
    for x, y in _TRAIL_POINTS:
        renderer.draw_circle(x, y, 17, _PATH_EDGE)
    for x, y in _TRAIL_POINTS:
        renderer.draw_circle(x, y, 13, _PATH)


def _draw_chevrons(renderer: _SpriteRenderer) -> None:
    """Point every trail marker toward the Lantern shrine."""
    for segment_index, t in _CHEVRONS:
        x, y, dx, dy = _bezier(*_TRAIL_SEGMENTS[segment_index], t)
        length = math.hypot(dx, dy) or 1.0
        ux, uy = dx / length, dy / length
        tip = (round(x + ux * 6), round(y + uy * 6))
        for side in (-1, 1):
            renderer.draw_line(
                tip[0],
                tip[1],
                round(x - ux * 6 + side * uy * 7),
                round(y - uy * 6 - side * ux * 7),
                _PATH_MARK,
                3,
            )


def _draw_start_zone(renderer: _SpriteRenderer) -> None:
    cx, cy = _START_CENTER
    _ellipse(renderer, cx, cy, 124, 50, _PAD_RIM)
    _ellipse(renderer, cx, cy + 2, 116, 44, _PAD)
    _ellipse_outline(renderer, cx, cy + 2, 96, 34, _PAD_RING)
    for angle_index in range(8):
        angle = math.tau * angle_index / 8
        renderer.draw_circle(
            round(cx + 110 * math.cos(angle)),
            round(cy + 2 + 40 * math.sin(angle)),
            3,
            _PAD_RING,
        )
    renderer.draw_line(616, 392, 616, 294, _ROCK_LIGHT, 3)
    renderer.draw_polygon(((617, 296), (656, 309), (617, 322)), _FLAG)
    renderer.draw_circle(616, 293, 3, _PATH_MARK)


def _draw_clearing(renderer: _SpriteRenderer) -> None:
    cx, cy = _CLEARING_CENTER
    _ellipse(renderer, cx, cy, 84, 46, _CLEARING)
    for x, y in _CLEARING_STONES:
        renderer.draw_circle(x, y, 6, _ROCK)
        renderer.draw_circle(x - 1, y - 2, 3, _ROCK_LIGHT)


def _draw_shrine(renderer: _SpriteRenderer) -> None:
    cx, cy = _SHRINE_CENTER
    # Gate behind the Lantern: two pillars and a lintel frame the destination.
    for pillar_x in (88, 220):
        renderer.draw_rect(pillar_x, 424, 14, 72, _STONE_SHADE)
        renderer.draw_rect(pillar_x + 2, 424, 8, 72, _STONE)
    renderer.draw_rect(76, 410, 168, 12, _STONE)
    renderer.draw_rect(84, 422, 152, 4, _STONE_SHADE)
    renderer.draw_polygon(((cx, 406), (cx + 8, 416), (cx, 426), (cx - 8, 416)), _GEM)
    _ellipse(renderer, cx, cy, 98, 48, _PLAZA_RIM)
    _ellipse(renderer, cx, cy + 2, 90, 42, _PLAZA)
    _ellipse(renderer, cx, cy + 4, 70, 30, _PLAZA_GLOW)
    _ellipse(renderer, cx, cy + 6, 46, 18, _PLAZA_GLOW_CORE)
    for angle_index in range(12):
        angle = math.tau * angle_index / 12
        renderer.draw_line(
            round(cx + 74 * math.cos(angle)),
            round(cy + 4 + 32 * math.sin(angle)),
            round(cx + 86 * math.cos(angle)),
            round(cy + 4 + 38 * math.sin(angle)),
            _PLAZA_GLOW,
            2,
        )


def _draw_backdrop(renderer: _SpriteRenderer) -> None:
    _draw_sky(renderer)
    _draw_ground(renderer)
    _draw_trail(renderer)
    _draw_start_zone(renderer)
    _draw_clearing(renderer)
    _draw_shrine(renderer)
    _draw_chevrons(renderer)


#: Trusted scenery plates: the opaque background and the framing foreground.
MEADOW_BACKDROP: Final = ("scenery/moon-meadow", "night", "backdrop")
MEADOW_FOREGROUND: Final = ("scenery/moon-meadow-foreground", "night", "frame")


def draw_scenery_plate(renderer: object, plate: tuple[str, str, str]) -> bool:
    """Draw one full-screen trusted plate; report False when it is unavailable."""
    draw_frame = getattr(renderer, "draw_sprite_frame", None)
    if draw_frame is None:
        return False
    return bool(draw_frame(*plate, 0, 0, _WIDTH, _HEIGHT))


def illustrated_backdrop_available(renderer: object) -> bool:
    """True when the renderer's trusted library can serve the illustrated plate.

    Ambient effects use this to animate the painted scenery's positions, and
    fall back to the procedural backdrop's positions otherwise. The frame
    lookup is cached by the library, so asking every frame costs a dict read.
    """
    library = getattr(renderer, "sprite_sheets", None)
    frame = getattr(library, "frame", None)
    if frame is None:
        return False
    try:
        return frame(*MEADOW_BACKDROP, _WIDTH, _HEIGHT) is not None
    except Exception:
        return False


def draw_classroom_backdrop(renderer: _SpriteRenderer, mission_id: str) -> bool:
    """Draw the S02 scenery behind entities; report whether it completed."""
    if mission_id != S02_MISSION_ID:
        return False
    try:
        if draw_scenery_plate(renderer, MEADOW_BACKDROP):
            return True
        _draw_backdrop(renderer)
    except Exception:
        _LOGGER.exception("Classroom backdrop failed for %s; using plain frame", mission_id)
        return False
    return True
