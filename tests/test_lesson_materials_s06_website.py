"""S06 website publication stays grounded in the canonical lesson and M06 runtime."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

from engine.rendering._mission_presentation import mission_presentation
from engine.scenes import ClassroomTrailMissionCompletionRule
from explore.curriculum.missions import MISSION_06, MISSION_06_ID
from scripts.trail_driver import Trail

ROOT = Path(__file__).parents[1]
S06 = ROOT / "lessons" / "sessions" / "s06"
STUDENT = S06 / "student"
WEBSITE = ROOT / "course4teen-website"
SLIDES = WEBSITE / "app" / "students" / "slides" / "s06" / "page.tsx"
LEARN = WEBSITE / "lib" / "learn.ts"
LEARN_PAGE = WEBSITE / "app" / "students" / "learn" / "[session]" / "page.tsx"
CALENDAR = WEBSITE / "lib" / "calendar.ts"
TASK_CARD = STUDENT / "task-card.md"
STARTER = STUDENT / "starter.py"
PACKAGE = STUDENT / "explorer-package"
OBJECTS = tuple(sorted((PACKAGE / "objects").glob("*.yaml")))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(path: Path) -> str:
    return " ".join(_read(path).split())


def _published() -> list[str]:
    match = re.search(r"sessionsWithSlides[^=]*= \[([^\]]*)\]", _read(CALENDAR))
    assert match
    return re.findall(r'"(S\d\d)"', match.group(1))


def _s06_notes() -> str:
    return _read(LEARN).split('id: "S06"', 1)[1]


def _js_string(source: str, key: str) -> str:
    match = re.search(rf"{key}: `([^`]*)`", source)
    assert match, key
    return match.group(1)


def test_s06_is_published_without_s07() -> None:
    assert _published() == ["S01", "S02", "S03", "S04", "S05", "S06"]
    assert SLIDES.is_file()
    assert re.findall(r'^\s+id: "(S\d\d)"', _read(LEARN), re.MULTILINE) == _published()
    assert not (WEBSITE / "app" / "students" / "slides" / "s07").exists()
    assert not (WEBSITE / "public" / "journey" / "s07").exists()


def test_s06_title_date_and_next_session_are_calendar_derived() -> None:
    calendar = _read(CALENDAR)
    assert (
        '{ id: "S06", number: 6, date: "2026-10-24", title: "Build a Themed Collection" }'
        in calendar
    )
    slides = _read(SLIDES)
    assert 'classSessions.find((s) => s.id === "S06")!' in slides
    assert 'classSessions.find((s) => s.id === "S07")!' in slides
    assert "2026-10-24" not in slides
    assert "Create a Two-State Prop" not in slides
    assert "heading: `${nextSession.id} · ${nextSession.title}`" in slides


def test_s06_slides_follow_the_canonical_task_card_command() -> None:
    card = re.sub(r"\\\n\s*", " ", _read(TASK_CARD))
    (command,) = [
        " ".join(line.split())
        for line in card.splitlines()
        if line.strip().startswith("explore-package trail")
    ]
    slides = re.sub(r"\\\\\n\s*", " ", _read(SLIDES))
    assert command in " ".join(slides.split())
    assert "explore-package validate lessons/sessions/s06/student/explorer-package" in slides


def test_s06_slides_teach_the_bounded_python_path_in_order() -> None:
    slides = _read(SLIDES)
    headings = [
        "A dictionary is one record",
        "A list is an ordered collection of records",
        "Look up a value by key",
        "One plain for loop",
        "Trace the first iteration",
        "Complete the starter",
        "Find the missing y property",
        "Python plans; YAML drives the Trail",
        "Interact with all three objects",
        "One list, one loop, three records",
    ]
    positions = [slides.index(heading) for heading in headings]
    assert positions == sorted(positions)
    for required in (
        "exactly three",
        'object_record["x"]',
        "KeyError",
        "No list comprehension",
        "No nested loop",
        "No second loop",
        "No fourth object",
    ):
        assert required in slides, required


def test_s06_notes_are_a_worked_example_grounded_in_the_starter() -> None:
    notes = _s06_notes()
    assert 'sourceFile: "task-card.md"' in notes
    assert not (STUDENT / "python-notes.md").exists()
    for required in (
        'term: "dictionary"',
        'term: "list of dictionaries"',
        'term: "key lookup"',
        'term: "for loop"',
        'term: "KeyError"',
        "python lessons/sessions/s06/student/starter.py",
        'object_record["x"]',
        "validated package YAML",
    ):
        assert required in notes, required

    code = _js_string(notes, "code")
    output = _js_string(notes, "output")
    ran = subprocess.run(
        [sys.executable, "-c", code], check=True, capture_output=True, text=True
    ).stdout
    assert ran.strip() == output
    assert output in _read(SLIDES)


def test_s06_names_and_values_match_the_canonical_package() -> None:
    records = [yaml.safe_load(path.read_text(encoding="utf-8")) for path in OBJECTS]
    by_name = {record["name"]: record for record in records}
    assert set(by_name) == {"Sun Seed", "Rain Bell", "Wind Flower"}
    slides_and_notes = _read(SLIDES) + _s06_notes()
    for name in ("Sun Seed", "Rain Bell", "Wind Flower"):
        record = by_name[name]
        for value in (name, str(record["x"]), str(record["y"]), record["color"]):
            assert value in slides_and_notes


def test_s06_has_journey_context_on_slides_and_notes() -> None:
    slides = _read(SLIDES)
    assert 'import JourneyContext from "../../../components/JourneyContext";' in slides
    assert slides.count("<JourneyContext session={session.id} />") == 1
    learn_page = _read(LEARN_PAGE)
    assert learn_page.count("<JourneyContext session={session.id} />") == 1
    assert 'id: "S06"' in _read(LEARN)


def test_m06_contract_is_session_scoped_three_objects_all_visited_and_no_npc() -> None:
    assert MISSION_06_ID == "build-an-object-collection"
    assert MISSION_06.completion_rule is ClassroomTrailMissionCompletionRule.ALL_OBJECTS_VISITED
    # The mission id alone stays plain because later sessions reuse M06.
    assert mission_presentation(MISSION_06_ID) is None
    assert mission_presentation(MISSION_06_ID, package_ids=("starlight-garden",)) is not None
    assert len(OBJECTS) == 3
    records = [yaml.safe_load(path.read_text(encoding="utf-8")) for path in OBJECTS]
    for field in ("name", "x", "y", "color", "when_near", "when_interacted"):
        assert len({record[field] for record in records}) == 3, field

    trail = Trail(
        (ROOT / "examples" / "explorer-packages" / "nova-character", PACKAGE),
        mission_id=MISSION_06_ID,
    )
    try:
        assert trail.scene._presentation.active
        assert trail.scene.npcs == ()
        assert len(trail.scene.objects) == 3
        for index, record in enumerate(records):
            trail.walk_to(record["x"], record["y"])
            trail.press()
            assert trail.scene.mission_is_complete is (index == 2)
    finally:
        trail.close()


def test_s06_starter_and_lesson_materials_are_unchanged() -> None:
    source = _read(STARTER)
    assert source.count('{"name":') == 3
    assert source.count("for ") == 1
    assert "TODO: third garden object" in source
    assert "gate hidden in the sky" in _flat(TASK_CARD)
    assert "S07" not in _s06_notes()
    assert "toggle" not in _s06_notes().lower()
