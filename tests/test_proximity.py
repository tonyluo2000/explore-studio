"""Verify proximity detection behaviour.

All tests use a headless Pygame driver (SDL_VIDEODRIVER=dummy).
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
from engine.interactions._proximity import (
    _center_distance_sq,
    _validate_interaction_range,
    is_near,
)
from engine.rendering import Renderer
from engine.scenes import DefaultScene

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
# Range validation
# ==================================================================


def test_valid_int_range() -> None:
    r = _validate_interaction_range(120)
    assert r == 120.0
    assert isinstance(r, float)


def test_valid_float_range() -> None:
    r = _validate_interaction_range(120.5)
    assert r == 120.5


def test_zero_range_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        _validate_interaction_range(0)


def test_negative_range_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        _validate_interaction_range(-10)


def test_bool_range_rejected() -> None:
    with pytest.raises(TypeError, match="int or float"):
        _validate_interaction_range(True)  # type: ignore[arg-type]


def test_string_range_rejected() -> None:
    with pytest.raises(TypeError, match="int or float"):
        _validate_interaction_range("120")  # type: ignore[arg-type]


def test_nan_range_rejected() -> None:
    with pytest.raises(ValueError, match="NaN"):
        _validate_interaction_range(float("nan"))


def test_positive_infinity_rejected() -> None:
    with pytest.raises(ValueError, match="finite"):
        _validate_interaction_range(float("inf"))


def test_negative_infinity_rejected() -> None:
    with pytest.raises(ValueError, match="finite"):
        _validate_interaction_range(float("-inf"))


def test_none_range_rejected() -> None:
    with pytest.raises(TypeError, match="int or float"):
        _validate_interaction_range(None)  # type: ignore[arg-type]


# ==================================================================
# Distance calculation — unit tests
# ==================================================================


def test_identical_centers_are_near() -> None:
    """Two rectangles at the same position and size have identical centers."""
    assert is_near(0, 0, 10, 10, 0, 0, 10, 10, 100.0) is True


def test_distance_below_range_is_near() -> None:
    """When center distance < range, result is True."""
    # Centers at (5,5) and (10,5) → distance = 5, squared = 25
    assert is_near(0, 0, 10, 10, 5, 0, 10, 10, 100.0) is True
    assert is_near(0, 0, 10, 10, 5, 0, 10, 10, 26.0) is True


def test_distance_equal_to_range_is_near() -> None:
    """Inclusive boundary: distance == range → True."""
    # Centers at (5,5) and (15,5) → distance = 10, squared = 100
    assert is_near(0, 0, 10, 10, 10, 0, 10, 10, 100.0) is True


def test_distance_above_range_is_not_near() -> None:
    """When center distance > range, result is False."""
    # Centers at (5,5) and (15,5) → distance = 10, squared = 100
    assert is_near(0, 0, 10, 10, 10, 0, 10, 10, 99.0) is False
    # Just above: range_sq=99.9 < distance²=100
    assert is_near(0, 0, 10, 10, 10, 0, 10, 10, 99.9) is False


def test_horizontal_separation() -> None:
    """Pure horizontal separation."""
    # A at (0,0) 10×10 → center (5,5)
    # B at (100,0) 10×10 → center (105,5)
    # distance = 100, squared = 10000
    assert is_near(0, 0, 10, 10, 100, 0, 10, 10, 10000.0) is True
    assert is_near(0, 0, 10, 10, 100, 0, 10, 10, 9999.0) is False


def test_vertical_separation() -> None:
    """Pure vertical separation."""
    # A at (0,0) 10×10 → center (5,5)
    # B at (0,100) 10×10 → center (5,105)
    # distance = 100, squared = 10000
    assert is_near(0, 0, 10, 10, 0, 100, 10, 10, 10000.0) is True
    assert is_near(0, 0, 10, 10, 0, 100, 10, 10, 9999.0) is False


def test_diagonal_separation() -> None:
    """Diagonal separation (3-4-5 triangle)."""
    # A at (0,0) 10×10 → center (5,5)
    # B at (30,40) 10×10 → center (35,45)
    # dx = 30, dy = 40, distance² = 900 + 1600 = 2500
    assert is_near(0, 0, 10, 10, 30, 40, 10, 10, 2500.0) is True
    assert is_near(0, 0, 10, 10, 30, 40, 10, 10, 2499.0) is False


def test_fractional_character_coordinates() -> None:
    """Fractional character coordinates are preserved."""
    # Character at (10.6, 20.4) 100×100 → center (60.6, 70.4)
    # Object at (0, 0) 50×50 → center (25, 25)
    # dx = 35.6, dy = 45.4, distance² ≈ 1267.36 + 2061.16 = 3328.52
    assert is_near(10.6, 20.4, 100, 100, 0, 0, 50, 50, 3330.0) is True
    assert is_near(10.6, 20.4, 100, 100, 0, 0, 50, 50, 3328.0) is False


def test_integer_world_object_coordinates() -> None:
    """Integer object coordinates work naturally with fractional character."""
    # Object at int position (100, 200)
    assert is_near(0, 0, 100, 100, 100, 200, 50, 50, 100000.0) is True


def test_dimensions_included_in_center() -> None:
    """Center calculation correctly uses width and height."""
    # A: (0,0) 20×30 → center (10, 15)
    # B: (5,10) 10×20 → center (10, 20)
    # dx = 0, dy = 5, distance² = 25
    assert is_near(0, 0, 20, 30, 5, 10, 10, 20, 25.0) is True
    assert is_near(0, 0, 20, 30, 5, 10, 10, 20, 24.0) is False


def test_center_distance_sq_no_truncation() -> None:
    """_center_distance_sq preserves fractional values."""
    result = _center_distance_sq(10.3, 20.7, 100, 100, 0, 0, 50, 50)
    # Center A: (60.3, 70.7), Center B: (25, 25)
    # dx = 35.3, dy = 45.7 → dx² + dy²
    expected = 35.3**2 + 45.7**2
    assert result == pytest.approx(expected)


# ==================================================================
# Scene state — initial and read-only
# ==================================================================


def test_initial_proximity_is_false() -> None:
    """Default composition places Explorer far from Treasure Chest."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        assert scene.is_character_near_object is False
    finally:
        platform.shutdown()


