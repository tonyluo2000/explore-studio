"""Nova V3 (the class reference Explorer) and Pixel V3 (the class companion).

Both are painted with the SDF painter at 4x, lit from the moon (upper right)
with a soft cel shade toward the lower left, a cool rim light, and a dark
navy outline. Frames fill a 100 x 100 cell that maps 1:1 onto the unchanged
100 x 100 gameplay box, so nothing about their geometry changes.

Nova's sheet rows are ``down``, ``up``, and ``right`` (left is mirrored at
runtime). Columns are four idle breaths, a blink, and an eight-frame walk.
Pixel's single ``idle`` row has four idle bobs, a blink, and four greeting
frames.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image

from art.paint import (
    Box,
    Canvas,
    Circle,
    Color,
    Ellipse,
    Poly,
    Segment,
    Shape,
    Stroke,
    Union,
    linear,
    mix,
    radial,
    star_points,
)

SS = 4
LINE: Color = (26, 22, 50)
WHITE: Color = (255, 255, 255)
RIM: Color = (196, 226, 255)
SHADE_OFFSET = (1.6, -2.6)

# ---------------------------------------------------------------------------
# Nova
# ---------------------------------------------------------------------------

NOVA_ACCENT: Color = (255, 200, 50)
SUIT = NOVA_ACCENT
SUIT_SHADE: Color = (214, 136, 36)
SUIT_LIGHT: Color = (255, 234, 150)
HELMET: Color = (244, 246, 255)
HELMET_SHADE: Color = (170, 182, 222)
VISOR_GLASS: Color = (132, 200, 240)
SKIN: Color = (246, 204, 170)
SKIN_SHADE: Color = (222, 164, 136)
EYE: Color = (40, 32, 70)
CHEEK: Color = (255, 138, 150)
SCARF: Color = (244, 72, 96)
SCARF_SHADE: Color = (178, 40, 80)
SCARF_LIGHT: Color = (255, 150, 160)
PACK: Color = (96, 118, 170)
PACK_SHADE: Color = (62, 76, 124)
PACK_LIGHT: Color = (150, 172, 222)
ROLL: Color = (255, 150, 70)
ROLL_SHADE: Color = (204, 96, 48)
BOOT: Color = (112, 72, 60)
BOOT_SHADE: Color = (74, 46, 44)
SOLE: Color = (236, 224, 200)
GLOVE: Color = (246, 246, 252)
GLOVE_SHADE: Color = (180, 188, 214)
BEACON: Color = (255, 96, 86)
BELT: Color = (104, 70, 58)
HAIR: Color = (124, 70, 60)
HAIR_SHADE: Color = (78, 42, 48)
HAIR_LIGHT: Color = (196, 126, 96)
IRIS: Color = (82, 96, 196)
BROW: Color = (92, 52, 50)
MOUTH: Color = (140, 52, 72)
TONGUE: Color = (250, 128, 140)
GLASS_EDGE: Color = (150, 214, 250)
#: The silhouette line: a touch heavier than interior lines so Nova reads
#: cleanly against the busy meadow, even at half scale.
SILHOUETTE: Color = (18, 14, 40)

NOVA_ROWS = ("down", "up", "right")
NOVA_IDLE = ("idle-0", "idle-1", "idle-2", "idle-3")
NOVA_WALK = tuple(f"walk-{index}" for index in range(8))
NOVA_COLUMNS = (*NOVA_IDLE, "blink", *NOVA_WALK)
IDLE_BREATH = (0.0, 0.5, 1.0, 0.5)


def _finish(cv: Canvas) -> Canvas:
    """Seat a cutout in the moonlit scene: soft edges, cool lower shade, rim light.

    Presentation-only: the same 100 x 100 cell, the same pose, the same alpha
    footprint to within an anti-aliased pixel. Nothing here moves a limb.
    """
    ss = cv.ss
    # A heavier outer silhouette than the interior lines (thick-outside, thin-
    # inside), the classic game-sprite read.
    ring = _dilate(cv.a, max(1, round(0.7 * ss)))
    behind = (ring * (1 - cv.a))[..., None]
    cv.rgb = cv.rgb + np.asarray(SILHOUETTE, np.float32) / 255 * behind
    cv.a = cv.a + behind[..., 0]
    soft = cv.blurred(0.42)
    rgb = cv.rgb * 0.62 + soft.rgb * 0.38
    alpha = cv.a * 0.62 + soft.a * 0.38
    height, width = alpha.shape
    ys = (np.arange(height, dtype=np.float32) + 0.5)[:, None] / ss
    xs = (np.arange(width, dtype=np.float32) + 0.5)[None, :] / ss
    # Cooler, deeper toward the feet so the figure sits on the ground.
    low = np.clip((ys - 58) / 40, 0, 1)[..., None]
    rgb = rgb * (1 - low * 0.16 * np.asarray((1.0, 0.75, 0.45), np.float32))
    # Gentle moonlight from the upper right, and a soft cool bounce from below.
    lit = np.clip(1 - np.hypot((xs - 92) / 70, (ys - 8) / 70), 0, 1)[..., None] ** 1.3
    rgb = rgb + np.asarray((0.10, 0.13, 0.22), np.float32) * lit * alpha[..., None] * 0.55
    # A faint rim on the moon side: where alpha falls off toward the upper right.
    shifted = np.roll(np.roll(alpha, 2 * ss, axis=1), -ss, axis=0)
    rim = np.clip(alpha - shifted, 0, 1)[..., None]
    rgb = rgb + np.asarray((0.45, 0.55, 0.85), np.float32) * rim * 0.22
    cv.rgb = np.minimum(rgb, alpha[..., None]).astype(np.float32)
    cv.a = alpha.astype(np.float32)
    return cv


def _dilate(alpha: np.ndarray, radius: int) -> np.ndarray:
    """Grow an alpha mask by *radius* samples with a round kernel."""
    height, width = alpha.shape
    padded = np.pad(alpha, radius)
    grown = alpha.copy()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                window = padded[
                    radius + dy : radius + dy + height, radius + dx : radius + dx + width
                ]
                grown = np.maximum(grown, window)
    return grown


def _part(  # type: ignore[no-untyped-def]
    cv: Canvas,
    shape: Shape,
    fill,
    *,
    line: float = 1.1,
    shade: Color | None = None,
    rim: bool = True,
) -> None:
    cv.part(
        shape,
        fill,
        line=LINE if line else None,
        line_width=line,
        shade=shade,
        shade_offset=SHADE_OFFSET,
        shade_alpha=0.9,
        rim=RIM if rim else None,
        rim_alpha=0.55,
    )


def _boot(cv: Canvas, x: float, bottom: float, *, side: bool, far: bool = False) -> None:
    color = mix(BOOT, LINE, 0.3) if far else BOOT
    if side:
        shape = Union(
            Box(x - 5, bottom - 8, x + 3, bottom, 3), Ellipse(x + 3, bottom - 3, 5.5, 3.2), smooth=2
        )
    else:
        shape = Box(x - 5.5, bottom - 8.5, x + 5.5, bottom, 3.5)
    _part(cv, shape, color, shade=BOOT_SHADE)
    sole = shape & Box(x - 12, bottom - 2.2, x + 12, bottom + 1)
    cv.paint(sole, SOLE)
    cv.paint(
        Box(x - 3.5, bottom - 7.5, x + (1.5 if side else 3.5), bottom - 6, 0.8),
        mix(color, WHITE, 0.3),
        alpha=0.6,
        clip=shape,
    )


def _glove(cv: Canvas, x: float, y: float, *, far: bool = False) -> None:
    _part(cv, Circle(x, y, 4.1), mix(GLOVE, LINE, 0.2) if far else GLOVE, shade=GLOVE_SHADE)


def _limb(cv: Canvas, start, end, radius: float, *, far: bool = False, knee=None) -> None:  # type: ignore[no-untyped-def]
    color = mix(SUIT_SHADE, LINE, 0.28) if far else SUIT_SHADE
    points = [start, knee, end] if knee is not None else [start, end]
    shape = Stroke(points, radius, radius * 0.92)
    _part(cv, shape, color, shade=mix(color, LINE, 0.3), rim=not far)


def _star_badge(cv: Canvas, x: float, y: float, size: float) -> None:
    badge = Poly(star_points(x, y, size, size * 0.45, 5))
    cv.paint(badge.grow(0.8), LINE)
    cv.paint(badge, WHITE)
    cv.paint(badge - badge.shift(0.6, -0.8), (200, 214, 255), alpha=0.8, clip=badge)


def _nova_helmet(cv: Canvas, cx: float, cy: float, *, face: str, blink: bool) -> None:
    """Helmet with a clear visor over Nova's face (``front``/``side``/``back``)."""
    r = 22.5
    shell = Circle(cx, cy, r)
    # Antenna and beacon behind the shell.
    base = (cx - 12, cy - 17) if face != "side" else (cx - 8, cy - 19)
    tip = (base[0] - 5, base[1] - 9)
    cv.paint(Segment(base, tip, 1.5).grow(0.9), LINE)
    cv.paint(Segment(base, tip, 1.1), (150, 160, 196))
    cv.paint(Circle(*tip, 4.2), (255, 160, 140), alpha=0.25)
    _part(cv, Circle(*tip, 3.1), BEACON, shade=(196, 50, 60))
    cv.paint(Circle(tip[0] - 0.9, tip[1] - 1.0, 1.0), WHITE)
    if face == "front":
        for side in (-1, 1):
            pod = Box(cx + side * 25 - 4, cy - 6, cx + side * 25 + 4, cy + 9, 3.5)
            _part(cv, pod, SUIT, shade=SUIT_SHADE)
    _part(
        cv,
        shell,
        radial(cx + 8, cy - 10, r * 1.9, ((0, WHITE), (0.55, HELMET), (1, HELMET_SHADE))),
        line=1.4,
        shade=HELMET_SHADE,
    )
    cv.paint(Ellipse(cx - 9, cy - 13, 4.5, 2.6), WHITE, alpha=0.9)
    if face == "front":
        visor = Ellipse(cx, cy + 2.5, 17, 14.5)
        cv.paint(visor.grow(1.3), LINE)
        cv.paint(visor, radial(cx, cy + 6, 18, ((0, SKIN), (1, SKIN_SHADE))))
        cv.paint(visor - visor.shift(1.5, 3), (190, 120, 110), alpha=0.35, feather=1.2, clip=visor)
        _nova_face(cv, cx, cy, visor, blink=blink)
        _nova_glass(cv, visor, cx, cy)
        # Gold collar ring.
        collar = Ellipse(cx, cy + r - 1.5, 14, 3.8)
        _part(cv, collar, SUIT, shade=SUIT_SHADE, line=1.0)
    elif face == "side":
        pod = Box(cx - 9, cy - 5, cx - 1, cy + 9, 3.5)
        _part(cv, pod, SUIT, shade=SUIT_SHADE)
        cv.paint(Circle(cx - 5, cy + 2, 1.6), SUIT_LIGHT)
        visor = Ellipse(cx + 11, cy + 2.5, 11.5, 13.5)
        cv.paint(visor.grow(1.3) & shell.grow(1.4), LINE)
        visor_in = visor & shell
        cv.paint(visor_in, radial(cx + 12, cy + 6, 16, ((0, SKIN), (1, SKIN_SHADE))))
        _nova_side_face(cv, cx, cy, visor_in, blink=blink)
        _nova_glass(cv, visor_in, cx + 8, cy)
        collar = Ellipse(cx + 1, cy + r - 1.5, 12.5, 3.6)
        _part(cv, collar, SUIT, shade=SUIT_SHADE, line=1.0)
    else:
        for side in (-1, 1):
            pod = Box(cx + side * 25 - 4, cy - 6, cx + side * 25 + 4, cy + 9, 3.5)
            _part(cv, pod, SUIT, shade=SUIT_SHADE)
        stripe = Box(cx - 2.6, cy - r - 1, cx + 2.6, cy + r, 2.6)
        cv.paint(stripe, SUIT, clip=shell)
        cv.paint(stripe - stripe.shift(1.0, 0), SUIT_SHADE, alpha=0.9, clip=shell & stripe)
        for rivet_y in (cy - 8, cy + 2, cy + 12):
            cv.paint(Circle(cx + 9, rivet_y, 1.0), HELMET_SHADE, clip=shell)
            cv.paint(Circle(cx - 9, rivet_y, 1.0), HELMET_SHADE, clip=shell)
        collar = Ellipse(cx, cy + r - 1.5, 14, 3.8)
        _part(cv, collar, SUIT, shade=SUIT_SHADE, line=1.0)


