"""Capture real S02 Classroom Trail runtime frames for visual review.

Drives the actual Trail scene headlessly (``SDL_VIDEODRIVER=dummy``) with the
reviewed S02 packages, real directional input, real ``E`` presses, and fixed
60 FPS time steps, then saves the 960 x 640 window after each scene render.
Nothing is mocked or painted afterwards; the half-scale image is a smooth
downscale of a captured frame, approximating a Zoom screen share.

    SDL_VIDEODRIVER=dummy python3 scripts/capture_s02_visual_proof.py OUTPUT_DIR

Only long-standing scene APIs are used, so the same script also captures a
BEFORE frame from an older checkout placed first on ``PYTHONPATH`` with
``--only before``.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
S02_PACKAGES = (
    REPO / "examples/explorer-packages/nova-character",
    REPO / "examples/explorer-packages/pixel-companion",
    REPO / "examples/explorer-packages/crystal-lantern",
    REPO / "lessons/sessions/s02/student/explorer-package",
)
STEP = 1 / 60


class Trail:
    """One real Trail scene plus the platform that renders it."""

    def __init__(self, package_roots: tuple[Path, ...] = S02_PACKAGES) -> None:
        from engine._config import Config
        from engine._platform import Platform
        from engine.rendering import Renderer
        from explore.curriculum import MISSION_02_ID
        from explore.packages.classroom_trail import (
            create_classroom_trail_scene,
            plan_local_classroom_trail,
        )

        self.config = Config()
        self.platform = Platform(self.config)
        self.platform.initialize()
        self.renderer = Renderer(self.platform)
        planned = plan_local_classroom_trail(
            package_roots, player_qualified_id="nova-character:nova"
        )
        assert planned.is_planned, planned.issues
        self.scene = create_classroom_trail_scene(
            self.renderer, planned.plan, mission_id=MISSION_02_ID
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
        self.platform.clear_frame(self.config.background_color)
        self.scene.render()
        if self.record:
            self.frames.append(pygame.display.get_surface().copy())

    def hold(self, seconds: float, **keys: bool) -> None:
        for _ in range(round(seconds / STEP)):
            self.step(**keys)

    def press(self) -> None:
        self.step(interact=True)

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


def capture_before(out: Path) -> None:
    trail = Trail()
    trail.hold(0.5)
    trail.save(out / "before.png")
    trail.close()


def capture_all(out: Path, gif_frames: dict[str, list[pygame.Surface]]) -> None:
    trail = Trail()
    trail.hold(1.2)
    trail.save(out / "nova-idle.png")
    trail.hold(3.8)
    trail.save(out / "living-world-idle-5s.png")
    trail.hold(0.5)
    trail.save(out / "living-world-idle-5.5s.png")
    trail.close()

    # Pixel greeting: Nova starts within range of Pixel; press E.
    trail = Trail()
    trail.hold(0.6)
    trail.press()
    trail.hold(0.5)
    trail.save(out / "pixel-greeting.png")
    trail.close()

    # Walking, one frame per facing, then the Compass and Lantern.
    trail = Trail()
    trail.hold(0.3)
    trail.hold(0.42, right=True)
    trail.save(out / "nova-walking-right.png")
    trail.hold(0.36, left=True)
    trail.save(out / "nova-walking-left.png")
    trail.hold(0.32, down=True)
    trail.save(out / "nova-walking-down.png")
    trail.hold(0.3, up=True)
    trail.save(out / "nova-walking.png")
    _walk_to(trail, 250, 230)
    trail.hold(0.4)
    trail.save(out / "compass-prompt.png")
    trail.press()
    trail.hold(0.35)
    trail.save(out / "compass-interaction.png")
    trail.hold(1.5)
    _walk_to(trail, 190, 390)
    trail.hold(0.4)
    trail.save(out / "lantern-prompt.png")
    trail.press()
    trail.hold(0.25)
    trail.save(out / "lantern-interaction.png")
    trail.hold(0.35)
    trail.save(out / "mission-complete.png")
    trail.close()

    # Moving only the student-owned Compass moves its sprite and every effect.
    with tempfile.TemporaryDirectory() as temporary:
        compass = Path(temporary) / "moon-compass"
        shutil.copytree(S02_PACKAGES[-1], compass)
        source = compass / "objects" / "compass.yaml"
        source.write_text(
            source.read_text().replace("x: 240", "x: 690").replace("y: 180", "y: 360")
        )
        trail = Trail((*S02_PACKAGES[:-1], compass))
        trail.hold(1.0)
        trail.save(out / "moved-compass.png")
        trail.close()

    idle = pygame.image.load(str(out / "pixel-greeting.png"))
    half = pygame.transform.smoothscale(idle, (480, 320))
    pygame.image.save(half, str(out / "half-scale-zoom.png"))
    print(f"wrote {out / 'half-scale-zoom.png'}")

    # Short motion clips for GIF evidence (frames only; encoding is optional).
    trail = Trail()
    trail.record = True
    trail.hold(1.0)
    trail.hold(0.8, right=True)
    trail.hold(0.6, down=True)
    trail.hold(1.0, left=True)
    trail.hold(0.7, up=True)
    trail.hold(0.4)
    _walk_to(trail, 380, 250)
    trail.hold(0.3)
    trail.press()
    trail.hold(2.0)
    gif_frames["nova-walk-and-greet"] = trail.frames
    trail.close()

    trail = Trail()
    trail.hold(0.2)
    trail.record = True
    trail.hold(5.0)
    gif_frames["living-world-idle"] = trail.frames
    trail.close()


def write_gifs(out: Path, gif_frames: dict[str, list[pygame.Surface]]) -> None:
    try:
        from PIL import Image
    except ImportError:
        print("Pillow is not installed; skipping GIF encoding")
        return
    for name, frames in gif_frames.items():
        images = []
        for surface in frames[::4]:
            small = pygame.transform.smoothscale(surface, (480, 320))
            raw = pygame.image.tobytes(small, "RGB")
            images.append(Image.frombytes("RGB", (480, 320), raw).quantize(colors=128))
        path = out / f"{name}.gif"
        images[0].save(path, save_all=True, append_images=images[1:], duration=67, loop=0)
        print(f"wrote {path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--only", choices=("before", "all"), default="all")
    args = parser.parse_args(argv)
    if args.only == "before":
        # Keep PYTHONPATH first so an older checkout's runtime is the one used.
        capture_before(args.output)
        return 0
    sys.path.insert(0, str(REPO))
    gif_frames: dict[str, list[pygame.Surface]] = {}
    capture_all(args.output, gif_frames)
    write_gifs(args.output, gif_frames)
    return 0


if __name__ == "__main__":
    sys.exit(main())
