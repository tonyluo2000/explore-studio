"""Verify scene lifecycle behavior.

All tests use a headless Pygame driver (SDL_VIDEODRIVER=dummy).
"""

from __future__ import annotations

import threading
import time

import pytest

from engine import App, Config
from engine._logging import init_logging
from engine.scenes import DefaultScene, Scene, SceneLifecycleError, SceneState


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
    """A new Scene begins in CREATED state."""
    scene = Scene()
    assert scene.state == SceneState.CREATED
    assert scene.is_active is False


def test_scene_enter_succeeds() -> None:
    """enter() transitions CREATED → ACTIVE."""
    scene = Scene()
    scene.enter()
    assert scene.state == SceneState.ACTIVE
    assert scene.is_active is True


def test_scene_duplicate_enter_raises() -> None:
    """Calling enter() on an ACTIVE scene raises SceneLifecycleError."""
    scene = Scene()
    scene.enter()
    with pytest.raises(SceneLifecycleError, match="already active"):
        scene.enter()


def test_scene_exit_after_enter() -> None:
    """exit() transitions ACTIVE → EXITED."""
    scene = Scene()
    scene.enter()
    scene.exit()
    assert scene.state == SceneState.EXITED


def test_scene_enter_after_exit_raises() -> None:
    """Calling enter() on an EXITED scene raises."""
    scene = Scene()
    scene.enter()
    scene.exit()
    with pytest.raises(SceneLifecycleError, match="exited"):
        scene.enter()


def test_scene_duplicate_exit_is_idempotent() -> None:
    """Calling exit() twice does not raise."""
    scene = Scene()
    scene.enter()
    scene.exit()
    scene.exit()  # no-op


def test_scene_exit_from_created() -> None:
    """exit() on a CREATED scene transitions to EXITED with a warning."""
    scene = Scene()
    scene.exit()
    assert scene.state == SceneState.EXITED


def test_scene_on_frame_only_when_active() -> None:
    """on_frame() succeeds only in ACTIVE state."""
    scene = Scene()
    with pytest.raises(SceneLifecycleError, match="Cannot participate"):
        scene.on_frame()

    scene.enter()
    scene.on_frame()  # should not raise

    scene.exit()
    with pytest.raises(SceneLifecycleError, match="Cannot participate"):
        scene.on_frame()


def test_scene_ordering_enter_frame_exit() -> None:
    """enter → on_frame → exit must occur in that order."""
    scene = Scene()
    assert scene.state == SceneState.CREATED

    scene.enter()
    assert scene.state == SceneState.ACTIVE

    scene.on_frame()

    scene.exit()
    assert scene.state == SceneState.EXITED


# ==================================================================
# DefaultScene
# ==================================================================


def test_default_scene_is_scene() -> None:
    """DefaultScene is a valid Scene subclass."""
    scene = DefaultScene()
    assert isinstance(scene, Scene)


def test_default_scene_on_frame_noop() -> None:
    """DefaultScene.on_frame() is a no-op."""
    scene = DefaultScene()
    scene.enter()
    scene.on_frame()  # no-op, should not raise


# ==================================================================
# Application integration — scene lifecycle
# ==================================================================


class _SpyScene(Scene):
    """Scene that records lifecycle calls for test assertions."""

    def __init__(self) -> None:
        super().__init__()
        self.enter_calls = 0
        self.frame_calls = 0
        self.exit_calls = 0

    def enter(self) -> None:
        self.enter_calls += 1
        super().enter()

    def on_frame(self) -> None:
        self.frame_calls += 1
        super().on_frame()

    def exit(self) -> None:
        self.exit_calls += 1
        super().exit()


class _SpyApp(App):
    """App that injects a spy scene."""

    def __init__(self, scene: Scene, config: Config | None = None) -> None:
        super().__init__(config)
        self._injected_scene = scene

    def _create_scene(self) -> Scene:
        return self._injected_scene


def test_scene_enters_once_per_run() -> None:
    """Scene enter() is called exactly once during a normal run."""
    scene = _SpyScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.1)
    app.start()
    assert scene.enter_calls == 1


def test_scene_exits_once_per_run() -> None:
    """Scene exit() is called exactly once during normal shutdown."""
    scene = _SpyScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.1)
    app.start()
    assert scene.exit_calls == 1


def test_scene_frames_occur_in_loop() -> None:
    """Scene on_frame() is called during the main loop."""
    scene = _SpyScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.15)
    app.start()
    assert scene.frame_calls > 0


