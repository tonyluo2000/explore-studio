"""S07 public content matches the authored lesson and keeps S08 details private."""

import json
import os
import re
import subprocess
import sys
from html import unescape
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "course4teen-website"
SLIDES = WEB / "app/students/slides/s07/page.tsx"
CARD = ROOT / "lessons/sessions/s07/student/task-card.md"
STARTER = CARD.with_name("starter.py")


def test_s07_publication_and_shared_context():
    calendar = (WEB / "lib/calendar.ts").read_text()
    ids = re.findall(
        r'"S\d\d"',
        calendar.split("sessionsWithSlides: readonly string[] = ", 1)[1].split(";", 1)[0],
    )
    assert ids == [f'"S{i:02}"' for i in range(1, 8)]
    slides = SLIDES.read_text()
    assert "<JourneyContext session={session.id} />" in slides
    assert '<PythonJourney session={session.id} mode="compact" />' in slides
    learn = (WEB / "app/students/learn/[session]/page.tsx").read_text()
    assert "<JourneyContext session={session.id} />" in learn
    assert '<PythonJourney session={session.id} mode="compact" />' in learn
    assert 'id: "S07"' in (WEB / "lib/learn.ts").read_text()
    assert not (WEB / "app/students/slides/s08").exists()
    assert not (WEB / "public/journey/s08").exists()


def test_commands_match_task_card_and_one_line_launch():
    slides = SLIDES.read_text()
    card = CARD.read_text()
    command = next(
        line.strip()
        for line in card.splitlines()
        if line.strip().startswith("explore-package trail ")
    )
    assert command in slides
    assert command.count("--mission-id") == 1
    assert "explore-package validate lessons/sessions/s07/student/explorer-package" in slides
    assert "python lessons/sessions/s07/student/starter.py" in slides


def test_starter_bug_and_worked_repair_are_executable_and_truthful():
    starter = subprocess.check_output([sys.executable, str(STARTER)], text=True)
    assert starter == "False blue\nFalse gold\n"
    source = (WEB / "lib/learn.ts").read_text().split('id: "S07",', 1)[1]
    code = re.search(r"code: `([^`]*)`", source).group(1)
    result = subprocess.check_output([sys.executable, "-c", code], text=True)
    assert result == "False blue\nTrue gold\n"
    assert "output: `False blue\nTrue gold`" in source
    for text in (
        "Boolean",
        "assignment",
        "state",
        "toggle sequence",
        "Printing a color string does not mutate is_on",
        "YAML declares",
        "Trail owns runtime session state",
    ):
        assert text in source


def test_slides_cover_the_canonical_teaching_sequence():
    slides = SLIDES.read_text()
    headings = [
        "S07 · Create a Two-State Prop",
        "Python Journey so far",
        "Today in Python: Booleans & state",
        "False and True",
        "is_on stores one state",
        "Predict the 4-row trace",
        "Find the starter bug",
        "Printing a color does not change state",
        "Repair the assignment",
        "Check the repaired output",
        "Python → YAML → Trail",
        "Declare the two colors",
        "Validate the package",
        "Launch S07 Trail",
        "Observe OFF → ON → OFF → ON",
        "What M07 completion means",
        "Explain what changed",
    ]
    positions = [slides.index(f'heading: "{heading}"') for heading in headings]
    assert positions == sorted(positions)
    assert "after the toggle changes at least once" in slides
    assert "Final ON/gold is a story target, not mission-checked" in slides
    assert "confirm it by observation" in slides
    assert "These fixed messages do not read state" in slides


def test_s07_journey_stop_and_snapshot_state_contract():
    from scripts.journey_snapshots import SESSIONS_BY_ID

    data = json.loads((WEB / "journey/journey.json").read_text())
    assert [stop["session"] for stop in data["stops"]] == [f"S{i:02}" for i in range(1, 8)]
    assert data["stops"][-1]["landmark"] == "sky-signal"
    hero = SESSIONS_BY_ID["S07"].hero
    assert hero.expect.complete and hero.expect.toggle_on == ("sky-lantern-switch:sky-lantern",)
    assert "S08" not in SESSIONS_BY_ID


SITE = os.environ.get("JOURNEY_SITE_OUT")


@pytest.mark.skipif(not SITE, reason="requires fresh exported site")
def test_rendered_s07_progress_no_s08_details_or_bundles():
    out = ROOT / SITE
    for route in ("slides", "learn"):
        html = (out / f"students/{route}/s07/index.html").read_text()
        assert "Boolean state" in html
        assert 'data-python-current="S07"' in html
        visible = " ".join(unescape(re.sub("<[^>]*>", " ", html)).split())
        assert re.search(r"7\s*/\s*30", visible)
        assert 'data-python-step="S08"' not in html
        assert not (out / f"students/{route}/s08/index.html").exists()
    forbidden = (
        "Boolean branches",
        "Choose between two behaviors based on state.",
        "respond_to_toggle",
        "when_on",
        "when_off",
        "guardian-response",
        "/journey/s08/",
    )
    files = [
        out / "students/journey/index.html",
        *out.glob("students/*/s07/index.html"),
        *out.glob("_next/static/**/*.js"),
    ]
    for path in files:
        content = path.read_text()
        for term in forbidden:
            assert term not in content, (path, term)


def test_ci_runs_s07_publication_and_runtime_regressions():
    workflow = (ROOT / ".github/workflows/course-readiness.yml").read_text()
    assert "          tests/test_lesson_materials_s07_website.py" in workflow
    assert "          tests/test_s07_presentation.py" in workflow
