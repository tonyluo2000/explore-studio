"""Build the course-owned trusted sprite sheets for the S02 Classroom Trail.

This is the provenance for every PNG under ``engine/assets/trusted``. The art
is original and drawn from code: each frame is painted at 4x on a transparent
canvas with Pygame primitives, then smooth-scaled down so outlines and curves
are anti-aliased. The script also writes ``manifest.json``, which records each
sheet's frame grid, declared accent color, and SHA-256 digest. The runtime
loads only files listed in that manifest whose bytes match their digest.

Run from the repository root after changing the art, then review the PNGs::

    SDL_VIDEODRIVER=dummy python3 scripts/build_trusted_art.py

The committed PNGs and manifest are the reviewed artifact; regenerating them
with a different Pygame build may change bytes, so always commit the pair.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
TRUSTED_ROOT = REPO / "engine" / "assets" / "trusted"
SUPERSAMPLE = 4

Color = tuple[int, int, int]
Point = tuple[float, float]

OUTLINE: Color = (28, 24, 40)
WHITE: Color = (255, 255, 255)


class Canvas:
    """Draw in frame units (one unit = one final pixel) at 4x resolution."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.surface = pygame.Surface(
            (width * SUPERSAMPLE, height * SUPERSAMPLE), pygame.SRCALPHA, 32
        )
        self.surface.fill((0, 0, 0, 0))

    @staticmethod
    def _s(value: float) -> int:
        return round(value * SUPERSAMPLE)

    def circle(self, color: Color, cx: float, cy: float, r: float, *, outline: float = 0) -> None:
        if outline:
            pygame.draw.circle(
                self.surface, OUTLINE, (self._s(cx), self._s(cy)), self._s(r + outline)
            )
        pygame.draw.circle(self.surface, color, (self._s(cx), self._s(cy)), self._s(r))

    def ellipse(
        self, color: Color, cx: float, cy: float, rx: float, ry: float, *, outline: float = 0
    ) -> None:
        if outline:
            self.ellipse(OUTLINE, cx, cy, rx + outline, ry + outline)
        rect = pygame.Rect(0, 0, self._s(rx * 2), self._s(ry * 2))
        rect.center = (self._s(cx), self._s(cy))
        pygame.draw.ellipse(self.surface, color, rect)

    def rrect(
        self,
        color: Color,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        radius: float,
        *,
        outline: float = 0,
    ) -> None:
        if outline:
            self.rrect(
                OUTLINE, x0 - outline, y0 - outline, x1 + outline, y1 + outline, radius + outline
            )
        rect = pygame.Rect(self._s(x0), self._s(y0), self._s(x1 - x0), self._s(y1 - y0))
        pygame.draw.rect(self.surface, color, rect, border_radius=self._s(radius))

    def polygon(self, color: Color, points: Sequence[Point], *, outline: float = 0) -> None:
        scaled = [(self._s(x), self._s(y)) for x, y in points]
        if outline:
            pygame.draw.polygon(self.surface, OUTLINE, scaled)
            pygame.draw.polygon(self.surface, OUTLINE, scaled, self._s(outline * 2))
        pygame.draw.polygon(self.surface, color, scaled)

    def line(self, color: Color, start: Point, end: Point, width: float) -> None:
        self.capsule(color, start, end, width / 2)

    def capsule(
        self, color: Color, start: Point, end: Point, radius: float, *, outline: float = 0
    ) -> None:
        if outline:
            self.capsule(OUTLINE, start, end, radius + outline)
        pygame.draw.line(
            self.surface,
            color,
            (self._s(start[0]), self._s(start[1])),
            (self._s(end[0]), self._s(end[1])),
            max(1, self._s(radius * 2)),
        )
        for x, y in (start, end):
            pygame.draw.circle(self.surface, color, (self._s(x), self._s(y)), self._s(radius))

    def arc(
        self, color: Color, cx: float, cy: float, r: float, start: float, stop: float, width: float
    ) -> None:
        steps = 10
        points = [
            (
                cx + r * math.cos(start + (stop - start) * index / steps),
                cy + r * math.sin(start + (stop - start) * index / steps),
            )
            for index in range(steps + 1)
        ]
        for first, second in zip(points, points[1:], strict=False):
            self.line(color, first, second, width)

    def finish(self) -> pygame.Surface:
        return pygame.transform.smoothscale(self.surface, (self.width, self.height))


