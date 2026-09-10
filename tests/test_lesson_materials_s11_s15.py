from __future__ import annotations

import runpy
from pathlib import Path

import pytest
import yaml

from explore.packages.classroom_trail import plan_local_classroom_trail
from explore.packages.loader import load_explorer_package

MATERIALS_ROOT = Path(__file__).parents[1] / "lessons" / "sessions"
SESSION_MISSIONS = {
    "s11": "require-all-switches-on",
    "s12": "open-with-either-switch",
    "s13": "invert-a-switch-condition",
    "s14": "reuse-a-named-toggle-style",
    "s15": "complete-actions-in-order",
}
EXPECTED_STARTER_OUTPUTS = {
    "s11": """False False False
False True False
True False True
True True True
""",
    "s12": """False False False
False True False
True False False
True True True
""",
    "s13": """False False
True True
""",
    "s15": """True
0
0
0
""",
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
    "Required evidence/checkpoints",
    "AI receipt",
    "Git close",
    "git diff --staged",
    "Do not paste whole files or ask AI for a complete solution.",
)


@pytest.mark.parametrize(("session", "mission_id"), SESSION_MISSIONS.items())
def test_s11_s15_use_v2_structure_and_canonical_mapping(session: str, mission_id: str) -> None:
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
def test_python_primary_starters_are_incomplete_but_runnable(
    session: str, expected: str, capsys: pytest.CaptureFixture[str]
) -> None:
    starter = MATERIALS_ROOT / session / "student" / "starter.py"
    source = starter.read_text(encoding="utf-8")

    assert "TODO" in source
    runpy.run_path(str(starter))
    assert capsys.readouterr().out == expected


def test_s14_balanced_starter_is_incomplete_and_runnable(
    capsys: pytest.CaptureFixture[str],
) -> None:
    starter = MATERIALS_ROOT / "s14" / "student" / "starter.py"
    source = starter.read_text(encoding="utf-8")

    assert "TODO" in source
    assert source.count("build_switch(") == 3
    assert "shared_style" in source
    runpy.run_path(str(starter))
    output = capsys.readouterr().out
    assert "North Beacon" in output and "South Beacon" in output


@pytest.mark.parametrize("session", SESSION_MISSIONS)
def test_s11_s15_keep_ai_git_and_local_runtime_boundaries(session: str) -> None:
    task_card = (MATERIALS_ROOT / session / "student" / "task-card.md").read_text(encoding="utf-8")
    normalized = " ".join(task_card.lower().split())

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
    assert "Understanding" in task_card
    assert "validated yaml" in normalized
    assert "python remains local" in normalized


@pytest.mark.parametrize("session", SESSION_MISSIONS)
def test_s11_s15_student_packages_are_valid(session: str) -> None:
    result = load_explorer_package(MATERIALS_ROOT / session / "student" / "explorer-package")

    assert result.is_loaded, result.all_issues


def test_boolean_prediction_gates_and_session_differentiation() -> None:
    s11 = (MATERIALS_ROOT / "s11" / "student" / "task-card.md").read_text(encoding="utf-8")
    s12 = (MATERIALS_ROOT / "s12" / "student" / "task-card.md").read_text(encoding="utf-8")
    s13 = (MATERIALS_ROOT / "s13" / "student" / "task-card.md").read_text(encoding="utf-8")

    normalized_s11 = " ".join(s11.split())
    assert s11.count("| False |") >= 2 and s11.count("| True |") >= 2
    assert "all conditions must be true" in s11
    assert "Do not add an `if`/`else`" in normalized_s11
    assert s12.count("| False |") >= 2 and s12.count("| True |") >= 2
    assert "any condition may be true" in s12
    assert "S11 AND" in s12 and "same/different" in s12
    assert "not is_on" in s13 and "both rows" in s13
    assert "not general `not` syntax" in s13
    assert "vault" in s11.lower()
    assert "rescue" in s12.lower()
    assert "moonflower" in s13.lower()


def test_boolean_ai_boundaries_follow_student_reasoning() -> None:
    s11 = (MATERIALS_ROOT / "s11" / "student" / "task-card.md").read_text(encoding="utf-8")
    s12 = (MATERIALS_ROOT / "s12" / "student" / "task-card.md").read_text(encoding="utf-8")
    s13 = (MATERIALS_ROOT / "s13" / "student" / "task-card.md").read_text(encoding="utf-8")

    assert "completed truth table only after your prediction" in " ".join(s11.split())
    assert "one mismatch you selected only after" in " ".join(s12.split())
    assert "challenge your explanation after you write it" in " ".join(s13.split())