def _eye(cv: Canvas, ex: float, ey: float, rx: float, ry: float, *, blink: bool) -> None:
    """A big, glossy cartoon eye (or a happy closed arc when blinking)."""
    if blink:
        cv.paint(Stroke([(ex - rx - 0.4, ey), (ex, ey + 1.6), (ex + rx + 0.4, ey)], 0.95), EYE)
        return
    eye = Ellipse(ex, ey, rx, ry)
    cv.paint(eye, EYE)
    cv.paint(Ellipse(ex, ey + ry * 0.42, rx * 0.8, ry * 0.5), IRIS, clip=eye)
    cv.paint(Ellipse(ex, ey + ry * 0.62, rx * 0.5, ry * 0.26), (150, 170, 255), clip=eye)
    cv.paint(Circle(ex + rx * 0.3, ey - ry * 0.38, rx * 0.44), WHITE)
    cv.paint(Circle(ex - rx * 0.36, ey + ry * 0.42, rx * 0.2), WHITE, alpha=0.9)


def _hair(cv: Canvas, visor: Shape, points: list[tuple[float, float]], top: float) -> None:
    """A soft fringe of bangs inside the visor: Nova's own personality."""
    fringe = Union(
        Box(points[0][0] - 4, top - 12, points[-1][0] + 4, top + 1.5, 2),
        Poly(points),
        smooth=1.2,
    )
    hair = fringe & visor
    cv.paint(hair.grow(0.55) & visor, HAIR_SHADE)
    cv.paint(hair, HAIR)
    cv.paint(hair - hair.shift(-1.2, -1.6), HAIR_SHADE, alpha=0.75, feather=0.4, clip=hair)
    cv.paint(
        Stroke([(points[0][0] + 4, top - 1.5), (points[-1][0] - 6, top - 3.4)], 0.9, 0.4),
        HAIR_LIGHT,
        alpha=0.8,
        clip=hair,
    )


