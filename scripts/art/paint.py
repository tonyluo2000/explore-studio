"""A tiny signed-distance-field painter for the course-owned trusted art.

This is build-time tooling only (numpy + Pillow); the runtime never imports it.
Every shape is a signed distance function evaluated inside its own bounding
box, so edges are analytically anti-aliased, outlines are simple offsets, and
soft shading is a feathered difference of two shapes. A canvas stores
premultiplied RGBA in float32 at ``ss`` samples per final pixel and is
box-filtered down when finished. Everything is deterministic: noise comes from
seeded generators and nothing reads the clock or the network.

Coordinates are always in final pixels, with (0, 0) at the top-left corner.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
from PIL import Image

Color = tuple[int, int, int]
Point = tuple[float, float]
Paint = Color | Callable[[np.ndarray, np.ndarray], np.ndarray]
BBox = tuple[float, float, float, float]

_EMPTY: BBox = (0.0, 0.0, 0.0, 0.0)


def rgb(value: Color) -> np.ndarray:
    return np.asarray(value, np.float32) / 255.0


def mix(first: Color, second: Color, amount: float) -> Color:
    amount = max(0.0, min(1.0, amount))
    return tuple(  # type: ignore[return-value]
        round(a + (b - a) * amount) for a, b in zip(first, second, strict=True)
    )


def smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((value - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _union_box(boxes: Sequence[BBox]) -> BBox:
    boxes = [box for box in boxes if box != _EMPTY]
    if not boxes:
        return _EMPTY
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


# ---------------------------------------------------------------------------
# Shapes
# ---------------------------------------------------------------------------


class Shape:
    """A signed distance field: negative inside, positive outside (pixels)."""

    def sdf(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def bbox(self) -> BBox:
        raise NotImplementedError

    # Combinators -----------------------------------------------------------

    def __or__(self, other: Shape) -> Shape:
        return Union(self, other)

    def __sub__(self, other: Shape) -> Shape:
        return Subtract(self, other)

    def __and__(self, other: Shape) -> Shape:
        return Intersect(self, other)

    def grow(self, amount: float) -> Shape:
        return Offset(self, amount)

    def shift(self, dx: float, dy: float) -> Shape:
        return Shift(self, dx, dy)


@dataclass(frozen=True)
class Circle(Shape):
    cx: float
    cy: float
    r: float

    def sdf(self, x, y):  # type: ignore[no-untyped-def]
        return np.hypot(x - self.cx, y - self.cy) - self.r

    def bbox(self) -> BBox:
        return (self.cx - self.r, self.cy - self.r, self.cx + self.r, self.cy + self.r)


@dataclass(frozen=True)
class Ellipse(Shape):
    cx: float
    cy: float
    rx: float
    ry: float

    def sdf(self, x, y):  # type: ignore[no-untyped-def]
        px, py = (x - self.cx), (y - self.cy)
        k0 = np.hypot(px / self.rx, py / self.ry)
        k1 = np.hypot(px / (self.rx * self.rx), py / (self.ry * self.ry))
        return np.where(k1 > 1e-9, k0 * (k0 - 1) / np.maximum(k1, 1e-9), -min(self.rx, self.ry))

    def bbox(self) -> BBox:
        return (self.cx - self.rx, self.cy - self.ry, self.cx + self.rx, self.cy + self.ry)


@dataclass(frozen=True)
class Box(Shape):
    x0: float
    y0: float
    x1: float
    y1: float
    radius: float = 0.0

    def sdf(self, x, y):  # type: ignore[no-untyped-def]
        cx, cy = (self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2
        hx, hy = (self.x1 - self.x0) / 2, (self.y1 - self.y0) / 2
        r = min(self.radius, hx, hy)
        qx = np.abs(x - cx) - hx + r
        qy = np.abs(y - cy) - hy + r
        outside = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0))
        inside = np.minimum(np.maximum(qx, qy), 0)
        return outside + inside - r

    def bbox(self) -> BBox:
        return (self.x0, self.y0, self.x1, self.y1)


@dataclass(frozen=True)
class Segment(Shape):
    """A capsule whose radius tapers from ``r0`` at ``p0`` to ``r1`` at ``p1``."""

    p0: Point
    p1: Point
    r0: float
    r1: float | None = None

    def sdf(self, x, y):  # type: ignore[no-untyped-def]
        r1 = self.r0 if self.r1 is None else self.r1
        ax, ay = self.p0
        bx, by = self.p1
        dx, dy = bx - ax, by - ay
        length2 = dx * dx + dy * dy
        if length2 < 1e-9:
            return np.hypot(x - ax, y - ay) - self.r0
        t = np.clip(((x - ax) * dx + (y - ay) * dy) / length2, 0.0, 1.0)
        return np.hypot(x - (ax + t * dx), y - (ay + t * dy)) - (self.r0 + (r1 - self.r0) * t)

    def bbox(self) -> BBox:
        r = max(self.r0, self.r0 if self.r1 is None else self.r1)
        return (
            min(self.p0[0], self.p1[0]) - r,
            min(self.p0[1], self.p1[1]) - r,
            max(self.p0[0], self.p1[0]) + r,
            max(self.p0[1], self.p1[1]) + r,
        )


class Stroke(Shape):
    """A polyline whose radius tapers along its length (blades, tails, stems)."""

    def __init__(self, points: Sequence[Point], r0: float, r1: float | None = None) -> None:
        r1 = r0 if r1 is None else r1
        lengths = [0.0]
        for a, b in zip(points, points[1:], strict=False):
            lengths.append(lengths[-1] + math.dist(a, b))
        total = lengths[-1] or 1.0
        self.segments = [
            Segment(
                a,
                b,
                r0 + (r1 - r0) * lengths[index] / total,
                r0 + (r1 - r0) * lengths[index + 1] / total,
            )
            for index, (a, b) in enumerate(zip(points, points[1:], strict=False))
        ]

    def sdf(self, x, y):  # type: ignore[no-untyped-def]
        result = self.segments[0].sdf(x, y)
        for segment in self.segments[1:]:
            result = np.minimum(result, segment.sdf(x, y))
        return result

    def bbox(self) -> BBox:
        return _union_box([segment.bbox() for segment in self.segments])


class Poly(Shape):
    """Exact signed distance to a simple polygon."""

    def __init__(self, points: Sequence[Point]) -> None:
        self.points = np.asarray(points, np.float64)

    def sdf(self, x, y):  # type: ignore[no-untyped-def]
        v = self.points
        d = (x - v[0, 0]) ** 2 + (y - v[0, 1]) ** 2
        sign = np.ones_like(x)
        count = len(v)
        for i in range(count):
            j = i - 1
            ex, ey = v[j, 0] - v[i, 0], v[j, 1] - v[i, 1]
            wx, wy = x - v[i, 0], y - v[i, 1]
            denom = ex * ex + ey * ey or 1e-9
            t = np.clip((wx * ex + wy * ey) / denom, 0, 1)
            bx, by = wx - ex * t, wy - ey * t
            d = np.minimum(d, bx * bx + by * by)
            c1 = y >= v[i, 1]
            c2 = y < v[j, 1]
            c3 = ex * wy > ey * wx
            flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
            sign = np.where(flip, -sign, sign)
        return sign * np.sqrt(d)

    def bbox(self) -> BBox:
        return (
            float(self.points[:, 0].min()),
            float(self.points[:, 1].min()),
            float(self.points[:, 0].max()),
            float(self.points[:, 1].max()),
        )


class Union(Shape):
    def __init__(self, *shapes: Shape, smooth: float = 0.0) -> None:
        self.shapes = shapes
        self.smooth = smooth

    def sdf(self, x, y):  # type: ignore[no-untyped-def]
        result = self.shapes[0].sdf(x, y)
        k = self.smooth
        for shape in self.shapes[1:]:
            other = shape.sdf(x, y)
            if k > 0:
                h = np.clip(0.5 + 0.5 * (other - result) / k, 0, 1)
                result = other + (result - other) * h - k * h * (1 - h)
            else:
                result = np.minimum(result, other)
        return result

    def bbox(self) -> BBox:
        return _union_box([shape.bbox() for shape in self.shapes])


@dataclass(frozen=True)
class Subtract(Shape):
    base: Shape
    cut: Shape

    def sdf(self, x, y):  # type: ignore[no-untyped-def]
        return np.maximum(self.base.sdf(x, y), -self.cut.sdf(x, y))

    def bbox(self) -> BBox:
        return self.base.bbox()


@dataclass(frozen=True)
class Intersect(Shape):
    first: Shape
    second: Shape

    def sdf(self, x, y):  # type: ignore[no-untyped-def]
        return np.maximum(self.first.sdf(x, y), self.second.sdf(x, y))

    def bbox(self) -> BBox:
        a, b = self.first.bbox(), self.second.bbox()
        return (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))


@dataclass(frozen=True)
class Offset(Shape):
    shape: Shape
    amount: float

    def sdf(self, x, y):  # type: ignore[no-untyped-def]
        return self.shape.sdf(x, y) - self.amount

    def bbox(self) -> BBox:
        x0, y0, x1, y1 = self.shape.bbox()
        a = max(0.0, self.amount)
        return (x0 - a, y0 - a, x1 + a, y1 + a)


@dataclass(frozen=True)
class Shift(Shape):
    shape: Shape
    dx: float
    dy: float

    def sdf(self, x, y):  # type: ignore[no-untyped-def]
        return self.shape.sdf(x - self.dx, y - self.dy)

    def bbox(self) -> BBox:
        x0, y0, x1, y1 = self.shape.bbox()
        return (x0 + self.dx, y0 + self.dy, x1 + self.dx, y1 + self.dy)


@dataclass(frozen=True)
class Rotate(Shape):
    shape: Shape
    angle: float
    cx: float
    cy: float

    def sdf(self, x, y):  # type: ignore[no-untyped-def]
        c, s = math.cos(-self.angle), math.sin(-self.angle)
        dx, dy = x - self.cx, y - self.cy
        return self.shape.sdf(self.cx + dx * c - dy * s, self.cy + dx * s + dy * c)

    def bbox(self) -> BBox:
        x0, y0, x1, y1 = self.shape.bbox()
        corners = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
        c, s = math.cos(self.angle), math.sin(self.angle)
        moved = [
            (
                self.cx + (px - self.cx) * c - (py - self.cy) * s,
                self.cy + (px - self.cx) * s + (py - self.cy) * c,
            )
            for px, py in corners
        ]
        return (
            min(p[0] for p in moved),
            min(p[1] for p in moved),
            max(p[0] for p in moved),
            max(p[1] for p in moved),
        )


def blob(circles: Sequence[tuple[float, float, float]], smooth: float = 4.0) -> Shape:
    """Smoothly merged circles: clouds, bushes, canopies, mounds."""
    return Union(*(Circle(x, y, r) for x, y, r in circles), smooth=smooth)


def star_points(
    cx: float, cy: float, outer: float, inner: float, points: int = 5, rotation: float = 0.0
) -> list[Point]:
    result = []
    for index in range(points * 2):
        radius = outer if index % 2 == 0 else inner
        angle = rotation - math.pi / 2 + index * math.pi / points
        result.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return result


def ridge(
    x0: float,
    x1: float,
    base: float,
    height_fn: Callable[[float], float],
    step: float = 4.0,
    bottom: float | None = None,
) -> Poly:
    """A filled silhouette whose top edge follows ``height_fn(x)``."""
    bottom = base + 400 if bottom is None else bottom
    xs = np.arange(x0, x1 + step, step)
    top = [(float(x), float(base - height_fn(float(x)))) for x in xs]
    return Poly([(x0, bottom), *top, (x1, bottom)])


# ---------------------------------------------------------------------------
# Paints
# ---------------------------------------------------------------------------


def linear(p0: Point, p1: Point, stops: Sequence[tuple[float, Color]]) -> Paint:
    """A linear gradient from ``p0`` to ``p1`` through ``(t, color)`` stops."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    length2 = dx * dx + dy * dy or 1.0
    positions = np.asarray([t for t, _ in stops], np.float32)
    colors = np.asarray([rgb(c) for _, c in stops], np.float32)

    def paint(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        t = np.clip(((x - p0[0]) * dx + (y - p0[1]) * dy) / length2, 0, 1)
        return np.stack(
            [np.interp(t, positions, colors[:, channel]) for channel in range(3)], axis=-1
        )

    return paint


def radial(cx: float, cy: float, r: float, stops: Sequence[tuple[float, Color]]) -> Paint:
    positions = np.asarray([t for t, _ in stops], np.float32)
    colors = np.asarray([rgb(c) for _, c in stops], np.float32)

    def paint(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        t = np.clip(np.hypot(x - cx, y - cy) / r, 0, 1)
        return np.stack(
            [np.interp(t, positions, colors[:, channel]) for channel in range(3)], axis=-1
        )

    return paint


class Noise:
    """Seeded smooth value noise sampled in final-pixel coordinates."""

    def __init__(self, seed: int, width: int, height: int, cell: float) -> None:
        rng = np.random.default_rng(seed)
        self.cell = cell
        self.columns = int(width / cell) + 3
        self.rows = int(height / cell) + 3
        self.grid = rng.random((self.rows, self.columns)).astype(np.float32)

    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        gx = np.clip(x / self.cell, 0, self.columns - 2.001)
        gy = np.clip(y / self.cell, 0, self.rows - 2.001)
        ix, iy = gx.astype(np.int32), gy.astype(np.int32)
        fx, fy = gx - ix, gy - iy
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        g = self.grid
        top = g[iy, ix] * (1 - fx) + g[iy, ix + 1] * fx
        bottom = g[iy + 1, ix] * (1 - fx) + g[iy + 1, ix + 1] * fx
        return top * (1 - fy) + bottom * fy


class Fbm:
    def __init__(self, seed: int, width: int, height: int, cell: float, octaves: int = 4) -> None:
        self.layers = [
            Noise(seed + octave * 101, width, height, max(1.0, cell / 2**octave))
            for octave in range(octaves)
        ]

    def __call__(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        total = np.zeros_like(x, dtype=np.float32)
        weight_sum = 0.0
        for octave, layer in enumerate(self.layers):
            weight = 0.5**octave
            total += layer(x, y) * weight
            weight_sum += weight
        return total / weight_sum


def textured(base: Paint, noise: Callable, dark: Color, light: Color, amount: float) -> Paint:
    """Modulate a paint toward ``dark``/``light`` by a noise field."""

    def paint(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        color = base(x, y) if callable(base) else np.broadcast_to(rgb(base), (*x.shape, 3))
        n = (noise(x, y) - 0.5) * 2 * amount
        n = n[..., None]
        return np.where(n < 0, color + (rgb(dark) - color) * -n, color + (rgb(light) - color) * n)

    return paint


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------


class Canvas:
    def __init__(self, width: int, height: int, ss: int = 2) -> None:
        self.width, self.height, self.ss = width, height, ss
        self.rgb = np.zeros((height * ss, width * ss, 3), np.float32)
        self.a = np.zeros((height * ss, width * ss), np.float32)

    # Sampling ---------------------------------------------------------------

    def _window(self, box: BBox, pad: float):  # type: ignore[no-untyped-def]
        ss = self.ss
        x0, y0, x1, y1 = box
        j0 = max(0, int(math.floor((x0 - pad) * ss)))
        j1 = min(self.width * ss, int(math.ceil((x1 + pad) * ss)))
        i0 = max(0, int(math.floor((y0 - pad) * ss)))
        i1 = min(self.height * ss, int(math.ceil((y1 + pad) * ss)))
        if j1 <= j0 or i1 <= i0:
            return None
        xs = (np.arange(j0, j1, dtype=np.float32) + 0.5) / ss
        ys = (np.arange(i0, i1, dtype=np.float32) + 0.5) / ss
        x, y = np.meshgrid(xs, ys)
        return (slice(i0, i1), slice(j0, j1)), x, y

    def coverage(self, d: np.ndarray, feather: float) -> np.ndarray:
        if feather > 0:
            return smoothstep(feather, -feather, d)
        return np.clip(0.5 - d * self.ss, 0.0, 1.0)

    # Painting ---------------------------------------------------------------

    def paint(
        self,
        shape: Shape | None,
        color: Paint,
        *,
        alpha: float = 1.0,
        feather: float = 0.0,
        mode: str = "over",
        clip: Shape | None = None,
        clip_feather: float = 0.0,
        mask: Callable[[np.ndarray, np.ndarray], np.ndarray] | None = None,
        box: BBox | None = None,
    ) -> None:
        """Paint ``color`` through ``shape`` (or everywhere inside ``box``)."""
        if box is None:
            box = shape.bbox() if shape is not None else (0, 0, self.width, self.height)
        window = self._window(box, feather + 1.5)
        if window is None:
            return
        region, x, y = window
        cov = (
            self.coverage(shape.sdf(x, y), feather)
            if shape is not None
            else np.ones_like(x, dtype=np.float32)
        )
        if clip is not None:
            cov = cov * self.coverage(clip.sdf(x, y), clip_feather)
        if mask is not None:
            cov = cov * mask(x, y)
        cov = (cov * alpha).astype(np.float32)
        if not np.any(cov > 0):
            return
        col = color(x, y) if callable(color) else np.broadcast_to(rgb(color), (*x.shape, 3))
        c3 = cov[..., None]
        target = self.rgb[region]
        if mode == "over":
            self.rgb[region] = target * (1 - c3) + col * c3
            self.a[region] = self.a[region] * (1 - cov) + cov
        elif mode == "atop":
            a = self.a[region][..., None]
            self.rgb[region] = target * (1 - c3) + col * c3 * a
        elif mode == "add":
            self.rgb[region] = target + col * c3 * self.a[region][..., None]
        elif mode == "add_alpha":
            self.rgb[region] = target + col * c3
            self.a[region] = np.clip(self.a[region] + cov * 0.0, 0, 1)
        elif mode == "screen":
            a = self.a[region][..., None]
            self.rgb[region] = target + (col * a - target * col) * c3
        elif mode == "multiply":
            self.rgb[region] = target * (1 - c3 + col * c3)
        elif mode == "erase":
            self.rgb[region] = target * (1 - c3)
            self.a[region] = self.a[region] * (1 - cov)
        else:  # pragma: no cover - build-time guard
            raise ValueError(mode)

    def fill(self, color: Paint, **options) -> None:  # type: ignore[no-untyped-def]
        self.paint(None, color, **options)

    def glow(
        self,
        cx: float,
        cy: float,
        radius: float,
        color: Color,
        intensity: float,
        *,
        mode: str = "add",
        squash: float = 1.0,
        power: float = 2.0,
    ) -> None:
        """Soft radial light; ``squash`` < 1 flattens it into a ground pool."""

        def falloff(x: np.ndarray, y: np.ndarray) -> np.ndarray:
            d = np.hypot(x - cx, (y - cy) / squash) / radius
            return np.clip(1 - d, 0, 1) ** power

        self.paint(
            None,
            color,
            alpha=intensity,
            mode=mode,
            mask=falloff,
            box=(cx - radius, cy - radius * squash, cx + radius, cy + radius * squash),
        )

    def part(
        self,
        shape: Shape,
        fill: Paint,
        *,
        line: Color | None = None,
        line_width: float = 1.2,
        shade: Color | None = None,
        shade_offset: Point = (0.0, -3.0),
        shade_alpha: float = 1.0,
        shade_feather: float = 0.6,
        rim: Color | None = None,
        rim_offset: Point = (-1.2, 1.2),
        rim_alpha: float = 0.8,
    ) -> None:
        """Outline, fill, soft cel shade (away from the light), and rim light."""
        if line is not None and line_width > 0:
            self.paint(shape.grow(line_width), line)
        self.paint(shape, fill)
        if shade is not None:
            self.paint(
                shape - shape.shift(*shade_offset),
                shade,
                alpha=shade_alpha,
                feather=shade_feather,
                clip=shape,
            )
        if rim is not None:
            self.paint(
                shape - shape.shift(*rim_offset),
                rim,
                alpha=rim_alpha,
                feather=0.35,
                clip=shape,
            )

    # Layers -----------------------------------------------------------------

    def composite(self, layer: Canvas, *, alpha: float = 1.0, mode: str = "over") -> None:
        if (layer.width, layer.height, layer.ss) != (self.width, self.height, self.ss):
            raise ValueError("layers must share size and sampling")
        a = (layer.a * alpha)[..., None]
        if mode == "over":
            self.rgb = self.rgb * (1 - a) + layer.rgb * alpha
            self.a = self.a * (1 - a[..., 0]) + a[..., 0]
        elif mode == "add":
            self.rgb = self.rgb + layer.rgb * alpha
        else:  # pragma: no cover
            raise ValueError(mode)

    def blurred(self, radius: float) -> Canvas:
        """Approximate Gaussian blur (three box passes) of the whole canvas."""
        out = Canvas(self.width, self.height, self.ss)
        r = max(1, round(radius * self.ss / 1.7))
        out.rgb = _box3(self.rgb, r)
        out.a = _box3(self.a[..., None], r)[..., 0]
        return out

    # Output -----------------------------------------------------------------

    def _downsampled(self) -> tuple[np.ndarray, np.ndarray]:
        ss = self.ss
        h, w = self.height, self.width
        color = self.rgb.reshape(h, ss, w, ss, 3).mean(axis=(1, 3))
        alpha = self.a.reshape(h, ss, w, ss).mean(axis=(1, 3))
        return color, alpha

    def image(self, *, opaque: bool = False) -> Image.Image:
        color, alpha = self._downsampled()
        if opaque:
            data = np.clip(color * 255 + 0.5, 0, 255).astype(np.uint8)
            return Image.fromarray(data, "RGB")
        safe = np.where(alpha > 1e-6, alpha, 1.0)[..., None]
        straight = np.where(alpha[..., None] > 1e-6, color / safe, 0)
        data = np.concatenate([np.clip(straight, 0, 1), np.clip(alpha, 0, 1)[..., None]], axis=-1)
        return Image.fromarray(np.clip(data * 255 + 0.5, 0, 255).astype(np.uint8), "RGBA")


def _box1(values: np.ndarray, r: int, axis: int) -> np.ndarray:
    pad = [(0, 0)] * values.ndim
    pad[axis] = (r + 1, r)
    padded = np.pad(values, pad, mode="edge")
    summed = np.cumsum(padded, axis=axis, dtype=np.float64)
    size = values.shape[axis]
    upper = np.take(summed, np.arange(2 * r + 1, 2 * r + 1 + size), axis=axis)
    lower = np.take(summed, np.arange(0, size), axis=axis)
    return ((upper - lower) / (2 * r + 1)).astype(np.float32)


def _box3(values: np.ndarray, r: int) -> np.ndarray:
    for _ in range(3):
        values = _box1(values, r, 0)
        values = _box1(values, r, 1)
    return values


def sheet(frames: Sequence[Sequence[Image.Image]]) -> Image.Image:
    """Assemble rows of equal RGBA frames into one sprite sheet."""
    width, height = frames[0][0].size
    columns = max(len(row) for row in frames)
    out = Image.new("RGBA", (width * columns, height * len(frames)), (0, 0, 0, 0))
    for row_index, row in enumerate(frames):
        for column_index, frame in enumerate(row):
            out.paste(frame, (column_index * width, row_index * height))
    return out