def test_s14_requires_duplication_before_refactor_and_one_shared_style() -> None:
    student = MATERIALS_ROOT / "s14" / "student"
    task_card = (student / "task-card.md").read_text(encoding="utf-8")
    manifest = yaml.safe_load((student / "explorer-package" / "manifest.yaml").read_text())
    objects = [
        yaml.safe_load(path.read_text())
        for path in sorted((student / "explorer-package" / "objects").glob("*.yaml"))
    ]

    assert "identify duplication before refactoring" in task_card.lower()
    assert "one style dictionary is\n   reused by two calls" in task_card
    assert "Python → shared style → two world objects" in task_card
    assert "inline/reference conflict" in task_card
    assert len(manifest["toggle_styles"]) == 1
    style_id = manifest["toggle_styles"][0]["id"]
    assert [item["toggle_style_id"] for item in objects] == [style_id, style_id]


def test_s15_materials_match_sequence_reset_semantics_and_capstone_requirements() -> None:
    session = MATERIALS_ROOT / "s15"
    task_card = (session / "student" / "task-card.md").read_text(encoding="utf-8")
    runbook = (session / "teacher-runbook.md").read_text(encoding="utf-8")
    starter = (session / "student" / "starter.py").read_text(encoding="utf-8")
    manifest = yaml.safe_load(
        (session / "student" / "explorer-package" / "manifest.yaml").read_text()
    )
    sequence = yaml.safe_load(
        (
            session / "student" / "explorer-package" / "character" / "sequence-keeper.yaml"
        ).read_text()
    )["respond_to_sequence"]["object_ids"]

    assert "has_three_distinct_ids" in starter
    assert "def compare_order(expected_ids, attempted_ids):" in starter
    assert "TODO: write a normal-case assertion" in starter
    assert "TODO: add an assertion" in starter
    assert "assert compare_order(expected, expected) == 3" in runbook
    assert 'compare_order(expected, ["star-map", "echo-drum"]) == 0' in runbook
    assert all(
        phrase in task_card
        for phrase in (
            "Correct sequence",
            "Wrong authored member reset",
            "Unrelated-object interaction",
            "not immediately",
            "leaves progress unchanged",
            "First-half capstone checklist",
            "Creative choice",
            "Python change",
            "Test run",
            "60 seconds",
        )
    )
    assert sequence == ["star-map", "moon-switch", "echo-drum"]
    contribution_ids = [item["id"] for item in manifest["contributions"]]
    assert all(object_id in contribution_ids for object_id in sequence)
    object_paths = (session / "student" / "explorer-package" / "objects").glob("*.yaml")
    object_text = " ".join(path.read_text() for path in object_paths)
    assert "toggle:" in object_text and "counter:" in object_text
    assert "AI may suggest tests only" in " ".join(task_card.split())


def test_s15_documented_launch_roots_include_unrelated_crystal_lantern() -> None:
    project_root = MATERIALS_ROOT.parents[1]
    task_card = (MATERIALS_ROOT / "s15" / "student" / "task-card.md").read_text(encoding="utf-8")
    runbook = (MATERIALS_ROOT / "s15" / "teacher-runbook.md").read_text(encoding="utf-8")
    documented_roots = (
        "examples/explorer-packages/nova-character",
        "examples/explorer-packages/crystal-lantern",
        "lessons/sessions/s15/student/explorer-package",
    )

    assert all(root in task_card and root in runbook for root in documented_roots)
    planned = plan_local_classroom_trail(
        (project_root / root for root in documented_roots),
        player_qualified_id="nova-character:nova",
    )

    assert planned.is_planned, planned.issues
    assert planned.plan is not None
    qualified_object_ids = {item.qualified_id for item in planned.plan.world_objects}
    assert "crystal-lantern:lantern" in qualified_object_ids
    assert {
        "star-song-sequence:star-map",
        "star-song-sequence:moon-switch",
        "star-song-sequence:echo-drum",
    } <= qualified_object_ids


def test_no_s29_or_later_lesson_materials_exist() -> None:
    assert not any((MATERIALS_ROOT / f"s{number:02d}").exists() for number in range(29, 31))