def _nova_face(cv: Canvas, cx: float, cy: float, visor: Shape, *, blink: bool) -> None:
    top = cy - 6.5
    _hair(
        cv,
        visor,
        [
            (cx - 17, top),
            (cx - 12, top + 4.6),
            (cx - 9, top + 0.8),
            (cx - 4.5, top + 5.6),
            (cx - 1, top + 1.0),
            (cx + 4, top + 4.4),
            (cx + 7, top + 0.6),
            (cx + 11.5, top + 3.8),
            (cx + 17, top - 1),
        ],
        top,
    )
    for side in (-1, 1):
        ex = cx + side * 6.8
        # Soft, raised arches: curious and friendly.
        cv.paint(
            Stroke([(ex - 2.5, cy - 1.9), (ex - 0.2 * side, cy - 3.1), (ex + 2.5, cy - 2.0)], 0.6),
            BROW,
            alpha=0.85,
        )
        _eye(cv, ex, cy + 3.0, 3.1, 4.2, blink=blink)
        cv.paint(Ellipse(ex + side * 2.6, cy + 8.6, 2.8, 1.5), CHEEK, alpha=0.7)
    mouth = Ellipse(cx, cy + 9.6, 2.7, 2.2) & Box(cx - 4, cy + 9.4, cx + 4, cy + 13)
    cv.paint(mouth.grow(0.45), MOUTH)
    cv.paint(mouth, (110, 34, 56))
    cv.paint(Ellipse(cx, cy + 11.2, 1.7, 0.9), TONGUE, clip=mouth)


def _nova_side_face(cv: Canvas, cx: float, cy: float, visor: Shape, *, blink: bool) -> None:
    top = cy - 6.5
    _hair(
        cv,
        visor,
        [
            (cx - 2, top - 2),
            (cx + 5, top + 4.6),
            (cx + 8.5, top + 0.6),
            (cx + 12.5, top + 5.2),
            (cx + 16, top + 1.2),
            (cx + 21, top + 3.2),
            (cx + 24, top - 2),
        ],
        top,
    )
    ex = cx + 15.0
    cv.paint(
        Stroke([(ex - 2.3, cy - 1.9), (ex, cy - 3.0), (ex + 2.2, cy - 2.1)], 0.6), BROW, alpha=0.85
    )
    _eye(cv, ex, cy + 3.0, 2.6, 4.1, blink=blink)
    cv.paint(Ellipse(ex - 3.2, cy + 8.6, 2.6, 1.5), CHEEK, alpha=0.7)
    mouth = Ellipse(ex + 3.6, cy + 9.6, 1.8, 1.7) & Box(ex, cy + 9.4, ex + 8, cy + 13)
    cv.paint(mouth.grow(0.45) & visor, MOUTH)
    cv.paint(mouth & visor, (110, 34, 56))


def _nova_glass(cv: Canvas, visor: Shape, cx: float, cy: float) -> None:
    """Glass over the face: a sky-tinted top, a crisp edge, and moon glints."""
    cv.paint(visor, VISOR_GLASS, alpha=0.12)
    cv.paint(
        visor & Box(cx - 30, cy - 30, cx + 30, cy - 4),
        (190, 228, 255),
        alpha=0.16,
        feather=2.5,
    )
    cv.paint(visor - visor.grow(-1.1), GLASS_EDGE, alpha=0.55, clip=visor)
    cv.paint(visor - visor.shift(-2, 2.5), (210, 240, 255), alpha=0.5, feather=0.6, clip=visor)
    cv.paint(
        Stroke([(cx - 12, cy - 2), (cx - 8.5, cy - 8)], 1.5, 0.9), WHITE, alpha=0.8, clip=visor
    )
    cv.paint(Circle(cx - 13, cy + 2.2, 0.95), WHITE, alpha=0.7, clip=visor)
    # The moon's small reflection on the upper right of the glass.
    cv.paint(Ellipse(cx + 10.5, cy - 4.5, 1.9, 1.3), WHITE, alpha=0.85, clip=visor)


def _scarf_front(cv: Canvas, cx: float, top: float, sway: float, *, back: bool) -> None:
    band = Box(cx - 13, top - 3, cx + 13, top + 3.8, 3)
    _part(cv, band, SCARF, shade=SCARF_SHADE)
    cv.paint(
        Stroke([(cx - 11, top - 1.2), (cx + 11, top - 1.2)], 0.7), SCARF_LIGHT, alpha=0.8, clip=band
    )
    if back:
        tail = Stroke(
            [(cx - 2, top + 2), (cx - 5 - sway * 0.5, top + 9), (cx - 3 - sway, top + 15)], 3.0, 2.2
        )
    else:
        tail = Stroke(
            [(cx + 7, top + 2), (cx + 10 + sway * 0.5, top + 8), (cx + 9 + sway, top + 14)],
            2.8,
            2.1,
        )
    _part(cv, tail, SCARF, shade=SCARF_SHADE, line=1.0)
    end = tail.segments[-1].p1
    cv.paint(Segment((end[0] - 2.2, end[1] + 1.6), (end[0] + 2.2, end[1] + 1.6), 0.6), SCARF_LIGHT)


