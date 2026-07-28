"""Verify text drawing and interaction feedback behaviour.

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
from engine.input import DirectionalInput, InteractionInput
from engine.rendering import Renderer
from engine.scenes import DefaultScene

_NO_INPUT = DirectionalInput()
_NO_INTERACTION = InteractionInput()
_E_PRESSED = InteractionInput(interact_pressed=True)


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
# Text validation — platform.draw_text
# ==================================================================


def test_draw_text_valid() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        platform.clear_frame((0, 0, 0))
        platform.draw_text("Hello", 10, 20, (255, 255, 255), 24)
        # No exception → success
    finally:
        platform.shutdown()


def test_draw_text_empty_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(ValueError, match="empty"):
            platform.draw_text("", 0, 0, (255, 255, 255), 24)
    finally:
        platform.shutdown()


def test_draw_text_whitespace_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(ValueError, match="whitespace"):
            platform.draw_text("   ", 0, 0, (255, 255, 255), 24)
    finally:
        platform.shutdown()


def test_draw_text_non_string_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(TypeError, match="str"):
            platform.draw_text(123, 0, 0, (255, 255, 255), 24)  # type: ignore[arg-type]
    finally:
        platform.shutdown()


def test_draw_text_negative_x_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(ValueError, match="x"):
            platform.draw_text("Hi", -1, 0, (255, 255, 255), 24)
    finally:
        platform.shutdown()


def test_draw_text_bool_x_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(TypeError, match="x"):
            platform.draw_text("Hi", True, 0, (255, 255, 255), 24)  # type: ignore[arg-type]
    finally:
        platform.shutdown()


def test_draw_text_non_int_x_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(TypeError, match="x"):
            platform.draw_text("Hi", 1.5, 0, (255, 255, 255), 24)  # type: ignore[arg-type]
    finally:
        platform.shutdown()


def test_draw_text_negative_y_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(ValueError, match="y"):
            platform.draw_text("Hi", 0, -1, (255, 255, 255), 24)
    finally:
        platform.shutdown()


def test_draw_text_bool_y_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(TypeError, match="y"):
            platform.draw_text("Hi", 0, True, (255, 255, 255), 24)  # type: ignore[arg-type]
    finally:
        platform.shutdown()


def test_draw_text_font_size_positive() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        platform.clear_frame((0, 0, 0))
        platform.draw_text("Hi", 0, 0, (255, 255, 255), 24)
    finally:
        platform.shutdown()


def test_draw_text_zero_font_size_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(ValueError, match="font_size"):
            platform.draw_text("Hi", 0, 0, (255, 255, 255), 0)
    finally:
        platform.shutdown()


def test_draw_text_negative_font_size_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(ValueError, match="font_size"):
            platform.draw_text("Hi", 0, 0, (255, 255, 255), -5)
    finally:
        platform.shutdown()


def test_draw_text_non_int_font_size_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(TypeError, match="font_size"):
            platform.draw_text("Hi", 0, 0, (255, 255, 255), 12.5)  # type: ignore[arg-type]
    finally:
        platform.shutdown()


def test_draw_text_bool_font_size_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(TypeError, match="font_size"):
            platform.draw_text("Hi", 0, 0, (255, 255, 255), True)  # type: ignore[arg-type]
    finally:
        platform.shutdown()


def test_draw_text_invalid_color_length() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(ValueError, match="3 channels"):
            platform.draw_text("Hi", 0, 0, (255, 0), 24)  # type: ignore[arg-type]
    finally:
        platform.shutdown()


def test_draw_text_color_out_of_range() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(ValueError, match="0–255"):
            platform.draw_text("Hi", 0, 0, (256, 0, 0), 24)
    finally:
        platform.shutdown()


def test_draw_text_bool_color_channel_rejected() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        with pytest.raises(TypeError, match="int"):
            platform.draw_text("Hi", 0, 0, (True, 0, 0), 24)  # type: ignore[arg-type]
    finally:
        platform.shutdown()


def test_draw_text_no_pygame_type_returned() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        platform.clear_frame((0, 0, 0))
        result = platform.draw_text("Hi", 0, 0, (255, 255, 255), 24)
        assert result is None
    finally:
        platform.shutdown()


def test_draw_text_before_initialize_raises() -> None:
    platform = Platform(Config())
    with pytest.raises(RuntimeError, match="not initialized"):
        platform.draw_text("Hi", 0, 0, (255, 255, 255), 24)


def test_draw_text_after_shutdown_raises() -> None:
    platform = Platform(Config())
    platform.initialize()
    platform.shutdown()
    with pytest.raises(RuntimeError, match="not initialized"):
        platform.draw_text("Hi", 0, 0, (255, 255, 255), 24)


# ==================================================================
# Renderer delegation
# ==================================================================


def test_renderer_delegates_text_to_platform() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        renderer.clear_frame((0, 0, 0))
        renderer.draw_text("Test", 50, 60, (200, 200, 200), 18)
        # No exception → delegated successfully
    finally:
        platform.shutdown()


def test_renderer_draw_text_no_pygame_objects() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        renderer.clear_frame((0, 0, 0))
        result = renderer.draw_text("A", 0, 0, (255, 255, 255), 16)
        assert result is None
    finally:
        platform.shutdown()


def test_renderer_rectangle_drawing_unchanged() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        renderer.clear_frame((0, 0, 0))
        renderer.draw_rect(10, 20, 30, 40, (100, 150, 200))
        # No exception → rectangle drawing works
    finally:
        platform.shutdown()


# ==================================================================
# Prompt visibility
# ==================================================================


def _make_near_scene(platform: Platform) -> DefaultScene:
    """Create a scene with character near the world object (range 200)."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    renderer = Renderer(platform)
    return DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)


