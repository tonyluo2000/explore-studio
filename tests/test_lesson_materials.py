from __future__ import annotations

import runpy
from pathlib import Path

import pytest

from explore.packages.loader import load_explorer_package

MATERIALS_ROOT = Path(__file__).parents[1] / "lessons" / "sessions"
SESSION_MISSIONS = {
    "s01": "visit-all-classroom-objects",
    "s02": "create-a-classroom-object",
    "s03": "make-your-object-respond",
    "s04": "introduce-your-character",
    "s05": "write-a-short-conversation",
}
REQUIRED_RUNBOOK_SECTIONS = (
    "Learning objective",
    "Prerequisite",
    "45-minute runbook",
    "Teacher cut line",
    "Student task",
    "prediction",
    "Deliberate debugging exercise",
    "Expected output and behavior",
    "Bounded AI assistance",
    "Git close",
    "Optional extension",
    "Teacher notes and answer key",
)
REQUIRED_TASK_CARD_CONTENT = (
    "Learning target",
    "Predict before running",
    "Core",
    "Checkpoint",
    "Support path",
    "Extension path",
    "AI receipt",
    "Git close",
    "Do not paste whole files or ask AI for a complete solution.",
)
EXPECTED_STARTER_OUTPUTS = {
    "s01": (
        "The crystal lantern glows beside the path.\n"
        "The river fountain sounds like quiet rain.\n"
        "Fern waits near the edge of the trail.\n"
    ),
    "s02": "Moon Compass\n240 180\npurple\n",
    "s03": "Moon Compass\nYou turn the Moon Compass toward a hidden trail!\n",
    "s04": "Welcome to TODO: name your setting, Ari!\n",
    "s05": "2\n",
}


@pytest.mark.parametrize(("session", "mission_id"), SESSION_MISSIONS.items())
def test_session_runbook_uses_v2_structure_and_canonical_mission(
    session: str, mission_id: str
) -> None:
    runbook = (MATERIALS_ROOT / session / "teacher-runbook.md").read_text(encoding="utf-8")

    assert mission_id in runbook
    assert "Clock anchor" in runbook
    assert "Range" in runbook
    assert "0:00–0:05" in runbook
    assert "0:42–0:45" in runbook
    assert "explain intent → predict → ask one bounded question → test →" in runbook
    assert "revise → explain accepted code" in runbook
    assert all(section.lower() in runbook.lower() for section in REQUIRED_RUNBOOK_SECTIONS)


@pytest.mark.parametrize("session", SESSION_MISSIONS)
def test_each_session_has_student_task_card(session: str) -> None:
    task_card = (MATERIALS_ROOT / session / "student" / "task-card.md").read_text(encoding="utf-8")

    assert all(item.lower() in task_card.lower() for item in REQUIRED_TASK_CARD_CONTENT)
    assert "../../student-quick-start.md" in task_card
    assert "git diff --staged" in task_card


def test_shared_quick_start_covers_setup_accessibility_ai_and_git() -> None:
    quick_start = (MATERIALS_ROOT / "student-quick-start.md").read_text(encoding="utf-8")

    required_setup = (
        "repository root",
        ".venv",
        "explore-package --help",
        "WASD",
        "arrow keys",
        "Press **E**",
        "keyboard focus",
        "Control-C",
        "Git knows your name and email",
        "screen sharing",
        "Accessibility and low-bandwidth route",
        "Common failures",
    )
    required_ai_receipt = (
        "Intent:",
        "Prediction:",
        "Exact bounded question:",
        "Suggestion tested:",
        "Accepted/rejected change:",
        "Student explanation:",
        "Do not paste whole files or ask AI for a complete solution.",
    )
    required_git = (
        "`M` means",
        "`??` means",
        "No output",
        "git diff --staged",
        "git config user.name",
        "git config user.email",
        "Control-C",
        "understanding",
    )

    assert all(item.lower() in quick_start.lower() for item in required_setup)
    assert all(item.lower() in quick_start.lower() for item in required_ai_receipt)
    assert all(item.lower() in quick_start.lower() for item in required_git)


def test_v2_index_documents_structure_timing_and_execution_boundary() -> None:
    index = (MATERIALS_ROOT / "README.md").read_text(encoding="utf-8")
    normalized_index = " ".join(index.split())

    assert "Session Materials v2" in index
    assert "task-card.md" in index
    assert "debug.py" in index
    assert "cut line" in index.lower()
    assert "finish the same descriptive commit after" in index
    assert "local Python value → declarative package field → visible world result" in index
    assert "never executed by the shared runtime" in normalized_index


@pytest.mark.parametrize(("session", "expected"), EXPECTED_STARTER_OUTPUTS.items())
def test_student_python_starter_remains_runnable(
    session: str, expected: str, capsys: pytest.CaptureFixture[str]
) -> None:
    runpy.run_path(str(MATERIALS_ROOT / session / "student" / "starter.py"))

    assert capsys.readouterr().out == expected


def test_later_starters_leave_meaningful_student_work() -> None:
    s03 = (MATERIALS_ROOT / "s03" / "student" / "starter.py").read_text(encoding="utf-8")
    s04 = (MATERIALS_ROOT / "s04" / "student" / "starter.py").read_text(encoding="utf-8")
    s05 = (MATERIALS_ROOT / "s05" / "student" / "starter.py").read_text(encoding="utf-8")

    assert 'near_message = f"{object_name}"' in s03
    assert "TODO" in s03
    assert "TODO: name your setting" in s04
    assert s04.count('greet("') == 1
    assert s05.count("TODO: write") == 2
    assert "dialogue[0]" not in s05
    assert "dialogue[-1]" not in s05


def test_session_specific_v2_support_is_present() -> None:
    s01 = (MATERIALS_ROOT / "s01" / "student" / "task-card.md").read_text(encoding="utf-8")
    s02 = (MATERIALS_ROOT / "s02" / "student" / "task-card.md").read_text(encoding="utf-8")
    s03 = (MATERIALS_ROOT / "s03" / "student" / "task-card.md").read_text(encoding="utf-8")
    s04_runbook = (MATERIALS_ROOT / "s04" / "teacher-runbook.md").read_text(encoding="utf-8")
    s05 = (MATERIALS_ROOT / "s05" / "student" / "task-card.md").read_text(encoding="utf-8")

    assert "first-day" in s01.lower()
    assert "Python value" in s02 and "YAML field" in s02 and "Visible world result" in s02
    assert "x = 80–800" in s02 and "y = 100–500" in s02
    assert all(item in s02 for item in ("Invalid color", "YAML indentation", "Off-screen"))
    assert "edit → predict → run → restore" in s03
    assert all(
        item in s04_runbook
        for item in (
            "Indentation",
            "Misspelled function name",
            "missing argument",
            "Traceback location",
        )
    )
    assert "0:12–0:28" in (MATERIALS_ROOT / "s05" / "teacher-runbook.md").read_text(
        encoding="utf-8"
    )
    assert all(item in s05 for item in ("Creative choice", "Python change", "Test run"))


@pytest.mark.parametrize("session", ("s02", "s03", "s04", "s05"))
def test_authored_session_package_is_valid(session: str) -> None:
    result = load_explorer_package(MATERIALS_ROOT / session / "student" / "explorer-package")

    assert result.is_loaded, result.all_issues


def test_no_s30_or_later_lesson_materials_exist() -> None:
    assert not any((MATERIALS_ROOT / f"s{number:02d}").exists() for number in range(30, 31))
