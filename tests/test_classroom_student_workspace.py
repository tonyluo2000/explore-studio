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
    STUDENT_GITIGNORE_RULE,
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
    (target / ".gitignore").write_text(".venv/\n", encoding="utf-8")
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
    assert STUDENT_GITIGNORE_RULE in (target / ".gitignore").read_text().splitlines()


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
    s01_runbook = (PROJECT_ROOT / "lessons" / "sessions" / "s01" / "teacher-runbook.md").read_text()
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
    assert "Python 3.11" in setup and "git --version" in setup
    assert "Zoom desktop client" in setup and "private channel" in setup
    assert "screen sharing" in setup and "actual class meeting" in setup
    assert "clean-Mac and Zoom preflight" in s01_runbook
    assert "1 passed in 16.14s" in rehearsal
    assert COURSE_PLATFORM_COMMIT in rehearsal
    assert "--mission-id visit-all-classroom-objects" in rehearsal


def test_s01_onboarding_does_not_require_git_or_github():
    sessions = PROJECT_ROOT / "lessons" / "sessions"
    task_card = (sessions / "s01" / "student" / "task-card.md").read_text(encoding="utf-8")
    runbook = (sessions / "s01" / "teacher-runbook.md").read_text(encoding="utf-8")
    quick_start = (sessions / "student-quick-start.md").read_text(encoding="utf-8")

    assert "You do not need Git or a GitHub account for this session." in task_card
    assert "## Git close" not in task_card
    assert "git add lessons/sessions/s01/student/starter.py" not in task_card
    assert "No Git client, GitHub account, or clone is required" in runbook
    assert "Git identity is not part of S01" in runbook
    assert "not an S01 prerequisite" in runbook
    assert "do **not** need a GitHub account" in quick_start
    assert "Git identity is not part of this checklist." in quick_start
    assert "## Later: Git (optional, teacher-managed)" in quick_start
    assert "**It is not\nrequired for S01**" in quick_start


def test_s01_keeps_its_learning_objective_and_m01_trail_behavior():
    sessions = PROJECT_ROOT / "lessons" / "sessions"
    task_card = (sessions / "s01" / "student" / "task-card.md").read_text(encoding="utf-8")
    runbook = (sessions / "s01" / "teacher-runbook.md").read_text(encoding="utf-8")
    starter = (sessions / "s01" / "student" / "starter.py").read_text(encoding="utf-8")

    assert "M01 `visit-all-classroom-objects`" in task_card
    assert '--mission-id "visit-all-classroom-objects"' in task_card
    assert "Keep exactly three" in task_card and "`print(...)` calls." in task_card
    assert starter.count("print(") == 3
    assert "matching quotation marks to record three observations" in runbook
    assert "`Visited 2 / 2`" in runbook


def test_s01_onboarding_directs_students_through_the_computer_check():
    sessions = PROJECT_ROOT / "lessons" / "sessions"
    task_card = (sessions / "s01" / "student" / "task-card.md").read_text(encoding="utf-8")
    quick_start = (sessions / "student-quick-start.md").read_text(encoding="utf-8")
    start_here = (PROJECT_ROOT / "classroom" / "START-HERE.md").read_text(encoding="utf-8")

    assert "python3 check-my-computer.py" in task_card
    assert "python3 check-my-computer.py" in quick_start
    assert "python3 check-my-computer.py" in start_here
    assert "READY FOR EXPLORE STUDIO" in start_here
    assert "SETUP HELP NEEDED" in start_here
    assert "requirements-student.txt" in start_here
    assert "do **not** need to install Git to begin" in start_here


def test_computer_readiness_doc_states_hardware_floor_and_unsupported_devices():
    readiness = (PROJECT_ROOT / "docs" / "computer-readiness.md").read_text(encoding="utf-8")

    assert "**8 GB**" in readiness
    assert "**5 GB**" in readiness
    assert "Physical keyboard" in readiness
    assert "Stable connection" in readiness
    assert "| Microphone | **Required** |" in readiness
    assert "| Webcam | Recommended |" in readiness
    assert "| Headphones | Recommended |" in readiness
    assert (
        "A **phone, tablet, or Chromebook is not a supported primary coding device for\n"
        "this cohort.**" in readiness
    )
    assert "Python **3.11 or newer**" in readiness
    assert "WSL 2 with Ubuntu and WSLg" in readiness
    assert "collects no credentials and no personal data" in readiness


def test_setup_doc_makes_the_zip_primary_and_keeps_the_git_path_available():
    setup = (PROJECT_ROOT / "docs" / "classroom-student-workspace.md").read_text(encoding="utf-8")

    assert "## Student ZIP distribution (primary)" in setup
    assert "## Git-derived student repository (advanced, later)" in setup
    assert "python3 scripts/build_student_zip.py" in setup
    assert "python3 scripts/provision_student_workspace.py" in setup
    assert "byte-identical archive bytes" in setup
    assert "student device needs Git for S01" in setup


def test_student_pin_installs_the_course_platform_without_a_git_client():
    pin = (PROJECT_ROOT / "classroom" / "requirements-student.txt").read_text(encoding="utf-8")

    assert COURSE_PLATFORM_COMMIT in pin
    assert "git+" not in pin
    assert pin.strip().endswith(".tar.gz")


def test_provisioned_workspace_also_carries_the_zip_entry_points(tmp_path):
    target = make_template(tmp_path / "student")

    provision_student_workspace(target, PROJECT_ROOT)

    readiness_check = target / "check-my-computer.py"
    assert readiness_check.is_file()
    assert readiness_check.stat().st_mode & 0o111
    assert (target / "START-HERE.md").is_file()
    assert (target / "requirements-student.txt").is_file()
    assert (target / "docs" / "computer-readiness.md").is_file()