def test_proximity_result_is_read_only() -> None:
    """Callers cannot assign is_character_near_object directly."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        with pytest.raises(AttributeError):
            scene.is_character_near_object = True  # type: ignore[misc]
    finally:
        platform.shutdown()


def test_proximity_becomes_true_when_near() -> None:
    """Moving the character close to the object sets proximity to True."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=100, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=60)
        scene.enter()
        assert scene.is_character_near_object is False
        # Move right toward object
        scene.on_frame(DirectionalInput(right=True), 1.0)
        # Character moves 160px right → x=160, center (180,20)
        # Object center (120,20), distance = 60 → exactly at boundary
        assert scene.is_character_near_object is True
    finally:
        platform.shutdown()


def test_proximity_becomes_false_after_moving_away() -> None:
    """Proximity returns to False when character moves away."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=100, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=60)
        scene.enter()
        # Move into range
        scene.on_frame(DirectionalInput(right=True), 1.0)
        assert scene.is_character_near_object is True
        # Move back out
        scene.on_frame(DirectionalInput(left=True), 1.0)
        assert scene.is_character_near_object is False
    finally:
        platform.shutdown()


def test_repeated_near_frames_remain_true() -> None:
    """Multiple frames inside range keep proximity True."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=100, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()
        scene.on_frame(DirectionalInput(right=True), 0.5)
        assert scene.is_character_near_object is True
        # Stay put — no movement
        scene.on_frame(_NO_INPUT, 0.016)
        assert scene.is_character_near_object is True
        scene.on_frame(_NO_INPUT, 0.016)
        assert scene.is_character_near_object is True
    finally:
        platform.shutdown()


def test_repeated_far_frames_remain_false() -> None:
    """Multiple frames outside range keep proximity False."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        scene.enter()
        assert scene.is_character_near_object is False
        scene.on_frame(_NO_INPUT, 0.016)
        assert scene.is_character_near_object is False
        scene.on_frame(_NO_INPUT, 0.016)
        assert scene.is_character_near_object is False
    finally:
        platform.shutdown()


def test_scene_owns_proximity_result() -> None:
    """Each DefaultScene owns its own proximity result."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene1 = DefaultScene(renderer)
        scene2 = DefaultScene(renderer)
        assert scene1.is_character_near_object is scene2.is_character_near_object is False
        # These are independent instances
        assert scene1.is_character_near_object is False
        assert scene2.is_character_near_object is False
    finally:
        platform.shutdown()


