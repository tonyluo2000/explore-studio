"""Explore Studio engine — configuration.

Owns all engine configuration values. Provides a single, immutable-after-creation
configuration object consumed by other subsystems. Validates values on creation.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _check_positive(value: int, name: str) -> int:
    """Validate that *value* is a positive integer.

    Args:
        value: The value to validate.
        name: Human-readable field name for the error message.

    Returns:
        The value unchanged if valid.

    Raises:
        ValueError: If *value* is not positive.
    """
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def _check_color_channel(value: Any, position: int, name: str) -> int:
    """Validate a single color channel (0–255 integer, bool rejected).

    Python ``bool`` is a subclass of ``int``, so we reject it explicitly
    to prevent ``True`` / ``False`` from being silently coerced to 1 / 0.

    Args:
        value: The channel value to validate.
        position: 0-based channel index (for error messages).
        name: Human-readable field name.

    Returns:
        The value as an int if valid.

    Raises:
        TypeError: If *value* is not an int, or is a bool.
        ValueError: If *value* is outside 0–255.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name}[{position}] must be int, got {type(value).__name__}")
    if not (0 <= value <= 255):
        raise ValueError(f"{name}[{position}] must be 0–255, got {value}")
    return value


def _validate_background_color(color: object) -> tuple[int, int, int]:
    """Validate a ``(r, g, b)`` background-color tuple.

    Returns a validated ``(r, g, b)`` tuple. Rejects non-tuples,
    wrong-length tuples, non-integer channels, bool channels, and
    out-of-range channels.

    Args:
        color: The candidate background color.

    Returns:
        A validated ``(r, g, b)`` tuple of ints.

    Raises:
        TypeError: If not a tuple, or a channel is not int / is bool.
        ValueError: If wrong length or channel out of range.
    """
    if not isinstance(color, tuple):
        raise TypeError(f"background_color must be a tuple, got {type(color).__name__}")
    if len(color) != 3:
        raise ValueError(f"background_color must have 3 channels, got {len(color)}")
    return tuple(
        _check_color_channel(ch, i, "background_color") for i, ch in enumerate(color)
    )  # type: ignore[return-value]


@dataclass(frozen=True)
class Config:
    """Immutable engine configuration.

    All integer dimensions, rates, and color channels are validated at
    construction time.

    Attributes:
        app_name: Human-readable application name.
        version: Engine version string.
        target_fps: Target frames per second for the main loop.
        window_width: Window width in pixels.
        window_height: Window height in pixels.
        background_color: ``(r, g, b)`` tuple; each channel 0–255.
            Bool values are rejected to avoid silent coercion.
            Default: ``(32, 32, 48)`` — a dark blue-grey.
    """

    app_name: str = "Explore Studio"
    version: str = "0.1.0"
    target_fps: int = field(default=60, metadata={"validate": _check_positive})
    window_width: int = field(default=960, metadata={"validate": _check_positive})
    window_height: int = field(default=640, metadata={"validate": _check_positive})
    background_color: tuple[int, int, int] = field(
        default=(32, 32, 48),
        metadata={"validate": _validate_background_color},
    )

    def __post_init__(self) -> None:
        """Validate all constrained fields after dataclass initialization."""
        _check_positive(self.target_fps, "target_fps")
        _check_positive(self.window_width, "window_width")
        _check_positive(self.window_height, "window_height")
        _validate_background_color(self.background_color)
