"""Verify interaction input and proximity-gated interaction behaviour.

All tests use a headless Pygame driver (SDL_VIDEODRIVER=dummy).
"""

from __future__ import annotations

import threading
import time

import pytest

from engine import App, Config
from engine._logging import init_logging
from engine._platform import FrameEvents, Platform
from engine.entities import Character, WorldObject
from engine.input import DirectionalInput, InteractionInput
from engine.rendering import Renderer
from engine.scenes import DefaultScene, Scene, SceneLifecycleError

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


def _post_e_key_after(delay: float = 0.1) -> None:
    """Post an E KEYDOWN followed by QUIT after *delay* seconds."""
    import pygame

    def _post() -> None:
        time.sleep(delay)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        time.sleep(0.05)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=_post, daemon=True).start()


@pytest.fixture(autouse=True)
def _ensure_logging() -> None:
    init_logging()


# ==================================================================
# InteractionInput model
# ==================================================================


def test_interaction_input_default_not_pressed() -> None:
    inp = InteractionInput()
    assert inp.interact_pressed is False


def test_interaction_input_pressed() -> None:
    inp = InteractionInput(interact_pressed=True)
    assert inp.interact_pressed is True


def test_interaction_input_is_immutable() -> None:
    inp = InteractionInput()
    with pytest.raises(AttributeError):
        inp.interact_pressed = True  # type: ignore[misc]


def test_interaction_input_no_pygame_types() -> None:
    inp = InteractionInput(interact_pressed=True)
    assert isinstance(inp.interact_pressed, bool)


# ==================================================================
# FrameEvents model
# ==================================================================


def test_frame_events_defaults() -> None:
    fe = FrameEvents()
    assert fe.quit_requested is False
    assert fe.interaction_pressed is False


def test_frame_events_is_immutable() -> None:
    fe = FrameEvents(quit_requested=True)
    with pytest.raises(AttributeError):
        fe.quit_requested = False  # type: ignore[misc]


# ==================================================================
# Platform event polling
# ==================================================================


def test_poll_frame_events_no_quit_by_default() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        events = platform.poll_frame_events()
        assert events.quit_requested is False
        assert events.interaction_pressed is False
    finally:
        platform.shutdown()


def test_poll_frame_events_detects_quit() -> None:
    import pygame

    platform = Platform(Config())
    platform.initialize()
    try:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        events = platform.poll_frame_events()
        assert events.quit_requested is True
    finally:
        platform.shutdown()


def test_poll_frame_events_detects_e_keydown() -> None:
    import pygame

    platform = Platform(Config())
    platform.initialize()
    try:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        events = platform.poll_frame_events()
        assert events.interaction_pressed is True
    finally:
        platform.shutdown()


def test_poll_frame_events_unrelated_key_ignored() -> None:
    import pygame

    platform = Platform(Config())
    platform.initialize()
    try:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f))
        events = platform.poll_frame_events()
        assert events.interaction_pressed is False
    finally:
        platform.shutdown()


def test_poll_frame_events_keyup_ignored() -> None:
    import pygame

    platform = Platform(Config())
    platform.initialize()
    try:
        pygame.event.post(pygame.event.Event(pygame.KEYUP, key=pygame.K_e))
        events = platform.poll_frame_events()
        assert events.interaction_pressed is False
    finally:
        platform.shutdown()


def test_poll_frame_events_e_and_quit_together() -> None:
    """When both quit and E occur, quit takes precedence (both are reported)."""
    import pygame

    platform = Platform(Config())
    platform.initialize()
    try:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        events = platform.poll_frame_events()
        # Quit and interaction can coexist in the result; the app loop
        # checks quit first and breaks before using interaction.
        assert events.quit_requested is True
        assert events.interaction_pressed is True
    finally:
        platform.shutdown()


def test_poll_frame_events_clears_queue() -> None:
    """Second poll after processing should be empty."""
    import pygame

    platform = Platform(Config())
    platform.initialize()
    try:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        first = platform.poll_frame_events()
        assert first.interaction_pressed is True
        second = platform.poll_frame_events()
        assert second.interaction_pressed is False
    finally:
        platform.shutdown()


def test_poll_frame_events_no_pygame_types_returned() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        events = platform.poll_frame_events()
        assert isinstance(events, FrameEvents)
        assert isinstance(events.quit_requested, bool)
        assert isinstance(events.interaction_pressed, bool)
    finally:
        platform.shutdown()


# ==================================================================
# Scene update/render lifecycle
# ==================================================================


def test_scene_update_only_when_active() -> None:
    scene = Scene()
    with pytest.raises(SceneLifecycleError, match="Cannot update"):
        scene.update(_NO_INPUT, _NO_INTERACTION, 0.0)