def mix(color: Color, target: Color, amount: float) -> Color:
    return tuple(  # type: ignore[return-value]
        round(channel + (target_channel - channel) * amount)
        for channel, target_channel in zip(color, target, strict=True)
    )


# ---------------------------------------------------------------------------
# Nova — the class reference Explorer
# ---------------------------------------------------------------------------

NOVA_ACCENT: Color = (255, 200, 50)
GOLD = NOVA_ACCENT
GOLD_SHADE: Color = (214, 146, 34)
GOLD_LIGHT: Color = (255, 232, 150)
HELMET: Color = (238, 242, 250)
HELMET_SHADE: Color = (184, 194, 218)
VISOR: Color = (26, 40, 78)
VISOR_SHINE: Color = (86, 128, 196)
EYE: Color = (140, 246, 255)
SCARF: Color = (230, 72, 84)
SCARF_SHADE: Color = (172, 42, 62)
PACK: Color = (112, 126, 152)
PACK_SHADE: Color = (82, 94, 120)
ROLL: Color = (238, 132, 62)
ROLL_SHADE: Color = (190, 94, 46)
BOOT: Color = (96, 66, 54)
BOOT_SOLE: Color = (226, 214, 192)
GLOVE: Color = (242, 242, 248)
BEACON: Color = (255, 112, 92)
BOLT: Color = (150, 162, 186)

NOVA_FRAME = (100, 100)
#: Sheet columns: idle 0-3, blink, walk 0-3. Rows: down, up, right.
NOVA_COLUMNS = (
    "idle-0",
    "idle-1",
    "idle-2",
    "idle-3",
    "blink",
    "walk-0",
    "walk-1",
    "walk-2",
    "walk-3",
)
NOVA_ROWS = ("down", "up", "right")

IDLE_BOB = (0.0, 0.7, 1.4, 0.7)
WALK_BOB = (1.4, 0.0, 1.4, 0.0)


def _nova_helmet(canvas: Canvas, cx: float, cy: float, *, face: str, blink: bool) -> None:
    """Helmet with visor; *face* is ``front``, ``side`` or ``back``."""
    antenna_base = (cx - 11, cy - 17) if face != "side" else (cx - 9, cy - 18)
    antenna_tip = (antenna_base[0] - 4, antenna_base[1] - 7)
    canvas.line(OUTLINE, antenna_base, antenna_tip, 2.6)
    canvas.circle(BEACON, *antenna_tip, 3.0, outline=1.2)
    canvas.circle(WHITE, antenna_tip[0] - 0.9, antenna_tip[1] - 0.9, 0.9)
    if face == "front":
        canvas.circle(BOLT, cx - 20.5, cy + 2, 4.2, outline=1.2)
        canvas.circle(BOLT, cx + 20.5, cy + 2, 4.2, outline=1.2)
    canvas.circle(HELMET_SHADE, cx, cy, 21, outline=1.6)
    canvas.circle(HELMET, cx - 2, cy - 2, 18.6)
    canvas.circle(WHITE, cx - 10, cy - 11, 3.2)
    if face == "front":
        canvas.rrect(VISOR, cx - 17, cy - 10, cx + 17, cy + 12, 10, outline=1.4)
        canvas.rrect(VISOR_SHINE, cx - 13, cy - 7.5, cx - 4, cy - 5, 1.2)
        for eye_x in (cx - 6.5, cx + 6.5):
            if blink:
                canvas.line(EYE, (eye_x - 3, cy + 2), (eye_x + 3, cy + 2), 2.0)
            else:
                canvas.rrect(EYE, eye_x - 2.6, cy - 4, eye_x + 2.6, cy + 6, 2.6)
                canvas.circle(WHITE, eye_x - 0.8, cy - 1.8, 1.0)
    elif face == "side":
        canvas.circle(BOLT, cx - 6, cy + 2, 4.0, outline=1.2)
        canvas.rrect(VISOR, cx + 2, cy - 10, cx + 21, cy + 12, 9, outline=1.4)
        canvas.rrect(VISOR_SHINE, cx + 6, cy - 7.5, cx + 12, cy - 5, 1.2)
        eye_x = cx + 13
        if blink:
            canvas.line(EYE, (eye_x - 2.6, cy + 2), (eye_x + 2.6, cy + 2), 2.0)
        else:
            canvas.rrect(EYE, eye_x - 2.4, cy - 4, eye_x + 2.4, cy + 6, 2.4)
            canvas.circle(WHITE, eye_x - 0.6, cy - 1.8, 1.0)
    else:
        canvas.rrect(HELMET_SHADE, cx - 8, cy + 1, cx + 8, cy + 12, 4, outline=1.0)
        for slit in (-4, 0, 4):
            canvas.line(PACK_SHADE, (cx + slit, cy + 4), (cx + slit, cy + 9), 1.6)


