from __future__ import annotations

import runpy
from pathlib import Path

import pytest

from explore.packages.classroom_trail import plan_local_classroom_trail
from explore.packages.loader import load_explorer_package

PROJECT_ROOT = Path(__file__).parents[1]
MATERIALS_ROOT = PROJECT_ROOT / "lessons" / "sessions"
SESSIONS = {
    "s21": ("Package Gatekeeper", "build-an-object-collection"),
    "s22": ("Traceback Detective", "respond-to-object-state"),
    "s23": ("Builder's Workshop", "reuse-a-named-toggle-style"),
    "s24": ("Fast Ranger Index", "complete-actions-in-order"),
}
RUNBOOK_SECTIONS = (
    "Learning objective",
    "Prerequisite",
    "Before class",
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
TASK_SECTIONS = (
    "Learning target",
    "Predict",
    "Core Python",
    "World payoff",
    "Support path",
    "Extension path",
    "Required evidence/checkpoints",
    "AI receipt",
    "Git close",
)


@pytest.mark.parametrize(("session", "title_mission"), SESSIONS.items())
def test_s21_s24_use_v2_structure_titles_and_existing_world_goals(
    session: str, title_mission: tuple[str, str]
) -> None:
    title, mission = title_mission
    session_root = MATERIALS_ROOT / session
    runbook = (session_root / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (session_root / "student" / "task-card.md").read_text(encoding="utf-8")
    starter = session_root / "student" / "starter.py"

    assert runbook.startswith(f"# {session.upper()} — {title}")
    assert task.startswith(f"# {session.upper()} Task Card — {title}")
    assert "**Role:** Python-primary software fluency" in task
    assert mission in task
    assert starter.is_file()
    assert "TODO" in starter.read_text(encoding="utf-8")
    assert all(section.lower() in runbook.lower() for section in RUNBOOK_SECTIONS)
    assert all(section.lower() in task.lower() for section in TASK_SECTIONS)
    assert "../../student-quick-start.md" in task
    assert all(anchor in runbook for anchor in ("0:00–0:04", "0:04–0:10", "0:10–0:28"))
    assert all(anchor in runbook for anchor in ("0:28–0:35", "0:35–0:42", "0:42–0:45"))


@pytest.mark.parametrize("session", SESSIONS)
def test_s21_s24_keep_ai_git_accessibility_and_runtime_boundaries(session: str) -> None:
    task = (MATERIALS_ROOT / session / "student" / "task-card.md").read_text(encoding="utf-8")
    normalized = " ".join(task.lower().split())

    assert all(
        field in normalized
        for field in (
            "intent",
            "prediction",
            "exact bounded question",
            "suggestion tested",
            "accepted/rejected change",
            "student explanation",
        )
    )
    assert "do not paste whole files or ask ai for a complete solution." in normalized
    assert "git diff --staged" in task
    assert all(item in normalized for item in ("`m`", "`??`", "no output", "identity"))
    assert "cancel/correct/retry" in normalized
    assert "understanding takes priority" in normalized
    assert "low bandwidth" in normalized
    assert (
        "python remains local" in normalized
        or "python and yaml file i/o remain local-only" in normalized
    )
    assert "validated declarative" in normalized


@pytest.mark.parametrize("session", SESSIONS)
def test_s21_s24_packages_validate_and_plan_with_existing_runtime(session: str) -> None:
    package_root = MATERIALS_ROOT / session / "student" / "explorer-package"
    loaded = load_explorer_package(package_root)
    plan = plan_local_classroom_trail(
        (PROJECT_ROOT / "examples" / "explorer-packages" / "nova-character", package_root),
        player_qualified_id="nova-character:nova",
    )

    assert loaded.is_loaded, loaded.all_issues
    assert plan.is_planned, plan.issues


def test_s21_returns_ordered_diagnostics_and_invalid_package_fails_closed() -> None:
    student = MATERIALS_ROOT / "s21" / "student"
    namespace = runpy.run_path(str(student / "starter.py"))
    validate_records = namespace["validate_records"]
    malformed = namespace["CASES"][1]

    assert validate_records(malformed[1]) == malformed[2]
    assert validate_records(["not-a-record"]) == ["record 1: expected a dictionary"]
    invalid = load_explorer_package(student / "invalid-package")
    assert not invalid.is_loaded
    assert any(issue.code.value == "FILE_MISSING" for issue in invalid.all_issues)

    task = (student / "task-card.md").read_text(encoding="utf-8")
    normalized = " ".join(task.split())
    assert all(
        phrase in task
        for phrase in ("missing fields", "wrong types", "invalid ranges", "duplicate ID")
    )
    assert "AI may supply at most one malformed example" in normalized
    assert "generic validation framework" in normalized


@pytest.mark.parametrize(
    ("session", "expected_output"),
    (
        ("s21", "valid []"),
        ("s22", "3 regression checks pass"),
        ("s23", "--- manifest.yaml ---"),
        ("s24", "small: (15, 6"),
    ),
)
def test_s21_s24_starters_are_runnable_and_incomplete(
    session: str, expected_output: str, capsys: pytest.CaptureFixture[str]
) -> None:
    starter = MATERIALS_ROOT / session / "student" / "starter.py"

    runpy.run_path(str(starter), run_name="__main__")

    assert expected_output in capsys.readouterr().out
    assert "TODO" in starter.read_text(encoding="utf-8")


def test_s22_prepares_three_failures_and_requires_full_regression_workflow() -> None:
    student = MATERIALS_ROOT / "s22" / "student"
    debug = runpy.run_path(str(student / "debug.py"))
    task = (student / "task-card.md").read_text(encoding="utf-8")

    with pytest.raises(KeyError):
        debug["run_prepared_failure"]("key-error")
    with pytest.raises(IndexError):
        debug["run_prepared_failure"]("off-by-one")
    with pytest.raises(AssertionError):
        debug["run_prepared_failure"]("incorrect-return")

    normalized = " ".join(task.lower().split())
    assert all(item in task for item in ("`KeyError`", "`IndexError`", "incorrect-return"))
    assert "first relevant student-code frame" in normalized
    assert all(step in normalized for step in ("reproduce", "predict", "one change", "rerun"))
    assert "regression assertion" in normalized
    assert "one hint at a time only after you interpret the traceback" in normalized


def test_s23_requires_design_then_exact_behavior_preserving_modular_refactor() -> None:
    student = MATERIALS_ROOT / "s23" / "student"
    namespace = runpy.run_path(str(student / "starter.py"))
    expected = (student / "expected-output.txt").read_text(encoding="utf-8")
    task = (student / "task-card.md").read_text(encoding="utf-8")

    assert namespace["pipeline_text"]() == expected
    assert all((student / name).is_file() for name in ("data_io.py", "rules.py", "build_output.py"))
    assert all(
        phrase in task
        for phrase in (
            "call/data flow",
            "data I/O",
            "validation/rules",
            "build/output",
            "exact-output regression",
            "M14 reuse analogy",
            "behavior-preserving refactor",
        )
    )
    assert "Do not add classes" in task
    assert "only after you identify a candidate" in task


def test_s24_counts_inspections_rejects_duplicates_and_preserves_results() -> None:
    student = MATERIALS_ROOT / "s24" / "student"
    namespace = runpy.run_path(str(student / "starter.py"))
    task = (student / "task-card.md").read_text(encoding="utf-8")

    assert namespace["compare"](6) == (15, 6, ["clue-4", "clue-5", "clue-6"])
    assert namespace["compare"](12) == (33, 12, ["clue-10", "clue-11", "clue-12"])
    duplicate = [{"id": "same"}, {"id": "same"}]
    with pytest.raises(ValueError, match="duplicate id"):
        namespace["build_id_index"](duplicate)

    normalized = " ".join(task.lower().split())
    assert "count inspected records, not seconds" in normalized
    assert "what happens to each count when the data doubles" in normalized
    assert "assert scanned == indexed" in task
    assert "no big-o notation is required" in normalized
    assert "do not create a runtime index/cache feature" in normalized


def test_no_s28_or_later_lesson_materials_exist() -> None:
    assert not any((MATERIALS_ROOT / f"s{number:02d}").exists() for number in range(28, 31))
