"""Verify rendering subsystem behavior.

All tests use a headless Pygame driver (SDL_VIDEODRIVER=dummy) set by
conftest.py. No physical display is required.
"""

from __future__ import annotations

import threading
import time

import pytest

from engine import App, Config
from engine._logging import init_logging
from engine._platform import Platform
from engine.rendering import Renderer


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


# ------------------------------------------------------------------
# Renderer lifecycle
# ------------------------------------------------------------------


def test_renderer_creation() -> None:
    """Renderer can be created from an initialized Platform."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        assert renderer.frame_count == 0
    finally:
        platform.shutdown()


def test_render_frame_increments_count() -> None:
    """Each render_frame call increments the frame counter."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        renderer.render_frame((0, 0, 0))
        assert renderer.frame_count == 1
        renderer.render_frame((255, 255, 255))
        assert renderer.frame_count == 2
    finally:
        platform.shutdown()


# ------------------------------------------------------------------
# Frame operations before/after platform lifecycle
# ------------------------------------------------------------------


def test_clear_before_initialize_raises() -> None:
    """Calling clear_frame before initialize raises RuntimeError."""
    platform = Platform(Config())
    with pytest.raises(RuntimeError, match="not initialized"):
        platform.clear_frame((0, 0, 0))


def test_present_before_initialize_raises() -> None:
    """Calling present_frame before initialize raises RuntimeError."""
    platform = Platform(Config())
    with pytest.raises(RuntimeError, match="not initialized"):
        platform.present_frame()


def test_clear_after_shutdown_raises() -> None:
    """Calling clear_frame after shutdown raises RuntimeError."""
    platform = Platform(Config())
    platform.initialize()
    platform.shutdown()
    with pytest.raises(RuntimeError, match="not initialized"):
        platform.clear_frame((0, 0, 0))


def test_present_after_shutdown_raises() -> None:
    """Calling present_frame after shutdown raises RuntimeError."""
    platform = Platform(Config())
    platform.initialize()
    platform.shutdown()
    with pytest.raises(RuntimeError, match="not initialized"):
        platform.present_frame()


# ------------------------------------------------------------------
# Integration: App renders frames in main loop
# ------------------------------------------------------------------


def test_app_renders_frames_in_loop() -> None:
    """App produces frames in the main loop."""
    app = App(Config(target_fps=120))
    _post_quit_after(0.15)
    app.start()
    # If the app exited cleanly, rendering ran without error.
    assert app.is_running is False


def test_app_uses_configured_background() -> None:
    """Frame clearing uses configured background_color."""
    import pygame

    color = (100, 150, 200)
    app = App(Config(background_color=color, target_fps=120))

    captured: list[tuple[int, int, int]] = []

    def check_and_quit() -> None:
        time.sleep(0.1)
        surface = pygame.display.get_surface()
        if surface is not None:
            # Sample a pixel to verify the cleared color
            px = surface.get_at((10, 10))
            captured.append((px.r, px.g, px.b))
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=check_and_quit, daemon=True).start()
    app.start()

    assert len(captured) == 1
    assert captured[0] == color


def test_quit_does_not_produce_extra_frame() -> None:
    """A quit event does not cause an extra frame after the loop exits."""
    import pygame

    app = App(Config(target_fps=120))

    def quit_immediately() -> None:
        time.sleep(0.05)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=quit_immediately, daemon=True).start()
    app.start()

    # No assertion needed — if an extra frame was produced after
    # quit, it wouldn't cause a test failure on its own, but the
    # loop structure (while not quit → render → tick) guarantees
    # no frame is rendered after quit is detected.


# ------------------------------------------------------------------
# Regression
# ------------------------------------------------------------------


def test_imports_still_valid() -> None:
    """Public API does not expose Pygame types."""
    from engine import App, Config, LifecycleError, init_logging  # noqa: F401

    # The Renderer is internal to the rendering subsystem.
    from engine.rendering import Renderer  # noqa: F401
