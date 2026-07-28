"""Verify Character model behavior.

All rendering tests use SDL_VIDEODRIVER=dummy (conftest.py).
"""

from __future__ import annotations

import threading
import time

import pytest

from engine import App, Config
from engine._logging import init_logging
from engine._platform import Platform
from engine.entities import Character
from engine.rendering import Renderer
from engine.scenes import DefaultScene


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


# ==================================================================
# Construction — valid
# ==================================================================


def test_valid_character() -> None:
    """A Character with valid fields is created successfully."""
    ch = Character(name="Test", x=10, y=20, width=30, height=40, color=(100, 150, 200))
    assert ch.name == "Test"
    assert ch.x == 10
    assert ch.y == 20
    assert ch.width == 30
    assert ch.height == 40
    assert ch.color == (100, 150, 200)


def test_character_name_preserved() -> None:
    """Name is preserved exactly as provided."""
    ch = Character(name="Explorer", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    assert ch.name == "Explorer"


# ==================================================================
# Name validation
# ==================================================================


def test_empty_name_rejected() -> None:
    with pytest.raises(ValueError, match="name"):
        Character(name="", x=0, y=0, width=10, height=10, color=(0, 0, 0))


def test_whitespace_name_rejected() -> None:
    with pytest.raises(ValueError, match="name"):
        Character(name="   ", x=0, y=0, width=10, height=10, color=(0, 0, 0))


def test_non_string_name_rejected() -> None:
    with pytest.raises(TypeError, match="str"):
        Character(name=123, x=0, y=0, width=10, height=10, color=(0, 0, 0))  # type: ignore[arg-type]


# ==================================================================
# Position validation
# ==================================================================


def test_negative_x_rejected() -> None:
    with pytest.raises(ValueError, match="x"):
        Character(name="A", x=-1, y=0, width=10, height=10, color=(0, 0, 0))


def test_bool_x_rejected() -> None:
    with pytest.raises(TypeError, match="x"):
        Character(name="A", x=True, y=0, width=10, height=10, color=(0, 0, 0))  # type: ignore[arg-type]


def test_non_int_x_rejected() -> None:
    with pytest.raises(TypeError, match="x"):
        Character(name="A", x=1.5, y=0, width=10, height=10, color=(0, 0, 0))  # type: ignore[arg-type]


def test_bool_y_rejected() -> None:
    with pytest.raises(TypeError, match="y"):
        Character(name="A", x=0, y=False, width=10, height=10, color=(0, 0, 0))  # type: ignore[arg-type]


# ==================================================================
# Dimension validation
# ==================================================================


def test_zero_width_rejected() -> None:
    with pytest.raises(ValueError, match="width"):
        Character(name="A", x=0, y=0, width=0, height=10, color=(0, 0, 0))


def test_negative_height_rejected() -> None:
    with pytest.raises(ValueError, match="height"):
        Character(name="A", x=0, y=0, width=10, height=-5, color=(0, 0, 0))


def test_bool_width_rejected() -> None:
    with pytest.raises(TypeError, match="width"):
        Character(name="A", x=0, y=0, width=True, height=10, color=(0, 0, 0))  # type: ignore[arg-type]


def test_non_int_height_rejected() -> None:
    with pytest.raises(TypeError, match="height"):
        Character(name="A", x=0, y=0, width=10, height=3.14, color=(0, 0, 0))  # type: ignore[arg-type]


# ==================================================================
# Color validation
# ==================================================================


def test_invalid_color_length_rejected() -> None:
    with pytest.raises(ValueError, match="3 channels"):
        Character(name="A", x=0, y=0, width=10, height=10, color=(0, 0))


def test_color_channel_out_of_range_rejected() -> None:
    with pytest.raises(ValueError, match="0–255"):
        Character(name="A", x=0, y=0, width=10, height=10, color=(256, 0, 0))


def test_color_bool_channel_rejected() -> None:
    with pytest.raises(TypeError, match="int"):
        Character(name="A", x=0, y=0, width=10, height=10, color=(True, 0, 0))  # type: ignore[arg-type]


def test_color_non_int_channel_rejected() -> None:
    with pytest.raises(TypeError, match="int"):
        Character(name="A", x=0, y=0, width=10, height=10, color=(0.5, 0, 0))  # type: ignore[arg-type]


# ==================================================================
# Immutability
# ==================================================================


def test_character_is_immutable() -> None:
    """Character attributes cannot be reassigned."""
    from dataclasses import FrozenInstanceError

    ch = Character(name="A", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    with pytest.raises(FrozenInstanceError):
        ch.name = "B"  # type: ignore[misc]


def test_character_has_no_move_api() -> None:
    """Character has no move, update, or set_position methods."""
    ch = Character(name="A", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    assert not hasattr(ch, "move")
    assert not hasattr(ch, "update")
    assert not hasattr(ch, "set_position")


# ==================================================================
# No Pygame types
# ==================================================================


def test_character_has_no_pygame_types() -> None:
    """Character fields are plain Python types, not Pygame objects."""
    ch = Character(name="A", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    assert isinstance(ch.name, str)
    assert isinstance(ch.x, int)
    assert isinstance(ch.y, int)
    assert isinstance(ch.width, int)
    assert isinstance(ch.height, int)
    assert isinstance(ch.color, tuple)


# ==================================================================
# Default scene character
# ==================================================================


def test_default_scene_owns_character() -> None:
    """DefaultScene has a character property."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        assert isinstance(scene.character, Character)
    finally:
        platform.shutdown()


def test_default_character_within_window() -> None:
    """Default character fits fully within the default 960x640 window."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        ch = scene.character
        assert ch.x >= 0
        assert ch.y >= 0
        assert ch.x + ch.width <= 960
        assert ch.y + ch.height <= 640
    finally:
        platform.shutdown()


def test_custom_character_fits_in_window() -> None:
    """A custom small character fits in the window."""
    ch = Character(name="Test", x=0, y=0, width=50, height=50, color=(255, 0, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch)
        assert scene.character is ch
    finally:
        platform.shutdown()


# ==================================================================
# Drawing
# ==================================================================


def test_character_drawn_between_clear_and_present() -> None:
    """draw_rect succeeds between clear_frame and present_frame."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        ch = Character(name="A", x=10, y=20, width=30, height=40, color=(255, 0, 0))
        scene = DefaultScene(renderer, character=ch)
        scene.enter()
        renderer.clear_frame((0, 0, 0))
        scene.on_frame()
        renderer.present_frame()
        assert renderer.frame_count == 1
    finally:
        platform.shutdown()


def test_app_draws_character_each_frame() -> None:
    """App with default scene draws the character in the loop."""
    app = App(Config(target_fps=120))
    _post_quit_after(0.15)
    app.start()
    assert app.is_running is False


def test_character_visible_at_expected_position() -> None:
    """Character is drawn at the configured position and color."""
    import pygame

    ch = Character(name="Test", x=5, y=10, width=20, height=30, color=(255, 128, 64))

    platform = Platform(Config(window_width=200, window_height=200))
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch)
        scene.enter()
        renderer.clear_frame((0, 0, 0))
        scene.on_frame()

        # Sample pixel at character position
        surface = pygame.display.get_surface()
        assert surface is not None
        px = surface.get_at((ch.x + 5, ch.y + 5))
        assert (px.r, px.g, px.b) == ch.color

        # Pixel outside character should still be background
        bg_px = surface.get_at((0, 0))
        assert (bg_px.r, bg_px.g, bg_px.b) == (0, 0, 0)
    finally:
        platform.shutdown()


def test_draw_before_initialize_raises() -> None:
    """draw_rect before platform init raises RuntimeError."""
    platform = Platform(Config())
    with pytest.raises(RuntimeError, match="not initialized"):
        platform.draw_rect(0, 0, 10, 10, (0, 0, 0))


def test_draw_after_shutdown_raises() -> None:
    """draw_rect after shutdown raises RuntimeError."""
    platform = Platform(Config())
    platform.initialize()
    platform.shutdown()
    with pytest.raises(RuntimeError, match="not initialized"):
        platform.draw_rect(0, 0, 10, 10, (0, 0, 0))


# ==================================================================
# Regression
# ==================================================================


def test_character_imports_valid() -> None:
    """Character is importable from engine.entities."""
    from engine.entities import Character  # noqa: F401


def test_default_app_renders_character() -> None:
    """App.main() with default config renders the character."""
    _post_quit_after(0.15)
    App.main()
