"""The illustrated S02 Moon Meadow: background plate and foreground frame.

The background is one opaque 960 x 640 plate painted back to front:

* sky: gradient, nebula haze, stars, the big moon, and moonlit clouds;
* distance: floating islands, far mountains, rolling hills with tree lines,
  and a mist band that sells the depth;
* the meadow: textured ground, the authored trail, a pond, crystal clusters,
  rocks, flowers, bushes, and thousands of grass blades;
* the three landmarks: the start camp (landing pad and lander), the Moon
  Compass clearing (a rune dais inside standing stones), and the Crystal
  Lantern shrine (arch, braziers, warm plaza, steps, and flowers);
* lighting: moonlight, the Lantern's warm pool, landmark glows, and a
  subtle vignette.

The foreground is a transparent plate of dark framing plants and rocks drawn
over the entities, kept to the very edges so it never hides gameplay.

Positions come from ``engine.rendering._meadow_layout`` (and the gameplay
landmarks behind it) so runtime effects land on the painted scenery.
"""

from __future__ import annotations

import math

import numpy as np

from art.paint import (
    Box,
    Canvas,
    Circle,
    Color,
    Ellipse,
    Fbm,
    Noise,
    Poly,
    Rotate,
    Segment,
    Stroke,
    Union,
    blob,
    linear,
    mix,
    radial,
    ridge,
    star_points,
    textured,
)
from engine.rendering._classroom_ambience import ANT_TRAILS, REED_CLUMPS
from engine.rendering._meadow_layout import (
    BRIGHT_STARS,
    CLEARING_CENTER,
    CRYSTAL_CLUSTERS,
    HORIZON,
    MOON,
    POND,
    SHRINE_CENTER,
    SHRINE_FLAMES,
    START_CENTER,
    TRAIL_SEGMENTS,
)

WIDTH, HEIGHT = 960, 640

# Palette ---------------------------------------------------------------------

SKY_TOP: Color = (8, 10, 34)
SKY_MID: Color = (20, 24, 66)
SKY_LOW: Color = (46, 48, 112)
SKY_GLOW: Color = (112, 96, 170)
NEBULA: Color = (96, 70, 160)
STAR: Color = (236, 238, 255)
MOON_LIGHT: Color = (255, 246, 214)
MOON_SHADE: Color = (222, 206, 170)
MOON_HALO: Color = (120, 140, 230)
CLOUD: Color = (54, 60, 124)
CLOUD_LIT: Color = (150, 158, 222)
FAR_HILL: Color = (66, 72, 142)
FAR_HILL_RIM: Color = (122, 128, 204)
MID_HILL: Color = (42, 56, 112)
TREE_LINE: Color = (30, 46, 92)
MIST: Color = (150, 160, 220)
GROUND_FAR: Color = (52, 102, 112)
GROUND_MID: Color = (40, 100, 94)
GROUND_NEAR: Color = (22, 62, 66)
GRASS_DARK: Color = (20, 58, 62)
GRASS_MID: Color = (46, 118, 100)
GRASS_LIGHT: Color = (98, 176, 138)
GRASS_MOON: Color = (158, 222, 196)
PATH_LIGHT: Color = (214, 194, 160)
PATH_MID: Color = (176, 154, 138)
PATH_DARK: Color = (118, 100, 112)
PATH_EDGE: Color = (54, 62, 80)
STONE_LIGHT: Color = (188, 184, 214)
STONE: Color = (124, 120, 158)
STONE_DARK: Color = (68, 66, 100)
INK: Color = (18, 22, 44)
WARM: Color = (255, 190, 100)
WARM_HOT: Color = (255, 238, 184)
CYAN_LIGHT: Color = (196, 252, 255)
CYAN: Color = (92, 214, 244)
CYAN_DARK: Color = (38, 104, 172)
VIOLET_LIGHT: Color = (236, 210, 255)
VIOLET: Color = (174, 124, 250)
VIOLET_DARK: Color = (86, 58, 168)
FLOWERS: tuple[Color, ...] = (
    (255, 146, 200),
    (156, 224, 255),
    (255, 234, 146),
    (242, 242, 255),
    (206, 170, 255),
)
WATER_DEEP: Color = (14, 26, 60)
WATER: Color = (34, 62, 110)
WOOD: Color = (120, 82, 64)
WOOD_DARK: Color = (74, 50, 46)
TEAL_LIGHT: Color = (120, 255, 226)
HULL: Color = (226, 232, 246)
HULL_SHADE: Color = (150, 160, 196)
HULL_TRIM: Color = (236, 104, 96)

#: The HUD's long instruction row spans this box; the sky stays calm behind it.
HUD_BOX = (10, 10, 890, 142)


# Trail geometry ----------------------------------------------------------------


def _bezier(p0, p1, p2, p3, t):  # type: ignore[no-untyped-def]
    u = 1 - t
    return (
        u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
    )


TRAIL_POINTS: list[tuple[float, float]] = [
    _bezier(*segment, step / 48)
    for index, segment in enumerate(TRAIL_SEGMENTS)
    for step in range(0 if index == 0 else 1, 49)
]
_TRAIL_ARRAY = np.asarray(TRAIL_POINTS)


def trail_distance(x: float, y: float) -> float:
    return float(np.min(np.hypot(_TRAIL_ARRAY[:, 0] - x, _TRAIL_ARRAY[:, 1] - y)))


def trail_width(index: int) -> float:
    """Half-width along the trail: wide at camp, narrow at the clearing."""
    t = index / (len(TRAIL_POINTS) - 1)
    if t < 0.5:
        return 21 - 6 * (t / 0.5)
    return 15 + 4 * ((t - 0.5) / 0.5)


def _keepout(x: float, y: float, margin: float = 0.0) -> bool:
    """True where scattered scenery must not go (trail, landmarks, water)."""
    if y < HORIZON + 6:
        return True
    if trail_distance(x, y) < 30 + margin:
        return True
    zones = (
        (START_CENTER[0], START_CENTER[1] + 4, 138, 58),
        (CLEARING_CENTER[0], CLEARING_CENTER[1] + 6, 112, 58),
        (SHRINE_CENTER[0], SHRINE_CENTER[1] - 20, 124, 100),
        (POND[0], POND[1], POND[2] + 14, POND[3] + 12),
        (676, 332, 62, 52),
        (928, 300, 70, 60),
        (18, 230, 40, 30),
    )
    for cx, cy, rx, ry in zones:
        if ((x - cx) / (rx + margin)) ** 2 + ((y - cy) / (ry + margin)) ** 2 < 1:
            return True
    for trail in ANT_TRAILS:
        xs = [p[0] for p in trail.loop] + [trail.hill[0]]
        ys = [p[1] for p in trail.loop] + [trail.hill[1]]
        if min(xs) - 16 < x < max(xs) + 16 and min(ys) - 14 < y < max(ys) + 12:
            return True
    return False


def _in_text_band(x: float, y: float) -> bool:
    """The HUD's bottom feedback lines (y 520-590) keep a calm backing."""
    return 340 < x < 900 and 512 < y < 596


# Sky --------------------------------------------------------------------------------


