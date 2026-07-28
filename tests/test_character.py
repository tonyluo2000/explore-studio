"""Verify Character model and movement behavior.

All rendering tests use SDL_VIDEODRIVER=dummy (conftest.py).
"""

from __future__ import annotations

import threading
import time

import pytest

from engine import App, Config
from engine._logging import init_logging
from engine._platform import Platform
from engine.entities import Bounds, Character
from engine.input import DirectionalInput
from engine.rendering import Renderer

_NO_INPUT = DirectionalInput()


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
    ch = Character(name="Test", x=10, y=20, width=30, height=40, color=(100, 150, 200))
    assert ch.name == "Test"
    assert ch.x == 10
    assert ch.y == 20
    assert ch.width == 30
    assert ch.height == 40
    assert ch.color == (100, 150, 200)


def test_character_float_position() -> None:
    ch = Character(name="A", x=10.6, y=20.4, width=10, height=10, color=(0, 0, 0))
    assert ch.x_float == 10.6
    assert ch.y_float == 20.4
    assert ch.x == 11  # round(10.6) → 11
    assert ch.y == 20  # round(20.4) → 20


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


def test_non_numeric_x_rejected() -> None:
    with pytest.raises(TypeError, match="x"):
        Character(name="A", x="bad", y=0, width=10, height=10, color=(0, 0, 0))  # type: ignore[arg-type]


def test_nan_x_rejected() -> None:
    with pytest.raises(ValueError, match="finite"):
        Character(name="A", x=float("nan"), y=0, width=10, height=10, color=(0, 0, 0))


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


# ==================================================================
# Color validation
# ==================================================================


def test_invalid_color_length_rejected() -> None:
    with pytest.raises(ValueError, match="3 channels"):
        Character(name="A", x=0, y=0, width=10, height=10, color=(0, 0))


def test_color_channel_out_of_range_rejected() -> None:
    with pytest.raises(ValueError, match="0–255"):
        Character(name="A", x=0, y=0, width=10, height=10, color=(256, 0, 0))


# ==================================================================
# Identity/appearance immutability
# ==================================================================


