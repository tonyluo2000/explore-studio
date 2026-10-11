"""Capture real S05 Classroom Trail runtime frames for visual review.

Drives the actual M05 Trail scene headlessly (``SDL_VIDEODRIVER=dummy``) with
the canonical S05 command's packages (Nova, the Crystal Lantern, and the S05
package's Moonlit Guide), real directional input, real ``E`` presses, and fixed
60 FPS time steps, then saves the 960 x 640 window after each scene render.
Nothing is mocked or painted afterwards; the half-scale image is a smooth
downscale of a captured frame, approximating a Zoom screen share.

    SDL_VIDEODRIVER=dummy python3 scripts/capture_s05_visual_proof.py OUTPUT_DIR

Only long-standing scene APIs are used, so ``--only before`` captures the same
start and middle-line moments from an older checkout placed first on
``PYTHONPATH``. When ``before-*.png`` files are in OUTPUT_DIR, a full run also
writes side-by-side comparisons.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Appended, so an older checkout first on PYTHONPATH still provides the runtime.
sys.path.append(str(REPO))

import pygame  # noqa: E402

from scripts.trail_driver import Trail as _Trail  # noqa: E402
from scripts.trail_driver import half_scale, save_surface  # noqa: E402

S05_PACKAGES = (
    REPO / "examples/explorer-packages/nova-character",
    REPO / "examples/explorer-packages/crystal-lantern",
    REPO / "lessons/sessions/s05/student/explorer-package",
)
MISSION_05_ID = "write-a-short-conversation"
#: Where Nova stops to talk, as in S04: in range of the Guide, beside it.
APPROACH = (455, 262)


class Trail(_Trail):
    """One real M05 Trail scene, with the canonical S05 packages."""

    def __init__(self) -> None:
        super().__init__(S05_PACKAGES, mission_id=MISSION_05_ID)


def capture_before(out: Path) -> None:
    trail = Trail()
    try:
        trail.hold(0.3)
        trail.save(out / "before-start.png")
        trail.walk_to(*APPROACH)
        trail.hold(0.5)
        for _ in range(2):
            trail.press()
            trail.hold(0.6)
        trail.save(out / "before-line-2.png")
    finally:
        trail.close()


def capture(out: Path) -> None:
    trail = Trail()
    try:
        # The exact canonical start: nothing driven yet but the first frames.
        trail.hold(0.3)
        trail.save(out / "s05-start.png")
        trail.walk_to(*APPROACH)
        trail.hold(0.5)
        trail.save(out / "s05-approach.png")  # prompt and talk cue
        for line in (1, 2, 3):
            trail.press()
            trail.hold(0.6)
            name = "s05-line-3-complete.png" if line == 3 else f"s05-line-{line}.png"
            trail.save(out / name)
            if line == 2:
                save_surface(half_scale(trail.surface()), out / "s05-line-2-480x320.png")
        # Between lines the cue returns once the bubble has gone; after the
        # final line it is gone for good.
        trail.hold(14.0)
        trail.save(out / "s05-after-final-line.png")
        trail.press()
        trail.hold(0.6)
        trail.save(out / "s05-restart.png")  # wraps to line one; M05 stays complete
    finally:
        trail.close()
    for moment in ("start", "line-2"):
        before = out / f"before-{moment}.png"
        after = out / ("s05-line-2.png" if moment == "line-2" else "s05-start.png")
        if before.is_file():
            pair = pygame.Surface((960 * 2 + 16, 640))
            pair.fill((24, 26, 40))
            pair.blit(pygame.image.load(str(before)), (0, 0))
            pair.blit(pygame.image.load(str(after)), (976, 0))
            save_surface(pair, out / f"comparison-{moment}.png")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", type=Path)
    parser.add_argument("--only", choices=("before",))
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.only == "before":
        capture_before(args.out)
    else:
        capture(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
