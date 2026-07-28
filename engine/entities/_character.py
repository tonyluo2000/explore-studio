"""Explore Studio engine — character model.

Defines the Character concept: an engine-internal domain object
representing one inhabitant of a scene. Characters have identity,
position (mutable via move()), size, and color.

No generic Entity base class. No component system.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


def _check_positive_dimension(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be int, got {type(value).__name__}")
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def _check_name(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError(f"name must be str, got {type(value).__name__}")
    if not value.strip():
        raise ValueError("name must not be empty or whitespace-only")
    return value


def _check_float(value: Any, name: str) -> float:
    """Validate a finite float (rejects bool, NaN, inf)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be float or int, got {type(value).__name__}")
    f = float(value)
    if math.isnan(f) or math.isinf(f):
        raise ValueError(f"{name} must be finite, got {f}")
    return f


def _validate_rgb_color(color: object) -> tuple[int, int, int]:
    if not isinstance(color, tuple):
        raise TypeError(f"color must be a tuple, got {type(color).__name__}")
    if len(color) != 3:
        raise ValueError(f"color must have 3 channels, got {len(color)}")
    for i, ch in enumerate(color):
        if not isinstance(ch, int) or isinstance(ch, bool):
            raise TypeError(f"color[{i}] must be int, got {type(ch).__name__}")
        if not (0 <= ch <= 255):
            raise ValueError(f"color[{i}] must be 0–255, got {ch}")
    return (color[0], color[1], color[2])  # type: ignore[return-value]


@dataclass(frozen=True)
class Bounds:
    """Axis-aligned movement bounds."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float


class Character:
    """An inhabitant of a scene.

    Identity, size, and color are immutable. Position is mutable only
    via ``move()``. Internal position is stored as float for smooth
    frame-rate-aware movement; ``x``/``y`` return rounded ints for
    rendering.
    """

    def __init__(
        self,
        *,
        name: str,
        x: float = 0,
        y: float = 0,
        width: int,
        height: int,
        color: tuple[int, int, int],
    ) -> None:
        _check_name(name)
        _check_float(x, "x")
        _check_float(y, "y")
        if x < 0:
            raise ValueError(f"x must be >= 0, got {x}")
        if y < 0:
            raise ValueError(f"y must be >= 0, got {y}")
        _check_positive_dimension(width, "width")
        _check_positive_dimension(height, "height")
        _validate_rgb_color(color)
        self._name = name
        self._x = float(x)
        self._y = float(y)
        self._width = width
        self._height = height
        self._color = color

    @property
    def name(self) -> str:
        return self._name

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def color(self) -> tuple[int, int, int]:
        return self._color

    @property
    def x(self) -> int:
        return round(self._x)

    @property
    def y(self) -> int:
        return round(self._y)

    @property
    def x_float(self) -> float:
        return self._x

    @property
    def y_float(self) -> float:
        return self._y

    def move(self, dx: float, dy: float, bounds: Bounds) -> None:
        """Apply displacement and clamp to bounds."""
        _check_float(dx, "dx")
        _check_float(dy, "dy")
        self._x += dx
        self._y += dy
        if self._x < bounds.min_x:
            self._x = bounds.min_x
        elif self._x > bounds.max_x:
            self._x = bounds.max_x
        if self._y < bounds.min_y:
            self._y = bounds.min_y
        elif self._y > bounds.max_y:
            self._y = bounds.max_y
