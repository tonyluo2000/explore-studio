"""Explore Studio engine — configuration.

Owns all engine configuration values. Provides a single, immutable-after-creation
configuration object consumed by other subsystems.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Immutable engine configuration.

    Attributes:
        app_name: Human-readable application name.
        version: Engine version string.
        target_fps: Target frames per second (placeholder for future use).
        window_width: Default window width in pixels (placeholder).
        window_height: Default window height in pixels (placeholder).
    """

    app_name: str = "Explore Studio"
    version: str = "0.1.0"
    target_fps: int = 60
    window_width: int = 960
    window_height: int = 640