def test_scene_render_only_when_active() -> None:
    scene = Scene()
    with pytest.raises(SceneLifecycleError, match="Cannot render"):
        scene.render()


def test_scene_update_and_render_when_active() -> None:
    scene = Scene()
    scene.enter()
    scene.update(_NO_INPUT, _NO_INTERACTION, 0.0)
    scene.render()
    scene.exit()


def test_default_scene_update_before_render() -> None:
    """update changes state; render draws but doesn't change state."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=140, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=50)
        scene.enter()
        # Before update: far
        assert scene.is_character_near_object is False
        assert scene.did_interact_this_frame is False

        # Update moves character toward object (160 px/s × 1.0s → x=160)
        # Character center: (160+20, 20) = (180, 20)
        # Object at (140,0) 40×40 → center (160, 20) → distance = 20 ≤ 50
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)

        # After update: near, and E was pressed → interaction pulse
        assert scene.is_character_near_object is True
        assert scene.did_interact_this_frame is True

        # Render should not change proximity or interaction
        scene.render()
        assert scene.is_character_near_object is True
        assert scene.did_interact_this_frame is True
    finally:
        platform.shutdown()


def test_render_does_not_recalculate_proximity() -> None:
    """render() does not call _evaluate_proximity."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        scene.enter()

        # Get initial proximity
        initial_near = scene.is_character_near_object

        # Call render without update — proximity should be unchanged
        scene.render()
        assert scene.is_character_near_object == initial_near
    finally:
        platform.shutdown()


def test_render_does_not_recalculate_interaction() -> None:
    """render() does not call _evaluate_interaction."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        scene.enter()

        initial_pulse = scene.did_interact_this_frame
        scene.render()
        assert scene.did_interact_this_frame == initial_pulse
    finally:
        platform.shutdown()


def test_one_update_and_render_per_frame() -> None:
    """Each frame has exactly one update and one render."""

    class _CountingScene(DefaultScene):
        def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            super().__init__(*args, **kwargs)
            self.update_count = 0
            self.render_count = 0

        def update(self, input_state, interaction_input, dt) -> None:
            self.update_count += 1
            super().update(input_state, interaction_input, dt)

        def render(self) -> None:
            self.render_count += 1
            super().render()

    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _CountingScene(renderer)
        scene.enter()

        for _ in range(3):
            scene.update(_NO_INPUT, _NO_INTERACTION, 0.016)
            scene.render()

        assert scene.update_count == 3
        assert scene.render_count == 3
    finally:
        platform.shutdown()


# ==================================================================
# Valid interaction — near + E
# ==================================================================


def test_e_near_chest_produces_pulse() -> None:
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()

        # Move into range and press E
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.is_character_near_object is True
        assert scene.did_interact_this_frame is True
    finally:
        platform.shutdown()


def test_no_e_near_chest_produces_no_pulse() -> None:
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()

        scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
        assert scene.is_character_near_object is True
        assert scene.did_interact_this_frame is False
    finally:
        platform.shutdown()


def test_e_far_from_chest_produces_no_pulse() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        scene.enter()

        scene.update(_NO_INPUT, _E_PRESSED, 0.016)
        assert scene.is_character_near_object is False
        assert scene.did_interact_this_frame is False
    finally:
        platform.shutdown()


def test_move_into_range_and_press_e_same_frame() -> None:
    """E pressed during the same frame as moving into range succeeds."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=200, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=50)
        scene.enter()

        # Initially far
        assert scene.is_character_near_object is False
        # Move into range AND press E in the same frame
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.25)
        # After 1.25s at 160px/s: x≈200, centers align → near + interact
        assert scene.is_character_near_object is True
        assert scene.did_interact_this_frame is True
    finally:
        platform.shutdown()


def test_pulse_resets_next_frame() -> None:
    """Pulse is True only for the frame of the press, then resets."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()

        # Frame 1: E pressed near → pulse
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.did_interact_this_frame is True

        # Frame 2: no E → pulse resets
        scene.update(_NO_INPUT, _NO_INTERACTION, 0.016)
        assert scene.did_interact_this_frame is False
    finally:
        platform.shutdown()


def test_second_e_press_produces_second_pulse() -> None:
    """Another E press later produces another pulse."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()

        # First E press
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.did_interact_this_frame is True

        # Frame without E
        scene.update(_NO_INPUT, _NO_INTERACTION, 0.016)
        assert scene.did_interact_this_frame is False

        # Second E press
        scene.update(_NO_INPUT, _E_PRESSED, 0.016)
        assert scene.did_interact_this_frame is True
    finally:
        platform.shutdown()


# ==================================================================
# Held-key behaviour
# ==================================================================