def _boot(canvas: Canvas, x: float, bottom: float, *, side: bool, shade: bool) -> None:
    color = mix(BOOT, OUTLINE, 0.35) if shade else BOOT
    if side:
        canvas.rrect(color, x - 5, bottom - 7, x + 7, bottom, 3, outline=1.3)
        canvas.rrect(BOOT_SOLE, x - 5, bottom - 2, x + 7, bottom, 1)
    else:
        canvas.rrect(color, x - 5.5, bottom - 8, x + 5.5, bottom, 3, outline=1.3)
        canvas.rrect(BOOT_SOLE, x - 5.5, bottom - 2, x + 5.5, bottom, 1)


def _nova_front(
    canvas: Canvas,
    *,
    bob: float,
    lift: tuple[float, float],
    swing: float,
    blink: bool,
    sway: float,
    back: bool,
) -> None:
    body = 49 + bob
    for leg_x, leg_lift in zip((42.0, 54.0), lift, strict=True):
        canvas.capsule(GOLD_SHADE, (leg_x, body + 24), (leg_x, 90 - leg_lift), 4.2, outline=1.3)
        _boot(canvas, leg_x, 97 - leg_lift, side=False, shade=False)
    if not back:
        canvas.rrect(PACK, 29, body - 1, 67, body + 24, 6, outline=1.4)
    for shoulder_x, hand_x, hand_dy in ((34.5, 30.0, swing), (61.5, 66.0, -swing)):
        hand = (hand_x, body + 20 + hand_dy)
        canvas.capsule(GOLD_SHADE, (shoulder_x, body + 5), hand, 4.0, outline=1.3)
        canvas.circle(GLOVE, *hand, 4.3, outline=1.2)
    canvas.rrect(GOLD, 34, body, 62, body + 27, 9, outline=1.5)
    canvas.rrect(GOLD_LIGHT, 37, body + 3, 42, body + 19, 2.5)
    canvas.rrect(GOLD_SHADE, 34, body + 20, 62, body + 27, 6)
    canvas.rrect(BOOT, 34, body + 20, 62, body + 24.5, 1.5)
    if back:
        canvas.rrect(ROLL, 31, body - 7, 65, body, 3.5, outline=1.4)
        canvas.line(ROLL_SHADE, (40, body - 6), (40, body - 1), 1.4)
        canvas.line(ROLL_SHADE, (56, body - 6), (56, body - 1), 1.4)
        canvas.rrect(PACK, 32, body - 1, 64, body + 25, 7, outline=1.4)
        canvas.rrect(PACK_SHADE, 32, body - 1, 64, body + 8, 5)
        canvas.rrect(PACK_SHADE, 38, body + 11, 58, body + 22, 3, outline=1.0)
        canvas.rrect(GOLD_LIGHT, 46, body + 7, 50, body + 12, 1)
    else:
        canvas.line(PACK_SHADE, (39.5, body + 1), (38.5, body + 20), 2.6)
        canvas.line(PACK_SHADE, (56.5, body + 1), (57.5, body + 20), 2.6)
        canvas.rrect(GOLD_LIGHT, 45, body + 19.5, 51, body + 25, 1.5, outline=0.8)
        star_y = body + 11
        canvas.polygon(
            WHITE,
            (
                (48, star_y - 5),
                (49.5, star_y - 1.5),
                (53, star_y),
                (49.5, star_y + 1.5),
                (48, star_y + 5),
                (46.5, star_y + 1.5),
                (43, star_y),
                (46.5, star_y - 1.5),
            ),
            outline=0.8,
        )
    # Scarf: a red band with a tail that sways as Nova breathes or walks.
    canvas.rrect(SCARF, 35, body - 3, 61, body + 3.5, 3, outline=1.2)
    if back:
        canvas.polygon(
            SCARF_SHADE,
            ((45, body), (41 - sway, body + 10), (45 - sway, body + 10), (48, body + 1)),
            outline=0.9,
        )
    else:
        canvas.polygon(
            SCARF_SHADE,
            ((54, body + 1), (60 + sway, body + 12), (56 + sway, body + 13), (51, body + 2)),
            outline=0.9,
        )
    _nova_helmet(canvas, 48, 29 + bob, face="back" if back else "front", blink=blink)


