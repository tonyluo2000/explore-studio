"""Verify WorldObject model and default scene integration.

All rendering tests use SDL_VIDEODRIVER=dummy (conftest.py).
"""

from __future__ import annotations

import threading
import time

import pytest

from engine import App, Config
from engine._logging import init_logging
from engine._platform import Platform
from engine.entities import Character, WorldObject
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


def test_valid_world_object() -> None:
    wo = WorldObject(name="Tree", x=10, y=20, width=30, height=40, color=(0, 100, 0))
    assert wo.name == "Tree"
    assert wo.x == 10
    assert wo.y == 20
    assert wo.width == 30
    assert wo.height == 40
    assert wo.color == (0, 100, 0)


# ==================================================================
# Name validation
# ==================================================================


def test_empty_name_rejected() -> None:
    with pytest.raises(ValueError, match="name"):
        WorldObject(name="", x=0, y=0, width=10, height=10, color=(0, 0, 0))


def test_whitespace_name_rejected() -> None:
    with pytest.raises(ValueError, match="name"):
        WorldObject(name="   ", x=0, y=0, width=10, height=10, color=(0, 0, 0))


def test_non_string_name_rejected() -> None:
    with pytest.raises(TypeError, match="str"):
        WorldObject(name=123, x=0, y=0, width=10, height=10, color=(0, 0, 0))  # type: ignore[arg-type]


# ==================================================================
# Position validation
# ==================================================================


def test_negative_x_rejected() -> None:
    with pytest.raises(ValueError, match="x"):
        WorldObject(name="A", x=-1, y=0, width=10, height=10, color=(0, 0, 0))


def test_bool_x_rejected() -> None:
    with pytest.raises(TypeError, match="x"):
        WorldObject(name="A", x=True, y=0, width=10, height=10, color=(0, 0, 0))  # type: ignore[arg-type]


def test_non_int_x_rejected() -> None:
    with pytest.raises(TypeError, match="x"):
        WorldObject(name="A", x=1.5, y=0, width=10, height=10, color=(0, 0, 0))  # type: ignore[arg-type]


# ==================================================================
# Dimension validation
# ==================================================================


def test_zero_width_rejected() -> None:
    with pytest.raises(ValueError, match="width"):
        WorldObject(name="A", x=0, y=0, width=0, height=10, color=(0, 0, 0))


def test_negative_height_rejected() -> None:
    with pytest.raises(ValueError, match="height"):
        WorldObject(name="A", x=0, y=0, width=10, height=-5, color=(0, 0, 0))


def test_bool_width_rejected() -> None:
    with pytest.raises(TypeError, match="width"):
        WorldObject(name="A", x=0, y=0, width=True, height=10, color=(0, 0, 0))  # type: ignore[arg-type]


# ==================================================================
# Color validation
# ==================================================================


def test_color_wrong_length_rejected() -> None:
    with pytest.raises(ValueError, match="3 channels"):
        WorldObject(name="A", x=0, y=0, width=10, height=10, color=(0, 0))


def test_color_channel_out_of_range() -> None:
    with pytest.raises(ValueError, match="0–255"):
        WorldObject(name="A", x=0, y=0, width=10, height=10, color=(256, 0, 0))


def test_color_bool_channel_rejected() -> None:
    with pytest.raises(TypeError, match="int"):
        WorldObject(name="A", x=0, y=0, width=10, height=10, color=(True, 0, 0))  # type: ignore[arg-type]


# ==================================================================
# Immutability
# ==================================================================


def test_world_object_is_immutable() -> None:
    wo = WorldObject(name="A", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    with pytest.raises(AttributeError):
        wo.name = "B"  # type: ignore[misc]


def test_world_object_no_move_api() -> None:
    wo = WorldObject(name="A", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    assert not hasattr(wo, "move")
    assert not hasattr(wo, "update")
    assert not hasattr(wo, "interact")


def test_world_object_no_pygame_types() -> None:
    wo = WorldObject(name="A", x=0, y=0, width=10, height=10, color=(0, 0, 0))
    assert isinstance(wo.name, str)
    assert isinstance(wo.x, int)
    assert isinstance(wo.color, tuple)


# ==================================================================
# Default scene integration
# ==================================================================


def test_default_scene_owns_world_object() -> None:
    from engine.scenes import DefaultScene

    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        assert isinstance(scene.world_object, WorldObject)
    finally:
        platform.shutdown()


def test_default_object_within_window() -> None:
    from engine.scenes import DefaultScene

    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        wo = scene.world_object
        assert wo.x >= 0 and wo.y >= 0
        assert wo.x + wo.width <= 960
        assert wo.y + wo.height <= 640
    finally:
        platform.shutdown()


def test_initial_character_and_object_no_overlap() -> None:
    from engine.scenes import DefaultScene

    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        ch = scene.character
        wo = scene.world_object
        # Rectangles overlap if one is not to the left/right/above/below the other
        overlap_x = ch.x < wo.x + wo.width and ch.x + ch.width > wo.x
        overlap_y = ch.y < wo.y + wo.height and ch.y + ch.height > wo.y
        assert not (overlap_x and overlap_y), "Character and world object should not overlap"
    finally:
        platform.shutdown()


# ==================================================================
# Drawing
# ==================================================================


def test_object_drawn_before_character() -> None:
    """World object is drawn, then character, in each frame."""
    from engine.scenes import DefaultScene

    ch = Character(name="C", x=100, y=100, width=20, height=20, color=(0, 0, 255))
    wo = WorldObject(name="O", x=5, y=5, width=10, height=10, color=(255, 0, 0))

    platform = Platform(Config(window_width=200, window_height=200))
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo)
        scene.enter()
        renderer.clear_frame((0, 0, 0))
        scene.on_frame(_NO_INPUT, 0.016)
        # Character is drawn second, so at character position we see character color
        import pygame

        surface = pygame.display.get_surface()
        assert surface is not None
        ch_px = surface.get_at((ch.x + 5, ch.y + 5))
        assert (ch_px.r, ch_px.g, ch_px.b) == ch.color
        # Object pixel shows object color
        wo_px = surface.get_at((wo.x + 5, wo.y + 5))
        assert (wo_px.r, wo_px.g, wo_px.b) == wo.color
    finally:
        platform.shutdown()


def test_app_with_world_object_runs() -> None:
    """App with default scene containing world object starts and exits."""
    app = App(Config(target_fps=120))
    _post_quit_after(0.15)
    app.start()
    assert app.is_running is False


def test_world_object_imports_valid() -> None:
    from engine.entities import WorldObject  # noqa: F401


def test_directional_input_return_type() -> None:
    """Platform.poll_directional_input() returns DirectionalInput, not dict."""
    platform = Platform(Config())
    platform.initialize()
    try:
        result = platform.poll_directional_input()
        assert isinstance(result, DirectionalInput)
        assert not isinstance(result, dict)
    finally:
        platform.shutdown()
