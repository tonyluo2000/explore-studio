from __future__ import annotations

import ast
import runpy
from pathlib import Path

import pytest

from explore.packages.classroom_trail import plan_local_classroom_trail
from explore.packages.loader import load_explorer_package

PROJECT_ROOT = Path(__file__).parents[1]
MATERIALS_ROOT = PROJECT_ROOT / "lessons" / "sessions"
SESSION_TITLES_AND_ROLES = {
    "s16": ("Curator's Atlas", "Python-primary data fluency"),
    "s17": ("Clue Finder", "Python-primary data fluency"),
    "s18": ("Power Station Scoreboard", "Python-primary data fluency"),
    "s19": ("Route Planner", "Python-primary data fluency"),
    "s20": ("Data-Built Mystery Trail", "Balanced data-fluency milestone"),
}
EXPECTED_STARTER_OUTPUTS = {
    "s16": """1. Sun Dial [sun-dial] — gold
2. Rain Jar [rain-jar] — blue
3. Moss Map [moss-map] — green
""",
    "s17": """None
[]
0
""",
    "s18": """{'minimum': 0, 'maximum': 0, 'total': 0, 'average': 0.0}
None
False False False
""",
    "s19": """[]
[]
[]
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


@pytest.mark.parametrize(("session", "title_role"), SESSION_TITLES_AND_ROLES.items())
def test_s16_s20_use_v2_structure_exact_titles_and_roles(
    session: str, title_role: tuple[str, str]
) -> None:
    title, role = title_role
    session_root = MATERIALS_ROOT / session
    runbook = (session_root / "teacher-runbook.md").read_text(encoding="utf-8")
    task_card = (session_root / "student" / "task-card.md").read_text(encoding="utf-8")

    assert runbook.startswith(f"# {session.upper()} — {title}")
    assert f"**Role:** {role}" in task_card
    assert (session_root / "student" / "starter.py").is_file()
    assert "0:00–0:04" in runbook
    assert "0:04–0:10" in runbook
    assert "0:10–0:28" in runbook
    assert "0:28–0:35" in runbook
    assert "0:35–0:42" in runbook
    assert "0:42–0:45" in runbook
    assert all(item.lower() in runbook.lower() for item in REQUIRED_RUNBOOK_CONTENT)
    assert all(item.lower() in task_card.lower() for item in REQUIRED_TASK_CARD_CONTENT)
    assert "../../student-quick-start.md" in task_card


@pytest.mark.parametrize(("session", "expected"), EXPECTED_STARTER_OUTPUTS.items())
def test_s16_s19_starters_are_runnable_and_incomplete(
    session: str, expected: str, capsys: pytest.CaptureFixture[str]
) -> None:
    starter = MATERIALS_ROOT / session / "student" / "starter.py"
    source = starter.read_text(encoding="utf-8")

    assert "TODO" in source
    runpy.run_path(str(starter), run_name="__main__")
    assert capsys.readouterr().out == expected


def test_s20_starter_is_runnable_and_incomplete(capsys: pytest.CaptureFixture[str]) -> None:
    starter = MATERIALS_ROOT / "s20" / "student" / "starter.py"
    source = starter.read_text(encoding="utf-8")

    assert "TODO" in source
    assert "yaml.safe_load" in source
    assert "sort_keys=False" in source
    runpy.run_path(str(starter), run_name="__main__")
    output = capsys.readouterr().out
    assert "Selected 3 records" in output
    assert "Priority total: 6" in output
    assert "['sun-compass', 'whisper-stone', 'tide-chime']" in output


@pytest.mark.parametrize("session", SESSION_TITLES_AND_ROLES)
def test_s16_s20_keep_ai_git_access_and_runtime_boundaries(session: str) -> None:
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
    assert "understanding takes priority" in normalized
    assert (
        "python remains local" in normalized
        or "python and yaml file i/o remain local-only" in normalized
    )
    assert "validated yaml" in normalized or "validated declarative package data" in normalized
    assert "low bandwidth" in normalized


@pytest.mark.parametrize("session", SESSION_TITLES_AND_ROLES)
def test_s16_s20_packages_validate_and_plan_with_existing_runtime(session: str) -> None:
    package_root = MATERIALS_ROOT / session / "student" / "explorer-package"
    loaded = load_explorer_package(package_root)
    planned = plan_local_classroom_trail(
        (PROJECT_ROOT / "examples" / "explorer-packages" / "nova-character", package_root),
        player_qualified_id="nova-character:nova",
    )

    assert loaded.is_loaded, loaded.all_issues
    assert planned.is_planned, planned.issues


def test_s16_requires_two_traces_and_one_simple_noncomprehension_loop() -> None:
    student = MATERIALS_ROOT / "s16" / "student"
    starter_source = (student / "starter.py").read_text(encoding="utf-8")
    task_card = (student / "task-card.md").read_text(encoding="utf-8")
    debug_source = (student / "debug.py").read_text(encoding="utf-8")
    tree = ast.parse(starter_source)

    assert "first two iterations" in task_card.lower()
    assert len([node for node in ast.walk(tree) if isinstance(node, ast.For)]) == 1
    assert not any(
        isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))
        for node in ast.walk(tree)
    )
    assert "enumerate(" in starter_source
    assert all(
        phrase in debug_source for phrase in ("missing key", "duplicate ID", "incorrect nesting")
    )
    assert "Do not use comprehensions or nested loops" in task_card


def test_s17_students_own_search_filter_and_count_with_prediction_cases() -> None:
    student = MATERIALS_ROOT / "s17" / "student"
    starter_source = (student / "starter.py").read_text(encoding="utf-8")
    task_card = (student / "task-card.md").read_text(encoding="utf-8")
    tree = ast.parse(starter_source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    normalized = " ".join(task_card.split())

    assert set(functions) == {"find_by_id", "filter_by_color", "count_matching"}
    assert not any(
        isinstance(node, ast.For) for function in functions.values() for node in ast.walk(function)
    )
    assert all(
        phrase in normalized
        for phrase in ("no-match", "one-match", "multiple-match", "original order")
    )
    assert "AI may suggest one edge case only" in normalized


def test_s18_defines_empty_contract_statistics_ties_and_boundaries() -> None:
    student = MATERIALS_ROOT / "s18" / "student"
    starter_source = (student / "starter.py").read_text(encoding="utf-8")
    task_card = (student / "task-card.md").read_text(encoding="utf-8")

    assert "if not records:" in starter_source and "return None" in starter_source
    assert "`summarize_counts([])` returns **`None`**" in task_card
    assert all(name in task_card for name in ("min(counts)", "max(counts)", "sum(counts)"))
    assert "average" in task_card and "tied for maximum" in task_card
    assert all(case in task_card for case in ("below False", "exactly True", "above True"))


def test_s19_teaches_stable_sorted_copy_and_three_debug_cases() -> None:
    student = MATERIALS_ROOT / "s19" / "student"
    starter_source = (student / "starter.py").read_text(encoding="utf-8")
    task_card = (student / "task-card.md").read_text(encoding="utf-8")

    assert "nested" in task_card.lower() and "flatten" in task_card.lower()
    assert "sorted(records, key=lambda record:" in task_card
    assert "stable" in task_card.lower() and "equal keys" in task_card.lower()
    assert "does `flat_records` change?" in task_card
    assert all(
        phrase in task_card for phrase in ("Equal keys", "Missing priority", "Accidental mutation")
    )
    assert "TODO" in starter_source and "return list(records)" in starter_source
    assert "River Rune → Mist Bell → Star Lens" in task_card


def test_s20_pipeline_output_is_deterministic_valid_and_current_contract(tmp_path: Path) -> None:
    student = MATERIALS_ROOT / "s20" / "student"
    namespace = runpy.run_path(str(student / "starter.py"))
    plan = namespace["load_plan"](student / "mystery-plan.yaml")
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_order = namespace["build_package"](plan, first)
    second_order = namespace["build_package"](plan, second)
    first_files = {
        path.relative_to(first): path.read_bytes() for path in first.rglob("*") if path.is_file()
    }
    second_files = {
        path.relative_to(second): path.read_bytes() for path in second.rglob("*") if path.is_file()
    }

    assert [record["id"] for record in first_order] == [
        "sun-compass",
        "whisper-stone",
        "tide-chime",
    ]
    assert first_order == second_order
    assert first_files == second_files
    assert load_explorer_package(first).is_loaded
    assert b"schema_version: '0.1'" in first_files[Path("manifest.yaml")]


def test_s20_requires_trace_three_tests_validation_play_and_milestone_review() -> None:
    student = MATERIALS_ROOT / "s20" / "student"
    task_card = (student / "task-card.md").read_text(encoding="utf-8")
    starter_source = (student / "starter.py").read_text(encoding="utf-8")
    pipeline_tests = (student / "test_pipeline.py").read_text(encoding="utf-8")
    normalized = " ".join(task_card.split())

    assert all(stage in task_card for stage in ("input", "transformation", "output", "world"))
    assert all(
        case in task_card for case in ("Normal case", "Boundary case", "Malformed/invalid record")
    )
    assert all(
        test_name in pipeline_tests
        for test_name in ("test_normal_case", "test_boundary_case", "test_malformed_record")
    )
    assert "yaml.safe_load" in starter_source
    assert "validate" in normalized.lower() and "M15" in task_card
    assert all(
        phrase in task_card
        for phrase in (
            "Structured input safely loaded",
            "Search/aggregate/sort/transform",
            "Deterministic current-contract YAML",
            "Explorer Package validation passed",
            "Playable M15 sequence completed",
            "Transformation explanation",
            "Revision explanation",
        )
    )
    assert "AI may ask one pipeline question or propose one test only" in normalized


def test_no_s27_or_later_lesson_materials_exist() -> None:
    assert not any((MATERIALS_ROOT / f"s{number:02d}").exists() for number in range(27, 31))
