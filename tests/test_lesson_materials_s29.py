from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import yaml

from explore.curriculum.missions import MISSION_14_ID, MISSION_15_ID
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from explore.packages.loader import load_explorer_package
from lessons.sessions.s29.student import review_harness

PROJECT_ROOT = Path(__file__).parents[1]
MATERIALS_ROOT = PROJECT_ROOT / "lessons" / "sessions"
S29_ROOT = MATERIALS_ROOT / "s29"
STUDENT_ROOT = S29_ROOT / "student"
PACKAGE_ROOT = STUDENT_ROOT / "explorer-package"
FIXTURE_ROOT = STUDENT_ROOT / "review-fixtures"
LEARNER_TEST = STUDENT_ROOT / "test_review_harness.py"


def read_materials():
    runbook = (S29_ROOT / "teacher-runbook.md").read_text(encoding="utf-8")
    task = (STUDENT_ROOT / "task-card.md").read_text(encoding="utf-8")
    record = (STUDENT_ROOT / "project-record.md").read_text(encoding="utf-8")
    checklist = (STUDENT_ROOT / "review-checklist.md").read_text(encoding="utf-8")
    return runbook, task, record, checklist


def test_s29_identity_project_primary_structure_and_exact_rhythm():
    runbook, task, _, _ = read_materials()

    assert runbook.startswith("# S29 — Expedition Review")
    assert task.startswith("# S29 Task Card — Expedition Review")
    assert "**Role:** Project-primary production lesson" in runbook
    assert "**Role:** Project-primary production lesson" in task
    assert all(
        anchor in runbook
        for anchor in (
            "0:00–0:04",
            "0:04–0:09",
            "0:09–0:31",
            "0:31–0:38",
            "0:38–0:42",
            "0:42–0:45",
        )
    )
    assert all(
        path.exists()
        for path in (
            STUDENT_ROOT / "project-record.md",
            STUDENT_ROOT / "review_harness.py",
            STUDENT_ROOT / "review-checklist.md",
            LEARNER_TEST,
            PACKAGE_ROOT / "manifest.yaml",
        )
    )
    assert not (MATERIALS_ROOT / "s31").exists()


def test_s29_requires_student_review_and_risk_prediction_before_outside_feedback():
    runbook, task, record, _ = read_materials()
    normalized = " ".join((runbook + task + record).lower().split())

    assert "before any peer, teacher, or ai suggestion" in normalized
    assert "only after this student review" in normalized
    assert task.lower().index("before any peer, teacher, or ai") < task.lower().index(
        "## ai boundary"
    )
    assert all(
        phrase in normalized
        for phrase in (
            "annotate the current diff or code",
            "what could break",
            "which test or evidence would catch",
            "what output should stay identical",
            "timestamp/order evidence",
        )
    )


def test_s29_review_observations_are_evidence_linked_with_three_responses():
    runbook, task, record, checklist = read_materials()
    normalized = " ".join((runbook + task + record + checklist).lower().split())

    assert all(
        phrase in normalized
        for phrase in (
            "line/function/test",
            "observable behavior risk",
            "accept",
            "reject",
            "ask one clarification",
            "technical reason",
            "behavior to preserve",
            "regression evidence",
        )
    )
    assert "feedback never replaces the student's implementation wholesale" in normalized


def test_s29_requires_both_bounded_refactors_and_an_improved_name():
    runbook, task, record, _ = read_materials()
    normalized = " ".join((runbook + task + record).lower().split())

    assert "remove one duplicated record-shaping block" in normalized
    assert "split one confusing multi-purpose function" in normalized
    assert "improve at least one ambiguous variable or function name" in normalized
    assert "targeted regression test for each accepted" in normalized
    assert "do not introduce artificial defects" in normalized


def test_s29_prepared_example_is_separate_fixed_and_contains_only_practice_problems():
    runbook, task, _, _ = read_materials()
    example_path = FIXTURE_ROOT / "prepared_review_example.py"
    example = example_path.read_text(encoding="utf-8")
    tree = ast.parse(example)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    normalized = " ".join((runbook + task).lower().split())

    assert FIXTURE_ROOT != PACKAGE_ROOT
    assert (FIXTURE_ROOT / "cases.yaml").exists()
    assert (FIXTURE_ROOT / "expected-output.yaml").exists()
    assert "fixed and read-only" in normalized
    assert "separate" in normalized and "practice/support only" in normalized
    assert "cannot count as your real capstone work" in normalized
    assert all(name in functions for name in ("shape_records", "shape_enabled_records", "run"))
    assert example.count('"label": record["name"].strip()') == 2
    assert functions["run"].args.args[0].arg == "x"
    assert len(functions["run"].args.args) == 3
    assert "no replacement implementation is provided" in normalized


def test_s29_requires_before_after_deterministic_and_regression_evidence():
    runbook, task, record, checklist = read_materials()
    normalized = " ".join((runbook + task + record + checklist).lower().split())

    assert all(
        phrase in normalized
        for phrase in (
            "before-output",
            "after-output",
            "sha-256",
            "compare_snapshots",
            "deterministic package",
            "targeted regression",
            "package validates and plans",
            "no unexplained differences",
        )
    )


