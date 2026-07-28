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
from engine.scenes import DefaultScene, Scene


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
        self._scene: Scene | None = None
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

        # --- scene ---
        self._scene = self._create_scene()

        try:
            self._scene.enter()
        except Exception:
            self._log.exception("Scene entry failed.")
            self._cleanup_scene()
            self._cleanup_platform()
            raise

        # --- main loop ---
        self._state = _LifecycleState.RUNNING
        loop_error: BaseException | None = None
        try:
            self._run_loop()
        except BaseException as _exc:
            loop_error = _exc
            if isinstance(_exc, Exception):
                self._log.exception("Unhandled error in main loop.")
            raise
        finally:
            self._state = _LifecycleState.STOPPED
            self._cleanup_scene(earlier_error=loop_error)
            self._cleanup_platform()

    def shutdown(self) -> None:
        """Shut down the application cleanly.

        Safe to call at any point. Exits the scene if active, then
        performs platform cleanup. Idempotent — subsequent calls are
        no-ops.
        """
        if self._state == _LifecycleState.STOPPED:
            return

        if self._log is not None:
            self._log.info("%s shutting down.", self._config.app_name)

        if self._state == _LifecycleState.RUNNING:
            self._state = _LifecycleState.STOPPED

        self._cleanup_scene(earlier_error=None)
        self._cleanup_platform()

    # ------------------------------------------------------------------
    # Internal: scene
    # ------------------------------------------------------------------

    def _create_scene(self) -> Scene:
        """Create the scene for this application run.

        Override in subclasses to provide a custom scene. The default
        returns a ``DefaultScene`` with a centered character and the
        configured background colour.

        Returns:
            A new Scene instance (not yet entered).
        """
        assert self._renderer is not None
        return DefaultScene(
            self._renderer,
            background_color=self._config.background_color,
        )

    def _cleanup_scene(self, *, earlier_error: BaseException | None = None) -> None:
        """Exit the active scene if it was entered.

        Args:
            earlier_error: If an operational failure is already in
                flight, it takes precedence. The exit failure is logged
                but not re-raised. If no earlier error exists, the
                exit failure is raised so it remains observable.
        """
        if self._scene is None:
            return

        try:
            self._scene.exit()
        except Exception:
            if earlier_error is not None:
                self._log.exception(
                    "Scene exit failed during error recovery; " "preserving original exception."
                )
            else:
                raise

    # ------------------------------------------------------------------
    # Internal: main loop
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        """Execute the application main loop.

        Each iteration:
        1. Polls platform events for quit requests.
        2. Obtains elapsed time (dt) from the platform clock.
        3. Reads current directional input.
        4. Allows the active scene to update and draw.
           The scene is responsible for clearing the frame at the
           appropriate point so that failures in update logic
           (movement, proximity) prevent the clear.
        5. Presents the completed frame.

        Exits when a quit event is received. A failure in any step
        prevents frame presentation and preserves the original exception.
        """
        assert self._platform is not None
        assert self._renderer is not None
        assert self._scene is not None
        self._log.info("Entering main loop (target %d FPS).", self._config.target_fps)

        while not self._platform.has_quit_request():
            dt = self._platform.tick()
            inp = self._platform.poll_directional_input()

            try:
                self._scene.on_frame(inp, dt)
            except Exception:
                self._log.exception("Scene frame participation failed.")
                raise
            self._renderer.present_frame()

        self._log.info("Quit requested. Exiting main loop.")

    # ------------------------------------------------------------------
    # Internal: cleanup
    # ------------------------------------------------------------------

    def _cleanup_platform(self) -> None:
        """Release platform resources if they were acquired.

        Safe to call at any point. Platform shutdown is idempotent.
        """
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