def _nova_side(
    canvas: Canvas,
    *,
    bob: float,
    near_foot: Point,
    far_foot: Point,
    arm_angle: float,
    blink: bool,
    sway: float,
) -> None:
    body = 49 + bob
    hip = (49.0, body + 24)
    # Far limbs sit behind the body in a darker tone.
    canvas.capsule(
        mix(GOLD_SHADE, OUTLINE, 0.25), hip, (far_foot[0], far_foot[1] - 5), 4.0, outline=1.3
    )
    _boot(canvas, far_foot[0], far_foot[1], side=True, shade=True)
    far_hand = (50 - 13 * math.sin(arm_angle), body + 5 + 13 * math.cos(arm_angle))
    canvas.capsule(mix(GOLD_SHADE, OUTLINE, 0.25), (50, body + 5), far_hand, 3.8, outline=1.3)
    canvas.circle(mix(GLOVE, OUTLINE, 0.2), *far_hand, 4.0, outline=1.2)
    # Backpack and bedroll behind Nova.
    canvas.rrect(PACK, 24, body - 1, 41, body + 26, 5, outline=1.4)
    canvas.rrect(PACK_SHADE, 24, body - 1, 41, body + 8, 4)
    canvas.rrect(PACK_SHADE, 26, body + 13, 34, body + 22, 2)
    canvas.circle(ROLL, 31, body - 3, 5.0, outline=1.3)
    canvas.circle(ROLL_SHADE, 31, body - 3, 2.2)
    canvas.capsule(GOLD_SHADE, hip, (near_foot[0], near_foot[1] - 5), 4.2, outline=1.3)
    _boot(canvas, near_foot[0], near_foot[1], side=True, shade=False)
    canvas.rrect(GOLD, 38, body, 61, body + 27, 9, outline=1.5)
    canvas.rrect(GOLD_LIGHT, 41, body + 3, 46, body + 19, 2.5)
    canvas.rrect(GOLD_SHADE, 38, body + 20, 61, body + 27, 6)
    canvas.rrect(BOOT, 38, body + 20, 61, body + 24.5, 1.5)
    canvas.line(PACK_SHADE, (43, body + 1), (42, body + 20), 2.6)
    canvas.rrect(SCARF, 38, body - 3, 60, body + 3.5, 3, outline=1.2)
    canvas.polygon(
        SCARF_SHADE,
        (
            (41, body),
            (29 - sway, body + 4 + sway * 0.5),
            (30 - sway, body + 8 + sway * 0.5),
            (42, body + 3),
        ),
        outline=0.9,
    )
    near_hand = (51 + 13 * math.sin(arm_angle), body + 5 + 13 * math.cos(arm_angle))
    canvas.capsule(GOLD_SHADE, (51, body + 5), near_hand, 4.0, outline=1.3)
    canvas.circle(GLOVE, *near_hand, 4.3, outline=1.2)
    _nova_helmet(canvas, 50, 29 + bob, face="side", blink=blink)


