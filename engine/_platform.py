"""Explore Studio engine — platform boundary.

Wraps Pygame initialization, window creation, event polling, frame-rate
limiting, and shutdown behind a narrow engine-owned interface.

No Pygame types are exposed to the rest of the engine. All platform
interaction goes through this module.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any, Final

import pygame

from engine._config import Config
from engine.assets import ImageHandle
from engine.input import DirectionalInput

_LOGGER = logging.getLogger("explore-studio.platform")

#: Bounds on cached effect textures and fonts; each cache is cleared when full.
_MAX_EFFECT_TEXTURES: Final = 192
_GLOW_LEVELS: Final = 16


@dataclass(frozen=True)
class FrameEvents:
    """Engine-owned result of one event-queue poll.

    Contains no Pygame types.  Created by ``Platform.poll_frame_events()``
    once per application iteration.

    Attributes:
        quit_requested: ``True`` if a quit event was received.
        interaction_pressed: ``True`` if the E key was newly pressed
            (``KEYDOWN``).  Held-key repeats do not set this.
    """

    quit_requested: bool = False
    interaction_pressed: bool = False


class Platform:
    """Thin wrapper around Pygame lifecycle and window management.

    Created once at application startup. Owns pygame.init/pygame.quit,
    window creation, event polling, and frame-rate control.
    """

    def __init__(self, config: Config) -> None:
        """Initialize the platform layer.

        Calls pygame.init() and creates the application window.
        Does **not** enter a main loop.

        Args:
            config: Engine configuration providing title and dimensions.
        """
        self._config = config
        self._window: pygame.Surface | None = None
        self._clock: pygame.time.Clock | None = None
        self._initialized = False
        self._fonts: dict[int, pygame.font.Font] = {}
        self._glows: dict[tuple[int, tuple[int, int, int], int], pygame.Surface] = {}
        self._shadows: dict[tuple[int, int, tuple[int, int, int], int], pygame.Surface] = {}

    def initialize(self) -> None:
        """Initialize Pygame and create the application window.

        Must be called once before run_loop. Idempotent for safety
        (multiple calls after the first are no-ops).

        Raises:
            RuntimeError: If Pygame initialization fails.
        """
        if self._initialized:
            return

        try:
            pygame.init()
        except pygame.error as exc:
            raise RuntimeError(f"Failed to initialize platform: {exc}") from exc

        _LOGGER.debug("Pygame %s initialized.", pygame.version.ver)

        self._window = pygame.display.set_mode(
            (self._config.window_width, self._config.window_height),
        )
        pygame.display.set_caption(self._config.app_name)

        self._clock = pygame.time.Clock()
        self._initialized = True

        _LOGGER.info(
            "Window created: %dx%d, target %d FPS.",
            self._config.window_width,
            self._config.window_height,
            self._config.target_fps,
        )

    # ------------------------------------------------------------------
    # Lifecycle queries
    # ------------------------------------------------------------------

    @property
    def is_initialized(self) -> bool:
        """True after initialize() has completed successfully."""
        return self._initialized

    # ------------------------------------------------------------------
    # Event polling
    # ------------------------------------------------------------------

    def poll_frame_events(self) -> FrameEvents:
        """Poll the Pygame event queue once and return engine-owned events.

        Processes every pending event in a single pass.  Maps:

        * ``pygame.QUIT`` → ``FrameEvents.quit_requested = True``
        * ``pygame.KEYDOWN`` (E key) → ``FrameEvents.interaction_pressed = True``

        Other events are consumed but ignored.  Raw Pygame types never
        leave this method.

        Returns:
            ``FrameEvents`` with the results of this poll.
        """
        quit_requested = False
        interaction_pressed = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_requested = True
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                interaction_pressed = True
        return FrameEvents(
            quit_requested=quit_requested,
            interaction_pressed=interaction_pressed,
        )

    def poll_events(self) -> list[dict[str, Any]]:
        """Collect pending platform events.

        Returns a list of plain dicts — never raw Pygame event objects.
        Currently only reports quit requests.

        Returns:
            A list of event dicts.  Currently supported keys:
            ``{"type": "quit"}``.
        """
        events: list[dict[str, Any]] = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                events.append({"type": "quit"})
        return events

    def has_quit_request(self) -> bool:
        """Return True if any pending event is a quit request.

        This is a convenience for loop-termination checks. It polls
        events and discards non-quit events.
        """
        return any(event.type == pygame.QUIT for event in pygame.event.get())

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def poll_directional_input(self) -> DirectionalInput:
        """Return current directional key state as a DirectionalInput.

        Maps arrow keys and WASD to direction booleans. Returns the
        engine-owned value object directly — no dict or Pygame types.

        Returns:
            ``DirectionalInput`` with pressed directions.
        """
        keys = pygame.key.get_pressed()
        return DirectionalInput(
            left=keys[pygame.K_LEFT] or keys[pygame.K_a],
            right=keys[pygame.K_RIGHT] or keys[pygame.K_d],
            up=keys[pygame.K_UP] or keys[pygame.K_w],
            down=keys[pygame.K_DOWN] or keys[pygame.K_s],
        )

    # ------------------------------------------------------------------
    # Frame control
    # ------------------------------------------------------------------

    def clear_frame(self, color: tuple[int, int, int]) -> None:
        """Fill the entire window surface with *color*.

        Must only be called after initialize() and before shutdown().

        Args:
            color: ``(r, g, b)`` tuple; each channel 0–255.

        Raises:
            RuntimeError: If the platform is not initialized.
        """
        if self._window is None:
            raise RuntimeError("Cannot clear frame: platform not initialized.")
        self._window.fill(color)

    def draw_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a filled rectangle at *(x, y)* with the given dimensions.

        Args:
            x: Left-edge x-coordinate in pixels.
            y: Top-edge y-coordinate in pixels.
            width: Rectangle width in pixels.
            height: Rectangle height in pixels.
            color: ``(r, g, b)`` fill color.

        Raises:
            RuntimeError: If the platform is not initialized.
        """
        if self._window is None:
            raise RuntimeError("Cannot draw: platform not initialized.")
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self._window, color, rect)

    def draw_circle(
        self,
        center_x: int,
        center_y: int,
        radius: int,
        color: tuple[int, int, int],
    ) -> None:
        """Draw a filled circle without exposing a Pygame surface or point type."""
        if self._window is None:
            raise RuntimeError("Cannot draw: platform not initialized.")
        pygame.draw.circle(self._window, color, (center_x, center_y), radius)

    def draw_line(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        color: tuple[int, int, int],
        width: int = 1,
    ) -> None:
        """Draw a line using only engine-owned scalar values."""
        if self._window is None:
            raise RuntimeError("Cannot draw: platform not initialized.")
        pygame.draw.line(
            self._window,
            color,
            (start_x, start_y),
            (end_x, end_y),
            width,
        )

    def draw_polygon(
        self,
        points: tuple[tuple[int, int], ...],
        color: tuple[int, int, int],
    ) -> None:
        """Draw a filled polygon from immutable engine-owned points."""
        if self._window is None:
            raise RuntimeError("Cannot draw: platform not initialized.")
        pygame.draw.polygon(self._window, color, points)

    def draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
        font_size: int,
    ) -> None:
        """Draw one line of text at *(x, y)* using the default Pygame font.

        All inputs are validated with the same engine-owned rules used
        elsewhere (colour channels, positive dimensions, etc.).  No
        Pygame types are returned.

        Args:
            text: Non-empty, non-whitespace string.
            x: Left-edge x-coordinate (int, >= 0).
            y: Top-edge y-coordinate (int, >= 0).
            color: ``(r, g, b)``; each channel 0–255.
            font_size: Positive integer point size.

        Raises:
            TypeError / ValueError: On invalid input.
            RuntimeError: If the platform is not initialized.
        """
        # --- validate text ---
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        if not text.strip():
            raise ValueError("text must not be empty or whitespace-only")

        # --- validate position ---
        if isinstance(x, bool) or not isinstance(x, int):
            raise TypeError(f"x must be int, got {type(x).__name__}")
        if isinstance(y, bool) or not isinstance(y, int):
            raise TypeError(f"y must be int, got {type(y).__name__}")
        if x < 0:
            raise ValueError(f"x must be >= 0, got {x}")
        if y < 0:
            raise ValueError(f"y must be >= 0, got {y}")

        # --- validate font size ---
        if isinstance(font_size, bool) or not isinstance(font_size, int):
            raise TypeError(f"font_size must be int, got {type(font_size).__name__}")
        if font_size <= 0:
            raise ValueError(f"font_size must be positive, got {font_size}")

        # --- validate colour ---
        from engine._color import _validate_rgb_color

        _validate_rgb_color(color)

        # --- render ---
        if self._window is None:
            raise RuntimeError("Cannot draw text: platform not initialized.")
        surface = self._font(font_size).render(text, True, color)
        self._window.blit(surface, (x, y))

    def _font(self, font_size: int) -> pygame.font.Font:
        font = self._fonts.get(font_size)
        if font is None:
            if len(self._fonts) >= 16:
                self._fonts.clear()
            font = pygame.font.Font(None, font_size)
            self._fonts[font_size] = font
        return font

    def measure_text(self, text: str, font_size: int) -> tuple[int, int]:
        """Return the pixel size ``draw_text`` would use for *text*."""
        if isinstance(font_size, bool) or not isinstance(font_size, int) or font_size <= 0:
            raise ValueError(f"font_size must be positive, got {font_size}")
        if not pygame.font.get_init():
            raise RuntimeError("Cannot measure text: platform not initialized.")
        return self._font(font_size).size(text)

    # ------------------------------------------------------------------
    # Images and effects (engine-owned handles; no Pygame types escape)
    # ------------------------------------------------------------------

    def decode_image(self, data: bytes) -> ImageHandle:
        """Decode verified PNG bytes into an opaque engine image handle."""
        try:
            surface = pygame.image.load(io.BytesIO(data), "sheet.png")
        except pygame.error as exc:
            raise ValueError(f"image could not be decoded: {exc}") from exc
        if pygame.display.get_init() and pygame.display.get_surface() is not None:
            surface = surface.convert_alpha()
        return ImageHandle(surface.get_width(), surface.get_height(), surface)

    def crop_image(
        self,
        image: ImageHandle,
        x: int,
        y: int,
        width: int,
        height: int,
        out_width: int,
        out_height: int,
        flip_x: bool,
    ) -> ImageHandle:
        """Cut one frame from *image*, optionally scaled and mirrored."""
        source = image.native
        if not isinstance(source, pygame.Surface):
            raise TypeError("image is not a platform image")
        frame = source.subsurface(pygame.Rect(x, y, width, height)).copy()
        if (out_width, out_height) != (width, height):
            frame = pygame.transform.smoothscale(frame, (out_width, out_height))
        if flip_x:
            frame = pygame.transform.flip(frame, True, False)
        return ImageHandle(frame.get_width(), frame.get_height(), frame)

    def draw_image(self, image: ImageHandle, x: int, y: int) -> None:
        """Blit an engine image with its per-pixel transparency."""
        if self._window is None:
            raise RuntimeError("Cannot draw: platform not initialized.")
        if not isinstance(image.native, pygame.Surface):
            raise TypeError("image is not a platform image")
        self._window.blit(image.native, (x, y))

    def draw_glow(
        self,
        center_x: int,
        center_y: int,
        radius: int,
        color: tuple[int, int, int],
        intensity: float,
    ) -> None:
        """Add a soft radial light (additive blend) from a cached texture."""
        if self._window is None:
            raise RuntimeError("Cannot draw: platform not initialized.")
        level = max(0, min(_GLOW_LEVELS, round(intensity * _GLOW_LEVELS)))
        if radius <= 0 or level == 0:
            return
        key = (radius, color, level)
        texture = self._glows.get(key)
        if texture is None:
            if len(self._glows) >= _MAX_EFFECT_TEXTURES:
                self._glows.clear()
            texture = pygame.Surface((radius * 2, radius * 2))
            texture.fill((0, 0, 0))
            strength = level / _GLOW_LEVELS
            step = max(1, radius // 24)
            for ring in range(radius, 0, -step):
                falloff = (1 - ring / radius) ** 2 * strength
                pygame.draw.circle(
                    texture,
                    tuple(round(channel * falloff) for channel in color),
                    (radius, radius),
                    ring,
                )
            self._glows[key] = texture
        self._window.blit(
            texture, (center_x - radius, center_y - radius), special_flags=pygame.BLEND_RGB_ADD
        )

    def draw_soft_ellipse(
        self,
        center_x: int,
        center_y: int,
        radius_x: int,
        radius_y: int,
        color: tuple[int, int, int],
        alpha: int,
    ) -> None:
        """Blend a feathered translucent ellipse, e.g. a grounded shadow."""
        if self._window is None:
            raise RuntimeError("Cannot draw: platform not initialized.")
        if radius_x <= 0 or radius_y <= 0 or alpha <= 0:
            return
        alpha = min(255, alpha) // 8 * 8
        key = (radius_x, radius_y, color, alpha)
        texture = self._shadows.get(key)
        if texture is None:
            if len(self._shadows) >= _MAX_EFFECT_TEXTURES:
                self._shadows.clear()
            texture = pygame.Surface((radius_x * 2, radius_y * 2), pygame.SRCALPHA)
            texture.fill((0, 0, 0, 0))
            for step in range(6):
                fraction = 1 - step / 6
                rect = pygame.Rect(
                    0, 0, round(radius_x * 2 * fraction), round(radius_y * 2 * fraction)
                )
                rect.center = (radius_x, radius_y)
                pygame.draw.ellipse(texture, (*color, alpha * (step + 1) // 6), rect)
            self._shadows[key] = texture
        self._window.blit(texture, (center_x - radius_x, center_y - radius_y))

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
        """Draw a filled rounded panel with an optional border."""
        if self._window is None:
            raise RuntimeError("Cannot draw: platform not initialized.")
        rect = pygame.Rect(x, y, width, height)
        if border_color is not None and border_width > 0:
            pygame.draw.rect(self._window, border_color, rect, border_radius=radius)
            rect = rect.inflate(-2 * border_width, -2 * border_width)
            radius = max(0, radius - border_width)
        pygame.draw.rect(self._window, color, rect, border_radius=radius)

    def present_frame(self) -> None:
        """Swap buffers / present the completed frame to the display.

        Must only be called after initialize() and before shutdown().

        Raises:
            RuntimeError: If the platform is not initialized.
        """
        if self._window is None:
            raise RuntimeError("Cannot present frame: platform not initialized.")
        pygame.display.flip()

    def tick(self) -> float:
        """Advance one frame and return elapsed time in seconds.

        Must only be called after initialize(). Caps the frame rate to
        the configured target FPS.

        Returns:
            Elapsed time in seconds (float) since the last tick call.
        """
        if self._clock is None:
            raise RuntimeError("Platform not initialized; call initialize() first.")
        return self._clock.tick(self._config.target_fps) / 1000.0

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    def shutdown(self) -> None:
        """Clean up platform resources.

        Closes the window and calls pygame.quit(). Safe to call
        multiple times — subsequent calls after the first are no-ops.
        """
        if not self._initialized:
            return

        _LOGGER.debug("Shutting down platform.")

        if self._window is not None:
            self._window = None

        if self._clock is not None:
            self._clock = None

        self._fonts.clear()
        self._glows.clear()
        self._shadows.clear()
        pygame.quit()
        self._initialized = False

        _LOGGER.info("Platform shut down.")

    # ------------------------------------------------------------------
    # Window properties (read-only helpers for tests)
    # ------------------------------------------------------------------

    @property
    def window_size(self) -> tuple[int, int] | None:
        """Current window dimensions, or None if not initialized."""
        if self._window is None:
            return None
        return self._window.get_size()

    @property
    def window_title(self) -> str | None:
        """Current window title, or None if not initialized."""
        if self._window is None:
            return None
        return pygame.display.get_caption()[0]
