"""Explore Studio engine — platform boundary.

Wraps Pygame initialization, window creation, event polling, frame-rate
limiting, and shutdown behind a narrow engine-owned interface.

No Pygame types are exposed to the rest of the engine. All platform
interaction goes through this module.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pygame

from engine._config import Config
from engine.input import DirectionalInput

_LOGGER = logging.getLogger("explore-studio.platform")


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
