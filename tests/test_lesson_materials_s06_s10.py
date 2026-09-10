from __future__ import annotations

import runpy
from pathlib import Path

import pytest

from explore.packages.loader import load_explorer_package

MATERIALS_ROOT = Path(__file__).parents[1] / "lessons" / "sessions"
SESSION_MISSIONS = {
    "s06": "build-an-object-collection",
    "s07": "toggle-an-object-state",
    "s08": "respond-to-object-state",
    "s09": "count-object-interactions",
    "s10": "compare-a-counter-to-its-goal",
}
EXPECTED_STARTER_OUTPUTS = {
    "s06": """Sun Seed 180 180 gold
Rain Bell 380 300 blue
TODO: third garden object 620 420 green
""",
    "s07": "False blue\nFalse gold\n",
    "s08": "The portal is glowing!\nThe portal is sleeping.\n",
    "s09": "1 1\n2 2\n3 3\n",
    "s10": "False\nFalse\nFalse\n",
}
REQUIRED_RUNBOOK_CONTENT = (
    "Learning objective",
    "Prerequisite",
    "45-minute runbook",
    "Teacher cut line",
    "Student task and prediction",
    "Deliberate debugging exercise",
    "Expected output and behavior",
    "Bounded AI assistance",
    "Git close",
    "Optional extension",
    "Teacher notes and answer key",
)
REQUIRED_TASK_CARD_CONTENT = (
    "Learning target",
    "Predict",
    "Core",
    "Checkpoint",
    "Support path",
    "Extension path",
    "AI receipt",
    "Git close",
    "git diff --staged",
    "Do not paste whole files or ask AI for a complete solution.",
)


@pytest.mark.parametrize(("session", "mission_id"), SESSION_MISSIONS.items())
def test_s06_s10_use_v2_structure_and_canonical_mapping(session: str, mission_id: str) -> None:
    session_root = MATERIALS_ROOT / session
    runbook = (session_root / "teacher-runbook.md").read_text(encoding="utf-8")
    task_card = (session_root / "student" / "task-card.md").read_text(encoding="utf-8")

    assert (session_root / "student" / "starter.py").is_file()
    assert mission_id in runbook
    assert mission_id in task_card
    assert "Clock anchor" in runbook and "Range" in runbook
    assert "0:42–0:45" in runbook
    assert all(item.lower() in runbook.lower() for item in REQUIRED_RUNBOOK_CONTENT)
    assert all(item.lower() in task_card.lower() for item in REQUIRED_TASK_CARD_CONTENT)
    assert "../../student-quick-start.md" in task_card


@pytest.mark.parametrize(("session", "expected"), EXPECTED_STARTER_OUTPUTS.items())
def test_s06_s10_starters_are_incomplete_but_runnable(
    session: str, expected: str, capsys: pytest.CaptureFixture[str]
) -> None:
    starter = MATERIALS_ROOT / session / "student" / "starter.py"
    source = starter.read_text(encoding="utf-8")

    assert "TODO" in source
    runpy.run_path(str(starter))
    assert capsys.readouterr().out == expected


@pytest.mark.parametrize("session", SESSION_MISSIONS)
def test_s06_s10_keep_ai_and_git_boundaries(session: str) -> None:
    task_card = (MATERIALS_ROOT / session / "student" / "task-card.md").read_text(encoding="utf-8")
    normalized_task_card = " ".join(task_card.lower().split())

    assert all(
        field in normalized_task_card
        for field in (
            "intent",
            "prediction",
            "exact bounded question",
            "suggestion tested",
            "accepted/rejected change",
            "student explanation",
        )
    )
    assert "Understanding" in task_card


@pytest.mark.parametrize("session", SESSION_MISSIONS)
def test_s06_s10_student_packages_are_valid(session: str) -> None:
    result = load_explorer_package(MATERIALS_ROOT / session / "student" / "explorer-package")

    assert result.is_loaded, result.all_issues


def test_s06_has_three_records_one_loop_trace_and_valid_recovery_package() -> None:
    student = MATERIALS_ROOT / "s06" / "student"
    starter = (student / "starter.py").read_text(encoding="utf-8")
    task_card = (student / "task-card.md").read_text(encoding="utf-8")
    debug = (student / "debug.py").read_text(encoding="utf-8")
    recovery_result = load_explorer_package(student / "recovery-package")

    assert starter.count('{"name":') == 3
    assert starter.count("for ") == 1
    assert "first loop iteration" in task_card
    assert "Python debugging first" in task_card
    assert "Transfer table" in task_card
    assert "comprehension" in task_card and "nested loop" in task_card
    assert '"y"' not in debug.split("print(broken_record)", maxsplit=1)[0]
    assert recovery_result.is_loaded, recovery_result.all_issues


def test_s07_s09_required_reasoning_work_is_present() -> None:
    s07 = (MATERIALS_ROOT / "s07" / "student" / "task-card.md").read_text(encoding="utf-8")
    s08 = (MATERIALS_ROOT / "s08" / "student" / "task-card.md").read_text(encoding="utf-8")
    s09 = (MATERIALS_ROOT / "s09" / "student" / "task-card.md").read_text(encoding="utf-8")

    assert "After interaction 3" in s07
    assert "is_on = False" in (MATERIALS_ROOT / "s07" / "student" / "starter.py").read_text(
        encoding="utf-8"
    )
    assert "Predict both branches before execution" in s08
    assert "must not generate branch logic" in s08
    assert "exact interaction where success should first appear" in s09
    assert "assertion" in s09 and "off-by-one" in s09


def test_s10_requires_prediction_gate_function_and_three_assertions() -> None:
    session_root = MATERIALS_ROOT / "s10"
    starter = (session_root / "student" / "starter.py").read_text(encoding="utf-8")
    task_card = (session_root / "student" / "task-card.md").read_text(encoding="utf-8")
    runbook = (session_root / "teacher-runbook.md").read_text(encoding="utf-8")

    assert "def at_goal(count, goal):" in starter
    assert "goal - 1" in task_card and "goal + 1" in task_card
    assert "Prediction gate" in task_card
    assert "Write three assertions" in task_card
    normalized_task_card = " ".join(task_card.split())
    assert "Do not ask AI to generate a truth table" in normalized_task_card
    assert "AI may propose one edge case only after" in normalized_task_card
    assert "return count >= goal" in runbook
    assert all(item in task_card for item in ("Creative choice", "Python change", "Test run"))


def test_no_s28_or_later_lesson_materials_exist() -> None:
    assert not any((MATERIALS_ROOT / f"s{number:02d}").exists() for number in range(28, 31))