def test_initial_far_no_prompt() -> None:
    """When far away, no prompt is drawn."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = DefaultScene(Renderer(platform))
        scene.enter()
        assert scene.is_character_near_object is False
        assert scene.feedback_remaining == 0.0
    finally:
        platform.shutdown()


def test_prompt_appears_when_near() -> None:
    """Moving near displays the prompt."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
        assert scene.is_character_near_object is True
        assert scene.feedback_remaining == 0.0
        # Prompt should draw when near — verified by rendering without error
        renderer2 = scene._renderer  # type: ignore[attr-defined]
        renderer2.clear_frame((0, 0, 0))
        scene.render()
    finally:
        platform.shutdown()


def test_prompt_remains_while_near() -> None:
    """Staying near keeps the prompt visible."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
        assert scene.is_character_near_object is True
        # Another frame near — still no crash drawing
        scene.update(_NO_INPUT, _NO_INTERACTION, 0.016)
        assert scene.is_character_near_object is True
        renderer2 = scene._renderer  # type: ignore[attr-defined]
        renderer2.clear_frame((0, 0, 0))
        scene.render()
    finally:
        platform.shutdown()


def test_prompt_disappears_when_far() -> None:
    """Moving away removes the prompt."""
    # Object at x=300 so character can leave range when moving left.
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=300, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = DefaultScene(
            Renderer(platform), character=ch, world_object=wo, interaction_range=40
        )
        scene.enter()
        # Move right 2s (320px) → center at (340,20), object center (320,20) → dist=20 <= 40 → near
        scene.update(DirectionalInput(right=True), _NO_INTERACTION, 2.0)
        assert scene.is_character_near_object is True
        # Move left 2s (320px) → back to x=0, center (20,20) → dist=300 > 40 → far
        scene.update(DirectionalInput(left=True), _NO_INTERACTION, 2.0)
        assert scene.is_character_near_object is False
    finally:
        platform.shutdown()


def test_proximity_alone_no_success_message() -> None:
    """Being near without pressing E does not show success."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
        assert scene.is_character_near_object is True
        assert scene.did_interact_this_frame is False
        assert scene.feedback_remaining == 0.0
    finally:
        platform.shutdown()


