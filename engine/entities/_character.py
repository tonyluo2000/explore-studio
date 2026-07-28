"""Explore Studio engine — character model.

Defines the Character concept: an engine-internal domain object
representing one inhabitant of a scene. Characters have identity,
position, size, and color.

No generic Entity base class. No component system. No movement.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _check_positive_dimension(value: Any, name: str) -> int:
    """Validate a positive integer dimension (rejects bool)."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be int, got {type(value).__name__}")
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def _check_coordinate(value: Any, name: str) -> int:
    """Validate an integer coordinate (rejects bool; allows zero or positive)."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be int, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")
    return value


def _check_name(value: Any) -> str:
    """Validate a non-empty, non-whitespace character name."""
    if not isinstance(value, str):
        raise TypeError(f"name must be str, got {type(value).__name__}")
    if not value.strip():
        raise ValueError("name must not be empty or whitespace-only")
    return value


def _validate_rgb_color(color: object) -> tuple[int, int, int]:
    """Validate an (r, g, b) tuple with channels 0–255 (rejects bool)."""
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
class Character:
    """An inhabitant of a scene.

    Immutable: once created, a character's identity, position, size,
    and color cannot change. Movement and state mutation belong to
    future milestones.

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
        """Validate all fields after dataclass initialization."""
        _check_name(self.name)
        _check_coordinate(self.x, "x")
        _check_coordinate(self.y, "y")
        _check_positive_dimension(self.width, "width")
        _check_positive_dimension(self.height, "height")
        _validate_rgb_color(self.color)
