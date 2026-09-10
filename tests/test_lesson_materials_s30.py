from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from explore.curriculum.missions import MISSION_16_ID
from explore.packages.classroom_trail import create_classroom_trail_scene
from lessons.sessions.s30.student import premiere_evidence

PROJECT_ROOT = Path(__file__).parents[1]
S30_ROOT = PROJECT_ROOT / "lessons" / "sessions" / "s30"
STUDENT_ROOT = S30_ROOT / "student"
PACKAGE_ROOT = STUDENT_ROOT / "explorer-package"
LEARNER_TEST = STUDENT_ROOT / "test_premiere_evidence.py"


def read_materials():
    return tuple(
        path.read_text(encoding="utf-8")
        for path in (
            S30_ROOT / "teacher-runbook.md",
            STUDENT_ROOT / "task-card.md",
            STUDENT_ROOT / "project-record.md",
            STUDENT_ROOT / "premiere-checklist.md",
        )
    )


def test_s30_identity_structure_and_exact_rhythm():
    runbook, task, _, _ = read_materials()

    assert runbook.startswith("# S30 — World Premiere")
    assert task.startswith("# S30 Task Card — World Premiere")
    assert "**Role:** Project-primary production lesson" in runbook
    assert all(
        anchor in runbook
        for anchor in (
            "0:00–0:05",
            "0:05–0:15",
            "0:15–0:25",
            "0:25–0:32",
            "0:32–0:41",
            "0:41–0:45",
        )
    )
    assert all(
        path.exists()
        for path in (
            STUDENT_ROOT / "project-record.md",
            STUDENT_ROOT / "premiere-checklist.md",
            STUDENT_ROOT / "premiere_evidence.py",
            LEARNER_TEST,
            PACKAGE_ROOT / "manifest.yaml",
        )
    )


def test_s30_requires_final_tests_validation_two_exports_and_recovery():
    normalized = " ".join(" ".join(read_materials()).lower().split())

    assert all(
        phrase in normalized
        for phrase in (
            "normal, boundary, invalid, and regression",
            "package validation",
            "two fresh",
            "identical",
            "sha-256",
            "raw bytes",
            "one likely failure",
            "one bounded correction",
            "rerun the exact failed check",
            "resume at a named point",
        )
    )


def test_s30_requires_synthesis_algorithm_and_authorship_explanation():
    runbook, task, record, _ = read_materials()
    normalized = " ".join((runbook + task + record).lower().split())

    assert "at least two meaningful search" in normalized
    assert all(
        phrase in normalized
        for phrase in (
            "input/output shapes",
            "intermediate state",
            "stable ordering",
            "boundary behavior",
            "runtime consumes validated declarative yaml",
            "debugging or refactoring story",
            "every accepted line",
            "all accepted ai assistance",
        )
    )


def test_s30_evidence_harness_validates_plans_m16_and_exports_identically(tmp_path):
    evidence = premiere_evidence.collect_premiere_evidence(tmp_path / "exports")

    assert evidence.mission_id == MISSION_16_ID
    assert evidence.exports_match
    assert evidence.first_sha256 == evidence.second_sha256
    assert evidence.member_paths[0] == "manifest.yaml"
    assert len(evidence.world_object_ids) == 3


def test_s30_package_supports_existing_m14_m15_and_m16():
    loaded, planned = _load_and_plan()

    assert loaded.is_loaded
    assert planned.is_planned and planned.plan is not None
    assert len(loaded.package.toggle_style_uses) == 1
    guide = loaded.package.characters[0]
    assert guide.respond_to_sequence is not None
    assert create_classroom_trail_scene(object(), planned.plan, mission_id=MISSION_16_ID)


def _load_and_plan():
    from explore.packages.classroom_trail import plan_local_classroom_trail
    from explore.packages.loader import load_explorer_package

    loaded = load_explorer_package(PACKAGE_ROOT)
    planned = plan_local_classroom_trail(
        (premiere_evidence.PLAYER_PACKAGE_ROOT, PACKAGE_ROOT),
        player_qualified_id=premiere_evidence.PLAYER_ID,
    )
    return loaded, planned


def test_s30_m16_completion_is_explicitly_not_mastery_or_release():
    normalized = " ".join(" ".join(read_materials()).lower().split())

    assert "complete means only that the guided object tour is complete" in normalized
    assert all(
        phrase in normalized
        for phrase in (
            "python quality",
            "presentation quality",
            "teacher rubric",
            "approval",
            "publication",
            "release",
        )
    )


def test_s30_ai_is_limited_to_two_questions_without_answers_or_repairs():
    normalized = " ".join(" ".join(read_materials()).lower().split())

    assert "at most **two rehearsal questions only**" in normalized
    assert "after the student's own script" in normalized
    assert all(
        phrase in normalized
        for phrase in (
            "may not answer for the student",
            "rewrite code",
            "generate the presentation or package",
            "repair failures",
            "invent evidence",
            "add features",
        )
    )


def test_s30_scope_git_access_and_publication_boundaries():
    normalized = " ".join(" ".join(read_materials()).lower().split())

    assert "status → diff → staged diff" in normalized
    assert "optional tag stays local" in normalized
    assert "commit ≠ export ≠ publish ≠ approve ≠ release" in normalized
    assert "teacher-operated trail" in normalized
    assert "adds no s31 materials" in normalized
    assert "engine/schema/student api/trail/mission/runtime behavior" in normalized
    assert "publication, deployment, authentication, or phase e work" in normalized


def test_s30_project_record_holds_receipts_without_task_card_blanks():
    _, task, record, checklist = read_materials()

    assert all(
        heading in record
        for heading in (
            "Final reviewed state",
            "Technical explanation",
            "Final test and package receipt",
            "Demonstration script",
            "Recovery rehearsal",
            "Engineering story and authorship",
            "AI assistance receipt",
            "Final review close",
        )
    )
    assert task.count("___") == 0
    assert record.count("___") >= 30
    assert checklist.count("___") == 5


def test_s30_focused_learner_suite_is_green_and_outside_default_collection():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(LEARNER_TEST)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "4 passed" in result.stdout
    assert LEARNER_TEST.parent != PROJECT_ROOT / "tests"


def test_s30_invalid_evidence_path_fails_closed_before_outputs(tmp_path):
    broken = tmp_path / "broken"
    broken.mkdir()
    output = tmp_path / "exports"

    with pytest.raises(premiere_evidence.PremiereEvidenceError, match="validation failed"):
        premiere_evidence.collect_premiere_evidence(output, broken)

    assert not output.exists()
