"""S05 student website: slides and Python Notes stay grounded in the canonical lesson
and runtime, and S06 stays unpublished."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

from engine.rendering._mission_presentation import mission_presentation
from engine.scenes import ClassroomTrailMissionCompletionRule
from explore.curriculum.missions import MISSION_05, MISSION_05_ID

PROJECT_ROOT = Path(__file__).parents[1]
S05 = PROJECT_ROOT / "lessons" / "sessions" / "s05"
WEBSITE = PROJECT_ROOT / "course4teen-website"
SLIDES = WEBSITE / "app" / "students" / "slides" / "s05" / "page.tsx"
LEARN = WEBSITE / "lib" / "learn.ts"
CALENDAR = WEBSITE / "lib" / "calendar.ts"
TRAIL_PRESENTATION = PROJECT_ROOT / "engine" / "rendering" / "_trail_presentation.py"
GUIDE = S05 / "student" / "explorer-package" / "character" / "guide.yaml"
STARTER = S05 / "student" / "starter.py"
TASK_CARD = S05 / "student" / "task-card.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(path: Path) -> str:
    return " ".join(_read(path).split())


def _s05_learn_entry() -> str:
    return _read(LEARN).split('id: "S05"', 1)[1]


def _slides_published() -> list[str]:
    match = re.search(r"sessionsWithSlides[^=]*= \[([^\]]*)\]", _read(CALENDAR))
    assert match
    return re.findall(r'"(S\d\d)"', match.group(1))


def _js_string(source: str, key: str) -> str:
    """The template-literal value of ``key: `...``` in learn.ts."""
    match = re.search(rf"{key}: `([^`]*)`", source)
    assert match, key
    return match.group(1)


def test_s05_is_published_and_s06_is_not():
    assert _slides_published() == ["S01", "S02", "S03", "S04", "S05"]
    learn_ids = re.findall(r'^\s+id: "(S\d\d)"', _read(LEARN), re.MULTILINE)
    assert learn_ids == ["S01", "S02", "S03", "S04", "S05"]
    assert not (WEBSITE / "app" / "students" / "slides" / "s06").exists()
    assert not (WEBSITE / "public" / "journey" / "s06").exists()
    slides = _read(SLIDES)
    assert 'canonical: "/students/slides/s05/"' in slides
    assert "/students/learn/s05/" in slides
    assert "/students/slides/s06/" not in slides and "/students/learn/s06/" not in slides


def test_s05_title_and_date_come_from_the_calendar_only():
    calendar = _read(CALENDAR)
    assert (
        '{ id: "S05", number: 5, date: "2026-10-17", title: "Script a Conversation" }' in calendar
    )
    assert "# S05 Task Card — Script a Conversation" in _read(TASK_CARD)
    slides = _read(SLIDES)
    # Title, date, and the next session's title are derived, never restated.
    assert 'classSessions.find((s) => s.id === "S05")!' in slides
    assert "title: `${session.id} Slides · ${session.title} | Course4Teen`" in slides
    # Only the task card's window title (--name) repeats it, inside the command.
    assert slides.count("Script a Conversation") == 1
    assert '--name "S05 Script a Conversation"' in slides
    assert "2026-10-17" not in slides
    assert "Build a Themed Collection" not in slides
    assert "heading: `${nextSession.id} · ${nextSession.title}`" in slides


def test_s05_mission_matches_the_curriculum():
    assert MISSION_05_ID == "write-a-short-conversation"
    assert (
        MISSION_05.completion_rule
        is ClassroomTrailMissionCompletionRule.ALL_CONVERSATION_NPCS_COMPLETED
    )
    slides = _read(SLIDES)
    for required in (
        f"<code>{MISSION_05_ID}</code>",
        f"M05 · {MISSION_05.title}",
        "explore-package validate lessons/sessions/s05/student/explorer-package",
        f'--mission-id "{MISSION_05_ID}"',
        '--name "S05 Script a Conversation"',
        "examples/explorer-packages/crystal-lantern",
    ):
        assert required in slides, required


def test_s05_slides_trail_command_is_the_task_card_command():
    card = re.sub(r"\\\n\s*", " ", _read(TASK_CARD))
    (command,) = [
        " ".join(line.split())
        for line in card.splitlines()
        if line.strip().startswith("explore-package trail")
    ]
    slides = re.sub(r"\\\\\n\s*", " ", _read(SLIDES))
    assert command in " ".join(slides.split())


def test_s05_slides_teach_list_index_len_and_debugging_in_order():
    slides = _read(SLIDES)
    ordered = [
        "What is a list?",
        'heading: "dialogue[0] and dialogue[-1]"',
        'heading: "len(dialogue)"',
        'heading: "The starter"',
        "Write four predictions first",
        "Lines, indexes, run",
        "Ask for dialogue[3]",
        "Swap two lines",
        "Python list, YAML conversation",
        "Back to the Moonlit Guide",
        "Talk to Moonlit Guide",
        "M05 complete",
    ]
    positions = [slides.index(heading) for heading in ordered]
    assert positions == sorted(positions)
    for concept in ("<strong>list</strong>", "<strong>0</strong>", "[-1]", "len(...)"):
        assert concept in slides, concept
    # No concept beyond S05's lesson: no loops, dictionaries, or branching yet.
    for later in ("for ", "dict", "if ", "elif", "while "):
        assert f"<code>{later}" not in slides, later


def test_s05_slides_show_the_real_starter_and_its_unfinished_output():
    slides = _read(SLIDES)
    for line in _read(STARTER).splitlines()[2:]:
        assert line in slides, line
    output = subprocess.run(
        [sys.executable, str(STARTER)], check=True, capture_output=True, text=True
    ).stdout
    assert output == "2\n"
    assert "<code>2</code>" in slides


def test_s05_notes_code_prints_exactly_the_published_output():
    notes = _s05_learn_entry()
    code, output = _js_string(notes, "code"), _js_string(notes, "output")
    ran = subprocess.run(
        [sys.executable, "-c", code], check=True, capture_output=True, text=True
    ).stdout
    assert ran.strip() == output
    assert output in _read(SLIDES)
    # The runbook's expected output is what the published code prints.
    assert output in _read(S05 / "teacher-runbook.md")


def test_s05_notes_and_slides_lines_match_the_package_in_order():
    lines = yaml.safe_load(_read(GUIDE))["conversation"]
    code = _js_string(_s05_learn_entry(), "code")
    for line in lines:
        assert f'    "Guide: {line}",' in code
    yaml_block = "conversation:\n" + "".join(f'  - "{line}"\n' for line in lines)
    assert yaml_block.rstrip("\n") in _read(SLIDES)


def test_s05_debugging_traceback_is_the_real_error():
    notes = _s05_learn_entry()
    result = subprocess.run(
        [sys.executable, "-c", 'dialogue = ["a", "b", "c"]\nprint(dialogue[3])'],
        capture_output=True,
        text=True,
    )
    final_line = result.stderr.strip().splitlines()[-1]
    assert final_line == "IndexError: list index out of range"
    assert final_line in notes and final_line in _read(SLIDES)
    assert "broken: `print(dialogue[3])`" in notes
    assert "fixed: `print(dialogue[-1])`" in notes


def test_s05_trail_wording_matches_the_runtime():
    guide = yaml.safe_load(_read(GUIDE))
    presentation = mission_presentation(MISSION_05_ID)
    assert presentation is not None
    assert presentation.talk_cue and presentation.dialogue_focus
    assert not presentation.lantern_waypoint
    assert not presentation.celebration and not presentation.discovery_label
    assert 'return f"Talk to {npc.character.name}"' in _read(TRAIL_PRESENTATION)

    slides = _flat(SLIDES)
    for required in (
        f"Talk to {guide['name']}",
        "same painted Moon Meadow as S04",
        "floating speech cue",
        "until it has said its final line",
        "speech bubble",
        "<strong>Moonlit Guide</strong> name tag",
        "<strong>Mission state</strong> row change to <strong>Complete</strong>",
        "starts again at line one, and M05 stays complete",
        "not today&rsquo;s target",
    ):
        assert required in slides, required
    card = _flat(TASK_CARD)
    assert "**Talk to Moonlit Guide**" in card
    assert "Read each line in the guide's speech bubble." in card


def test_s05_slides_do_not_describe_retired_unshipped_or_later_content():
    slides = _read(SLIDES).lower()
    for absent in (
        "rectangle",
        "plain trail",
        "standard trail",
        "confetti",
        "discovered!",
        "pixel",
        "compass clearing",
        "starlight",
        "sun seed",
        "rain bell",
        "wind flower",
        "breadcrumb",
        "collection",
    ):
        assert absent not in slides, absent


def test_s05_notes_name_their_real_course_kit_source_and_concepts():
    notes = _s05_learn_entry()
    assert 'sourceFile: "task-card.md"' in notes
    assert TASK_CARD.is_file()
    assert not (S05 / "student" / "python-notes.md").exists(), (
        "S05 now has python-notes.md; drop sourceFile so the Learn page points at it"
    )
    for required in (
        'term: "list"',
        'term: "index"',
        'term: "[-1]"',
        'term: "len(...)"',
        'term: "IndexError"',
        "python lessons/sessions/s05/student/starter.py",
        "conversation:",
        "Moonlit Guide",
    ):
        assert required in notes, required


def test_s04_and_s05_runbooks_tell_the_journey_in_order():
    s04 = _flat(PROJECT_ROOT / "lessons" / "sessions" / "s04" / "teacher-runbook.md")
    assert "opened in S03" not in s04
    assert "began with the S01 arrival in Moon Meadow" in s04
    assert "In S03 the Compass awakened and pointed toward the guide" in s04
    s05 = _flat(S05 / "teacher-runbook.md")
    assert "at the same spot as S04: in Moon Meadow, below Moonlit Ridge" in s05