def test_s29_review_harness_is_read_only_deterministic_and_detects_delta(tmp_path):
    first = review_harness.snapshot_package()
    second = review_harness.snapshot_package()
    copied_root = tmp_path / "package"
    copied_root.mkdir()
    changed_file = copied_root / "only.yaml"
    changed_file.write_text("name: before\n", encoding="utf-8")
    before = review_harness.snapshot_package(copied_root)
    changed_file.write_text("name: after\n", encoding="utf-8")
    after = review_harness.snapshot_package(copied_root)

    assert first == second
    assert review_harness.compare_snapshots(first, second) == ()
    assert review_harness.compare_snapshots(before, after) == ("only.yaml",)
    source = (STUDENT_ROOT / "review_harness.py").read_text(encoding="utf-8")
    assert not any(token in source for token in ("unlink(", "rmtree(", "remove(", "write_text("))


def test_s29_visitor_walkthrough_maps_full_path_ownership_and_runtime_truth():
    runbook, task, record, checklist = read_materials()
    normalized = " ".join((runbook + task + record + checklist).lower().split())

    assert all(
        phrase in normalized
        for phrase in (
            "source input",
            "local python pipeline",
            "generated package files",
            "package validation",
            "trail",
            "m14 shared-style observation",
            "m15 sequence path",
            "where data changes shape",
            "module owns each responsibility",
            "runtime source of truth",
        )
    )


def test_s29_student_package_validates_plans_and_preserves_m14_m15():
    loaded = load_explorer_package(PACKAGE_ROOT)
    planned = plan_local_classroom_trail(
        (
            PROJECT_ROOT / "examples" / "explorer-packages" / "nova-character",
            PACKAGE_ROOT,
        ),
        player_qualified_id="nova-character:nova",
    )
    manifest = yaml.safe_load((PACKAGE_ROOT / "manifest.yaml").read_text())
    guide = yaml.safe_load((PACKAGE_ROOT / "character" / "sky-guide.yaml").read_text())

    assert loaded.is_loaded, loaded.all_issues
    assert planned.is_planned, planned.issues
    assert planned.plan is not None
    assert manifest["schema_version"] == "0.2"
    assert len(manifest["toggle_styles"]) == 1
    assert tuple(guide["respond_to_sequence"]["object_ids"]) == (
        "echo-lens",
        "wind-dial",
        "comet-bell",
    )
    assert create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_14_ID)
    assert create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_15_ID)


def test_s29_manual_smoke_checklist_covers_required_existing_behavior():
    _, task, record, checklist = read_materials()
    normalized = " ".join((task + record + checklist).lower().split())

    assert all(
        phrase in normalized
        for phrase in (
            "approach",
            "interaction",
            "observatory-glow",
            "echo lens → wind dial → comet bell",
            "wrong-member/reset",
            "clean exit",
            "teacher-run trail",
        )
    )


def test_s29_project_record_carries_decisions_evidence_and_lesson_without_task_duplication():
    _, task, record, _ = read_materials()

    assert all(
        heading in record
        for heading in (
            "Capstone state carried forward",
            "My review before outside feedback",
            "Review observations and responses",
            "Refactor 1 — duplication removal",
            "Refactor 2 — responsibility and naming",
            "Before/after deterministic evidence",
            "Validation, walkthrough, and manual smoke",
            "Review lesson and next step",
            "AI review receipt",
        )
    )
    assert "One lesson I learned from review" in record
    assert task.count("___") == 0
    assert record.count("___") >= 30


def test_s29_ai_boundary_is_max_two_diagnostic_review_only_after_student_review():
    runbook, task, record, _ = read_materials()
    normalized = " ".join((runbook + task + record).lower().split())

    assert "at most **two evidence-based review observations**" in (runbook + task).lower()
    assert "only after the student's own review" in normalized
    assert all(
        forbidden in normalized
        for forbidden in (
            "rewrite whole functions",
            "provide the final refactor",
            "replace peer/teacher review",
            "generate package contents",
            "change architecture",
            "propose new runtime features",
        )
    )
    assert "implements the change" in normalized or "implement changes yourself" in normalized


def test_s29_git_support_extension_cut_line_and_scope_boundaries():
    runbook, task, _, _ = read_materials()
    normalized = " ".join((runbook + task).lower().split())

    assert all(
        phrase in normalized
        for phrase in (
            "review notes / test evidence",
            "duplication-removal refactor",
            "responsibility/naming refactor",
            "final regression/smoke evidence",
            "no squash or rewrite requirement",
            "original reviewed state",
            "text diff",
            "printed before/after output",
            "teacher-run trail",
            "improve one test name or one user-facing validation/error message",
        )
    )
    assert "do not add s30 materials" in normalized
    assert "engine/schema/student api/trail/mission/ runtime behavior" in normalized
    assert "deployment, authentication, or phase e work" in normalized


def test_s29_focused_learner_suite_is_green_and_outside_default_collection():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(LEARNER_TEST)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "7 passed" in result.stdout
    assert LEARNER_TEST.parent != PROJECT_ROOT / "tests"
