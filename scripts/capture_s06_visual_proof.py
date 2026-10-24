"""Capture real S06 Moon Meadow runtime frames for visual review.

Drives the canonical S06 Trail with real movement and interaction input. Every
PNG is the actual 960 x 640 runtime frame; nothing is painted afterward.

    SDL_VIDEODRIVER=dummy python3 scripts/capture_s06_visual_proof.py OUTPUT_DIR
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO))

from scripts.trail_driver import Trail, half_scale, save_surface  # noqa: E402

PACKAGES = (
    REPO / "examples/explorer-packages/nova-character",
    REPO / "lessons/sessions/s06/student/explorer-package",
)
MISSION_ID = "build-an-object-collection"
ROUTE = (("sun-seed", 180, 180), ("rain-bell", 380, 300), ("wind-flower", 570, 420))


def capture(out: Path) -> None:
    trail = Trail(PACKAGES, mission_id=MISSION_ID)
    try:
        trail.hold(0.3)
        trail.save(out / "s06-spawn.png")
        for index, (slug, x, y) in enumerate(ROUTE, start=1):
            trail.walk_to(x, y)
            trail.hold(3.2 if index > 1 else 0.4)
            trail.save(out / f"s06-{slug}-near.png")
            trail.press()
            trail.hold(0.35)
            trail.save(out / f"s06-{slug}-interacted.png")
            if index == 2:
                trail.walk_to(570, 420)
                trail.hold(3.2)
                trail.save(out / "s06-two-of-three.png")
                save_surface(half_scale(trail.surface()), out / "s06-two-of-three-480x320.png")
        assert trail.scene.mission_is_complete
    finally:
        trail.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", type=Path)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    capture(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