def paint_sky(cv: Canvas, rng: np.random.Generator) -> None:
    cv.fill(
        linear(
            (0, 0),
            (0, HORIZON + 10),
            ((0.0, SKY_TOP), (0.45, SKY_MID), (0.8, SKY_LOW), (1.0, SKY_GLOW)),
        ),
        box=(0, 0, WIDTH, HORIZON + 40),
    )
    haze = Fbm(11, WIDTH, HEIGHT, 90, 4)

    def nebula_mask(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        # A diagonal band of haze rising from the lower left to the moon.
        band = np.exp(-(((y - (150 - 0.12 * x)) / 46) ** 2))
        return np.clip(band * (haze(x, y) - 0.35) * 1.6, 0, 1)

    cv.paint(None, NEBULA, alpha=0.32, mode="add", mask=nebula_mask, box=(0, 0, WIDTH, 190))
    cv.paint(
        None,
        (60, 100, 170),
        alpha=0.18,
        mode="add",
        mask=lambda x, y: np.clip((haze(x + 300, y) - 0.5) * 2, 0, 1),
        box=(0, 0, WIDTH, 170),
    )
    # Small stars, dimmer behind the HUD rows so mission text stays calm.
    mx, my, mr = MOON
    for _ in range(260):
        x, y = float(rng.uniform(4, WIDTH - 4)), float(rng.uniform(4, HORIZON - 14))
        if math.hypot(x - mx, y - my) < mr + 26:
            continue
        bright = float(rng.uniform(0.25, 0.95))
        in_hud = HUD_BOX[0] < x < HUD_BOX[2] and HUD_BOX[1] < y < HUD_BOX[3]
        if in_hud:
            bright *= 0.45
        size = float(rng.choice((0.55, 0.7, 0.9, 1.1), p=(0.4, 0.3, 0.2, 0.1)))
        tint = mix(STAR, (255, 226, 190) if rng.random() < 0.3 else (190, 210, 255), 0.4)
        cv.paint(Circle(x, y, size), tint, alpha=bright)
    for x, y in BRIGHT_STARS:
        cv.glow(x, y, 9, (160, 170, 255), 0.35)
        cv.paint(Poly(star_points(x, y, 4.6, 0.9, 4)), STAR, alpha=0.9)
        cv.paint(Circle(x, y, 1.4), (255, 255, 255))


def paint_moon(cv: Canvas) -> None:
    mx, my, r = MOON
    cv.glow(mx, my, r * 4.2, MOON_HALO, 0.28, power=2.2)
    cv.glow(mx, my, r * 2.0, (200, 200, 255), 0.25, power=2.0)
    disc = Circle(mx, my, r)
    cv.paint(
        disc,
        radial(mx + r * 0.25, my - r * 0.3, r * 1.4, ((0.0, MOON_LIGHT), (1.0, MOON_SHADE))),
    )
    for cx, cy, cr in ((-18, -12, 9), (10, 14, 12), (22, -20, 6), (-6, 26, 6), (-26, 14, 5)):
        crater = Circle(mx + cx, my + cy, cr)
        cv.paint(crater, (206, 188, 150), alpha=0.45, clip=disc)
        cv.paint(crater - crater.shift(1.5, -1.5), (255, 250, 230), alpha=0.5, clip=disc)
    # Soft terminator on the lower left keeps the moon round.
    cv.paint(
        disc - Circle(mx + 10, my - 8, r * 1.02),
        (150, 140, 170),
        alpha=0.35,
        feather=6,
        clip=disc,
    )
    cv.paint(disc - disc.grow(-2.0), (255, 255, 240), alpha=0.6, clip=disc)


def _cloud(cv: Canvas, cx: float, cy: float, scale: float, alpha: float) -> None:
    puffs = [
        (cx - 38 * scale, cy + 4 * scale, 14 * scale),
        (cx - 18 * scale, cy - 6 * scale, 19 * scale),
        (cx + 6 * scale, cy - 12 * scale, 22 * scale),
        (cx + 30 * scale, cy - 2 * scale, 16 * scale),
        (cx + 50 * scale, cy + 6 * scale, 11 * scale),
    ]
    body = blob(puffs, smooth=8 * scale) & Box(
        cx - 80 * scale, cy - 60, cx + 80 * scale, cy + 8 * scale
    )
    cv.paint(body, CLOUD, alpha=alpha, feather=1.2)
    cv.paint(body - body.shift(-3, 5), CLOUD_LIT, alpha=alpha * 0.8, feather=1.4, clip=body)


def paint_clouds(cv: Canvas) -> None:
    for cx, cy, scale, alpha in (
        (842, 118, 1.1, 0.85),
        (640, 146, 0.8, 0.7),
        (116, 150, 0.9, 0.55),
        (400, 132, 0.6, 0.55),
        (946, 150, 0.7, 0.8),
    ):
        _cloud(cv, cx, cy, scale, alpha)


def _island(cv: Canvas, cx: float, cy: float, w: float, rng: np.random.Generator) -> None:
    """A distant floating island: a hanging rock with a grassy crown."""
    rock = Poly(
        [
            (cx - w * 0.5, cy),
            (cx - w * 0.42, cy + w * 0.12),
            (cx - w * 0.26, cy + w * 0.2),
            (cx - w * 0.14, cy + w * 0.42),
            (cx - w * 0.04, cy + w * 0.72),
            (cx + w * 0.06, cy + w * 0.46),
            (cx + w * 0.2, cy + w * 0.3),
            (cx + w * 0.34, cy + w * 0.18),
            (cx + w * 0.5, cy),
        ]
    )
    cv.paint(rock, linear((cx, cy), (cx, cy + w * 0.7), ((0, (70, 70, 140)), (1, (44, 44, 104)))))
    cv.paint(rock - rock.shift(-w * 0.07, 0), (108, 108, 180), alpha=0.55, clip=rock)
    crown = blob(
        [
            (cx - w * 0.3, cy - w * 0.02, w * 0.2),
            (cx, cy - w * 0.08, w * 0.24),
            (cx + w * 0.3, cy - w * 0.02, w * 0.2),
        ],
        smooth=w * 0.1,
    ) & Box(cx - w, cy - w, cx + w, cy + w * 0.04)
    cv.paint(crown, (58, 92, 140))
    cv.paint(crown - crown.shift(-w * 0.03, w * 0.06), (120, 170, 200), alpha=0.6, clip=crown)
    fall = Segment((cx + w * 0.3, cy + 1), (cx + w * 0.3, cy + w * 0.6), w * 0.02, w * 0.004)
    cv.paint(fall, (190, 214, 255), alpha=0.5)
    del rng


def paint_distance(cv: Canvas, rng: np.random.Generator) -> None:
    for cx, cy, w in ((566, 118, 56), (700, 132, 32), (462, 138, 22)):
        _island(cv, cx, cy, w, rng)
    far = ridge(
        0,
        WIDTH,
        HORIZON + 2,
        lambda x: 30
        + 16 * math.sin(x / 90 + 1.0)
        + 12 * math.sin(x / 37 + 0.3)
        + 22 * max(0.0, math.sin(x / 160 - 0.4)),
        step=3,
        bottom=HORIZON + 40,
    )
    cv.paint(far, linear((0, HORIZON - 70), (0, HORIZON + 10), ((0, FAR_HILL), (1, SKY_GLOW))))
    cv.paint(far - far.shift(-2, 3), FAR_HILL_RIM, alpha=0.55, feather=0.8, clip=far)
    mist = linear((0, HORIZON - 30), (0, HORIZON + 6), ((0, SKY_GLOW), (1, MIST)))
    cv.paint(
        None,
        mist,
        alpha=0.35,
        mask=lambda x, y: np.exp(-(((y - (HORIZON - 6)) / 14) ** 2)),
        box=(0, HORIZON - 40, WIDTH, HORIZON + 20),
    )
    mid = ridge(
        0,
        WIDTH,
        HORIZON + 8,
        lambda x: 12 + 9 * math.sin(x / 70 + 2.1) + 6 * math.sin(x / 23),
        step=3,
        bottom=HORIZON + 40,
    )
    cv.paint(mid, MID_HILL)
    cv.paint(mid - mid.shift(-1.5, 2.5), (84, 100, 170), alpha=0.5, feather=0.6, clip=mid)
    # Round moon-trees on the ridge, thinning near the HUD rows.
    x = 8.0
    while x < WIDTH:
        base = HORIZON + 8 - (12 + 9 * math.sin(x / 70 + 2.1) + 6 * math.sin(x / 23))
        size = float(rng.uniform(5, 11))
        if not (180 < x < 400):
            trunk = Segment((x, base + 4), (x, base - size), 1.1)
            crown = blob(
                [
                    (x, base - size - 3, size * 0.8),
                    (x - size * 0.5, base - size + 1, size * 0.55),
                    (x + size * 0.5, base - size + 2, size * 0.5),
                ],
                smooth=3,
            )
            cv.paint(trunk, TREE_LINE)
            cv.paint(crown, TREE_LINE)
            cv.paint(crown - crown.shift(-1.5, 2), (70, 92, 160), alpha=0.6, clip=crown)
        x += float(rng.uniform(14, 40))
    cv.paint(
        None,
        MIST,
        alpha=0.22,
        mask=lambda x, y: np.exp(-(((y - (HORIZON + 4)) / 9) ** 2)),
        box=(0, HORIZON - 20, WIDTH, HORIZON + 24),
    )


# Ground -------------------------------------------------------------------------------


def _ground_edge(x: float) -> float:
    """The meadow's far edge, with a gentle knoll under the Compass clearing."""
    knoll = 12 * math.exp(-(((x - CLEARING_CENTER[0]) / 120) ** 2))
    return HORIZON + 4 + 4 * math.sin(x / 110) - knoll


def paint_ground(cv: Canvas) -> None:
    ground = ridge(0, WIDTH, 0, lambda x: -_ground_edge(x), step=4, bottom=HEIGHT + 4)
    texture = Fbm(21, WIDTH, HEIGHT, 70, 5)
    base = linear(
        (0, HORIZON),
        (0, HEIGHT),
        ((0.0, GROUND_FAR), (0.3, GROUND_MID), (0.72, (32, 84, 80)), (1.0, GROUND_NEAR)),
    )
    cv.paint(ground, textured(base, texture, (18, 50, 56), (70, 132, 118), 0.55))
    # Broad moss and clover patches for large-scale variation.
    patches = Fbm(33, WIDTH, HEIGHT, 150, 3)
    cv.paint(
        None,
        (84, 150, 112),
        alpha=0.35,
        mask=lambda x, y: np.clip((patches(x, y) - 0.55) * 4, 0, 1),
        clip=ground,
        box=(0, HORIZON, WIDTH, HEIGHT),
    )
    cv.paint(
        None,
        (20, 48, 60),
        alpha=0.4,
        mask=lambda x, y: np.clip((0.42 - patches(x + 400, y)) * 4, 0, 1),
        clip=ground,
        box=(0, HORIZON, WIDTH, HEIGHT),
    )
    # Moonlit midground, a darker foreground band, and drifting cloud shadows.
    cv.paint(
        None,
        (120, 190, 170),
        alpha=0.22,
        mask=lambda x, y: np.exp(-(((y - 300) / 90) ** 2)) * np.clip((x + 200) / 1100, 0, 1),
        clip=ground,
        box=(0, HORIZON, WIDTH, HEIGHT),
    )
    cv.paint(
        None,
        (10, 30, 40),
        alpha=0.55,
        mask=lambda x, y: np.clip((y - 470) / 170, 0, 1),
        clip=ground,
        box=(0, 460, WIDTH, HEIGHT),
    )
    shadows = Fbm(44, WIDTH, HEIGHT, 220, 2)
    cv.paint(
        None,
        (14, 30, 52),
        alpha=0.35,
        mask=lambda x, y: np.clip((shadows(x, y * 1.8) - 0.52) * 5, 0, 1),
        clip=ground,
        box=(0, HORIZON + 30, WIDTH, HEIGHT),
    )
    # Soft rim where the meadow meets the misty hills.
    edge = ground - ground.shift(0, 5)
    cv.paint(edge, (120, 170, 170), alpha=0.35, feather=2.5, clip=ground)


def paint_pond(cv: Canvas) -> None:
    cx, cy, rx, ry = POND
    bank = Ellipse(cx, cy + 2, rx + 8, ry + 6)
    water = Ellipse(cx, cy, rx, ry)
    cv.paint(bank, (30, 60, 66))
    cv.paint(bank - bank.shift(0, -3), (18, 40, 50), alpha=0.8, clip=bank)
    cv.paint(water, linear((0, cy - ry), (0, cy + ry), ((0, WATER_DEEP), (1, WATER))))
    # The moon's shimmering reflection and a few ripples.
    for index, (dy, width) in enumerate(((-12, 7), (-6, 12), (0, 16), (6, 11), (12, 6))):
        cv.paint(
            Ellipse(cx + 18 + (index % 2) * 3, cy + dy, width, 1.3),
            (220, 226, 255),
            alpha=0.55 - abs(dy) * 0.025,
            clip=water,
        )
    for rx_, ry_ in ((22, 6), (36, 10)):
        ring = Ellipse(cx - 20, cy + 4, rx_, ry_) - Ellipse(cx - 20, cy + 4, rx_ - 1.2, ry_ - 0.8)
        cv.paint(ring, (110, 140, 200), alpha=0.35, clip=water)
    cv.paint(water - water.shift(0, 3), (8, 16, 40), alpha=0.6, clip=water)
    # Lily pads with one pink bloom.
    for px, py, pr in ((cx - 34, cy - 4, 6.5), (cx - 22, cy + 9, 5.0), (cx + 40, cy + 6, 5.5)):
        pad = Circle(px, py, pr) - Poly(
            [(px, py), (px + pr * 1.2, py - 3), (px + pr * 1.2, py + 2)]
        )
        cv.paint(Ellipse(px, py, pr, pr * 0.55), (38, 110, 86))
        cv.paint(Ellipse(px - 0.6, py - 0.6, pr * 0.7, pr * 0.36), (70, 160, 110), alpha=0.8)
        del pad
    bloom_x, bloom_y = cx - 34, cy - 7
    for angle in range(5):
        a = angle * math.tau / 5
        cv.paint(
            Ellipse(bloom_x + 2.4 * math.cos(a), bloom_y + 1.4 * math.sin(a), 2.2, 1.6), FLOWERS[0]
        )
    cv.paint(Circle(bloom_x, bloom_y, 1.3), (255, 240, 170))
    cv.glow(bloom_x, bloom_y, 10, (255, 150, 200), 0.3)
    # Bank stones.
    for angle in (0.2, 0.9, 1.6, 2.6, 3.4, 4.3, 5.2, 5.8):
        sx = cx + (rx + 5) * math.cos(angle)
        sy = cy + 2 + (ry + 4) * math.sin(angle)
        stone = Ellipse(sx, sy, 5.5, 3.4)
        cv.part(
            stone,
            STONE,
            line=(26, 34, 52),
            line_width=0.8,
            shade=STONE_DARK,
            shade_offset=(0, -1.8),
        )


def paint_trail(cv: Canvas, rng: np.random.Generator) -> None:
    edge_shapes = []
    fill_shapes = []
    for index, (a, b) in enumerate(zip(TRAIL_POINTS, TRAIL_POINTS[1:], strict=False)):
        w0, w1 = trail_width(index), trail_width(index + 1)
        edge_shapes.append(Segment(a, b, w0 + 3.5, w1 + 3.5))
        fill_shapes.append(Segment(a, b, w0, w1))
    edge = Union(*edge_shapes)
    path = Union(*fill_shapes)
    grit = Fbm(51, WIDTH, HEIGHT, 26, 4)
    cv.paint(edge, PATH_EDGE, alpha=0.9, feather=1.4)
    cv.paint(
        path,
        textured(
            linear((600, 180), (100, 560), ((0, PATH_LIGHT), (1, PATH_MID))),
            grit,
            PATH_DARK,
            (234, 220, 190),
            0.45,
        ),
        feather=0.8,
    )
    # Inner shading: darker toward the lower edge, lighter along the upper one.
    cv.paint(path - path.shift(0, -4), PATH_DARK, alpha=0.45, feather=2.0, clip=path)
    cv.paint(path - path.shift(1, 3), (236, 224, 196), alpha=0.35, feather=1.5, clip=path)
    # Flat stepping stones and pebbles set into the trail.
    count = len(TRAIL_POINTS)
    for index in range(3, count - 3, 5):
        x, y = TRAIL_POINTS[index]
        nx, ny = TRAIL_POINTS[index + 1]
        dx, dy = nx - x, ny - y
        length = math.hypot(dx, dy) or 1.0
        px, py = -dy / length, dx / length
        side = (-1) ** index * float(rng.uniform(0.0, 0.45)) * trail_width(index)
        sx, sy = x + px * side, y + py * side
        size = trail_width(index) * float(rng.uniform(0.42, 0.55))
        stone = Ellipse(sx, sy, size, size * 0.56)
        cv.paint(stone.grow(1.0), (92, 84, 100), alpha=0.75)
        cv.paint(stone, (196, 186, 190))
        cv.paint(stone - stone.shift(0, -1.8), (140, 130, 146), alpha=0.9, clip=stone)
        cv.paint(stone - stone.shift(1, 1.4), (240, 234, 226), alpha=0.6, clip=stone)
    for _ in range(90):
        index = int(rng.integers(0, count))
        x, y = TRAIL_POINTS[index]
        w = trail_width(index)
        ox, oy = float(rng.uniform(-w, w)), float(rng.uniform(-w * 0.7, w * 0.7))
        cv.paint(Ellipse(x + ox, y + oy, 1.4, 0.9), (110, 96, 104), alpha=0.8)
        cv.paint(Ellipse(x + ox - 0.3, y + oy - 0.4, 0.9, 0.5), (236, 226, 206), alpha=0.7)
    # Moon-rune waymarkers along the edge point the way to the shrine.
    for fraction in (0.28, 0.62, 0.8):
        index = int(fraction * (count - 1))
        x, y = TRAIL_POINTS[index]
        nx, ny = TRAIL_POINTS[index + 1]
        dx, dy = nx - x, ny - y
        length = math.hypot(dx, dy) or 1.0
        px, py = -dy / length, dx / length
        side = 1 if fraction != 0.62 else -1
        mx, my = (
            x + px * (trail_width(index) + 12) * side,
            y + py * (trail_width(index) + 12) * side,
        )
        _waystone(cv, mx, my)


def _waystone(cv: Canvas, x: float, y: float) -> None:
    cv.paint(Ellipse(x, y + 1, 7, 2.6), (8, 16, 24), alpha=0.5, feather=1.2)
    stone = Box(x - 4.5, y - 15, x + 4.5, y + 1, 3.5)
    cv.part(stone, STONE, line=INK, line_width=0.9, shade=STONE_DARK, shade_offset=(2.5, 0))
    cv.paint(Poly(star_points(x, y - 8, 2.8, 1.0, 4)), CYAN_LIGHT)
    cv.glow(x, y - 8, 12, (90, 220, 255), 0.45)


# Landmarks ---------------------------------------------------------------------------


def paint_start_camp(cv: Canvas) -> None:
    cx, cy = START_CENTER
    cy += 3
    cv.paint(Ellipse(cx, cy + 6, 128, 50), (10, 24, 34), alpha=0.45, feather=5)
    rim = Ellipse(cx, cy, 122, 46)
    pad = Ellipse(cx, cy - 2, 112, 40)
    cv.part(rim, (70, 82, 118), line=INK, line_width=1.2, shade=(44, 52, 86), shade_offset=(0, -5))
    cv.paint(
        pad,
        textured(
            radial(cx + 30, cy - 18, 150, ((0, (112, 128, 160)), (1, (70, 82, 118)))),
            Noise(61, WIDTH, HEIGHT, 5),
            (64, 74, 108),
            (128, 144, 176),
            0.25,
        ),
    )
    # Engraved rings and panel seams.
    for rx, ry in ((92, 32), (60, 20)):
        ring = Ellipse(cx, cy - 2, rx, ry) - Ellipse(cx, cy - 2, rx - 1.6, ry - 1.0)
        cv.paint(ring, (70, 80, 116), alpha=0.9)
        cv.paint(ring.shift(0, 1.4), (176, 190, 214), alpha=0.35)
    for index in range(8):
        a = index * math.tau / 8 + math.tau / 16
        cv.paint(
            Segment(
                (cx + 60 * math.cos(a), cy - 2 + 20 * math.sin(a)),
                (cx + 92 * math.cos(a), cy - 2 + 32 * math.sin(a)),
                0.6,
            ),
            (74, 84, 120),
            alpha=0.8,
        )
    # Teal landing lights around the rim.
    for index in range(12):
        a = index * math.tau / 12
        lx, ly = cx + 104 * math.cos(a), cy - 1 + 36 * math.sin(a)
        cv.glow(lx, ly, 10, (60, 230, 210), 0.45)
        cv.paint(Ellipse(lx, ly, 2.6, 1.8), TEAL_LIGHT)
    cv.glow(cx, cy, 150, (40, 150, 160), 0.14, squash=0.4)
    # A painted explorer star at the heart of the pad.
    emblem = Poly(
        [(x, (y - (cy - 2)) * 0.36 + cy - 2) for x, y in star_points(cx + 8, cy - 2, 30, 13, 5)]
    )
    cv.paint(emblem, (150, 170, 210), alpha=0.35)
    cv.paint(emblem - emblem.grow(-1.4), (200, 226, 255), alpha=0.35)
    # Glowing chevrons lead off the pad toward the trail and the Compass.
    for index, chevron_x in enumerate((432.0, 414.0, 396.0)):
        chevron = Stroke(
            [(chevron_x + 6, cy - 9), (chevron_x, cy - 2), (chevron_x + 6, cy + 5)], 1.6
        )
        cv.glow(chevron_x + 3, cy - 2, 14, (60, 230, 210), 0.35 - index * 0.06)
        cv.paint(chevron, TEAL_LIGHT, alpha=0.95 - index * 0.2)
    paint_lander(cv, 676, 372)
    _crates(cv, 430, 416)
    _telescope(cv, 604, 356)
    # A little signpost pointing toward the Compass clearing.
    sx, sy = 392, 338
    cv.paint(Ellipse(sx + 1, sy + 1, 6, 2.2), (8, 16, 24), alpha=0.5, feather=1)
    cv.part(Box(sx - 1.6, sy - 30, sx + 1.6, sy + 1, 1), WOOD, line=INK, line_width=0.9)
    board = Poly(
        [
            (sx - 16, sy - 30),
            (sx + 8, sy - 30),
            (sx + 8, sy - 22),
            (sx - 16, sy - 22),
            (sx - 21, sy - 26),
        ]
    )
    cv.part(board, (150, 104, 76), line=INK, line_width=0.9, shade=WOOD_DARK, shade_offset=(0, -2))
    cv.paint(Poly(star_points(sx - 5, sy - 26, 2.6, 1.0, 4)), (190, 150, 255))


def _crates(cv: Canvas, x: float, y: float) -> None:
    cv.paint(Ellipse(x + 4, y + 1, 20, 4), (6, 12, 20), alpha=0.5, feather=1.5)
    for bx, by, size in ((x - 8, y, 13), (x + 7, y, 11), (x - 2, y - 12, 10)):
        crate = Box(bx - size / 2, by - size, bx + size / 2, by, 1.5)
        cv.part(
            crate,
            (170, 120, 80),
            line=INK,
            line_width=1.0,
            shade=(116, 78, 60),
            shade_offset=(2, 0),
        )
        cv.paint(
            Segment((bx - size / 2 + 2, by - size + 2), (bx + size / 2 - 2, by - 2), 0.6),
            (110, 74, 56),
        )
        cv.paint(
            Box(bx - size / 2, by - size, bx + size / 2, by - size + 2, 1),
            (220, 170, 120),
            alpha=0.7,
        )


def _telescope(cv: Canvas, x: float, y: float) -> None:
    cv.paint(Ellipse(x, y + 1, 12, 3), (6, 12, 20), alpha=0.5, feather=1.2)
    for leg in (-7, 0, 7):
        cv.paint(Segment((x, y - 14), (x + leg, y), 1.0), (60, 50, 70))
    tube = Rotate(Box(x - 13, y - 19, x + 11, y - 13, 2.5), -0.55, x, y - 16)
    cv.part(
        tube, (230, 190, 110), line=INK, line_width=0.9, shade=(170, 124, 70), shade_offset=(0, -2)
    )
    cv.paint(Circle(x + 9, y - 23, 2.2), (170, 230, 255))


def paint_lander(cv: Canvas, x: float, base: float) -> None:
    """A friendly little lander parked at the edge of the camp pad."""
    cv.paint(Ellipse(x, base + 1, 44, 9), (8, 14, 24), alpha=0.5, feather=3)
    for lx in (-26, 26):
        cv.part(
            Segment((x + lx * 0.55, base - 28), (x + lx, base - 2), 2.0),
            (170, 176, 204),
            line=INK,
            line_width=1.0,
        )
        cv.part(Ellipse(x + lx, base - 1, 6, 2.4), (130, 136, 170), line=INK, line_width=0.9)
    hull = Union(
        Ellipse(x, base - 44, 27, 30),
        Box(x - 27, base - 44, x + 27, base - 24, 10),
        smooth=4,
    )
    cv.part(
        hull,
        linear((x + 20, base - 70), (x - 25, base - 20), ((0, HULL), (1, HULL_SHADE))),
        line=INK,
        line_width=1.4,
        shade=(118, 126, 170),
        shade_offset=(3, -4),
        rim=(200, 230, 255),
        rim_offset=(-1.5, 1.5),
    )
    band = Box(x - 27, base - 34, x + 27, base - 28, 1)
    cv.paint(band, HULL_TRIM, clip=hull)
    cv.paint(band - band.shift(0, -2), (180, 70, 76), alpha=0.8, clip=hull & band)
    for fin in (-1, 1):
        cv.part(
            Poly(
                [
                    (x + fin * 22, base - 36),
                    (x + fin * 36, base - 18),
                    (x + fin * 34, base - 12),
                    (x + fin * 20, base - 22),
                ]
            ),
            HULL_TRIM,
            line=INK,
            line_width=1.1,
            shade=(170, 64, 72),
            shade_offset=(0, -2),
        )
    window = Circle(x + 2, base - 50, 10.5)
    cv.part(window, (160, 170, 200), line=INK, line_width=1.2)
    glass = Circle(x + 2, base - 50, 7.8)
    cv.paint(glass, radial(x + 4, base - 53, 10, ((0, (170, 255, 240)), (1, (40, 150, 170)))))
    cv.paint(Ellipse(x - 0.5, base - 53, 3, 1.8), (255, 255, 255), alpha=0.85)
    cv.glow(x + 2, base - 50, 26, (80, 230, 210), 0.35)
    cv.paint(Segment((x - 6, base - 74), (x - 6, base - 84), 0.9), (150, 160, 190))
    cv.paint(Circle(x - 6, base - 85, 2.2), (255, 120, 100))
    cv.glow(x - 6, base - 85, 9, (255, 110, 90), 0.5)
    # Ramp down to the pad.
    ramp = Poly([(x - 20, base - 16), (x - 8, base - 16), (x - 30, base + 2), (x - 46, base + 2)])
    cv.part(
        ramp, (178, 184, 210), line=INK, line_width=1.0, shade=(128, 134, 170), shade_offset=(0, -2)
    )


def _standing_stone(cv: Canvas, x: float, y: float, h: float, lean: float) -> None:
    cv.paint(Ellipse(x + 2, y + 1, 9, 3), (6, 14, 22), alpha=0.5, feather=1.5)
    stone = Poly(
        [
            (x - 7, y + 1),
            (x - 6 + lean * 0.3, y - h * 0.7),
            (x - 2 + lean, y - h),
            (x + 4 + lean, y - h + 2),
            (x + 7, y - h * 0.6),
            (x + 7, y + 1),
        ]
    )
    cv.part(
        stone,
        linear((x + 6, y - h), (x - 6, y), ((0, (150, 150, 190)), (1, (92, 92, 132)))),
        line=INK,
        line_width=1.0,
        shade=STONE_DARK,
        shade_offset=(3, 0),
        rim=(200, 214, 255),
        rim_offset=(-1.2, 1.4),
    )
    cv.paint(stone & Box(x - 8, y - h * 0.35, x + 8, y + 2), (60, 110, 90), alpha=0.55, clip=stone)
    rx, ry = x + lean * 0.4, y - h * 0.55
    cv.paint(Poly(star_points(rx, ry, 2.6, 0.9, 4)), (206, 180, 255), alpha=0.95)
    cv.glow(rx, ry, 11, (170, 120, 255), 0.4)


def paint_clearing(cv: Canvas) -> None:
    cx, cy = CLEARING_CENTER
    cy += 8
    cv.glow(cx, cy - 4, 130, (110, 80, 200), 0.18, squash=0.5)
    cv.paint(Ellipse(cx, cy + 4, 76, 28), (8, 16, 30), alpha=0.5, feather=4)
    dais = Ellipse(cx, cy, 70, 25)
    top = Ellipse(cx, cy - 3, 64, 21)
    cv.part(dais, STONE, line=INK, line_width=1.2)
    cv.paint(
        top,
        textured(
            radial(cx + 20, cy - 12, 90, ((0, (170, 168, 206)), (1, (116, 114, 156)))),
            Noise(71, WIDTH, HEIGHT, 4),
            (104, 102, 144),
            (184, 184, 220),
            0.3,
        ),
    )
    # Compass rose inlay and a rune ring on the dais.
    rose = Poly(star_points(cx, cy - 3, 30, 5, 4))
    cv.paint(
        Poly([(x, (y - (cy - 3)) * 0.34 + cy - 3) for x, y in rose.points]),
        (96, 90, 150),
        alpha=0.9,
    )
    ring = Ellipse(cx, cy - 3, 50, 16) - Ellipse(cx, cy - 3, 48.5, 15)
    cv.paint(ring, (200, 170, 255), alpha=0.75)
    cv.glow(cx, cy - 3, 60, (140, 100, 255), 0.18, squash=0.34)
    for index in range(12):
        a = index * math.tau / 12
        rx, ry = cx + 56 * math.cos(a), cy - 3 + 18.5 * math.sin(a)
        cv.paint(Ellipse(rx, ry, 1.6, 1.0), (220, 200, 255))
    # Standing stones, leaving the view of the Compass open.
    for angle, h in (
        (200, 26),
        (160, 24),
        (130, 20),
        (228, 30),
        (318, 30),
        (345, 24),
        (20, 24),
        (50, 20),
    ):
        a = math.radians(angle)
        sx, sy = cx + 96 * math.cos(a), cy + 40 * math.sin(a)
        _standing_stone(cv, sx, sy, h, lean=2 * math.cos(a))


def paint_shrine(cv: Canvas) -> None:
    cx, cy = SHRINE_CENTER
    # Warm light pools under everything that belongs to the shrine.
    cv.glow(cx + 10, cy - 30, 250, (255, 130, 40), 0.42, squash=0.7, power=1.6)
    cv.glow(cx, cy, 140, (255, 200, 110), 0.38, squash=0.5)
    # Plaza with radial flagstones, then front steps down toward the viewer.
    plaza = Ellipse(cx, cy + 6, 98, 36)
    cv.paint(Ellipse(cx, cy + 12, 104, 40), (10, 16, 26), alpha=0.5, feather=4)
    for step in range(3):
        stair = Box(
            cx - 56 + step * 8, cy + 30 + step * 7, cx + 56 - step * 8, cy + 40 + step * 7, 3
        )
        cv.part(
            stair,
            (150, 128, 120),
            line=INK,
            line_width=1.0,
            shade=(104, 86, 90),
            shade_offset=(0, -3),
        )
        cv.paint(stair - stair.shift(0, 2), (230, 200, 160), alpha=0.5, clip=stair)
    cv.part(plaza, (160, 136, 124), line=INK, line_width=1.2)
    tiles = radial(
        cx, cy + 4, 100, ((0, (236, 206, 160)), (0.6, (186, 158, 138)), (1, (140, 118, 116)))
    )
    inner = Ellipse(cx, cy + 3, 92, 31)
    cv.paint(
        inner, textured(tiles, Noise(81, WIDTH, HEIGHT, 5), (150, 126, 120), (246, 222, 180), 0.25)
    )
    for index in range(16):
        a = index * math.tau / 16
        cv.paint(
            Segment(
                (cx + 30 * math.cos(a), cy + 3 + 10 * math.sin(a)),
                (cx + 92 * math.cos(a), cy + 3 + 31 * math.sin(a)),
                0.55,
            ),
            (120, 96, 96),
            alpha=0.7,
            clip=inner,
        )
    for rx, ry in ((30, 10), (62, 21)):
        cv.paint(
            Ellipse(cx, cy + 3, rx, ry) - Ellipse(cx, cy + 3, rx - 1.1, ry - 0.8),
            (120, 96, 96),
            alpha=0.7,
        )
    # Pedestal ring the Lantern stands on.
    cv.paint(Ellipse(cx, cy + 17, 30, 9), (255, 214, 140), alpha=0.35, feather=3)
    # The arch: two pillars and a carved lintel framing the Lantern.
    for px in (92.0, 234.0):
        _pillar(cv, px, 376, cy + 2)
    lintel = Poly([(66, 366), (260, 366), (252, 352), (160, 340), (74, 352)])
    cv.part(
        lintel,
        linear((160, 340), (160, 368), ((0, (206, 182, 170)), (1, (140, 116, 124)))),
        line=INK,
        line_width=1.3,
        shade=(104, 86, 100),
        shade_offset=(0, -3),
        rim=(255, 226, 180),
        rim_offset=(0, 1.5),
    )
    cv.paint(Box(70, 364, 256, 372, 2), (112, 92, 104))
    cv.paint(Box(70, 364, 256, 366, 1), (60, 48, 64), alpha=0.7)
    for flame_x, flame_y in SHRINE_FLAMES:
        _brazier(cv, flame_x, flame_y)
    # Keystone moon emblem.
    emblem = Circle(160, 352, 8)
    cv.part(emblem, (255, 222, 140), line=INK, line_width=1.0)
    cv.paint(Circle(163, 350, 6.5), (160, 136, 124), clip=emblem)
    cv.glow(160, 352, 26, (255, 200, 110), 0.5)
    # Hanging vines with little glowing blossoms.
    for vx, length in ((84, 30), (104, 18), (222, 24), (242, 34), (132, 12), (190, 14)):
        points = [(vx, 368), (vx + 1.5, 368 + length * 0.5), (vx - 1, 368 + length)]
        cv.paint(Stroke(points, 1.2, 0.6), (40, 110, 80))
        for leaf in range(3):
            ly = 370 + leaf * length / 3
            cv.paint(Ellipse(vx + (2 if leaf % 2 else -2), ly, 2.4, 1.3), (70, 160, 100))
        cv.paint(Circle(vx - 1, 368 + length + 1, 1.6), (255, 190, 220))
        cv.glow(vx - 1, 368 + length + 1, 7, (255, 170, 210), 0.35)
    # Flower beds hugging the plaza.
    for fx, fy in ((58, 520), (262, 520), (72, 474), (248, 470), (116, 548), (206, 548)):
        _flower_bush(cv, fx, fy, warm=True)


def _brazier(cv: Canvas, x: float, y: float) -> None:
    """A small bronze bowl with a warm crystal flame (``y`` is the bowl rim)."""
    bowl = Poly([(x - 8, y), (x + 8, y), (x + 5, y + 6), (x - 5, y + 6)])
    cv.part(
        bowl, (150, 100, 64), line=INK, line_width=0.9, shade=(96, 62, 44), shade_offset=(0, -2)
    )
    cv.paint(Box(x - 8, y - 1, x + 8, y + 1.2, 0.6), (230, 170, 100))
    cv.glow(x, y - 6, 34, (255, 170, 80), 0.65)
    outer = Poly([(x, y - 17), (x + 5.5, y - 6), (x + 3, y), (x - 3, y), (x - 5.5, y - 6)])
    cv.paint(outer.grow(0.8), (190, 90, 40), alpha=0.8)
    cv.paint(outer, (255, 184, 90))
    cv.paint(Poly([(x, y - 12), (x + 2.8, y - 5), (x, y - 1), (x - 2.8, y - 5)]), WARM_HOT)


def _pillar(cv: Canvas, x: float, top: float, base: float) -> None:
    cv.paint(Ellipse(x + 3, base + 2, 17, 5), (10, 14, 22), alpha=0.55, feather=2)
    foot = Box(x - 14, base - 12, x + 14, base + 2, 3)
    cv.part(
        foot, (150, 128, 130), line=INK, line_width=1.1, shade=(104, 86, 98), shade_offset=(0, -3)
    )
    shaft = Box(x - 10, top + 6, x + 10, base - 10, 2)
    cv.part(
        shaft,
        linear(
            (x - 10, 0),
            (x + 10, 0),
            ((0, (112, 96, 112)), (0.55, (186, 164, 160)), (1, (150, 128, 132))),
        ),
        line=INK,
        line_width=1.2,
    )
    for groove in (-4, 3):
        cv.paint(
            Segment((x + groove, top + 10), (x + groove, base - 14), 0.7), (110, 92, 104), alpha=0.8
        )
    cap = Box(x - 14, top - 2, x + 14, top + 8, 2)
    cv.part(
        cap, (196, 172, 164), line=INK, line_width=1.1, shade=(130, 108, 116), shade_offset=(0, -3)
    )
    # Ivy up the shaft.
    ivy = Stroke(
        [(x - 9, base - 10), (x - 4, base - 30), (x - 9, base - 52), (x - 3, base - 76)], 1.1, 0.6
    )
    cv.paint(ivy, (40, 104, 76))
    for index in range(6):
        ly = base - 14 - index * 11
        lx = x - 8 + (3 if index % 2 else -1)
        cv.paint(Ellipse(lx, ly, 2.6, 1.6), (72, 156, 100) if index % 2 else (52, 128, 88))


# Scatter ------------------------------------------------------------------------------


def _crystal_cluster(cv: Canvas, x: float, y: float, scale: float, hue: float) -> None:
    light = VIOLET_LIGHT if hue else CYAN_LIGHT
    mid = VIOLET if hue else CYAN
    dark = VIOLET_DARK if hue else CYAN_DARK
    glow_color = (170, 120, 255) if hue else (80, 210, 255)
    cv.glow(x, y - 16 * scale, 54 * scale, glow_color, 0.35)
    cv.glow(x, y + 2, 46 * scale, glow_color, 0.25, squash=0.35)
    cv.paint(Ellipse(x, y + 1, 22 * scale, 5 * scale), (6, 12, 24), alpha=0.5, feather=2)
    shards = (
        (-13, 17, -0.5, 5.0),
        (13, 20, 0.45, 5.5),
        (-6, 27, -0.2, 6.0),
        (1, 34, 0.02, 7.0),
        (8, 24, 0.25, 5.2),
        (-18, 11, -0.8, 3.6),
        (19, 12, 0.8, 3.6),
    )
    for dx, h, lean, w in shards:
        bx = x + dx * scale
        tip = (bx + lean * h * scale * 0.5, y - h * scale)
        body = Poly(
            [
                (bx - w * scale, y + 1),
                (bx - w * scale * 0.9 + lean * h * scale * 0.35, y - h * scale * 0.72),
                tip,
                (bx + w * scale * 0.9 + lean * h * scale * 0.35, y - h * scale * 0.72),
                (bx + w * scale, y + 1),
            ]
        )
        cv.paint(body.grow(0.9), INK)
        cv.paint(body, linear(tip, (bx, y), ((0, light), (0.5, mid), (1, dark))))
        facet = Poly(
            [
                tip,
                (bx + lean * h * scale * 0.35, y - h * scale * 0.72),
                (bx, y + 1),
                (bx + w * scale, y + 1),
                (bx + w * scale * 0.9 + lean * h * scale * 0.35, y - h * scale * 0.72),
            ]
        )
        cv.paint(facet, dark, alpha=0.5, clip=body)
        cv.paint(
            Segment(tip, (bx - w * scale * 0.4, y - h * scale * 0.4), 0.6),
            (255, 255, 255),
            alpha=0.7,
            clip=body,
        )


def _rock(
    cv: Canvas, x: float, y: float, size: float, rng: np.random.Generator, moss: bool = True
) -> None:
    cv.paint(
        Ellipse(x + size * 0.2, y + size * 0.3, size * 1.2, size * 0.35),
        (6, 14, 22),
        alpha=0.5,
        feather=2,
    )
    points = []
    for index in range(9):
        a = math.pi + index * math.pi / 8
        r = size * float(rng.uniform(0.8, 1.05))
        points.append((x + r * math.cos(a) * 1.15, y + r * math.sin(a) * 0.8))
    rock = Union(
        Poly([*points, (x + size * 1.1, y + size * 0.3), (x - size * 1.1, y + size * 0.3)]),
        smooth=0,
    )
    cv.part(
        rock,
        linear(
            (x + size, y - size),
            (x - size, y + size * 0.3),
            ((0, (148, 146, 184)), (1, (78, 78, 116))),
        ),
        line=INK,
        line_width=1.0,
        shade=STONE_DARK,
        shade_offset=(size * 0.35, -size * 0.1),
        rim=(196, 208, 250),
        rim_offset=(-1.2, 1.2),
    )
    if moss:
        cap = Ellipse(x - size * 0.1, y - size * 0.62, size * 0.7, size * 0.28)
        cv.paint(cap, (70, 150, 104), alpha=0.9, clip=rock)
        cv.paint(cap - cap.shift(0, 1.4), (130, 210, 150), alpha=0.6, clip=rock & cap)


def _flower_bush(
    cv: Canvas, x: float, y: float, *, warm: bool = False, rng: np.random.Generator | None = None
) -> None:
    leaves = blob([(x - 7, y - 4, 6), (x, y - 8, 7.5), (x + 7, y - 4, 6), (x, y - 1, 6)], smooth=3)
    cv.paint(Ellipse(x, y + 1, 13, 3.5), (6, 12, 20), alpha=0.5, feather=1.5)
    cv.part(
        leaves,
        (40, 112, 84),
        line=(14, 34, 40),
        line_width=0.9,
        shade=(26, 74, 64),
        shade_offset=(0, -3),
        rim=(130, 214, 160),
        rim_offset=(-1, 1.2),
    )
    palette = ((255, 170, 110), (255, 226, 140), (255, 150, 190)) if warm else FLOWERS
    for index, (fx, fy) in enumerate(
        ((x - 6, y - 7), (x + 1, y - 12), (x + 6, y - 6), (x - 1, y - 4))
    ):
        color = palette[index % len(palette)]
        cv.paint(Circle(fx, fy, 2.1), color)
        cv.paint(Circle(fx - 0.5, fy - 0.5, 0.8), (255, 255, 240))
        cv.glow(fx, fy, 6, color, 0.25)
    del rng


def _mushrooms(cv: Canvas, x: float, y: float, scale: float) -> None:
    for dx, h, r in ((-5, 9, 5.0), (3, 13, 6.5), (9, 6, 3.6)):
        mx = x + dx * scale
        cv.paint(Segment((mx, y), (mx, y - h * scale), 1.3 * scale), (220, 226, 236))
        cap = Ellipse(mx, y - h * scale, r * scale, r * scale * 0.6) & Box(
            mx - 20, y - h * scale - 20, mx + 20, y - h * scale + 1
        )
        cv.paint(cap.grow(0.8), INK)
        cv.paint(cap, (90, 230, 220))
        cv.paint(
            Circle(mx - r * 0.3 * scale, y - h * scale - r * 0.3 * scale, 0.9 * scale),
            (230, 255, 250),
        )
        cv.glow(mx, y - h * scale, 16 * scale, (60, 230, 210), 0.35)


def _tuft(
    cv: Canvas, x: float, y: float, h: float, rng: np.random.Generator, color: Color, light: Color
) -> None:
    for index in range(5):
        lean = float(rng.uniform(-0.7, 0.7)) * h * 0.5 + (index - 2) * h * 0.12
        blade_h = h * float(rng.uniform(0.6, 1.0))
        points = [
            (x + (index - 2) * 1.2, y),
            (x + (index - 2) * 1.2 + lean * 0.35, y - blade_h * 0.55),
            (x + (index - 2) + lean, y - blade_h),
        ]
        cv.paint(Stroke(points, 1.2, 0.2), color if index % 2 else light)


def _moon_tree(cv: Canvas, x: float, base: float, scale: float, rng: np.random.Generator) -> None:
    """A round-canopied moon tree with glowing hanging fruit."""
    cv.paint(
        Ellipse(x - 10 * scale, base + 2, 46 * scale, 9 * scale), (6, 12, 22), alpha=0.5, feather=4
    )
    trunk = Poly(
        [
            (x - 9 * scale, base + 2),
            (x - 5 * scale, base - 40 * scale),
            (x - 12 * scale, base - 74 * scale),
            (x - 2 * scale, base - 70 * scale),
            (x + 4 * scale, base - 92 * scale),
            (x + 7 * scale, base - 44 * scale),
            (x + 12 * scale, base + 2),
        ]
    )
    cv.part(
        trunk,
        linear((x + 10 * scale, 0), (x - 10 * scale, 0), ((0, (104, 86, 110)), (1, (58, 46, 72)))),
        line=INK,
        line_width=1.3,
        rim=(170, 170, 230),
        rim_offset=(-1.6, 0.8),
    )
    for root in (-1, 1):
        cv.paint(
            Stroke(
                [(x + root * 6 * scale, base - 6 * scale), (x + root * 16 * scale, base + 2)],
                3 * scale,
                1,
            ),
            (74, 60, 86),
        )
    puffs = [
        (x - 2 * scale, base - 118 * scale, 34 * scale),
        (x - 34 * scale, base - 100 * scale, 26 * scale),
        (x + 30 * scale, base - 100 * scale, 27 * scale),
        (x - 14 * scale, base - 84 * scale, 26 * scale),
        (x + 14 * scale, base - 82 * scale, 24 * scale),
        (x - 48 * scale, base - 80 * scale, 16 * scale),
        (x + 46 * scale, base - 80 * scale, 16 * scale),
    ]
    canopy = blob(puffs, smooth=10 * scale)
    cv.paint(canopy.grow(1.4), INK)
    cv.paint(
        canopy,
        linear(
            (x + 30 * scale, base - 150 * scale),
            (x - 30 * scale, base - 60 * scale),
            ((0, (74, 150, 150)), (1, (28, 70, 90))),
        ),
    )
    for px, py, pr in puffs:
        puff = Circle(px, py, pr)
        cv.paint(
            puff - puff.shift(-pr * 0.25, pr * 0.3),
            (126, 204, 190),
            alpha=0.45,
            feather=2,
            clip=canopy,
        )
    cv.paint(canopy - canopy.shift(0, -8 * scale), (16, 40, 60), alpha=0.6, feather=3, clip=canopy)
    for _ in range(9):
        fx = x + float(rng.uniform(-44, 44)) * scale
        fy = base - float(rng.uniform(66, 100)) * scale
        if canopy.sdf(np.asarray([fx]), np.asarray([fy]))[0] > -3:
            continue
        cv.paint(Segment((fx, fy - 5 * scale), (fx, fy), 0.5), (40, 80, 80))
        cv.glow(fx, fy, 14 * scale, (120, 255, 220), 0.4)
        cv.paint(Circle(fx, fy + 1, 2.3 * scale), (170, 255, 230))
        cv.paint(Circle(fx - 0.6, fy + 0.4, 0.8 * scale), (255, 255, 255))


def paint_trees(cv: Canvas, rng: np.random.Generator) -> None:
    _moon_tree(cv, 928, 348, 1.25, rng)
    _moon_tree(cv, 18, 250, 0.72, rng)


def _flower_field(
    cv: Canvas,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    count: int,
    rng: np.random.Generator,
    palette: tuple[Color, ...],
) -> None:
    cv.paint(Ellipse(cx, cy, rx, ry), (70, 140, 110), alpha=0.25, feather=ry * 0.8)
    items = []
    for _ in range(count):
        a = float(rng.uniform(0, math.tau))
        r = math.sqrt(float(rng.uniform(0, 1)))
        items.append((cy + r * ry * math.sin(a), cx + r * rx * math.cos(a)))
    for fy, fx in sorted(items):
        if _keepout(fx, fy, -20):
            continue
        color = palette[int(rng.integers(0, len(palette)))]
        h = float(rng.uniform(4, 8))
        cv.paint(Segment((fx, fy), (fx, fy - h), 0.55), (44, 110, 84))
        cv.paint(Ellipse(fx + 1.4, fy - h * 0.5, 1.6, 0.8), (60, 140, 96))
        for petal in range(5):
            a = petal * math.tau / 5
            cv.paint(Circle(fx + 1.5 * math.cos(a), fy - h + 1.2 * math.sin(a), 1.25), color)
        cv.paint(Circle(fx, fy - h, 0.8), (255, 246, 190))
        cv.glow(fx, fy - h, 7, color, 0.22)


def paint_flower_fields(cv: Canvas, rng: np.random.Generator) -> None:
    blue = ((156, 224, 255), (206, 170, 255), (242, 242, 255))
    pink = ((255, 146, 200), (255, 190, 220), (255, 234, 146))
    for cx, cy, rx, ry, count, palette in (
        (760, 300, 60, 22, 46, blue),
        (620, 420, 52, 18, 36, pink),
        (470, 468, 44, 14, 26, blue),
        (820, 600, 70, 20, 40, pink),
        (560, 250, 44, 12, 24, pink),
        (230, 612, 40, 12, 24, pink),
    ):
        _flower_field(cv, cx, cy, rx, ry, count, rng, palette)


def paint_scatter(cv: Canvas, rng: np.random.Generator) -> None:
    for cluster in CRYSTAL_CLUSTERS:
        _crystal_cluster(cv, *cluster)
    placed: list[tuple[float, float, float]] = []

    def free(x: float, y: float, r: float) -> bool:
        if _keepout(x, y, r * 0.5) or _in_text_band(x, y):
            return False
        for cx, cy, _, _ in CRYSTAL_CLUSTERS:
            if math.hypot(x - cx, (y - cy) * 1.6) < 40 + r:
                return False
        for rx, ry in REED_CLUMPS:
            if math.hypot(x - rx, y - ry) < 18 + r:
                return False
        return all(math.hypot(x - px, y - py) > pr + r + 6 for px, py, pr in placed)

    # Rocks, bushes, and glowing mushrooms, depth-sorted so nearer ones overlap.
    props: list[tuple[float, float, str, float]] = []
    attempts = 0
    while len(props) < 40 and attempts < 4000:
        attempts += 1
        x = float(rng.uniform(10, WIDTH - 10))
        y = float(rng.uniform(HORIZON + 20, HEIGHT - 60))
        depth = (y - HORIZON) / (HEIGHT - HORIZON)
        kind = str(rng.choice(("rock", "rock", "bush", "mushroom", "tuft", "tuft", "flowers")))
        r = (6 + 10 * depth) * (1.2 if kind == "rock" else 1.0)
        if not free(x, y, r):
            continue
        placed.append((x, y, r))
        props.append((y, x, kind, r))
    for y, x, kind, _radius in sorted(props):
        depth = (y - HORIZON) / (HEIGHT - HORIZON)
        if kind == "rock":
            _rock(cv, x, y, 4 + 8 * depth, rng)
        elif kind == "bush":
            _flower_bush(cv, x, y)
        elif kind == "tuft":
            _tuft(cv, x, y, 8 + 10 * depth, rng, GRASS_MID, GRASS_LIGHT)
            _tuft(cv, x + 5, y + 2, 6 + 8 * depth, rng, GRASS_DARK, GRASS_MID)
        elif kind == "mushroom":
            _mushrooms(cv, x, y, 0.7 + 0.6 * depth)
        else:
            for _ in range(7):
                fx, fy = x + float(rng.uniform(-12, 12)), y + float(rng.uniform(-5, 5))
                color = FLOWERS[int(rng.integers(0, len(FLOWERS)))]
                cv.paint(Segment((fx, fy), (fx, fy - 5), 0.5), (50, 120, 90))
                cv.paint(Circle(fx, fy - 5.5, 1.6), color)
                cv.glow(fx, fy - 5.5, 5, color, 0.25)


def paint_grass(cv: Canvas, rng: np.random.Generator) -> None:
    """Thousands of tapered blades, larger and darker toward the viewer."""
    light_noise = Fbm(91, WIDTH, HEIGHT, 120, 3)
    blades: list[tuple[float, float]] = []
    for _ in range(7600):
        x = float(rng.uniform(0, WIDTH))
        y = float(rng.uniform(HORIZON + 8, HEIGHT + 4))
        if y < _ground_edge(x) + 4:
            continue
        if trail_distance(x, y) < 22 or _keepout(x, y, -24) or _in_text_band(x, y):
            continue
        blades.append((y, x))
    blades.sort()
    for y, x in blades:
        depth = (y - HORIZON) / (HEIGHT - HORIZON)
        h = 3.5 + 11 * depth * float(rng.uniform(0.6, 1.2))
        lean = float(rng.uniform(-0.5, 0.5)) * h
        light = float(light_noise(np.asarray([x]), np.asarray([y]))[0])
        lit = min(1.0, max(0.0, (light - 0.3) * 1.8 + (1 - depth) * 0.3))
        base = mix(GRASS_DARK, GRASS_MID, 0.4 + 0.4 * (1 - depth))
        tip = mix(GRASS_LIGHT, GRASS_MOON, lit * 0.8)
        width = 0.55 + 0.75 * depth
        points = [(x, y), (x + lean * 0.3, y - h * 0.5), (x + lean, y - h)]
        cv.paint(Stroke(points, width, 0.15), base)
        cv.paint(Stroke(points[1:], width * 0.7, 0.12), tip, alpha=0.9)
    # Trail-edge tufts overhang the path so it sits inside the meadow.
    for index in range(0, len(TRAIL_POINTS) - 1, 2):
        x, y = TRAIL_POINTS[index]
        nx, ny = TRAIL_POINTS[index + 1]
        dx, dy = nx - x, ny - y
        length = math.hypot(dx, dy) or 1.0
        px, py = -dy / length, dx / length
        for side in (-1, 1):
            if rng.random() < 0.55:
                w = trail_width(index) + 2.5
                tx, ty = x + px * w * side, y + py * w * side
                if _keepout(tx, ty, -26) and trail_distance(tx, ty) >= 30 - 26:
                    depth = (ty - HORIZON) / (HEIGHT - HORIZON)
                    _tuft(cv, tx, ty, 5 + 7 * depth, rng, GRASS_MID, GRASS_LIGHT)


def paint_ant_colonies(cv: Canvas) -> None:
    """A dusty ant highway, a hill, and a crystal-crumb stash per colony."""
    for trail in ANT_TRAILS:
        loop = [*trail.loop, trail.loop[0]]
        highway = Union(*(Segment(a, b, 7.5) for a, b in zip(loop, loop[1:], strict=False)))
        cv.paint(highway, (38, 58, 56), alpha=0.4, feather=3.0)
        cv.paint(highway.grow(-2.5), (120, 108, 92), alpha=0.6, feather=1.8)
        hx, hy = trail.hill
        cv.paint(Ellipse(hx, hy + 3, 18, 5), (8, 14, 20), alpha=0.5, feather=2)
        mound = Ellipse(hx, hy, 16, 9) & Box(hx - 20, hy - 12, hx + 20, hy + 4)
        cv.part(
            mound,
            (150, 120, 96),
            line=(40, 32, 38),
            line_width=1.0,
            shade=(104, 82, 70),
            shade_offset=(2, -2),
            rim=(214, 186, 150),
            rim_offset=(-1, 1.2),
        )
        cv.paint(Ellipse(hx + 1, hy - 5, 3.2, 1.8), (30, 22, 24))
        far = max(trail.loop, key=lambda point: point[0])
        sx, sy = far[0] + 7, far[1] - 2
        for dx, dy, r in ((-3, 1, 2.2), (2, 0, 2.6), (0, -3, 2.0), (4, -2, 1.6)):
            cv.paint(Poly(star_points(sx + dx, sy + dy, r + 0.8, r * 0.5, 4)), CYAN_LIGHT)
        cv.glow(sx, sy - 1, 14, (80, 210, 255), 0.4)


def paint_lighting(cv: Canvas) -> None:
    """Moonlight from the upper right, then a gentle vignette."""
    cv.glow(760, 120, 620, (46, 64, 96), 0.45, power=1.6)
    cv.glow(WIDTH / 2, HEIGHT * 0.55, 460, (30, 40, 60), 0.2, power=1.5)

    def vignette(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        nx = (x - WIDTH / 2) / (WIDTH * 0.62)
        ny = (y - HEIGHT * 0.46) / (HEIGHT * 0.62)
        return np.clip((np.hypot(nx, ny) - 0.62) * 1.25, 0, 0.55)

    cv.paint(None, (4, 6, 20), mode="over", mask=vignette, box=(0, 0, WIDTH, HEIGHT))
    # A calm, darker backing behind the HUD's bottom feedback lines.
    cv.paint(
        Box(340, 516, 920, 596, 30),
        (6, 12, 24),
        alpha=0.22,
        feather=22,
    )


def paint_background() -> Canvas:
    rng = np.random.default_rng(20260930)
    cv = Canvas(WIDTH, HEIGHT, ss=2)
    paint_sky(cv, rng)
    paint_moon(cv)
    paint_clouds(cv)
    paint_distance(cv, rng)
    paint_ground(cv)
    paint_pond(cv)
    paint_ant_colonies(cv)
    paint_trail(cv, rng)
    paint_grass(cv, rng)
    paint_start_camp(cv)
    paint_clearing(cv)
    paint_flower_fields(cv, rng)
    paint_scatter(cv, rng)
    paint_trees(cv, rng)
    paint_shrine(cv)
    paint_lighting(cv)
    return cv


# Foreground ---------------------------------------------------------------------------

FG_DARK: Color = (8, 20, 28)
FG_MID: Color = (14, 36, 42)
FG_RIM: Color = (60, 110, 120)


def _frond(
    cv: Canvas, base: tuple[float, float], tip: tuple[float, float], width: float, bend: float
) -> None:
    bx, by = base
    tx, ty = tip
    mx, my = (bx + tx) / 2 + bend, (by + ty) / 2 - abs(bend) * 0.4
    spine = [(bx, by), (mx, my), (tx, ty)]
    cv.paint(Stroke(spine, width, 0.4), FG_MID)
    steps = 9
    for index in range(1, steps):
        t = index / steps
        px = (1 - t) ** 2 * bx + 2 * (1 - t) * t * mx + t * t * tx
        py = (1 - t) ** 2 * by + 2 * (1 - t) * t * my + t * t * ty
        leaf = width * 2.6 * (1 - t * 0.7)
        for side in (-1, 1):
            cv.paint(
                Stroke([(px, py), (px + side * leaf, py - leaf * 0.5)], width * 0.7, 0.3), FG_DARK
            )
    cv.paint(Stroke(spine[1:], width * 0.35, 0.2), FG_RIM, alpha=0.5)


def paint_foreground() -> Canvas:
    """Dark framing plants in the bottom corners and a thin bottom fringe."""
    rng = np.random.default_rng(7)
    cv = Canvas(WIDTH, HEIGHT, ss=2)
    # Bottom-left ferns, kept below the shrine steps.
    for base, tip, width, bend in (
        ((-6, 648), (62, 598), 2.4, -8),
        ((12, 650), (104, 622), 2.0, -4),
        ((-4, 632), (24, 580), 2.0, 6),
    ):
        _frond(cv, base, tip, width, bend)
    # Bottom-right: a mossy rock half out of frame behind broad leaves.
    rock = blob([(948, 646, 40), (918, 660, 30), (972, 616, 24)], smooth=10)
    cv.paint(rock.grow(1.2), (4, 10, 16))
    cv.paint(rock, linear((960, 590), (900, 650), ((0, (30, 48, 66)), (1, FG_DARK))))
    cv.paint(rock - rock.shift(-3, 4), FG_RIM, alpha=0.6, feather=0.8, clip=rock)
    for base, tip, width, bend in (
        ((968, 648), (888, 604), 2.4, 8),
        ((972, 628), (920, 578), 2.0, 6),
        ((930, 652), (852, 628), 1.8, 5),
    ):
        _frond(cv, base, tip, width, bend)
    # A low grass fringe along the bottom edge, thinnest in the middle.
    for _ in range(190):
        x = float(rng.uniform(0, WIDTH))
        edge_weight = min(1.0, abs(x - WIDTH / 2) / (WIDTH / 2) + 0.15)
        h = float(rng.uniform(4, 15)) * edge_weight
        lean = float(rng.uniform(-4, 4))
        y = HEIGHT + 3
        cv.paint(
            Stroke([(x, y), (x + lean * 0.4, y - h * 0.55), (x + lean, y - h)], 1.4, 0.2), FG_DARK
        )
        if rng.random() < 0.35:
            cv.paint(
                Stroke([(x + lean * 0.4, y - h * 0.55), (x + lean, y - h)], 0.6, 0.15),
                FG_RIM,
                alpha=0.6,
            )
    return cv