def _nova_front(
    cv: Canvas,
    *,
    bob: float,
    lift: tuple[float, float],
    swing: float,
    sway_x: float,
    blink: bool,
    scarf: float,
    back: bool,
) -> None:
    cx = 50 + sway_x
    body = 57 + bob
    hips = body + 22
    # Legs and boots first (they sit behind the torso).
    for side, leg_lift in zip((-1, 1), lift, strict=True):
        lx = 50 + side * 6.5
        foot_y = 97 - leg_lift
        _limb(cv, (cx + side * 6, hips), (lx, foot_y - 6), 3.9)
        _boot(cv, lx, foot_y, side=False)
    if not back:
        # Backpack edges peek out behind the shoulders.
        pack = Box(cx - 18, body - 1, cx + 18, body + 21, 6)
        _part(cv, pack, PACK, shade=PACK_SHADE)
    for side, hand_dy in ((-1, swing), (1, -swing)):
        shoulder = (cx + side * 13, body + 4)
        hand = (cx + side * 18.5, body + 19 + hand_dy)
        elbow = (cx + side * 18, body + 11 + hand_dy * 0.4)
        _limb(cv, shoulder, hand, 3.6, knee=elbow)
        _glove(cv, *hand)
    torso = Box(cx - 14, body, cx + 14, hips + 2, 9)
    _part(
        cv,
        torso,
        linear((cx + 10, body), (cx - 10, hips), ((0, SUIT_LIGHT), (0.35, SUIT), (1, SUIT_SHADE))),
        line=1.3,
        shade=SUIT_SHADE,
    )
    # Contact shade under the helmet and above the belt seats the parts together.
    cv.paint(Ellipse(cx, body + 1.5, 13, 4.5), LINE, alpha=0.32, feather=1.6, clip=torso)
    belt = Box(cx - 14, hips - 5, cx + 14, hips - 0.5, 1.5) & torso
    cv.paint(belt, BELT)
    if back:
        pack = Box(cx - 16, body - 1, cx + 16, hips - 1, 7)
        _part(
            cv,
            pack,
            linear(
                (cx + 12, body), (cx - 12, hips), ((0, PACK_LIGHT), (0.4, PACK), (1, PACK_SHADE))
            ),
            line=1.3,
            shade=PACK_SHADE,
        )
        flap = Box(cx - 13, body + 3, cx + 13, body + 12, 4)
        _part(cv, flap, PACK_LIGHT, line=0.9, shade=PACK, rim=False)
        for buckle in (-7, 7):
            cv.paint(
                Box(cx + buckle - 1.6, body + 9, cx + buckle + 1.6, body + 14, 0.8), SUIT_LIGHT
            )
        roll = Box(cx - 17, hips - 5, cx + 17, hips + 3, 4)
        _part(cv, roll, ROLL, shade=ROLL_SHADE)
        for strap in (-9, 9):
            cv.paint(Segment((cx + strap, hips - 5), (cx + strap, hips + 3), 0.9), ROLL_SHADE)
    else:
        for strap in (-7.5, 7.5):
            cv.paint(
                Segment((cx + strap, body + 0.5), (cx + strap * 1.05, hips - 5), 1.2),
                PACK_SHADE,
                alpha=0.6,
                clip=torso,
            )
        _star_badge(cv, cx, body + 11, 4.4)
        buckle = Box(cx - 3, hips - 5.5, cx + 3, hips, 1)
        _part(cv, buckle, SUIT_LIGHT, line=0.8, rim=False)
    _scarf_front(cv, cx, body, scarf, back=back)
    _nova_helmet(cv, cx, 33 + bob, face="back" if back else "front", blink=blink)


def _nova_side(
    cv: Canvas,
    *,
    bob: float,
    near: tuple[float, float, float],
    far: tuple[float, float, float],
    arm: float,
    blink: bool,
    scarf: float,
    lean: float = 0.0,
) -> None:
    """Side view facing right. ``near``/``far`` are (foot x, lift, knee push).

    ``lean`` tips the upper body forward (pixels at the helmet) while walking.
    """
    cx = 50
    body = 57 + bob
    hips = body + 22
    hip = (cx, hips - 1)
    # Far leg and arm behind everything, darker.
    fx, flift, fknee = far
    foot = (fx, 97 - flift)
    knee = ((hip[0] + fx) / 2 + fknee, (hip[1] + foot[1] - 6) / 2)
    _limb(cv, hip, (fx, foot[1] - 6), 3.7, far=True, knee=knee)
    _boot(cv, fx, foot[1], side=True, far=True)
    shoulder = (cx + 1, body + 5)
    far_hand = (shoulder[0] - 13 * math.sin(arm), shoulder[1] + 13 * math.cos(arm))
    _limb(cv, shoulder, far_hand, 3.4, far=True)
    _glove(cv, *far_hand, far=True)
    # Backpack and bedroll behind Nova.
    pack = Box(cx - 22, body - 1, cx - 6, hips + 1, 5)
    _part(
        cv,
        pack,
        linear((cx - 6, body), (cx - 22, hips), ((0, PACK_LIGHT), (0.4, PACK), (1, PACK_SHADE))),
        line=1.3,
        shade=PACK_SHADE,
    )
    cv.paint(Box(cx - 20, body + 10, cx - 12, hips - 3, 2), PACK_SHADE)
    roll = Circle(cx - 14, body - 3, 5.2)
    _part(cv, roll, ROLL, shade=ROLL_SHADE)
    cv.paint(Circle(cx - 14, body - 3, 2.2), ROLL_SHADE)
    # Scarf tail streams behind.
    tail = Stroke(
        [
            (cx - 6, body + 1),
            (cx - 14 - scarf * 0.6, body + 3 + scarf * 0.3),
            (cx - 22 - scarf, body + 6 + scarf * 0.6),
        ],
        2.8,
        1.9,
    )
    _part(cv, tail, SCARF, shade=SCARF_SHADE, line=1.0)
    # Near leg.
    nx, nlift, nknee = near
    foot = (nx, 97 - nlift)
    knee = ((hip[0] + nx) / 2 + nknee, (hip[1] + foot[1] - 6) / 2)
    _limb(cv, hip, (nx, foot[1] - 6), 3.9, knee=knee)
    _boot(cv, nx, foot[1], side=True)
    torso = Box(cx - 11, body, cx + 12, hips + 2, 9)
    _part(
        cv,
        torso,
        linear((cx + 10, body), (cx - 8, hips), ((0, SUIT_LIGHT), (0.35, SUIT), (1, SUIT_SHADE))),
        line=1.3,
        shade=SUIT_SHADE,
    )
    cv.paint(Ellipse(cx + 1, body + 1.5, 11, 4.2), LINE, alpha=0.32, feather=1.6, clip=torso)
    cv.paint(Box(cx - 11, hips - 5, cx + 12, hips - 0.5, 1.5) & torso, BELT)
    cv.paint(Segment((cx - 5, body + 1), (cx - 4, hips - 5), 1.4), PACK_SHADE, clip=torso)
    _star_badge(cv, cx + 5, body + 10, 3.4)
    band = Box(cx - 11, body - 3, cx + 12, body + 3.8, 3)
    _part(cv, band, SCARF, shade=SCARF_SHADE)
    cv.paint(
        Stroke([(cx - 9, body - 1.2), (cx + 10, body - 1.2)], 0.7),
        SCARF_LIGHT,
        alpha=0.8,
        clip=band,
    )
    near_hand = (shoulder[0] + 13 * math.sin(arm), shoulder[1] + 13 * math.cos(arm))
    elbow = (shoulder[0] + 6 * math.sin(arm) + 1.5, shoulder[1] + 6.5 * math.cos(arm))
    _limb(cv, shoulder, near_hand, 3.6, knee=elbow)
    _glove(cv, *near_hand)
    _nova_helmet(cv, cx + 1 + lean, 33 + bob, face="side", blink=blink)


