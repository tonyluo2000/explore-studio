"""The Moon Compass, the Crystal Lantern, and the swaying reed clumps.

The Moon Compass is student-colored, so its art is split into layers that are
drawn in order at the Compass's own x/y:

* ``ring`` — the rune ring and gem sockets in neutral greys. The runtime
  multiplies this layer by the student's color, so any color stays meaningful.
  Its columns turn the 8-fold rune ring through 45 degrees for a seamless loop.
* ``body`` — the untinted brass bezel, the star-chart face, the north marker,
  and white glints that stay white on any ring color.
* ``glass`` — the dome sheen, drawn last over the needle.

The needle is its own sheet with 64 pre-rotated angles, so it turns smoothly
without any runtime rotation.

The Crystal Lantern's glow and rays are runtime effects; the sheet holds the
brass lantern and its flickering crystal flame. The reeds sheet holds one
cattail clump at nine lean angles for the ambient sway.
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
    Rotate,
    Segment,
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

# ---------------------------------------------------------------------------
# Moon Compass
# ---------------------------------------------------------------------------

COMPASS_FRAME = (80, 60)
#: The face center matches the runtime aura center (x + w/2, y + 0.45 h).
COMPASS_CENTER = (40.0, 27.0)
COMPASS_RADIUS = 25.0
COMPASS_ROWS = ("ring", "body", "glass")
COMPASS_SPIN = tuple(f"spin-{index:02d}" for index in range(12))
NEEDLE_COLUMNS = tuple(f"angle-{index:02d}" for index in range(64))
#: The neutral accent: the ring is drawn for white and tinted at runtime.
COMPASS_ACCENT: Color = (255, 255, 255)

BRASS: Color = (236, 196, 110)
BRASS_SHADE: Color = (170, 118, 60)
BRASS_LIGHT: Color = (255, 238, 180)
FACE: Color = (246, 242, 228)
FACE_EDGE: Color = (206, 206, 226)
CHART: Color = (120, 128, 176)
NORTH: Color = (240, 70, 84)
NEEDLE_SOUTH: Color = (228, 234, 250)


def compass_frame(row: str, column: str) -> Image.Image:
    cv = Canvas(*COMPASS_FRAME, SS)
    cx, cy = COMPASS_CENTER
    r = COMPASS_RADIUS
    spin = int(column.rpartition("-")[2]) / len(COMPASS_SPIN) * (math.tau / 8)
    if row == "ring":
        outer = Circle(cx, cy, r)
        inner = Circle(cx, cy, r - 5.2)
        band = outer - inner
        cv.paint(outer.grow(1.4), (70, 70, 80))
        cv.paint(
            band,
            radial(
                cx + 8,
                cy - 10,
                r * 1.8,
                ((0, (252, 252, 252)), (0.6, (214, 214, 218)), (1, (150, 150, 158))),
            ),
        )
        cv.paint(band - band.shift(1.4, -1.8), (132, 132, 140), alpha=0.8, feather=0.4, clip=band)
        # Eight rune notches and dots turn with the ring.
        for index in range(8):
            a = spin + index * math.tau / 8
            px, py = cx + (r - 2.6) * math.cos(a), cy + (r - 2.6) * math.sin(a)
            rune = Rotate(Poly(star_points(px, py, 1.9, 0.8, 4)), a, px, py)
            cv.paint(rune, (255, 255, 255))
            ma = a + math.tau / 16
            cv.paint(
                Circle(cx + (r - 2.6) * math.cos(ma), cy + (r - 2.6) * math.sin(ma), 0.7),
                (120, 120, 130),
            )
        return cv.image()
    if row == "body":
        bezel = Circle(cx, cy, r - 5.0)
        cv.paint(bezel.grow(0.8), LINE)
        cv.paint(
            bezel,
            linear(
                (cx + 10, cy - 14),
                (cx - 10, cy + 14),
                ((0, BRASS_LIGHT), (0.5, BRASS), (1, BRASS_SHADE)),
            ),
        )
        face = Circle(cx, cy, r - 7.6)
        cv.paint(face.grow(0.6), (120, 90, 60))
        cv.paint(face, radial(cx + 4, cy - 5, r, ((0, WHITE), (0.6, FACE), (1, FACE_EDGE))))
        # Star-chart rose and ticks.
        cv.paint(Poly(star_points(cx, cy, r - 9.5, 2.4, 4)), mix(CHART, FACE, 0.45))
        cv.paint(
            Poly(star_points(cx, cy, r - 12.5, 1.6, 4, rotation=math.pi / 4)), mix(CHART, FACE, 0.6)
        )
        for index in range(16):
            a = index * math.tau / 16
            length = 2.4 if index % 4 == 0 else 1.2
            start = r - 8.2
            cv.paint(
                Segment(
                    (cx + start * math.cos(a), cy + start * math.sin(a)),
                    (cx + (start - length) * math.cos(a), cy + (start - length) * math.sin(a)),
                    0.45,
                ),
                CHART,
            )
        for sx, sy in ((cx - 6, cy - 7), (cx + 7, cy + 5), (cx - 5, cy + 8), (cx + 5, cy - 9)):
            cv.paint(Circle(sx, sy, 0.6), CHART)
        # North marker: a bright red-and-gold crown notch on the bezel.
        north = Poly([(cx, cy - r + 1.2), (cx + 3.6, cy - r + 6.6), (cx - 3.6, cy - r + 6.6)])
        cv.paint(north.grow(0.8), LINE)
        cv.paint(north, NORTH)
        cv.paint(Circle(cx, cy - r + 3.6, 0.8), WHITE)
        # Cardinal gem sockets that catch the moonlight.
        for index in range(4):
            a = index * math.tau / 4 + math.tau / 8
            gx, gy = cx + (r - 2.6) * math.cos(a), cy + (r - 2.6) * math.sin(a)
            cv.paint(Circle(gx, gy, 2.2).grow(0.7), LINE)
            cv.paint(
                Circle(gx, gy, 2.2),
                radial(gx - 0.6, gy - 0.6, 2.8, ((0, WHITE), (1, (190, 210, 255)))),
            )
        # Glints that stay white on any student ring color.
        cv.paint(
            Stroke([(cx + r * 0.52, cy - r * 0.8), (cx + r * 0.8, cy - r * 0.5)], 1.1, 0.6),
            WHITE,
            alpha=0.9,
        )
        cv.paint(Circle(cx - r * 0.86, cy + r * 0.32, 0.9), WHITE, alpha=0.8)
        return cv.image()
    # glass
    dome = Circle(cx, cy, r - 7.6)
    cv.paint(dome, (200, 230, 255), alpha=0.08)
    cv.paint(
        Stroke([(cx - 9, cy - 4), (cx - 5, cy - 10), (cx + 1, cy - 12)], 1.5, 0.7),
        WHITE,
        alpha=0.7,
        clip=dome,
    )
    cv.paint(Circle(cx + 7, cy + 8, 1.0), WHITE, alpha=0.6, clip=dome)
    return cv.image()


def needle_frame(column: str) -> Image.Image:
    cv = Canvas(*COMPASS_FRAME, SS)
    cx, cy = COMPASS_CENTER
    angle = int(column.rpartition("-")[2]) / len(NEEDLE_COLUMNS) * math.tau
    length = COMPASS_RADIUS - 9.4
    width = 3.0

    def turn(shape):  # type: ignore[no-untyped-def]
        return Rotate(shape, angle, cx, cy)

    north = turn(Poly([(cx, cy - length), (cx + width, cy), (cx - width, cy)]))
    south = turn(Poly([(cx, cy + length * 0.85), (cx - width, cy), (cx + width, cy)]))
    cv.paint(Union(north, south).grow(0.8), LINE)
    cv.paint(Union(north, south).grow(1.6).shift(0.8, 1.2), (0, 0, 0), alpha=0.18)
    cv.paint(south, NEEDLE_SOUTH)
    cv.paint(turn(Poly([(cx, cy + length * 0.85), (cx + width, cy), (cx, cy)])), (170, 180, 210))
    cv.paint(north, NORTH)
    cv.paint(turn(Poly([(cx, cy - length), (cx + width, cy), (cx, cy)])), (186, 40, 64))
    cap = Circle(cx, cy, 2.6)
    cv.paint(cap.grow(0.7), LINE)
    cv.paint(cap, radial(cx - 0.8, cy - 0.8, 3.2, ((0, BRASS_LIGHT), (1, BRASS))))
    cv.paint(Circle(cx - 0.7, cy - 0.7, 0.8), WHITE)
    return cv.image()


# ---------------------------------------------------------------------------
# Crystal Lantern
# ---------------------------------------------------------------------------

LANTERN_FRAME = (80, 60)
LANTERN_ACCENT: Color = (240, 210, 50)
LANTERN_COLUMNS = ("flicker-0", "flicker-1", "flicker-2", "flicker-3")
LANTERN_ROWS = ("glow",)
BRONZE: Color = (186, 124, 60)
BRONZE_DARK: Color = (112, 66, 36)
BRONZE_LIGHT: Color = (244, 190, 110)
AMBER: Color = (255, 196, 84)
CORE: Color = (255, 250, 222)
EMBER: Color = (255, 150, 50)


def lantern_frame(column: str) -> Image.Image:
    cv = Canvas(*LANTERN_FRAME, SS)
    index = int(column.rpartition("-")[2])
    cx = 40.0
    flame = (1.0, 1.1, 0.92, 1.04)[index]
    lean = (0.0, 0.8, -0.6, 0.3)[index]
    # A soft baked halo inside the glass so the lantern reads as lit.
    cv.paint(Circle(cx, 31, 20), (255, 200, 110), alpha=0.18, feather=8)
    # Stone pedestal.
    plinth = Box(cx - 16, 50, cx + 16, 58, 2.5)
    cv.part(
        plinth,
        (170, 150, 150),
        line=LINE,
        line_width=1.0,
        shade=(116, 100, 112),
        shade_offset=(0, -2.5),
    )
    cv.paint(Box(cx - 14, 50.5, cx + 14, 52, 1), (230, 210, 190), alpha=0.7)
    # Handle ring and cap.
    handle = Circle(cx, 7.5, 5.2) - Circle(cx, 7.5, 3.4)
    cv.paint(handle.grow(0.8), LINE)
    cv.paint(handle, BRONZE_LIGHT)
    cap = Poly([(cx - 13, 17), (cx + 13, 17), (cx + 7, 10), (cx - 7, 10)])
    cv.part(
        cap,
        linear((cx + 10, 10), (cx - 10, 17), ((0, BRONZE_LIGHT), (1, BRONZE))),
        line=LINE,
        line_width=1.1,
        shade=BRONZE_DARK,
        shade_offset=(1.5, -2),
    )
    cv.paint(Circle(cx, 9.6, 1.9), AMBER)
    # Glass body glowing from within.
    glass = Poly(
        [
            (cx - 11, 17),
            (cx + 11, 17),
            (cx + 12.5, 31),
            (cx + 10, 45),
            (cx - 10, 45),
            (cx - 12.5, 31),
        ]
    )
    cv.paint(glass.grow(1.2), LINE)
    cv.paint(glass, radial(cx, 31, 18, ((0, (255, 244, 190)), (0.55, AMBER), (1, (230, 140, 50)))))
    cv.paint(glass - glass.shift(-2, 0), (255, 250, 220), alpha=0.5, clip=glass)
    # The crystal flame.
    h = 11.5 * flame
    w = 6.4 / flame
    center = (cx, 32.0)
    crystal = Poly(
        [
            (center[0] + lean, center[1] - h),
            (center[0] + w, center[1] - 1),
            (center[0] + w * 0.6, center[1] + h * 0.7),
            (center[0] - w * 0.6, center[1] + h * 0.7),
            (center[0] - w, center[1] - 1),
        ]
    )
    cv.paint(crystal.grow(2.2), (255, 230, 150), alpha=0.6, feather=1.5)
    cv.paint(
        crystal,
        linear(
            (center[0], center[1] - h),
            (center[0], center[1] + h),
            ((0, CORE), (0.6, (255, 226, 130)), (1, EMBER)),
        ),
    )
    cv.paint(
        Poly(
            [
                (center[0] + lean, center[1] - h),
                (center[0], center[1] + h * 0.7),
                (center[0] - w * 0.6, center[1] + h * 0.7),
                (center[0] - w, center[1] - 1),
            ]
        ),
        WHITE,
        alpha=0.45,
        clip=crystal,
    )
    cv.paint(Circle(center[0], center[1] + 1, 1.6), WHITE)
    # Bronze cage bars over the glass.
    for bar in (-7.0, 0.0, 7.0):
        cv.paint(
            Segment((cx + bar * 1.05, 17.5), (cx + bar * 0.95, 44.5), 0.9 if bar else 0.6),
            BRONZE_DARK,
            alpha=0.9 if bar else 0.45,
        )
    cv.paint(Stroke([(cx - 8.5, 20), (cx - 9.5, 30)], 1.0, 0.6), WHITE, alpha=0.8)
    base = Box(cx - 14, 44, cx + 14, 50.5, 2)
    cv.part(
        base,
        linear((cx + 10, 44), (cx - 10, 50), ((0, BRONZE_LIGHT), (1, BRONZE))),
        line=LINE,
        line_width=1.1,
        shade=BRONZE_DARK,
        shade_offset=(1.5, -2),
    )
    for gem_x in (cx - 8, cx, cx + 8):
        cv.paint(Circle(gem_x, 47.2, 1.3), (120, 230, 255))
    return cv.image()


# ---------------------------------------------------------------------------
# Reeds
# ---------------------------------------------------------------------------

REED_FRAME = (32, 44)
REED_ROWS = ("sway",)
REED_COLUMNS = tuple(f"sway-{index}" for index in range(9))
REED_ACCENT: Color = (70, 110, 94)


def reed_frame(column: str) -> Image.Image:
    cv = Canvas(*REED_FRAME, SS)
    lean = (int(column.rpartition("-")[2]) - 4) / 4
    base_y = 42.0
    blades = (
        (-6, 22, -0.5, (40, 104, 84)),
        (-2, 32, -0.1, (64, 138, 104)),
        (2, 28, 0.2, (46, 116, 92)),
        (6, 20, 0.6, (78, 156, 112)),
        (9, 14, 0.9, (40, 104, 84)),
    )
    cv.paint(Ellipse(16, base_y, 10, 2.2), (6, 14, 20), alpha=0.45, feather=1.2)
    for dx, h, bias, color in blades:
        bx = 16 + dx
        bend = (lean * 5 + bias * 4) * h / 30
        points = [(bx, base_y), (bx + bend * 0.3, base_y - h * 0.55), (bx + bend, base_y - h)]
        cv.paint(Stroke(points, 1.4, 0.2).grow(0.5), (14, 34, 40))
        cv.paint(Stroke(points, 1.4, 0.2), color)
        cv.paint(Stroke(points[1:], 0.6, 0.1), mix(color, (200, 240, 210), 0.35), alpha=0.8)
    for dx, h in ((-1.5, 34), (3.5, 29)):
        bx = 16 + dx
        bend = lean * 5 * h / 30
        stem = [(bx, base_y), (bx + bend * 0.3, base_y - h * 0.55), (bx + bend, base_y - h)]
        cv.paint(Stroke(stem, 0.7).grow(0.4), (14, 34, 40))
        cv.paint(Stroke(stem, 0.7), (96, 150, 110))
        tx, ty = bx + bend * 0.92, base_y - h * 0.86
        head = Rotate(Box(tx - 2.2, ty - 5, tx + 2.2, ty + 5, 2.2), bend * 0.03, tx, ty)
        cv.paint(head.grow(0.6), (30, 20, 24))
        cv.paint(head, (148, 96, 70))
        cv.paint(head - head.shift(1, 0), (190, 140, 100), alpha=0.8, clip=head)
    return cv.image()
