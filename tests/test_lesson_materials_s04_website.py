"""S04 student website: slides and Python Notes stay grounded in the canonical lesson
and runtime."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

from engine.rendering._mission_presentation import mission_presentation
from engine.scenes import ClassroomTrailMissionCompletionRule
from explore.curriculum.missions import MISSION_04, MISSION_04_ID

PROJECT_ROOT = Path(__file__).parents[1]
S04 = PROJECT_ROOT / "lessons" / "sessions" / "s04"
WEBSITE = PROJECT_ROOT / "course4teen-website"
SLIDES = WEBSITE / "app" / "students" / "slides" / "s04" / "page.tsx"
LEARN = WEBSITE / "lib" / "learn.ts"
CALENDAR = WEBSITE / "lib" / "calendar.ts"
TRAIL_PRESENTATION = PROJECT_ROOT / "engine" / "rendering" / "_trail_presentation.py"
GUIDE = S04 / "student" / "explorer-package" / "character" / "guide.yaml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _s04_learn_entry() -> str:
    return _read(LEARN).split('id: "S04"', 1)[1]


def _slides_published() -> list[str]:
    match = re.search(r"sessionsWithSlides[^=]*= \[([^\]]*)\]", _read(CALENDAR))
    assert match
    return re.findall(r'"(S\d\d)"', match.group(1))


def _js_string(source: str, key: str) -> str:
    """The template-literal value of ``key: `...``` in learn.ts."""
    match = re.search(rf"{key}: `([^`]*)`", source)
    assert match, key
    return match.group(1)


def test_s04_is_published_and_s05_is_not():
    assert _slides_published() == ["S01", "S02", "S03", "S04"]
    learn_ids = re.findall(r'^\s+id: "(S\d\d)"', _read(LEARN), re.MULTILINE)
    assert learn_ids == ["S01", "S02", "S03", "S04"]
    assert not (WEBSITE / "app" / "students" / "slides" / "s05").exists()
    slides = _read(SLIDES)
    assert 'canonical: "/students/slides/s04/"' in slides
    assert "/students/learn/s04/" in slides


def test_s04_title_and_mission_match_the_curriculum():
    assert '{ id: "S04", number: 4, date: "2026-10-10", title: "Introduce a Character" }' in _read(
        CALENDAR
    )
    assert "# S04 Task Card — Introduce a Character" in _read(S04 / "student" / "task-card.md")
    slides = _read(SLIDES)
    assert 'title: "S04 Slides · Introduce a Character | Course4Teen"' in slides
    assert MISSION_04_ID == "introduce-your-character"
    assert (
        MISSION_04.completion_rule
        is ClassroomTrailMissionCompletionRule.ALL_INTERACTABLE_NPCS_SPOKEN_TO
    )
    for required in (
        f"<code>{MISSION_04_ID}</code>",
        f"M04 · {MISSION_04.title}",
        "Define and call",
        "explore-package validate lessons/sessions/s04/student/explorer-package",
        f'--mission-id "{MISSION_04_ID}"',
        '--name "S04 Introduce a Character"',
        "examples/explorer-packages/crystal-lantern",
    ):
        assert required in slides, required


def test_s04_slides_teach_function_parameter_argument_and_call_in_order():
    slides = _read(SLIDES)
    ordered = [
        "What is a function?",
        'heading: "def greet(name):"',
        'heading: "greet(\\"Ari\\")"',
        "Parameter vs. argument",
        'heading: "The starter"',
        "Write your two lines first",
        "Setting, second call, run",
        "Python greeting, YAML greeting",
        "Meet the Moonlit Guide",
        "Talk to Moonlit Guide",
        "M04 complete",
        "Call greet() with no argument",
    ]
    positions = [slides.index(heading) for heading in ordered]
    assert positions == sorted(positions)
    for concept in (
        "parameter",
        "argument",
        "four spaces",
        "<strong>call</strong>",
        "<strong>define</strong>",
    ):
        assert concept in slides, concept


def test_s04_slides_show_the_real_starter_and_its_unfinished_output():
    slides = _read(SLIDES)
    for line in _read(S04 / "student" / "starter.py").splitlines()[2:]:
        assert line in slides, line
    output = subprocess.run(
        [sys.executable, str(S04 / "student" / "starter.py")],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert output.strip() == "Welcome to TODO: name your setting, Ari!"
    assert output.strip() in slides


def test_s04_notes_code_prints_exactly_the_published_output():
    notes = _s04_learn_entry()
    code, output = _js_string(notes, "code"), _js_string(notes, "output")
    ran = subprocess.run(
        [sys.executable, "-c", code], check=True, capture_output=True, text=True
    ).stdout
    assert ran.strip() == output
    assert output in _read(SLIDES)


def test_s04_debugging_traceback_is_the_real_error():
    notes = _s04_learn_entry()
    result = subprocess.run(
        [sys.executable, "-c", "def greet(name):\n    print(name)\n\ngreet()"],
        capture_output=True,
        text=True,
    )
    final_line = result.stderr.strip().splitlines()[-1]
    assert final_line == "TypeError: greet() missing 1 required positional argument: 'name'"
    assert final_line in notes and final_line in _read(SLIDES)
    assert "broken: `greet()`" in notes


def test_s04_slides_greeting_matches_the_package():
    guide = yaml.safe_load(_read(GUIDE))
    slides = _read(SLIDES)
    assert f'greeting: "{guide["greeting"]}"' in slides
    assert f'name: "{guide["name"]}"' in slides


def test_s04_guide_wording_matches_the_runtime():
    guide = yaml.safe_load(_read(GUIDE))
    presentation = mission_presentation(MISSION_04_ID)
    assert presentation is not None
    assert presentation.talk_cue and presentation.dialogue_focus
    assert not presentation.lantern_waypoint
    assert not presentation.celebration and not presentation.discovery_label
    assert 'return f"Talk to {npc.character.name}"' in _read(TRAIL_PRESENTATION)

    slides = " ".join(_read(SLIDES).split())
    for required in (
        f"Talk to {guide['name']}",
        "same painted Moon Meadow as S02 and S03",
        "floating speech cue",
        "speech bubble",
        "<strong>Moonlit Guide</strong> name tag",
        "<strong>Mission state</strong> row change to <strong>Complete</strong>",
        "not today&rsquo;s target",
        "M04 completes by talking to the guide",
    ):
        assert required in slides, required


def test_s04_slides_do_not_describe_retired_or_unshipped_visuals():
    slides = _read(SLIDES).lower()
    for absent in (
        "rectangle",
        "plain trail",
        "plain dark",
        "standard trail",
        "confetti",
        "discovered!",
        "pixel",
    ):
        assert absent not in slides, absent
    assert "NovaPixelScene" not in _read(SLIDES)
    assert "S02TrailMap" not in _read(SLIDES)


def test_s04_notes_name_their_real_course_kit_source_and_concepts():
    notes = _s04_learn_entry()
    assert 'sourceFile: "task-card.md"' in notes
    assert (S04 / "student" / "task-card.md").is_file()
    assert not (
        S04 / "student" / "python-notes.md"
    ).exists(), "S04 now has python-notes.md; drop sourceFile so the Learn page points at it"
    for required in (
        'term: "function"',
        'term: "def"',
        'term: "parameter"',
        'term: "argument"',
        'term: "call"',
        'term: "indentation"',
        "python lessons/sessions/s04/student/starter.py",
        "greeting:",
        "Moonlit Guide",
    ):
        assert required in notes, required


def test_s04_runbook_recovery_output_is_what_the_published_code_prints():
    ran = subprocess.run(
        [sys.executable, "-c", _js_string(_s04_learn_entry(), "code")],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    runbook = _read(S04 / "teacher-runbook.md")
    assert "Welcome to Moonlit Trail, Ari!" in ran
    assert "Welcome to Moonlit Trail, Ari!\nWelcome to Moonlit Trail, Sam!" in runbook
    assert "Welcome to the Moonlit Trail" not in runbook