def nova_frame(row: str, column: str) -> Image.Image:
    cv = Canvas(100, 100, SS)
    kind, _, number = column.partition("-")
    index = int(number) if number else 0
    if kind in ("idle", "blink"):
        breath = IDLE_BREATH[index] if kind == "idle" else 0.0
        scarf = (0.0, 0.6, 1.2, 0.6)[index] if kind == "idle" else 0.0
        if row == "right":
            _nova_side(
                cv,
                bob=breath,
                near=(54, 0, 1.0),
                far=(45, 0, 1.0),
                arm=0.08,
                blink=kind == "blink",
                scarf=scarf,
            )
        else:
            _nova_front(
                cv,
                bob=breath,
                lift=(0, 0),
                swing=0,
                sway_x=0,
                blink=kind == "blink",
                scarf=scarf,
                back=row == "up",
            )
        return _finish(cv).image()
    phase = index / 8 * math.tau
    s, c = math.sin(phase), math.cos(phase)
    scarf = 3.0 + 2.0 * math.sin(phase * 2)
    if row == "right":
        # Up on the passing pose, down on contact: a springy, eager step.
        bob = 2.0 * abs(s) - 0.4
        near = (50 + 12 * s, 4.6 * max(0.0, c), 2.5 + 3.4 * max(0.0, c))
        far = (50 - 12 * s, 4.6 * max(0.0, -c), 2.5 + 3.4 * max(0.0, -c))
        _nova_side(
            cv, bob=bob, near=near, far=far, arm=-0.82 * s, blink=False, scarf=scarf, lean=1.6
        )
    else:
        bob = 1.8 * (1 - abs(s)) - 0.3
        lift = (4.8 * max(0.0, s), 4.8 * max(0.0, -s))
        _nova_front(
            cv,
            bob=bob,
            lift=lift,
            swing=4.0 * s,
            sway_x=1.0 * s,
            blink=False,
            scarf=scarf * 0.6,
            back=row == "up",
        )
    return _finish(cv).image()


# ---------------------------------------------------------------------------
# Pixel
# ---------------------------------------------------------------------------

PIXEL_ACCENT: Color = (50, 80, 220)
P_BODY = PIXEL_ACCENT
P_LIGHT: Color = (122, 156, 255)
P_SHADE: Color = (30, 46, 150)
P_SCREEN: Color = (12, 18, 46)
P_EYE: Color = (120, 255, 236)
P_BULB: Color = (255, 176, 90)
P_METAL: Color = (182, 192, 216)
P_METAL_SHADE: Color = (116, 126, 160)
P_TREAD: Color = (48, 50, 72)
P_CHEEK: Color = (255, 120, 170)

PIXEL_ROWS = ("idle",)
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


def _pixel_eyes(cv: Canvas, cx: float, cy: float, mood: str, screen: Shape) -> None:
    for ex in (cx - 8, cx + 8):
        if mood == "open":
            eye = Box(ex - 3.6, cy - 6, ex + 3.6, cy + 5, 3.4)
            cv.paint(eye.grow(2.2), P_EYE, alpha=0.18, clip=screen)
            cv.paint(eye, P_EYE)
            cv.paint(Box(ex - 3.6, cy + 1.5, ex + 3.6, cy + 5, 3.2), (70, 200, 214), clip=eye)
            cv.paint(Circle(ex - 1.2, cy - 3.2, 1.3), WHITE)
        elif mood == "closed":
            cv.paint(Stroke([(ex - 3.8, cy + 1), (ex, cy + 2.6), (ex + 3.8, cy + 1)], 1.1), P_EYE)
        else:
            cv.paint(Stroke([(ex - 4, cy + 1.5), (ex, cy - 2.8), (ex + 4, cy + 1.5)], 1.3), P_EYE)
    cv.paint(Ellipse(cx - 13, cy + 7, 2.8, 1.5), P_CHEEK, alpha=0.8, clip=screen)
    cv.paint(Ellipse(cx + 13, cy + 7, 2.8, 1.5), P_CHEEK, alpha=0.8, clip=screen)
    if mood == "happy":
        mouth = Ellipse(cx, cy + 8, 3.6, 3.0) & Box(cx - 5, cy + 8, cx + 5, cy + 12)
        cv.paint(mouth, P_EYE)
        cv.paint(Ellipse(cx, cy + 10.5, 1.8, 1.0), (255, 140, 170), clip=mouth)
    else:
        cv.paint(Stroke([(cx - 2.6, cy + 8), (cx, cy + 9.4), (cx + 2.6, cy + 8)], 0.8), P_EYE)