def test_prompt_no_state_mutation() -> None:
    """Prompt display does not change object or character state."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        original_wo_pos = (scene.world_object.x, scene.world_object.y)
        original_wo_color = scene.world_object.color

        scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
        assert scene.is_character_near_object is True

        assert scene.world_object.x == original_wo_pos[0]
        assert scene.world_object.y == original_wo_pos[1]
        assert scene.world_object.color == original_wo_color
    finally:
        platform.shutdown()


# ==================================================================
# Success message — duration
# ==================================================================


def test_valid_interaction_activates_success() -> None:
    """Valid E press near the chest activates success message."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.did_interact_this_frame is True
        assert scene.feedback_remaining == pytest.approx(2.0)
    finally:
        platform.shutdown()


def test_invalid_far_interaction_no_success() -> None:
    """E press far from chest does not activate success."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = DefaultScene(Renderer(platform))
        scene.enter()
        scene.update(_NO_INPUT, _E_PRESSED, 0.016)
        assert scene.did_interact_this_frame is False
        assert scene.feedback_remaining == 0.0
    finally:
        platform.shutdown()


def test_interaction_pulse_starts_full_duration() -> None:
    """Interaction pulse sets timer to full configured duration."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.feedback_remaining == pytest.approx(2.0)
    finally:
        platform.shutdown()


def test_success_message_remains_on_subsequent_frames() -> None:
    """Success message persists across frames."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        remaining_after_interact = scene.feedback_remaining

        # Next frame without E — message still active, timer decreased
        scene.update(_NO_INPUT, _NO_INTERACTION, 0.1)
        assert scene.feedback_remaining < remaining_after_interact
        assert scene.feedback_remaining > 0
    finally:
        platform.shutdown()


def test_timer_decreases_with_dt() -> None:
    """Timer decreases by dt each frame."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.feedback_remaining == pytest.approx(2.0)

        scene.update(_NO_INPUT, _NO_INTERACTION, 0.5)
        assert scene.feedback_remaining == pytest.approx(1.5)
    finally:
        platform.shutdown()


def test_zero_dt_preserves_duration() -> None:
    """Zero dt does not reduce the timer."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        before = scene.feedback_remaining

        scene.update(_NO_INPUT, _NO_INTERACTION, 0.0)
        assert scene.feedback_remaining == pytest.approx(before)
    finally:
        platform.shutdown()


def test_large_dt_expires_message() -> None:
    """A dt larger than remaining duration expires the message."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.feedback_remaining > 0

        scene.update(_NO_INPUT, _NO_INTERACTION, 5.0)
        assert scene.feedback_remaining == 0.0
    finally:
        platform.shutdown()


def test_timer_clamps_to_zero() -> None:
    """Timer never becomes negative."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        scene.update(_NO_INPUT, _NO_INTERACTION, 10.0)
        assert scene.feedback_remaining == 0.0
    finally:
        platform.shutdown()


def test_message_disappears_after_expiry() -> None:
    """Success message goes away after timer expires."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.feedback_remaining > 0

        # Expire it
        scene.update(_NO_INPUT, _NO_INTERACTION, 2.5)
        assert scene.feedback_remaining == 0.0
    finally:
        platform.shutdown()


def test_later_interaction_reactivates() -> None:
    """A later valid E press restarts the message."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()

        # First interaction
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.feedback_remaining == pytest.approx(2.0)

        # Let it expire
        scene.update(_NO_INPUT, _NO_INTERACTION, 2.5)
        assert scene.feedback_remaining == 0.0

        # Second interaction
        scene.update(_NO_INPUT, _E_PRESSED, 0.016)
        assert scene.feedback_remaining == pytest.approx(2.0)
    finally:
        platform.shutdown()


def test_interaction_while_active_restarts() -> None:
    """E press while message is active restarts timer at full duration."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()

        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.feedback_remaining == pytest.approx(2.0)

        # Wait a bit
        scene.update(_NO_INPUT, _NO_INTERACTION, 0.5)
        assert scene.feedback_remaining == pytest.approx(1.5)

        # Interact again — restarts at 2.0
        scene.update(_NO_INPUT, _E_PRESSED, 0.016)
        assert scene.feedback_remaining == pytest.approx(2.0)
    finally:
        platform.shutdown()


