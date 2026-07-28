"""Explore Studio engine — platform boundary.

Wraps Pygame initialization, window creation, event polling, frame-rate
limiting, and shutdown behind a narrow engine-owned interface.

No Pygame types are exposed to the rest of the engine. All platform
interaction goes through this module.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import logging
from typing import Any

import pygame

from engine._config import Config

_LOGGER = logging.getLogger("explore-studio.platform")


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
    # Frame control
    # ------------------------------------------------------------------

    def tick(self) -> float:
        """Advance one frame and return elapsed milliseconds.

        Must only be called after initialize(). Caps the frame rate to
        the configured target FPS.

        Returns:
            The elapsed time in milliseconds since the last tick call.
        """
        if self._clock is None:
            raise RuntimeError("Platform not initialized; call initialize() first.")
        return self._clock.tick(self._config.target_fps)

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
