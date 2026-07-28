"""Explore Studio engine — frame renderer.

Owns the engine-level frame contract: clear → present. Validates that
frame operations are only performed when the platform is ready.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine._platform import Platform

_LOGGER = logging.getLogger("explore-studio.rendering")


class Renderer:
    """Engine-level frame renderer.

    Owns the frame contract: each iteration produces one frame by
    clearing the display to the configured background color and then
    presenting it. Delegates low-level draw calls to the Platform.

    Created once when the application starts the main loop.
    """

    def __init__(self, platform: Platform) -> None:
        """Create a Renderer bound to *platform*.

        Args:
            platform: The initialized platform that owns the display
                surface and low-level draw operations.
        """
        self._platform = platform
        self._frame_count: int = 0

    # ------------------------------------------------------------------
    # Frame contract
    # ------------------------------------------------------------------

    def clear_frame(self, background_color: tuple[int, int, int]) -> None:
        """Clear the display to *background_color*.

        Does **not** present the frame — call ``present_frame`` after
        the scene has contributed content.

        Args:
            background_color: ``(r, g, b)`` tuple; each channel 0–255.

        Raises:
            RuntimeError: If the platform is not initialized.
        """
        self._platform.clear_frame(background_color)

    def present_frame(self) -> None:
        """Present the completed frame to the display.

        Must be called after ``clear_frame`` and scene participation.

        Raises:
            RuntimeError: If the platform is not initialized.
        """
        self._platform.present_frame()
        self._frame_count += 1

    def render_frame(self, background_color: tuple[int, int, int]) -> None:
        """Produce one complete frame (clear + present).

        Convenience for when no scene participation is needed between
        clear and present.

        Args:
            background_color: ``(r, g, b)`` tuple; each channel 0–255.
        """
        self.clear_frame(background_color)
        self.present_frame()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def frame_count(self) -> int:
        """Number of frames rendered since creation."""
        return self._frame_count
