"""Capture real S01 Classroom Trail runtime frames for visual review.

Drives the actual M01 Trail scene headlessly (``SDL_VIDEODRIVER=dummy``) with
the canonical S01 command's packages (Nova, Pixel, and the Crystal Lantern),
real directional input, a real ``E`` press, and fixed 60 FPS time steps, then
saves the 960 x 640 window after each scene render. Nothing is mocked or
painted afterwards; the half-scale image is a smooth downscale of a captured
frame, approximating a Zoom screen share.

    SDL_VIDEODRIVER=dummy python3 scripts/capture_s01_visual_proof.py OUTPUT_DIR

``--only before`` captures the retired S01 Trail (Nova, Fern, the Lantern, and
the River Fountain on the plain Trail) from an older checkout placed first on
``PYTHONPATH``; ``--only compare`` tiles those frames beside the new ones;
``--only benchmark`` times update + render.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
EXAMPLES = REPO / "examples/explorer-packages"
S01_PACKAGES = (
    EXAMPLES / "nova-character",
    EXAMPLES / "pixel-companion",
    EXAMPLES / "crystal-lantern",
)
#: The S01 cast before the Moon Meadow arrival, still shipped as examples.
RETIRED_S01_PACKAGES = (
    EXAMPLES / "nova-character",
    EXAMPLES / "forest-guide",
    EXAMPLES / "crystal-lantern",
    EXAMPLES / "river-fountain",
)
MISSION_01_ID = "visit-all-classroom-objects"
STEP = 1 / 60
#: A few paces from the start toward the path: still on the landing pad beside
#: Pixel, but out of Pixel's interaction range, so the hero has no prompt.
ARRIVAL = (340, 262)
#: Beside the Lantern shrine and in interaction range.
LANTERN_APPROACH = (130, 400)


class Trail:
    """One real M01 Trail scene plus the platform that renders it."""

    def __init__(
        self, package_roots: tuple[Path, ...] = S01_PACKAGES, mission_id: str | None = MISSION_01_ID
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
        self.renderer = Renderer(self.platform)
        planned = plan_local_classroom_trail(
            package_roots, player_qualified_id="nova-character:nova"
        )
        assert planned.is_planned, planned.issues
        options = {} if mission_id is None else {"mission_id": mission_id}
        self.scene = create_classroom_trail_scene(self.renderer, planned.plan, **options)
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

    def surface(self) -> pygame.Surface:
        return pygame.display.get_surface().copy()

    def save(self, path: Path) -> None:
        _save_surface(pygame.display.get_surface(), path)

    def close(self) -> None:
        self.scene.exit()
        self.platform.shutdown()


def _walk_to(trail: Trail, x: int, y: int) -> None:
    """Walk with real directional input until the player reaches (x, y)."""
    player = trail.scene.player
    for _ in range(900):
        dx, dy = x - player.x_float, y - player.y_float
        if abs(dx) < 3 and abs(dy) < 3:
            return
        trail.step(left=dx < -2, right=dx > 2, up=dy < -2, down=dy > 2)
    raise AssertionError(f"Nova never reached {(x, y)}")


def _save_surface(surface: pygame.Surface, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(path))
    print(f"wrote {path}")


def _half(surface: pygame.Surface) -> pygame.Surface:
    return pygame.transform.smoothscale(surface, (480, 320))


def capture_before(out: Path) -> None:
    trail = Trail(RETIRED_S01_PACKAGES)
    trail.hold(1.2)
    trail.save(out / "before-idle.png")
    _walk_to(trail, *LANTERN_APPROACH)
    trail.hold(0.4)
    trail.press()
    trail.hold(0.6)
    trail.save(out / "before-lantern.png")
    trail.close()


def capture_all(out: Path, gif_frames: dict[str, list[pygame.Surface]]) -> None:
    # S01_ARRIVAL_START: the exact canonical start; Pixel is in range, so the
    # Trail offers the optional "Talk to Pixel" prompt.
    trail = Trail()
    trail.hold(1.2)
    assert trail.scene.target_qualified_id == "pixel-companion:pixel"
    trail.save(out / "s01-arrival-start.png")
    trail.close()

    # S01_ARRIVAL (hero) and S01_HALF_SCALE: Nova a few paces onto the pad
    # beside Pixel, idle, with no prompt; the Lantern shrine and the empty
    # stone circle in view.
    trail = Trail()
    trail.hold(0.3)
    _walk_to(trail, *ARRIVAL)
    trail.step(down=True)
    trail.hold(2.0)
    assert trail.scene.target_qualified_id is None
    assert trail.scene.visited_count == 0
    trail.save(out / "s01-arrival.png")
    _save_surface(_half(trail.surface()), out / "s01-half-scale-480x320.png")
    trail.close()

    # S01_PIXEL_HELLO: the optional greeting; Visited stays 0 / 1.
    trail = Trail()
    trail.hold(0.6)
    trail.press()
    trail.hold(0.6)
    assert trail.scene.visited_count == 0 and not trail.scene.mission_is_complete
    trail.save(out / "s01-pixel-hello.png")
    trail.close()

    # S01_LANTERN_NEAR, S01_LANTERN_INTERACT, and S01_COMPLETE.
    trail = Trail()
    trail.hold(0.3)
    _walk_to(trail, *LANTERN_APPROACH)
    trail.hold(0.6)
    assert trail.scene.target_qualified_id == "crystal-lantern:lantern"
    trail.save(out / "s01-lantern-near.png")
    trail.press()
    trail.hold(0.4)
    assert trail.scene.mission_is_complete and trail.scene.visited_count == 1
    trail.save(out / "s01-lantern-interact.png")
    trail.hold(4.0)
    assert trail.scene.is_complete
    trail.save(out / "s01-complete.png")
    trail.close()

    # The no --mission-id free-play Trail with the same cast: still plain.
    trail = Trail(mission_id=None)
    trail.hold(1.2)
    trail.save(out / "s01-cast-without-mission-id.png")
    trail.close()

    # A short arrival-to-Lantern clip.
    trail = Trail()
    trail.hold(0.2)
    trail.record = True
    trail.hold(0.6)
    _walk_to(trail, *LANTERN_APPROACH)
    trail.hold(0.3)
    trail.press()
    trail.hold(1.6)
    gif_frames["s01-arrival-to-lantern"] = trail.frames
    trail.close()


def compare(out: Path) -> None:
    pairs = (
        ("comparison-arrival.png", "before-idle.png", "s01-arrival-start.png"),
        ("comparison-lantern.png", "before-lantern.png", "s01-lantern-interact.png"),
    )
    for name, before, after in pairs:
        left = pygame.image.load(str(out / before))
        right = pygame.image.load(str(out / after))
        sheet = pygame.Surface((left.get_width() + right.get_width() + 16, left.get_height()))
        sheet.fill((255, 255, 255))
        sheet.blit(left, (0, 0))
        sheet.blit(right, (left.get_width() + 16, 0))
        _save_surface(sheet, out / name)


def benchmark(frames: int = 600) -> None:
    """Time real update + render of a moving M01 frame (headless)."""
    import statistics
    import time

    trail = Trail()
    trail.hold(1.0)
    pattern = ["left"] * 112 + ["down"] * 48 + ["up"] * 48 + ["right"] * 112
    samples = []
    for index in range(frames):
        key = pattern[index % len(pattern)]
        start = time.perf_counter()
        trail.step(**{key: True}, interact=index % 60 == 0)
        samples.append((time.perf_counter() - start) * 1000)
    trail.close()
    samples.sort()
    mean = statistics.fmean(samples)
    p95 = samples[int(len(samples) * 0.95) - 1]
    print(f"frames={frames} mean_ms={mean:.2f} p95_ms={p95:.2f}")


def write_gifs(out: Path, gif_frames: dict[str, list[pygame.Surface]]) -> None:
    try:
        from PIL import Image
    except ImportError:
        print("Pillow is not installed; skipping GIF encoding")
        return
    for name, frames in gif_frames.items():
        images = []
        for surface in frames[::4]:
            raw = pygame.image.tobytes(_half(surface), "RGB")
            images.append(Image.frombytes("RGB", (480, 320), raw).quantize(colors=128))
        path = out / f"{name}.gif"
        images[0].save(path, save_all=True, append_images=images[1:], duration=67, loop=0)
        print(f"wrote {path}")
    # Losslessly recompress the PNG captures (pixels are unchanged).
    for png in sorted(out.glob("*.png")):
        with Image.open(png) as image:
            image.load()
            image.save(png, optimize=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--only", choices=("before", "all", "compare", "benchmark"), default="all")
    args = parser.parse_args(argv)
    if args.only == "before":
        # Keep PYTHONPATH first so an older checkout's runtime is the one used.
        capture_before(args.output)
        return 0
    if args.only == "compare":
        compare(args.output)
        return 0
    if args.only == "benchmark":
        benchmark()
        return 0
    sys.path.insert(0, str(REPO))
    gif_frames: dict[str, list[pygame.Surface]] = {}
    capture_all(args.output, gif_frames)
    write_gifs(args.output, gif_frames)
    return 0


if __name__ == "__main__":
    sys.exit(main())