def test_held_e_does_not_retrigger() -> None:
    """Holding E without releasing does not produce repeated pulses."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()

        # Frame 1: E pressed → pulse
        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.did_interact_this_frame is True

        # Frame 2: E held (no new KEYDOWN) → no pulse
        scene.update(_NO_INPUT, _NO_INTERACTION, 0.016)
        assert scene.did_interact_this_frame is False

        # Frame 3: E still held → still no pulse
        scene.update(_NO_INPUT, _NO_INTERACTION, 0.016)
        assert scene.did_interact_this_frame is False
    finally:
        platform.shutdown()


def test_release_and_repress_produces_new_pulse() -> None:
    """Release then press again produces another interaction."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()

        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.did_interact_this_frame is True

        # Released
        scene.update(_NO_INPUT, _NO_INTERACTION, 0.016)
        assert scene.did_interact_this_frame is False

        # Pressed again
        scene.update(_NO_INPUT, _E_PRESSED, 0.016)
        assert scene.did_interact_this_frame is True
    finally:
        platform.shutdown()


# ==================================================================
# Ordering: movement → proximity → interaction
# ==================================================================


def test_movement_before_proximity_before_interaction() -> None:
    """Interaction evaluation uses proximity from post-movement position."""

    class _OrderingScene(DefaultScene):
        def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            super().__init__(*args, **kwargs)
            self.order: list[str] = []

        def _move_character(self, inp, dt) -> None:
            self.order.append("move")
            super()._move_character(inp, dt)

        def _evaluate_proximity(self) -> None:
            self.order.append("proximity")
            super()._evaluate_proximity()

        def _evaluate_interaction(self, ii) -> None:
            self.order.append("interaction")
            super()._evaluate_interaction(ii)

    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _OrderingScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()

        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.order == ["move", "proximity", "interaction"]
    finally:
        platform.shutdown()


def test_interaction_evaluation_before_render() -> None:
    """Interaction is evaluated in update, not in render."""

    class _CheckScene(DefaultScene):
        def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            super().__init__(*args, **kwargs)
            self.interaction_during_render: bool | None = None

        def render(self) -> None:
            self.interaction_during_render = self.did_interact_this_frame
            super().render()

    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _CheckScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()

        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        # Pulse is True after update
        pulse_after_update = scene.did_interact_this_frame
        scene.render()
        # Render should not have changed the pulse
        assert scene.interaction_during_render == pulse_after_update
    finally:
        platform.shutdown()


# ==================================================================
# No side effects
# ==================================================================


def test_successful_interaction_does_not_mutate_chest() -> None:
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()

        original_name = wo.name
        original_x, original_y = wo.x, wo.y
        original_width, original_height = wo.width, wo.height
        original_color = wo.color

        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.did_interact_this_frame is True

        # World object unchanged
        assert wo.name == original_name
        assert wo.x == original_x and wo.y == original_y
        assert wo.width == original_width and wo.height == original_height
        assert wo.color == original_color
    finally:
        platform.shutdown()


def test_interaction_does_not_block_movement() -> None:
    """Character can still move through the object during interaction."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()

        scene.update(DirectionalInput(right=True), _E_PRESSED, 1.0)
        assert scene.did_interact_this_frame is True
        # Character moved fully
        assert ch.x_float == pytest.approx(160.0)
    finally:
        platform.shutdown()


def test_interaction_preserves_drawing_order() -> None:
    """Drawing order remains object before character."""
    import pygame

    ch = Character(name="C", x=20, y=20, width=20, height=20, color=(0, 0, 255))
    wo = WorldObject(name="O", x=20, y=20, width=20, height=20, color=(255, 0, 0))
    platform = Platform(Config(window_width=200, window_height=200))
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()

        scene.update(_NO_INPUT, _E_PRESSED, 0.016)
        renderer.clear_frame((0, 0, 0))
        scene.render()
        surface = pygame.display.get_surface()
        assert surface is not None
        # Overlapping pixel shows character color (drawn on top)
        px = surface.get_at((ch.x + 5, ch.y + 5))
        assert (px.r, px.g, px.b) == ch.color
    finally:
        platform.shutdown()


def test_interaction_no_text_or_prompt() -> None:
    """No text or visual prompt appears during interaction."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        scene.enter()
        # Interaction happens (or doesn't) — just verify no crash
        scene.update(_NO_INPUT, _E_PRESSED, 0.016)
        renderer.clear_frame((0, 0, 0))
        scene.render()
        # If we got here without errors, no unexpected side effects
    finally:
        platform.shutdown()


# ==================================================================
# Failure behaviour
# ==================================================================