def pixel_frame(column: str) -> Image.Image:
    cv = Canvas(100, 100, SS)
    kind, _, number = column.partition("-")
    index = int(number) if number else 0
    cx = 65.0
    if kind in ("idle", "blink"):
        lift = (0.0, 0.7, 1.3, 0.7)[index] if kind == "idle" else 0.0
        antenna = (-0.12, 0.0, 0.12, 0.0)[index] if kind == "idle" else 0.0
        mood = "closed" if kind == "blink" else "open"
        left_hand = (cx - 21, 76.0 + lift * 0.5)
        right_hand = (cx + 21, 76.0 + lift * 0.5)
    else:
        lift = (-2.0, -4.5, -4.5, -1.0)[index]
        antenna = (0.3, -0.35, 0.35, 0.0)[index]
        mood = "happy"
        left_hand = (cx - 21, 72.0 + lift)
        right_hand = (
            (cx + 27, 46.0),
            (cx + 31, 40.0 + lift * 0.3),
            (cx + 24, 40.0 + lift * 0.3),
            (cx + 24, 60.0),
        )[index]
    top = 17 + lift
    # Treads stay planted; everything above them bobs or hops.
    tread = Box(cx - 24, 83, cx + 24, 97, 7)
    _part(cv, tread, P_TREAD, shade=(26, 28, 44))
    cv.paint(Box(cx - 22, 84, cx + 22, 86.5, 1.2), (90, 94, 124), clip=tread)
    for wheel_x in (cx - 14, cx, cx + 14):
        _part(cv, Circle(wheel_x, 90.5, 4.4), P_METAL, shade=P_METAL_SHADE, line=0.9)
        cv.paint(Circle(wheel_x, 90.5, 1.6), P_TREAD)
    for tooth in range(9):
        tx = cx - 20 + tooth * 5
        cv.paint(Segment((tx, 95.2), (tx + 1.5, 95.2), 0.7), (86, 90, 118))
    body_top = top + 42
    body = Box(cx - 17, body_top, cx + 17, min(86.0, body_top + 25), 8)
    for shoulder, hand in (
        ((cx - 14, body_top + 7), left_hand),
        ((cx + 14, body_top + 7), right_hand),
    ):
        arm = Segment(shoulder, hand, 2.3)
        _part(cv, arm, P_METAL, shade=P_METAL_SHADE, line=1.0)
        _part(cv, Circle(*hand, 4.0), P_LIGHT, shade=P_SHADE, line=1.0)
    cv.paint(Box(cx - 4, top + 36, cx + 4, body_top + 2, 1.5).grow(0.9), LINE)
    cv.paint(Box(cx - 4, top + 36, cx + 4, body_top + 2, 1.5), P_METAL_SHADE)
    _part(
        cv,
        body,
        linear(
            (cx + 12, body_top),
            (cx - 12, body_top + 25),
            ((0, P_LIGHT), (0.4, P_BODY), (1, P_SHADE)),
        ),
        line=1.3,
        shade=P_SHADE,
    )
    panel = Box(cx - 11, body_top + 4, cx + 11, body_top + 18, 4)
    cv.paint(panel, (214, 226, 255))
    cv.paint(panel - panel.shift(1, -2), (160, 176, 226), alpha=0.8, clip=panel)
    heart = Union(
        Circle(cx - 2, body_top + 9.5, 2.5),
        Circle(cx + 2, body_top + 9.5, 2.5),
        Poly([(cx - 4.4, body_top + 10.5), (cx + 4.4, body_top + 10.5), (cx, body_top + 15)]),
    )
    cv.paint(heart, (255, 110, 150))
    cv.paint(Circle(cx - 2.6, body_top + 8.6, 0.9), WHITE)
    # Antenna with a glowing bulb.
    tip = (cx + 13 * math.sin(antenna), top - 12 * math.cos(antenna))
    cv.paint(Segment((cx, top + 1), tip, 1.1).grow(0.9), LINE)
    cv.paint(Segment((cx, top + 1), tip, 1.1), P_METAL)
    cv.paint(Circle(*tip, 7), P_BULB, alpha=0.18)
    _part(cv, Circle(*tip, 4.0), P_BULB, shade=(214, 110, 50))
    cv.paint(Circle(tip[0] - 1.3, tip[1] - 1.3, 1.3), WHITE)
    # Ear discs.
    for side in (-1, 1):
        ear = Circle(cx + side * 26, top + 19, 5.2)
        _part(cv, ear, P_METAL, shade=P_METAL_SHADE)
        cv.paint(Circle(cx + side * 26, top + 19, 2.3), P_LIGHT)
    head = Box(cx - 25, top, cx + 25, top + 37, 13)
    _part(
        cv,
        head,
        linear((cx + 20, top), (cx - 20, top + 37), ((0, P_LIGHT), (0.35, P_BODY), (1, P_SHADE))),
        line=1.5,
        shade=P_SHADE,
    )
    cv.paint(
        Stroke([(cx - 16, top + 3.2), (cx - 4, top + 3.2)], 1.2),
        (200, 214, 255),
        alpha=0.9,
        clip=head,
    )
    screen = Box(cx - 19.5, top + 6, cx + 19.5, top + 31, 9)
    cv.paint(screen.grow(1.0), LINE)
    cv.paint(screen, radial(cx, top + 16, 28, ((0, (26, 38, 86)), (1, P_SCREEN))))
    for line_y in range(int(top + 8), int(top + 31), 3):
        cv.paint(
            Segment((cx - 19, line_y), (cx + 19, line_y), 0.25),
            (40, 60, 110),
            alpha=0.5,
            clip=screen,
        )
    _pixel_eyes(cv, cx, top + 17, mood, screen)
    cv.paint(
        Stroke([(cx - 15, top + 10), (cx - 10, top + 8)], 1.0, 0.6), WHITE, alpha=0.45, clip=screen
    )
    return _finish(cv).image()


# ---------------------------------------------------------------------------
# Moonlit Guide
# ---------------------------------------------------------------------------

#: The canonical S04 Guide is ``color: "blue"``; this sheet is drawn only for it.
GUIDE_ACCENT: Color = (50, 80, 220)
G_CLOAK: Color = (58, 82, 196)
G_CLOAK_LIGHT: Color = (116, 146, 246)
G_CLOAK_SHADE: Color = (30, 38, 118)
G_LINING: Color = (150, 120, 214)
G_LINING_SHADE: Color = (100, 74, 168)
G_ROBE: Color = (226, 222, 246)
G_ROBE_SHADE: Color = (168, 162, 210)
G_TRIM: Color = (246, 214, 128)
G_TRIM_SHADE: Color = (196, 146, 70)
G_STAR: Color = (255, 236, 170)
G_HAIR: Color = (240, 240, 250)
G_HAIR_SHADE: Color = (176, 180, 212)
G_SKIN: Color = (240, 196, 164)
G_SKIN_SHADE: Color = (214, 156, 130)
G_STAFF: Color = (150, 100, 70)
G_STAFF_SHADE: Color = (96, 60, 48)
G_STAFF_LIGHT: Color = (204, 150, 104)
G_MOON: Color = (255, 226, 140)
G_MOON_SHADE: Color = (214, 160, 70)
G_ORB: Color = (214, 244, 255)
G_ORB_CORE: Color = (255, 255, 255)
G_ORB_GLOW: Color = (140, 214, 255)
G_SHOE: Color = (70, 52, 70)

GUIDE_ROWS = ("idle",)
GUIDE_IDLE = ("idle-0", "idle-1", "idle-2", "idle-3")
GUIDE_TALK = ("talk-0", "talk-1", "talk-2", "talk-3")
GUIDE_COLUMNS = (*GUIDE_IDLE, "blink", *GUIDE_TALK)
#: Where the staff's moon orb sits in the 100 x 100 cell; the runtime glow
#: and the half-scale anchor tests use the same fractions.
GUIDE_ORB = (24.0, 19.0)
#: (breath, hood-tip sway, hem sway) for the four idle frames.
_GUIDE_IDLE_MOTION = ((0.0, 0.0, 0.0), (0.5, 0.6, 0.5), (1.0, 1.2, 1.0), (0.5, 0.6, 0.5))
#: (raised hand x, y, mouth open) for the four talk frames: lift, open, wave, settle.
_GUIDE_TALK_HANDS = ((78.0, 60.0, 0.6), (82.0, 50.0, 1.0), (84.0, 46.0, 0.5), (80.0, 55.0, 0.8))


