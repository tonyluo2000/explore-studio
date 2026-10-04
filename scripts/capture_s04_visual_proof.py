"""Capture real S04 Classroom Trail runtime frames for visual review.

Drives the actual M04 Trail scene headlessly (``SDL_VIDEODRIVER=dummy``) with
the canonical S04 command's packages (Nova, the Crystal Lantern, and the S04
Moonlit Guide), real directional input, a real ``E`` press, and fixed 60 FPS
time steps, then saves the 960 x 640 window after each scene render. Nothing
is mocked or painted afterwards; the half-scale image is a smooth downscale of
a captured frame, approximating a Zoom screen share, and the close-ups are
plain crops scaled up.

    SDL_VIDEODRIVER=dummy python3 scripts/capture_s04_visual_proof.py OUTPUT_DIR

Only long-standing scene APIs are used, so ``--only before`` captures the
same idle and greeting moments from an older checkout placed first on
``PYTHONPATH``; ``--only benchmark`` times update + render.
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
S04_PACKAGES = (
    REPO / "examples/explorer-packages/nova-character",
    REPO / "examples/explorer-packages/crystal-lantern",
    REPO / "lessons/sessions/s04/student/explorer-package",
)
MISSION_04_ID = "introduce-your-character"
STEP = 1 / 60
#: Where Nova stops to talk: in range of the Guide, beside it, not in front.
APPROACH = (455, 262)
#: The Guide's 100 x 100 box (canonical x/y), padded for the close-up crop.
GUIDE_CROP = (500, 170, 180, 180)
#: The longest greeting the bubble shows whole (six lines), in the task card's
#: shape: who the guide is, the trail problem, and the help it needs.
STRESS_GREETING = (
    "Welcome, brave explorer! I'm Luma, keeper of the Moonlit Trail, and every lantern "
    "beyond the ridge went dark last night, so please help me find the three lost "
    "lights before dawn."
)
#: Longer than the bubble holds: it must end in an explicit ellipsis.
OVERFLOW_GREETING = STRESS_GREETING + (
    " I will wait right here by the old stone path and keep my staff glowing so you "
    "can always find your way back to me."
)


class Trail:
    """One real M04 Trail scene plus the platform that renders it."""

    def __init__(self, package_roots: tuple[Path, ...] = S04_PACKAGES) -> None:
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
        self.scene = create_classroom_trail_scene(
            self.renderer, planned.plan, mission_id=MISSION_04_ID
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

    def surface(self) -> pygame.Surface:
        return pygame.display.get_surface().copy()

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


def _greet(trail: Trail) -> None:
    """Approach the Guide and press E once; the greeting is now displayed."""
    _walk_to(trail, *APPROACH)
    assert trail.scene.target_qualified_id == "moonlit-guide:guide"
    assert not trail.scene.mission_is_complete
    trail.press()
    assert trail.scene.mission_is_complete


def _save_surface(surface: pygame.Surface, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(path))
    print(f"wrote {path}")


def _half(surface: pygame.Surface) -> pygame.Surface:
    return pygame.transform.smoothscale(surface, (480, 320))


def _closeup(surface: pygame.Surface, scale: int = 3) -> pygame.Surface:
    x, y, width, height = GUIDE_CROP
    crop = surface.subsurface(pygame.Rect(x, y, width, height)).copy()
    return pygame.transform.scale(crop, (width * scale, height * scale))


def _with_greeting(directory: Path, greeting: str) -> Path:
    """A copy of the S04 package whose student-authored greeting is *greeting*."""
    guide = directory / "explorer-package"
    shutil.copytree(S04_PACKAGES[-1], guide)
    source = guide / "character" / "guide.yaml"
    lines = [
        f'greeting: "{greeting}"' if line.startswith("greeting:") else line
        for line in source.read_text(encoding="utf-8").splitlines()
    ]
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return guide


def capture_before(out: Path) -> None:
    trail = Trail()
    trail.hold(1.2)
    trail.save(out / "before-idle.png")
    trail.close()
    trail = Trail()
    trail.hold(0.3)
    _greet(trail)
    trail.hold(0.6)
    trail.save(out / "before-dialogue.png")
    trail.close()


def capture_all(out: Path, gif_frames: dict[str, list[pygame.Surface]]) -> None:
    # S04_IDLE, S04_GUIDE_VISIBLE, and LIVING_WORLD_5S: Nova untouched. The strip
    # tiles five moments of the same idle, so ambient life shows in one still.
    trail = Trail()
    strip: list[pygame.Surface] = []
    for moment in range(5):
        trail.hold(1.2 if moment == 0 else 1.0)
        if moment == 0:
            trail.save(out / "s04-idle.png")
            _save_surface(_closeup(trail.surface()), out / "guide-closeup-idle.png")
        if moment == 1:
            trail.save(out / "s04-guide-visible.png")
        strip.append(trail.surface())
    trail.hold(0.8)
    trail.save(out / "s04-living-world-5s.png")
    trail.close()
    sheet = pygame.Surface((480 * len(strip), 320))
    for index, frame in enumerate(strip):
        sheet.blit(_half(frame), (480 * index, 0))
    _save_surface(sheet, out / "s04-living-world-strip.png")

    # S04_APPROACH, S04_DIALOGUE, S04_COMPLETE, and S04_HALF_SCALE.
    trail = Trail()
    trail.hold(0.3)
    _walk_to(trail, *APPROACH)
    trail.hold(0.5)
    trail.save(out / "s04-approach.png")
    trail.press()
    trail.hold(0.6)
    trail.save(out / "s04-dialogue.png")
    dialogue = trail.surface()
    _save_surface(_half(dialogue), out / "s04-half-scale-480x320.png")
    trail.hold(0.2)
    _save_surface(_closeup(trail.surface()), out / "guide-closeup-talking.png")
    # After the bubble's reading time the cue is gone and M04 stays Complete.
    trail.hold(12.0)
    assert trail.scene.mission_is_complete
    trail.save(out / "s04-complete.png")
    trail.close()

    # S04_DIALOGUE_STRESS: the longest greeting shown whole, and an overflow
    # greeting that ends in an explicit ellipsis instead of vanishing.
    for name, greeting in (
        ("s04-dialogue-stress", STRESS_GREETING),
        ("s04-dialogue-overflow", OVERFLOW_GREETING),
    ):
        with tempfile.TemporaryDirectory() as temporary:
            guide = _with_greeting(Path(temporary), greeting)
            trail = Trail((*S04_PACKAGES[:-1], guide))
            trail.hold(0.3)
            _greet(trail)
            trail.hold(0.6)
            trail.save(out / f"{name}.png")
            _save_surface(_half(trail.surface()), out / f"{name}-480x320.png")
            trail.close()

    # A short approach-and-greet clip and a five-second idle clip.
    trail = Trail()
    trail.hold(0.2)
    trail.record = True
    trail.hold(0.3)
    _walk_to(trail, *APPROACH)
    trail.hold(0.3)
    trail.press()
    trail.hold(2.4)
    gif_frames["s04-approach-and-greet"] = trail.frames
    trail.close()

    trail = Trail()
    trail.hold(0.2)
    trail.record = True
    trail.hold(5.0)
    gif_frames["s04-living-world-5s"] = trail.frames
    trail.close()


def benchmark(frames: int = 600) -> None:
    """Time real update + render of a moving, greeting M04 frame (headless).

    Nova walks a loop past the Guide and the Lantern while pressing E every
    second, so walking, prompts, the talk cue, and the dialogue bubble are all
    exercised. Works on older checkouts too.
    """
    import statistics
    import time

    trail = Trail()
    trail.hold(1.0)
    pattern = ["right"] * 40 + ["up"] * 30 + ["left"] * 160 + ["down"] * 140 + ["right"] * 120
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
    parser.add_argument("--only", choices=("before", "all", "benchmark"), default="all")
    args = parser.parse_args(argv)
    if args.only == "before":
        # Keep PYTHONPATH first so an older checkout's runtime is the one used.
        capture_before(args.output)
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