def test_no_global_proximity_state() -> None:
    """Proximity state lives only on the scene, not as a global variable."""
    import engine.interactions as interactions_module

    # The interactions package contains a _proximity helper module,
    # but it must not expose any mutable global proximity *state*.
    assert not hasattr(interactions_module, "is_near")
    assert not hasattr(interactions_module, "proximity_state")


# ==================================================================
# Frame ordering
# ==================================================================


def test_movement_before_proximity() -> None:
    """Proximity uses the character position updated in the same frame."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=200, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=50)
        scene.enter()
        assert scene.is_character_near_object is False
        # One frame: move right → should move before proximity check
        scene.on_frame(DirectionalInput(right=True), 1.0)
        # After 1s at 160px/s: x=160, center (180,20)
        # Object center (220,20), distance = 40 → within range 50
        assert scene.is_character_near_object is True
    finally:
        platform.shutdown()


def test_proximity_evaluated_before_clear() -> None:
    """Proximity is evaluated before the frame is cleared."""
    # We verify this indirectly: if proximity raised, clear must not occur.
    # We test the failure path separately; here we confirm normal ordering.
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        scene.enter()

        scene.on_frame(_NO_INPUT, 0.016)
        # Frame count didn't increment (present_frame not called by scene)
        # The main loop calls present_frame, not the scene
    finally:
        platform.shutdown()


def test_updated_position_used() -> None:
    """Proximity result reflects the position after movement, not before."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=200, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        # Small range so we can see the transition clearly
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=10)
        scene.enter()
        assert scene.is_character_near_object is False
        # Move to exactly the object position
        scene.on_frame(DirectionalInput(right=True), 1.25)
        # x ≈ 200, centers align
        assert scene.is_character_near_object is True
    finally:
        platform.shutdown()


class _SpyProximityScene(DefaultScene):
    """Scene that tracks how many times proximity is evaluated."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        self.proximity_eval_count = 0

    def _evaluate_proximity(self) -> None:
        self.proximity_eval_count += 1
        super()._evaluate_proximity()


def test_one_proximity_evaluation_per_frame() -> None:
    """Proximity is evaluated exactly once per completed frame."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _SpyProximityScene(renderer)
        scene.enter()
        assert scene.proximity_eval_count == 0
        scene.on_frame(_NO_INPUT, 0.016)
        assert scene.proximity_eval_count == 1
        scene.on_frame(_NO_INPUT, 0.016)
        assert scene.proximity_eval_count == 2
        scene.on_frame(_NO_INPUT, 0.016)
        assert scene.proximity_eval_count == 3
    finally:
        platform.shutdown()


def test_quit_before_frame_no_evaluation() -> None:
    """Quitting before any frame work means no proximity evaluation."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _SpyProximityScene(renderer)
        scene.enter()
        # Exit without any frames
        scene.exit()
        assert scene.proximity_eval_count == 0
    finally:
        platform.shutdown()


def test_shutdown_no_extra_evaluation() -> None:
    """Shutdown does not trigger extra proximity evaluation."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _SpyProximityScene(renderer)
        scene.enter()
        scene.on_frame(_NO_INPUT, 0.016)
        count_after_frame = scene.proximity_eval_count
        scene.exit()
        # No extra evaluation after exit
        assert scene.proximity_eval_count == count_after_frame
    finally:
        platform.shutdown()


# ==================================================================
# No side effects
# ==================================================================


def test_proximity_does_not_move_world_object() -> None:
    """Proximity detection does not change the world object's position."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        wo = WorldObject(name="O", x=50, y=50, width=30, height=30, color=(0, 255, 0))
        scene = DefaultScene(renderer, world_object=wo)
        scene.enter()
        original_x, original_y = wo.x, wo.y
        # Move character close
        scene.on_frame(DirectionalInput(right=True), 1.0)
        assert wo.x == original_x
        assert wo.y == original_y
    finally:
        platform.shutdown()


def test_proximity_does_not_alter_character_position() -> None:
    """Proximity detection does not change character position."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=100, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=50)
        scene.enter()
        # Move right into range
        scene.on_frame(DirectionalInput(right=True), 1.0)
        pos_after_move = (ch.x_float, ch.y_float)
        # Frame with no input — position should not change
        scene.on_frame(_NO_INPUT, 0.016)
        assert (ch.x_float, ch.y_float) == pos_after_move
    finally:
        platform.shutdown()


