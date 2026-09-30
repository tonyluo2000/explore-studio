"""Explore Studio engine — frame renderer.

Owns the engine-level frame contract: clear → present. Validates that
frame operations are only performed when the platform is ready.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from engine.assets import ImageHandle, SpriteSheetLibrary

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
        self._sprite_sheets: SpriteSheetLibrary | None = None

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

    def draw_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a filled rectangle at *(x, y)*.

        Must be called between ``clear_frame`` and ``present_frame``.

        Args:
            x: Left-edge x-coordinate.
            y: Top-edge y-coordinate.
            width: Width in pixels.
            height: Height in pixels.
            color: ``(r, g, b)`` fill color.
        """
        self._platform.draw_rect(x, y, width, height, color)

    def draw_circle(
        self,
        center_x: int,
        center_y: int,
        radius: int,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a filled circle through the platform boundary."""
        self._platform.draw_circle(center_x, center_y, radius, color)

    def draw_line(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        color: tuple[int, int, int],
        width: int = 1,
    ) -> None:
        """Draw a line through the platform boundary."""
        self._platform.draw_line(start_x, start_y, end_x, end_y, color, width)

    def draw_polygon(
        self,
        points: tuple[tuple[int, int], ...],
        color: tuple[int, int, int],
    ) -> None:
        """Draw a filled polygon through the platform boundary."""
        self._platform.draw_polygon(points, color)

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
        font_size: int,
    ) -> None:
        """Draw one line of text at *(x, y)*.

        Delegates to the platform.  Must be called between
        ``clear_frame`` and ``present_frame``.

        Args:
            text: Non-empty, non-whitespace string.
            x: Left-edge x-coordinate (int, >= 0).
            y: Top-edge y-coordinate (int, >= 0).
            color: ``(r, g, b)``; each channel 0–255.
            font_size: Positive integer point size.
        """
        self._platform.draw_text(text, x, y, color, font_size)

    def measure_text(self, text: str, font_size: int) -> tuple[int, int]:
        """Return the pixel size of one line of text."""
        return self._platform.measure_text(text, font_size)

    # ------------------------------------------------------------------
    # Images and effects
    # ------------------------------------------------------------------

    @property
    def sprite_sheets(self) -> SpriteSheetLibrary:
        """Decode-once cache of course-owned trusted sprite sheets."""
        if self._sprite_sheets is None:
            self._sprite_sheets = SpriteSheetLibrary(self._platform)
        return self._sprite_sheets

    def draw_image(self, image: ImageHandle, x: int, y: int) -> None:
        """Draw an engine image with its transparency."""
        self._platform.draw_image(image, x, y)

    def draw_sprite_frame(
        self,
        asset_id: str,
        row: str,
        column: str,
        x: int,
        y: int,
        width: int,
        height: int,
        *,
        flip_x: bool = False,
        accent: tuple[int, int, int] | None = None,
        tint: tuple[int, int, int] | None = None,
    ) -> bool:
        """Draw one trusted sprite frame filling *width* x *height* at *(x, y)*.

        Returns ``False`` without drawing when the sheet is missing, fails its
        digest, cannot be decoded, has no such frame, or was authored for a
        different *accent* color, so callers keep their procedural fallback.
        A *tint* multiplies neutral art by a color (see ``SpriteSheetLibrary``).
        """
        library = self.sprite_sheets
        if accent is not None and library.accent(asset_id) != accent:
            return False
        image = library.frame(asset_id, row, column, width, height, flip_x=flip_x, tint=tint)
        if image is None:
            return False
        self._platform.draw_image(image, x, y)
        return True

    def draw_glow(
        self,
        center_x: int,
        center_y: int,
        radius: int,
        color: tuple[int, int, int],
        intensity: float,
    ) -> None:
        """Add a soft additive light."""
        self._platform.draw_glow(center_x, center_y, radius, color, intensity)

    def draw_soft_ellipse(
        self,
        center_x: int,
        center_y: int,
        radius_x: int,
        radius_y: int,
        color: tuple[int, int, int],
        alpha: int,
    ) -> None:
        """Blend a feathered translucent ellipse such as a grounded shadow."""
        self._platform.draw_soft_ellipse(center_x, center_y, radius_x, radius_y, color, alpha)

    def draw_translucent_panel(
        self,
        rects: tuple[tuple[int, int, int, int], ...],
        color: tuple[int, int, int],
        alpha: int,
        radius: int,
        border_color: tuple[int, int, int] | None = None,
        border_alpha: int = 0,
        soften: bool = False,
    ) -> None:
        """Blend one translucent panel shaped as the union of rounded *rects*."""
        self._platform.draw_translucent_panel(
            rects, color, alpha, radius, border_color, border_alpha, soften
        )

    def draw_rounded_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: tuple[int, int, int],
        radius: int,
        border_color: tuple[int, int, int] | None = None,
        border_width: int = 0,
    ) -> None:
        """Draw a rounded panel with an optional border."""
        self._platform.draw_rounded_rect(
            x, y, width, height, color, radius, border_color, border_width
        )

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
