"""Keep the S08 slides, worked Python example, and Trail launch in sync."""

import re
import subprocess
import sys
from pathlib import Path

from scripts.journey_snapshots import canonical_command

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "course4teen-website"
STUDENT = ROOT / "lessons/sessions/s08/student"


def test_slides_use_the_canonical_m08_command():
    slides = (WEB / "app/students/slides/s08/page.tsx").read_text()
    command = next(
        line.strip()
        for line in (STUDENT / "task-card.md").read_text().splitlines()
        if line.strip().startswith("explore-package trail ")
    )
    assert f"`{command}`" in slides
    assert canonical_command("S08").mission_id == "respond-to-object-state"
    assert "Responses 1 / 2" in slides and "Responses 2 / 2" in slides


def test_worked_example_repairs_only_the_condition():
    starter = (STUDENT / "starter.py").read_text()
    learn = (WEB / "lib/learn.ts").read_text().split('id: "S08",', 1)[1]
    code = re.search(r"code: `([^`]*)`", learn).group(1)
    assert code == "\n".join(
        line for line in starter.splitlines()[2:] if "# TODO:" not in line
    ).strip().replace("if not is_on:", "if is_on:")
    actual = subprocess.check_output([sys.executable, "-c", code], text=True)
    assert actual == "The portal is sleeping.\nThe portal is glowing!\n"
    assert f"output: `{actual.strip()}`" in learn