def _nova_frame(row: str, column: str) -> pygame.Surface:
    canvas = Canvas(*NOVA_FRAME)
    kind, _, number = column.partition("-")
    index = int(number) if number else 0
    blink = kind == "blink"
    if kind in ("idle", "blink"):
        bob = IDLE_BOB[index]
        sway = bob * 0.8
        if row == "right":
            _nova_side(
                canvas,
                bob=bob,
                near_foot=(53, 97),
                far_foot=(45, 97),
                arm_angle=0.05,
                blink=blink,
                sway=sway,
            )
        else:
            _nova_front(
                canvas, bob=bob, lift=(0, 0), swing=0, blink=blink, sway=sway, back=row == "up"
            )
        return canvas.finish()
    bob = WALK_BOB[index]
    sway = (1.5, 3.0, 1.5, 3.0)[index]
    if row == "right":
        near, far = (
            ((59, 97), (39, 97)),
            ((47, 97), (53, 92)),
            ((39, 97), (59, 97)),
            ((53, 92), (47, 97)),
        )[index]
        arm = (-0.55, 0.0, 0.55, 0.0)[index]
        _nova_side(
            canvas, bob=bob, near_foot=near, far_foot=far, arm_angle=arm, blink=False, sway=sway
        )
    else:
        lift = ((3.5, 0.0), (0.0, 0.0), (0.0, 3.5), (0.0, 0.0))[index]
        swing = (2.6, 0.0, -2.6, 0.0)[index]
        _nova_front(
            canvas, bob=bob, lift=lift, swing=swing, blink=False, sway=sway, back=row == "up"
        )
    return canvas.finish()


# ---------------------------------------------------------------------------
# Pixel — the class companion robot (stationary in M02)
# ---------------------------------------------------------------------------

PIXEL_ACCENT: Color = (50, 80, 220)
PIXEL_LIGHT: Color = (116, 146, 246)
PIXEL_SHADE: Color = (34, 52, 156)
PIXEL_SCREEN: Color = (14, 20, 44)
PIXEL_EYE: Color = (132, 255, 244)
PIXEL_BULB: Color = (255, 170, 96)
METAL: Color = (172, 182, 204)
TREAD: Color = (50, 54, 70)

PIXEL_FRAME = (100, 100)
PIXEL_COLUMNS = (
    "idle-0",
    "idle-1",
    "idle-2",
    "idle-3",
    "blink",
    "greet-0",
    "greet-1",
    "greet-2",
    "greet-3",
)
PIXEL_ROWS = ("idle",)


