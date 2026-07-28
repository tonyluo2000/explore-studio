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

    def render_frame(self, background_color: tuple[int, int, int]) -> None:
        """Produce one complete frame.

        1. Clear the display to *background_color*.
        2. Present the frame.

        Args:
            background_color: ``(r, g, b)`` tuple; each channel 0–255.

        Raises:
            RuntimeError: If the platform is not initialized.
        """
        self._platform.clear_frame(background_color)
        self._platform.present_frame()
        self._frame_count += 1

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @property
    def frame_count(self) -> int:
        """Number of frames rendered since creation."""
        return self._frame_count
