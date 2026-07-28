"""Verify scene lifecycle behavior.

All tests use a headless Pygame driver (SDL_VIDEODRIVER=dummy).
"""

from __future__ import annotations

import threading
import time

import pytest

from engine import App, Config
from engine._logging import init_logging
from engine._platform import Platform
from engine.input import DirectionalInput
from engine.rendering import Renderer
from engine.scenes import DefaultScene, Scene, SceneLifecycleError, SceneState

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
# Scene lifecycle — normal
# ==================================================================


def test_scene_starts_created() -> None:
    scene = Scene()
    assert scene.state == SceneState.CREATED
    assert scene.is_active is False


def test_scene_enter_succeeds() -> None:
    scene = Scene()
    scene.enter()
    assert scene.state == SceneState.ACTIVE


def test_scene_duplicate_enter_raises() -> None:
    scene = Scene()
    scene.enter()
    with pytest.raises(SceneLifecycleError, match="already active"):
        scene.enter()


def test_scene_exit_after_enter() -> None:
    scene = Scene()
    scene.enter()
    scene.exit()
    assert scene.state == SceneState.EXITED


def test_scene_enter_after_exit_raises() -> None:
    scene = Scene()
    scene.enter()
    scene.exit()
    with pytest.raises(SceneLifecycleError, match="exited"):
        scene.enter()


def test_scene_duplicate_exit_is_idempotent() -> None:
    scene = Scene()
    scene.enter()
    scene.exit()
    scene.exit()


def test_scene_exit_from_created() -> None:
    scene = Scene()
    scene.exit()
    assert scene.state == SceneState.EXITED


def test_scene_on_frame_only_when_active() -> None:
    scene = Scene()
    with pytest.raises(SceneLifecycleError, match="Cannot participate"):
        scene.on_frame(_NO_INPUT, 0.0)

    scene.enter()
    scene.on_frame(_NO_INPUT, 0.0)

    scene.exit()
    with pytest.raises(SceneLifecycleError, match="Cannot participate"):
        scene.on_frame(_NO_INPUT, 0.0)


def test_scene_ordering_enter_frame_exit() -> None:
    scene = Scene()
    scene.enter()
    scene.on_frame(_NO_INPUT, 0.0)
    scene.exit()
    assert scene.state == SceneState.EXITED


# ==================================================================
# DefaultScene
# ==================================================================


def test_default_scene_is_scene() -> None:
    from engine._platform import Platform

    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        scene = DefaultScene(renderer)
        assert isinstance(scene, Scene)
    finally:
        platform.shutdown()


def test_default_scene_on_frame_draws() -> None:
    platform = Platform(Config())
    platform.initialize()
    try:
        renderer = Renderer(platform)
        renderer.clear_frame((0, 0, 0))
        scene = DefaultScene(renderer)
        scene.enter()
        scene.on_frame(_NO_INPUT, 0.016)
        renderer.present_frame()
    finally:
        platform.shutdown()


# ==================================================================
# App integration — spy scene
# ==================================================================


class _SpyScene(Scene):
    def __init__(self) -> None:
        super().__init__()
        self.enter_calls = 0
        self.frame_calls = 0
        self.exit_calls = 0

    def enter(self) -> None:
        self.enter_calls += 1
        super().enter()

    def on_frame(self, input_state: DirectionalInput, dt: float) -> None:
        self.frame_calls += 1
        super().on_frame(input_state, dt)

    def exit(self) -> None:
        self.exit_calls += 1
        super().exit()


class _SpyApp(App):
    def __init__(self, scene: Scene, config: Config | None = None) -> None:
        super().__init__(config)
        self._injected_scene = scene

    def _create_scene(self) -> Scene:
        return self._injected_scene


def test_scene_enters_once_per_run() -> None:
    scene = _SpyScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.1)
    app.start()
    assert scene.enter_calls == 1


def test_scene_exits_once_per_run() -> None:
    scene = _SpyScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.1)
    app.start()
    assert scene.exit_calls == 1


def test_scene_frames_occur_in_loop() -> None:
    scene = _SpyScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.15)
    app.start()
    assert scene.frame_calls > 0


