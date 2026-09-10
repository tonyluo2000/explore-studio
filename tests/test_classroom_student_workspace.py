from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.provision_student_workspace import (
    COURSE_PLATFORM_COMMIT,
    EXAMPLE_PACKAGE_IDS,
    REHEARSAL_RECORD,
    SESSION_IDS,
    ProvisionError,
    provision_student_workspace,
)

PROJECT_ROOT = Path(__file__).parents[1]


def unresolved_local_links(documents: list[Path]) -> list[tuple[Path, str]]:
    missing = []
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for link in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text):
            relative = link.split("#", 1)[0]
            if (
                relative
                and not relative.startswith(("http://", "https://", "mailto:"))
                and not (document.parent / relative).resolve().exists()
            ):
                missing.append((document, relative))
    return missing


def make_template(target: Path) -> Path:
    (target / ".git").mkdir(parents=True)
    (target / "explorer-package").mkdir()
    (target / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (target / "requirements-dev.txt").write_text("template pin\n", encoding="utf-8")
    (target / "explorer-package" / "manifest.yaml").write_text(
        'schema_version: "0.1"\n', encoding="utf-8"
    )
    return target


def test_provisioned_workspace_has_every_student_path_without_teacher_source(tmp_path):
    target = make_template(tmp_path / "student")

    receipt = provision_student_workspace(target, PROJECT_ROOT)

    assert receipt["course_platform_commit"] == COURSE_PLATFORM_COMMIT
    assert len(receipt["course_materials_source_commit"]) == 40
    assert receipt["sessions"] == [1, 30]
    for session_id in SESSION_IDS:
        student_root = target / "lessons" / "sessions" / session_id / "student"
        assert (student_root / "task-card.md").is_file()
        assert not (target / "lessons" / "sessions" / session_id / "teacher-runbook.md").exists()
    assert not (target / "lessons" / "sessions" / "s31").exists()
    assert not (target / "explore").exists()
    assert not (target / "engine").exists()


def test_provisioned_workspace_has_exact_course_pin_examples_and_receipt(tmp_path):
    target = make_template(tmp_path / "student")

    provision_student_workspace(target, PROJECT_ROOT)

    requirements = (target / "requirements-course.txt").read_text(encoding="utf-8")
    assert f"explore-studio.git@{COURSE_PLATFORM_COMMIT}" in requirements
    assert "-e .[dev]" in requirements
    for package_id in EXAMPLE_PACKAGE_IDS:
        assert (target / "examples" / "explorer-packages" / package_id / "manifest.yaml").is_file()
    receipt = json.loads((target / "course-materials.json").read_text(encoding="utf-8"))
    assert receipt["course_platform_commit"] == COURSE_PLATFORM_COMMIT
    assert (target / "docs" / "classroom-student-workspace.md").is_file()
    assert (target / "docs" / REHEARSAL_RECORD).is_file()


def test_all_student_task_card_local_links_and_course_paths_resolve(tmp_path):
    target = make_template(tmp_path / "student")
    provision_student_workspace(target, PROJECT_ROOT)

    task_cards = list((target / "lessons" / "sessions").glob("s*/student/task-card.md"))
    missing = unresolved_local_links(task_cards)
    for task_card in task_cards:
        text = task_card.read_text(encoding="utf-8")
        for path_text in re.findall(
            r"(?:lessons/sessions/s\d{2}/student|examples/explorer-packages)/[a-zA-Z0-9_./-]+",
            text,
        ):
            cleaned = path_text.rstrip(".,`)")
            if not (target / cleaned).exists():
                missing.append((task_card, cleaned))
    assert missing == []


def test_provisioned_student_facing_document_links_resolve(tmp_path):
    target = make_template(tmp_path / "student")
    provision_student_workspace(target, PROJECT_ROOT)

    documents = [
        target / "lessons" / "sessions" / "student-quick-start.md",
        target / "lessons" / "sessions" / "README.md",
        target / "docs" / "classroom-student-workspace.md",
    ]
    assert unresolved_local_links(documents) == []


def test_provisioning_refuses_non_template_or_existing_overlay_without_partial_copy(tmp_path):
    missing_marker = tmp_path / "not-template"
    missing_marker.mkdir()
    with pytest.raises(ProvisionError, match="student Git repository"):
        provision_student_workspace(missing_marker, PROJECT_ROOT)
    assert not (missing_marker / "lessons").exists()

    target = make_template(tmp_path / "student")
    provision_student_workspace(target, PROJECT_ROOT)
    with pytest.raises(ProvisionError, match="already contains course path"):
        provision_student_workspace(target, PROJECT_ROOT)


def test_readiness_docs_use_canonical_cli_windows_and_completed_course_status():
    quick_start = (PROJECT_ROOT / "lessons" / "sessions" / "student-quick-start.md").read_text()
    session_index = (PROJECT_ROOT / "lessons" / "sessions" / "README.md").read_text()
    s30 = (PROJECT_ROOT / "lessons" / "sessions" / "s30" / "student" / "task-card.md").read_text()
    roadmap = (PROJECT_ROOT / "docs" / "roadmap.md").read_text()
    setup = (PROJECT_ROOT / "docs" / "classroom-student-workspace.md").read_text()
    rehearsal = (
        PROJECT_ROOT / "docs" / "operations" / "s01-clean-rehearsal-2026-09-10.md"
    ).read_text()

    assert "derived student repository" in quick_start.lower()
    assert "requirements-course.txt" in quick_start
    assert "WSL 2" in quick_start and "native powershell" in quick_start.lower()
    assert "S29–S30" in session_index and "review/evidence harnesses" in session_index
    assert "--mission-id present-your-capstone-expedition" in s30
    assert "--mission present-your-capstone-expedition" not in s30
    assert "S01–S30 course materials complete" in roadmap
    assert "student-adventure-template" in setup
    assert "teacher runbooks" in setup
    assert "1 passed in 16.14s" in rehearsal
    assert COURSE_PLATFORM_COMMIT in rehearsal
    assert "--mission-id visit-all-classroom-objects" in rehearsal