def _guide_staff(cv: Canvas, *, lift: float) -> None:
    """A gnarled staff topped by a crescent moon cradling a glowing orb."""
    ox, oy = GUIDE_ORB
    oy += lift
    shaft = Stroke([(27.5, 97.0), (25.5, 70.0), (26.5, 46.0), (24.5, oy + 9.0)], 1.9, 1.6)
    _part(cv, shaft, G_STAFF, shade=G_STAFF_SHADE)
    cv.paint(
        Stroke([(26.3, 92.0), (24.9, 70.0), (25.8, 48.0)], 0.45),
        G_STAFF_LIGHT,
        alpha=0.7,
        clip=shaft,
    )
    # A small knot and a curl of leaf: a walking stick, not a weapon.
    _part(cv, Circle(25.9, 62.0, 2.3), G_STAFF, shade=G_STAFF_SHADE, line=0.9)
    leaf = Ellipse(30.5, 66.0, 3.4, 1.6)
    _part(cv, leaf, (120, 196, 150), shade=(70, 140, 110), line=0.8, rim=False)
    # The crescent moon cradle, opening up and right toward the real moon.
    crescent = Circle(ox, oy + 1.0, 8.6) - Circle(ox + 3.4, oy - 2.6, 8.0)
    cv.paint(Circle(ox, oy, 13.0), G_ORB_GLOW, alpha=0.22, feather=5.0)
    _part(cv, crescent, G_MOON, shade=G_MOON_SHADE, line=1.0)
    orb = Circle(ox + 1.6, oy - 1.4, 5.2)
    cv.paint(orb.grow(1.0), LINE)
    cv.paint(
        orb, radial(ox + 0.4, oy - 2.6, 6.4, ((0, G_ORB_CORE), (0.55, G_ORB), (1, G_ORB_GLOW)))
    )
    cv.paint(Circle(ox - 0.2, oy - 3.4, 1.5), WHITE, alpha=0.95)
    cv.paint(
        Poly(star_points(ox + 9.5, oy - 8.5, 2.4, 0.8, 4)),
        G_ORB_CORE,
        alpha=0.9,
    )


def _guide_stars(cv: Canvas, cloak: Shape) -> None:
    """A scatter of tiny embroidered stars on the cloak."""
    for sx, sy, size in (
        (40.0, 66.0, 1.9),
        (70.0, 70.0, 2.1),
        (36.0, 84.0, 1.6),
        (74.0, 87.0, 1.8),
        (63.0, 79.0, 1.3),
        (45.0, 76.0, 1.2),
    ):
        cv.paint(Poly(star_points(sx, sy, size, size * 0.42, 4)), G_STAR, alpha=0.85, clip=cloak)


def _guide_face(cv: Canvas, cx: float, cy: float, *, blink: bool, mouth: float) -> None:
    face = Ellipse(cx, cy, 11.2, 11.6)
    cv.paint(face.grow(1.1), LINE)
    cv.paint(face, radial(cx + 3, cy - 3, 15, ((0, mix(G_SKIN, WHITE, 0.2)), (1, G_SKIN_SHADE))))
    # Soft white fringe under the hood.
    fringe = Union(
        Ellipse(cx - 6.5, cy - 9.5, 6.5, 4.4),
        Ellipse(cx + 1.0, cy - 10.6, 7.0, 4.2),
        Ellipse(cx + 7.5, cy - 9.2, 5.4, 4.0),
        smooth=1.5,
    )
    cv.paint(fringe & face.grow(1.5), G_HAIR)
    cv.paint(
        (fringe - fringe.shift(-1.0, -1.4)) & face.grow(1.5), G_HAIR_SHADE, alpha=0.8, feather=0.4
    )
    for side in (-1, 1):
        ex = cx + side * 4.6
        # Big fluffy brows: the kindly, wise read.
        cv.paint(
            Stroke(
                [(ex - 3.0 * side, cy - 3.6), (ex, cy - 4.8), (ex + 3.2 * side, cy - 3.8)], 1.2, 0.7
            ),
            G_HAIR,
        )
        if blink:
            cv.paint(
                Stroke([(ex - 2.0, cy - 0.4), (ex, cy + 0.9), (ex + 2.0, cy - 0.4)], 0.75), EYE
            )
        else:
            eye = Ellipse(ex, cy - 0.2, 1.7, 2.3)
            cv.paint(eye, EYE)
            cv.paint(Circle(ex + 0.6, cy - 1.1, 0.75), WHITE)
        cv.paint(Ellipse(ex + side * 1.9, cy + 3.6, 2.4, 1.3), CHEEK, alpha=0.65)
    cv.paint(Ellipse(cx + 0.6, cy + 2.6, 1.8, 1.4), G_SKIN_SHADE)
    cv.paint(Circle(cx + 1.0, cy + 2.1, 0.6), WHITE, alpha=0.5)


def _guide_beard(cv: Canvas, cx: float, top: float, *, mouth: float) -> None:
    """A short, cloud-soft beard and mustache with a smile tucked inside."""
    beard = Union(
        Circle(cx - 6.5, top + 3.0, 4.6),
        Circle(cx, top + 5.0, 5.6),
        Circle(cx + 6.5, top + 3.0, 4.6),
        Circle(cx - 3.0, top + 8.6, 4.0),
        Circle(cx + 3.4, top + 8.4, 4.0),
        Circle(cx + 0.2, top + 11.4, 3.2),
        smooth=2.0,
    )
    cv.paint(beard.grow(1.0), LINE)
    cv.paint(beard, linear((cx + 6, top), (cx - 6, top + 14), ((0, WHITE), (1, G_HAIR))))
    cv.paint(beard - beard.shift(1.2, -1.8), G_HAIR_SHADE, alpha=0.85, feather=0.6, clip=beard)
    for curl_x, curl_y in ((cx - 4.5, top + 7.0), (cx + 4.0, top + 7.4), (cx, top + 10.4)):
        cv.paint(
            Stroke([(curl_x - 1.4, curl_y), (curl_x, curl_y + 0.9), (curl_x + 1.4, curl_y)], 0.35),
            G_HAIR_SHADE,
            alpha=0.8,
            clip=beard,
        )
    smile = Ellipse(cx + 0.3, top + 3.8, 2.6, 0.9 + 1.6 * mouth) & Box(
        cx - 4, top + 3.6, cx + 4, top + 8
    )
    cv.paint(smile.grow(0.4), MOUTH)
    cv.paint(smile, (110, 34, 56))
    if mouth > 0.5:
        cv.paint(Ellipse(cx + 0.3, top + 5.0 + mouth, 1.4, 0.7), TONGUE, clip=smile)
    mustache = Union(
        Ellipse(cx - 3.0, top + 1.6, 3.6, 2.0), Ellipse(cx + 3.6, top + 1.6, 3.6, 2.0), smooth=1.0
    )
    cv.paint(mustache.grow(0.6), G_HAIR_SHADE)
    cv.paint(mustache, WHITE)


