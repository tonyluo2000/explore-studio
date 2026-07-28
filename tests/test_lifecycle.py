"""Verify application lifecycle behavior.

All tests in this module use a headless Pygame driver (SDL_VIDEODRIVER=dummy)
set by conftest.py, so no physical display is required.
"""

from __future__ import annotations

import threading
import time

import pytest

from engine import App, LifecycleError
from engine._logging import init_logging


def _post_quit_after(delay: float = 0.1) -> threading.Thread:
    import pygame

    def _post() -> None:
        time.sleep(delay)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    t = threading.Thread(target=_post, daemon=True)
    t.start()
    return t


@pytest.fixture(autouse=True)
def _ensure_logging() -> None:
    init_logging()


def test_start_and_immediate_quit() -> None:
    app = App()
    _post_quit_after(0.1)
    app.start()
    assert app.is_running is False


def test_window_title_from_config() -> None:
    import pygame

    from engine import Config

    captured: list[str] = []

    def act() -> None:
        time.sleep(0.1)
        captured.append(pygame.display.get_caption()[0])
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=act, daemon=True).start()

    app = App(config=Config(app_name="TitleTest"))
    app.start()

    assert captured == ["TitleTest"]


def test_start_after_shutdown_raises() -> None:
    app = App()
    _post_quit_after(0.1)
    app.start()

    with pytest.raises(LifecycleError, match="already been started"):
        app.start()


def test_shutdown_is_idempotent() -> None:
    app = App()
    _post_quit_after(0.1)
    app.start()

    app.shutdown()
    app.shutdown()


def test_app_main_runs_and_exits() -> None:
    _post_quit_after(0.1)
    App.main()


def test_main_loop_respects_fps() -> None:
    from engine import Config

    app = App(config=Config(target_fps=30))
    _post_quit_after(0.15)
    app.start()

    assert app.is_running is False
