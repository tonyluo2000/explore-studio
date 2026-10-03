"""Capture real S03 Classroom Trail runtime frames for visual review.

Drives the actual M03 Trail scene headlessly (``SDL_VIDEODRIVER=dummy``) with
the canonical S03 command's packages (Nova plus the S03 Moon Compass), real
directional input, a real ``E`` press, and fixed 60 FPS time steps, then saves
the 960 x 640 window after each scene render. Nothing is mocked or painted
afterwards.

    SDL_VIDEODRIVER=dummy python3 scripts/capture_s03_visual_proof.py OUTPUT_DIR

Only long-standing scene APIs are used, so ``--only before`` captures the same
idle frame from an older checkout placed first on ``PYTHONPATH``.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
S03_PACKAGES = (
    REPO / "examples/explorer-packages/nova-character",
    REPO / "lessons/sessions/s03/student/explorer-package",
)
STEP = 1 / 60


class Trail:
    """One real M03 Trail scene plus the platform that renders it."""

    def __init__(self) -> None:
        from engine._config import Config
        from engine._platform import Platform
        from engine.rendering import Renderer
        from explore.curriculum import MISSION_03_ID
        from explore.packages.classroom_trail import (
            create_classroom_trail_scene,
            plan_local_classroom_trail,
        )

        self.config = Config()
        self.platform = Platform(self.config)
        self.platform.initialize()
        self.renderer = Renderer(self.platform)
        planned = plan_local_classroom_trail(
            S03_PACKAGES, player_qualified_id="nova-character:nova"
        )
        assert planned.is_planned, planned.issues
        self.scene = create_classroom_trail_scene(
            self.renderer, planned.plan, mission_id=MISSION_03_ID
        )
        self.scene.enter()

    def step(self, *, left=False, right=False, up=False, down=False, interact=False) -> None:  # type: ignore[no-untyped-def]
        from engine.input import DirectionalInput, InteractionInput

        self.scene.update(
            DirectionalInput(left=left, right=right, up=up, down=down),
            InteractionInput(interact_pressed=interact),
            STEP,
        )
        self.platform.clear_frame(self.config.background_color)
        self.scene.render()

    def hold(self, seconds: float, **keys: bool) -> None:
        for _ in range(round(seconds / STEP)):
            self.step(**keys)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(pygame.display.get_surface(), str(path))
        print(f"wrote {path}")

    def close(self) -> None:
        self.scene.exit()
        self.platform.shutdown()


def _walk_to(trail: Trail, x: int, y: int) -> None:
    """Walk with real directional input until the player reaches (x, y)."""
    player = trail.scene.player
    for _ in range(600):
        dx, dy = x - player.x_float, y - player.y_float
        if abs(dx) < 3 and abs(dy) < 3:
            return
        trail.step(left=dx < -2, right=dx > 2, up=dy < -2, down=dy > 2)


def capture(out: Path, *, before: bool) -> None:
    trail = Trail()
    trail.hold(1.2)
    trail.save(out / ("before-idle.png" if before else "s03-idle.png"))
    _walk_to(trail, 250, 230)
    trail.hold(0.4)
    assert trail.scene.visited_count == 0
    trail.save(out / ("before-near.png" if before else "s03-near-clue.png"))
    trail.step(interact=True)
    trail.hold(0.35)
    assert trail.scene.visited_count == 1 and trail.scene.mission_is_complete
    trail.save(out / ("before-reveal.png" if before else "s03-reveal.png"))
    if not before:
        trail.hold(2.5)
        trail.save(out / "s03-complete.png")
    trail.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("output", type=Path)
    parser.add_argument("--only", choices=("before",))
    args = parser.parse_args(argv)
    capture(args.output, before=args.only == "before")
    return 0


if __name__ == "__main__":
    sys.exit(main())