def _guide(
    cv: Canvas,
    *,
    breath: float,
    tip: float,
    hem: float,
    blink: bool,
    hand: tuple[float, float] | None,
    mouth: float,
) -> None:
    cx = 54.0
    head_y = 31.0 + breath
    shoulders = 51.0 + breath
    # Shoes peek from under the hem.
    for shoe_x in (46.0, 61.0):
        _part(cv, Ellipse(shoe_x, 95.3, 5.4, 2.6), G_SHOE, shade=(40, 30, 46), rim=False)
    # The staff stands behind the near (left) sleeve.
    _guide_staff(cv, lift=breath * 0.6)
    # Bell-shaped cloak with a gently swaying hem.
    sway = hem * 1.2
    cloak = Union(
        Poly(
            [
                (cx - 12, shoulders - 2),
                (cx + 12, shoulders - 2),
                (cx + 22 + sway, 90.0),
                (cx + 24 + sway, 95.0),
                (cx + 12 + sway * 0.6, 96.5),
                (cx + 2, 95.0),
                (cx - 9 + sway * 0.6, 96.5),
                (cx - 22 + sway, 95.0),
                (cx - 20 + sway, 90.0),
            ]
        ),
        Circle(cx, shoulders + 4, 13.0),
        smooth=4.0,
    )
    _part(
        cv,
        cloak,
        linear(
            (cx + 18, shoulders),
            (cx - 18, 96),
            ((0, G_CLOAK_LIGHT), (0.35, G_CLOAK), (1, G_CLOAK_SHADE)),
        ),
        line=1.35,
        shade=G_CLOAK_SHADE,
    )
    # Inner robe and the cloak's gold-trimmed front edges.
    robe = Poly([(cx - 4, shoulders + 6), (cx + 4, shoulders + 6), (cx + 9, 95), (cx - 7, 95)])
    cv.paint(robe & cloak, linear((cx + 6, 60), (cx - 6, 95), ((0, G_ROBE), (1, G_ROBE_SHADE))))
    for side in (-1, 1):
        edge = Stroke(
            [
                (cx + side * 4.2, shoulders + 6),
                (cx + side * 6.4 + 1, 75.0),
                (cx + side * 8.6, 95.0),
            ],
            1.15,
        )
        cv.paint(edge & cloak, G_TRIM)
    cv.paint(Box(cx - 22, 92.6, cx + 26, 97, 1) & cloak, G_TRIM_SHADE, alpha=0.9)
    _guide_stars(cv, cloak)
    # Near sleeve and hand on the staff (viewer's left).
    sleeve = Stroke([(cx - 10, shoulders + 3), (cx - 19, shoulders + 12), (30.5, 63.0)], 4.6, 5.4)
    _part(cv, sleeve, G_CLOAK, shade=G_CLOAK_SHADE)
    cv.paint(Ellipse(30.5, 63.0, 4.4, 4.0) & sleeve.grow(0.5), G_LINING_SHADE)
    _part(cv, Circle(27.8, 62.5, 3.4), G_SKIN, shade=G_SKIN_SHADE, line=1.0)
    # Far sleeve: resting, or raised in a small open-palm gesture while talking.
    if hand is None:
        far = Stroke(
            [(cx + 10, shoulders + 3), (cx + 17, shoulders + 12), (cx + 15, 67.0)], 4.4, 5.0
        )
        _part(cv, far, G_CLOAK, shade=G_CLOAK_SHADE)
        cv.paint(Ellipse(cx + 15, 67.5, 4.0, 3.2) & far.grow(0.5), G_LINING_SHADE)
        _part(cv, Circle(cx + 14.6, 69.0, 3.0), G_SKIN, shade=G_SKIN_SHADE, line=1.0)
    else:
        hx, hy = hand
        elbow = (cx + 19, (shoulders + 4 + hy) / 2 + 6)
        far = Stroke([(cx + 10, shoulders + 3), elbow, (hx - 1.5, hy + 4.0)], 4.2, 4.6)
        _part(cv, far, G_CLOAK, shade=G_CLOAK_SHADE)
        cv.paint(Circle(hx - 1.5, hy + 4.0, 4.2) & far.grow(0.4), G_LINING)
        palm = Union(
            Ellipse(hx, hy, 3.2, 3.8),
            Segment((hx - 1.6, hy - 2.8), (hx - 2.4, hy - 6.0), 0.95),
            Segment((hx, hy - 3.2), (hx, hy - 6.8), 0.95),
            Segment((hx + 1.7, hy - 2.8), (hx + 2.6, hy - 6.0), 0.95),
            Segment((hx + 2.8, hy), (hx + 5.2, hy - 2.4), 0.9),
            smooth=0.8,
        )
        _part(cv, palm, G_SKIN, shade=G_SKIN_SHADE, line=0.9)
        cv.paint(Poly(star_points(hx + 6.5, hy - 8.5, 2.2, 0.7, 4)), G_STAR, alpha=0.9)
    # Hood: a deep round cowl with a drooping star-tipped point.
    hood = Circle(cx, head_y, 19.5)
    point = Stroke(
        [(cx + 4, head_y - 14), (cx + 15 + tip * 0.5, head_y - 22), (cx + 25 + tip, head_y - 16)],
        7.0,
        1.4,
    )
    hood_shape = Union(hood, point, smooth=3.0)
    _part(
        cv,
        hood_shape,
        linear(
            (cx + 16, head_y - 18),
            (cx - 14, head_y + 16),
            ((0, G_CLOAK_LIGHT), (0.4, G_CLOAK), (1, G_CLOAK_SHADE)),
        ),
        line=1.4,
        shade=G_CLOAK_SHADE,
    )
    tassel = (cx + 25 + tip, head_y - 16)
    cv.paint(Circle(*tassel, 5.0), G_STAR, alpha=0.25, feather=2.0)
    _part(cv, Poly(star_points(*tassel, 3.6, 1.6, 5, 0.2)), G_STAR, shade=G_TRIM_SHADE, line=0.8)
    # The hood's gold rim and dark opening frame the face.
    opening = Ellipse(cx, head_y + 2.0, 14.2, 14.6)
    cv.paint(opening.grow(1.6), G_TRIM)
    cv.paint(opening.grow(1.6) - opening.grow(1.6).shift(-0.8, -1.2), G_TRIM_SHADE, alpha=0.8)
    cv.paint(opening, (30, 26, 70))
    _guide_face(cv, cx, head_y + 3.0, blink=blink, mouth=mouth)
    _guide_beard(cv, cx, head_y + 8.4, mouth=mouth)
    # A small crescent clasp holds the cloak at the collar.
    clasp = Circle(cx, shoulders + 3.6, 3.2) - Circle(cx + 1.6, shoulders + 2.4, 2.6)
    _part(cv, clasp, G_MOON, shade=G_MOON_SHADE, line=0.8, rim=False)


def guide_frame(column: str) -> Image.Image:
    """One frame of the Moonlit Guide: idle breaths, a blink, or a talk gesture."""
    cv = Canvas(100, 100, SS)
    kind, _, number = column.partition("-")
    index = int(number) if number else 0
    if kind == "talk":
        hx, hy, mouth = _GUIDE_TALK_HANDS[index]
        _guide(cv, breath=0.4, tip=0.8, hem=0.4, blink=False, hand=(hx, hy), mouth=mouth)
    else:
        breath, tip, hem = _GUIDE_IDLE_MOTION[index] if kind == "idle" else (0.0, 0.0, 0.0)
        _guide(cv, breath=breath, tip=tip, hem=hem, blink=kind == "blink", hand=None, mouth=0.0)
    return _finish(cv).image()