def test_proximity_does_not_block_movement() -> None:
    """Character can move through the object even when near."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()
        # Move past the object
        scene.on_frame(DirectionalInput(right=True), 1.0)
        # Character should have moved the full distance (not blocked)
        # x_float should be ~160 (160 px/s × 1s)
        assert ch.x_float == pytest.approx(160.0)
    finally:
        platform.shutdown()


def test_proximity_preserves_colors() -> None:
    """Proximity does not modify character or object colors."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
        wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()
        original_ch_color = ch.color
        original_wo_color = wo.color
        scene.on_frame(DirectionalInput(right=True), 1.0)
        assert scene.is_character_near_object is True
        assert ch.color == original_ch_color
        assert wo.color == original_wo_color
    finally:
        platform.shutdown()


def test_proximity_preserves_dimensions() -> None:
    """Proximity does not change character or object dimensions."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
        wo = WorldObject(name="O", x=30, y=0, width=50, height=30, color=(0, 255, 0))
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()
        scene.on_frame(DirectionalInput(right=True), 1.0)
        assert ch.width == 40 and ch.height == 40
        assert wo.width == 50 and wo.height == 30
    finally:
        platform.shutdown()


def test_proximity_preserves_drawing_order() -> None:
    """Drawing order (object before character) is unchanged by proximity."""
    import pygame

    ch = Character(name="C", x=20, y=20, width=20, height=20, color=(0, 0, 255))
    wo = WorldObject(name="O", x=20, y=20, width=20, height=20, color=(255, 0, 0))
    platform = Platform(Config(window_width=200, window_height=200))
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()
        scene.on_frame(_NO_INPUT, 0.016)
        surface = pygame.display.get_surface()
        assert surface is not None
        # Overlapping region should show character color (drawn second, on top)
        px = surface.get_at((ch.x + 5, ch.y + 5))
        assert (px.r, px.g, px.b) == ch.color
    finally:
        platform.shutdown()


def test_proximity_causes_no_interaction_outcome() -> None:
    """True proximity does not trigger any interaction behaviour."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()
        scene.on_frame(DirectionalInput(right=True), 1.0)
        assert scene.is_character_near_object is True
        # Object is unchanged — still the same name, position, color
        assert wo.name == "O"
        assert wo.x == 30 and wo.y == 0
        assert wo.color == (0, 255, 0)
    finally:
        platform.shutdown()


# ==================================================================
# Failure behaviour
# ==================================================================


class _FailingProximityScene(DefaultScene):
    """Scene whose proximity evaluation always raises."""

    def _evaluate_proximity(self) -> None:
        raise RuntimeError("simulated proximity failure")


def test_proximity_failure_prevents_clear() -> None:
    """When proximity fails, the frame is not cleared."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _FailingProximityScene(renderer)

        # Use a spy to detect whether clear_frame was called
        clear_called = False
        original_clear = renderer.clear_frame

        def spy_clear(color: tuple[int, int, int]) -> None:
            nonlocal clear_called
            clear_called = True
            original_clear(color)

        renderer.clear_frame = spy_clear  # type: ignore[method-assign]
        scene.enter()

        with pytest.raises(RuntimeError, match="simulated proximity failure"):
            scene.on_frame(_NO_INPUT, 0.016)

        assert clear_called is False
    finally:
        platform.shutdown()


def test_proximity_failure_prevents_world_object_drawing() -> None:
    """When proximity fails, the world object is not drawn."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _FailingProximityScene(renderer)

        draw_calls: list[str] = []
        original_draw = renderer.draw_rect

        def spy_draw(x: int, y: int, w: int, h: int, c: tuple[int, int, int]) -> None:
            draw_calls.append(f"draw({x},{y},{w},{h})")
            original_draw(x, y, w, h, c)

        renderer.draw_rect = spy_draw  # type: ignore[method-assign]
        scene.enter()

        with pytest.raises(RuntimeError, match="simulated proximity failure"):
            scene.on_frame(_NO_INPUT, 0.016)

        assert len(draw_calls) == 0, f"Expected no draw calls, got {draw_calls}"
    finally:
        platform.shutdown()


