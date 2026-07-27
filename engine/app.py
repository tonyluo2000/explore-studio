"""Explore Studio engine — application entry point.

Owns the application lifecycle: initialization, main loop placeholder,
and shutdown. Coordinates configuration, logging, and subsystem startup.

This module contains the App class — the single entry point through which
all engine functionality is accessed.
"""

from __future__ import annotations

import logging

from engine._config import Config


class App:
    """Explore Studio application.

    Owns the top-level application lifecycle. Created once at startup
    and coordinates engine initialization and shutdown.

    At this stage the application initializes configuration and logging,
    then exits cleanly. Window creation, rendering, and gameplay belong
    to later milestones.
    """

    def __init__(self, config: Config | None = None) -> None:
        """Initialize the application.

        Args:
            config: Engine configuration. Uses defaults if not provided.
        """
        self._config = config if config is not None else Config()
        self._log: logging.Logger | None = None

    @property
    def config(self) -> Config:
        """The application's immutable configuration."""
        return self._config

    def start(self) -> None:
        """Start the application.

        Initializes logging and validates the startup sequence. At this
        stage, does not open a window or enter a main loop.

        Raises:
            RuntimeError: If start is called more than once.
        """
        if self._log is not None:
            raise RuntimeError("App.start() has already been called.")

        from engine._logging import init_logging

        self._log = init_logging()
        self._log.info(
            "%s v%s starting.",
            self._config.app_name,
            self._config.version,
        )
        # Future: window creation, asset loading, scene initialization.

    def shutdown(self) -> None:
        """Shut down the application cleanly.

        Performs orderly teardown. At this stage, simply logs the event.
        """
        if self._log is not None:
            self._log.info(
                "%s shutting down.",
                self._config.app_name,
            )
        # Future: save state, release resources, close window.