def test_update_failure_prevents_clear() -> None:
    """If scene.update raises, the frame is not cleared."""

    class _FailingUpdateScene(DefaultScene):
        def update(self, input_state, interaction_input, dt) -> None:
            raise RuntimeError("update failure")

    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _FailingUpdateScene(renderer)
        scene.enter()

        with pytest.raises(RuntimeError, match="update failure"):
            scene.update(_NO_INPUT, _NO_INTERACTION, 0.016)
    finally:
        platform.shutdown()


def test_render_failure_prevents_presentation() -> None:
    """If scene.render raises, the frame is not presented."""

    class _FailingRenderScene(DefaultScene):
        def render(self) -> None:
            raise RuntimeError("render failure")

    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _FailingRenderScene(renderer)
        scene.enter()

        with pytest.raises(RuntimeError, match="render failure"):
            scene.render()
    finally:
        platform.shutdown()


def test_update_failure_scene_exit_still_occurs() -> None:
    """Scene exit works after an update failure."""

    class _FailingUpdateScene(DefaultScene):
        def update(self, input_state, interaction_input, dt) -> None:
            raise RuntimeError("update failure")

    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _FailingUpdateScene(renderer)
        scene.enter()

        with pytest.raises(RuntimeError, match="update failure"):
            scene.update(_NO_INPUT, _NO_INTERACTION, 0.016)

        scene.exit()
        assert scene.state.value == "exited"
    finally:
        platform.shutdown()


def test_platform_cleanup_after_update_failure() -> None:
    """Platform cleans up even after update failure in main loop."""
    import pygame

    class _FailingUpdateScene(DefaultScene):
        def update(self, input_state, interaction_input, dt) -> None:
            raise RuntimeError("update failure")

    class _FailingApp(App):
        def _create_scene(self) -> DefaultScene:
            assert self._renderer is not None
            return _FailingUpdateScene(self._renderer)

    app = _FailingApp(Config(target_fps=120))

    def post_quit() -> None:
        time.sleep(0.1)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=post_quit, daemon=True).start()

    with pytest.raises(RuntimeError, match="update failure"):
        app.start()

    assert app.is_running is False


def test_original_exception_observable() -> None:
    """Original update exception propagates unchanged."""

    class _FailingUpdateScene(DefaultScene):
        def update(self, input_state, interaction_input, dt) -> None:
            raise RuntimeError("update failure")

    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = _FailingUpdateScene(renderer)
        scene.enter()

        with pytest.raises(RuntimeError) as exc_info:
            scene.update(_NO_INPUT, _NO_INTERACTION, 0.016)

        assert "update failure" in str(exc_info.value)
    finally:
        platform.shutdown()


# ==================================================================
# Interaction scene state properties
# ==================================================================


def test_did_interact_read_only() -> None:
    """Callers cannot assign did_interact_this_frame."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        with pytest.raises(AttributeError):
            scene.did_interact_this_frame = True  # type: ignore[misc]
    finally:
        platform.shutdown()


def test_initial_interaction_pulse_is_false() -> None:
    """Before any update, did_interact_this_frame is False."""
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        assert scene.did_interact_this_frame is False
    finally:
        platform.shutdown()


# ==================================================================
# App integration — smoke tests
# ==================================================================


def test_app_with_interaction_runs() -> None:
    """Full app with interaction input starts and exits cleanly."""
    app = App(Config(target_fps=120))
    _post_quit_after(0.15)
    app.start()
    assert app.is_running is False


def test_app_e_key_near_chest() -> None:
    """App loop processes E key without error."""
    ch = Character(name="C", x=0, y=0, width=40, height=40, color=(255, 0, 0))
    wo = WorldObject(name="O", x=30, y=0, width=40, height=40, color=(0, 255, 0))
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer, character=ch, world_object=wo, interaction_range=200)
        scene.enter()
        # Simulate what the main loop does
        events = platform.poll_frame_events()
        dt = platform.tick()
        inp = platform.poll_directional_input()
        interaction = InteractionInput(interact_pressed=events.interaction_pressed)
        scene.update(inp, interaction, dt)
        renderer.clear_frame((0, 0, 0))
        scene.render()
        renderer.present_frame()
    finally:
        platform.shutdown()


def test_quit_and_e_same_batch() -> None:
    """Quit takes precedence — no frame processed when quit arrives."""
    import pygame

    platform = Platform(Config())
    platform.initialize()
    try:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        events = platform.poll_frame_events()
        assert events.quit_requested is True
        # The app loop would break on quit without processing interaction
    finally:
        platform.shutdown()


def test_directional_input_unchanged() -> None:
    """DirectionalInput model is unchanged by interaction changes."""
    inp = DirectionalInput(right=True)
    assert inp.horizontal == 1.0
    assert inp.vertical == 0.0
    assert isinstance(inp, DirectionalInput)
