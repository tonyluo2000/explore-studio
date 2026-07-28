"""Explore Studio engine — application entry point.

Owns the application lifecycle: initialization, main loop, and shutdown.
Coordinates configuration, logging, platform, and subsystem startup.

This module contains the App class — the single entry point through which
all engine functionality is accessed.
"""

from __future__ import annotations

import enum
import logging
import sys

from engine._config import Config
from engine._platform import Platform
from engine.rendering import Renderer


class _LifecycleState(enum.Enum):
    """Internal lifecycle states for the application."""

    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"


class LifecycleError(RuntimeError):
    """Raised when an invalid lifecycle transition is attempted."""


class App:
    """Explore Studio application.

    Owns the top-level application lifecycle. Coordinates platform
    initialization, the main loop, and orderly shutdown.

    Lifecycle::

        App()            → CREATED
        app.start()      → RUNNING  (enters main loop)
        app.shutdown()   → STOPPED

    Invalid transitions (raise LifecycleError):
        - start() when RUNNING or STOPPED
        - run() when not CREATED

    Usage::

        app = App()
        try:
            app.start()
        finally:
            app.shutdown()
    """

    def __init__(self, config: Config | None = None) -> None:
        """Initialize the application.

        Args:
            config: Engine configuration. Uses defaults if not provided.
        """
        self._config = config if config is not None else Config()
        self._log: logging.Logger | None = None
        self._platform: Platform | None = None
        self._renderer: Renderer | None = None
        self._state = _LifecycleState.CREATED

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def config(self) -> Config:
        """The application's immutable configuration."""
        return self._config

    @property
    def is_running(self) -> bool:
        """True while the main loop is active."""
        return self._state == _LifecycleState.RUNNING

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the application.

        Initializes logging, the platform (Pygame + window), and enters
        the main loop. Blocks until shutdown is requested.

        Raises:
            LifecycleError: If start has already been called or the app
                has been stopped.
        """
        if self._state != _LifecycleState.CREATED:
            raise LifecycleError(
                f"Cannot start from state {self._state.value}. " "App has already been started."
            )

        # --- logging ---
        from engine._logging import init_logging

        self._log = init_logging()
        self._log.info(
            "%s v%s starting.",
            self._config.app_name,
            self._config.version,
        )

        # --- platform ---
        self._platform = Platform(self._config)

        try:
            self._platform.initialize()
        except Exception:
            self._log.exception("Platform initialization failed.")
            self._cleanup_platform()
            raise

        # --- renderer ---
        self._renderer = Renderer(self._platform)

        # --- main loop ---
        self._state = _LifecycleState.RUNNING
        try:
            self._run_loop()
        except Exception:
            self._log.exception("Unhandled error in main loop.")
            raise
        finally:
            self._state = _LifecycleState.STOPPED
            self._cleanup_platform()

    def shutdown(self) -> None:
        """Shut down the application cleanly.

        Safe to call at any point. Performs platform cleanup if the
        platform was initialized. Idempotent — subsequent calls are
        no-ops.
        """
        if self._state == _LifecycleState.STOPPED:
            return

        if self._log is not None:
            self._log.info("%s shutting down.", self._config.app_name)

        if self._state == _LifecycleState.RUNNING:
            self._state = _LifecycleState.STOPPED

        self._cleanup_platform()

    # ------------------------------------------------------------------
    # Internal: main loop
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        """Execute the application main loop.

        Each iteration:
        1. Polls platform events for quit requests.
        2. Clears the frame to the configured background color.
        3. Presents the completed frame.
        4. Caps frame rate to the configured target FPS.

        Exits when a quit event is received.
        """
        assert self._platform is not None
        assert self._renderer is not None
        self._log.info("Entering main loop (target %d FPS).", self._config.target_fps)

        while not self._platform.has_quit_request():
            self._renderer.render_frame(self._config.background_color)
            self._platform.tick()

        self._log.info("Quit requested. Exiting main loop.")

    # ------------------------------------------------------------------
    # Internal: cleanup
    # ------------------------------------------------------------------

    def _cleanup_platform(self) -> None:
        """Release platform resources if they were acquired."""
        if self._platform is not None:
            self._platform.shutdown()
            self._platform = None

    # ------------------------------------------------------------------
    # Process-boundary helpers
    # ------------------------------------------------------------------

    @staticmethod
    def main() -> None:
        """Thin process-boundary wrapper.

        Constructs default configuration, creates an App, and runs the
        lifecycle. On failure, logs the error and exits with code 1.

        This is the canonical entry point called from ``__main__`` and
        tests.
        """
        config = Config()
        app = App(config=config)
        try:
            app.start()
        except LifecycleError:
            sys.exit(1)
        except Exception:
            sys.exit(1)