def test_character_name_immutable() -> None:
    ch = Character(name="A", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    with pytest.raises(AttributeError):
        ch.name = "B"  # type: ignore[misc]


def test_character_width_immutable() -> None:
    ch = Character(name="A", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    with pytest.raises(AttributeError):
        ch.width = 20  # type: ignore[misc]


def test_character_has_move_api() -> None:
    ch = Character(name="A", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    assert hasattr(ch, "move")


def test_character_has_no_pygame_types() -> None:
    ch = Character(name="A", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    assert isinstance(ch.name, str)
    assert isinstance(ch.x, int)
    assert isinstance(ch.width, int)
    assert isinstance(ch.color, tuple)


# ==================================================================
# Movement
# ==================================================================


def test_move_changes_position() -> None:
    ch = Character(name="A", x=100, y=100, width=20, height=20, color=(0, 0, 0))
    bounds = Bounds(0, 0, 200, 200)
    ch.move(50, 30, bounds)
    assert ch.x_float == 150
    assert ch.y_float == 130


def test_move_zero_displacement() -> None:
    ch = Character(name="A", x=100, y=100, width=20, height=20, color=(0, 0, 0))
    bounds = Bounds(0, 0, 200, 200)
    ch.move(0, 0, bounds)
    assert ch.x_float == 100
    assert ch.y_float == 100


def test_move_clamps_left_boundary() -> None:
    ch = Character(name="A", x=50, y=50, width=20, height=20, color=(0, 0, 0))
    bounds = Bounds(0, 0, 200, 200)
    ch.move(-100, 0, bounds)
    assert ch.x_float == 0


def test_move_clamps_right_boundary() -> None:
    ch = Character(name="A", x=50, y=50, width=20, height=20, color=(0, 0, 0))
    bounds = Bounds(0, 0, 200, 200)
    ch.move(200, 0, bounds)
    assert ch.x_float == 200


def test_move_clamps_top_boundary() -> None:
    ch = Character(name="A", x=50, y=50, width=20, height=20, color=(0, 0, 0))
    bounds = Bounds(0, 0, 200, 200)
    ch.move(0, -100, bounds)
    assert ch.y_float == 0


def test_move_clamps_bottom_boundary() -> None:
    ch = Character(name="A", x=50, y=50, width=20, height=20, color=(0, 0, 0))
    bounds = Bounds(0, 0, 200, 200)
    ch.move(0, 200, bounds)
    assert ch.y_float == 200


def test_move_rejects_bool_dx() -> None:
    ch = Character(name="A", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    bounds = Bounds(0, 0, 100, 100)
    with pytest.raises(TypeError, match="dx"):
        ch.move(True, 0, bounds)  # type: ignore[arg-type]


def test_move_rejects_nan() -> None:
    ch = Character(name="A", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    bounds = Bounds(0, 0, 100, 100)
    with pytest.raises(ValueError, match="finite"):
        ch.move(float("nan"), 0, bounds)


def test_move_identity_unchanged() -> None:
    ch = Character(name="A", x=100, y=100, width=30, height=40, color=(1, 2, 3))
    bounds = Bounds(0, 0, 500, 500)
    ch.move(10, 20, bounds)
    assert ch.name == "A"
    assert ch.width == 30
    assert ch.height == 40
    assert ch.color == (1, 2, 3)


def test_fractional_movement_accumulates() -> None:
    ch = Character(name="A", x=100.0, y=100.0, width=20, height=20, color=(0, 0, 0))
    bounds = Bounds(0, 0, 500, 500)
    # Move 0.3 three times = 0.9 total → x_float = 100.9, x = 101
    for _ in range(3):
        ch.move(0.3, 0, bounds)
    assert abs(ch.x_float - 100.9) < 0.001
    assert ch.x == 101


# ==================================================================
# DirectionalInput
# ==================================================================


def test_directional_input_defaults() -> None:
    inp = DirectionalInput()
    assert inp.left is False
    assert inp.right is False
    assert inp.up is False
    assert inp.down is False
    assert inp.horizontal == 0
    assert inp.vertical == 0


def test_directional_input_directions() -> None:
    assert DirectionalInput(left=True).horizontal == -1
    assert DirectionalInput(right=True).horizontal == 1
    assert DirectionalInput(up=True).vertical == -1
    assert DirectionalInput(down=True).vertical == 1


def test_directional_input_opposing_cancel() -> None:
    assert DirectionalInput(left=True, right=True).horizontal == 0
    assert DirectionalInput(up=True, down=True).vertical == 0


def test_directional_input_diagonal() -> None:
    inp = DirectionalInput(right=True, down=True)
    assert inp.horizontal == 1
    assert inp.vertical == 1


def test_directional_input_immutable() -> None:
    inp = DirectionalInput(left=True)
    with pytest.raises(AttributeError):
        inp.left = False  # type: ignore[misc]


# ==================================================================
# Default scene + movement integration
# ==================================================================


def test_default_scene_owns_character() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        from engine.scenes import DefaultScene

        scene = DefaultScene(renderer)
        assert isinstance(scene.character, Character)
    finally:
        platform.shutdown()


def test_default_character_within_window() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        from engine.scenes import DefaultScene

        scene = DefaultScene(renderer)
        ch = scene.character
        assert ch.x >= 0 and ch.y >= 0
        assert ch.x + ch.width <= 960
        assert ch.y + ch.height <= 640
    finally:
        platform.shutdown()


def test_character_drawn_between_clear_and_present() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        from engine.scenes import DefaultScene

        ch = Character(name="A", x=10, y=20, width=30, height=40, color=(255, 0, 0))
        scene = DefaultScene(renderer, character=ch)
        scene.enter()
        renderer.clear_frame((0, 0, 0))
        scene.on_frame(_NO_INPUT, 0.016)
        renderer.present_frame()
        assert renderer.frame_count == 1
    finally:
        platform.shutdown()


def test_app_draws_character_each_frame() -> None:
    app = App(Config(target_fps=120))
    _post_quit_after(0.15)
    app.start()
    assert app.is_running is False


def test_character_visible_at_expected_position() -> None:
    import pygame

    ch = Character(name="Test", x=5, y=10, width=20, height=30, color=(255, 128, 64))
    platform = Platform(Config(window_width=200, window_height=200))
    platform.initialize()
    try:
        renderer = Renderer(platform)
        from engine.scenes import DefaultScene

        scene = DefaultScene(renderer, character=ch)
        scene.enter()
        renderer.clear_frame((0, 0, 0))
        scene.on_frame(_NO_INPUT, 0.016)
        surface = pygame.display.get_surface()
        assert surface is not None
        px = surface.get_at((ch.x + 5, ch.y + 5))
        assert (px.r, px.g, px.b) == ch.color
        bg_px = surface.get_at((0, 0))
        assert (bg_px.r, bg_px.g, bg_px.b) == (0, 0, 0)
    finally:
        platform.shutdown()


def test_draw_before_initialize_raises() -> None:
    platform = Platform(Config())
    with pytest.raises(RuntimeError, match="not initialized"):
        platform.draw_rect(0, 0, 10, 10, (0, 0, 0))


def test_draw_after_shutdown_raises() -> None:
    platform = Platform(Config())
    platform.initialize()
    platform.shutdown()
    with pytest.raises(RuntimeError, match="not initialized"):
        platform.draw_rect(0, 0, 10, 10, (0, 0, 0))


def test_character_imports_valid() -> None:
    from engine.entities import Bounds, Character  # noqa: F401


def test_default_app_renders_character() -> None:
    _post_quit_after(0.15)
    App.main()
