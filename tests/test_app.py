"""Verify application bootstrap behavior.

All tests use a headless Pygame driver (SDL_VIDEODRIVER=dummy) set by
conftest.py. No physical display is required.
"""

from __future__ import annotations

import threading
import time

import pytest

from engine import App, Config, LifecycleError
from engine._logging import init_logging


def _post_quit_after(delay: float = 0.1) -> threading.Thread:
    """Return a daemon thread that posts a Pygame QUIT event after *delay*."""
    import pygame

    def _post() -> None:
        time.sleep(delay)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    t = threading.Thread(target=_post, daemon=True)
    t.start()
    return t


@pytest.fixture(autouse=True)
def _ensure_logging() -> None:
    """Ensure logging is initialized before each test."""
    init_logging()


def test_app_creation() -> None:
    """App can be created with default config."""
    app = App()
    assert app.config.app_name == "Explore Studio"


def test_app_creation_custom_config() -> None:
    """App accepts a custom Config."""
    config = Config(app_name="Custom")
    app = App(config=config)
    assert app.config.app_name == "Custom"


def test_app_start_shutdown_sequence() -> None:
    """App can start and shut down without error."""
    app = App()
    _post_quit_after(0.1)
    app.start()


def test_app_double_start_raises() -> None:
    """Starting the app twice raises LifecycleError."""
    app = App()
    _post_quit_after(0.1)
    app.start()

    with pytest.raises(LifecycleError, match="already been started"):
        app.start()
