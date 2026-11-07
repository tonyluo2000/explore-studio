"""Capture real, unedited S07 Trail frames across OFF/ON/OFF/ON for review."""

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
            ROOT / "lessons/sessions/s07/student/explorer-package",
        ),
        mission_id="toggle-an-object-state",
    )
    try:
        trail.hold(0.3)
        trail.save(out / "s07-spawn.png")
        trail.walk_to(290, 300)
        trail.hold(0.4)
        trail.save(out / "s07-near-off.png")
        for number, on in enumerate((True, False, True), 1):
            trail.press()
            trail.hold(0.35)
            assert bool(trail.scene.toggle_on_qualified_ids) is on
            assert trail.scene.mission_is_complete
            trail.save(out / f"s07-interaction-{number}-{'on' if on else 'off'}.png")
    finally:
        trail.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    capture(args.out)
