"""One real Classroom Trail scene, driven headlessly for captures.

Shared by the Journey snapshot harness (``scripts/capture_journey_snapshots.py``)
and the per-session review captures (``scripts/capture_s0*_visual_proof.py``).
It drives the actual Trail scene with real directional input, real ``E``
presses, and fixed 60 FPS time steps, rendering the 960 x 640 window after
every update exactly as ``explore-package trail`` does. Nothing is mocked or
painted afterwards.

The scene is created without an audio manager, which is what
``EXPLORE_STUDIO_AUDIO=off`` gives a student: gameplay and every frame are
identical except that no audio indicator is drawn.

Only long-standing scene APIs are used, so the proof scripts can still capture
BEFORE frames from an older checkout placed first on ``PYTHONPATH``.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

STEP = 1 / 60
NOVA = "nova-character:nova"


class RecordingRenderer:
    """Delegates every call to the real renderer and notes what one frame drew.

    Only observes: the pixels on screen come from the real renderer, and every
    other attribute (``hasattr`` checks included) resolves to it unchanged.
    """

    def __init__(self, renderer: object) -> None:
        self._renderer = renderer
        self.texts: list[str] = []
        #: (asset id, x, y, width, height, drawn) for every trusted sprite request.
        self.sprites: list[tuple[str, int, int, int, int, bool]] = []

    def reset(self) -> None:
        self.texts = []
        self.sprites = []

    def __getattr__(self, name: str) -> object:
        # Wrapped lazily, so a renderer without a method still lacks it here.
        attribute = getattr(self._renderer, name)
        if name == "draw_text":

            def draw_text(text, x, y, color, font_size):  # type: ignore[no-untyped-def]
                self.texts.append(text)
                return attribute(text, x, y, color, font_size)

            return draw_text
        if name == "draw_sprite_frame":

            def draw_sprite_frame(asset_id, row, column, x, y, width, height, **options):  # type: ignore[no-untyped-def]
                drawn = attribute(asset_id, row, column, x, y, width, height, **options)
                self.sprites.append((asset_id, x, y, width, height, bool(drawn)))
                return drawn

            return draw_sprite_frame
        return attribute


class Trail:
    """One real Trail scene plus the platform that renders it."""

    def __init__(
        self,
        package_roots: Sequence[Path],
        *,
        mission_id: str,
        player: str = NOVA,
    ) -> None:
        from engine._config import Config
        from engine._platform import Platform
        from engine.rendering import Renderer
        from explore.packages.classroom_trail import (
            create_classroom_trail_scene,
            plan_local_classroom_trail,
        )

        self.config = Config()
        self.platform = Platform(self.config)
        self.platform.initialize()
        self.renderer = RecordingRenderer(Renderer(self.platform))
        planned = plan_local_classroom_trail(tuple(package_roots), player_qualified_id=player)
        assert planned.is_planned, planned.issues
        self.scene = create_classroom_trail_scene(
            self.renderer, planned.plan, mission_id=mission_id
        )
        self.scene.enter()
        self.frames: list[pygame.Surface] = []
        self.record = False

    def step(self, *, left=False, right=False, up=False, down=False, interact=False) -> None:  # type: ignore[no-untyped-def]
        from engine.input import DirectionalInput, InteractionInput

        self.scene.update(
            DirectionalInput(left=left, right=right, up=up, down=down),
            InteractionInput(interact_pressed=interact),
            STEP,
        )
        self.renderer.reset()
        self.platform.clear_frame(self.config.background_color)
        self.scene.render()
        if self.record:
            self.frames.append(self.surface())

    def hold(self, seconds: float, **keys: bool) -> None:
        for _ in range(round(seconds / STEP)):
            self.step(**keys)

    def press(self) -> None:
        self.step(interact=True)

    def walk_to(self, x: int, y: int) -> None:
        """Walk with real directional input until the player reaches (x, y)."""
        player = self.scene.player
        for _ in range(600):
            dx, dy = x - player.x_float, y - player.y_float
            if abs(dx) < 3 and abs(dy) < 3:
                return
            self.step(left=dx < -2, right=dx > 2, up=dy < -2, down=dy > 2)
        raise AssertionError(f"the player never reached ({x}, {y})")

    def surface(self) -> pygame.Surface:
        return pygame.display.get_surface().copy()

    def save(self, path: Path) -> None:
        save_surface(pygame.display.get_surface(), path)

    def close(self) -> None:
        self.scene.exit()
        self.platform.shutdown()


def save_surface(surface: pygame.Surface, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(path))
    print(f"wrote {path}")


def half_scale(surface: pygame.Surface) -> pygame.Surface:
    """A smooth 480 x 320 downscale, approximating a Zoom screen share."""
    return pygame.transform.smoothscale(surface, (480, 320))