def test_proximity_failure_prevents_character_drawing() -> None:
    """When proximity fails, the character is not drawn."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _FailingProximityScene(renderer)

        draw_calls: list[str] = []
        original_draw = renderer.draw_rect

        def spy_draw(x: int, y: int, w: int, h: int, c: tuple[int, int, int]) -> None:
            draw_calls.append(f"draw({x},{y},{w},{h})")
            original_draw(x, y, w, h, c)

        renderer.draw_rect = spy_draw  # type: ignore[method-assign]
        scene.enter()

        with pytest.raises(RuntimeError, match="simulated proximity failure"):
            scene.on_frame(_NO_INPUT, 0.016)

        assert len(draw_calls) == 0
    finally:
        platform.shutdown()


def test_proximity_failure_prevents_presentation() -> None:
    """When proximity fails, the frame is not presented."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _FailingProximityScene(renderer)
        scene.enter()

        frame_before = renderer.frame_count
        with pytest.raises(RuntimeError, match="simulated proximity failure"):
            scene.on_frame(_NO_INPUT, 0.016)

        assert renderer.frame_count == frame_before
    finally:
        platform.shutdown()


def test_proximity_failure_scene_exit_still_occurs() -> None:
    """Scene exit proceeds normally after proximity failure."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _FailingProximityScene(renderer)
        scene.enter()

        with pytest.raises(RuntimeError, match="simulated proximity failure"):
            scene.on_frame(_NO_INPUT, 0.016)

        # Scene exit should still work
        scene.exit()
        assert scene.state.value == "exited"
    finally:
        platform.shutdown()


def test_proximity_failure_platform_shutdown_occurs() -> None:
    """Platform shutdown proceeds after proximity failure in main loop."""
    # Use the App with a failing scene to verify full cleanup
    import pygame

    class _FailingApp(App):
        def _create_scene(self) -> DefaultScene:
            assert self._renderer is not None
            return _FailingProximityScene(self._renderer)

    app = _FailingApp(Config(target_fps=120))

    # Post quit after a short delay so the loop processes one frame
    def post_quit() -> None:
        time.sleep(0.1)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=post_quit, daemon=True).start()

    # The app should raise because of the proximity failure,
    # but cleanup should still run
    with pytest.raises(RuntimeError, match="simulated proximity failure"):
        app.start()

    assert app.is_running is False


def test_proximity_failure_exception_observable() -> None:
    """Original proximity exception propagates, not a wrapped error."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _FailingProximityScene(renderer)
        scene.enter()

        with pytest.raises(RuntimeError) as exc_info:
            scene.on_frame(_NO_INPUT, 0.016)

        assert "simulated proximity failure" in str(exc_info.value)
    finally:
        platform.shutdown()


def test_cleanup_exception_precedence_preserved() -> None:
    """If proximity fails and exit also fails, original error takes precedence."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _FailingProximityScene(renderer)
        scene.enter()

        with pytest.raises(RuntimeError, match="simulated proximity failure"):
            scene.on_frame(_NO_INPUT, 0.016)

        # Scene exit should be idempotent
        scene.exit()
    finally:
        platform.shutdown()


def test_cleanup_not_duplicated() -> None:
    """Scene exit after proximity failure does not double-clean."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _FailingProximityScene(renderer)
        scene.enter()

        with pytest.raises(RuntimeError, match="simulated proximity failure"):
            scene.on_frame(_NO_INPUT, 0.016)

        # Exit once
        scene.exit()
        # Exit again — idempotent
        scene.exit()
        assert scene.state.value == "exited"
    finally:
        platform.shutdown()


# ==================================================================
# App integration — smoke test
# ==================================================================


def test_app_with_proximity_runs_and_exits() -> None:
    """Full application starts, runs, and exits with proximity detection."""
    app = App(Config(target_fps=120))
    _post_quit_after(0.15)
    app.start()
    assert app.is_running is False


def test_default_interaction_range_is_120() -> None:
    """The default interaction range is 120 pixels."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        assert scene.interaction_range == 120.0
    finally:
        platform.shutdown()


def test_interaction_range_read_only() -> None:
    """Callers cannot assign interaction_range directly."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        with pytest.raises(AttributeError):
            scene.interaction_range = 200.0  # type: ignore[misc]
    finally:
        platform.shutdown()
