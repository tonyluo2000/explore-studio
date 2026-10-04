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
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Appended, so an older checkout first on PYTHONPATH still provides the runtime.
sys.path.append(str(REPO))

from scripts.trail_driver import Trail as _Trail  # noqa: E402

S03_PACKAGES = (
    REPO / "examples/explorer-packages/nova-character",
    REPO / "lessons/sessions/s03/student/explorer-package",
)
MISSION_03_ID = "make-your-object-respond"


class Trail(_Trail):
    """One real M03 Trail scene with the canonical S03 packages."""

    def __init__(self) -> None:
        super().__init__(S03_PACKAGES, mission_id=MISSION_03_ID)


def capture(out: Path, *, before: bool) -> None:
    trail = Trail()
    trail.hold(1.2)
    trail.save(out / ("before-idle.png" if before else "s03-idle.png"))
    trail.walk_to(250, 230)
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