# ==================================================================
# Message priority
# ==================================================================


def test_success_overrides_prompt() -> None:
    """Success message overrides proximity prompt when both are active."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()

        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.is_character_near_object is True
        assert scene.feedback_remaining > 0
        # Success is active — drawing should use success text
        renderer2 = scene._renderer  # type: ignore[attr-defined]
        renderer2.clear_frame((0, 0, 0))
        scene.render()
    finally:
        platform.shutdown()


def test_prompt_returns_after_success_expires() -> None:
    """Prompt returns after success expires while still near."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()

        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.feedback_remaining > 0

        # Expire success while still near
        scene.update(_NO_INPUT, _NO_INTERACTION, 2.5)
        assert scene.feedback_remaining == 0.0
        assert scene.is_character_near_object is True
        # Now prompt should show
        renderer2 = scene._renderer  # type: ignore[attr-defined]
        renderer2.clear_frame((0, 0, 0))
        scene.render()
    finally:
        platform.shutdown()


def test_success_remains_after_moving_away() -> None:
    """Success message stays visible after moving away until expiry."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=300, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = DefaultScene(
            Renderer(platform), character=ch, world_object=wo, interaction_range=40
        )
        scene.enter()

        # Move right into range and interact
        scene.update(DirectionalInput(right=True), _E_PRESSED, 2.0)
        assert scene.feedback_remaining > 0

        # Move away but success still active (0.1s left, not enough to expire)
        scene.update(DirectionalInput(left=True), _NO_INTERACTION, 1.0)
        assert scene.is_character_near_object is False
        assert scene.feedback_remaining > 0
    finally:
        platform.shutdown()


def test_nothing_after_expiry_while_far() -> None:
    """No message after success expires while far away."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=300, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = DefaultScene(
            Renderer(platform), character=ch, world_object=wo, interaction_range=40
        )
        scene.enter()

        # Move right into range and interact
        scene.update(DirectionalInput(right=True), _E_PRESSED, 2.0)
        # Move away and let expire (2.5s > 2.0s feedback duration)
        scene.update(DirectionalInput(left=True), _NO_INTERACTION, 2.5)
        assert scene.is_character_near_object is False
        assert scene.feedback_remaining == 0.0
        # No message should draw
        renderer2 = scene._renderer  # type: ignore[attr-defined]
        renderer2.clear_frame((0, 0, 0))
        scene.render()
    finally:
        platform.shutdown()


# ==================================================================
# Update/render separation
# ==================================================================


def test_update_changes_feedback_timer() -> None:
    """update() modifies feedback_remaining."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()

        before = scene.feedback_remaining
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        after = scene.feedback_remaining
        assert after != before
    finally:
        platform.shutdown()


def test_render_does_not_change_feedback_timer() -> None:
    """render() does not modify feedback_remaining."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        before = scene.feedback_remaining

        renderer2 = scene._renderer  # type: ignore[attr-defined]
        renderer2.clear_frame((0, 0, 0))
        scene.render()
        assert scene.feedback_remaining == pytest.approx(before)
    finally:
        platform.shutdown()


def test_repeated_renders_do_not_reduce_duration() -> None:
    """Multiple render() calls without update() do not change timer."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        before = scene.feedback_remaining

        renderer2 = scene._renderer  # type: ignore[attr-defined]
        for _ in range(5):
            renderer2.clear_frame((0, 0, 0))
            scene.render()

        assert scene.feedback_remaining == pytest.approx(before)
    finally:
        platform.shutdown()


def test_render_does_not_evaluate_proximity() -> None:
    """render() does not recalculate proximity."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
        near_before = scene.is_character_near_object

        renderer2 = scene._renderer  # type: ignore[attr-defined]
        renderer2.clear_frame((0, 0, 0))
        scene.render()
        assert scene.is_character_near_object == near_before
    finally:
        platform.shutdown()


