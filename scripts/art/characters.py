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

NOVA_ROWS = ("down", "up", "right")
NOVA_IDLE = ("idle-0", "idle-1", "idle-2", "idle-3")
NOVA_WALK = tuple(f"walk-{index}" for index in range(8))
NOVA_COLUMNS = (*NOVA_IDLE, "blink", *NOVA_WALK)
IDLE_BREATH = (0.0, 0.5, 1.0, 0.5)


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
        for ex in (cx - 7, cx + 7):
            if blink:
                cv.paint(
                    Stroke([(ex - 3, cy + 2.4), (ex, cy + 3.8), (ex + 3, cy + 2.4)], 0.95), EYE
                )
            else:
                eye = Ellipse(ex, cy + 2, 2.9, 3.9)
                cv.paint(eye, EYE)
                cv.paint(Ellipse(ex, cy + 3.8, 2.1, 1.6), (86, 90, 170), clip=eye)
                cv.paint(Circle(ex + 0.9, cy + 0.4, 1.25), WHITE)
                cv.paint(Circle(ex - 1.0, cy + 3.8, 0.55), WHITE, alpha=0.9)
            cv.paint(
                Ellipse(ex + (-2.5 if ex < cx else 2.5), cy + 8.2, 2.7, 1.5), CHEEK, alpha=0.75
            )
        cv.paint(
            Stroke([(cx - 2.2, cy + 9.4), (cx, cy + 10.6), (cx + 2.2, cy + 9.4)], 0.7),
            (150, 70, 80),
        )
        # Glass tint and reflections over the face.
        cv.paint(visor, VISOR_GLASS, alpha=0.16)
        cv.paint(visor - visor.shift(-2, 2.5), (200, 236, 255), alpha=0.55, feather=0.6, clip=visor)
        cv.paint(
            Stroke([(cx - 12, cy - 3), (cx - 8, cy - 8.5)], 1.4, 0.9), WHITE, alpha=0.75, clip=visor
        )
        cv.paint(Circle(cx - 13, cy + 1.5, 0.9), WHITE, alpha=0.7, clip=visor)
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
        ex = cx + 14.5
        if blink:
            cv.paint(
                Stroke([(ex - 2.6, cy + 2.4), (ex, cy + 3.7), (ex + 2.2, cy + 2.4)], 0.95), EYE
            )
        else:
            eye = Ellipse(ex, cy + 2, 2.5, 3.8)
            cv.paint(eye, EYE)
            cv.paint(Ellipse(ex, cy + 3.8, 1.8, 1.5), (86, 90, 170), clip=eye)
            cv.paint(Circle(ex + 0.8, cy + 0.4, 1.15), WHITE)
        cv.paint(Ellipse(ex - 2.5, cy + 8.2, 2.6, 1.5), CHEEK, alpha=0.75)
        cv.paint(
            Stroke([(ex + 3.5, cy + 9.4), (ex + 5.2, cy + 10.2)], 0.7), (150, 70, 80), clip=visor_in
        )
        cv.paint(visor_in, VISOR_GLASS, alpha=0.16)
        cv.paint(
            Stroke([(cx + 5, cy - 3), (cx + 8, cy - 8)], 1.3, 0.8), WHITE, alpha=0.75, clip=visor_in
        )
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
                Segment((cx + strap, body + 0.5), (cx + strap * 1.05, hips - 5), 1.4),
                PACK_SHADE,
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
) -> None:
    """Side view facing right. ``near``/``far`` are (foot x, lift, knee push)."""
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
    _nova_helmet(cv, cx + 1, 33 + bob, face="side", blink=blink)


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
        return cv.image()
    phase = index / 8 * math.tau
    s, c = math.sin(phase), math.cos(phase)
    scarf = 2.5 + 1.5 * math.sin(phase * 2)
    if row == "right":
        bob = 1.6 * abs(s)
        near = (50 + 11 * s, 4.0 * max(0.0, c), 2.5 + 3.0 * max(0.0, c))
        far = (50 - 11 * s, 4.0 * max(0.0, -c), 2.5 + 3.0 * max(0.0, -c))
        _nova_side(cv, bob=bob, near=near, far=far, arm=-0.6 * s, blink=False, scarf=scarf)
    else:
        bob = 1.5 * (1 - abs(s))
        lift = (4.0 * max(0.0, s), 4.0 * max(0.0, -s))
        _nova_front(
            cv,
            bob=bob,
            lift=lift,
            swing=2.8 * s,
            sway_x=0.8 * s,
            blink=False,
            scarf=scarf * 0.6,
            back=row == "up",
        )
    return cv.image()


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
    return cv.image()