def test_scene_enter_before_frame() -> None:
    scene = _SpyScene()
    app = _SpyApp(scene, Config(target_fps=120))
    order: list[str] = []
    orig_enter = scene.enter
    orig_frame = scene.on_frame

    def tracking_enter() -> None:
        order.append("enter")
        orig_enter()

    def tracking_frame(input_state: DirectionalInput, dt: float) -> None:
        if "enter" not in order:
            order.append("frame-before-enter")
        else:
            order.append("frame")
        orig_frame(input_state, dt)

    scene.enter = tracking_enter  # type: ignore[method-assign]
    scene.on_frame = tracking_frame  # type: ignore[method-assign]

    _post_quit_after(0.1)
    app.start()
    assert "frame-before-enter" not in order
    assert order[0] == "enter"


def test_quit_before_any_frame_does_not_call_scene() -> None:
    import pygame

    scene = _SpyScene()
    app = _SpyApp(scene, Config(target_fps=120))

    def post_quit_immediately() -> None:
        time.sleep(0.05)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=post_quit_immediately, daemon=True).start()
    app.start()
    assert scene.enter_calls == 1
    assert scene.exit_calls == 1


def test_scene_exit_before_platform_shutdown() -> None:
    scene = _SpyScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.1)
    app.start()
    assert scene.enter_calls == 1
    assert scene.exit_calls == 1
    assert scene.state == SceneState.EXITED


# ==================================================================
# Failure: scene entry
# ==================================================================


class _FailingEnterScene(Scene):
    def enter(self) -> None:
        raise RuntimeError("entry failure")


def test_scene_entry_failure_triggers_platform_cleanup() -> None:
    scene = _FailingEnterScene()
    app = _SpyApp(scene, Config(target_fps=120))
    with pytest.raises(RuntimeError, match="entry failure"):
        app.start()
    assert app.is_running is False


def test_scene_entry_failure_preserves_exception() -> None:
    scene = _FailingEnterScene()
    app = _SpyApp(scene, Config(target_fps=120))
    with pytest.raises(RuntimeError, match="entry failure"):
        app.start()


# ==================================================================
# Failure: scene frame
# ==================================================================


class _FailingFrameScene(Scene):
    frame_call_count = 0

    def on_frame(self, input_state: DirectionalInput, dt: float) -> None:
        super().on_frame(input_state, dt)
        self.frame_call_count += 1
        if self.frame_call_count >= 2:
            raise RuntimeError("frame failure")


def test_scene_frame_failure_stops_loop() -> None:
    scene = _FailingFrameScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.5)
    with pytest.raises(RuntimeError, match="frame failure"):
        app.start()
    assert app.is_running is False


def test_scene_frame_failure_triggers_scene_exit() -> None:
    scene = _FailingFrameScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.5)
    with pytest.raises(RuntimeError, match="frame failure"):
        app.start()
    assert scene.state == SceneState.EXITED


# ==================================================================
# Failure: scene exit
# ==================================================================


class _FailingExitScene(Scene):
    def exit(self) -> None:
        raise RuntimeError("exit failure")


def test_scene_exit_failure_does_not_prevent_platform_cleanup() -> None:
    """If scene exit fails during normal shutdown, the failure is raised."""
    scene = _FailingExitScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.1)
    with pytest.raises(RuntimeError, match="exit failure"):
        app.start()
    assert app.is_running is False


class _FailingEnterAndExitScene(Scene):
    def enter(self) -> None:
        super().enter()

    def exit(self) -> None:
        raise RuntimeError("exit failure after ok enter")


def test_scene_exit_failure_preserved_when_no_earlier_error() -> None:
    """Exit failure during normal shutdown is raised and observable."""
    scene = _FailingEnterAndExitScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.1)
    with pytest.raises(RuntimeError, match="exit failure after ok enter"):
        app.start()


class _FailingFrameAndExitScene(Scene):
    frame_call_count = 0

    def on_frame(self, input_state: DirectionalInput, dt: float) -> None:
        super().on_frame(input_state, dt)
        self.frame_call_count += 1
        raise RuntimeError("frame failure first")

    def exit(self) -> None:
        raise RuntimeError("exit failure second")


def test_frame_failure_takes_precedence_over_exit_failure() -> None:
    scene = _FailingFrameAndExitScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.5)
    with pytest.raises(RuntimeError, match="frame failure first"):
        app.start()


def test_scene_imports_valid() -> None:
    from engine.scenes import DefaultScene, Scene, SceneLifecycleError, SceneState  # noqa: F401


def test_default_scene_integration_with_app() -> None:
    app = App(Config(target_fps=120))
    _post_quit_after(0.1)
    app.start()
    assert app.is_running is False