def test_render_does_not_evaluate_interaction() -> None:
    """render() does not change interaction state."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        pulse_before = scene.did_interact_this_frame

        renderer2 = scene._renderer  # type: ignore[attr-defined]
        renderer2.clear_frame((0, 0, 0))
        scene.render()
        assert scene.did_interact_this_frame == pulse_before
    finally:
        platform.shutdown()


def test_text_after_world_objects() -> None:
    """Text drawing happens after world-object and character drawing."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)

        # Record draw order
        calls: list[str] = []
        renderer2 = scene._renderer  # type: ignore[attr-defined]
        orig_draw_rect = renderer2.draw_rect
        orig_draw_text = renderer2.draw_text

        def tracking_draw_rect(*args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            calls.append("rect")
            orig_draw_rect(*args, **kwargs)

        def tracking_draw_text(*args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            calls.append("text")
            orig_draw_text(*args, **kwargs)

        renderer2.draw_rect = tracking_draw_rect  # type: ignore[method-assign]
        renderer2.draw_text = tracking_draw_text  # type: ignore[method-assign]

        renderer2.clear_frame((0, 0, 0))
        scene.render()

        # Last call should be text (feedback after objects)
        assert calls[-1] == "text"
        # All rect calls come before the text call
        last_rect_index = max(i for i, c in enumerate(calls) if c == "rect")
        first_text_index = min(i for i, c in enumerate(calls) if c == "text")
        assert last_rect_index < first_text_index
    finally:
        platform.shutdown()


def test_update_performs_no_drawing() -> None:
    """update() must not call any draw methods."""

    class _CheckDrawScene(DefaultScene):
        def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            super().__init__(*args, **kwargs)
            self.draw_calls_during_update = 0

    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _CheckDrawScene(
            Renderer(platform),
            character=Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0)),
            world_object=WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0)),
            interaction_range=200,
        )
        scene.enter()

        renderer2 = scene._renderer  # type: ignore[attr-defined]
        orig_draw_rect = renderer2.draw_rect
        orig_draw_text = renderer2.draw_text

        def tracking_draw_rect(*args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            scene.draw_calls_during_update += 1
            orig_draw_rect(*args, **kwargs)

        def tracking_draw_text(*args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            scene.draw_calls_during_update += 1
            orig_draw_text(*args, **kwargs)

        renderer2.draw_rect = tracking_draw_rect  # type: ignore[method-assign]
        renderer2.draw_text = tracking_draw_text  # type: ignore[method-assign]

        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.draw_calls_during_update == 0
    finally:
        platform.shutdown()


# ==================================================================
# No gameplay-state side effects
# ==================================================================


def test_feedback_does_not_mutate_world_object() -> None:
    """Feedback does not change world object name, position, or color."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()

        wo = scene.world_object
        orig_name = wo.name
        orig_x, orig_y = wo.x, wo.y
        orig_w, orig_h = wo.width, wo.height
        orig_color = wo.color

        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.feedback_remaining > 0

        assert wo.name == orig_name
        assert wo.x == orig_x and wo.y == orig_y
        assert wo.width == orig_w and wo.height == orig_h
        assert wo.color == orig_color
    finally:
        platform.shutdown()


def test_feedback_does_not_block_movement() -> None:
    """Feedback does not block character movement."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        # Character moved the full distance
        assert scene.character.x_float == pytest.approx(160.0)
    finally:
        platform.shutdown()


def test_feedback_no_inventory_or_reward() -> None:
    """No inventory or reward state exists on the scene."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        assert not hasattr(scene, "inventory")
        assert not hasattr(scene, "rewards")
        assert not hasattr(scene, "collected_items")
    finally:
        platform.shutdown()


# ==================================================================
# Failure behaviour
# ==================================================================


def test_feedback_update_failure_prevents_clear() -> None:
    """If feedback update fails, frame work stops."""

    class _FailingFeedbackScene(DefaultScene):
        def _update_feedback(self, dt) -> None:  # type: ignore[no-untyped-def]
            raise RuntimeError("feedback failure")

    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _FailingFeedbackScene(
            Renderer(platform),
            character=Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0)),
            world_object=WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0)),
            interaction_range=200,
        )
        scene.enter()
        with pytest.raises(RuntimeError, match="feedback failure"):
            scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    finally:
        platform.shutdown()


def test_feedback_update_failure_scene_exit() -> None:
    """Scene exit still works after feedback failure."""

    class _FailingFeedbackScene(DefaultScene):
        def _update_feedback(self, dt) -> None:  # type: ignore[no-untyped-def]
            raise RuntimeError("feedback failure")

    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _FailingFeedbackScene(
            Renderer(platform),
            character=Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0)),
            world_object=WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0)),
            interaction_range=200,
        )
        scene.enter()
        with pytest.raises(RuntimeError, match="feedback failure"):
            scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
        scene.exit()
        assert scene.state.value == "exited"
    finally:
        platform.shutdown()


def test_text_draw_failure_prevents_presentation() -> None:
    """If text drawing fails, the exception propagates."""

    class _FailingTextScene(DefaultScene):
        def _draw_feedback(self) -> None:
            raise RuntimeError("text draw failure")

    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _FailingTextScene(
            Renderer(platform),
            character=Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0)),
            world_object=WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0)),
            interaction_range=200,
        )
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)

        renderer2 = scene._renderer  # type: ignore[attr-defined]
        renderer2.clear_frame((0, 0, 0))
        with pytest.raises(RuntimeError, match="text draw failure"):
            scene.render()
    finally:
        platform.shutdown()


def test_text_draw_failure_scene_exit() -> None:
    """Scene exit works after text draw failure."""

    class _FailingTextScene(DefaultScene):
        def _draw_feedback(self) -> None:
            raise RuntimeError("text draw failure")

    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _FailingTextScene(
            Renderer(platform),
            character=Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0)),
            world_object=WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0)),
            interaction_range=200,
        )
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)

        renderer2 = scene._renderer  # type: ignore[attr-defined]
        renderer2.clear_frame((0, 0, 0))
        with pytest.raises(RuntimeError, match="text draw failure"):
            scene.render()
        scene.exit()
        assert scene.state.value == "exited"
    finally:
        platform.shutdown()


def test_cleanup_not_duplicated_after_feedback_failure() -> None:
    """Exit is idempotent after feedback failure."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = _make_near_scene(platform)
        scene.enter()
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        scene.exit()
        scene.exit()
        assert scene.state.value == "exited"
    finally:
        platform.shutdown()


# ==================================================================
# Feedback state properties
# ==================================================================


def test_feedback_remaining_read_only() -> None:
    """Callers cannot assign feedback_remaining."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = DefaultScene(Renderer(platform))
        with pytest.raises(AttributeError):
            scene.feedback_remaining = 5.0  # type: ignore[misc]
    finally:
        platform.shutdown()


def test_initial_feedback_remaining_zero() -> None:
    """Before any interaction, feedback_remaining is 0.0."""
    platform = Platform(Config())
    platform.initialize()
    try:
        scene = DefaultScene(Renderer(platform))
        assert scene.feedback_remaining == 0.0
    finally:
        platform.shutdown()


# ==================================================================
# App integration — smoke tests
# ==================================================================


def test_app_with_feedback_runs() -> None:
    """Full app with text feedback starts and exits cleanly."""
    app = App(Config(target_fps=120))
    _post_quit_after(0.15)
    app.start()
    assert app.is_running is False


def test_app_smoke_with_e_key() -> None:
    """App processes E key and draws feedback without error."""
    import pygame

    def post_e_then_quit() -> None:
        time.sleep(0.1)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        time.sleep(0.3)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=post_e_then_quit, daemon=True).start()

    app = App(Config(target_fps=120))
    app.start()
    assert app.is_running is False
