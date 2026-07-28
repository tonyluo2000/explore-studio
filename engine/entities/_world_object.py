"""Explore Studio engine — world object model.

Defines the WorldObject concept: an engine-internal domain object
representing a stationary item in the world. Objects have identity,
position, size, and color — all immutable.

No generic Entity base class. No interactions. No movement.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _check_positive_dimension(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be int, got {type(value).__name__}")
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def _check_coordinate(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be int, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")
    return value


def _check_name(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError(f"name must be str, got {type(value).__name__}")
    if not value.strip():
        raise ValueError("name must not be empty or whitespace-only")
    return value


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
class WorldObject:
    """A stationary item placed in the world.

    Immutable: identity, position, size, and color cannot change.
    World objects do not move, respond to input, or interact.

    Attributes:
        name: Display name (non-empty, non-whitespace).
        x: Left-edge x-coordinate in pixels (>= 0, int, bool rejected).
        y: Top-edge y-coordinate in pixels (>= 0, int, bool rejected).
        width: Width in pixels (positive int, bool rejected).
        height: Height in pixels (positive int, bool rejected).
        color: ``(r, g, b)`` tuple; each channel 0–255, bool rejected.
    """

    name: str = field(metadata={"validate": _check_name})
    x: int = field(metadata={"validate": _check_coordinate})
    y: int = field(metadata={"validate": _check_coordinate})
    width: int = field(metadata={"validate": _check_positive_dimension})
    height: int = field(metadata={"validate": _check_positive_dimension})
    color: tuple[int, int, int] = field(metadata={"validate": _validate_rgb_color})

    def __post_init__(self) -> None:
        _check_name(self.name)
        _check_coordinate(self.x, "x")
        _check_coordinate(self.y, "y")
        _check_positive_dimension(self.width, "width")
        _check_positive_dimension(self.height, "height")
        _validate_rgb_color(self.color)