def _pixel_frame(column: str) -> pygame.Surface:
    canvas = Canvas(*PIXEL_FRAME)
    kind, _, number = column.partition("-")
    index = int(number) if number else 0
    if kind in ("idle", "blink"):
        lift = (0.0, 0.8, 1.4, 0.8)[index]
        antenna = (-0.2, 0.0, 0.2, 0.0)[index]
        eyes = "closed" if kind == "blink" else "open"
        left_hand, right_hand = (37.0, 76.0), (91.0, 76.0)
    else:
        lift = (-2.0, -4.0, -4.0, -1.0)[index]
        antenna = (0.3, -0.3, 0.3, 0.0)[index]
        eyes = "happy"
        left_hand = (36.0, 74.0 + lift)
        right_hand = ((93.0, 46.0), (97.0, 44.0), (92.0, 44.0), (92.0, 58.0))[index]
    top = 18 + lift
    # Treads stay on the ground; everything above them bobs or hops.
    canvas.rrect(TREAD, 38, 83, 90, 96, 6, outline=1.4)
    for wheel_x in (47, 64, 81):
        canvas.circle(METAL, wheel_x, 89.5, 4.2, outline=1.0)
        canvas.circle(TREAD, wheel_x, 89.5, 1.4)
    body_top = top + 40
    for shoulder, hand in (((45.0, body_top + 7), left_hand), ((83.0, body_top + 7), right_hand)):
        canvas.capsule(METAL, shoulder, hand, 2.6, outline=1.2)
        canvas.circle(PIXEL_LIGHT, *hand, 3.6, outline=1.2)
    canvas.rrect(PIXEL_ACCENT, 44, body_top, 84, min(86.0, body_top + 27), 8, outline=1.4)
    canvas.rrect(PIXEL_LIGHT, 50, body_top + 5, 78, body_top + 21, 4)
    canvas.circle(PIXEL_BULB, 64, body_top + 13, 4.0, outline=1.0)
    canvas.circle(WHITE, 62.8, body_top + 11.8, 1.1)
    tip = (64 + 12 * math.sin(antenna), top - 12 * math.cos(antenna))
    canvas.line(OUTLINE, (64, top + 1), tip, 2.6)
    canvas.circle(PIXEL_BULB, *tip, 4.0, outline=1.2)
    canvas.circle(WHITE, tip[0] - 1.2, tip[1] - 1.2, 1.2)
    canvas.circle(METAL, 37.5, top + 19, 4.6, outline=1.2)
    canvas.circle(METAL, 90.5, top + 19, 4.6, outline=1.2)
    canvas.rrect(PIXEL_ACCENT, 38, top, 90, top + 38, 12, outline=1.6)
    canvas.rrect(PIXEL_LIGHT, 42, top + 3, 60, top + 6, 1.5)
    canvas.rrect(PIXEL_SCREEN, 44, top + 6, 84, top + 32, 8, outline=0.8)
    for eye_x in (55.0, 73.0):
        if eyes == "open":
            canvas.rrect(PIXEL_EYE, eye_x - 4, top + 12, eye_x + 4, top + 23, 3.5)
            canvas.circle(WHITE, eye_x - 1.5, top + 14.5, 1.2)
        elif eyes == "closed":
            canvas.line(PIXEL_EYE, (eye_x - 4, top + 19), (eye_x + 4, top + 19), 2.2)
        else:
            canvas.arc(PIXEL_EYE, eye_x, top + 21, 4.5, math.pi * 1.1, math.pi * 1.9, 2.4)
    if eyes == "happy":
        canvas.arc(PIXEL_EYE, 64, top + 23, 4.0, math.pi * 0.15, math.pi * 0.85, 2.0)
    else:
        canvas.line(PIXEL_EYE, (60.5, top + 27), (67.5, top + 27), 1.8)
    return canvas.finish()


# ---------------------------------------------------------------------------
# Crystal Lantern — the S02 destination (glow and rays are runtime VFX)
# ---------------------------------------------------------------------------

LANTERN_ACCENT: Color = (240, 210, 50)
BRONZE: Color = (150, 96, 44)
BRONZE_DARK: Color = (98, 60, 30)
BRONZE_LIGHT: Color = (212, 150, 78)
LANTERN_CORE: Color = (255, 252, 222)
LANTERN_EMBER: Color = (255, 150, 40)
STONE: Color = (112, 104, 124)
STONE_DARK: Color = (80, 74, 92)

LANTERN_FRAME = (80, 60)
LANTERN_COLUMNS = ("flicker-0", "flicker-1", "flicker-2", "flicker-3")
LANTERN_ROWS = ("glow",)