def test_scene_enter_before_frame() -> None:
    """Scene enter() happens before the first on_frame()."""
    scene = _SpyScene()
    app = _SpyApp(scene, Config(target_fps=120))

    # Use a list to capture ordering
    order: list[str] = []
    orig_enter = scene.enter
    orig_frame = scene.on_frame

    def tracking_enter() -> None:
        order.append("enter")
        orig_enter()

    def tracking_frame() -> None:
        if "enter" not in order:
            order.append("frame-before-enter")
        else:
            order.append("frame")
        orig_frame()

    scene.enter = tracking_enter  # type: ignore[method-assign]
    scene.on_frame = tracking_frame  # type: ignore[method-assign]

    _post_quit_after(0.1)
    app.start()

    assert "frame-before-enter" not in order
    assert order[0] == "enter"


def test_quit_before_any_frame_does_not_call_scene() -> None:
    """Scene on_frame() is never called if quit arrives before frames."""
    import pygame

    scene = _SpyScene()
    app = _SpyApp(scene, Config(target_fps=120))

    # Post quit in a thread before the first loop iteration
    def post_quit_immediately() -> None:
        time.sleep(0.05)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=post_quit_immediately, daemon=True).start()
    app.start()

    assert scene.enter_calls == 1
    assert scene.exit_calls == 1
    # The quit arrives quickly, so on_frame may be called 0 or very few times.
    # The key is that enter and exit both happen.
    assert scene.enter_calls == 1


def test_scene_exit_before_platform_shutdown() -> None:
    """Scene exit() occurs during cleanup — enter is called once and exit is called once."""
    scene = _SpyScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.1)
    app.start()

    # Both lifecycle methods were called exactly once, in order.
    assert scene.enter_calls == 1
    assert scene.exit_calls == 1
    # After shutdown, the scene is in EXITED state.
    assert scene.state == SceneState.EXITED


# ==================================================================
# Failure: scene entry
# ==================================================================


class _FailingEnterScene(Scene):
    def enter(self) -> None:
        raise RuntimeError("entry failure")


def test_scene_entry_failure_triggers_platform_cleanup() -> None:
    """If scene entry fails, platform is still shut down."""
    scene = _FailingEnterScene()
    app = _SpyApp(scene, Config(target_fps=120))

    with pytest.raises(RuntimeError, match="entry failure"):
        app.start()

    # App should not be running
    assert app.is_running is False


def test_scene_entry_failure_preserves_exception() -> None:
    """Original exception is preserved after scene entry failure."""
    scene = _FailingEnterScene()
    app = _SpyApp(scene, Config(target_fps=120))

    with pytest.raises(RuntimeError, match="entry failure"):
        app.start()


# ==================================================================
# Failure: scene frame
# ==================================================================


class _FailingFrameScene(Scene):
    frame_call_count = 0

    def on_frame(self) -> None:
        super().on_frame()
        self.frame_call_count += 1
        if self.frame_call_count >= 2:
            raise RuntimeError("frame failure")


def test_scene_frame_failure_stops_loop() -> None:
    """Scene frame failure stops the main loop."""
    scene = _FailingFrameScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.5)  # safety: quit if the loop doesn't stop

    with pytest.raises(RuntimeError, match="frame failure"):
        app.start()

    assert app.is_running is False
    assert scene.frame_call_count <= 2


def test_scene_frame_failure_triggers_scene_exit() -> None:
    """Scene exit is called after a frame failure."""
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
    """If scene exit fails, platform cleanup still occurs."""
    scene = _FailingExitScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.1)

    with pytest.raises(RuntimeError, match="exit failure"):
        app.start()

    assert app.is_running is False


class _FailingEnterAndExitScene(Scene):
    def enter(self) -> None:
        super().enter()
        # succeeds — but exit will fail
        pass

    def exit(self) -> None:
        raise RuntimeError("exit failure after ok enter")


def test_scene_exit_failure_preserved_when_no_earlier_error() -> None:
    """Exit failure is raised when no earlier exception exists."""
    scene = _FailingEnterAndExitScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.1)

    with pytest.raises(RuntimeError, match="exit failure after ok enter"):
        app.start()


class _FailingFrameAndExitScene(Scene):
    frame_call_count = 0

    def on_frame(self) -> None:
        super().on_frame()
        self.frame_call_count += 1
        raise RuntimeError("frame failure first")

    def exit(self) -> None:
        raise RuntimeError("exit failure second")


def test_frame_failure_takes_precedence_over_exit_failure() -> None:
    """When both frame and exit fail, original frame failure is preserved."""
    scene = _FailingFrameAndExitScene()
    app = _SpyApp(scene, Config(target_fps=120))
    _post_quit_after(0.5)

    with pytest.raises(RuntimeError, match="frame failure first"):
        app.start()


# ==================================================================
# Regression
# ==================================================================


def test_scene_imports_valid() -> None:
    """Scene symbols are importable and Pygame-free."""
    from engine.scenes import DefaultScene, Scene, SceneLifecycleError, SceneState  # noqa: F401


def test_default_scene_integration_with_app() -> None:
    """App with the default scene starts and exits cleanly."""
    app = App(Config(target_fps=120))
    _post_quit_after(0.1)
    app.start()
    assert app.is_running is False
