"""Explore Studio engine — configuration.

Owns all engine configuration values. Provides a single, immutable-after-creation
configuration object consumed by other subsystems. Validates values on creation.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from dataclasses import dataclass, field


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


@dataclass(frozen=True)
class Config:
    """Immutable engine configuration.

    All integer dimensions and rates are validated at construction time.

    Attributes:
        app_name: Human-readable application name.
        version: Engine version string.
        target_fps: Target frames per second for the main loop.
        window_width: Window width in pixels.
        window_height: Window height in pixels.
    """

    app_name: str = "Explore Studio"
    version: str = "0.1.0"
    target_fps: int = field(default=60, metadata={"validate": _check_positive})
    window_width: int = field(default=960, metadata={"validate": _check_positive})
    window_height: int = field(default=640, metadata={"validate": _check_positive})

    def __post_init__(self) -> None:
        """Validate all constrained fields after dataclass initialization."""
        _check_positive(self.target_fps, "target_fps")
        _check_positive(self.window_width, "window_width")
        _check_positive(self.window_height, "window_height")