def _lantern_frame(column: str) -> pygame.Surface:
    canvas = Canvas(*LANTERN_FRAME)
    index = int(column.rpartition("-")[2])
    glass = mix(LANTERN_ACCENT, BRONZE_DARK, 0.35)
    glass_inner = mix(LANTERN_ACCENT, BRONZE, 0.12)
    canvas.rrect(STONE, 25, 51, 55, 58, 2.5, outline=1.2)
    canvas.rrect(STONE_DARK, 25, 55, 55, 58, 1.5)
    canvas.arc(OUTLINE, 40, 8, 4.8, math.pi, math.tau, 2.8)
    canvas.arc(BRONZE_LIGHT, 40, 8, 4.8, math.pi, math.tau, 1.4)
    canvas.polygon(BRONZE, ((29, 16), (51, 16), (46, 9), (34, 9)), outline=1.1)
    canvas.rrect(glass, 30, 15, 50, 46, 3, outline=1.3)
    canvas.rrect(glass_inner, 33, 18, 47, 43, 2)
    width = (6.5, 7.5, 6.0, 7.0)[index]
    height = (12.5, 11.0, 13.5, 12.0)[index]
    lean = (0.0, 0.8, -0.6, 0.3)[index]
    center = (40.0, 31.0)
    canvas.polygon(
        LANTERN_CORE,
        (
            (center[0] + lean, center[1] - height),
            (center[0] + width, center[1]),
            (center[0], center[1] + height * 0.8),
            (center[0] - width, center[1]),
        ),
    )
    canvas.polygon(
        LANTERN_EMBER,
        (
            (center[0] + lean * 0.5, center[1] - height * 0.55),
            (center[0] + width * 0.45, center[1]),
            (center[0], center[1] + height * 0.45),
            (center[0] - width * 0.45, center[1]),
        ),
    )
    canvas.circle(WHITE, center[0], center[1], 1.6)
    for bar_x in (30.0, 50.0):
        canvas.line(BRONZE_DARK, (bar_x, 16), (bar_x, 45), 1.8)
    canvas.rrect(BRONZE, 27, 45, 53, 51, 2, outline=1.1)
    canvas.rrect(BRONZE_LIGHT, 29, 46, 51, 47.5, 0.8)
    canvas.line(WHITE, (32.5, 19), (32.5, 26), 1.2)
    return canvas.finish()


# ---------------------------------------------------------------------------
# Sheet assembly and manifest
# ---------------------------------------------------------------------------

SheetFrame = Callable[[str, str], pygame.Surface]


def _sheet(
    frame_size: tuple[int, int],
    rows: Sequence[str],
    columns: Sequence[str],
    draw: SheetFrame,
) -> pygame.Surface:
    width, height = frame_size
    sheet = pygame.Surface((width * len(columns), height * len(rows)), pygame.SRCALPHA, 32)
    sheet.fill((0, 0, 0, 0))
    for row_index, row in enumerate(rows):
        for column_index, column in enumerate(columns):
            sheet.blit(draw(row, column), (column_index * width, row_index * height))
    return sheet


SHEETS = (
    (
        "characters/nova",
        "characters/nova/nova.png",
        NOVA_FRAME,
        NOVA_ROWS,
        NOVA_COLUMNS,
        NOVA_ACCENT,
        _nova_frame,
    ),
    (
        "characters/pixel",
        "characters/pixel/pixel.png",
        PIXEL_FRAME,
        PIXEL_ROWS,
        PIXEL_COLUMNS,
        PIXEL_ACCENT,
        lambda _row, column: _pixel_frame(column),
    ),
    (
        "objects/crystal-lantern",
        "objects/crystal-lantern/lantern.png",
        LANTERN_FRAME,
        LANTERN_ROWS,
        LANTERN_COLUMNS,
        LANTERN_ACCENT,
        lambda _row, column: _lantern_frame(column),
    ),
)


def build(root: Path = TRUSTED_ROOT) -> dict[str, object]:
    pygame.init()
    try:
        assets: dict[str, object] = {}
        for asset_id, relative, frame, rows, columns, accent, draw in SHEETS:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(_sheet(frame, rows, columns, draw), str(destination))
            assets[asset_id] = {
                "file": relative,
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "frame_width": frame[0],
                "frame_height": frame[1],
                "rows": list(rows),
                "columns": list(columns),
                "accent": list(accent),
            }
        manifest = {
            "schema_version": 1,
            "generator": "scripts/build_trusted_art.py",
            "assets": assets,
        }
        (root / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return manifest
    finally:
        pygame.quit()


def main() -> int:
    manifest = build()
    for asset_id, entry in manifest["assets"].items():  # type: ignore[union-attr]
        print(f"{asset_id}: {entry['file']} sha256={entry['sha256'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
