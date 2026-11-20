"""Capture real S09 Trail frames: initial, partial, exact goal, and post-goal."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from scripts.trail_driver import Trail  # noqa: E402


def capture(out: Path):
    trail = Trail(
        (
            ROOT / "examples/explorer-packages/nova-character",
            ROOT / "lessons/sessions/s09/student/explorer-package",
        ),
        mission_id="count-object-interactions",
    )
    try:
        trail.hold(0.3)
        trail.save(out / "s09-spawn.png")
        trail.walk_to(350, 300)
        trail.hold(0.4)
        trail.save(out / "s09-initial.png")
        assert not trail.scene.mission_is_complete
        for number in range(1, 5):
            trail.press()
            trail.hold(0.35)
            assert dict(trail.scene.counter_counts) == {"storm-engine:storm-engine": number}
            assert trail.scene.mission_is_complete is (number > 2)
            trail.save(out / f"s09-interaction-{number}.png")
    finally:
        trail.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    capture(args.out)
