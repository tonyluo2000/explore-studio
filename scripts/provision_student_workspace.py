"""Provision the student-only course overlay into a clean template repository."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

COURSE_PLATFORM_COMMIT = "308bc6c0a2b149e8058f46c8f1beece50b793969"
SESSION_IDS = tuple(f"s{number:02d}" for number in range(1, 31))
EXAMPLE_PACKAGE_IDS = (
    "crystal-lantern",
    "forest-guide",
    "nova-character",
    "river-fountain",
)
TEMPLATE_MARKERS = (
    "pyproject.toml",
    "requirements-dev.txt",
    "explorer-package/manifest.yaml",
)
GENERATED_PATHS = (
    "course-materials.json",
    "requirements-course.txt",
    "lessons",
    "examples",
    "docs",
)
COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
REHEARSAL_RECORD = "operations/s01-clean-rehearsal-2026-09-10.md"


class ProvisionError(ValueError):
    """The source or target is not safe for a clean course overlay."""


def _git_revision(source_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source_root,
        capture_output=True,
        text=True,
        check=False,
    )
    revision = completed.stdout.strip()
    if completed.returncode != 0 or len(revision) != 40:
        raise ProvisionError("course source must be a Git checkout with a resolved HEAD")
    return revision


def _validate_source(source_root: Path) -> None:
    sessions_root = source_root / "lessons" / "sessions"
    for session_id in SESSION_IDS:
        student_root = sessions_root / session_id / "student"
        if not (student_root / "task-card.md").is_file():
            raise ProvisionError(f"course source is missing {session_id} student materials")
    if (sessions_root / "s31").exists():
        raise ProvisionError("course source must not contain S31 materials")
    for package_id in EXAMPLE_PACKAGE_IDS:
        if not (source_root / "examples" / "explorer-packages" / package_id).is_dir():
            raise ProvisionError(f"course source is missing example package {package_id}")
    if not (source_root / "classroom" / "requirements-course.txt").is_file():
        raise ProvisionError("course source is missing requirements-course.txt")
    if not (source_root / "docs" / "classroom-student-workspace.md").is_file():
        raise ProvisionError("course source is missing classroom workspace guidance")
    if not (source_root / "docs" / REHEARSAL_RECORD).is_file():
        raise ProvisionError("course source is missing the S01 rehearsal record")


def _validate_target(target_root: Path) -> None:
    if not target_root.is_dir():
        raise ProvisionError("target must be an existing student-template repository")
    if not (target_root / ".git").exists():
        raise ProvisionError("target must be an initialized student Git repository")
    for marker in TEMPLATE_MARKERS:
        if not (target_root / marker).is_file():
            raise ProvisionError(f"target is missing student-template marker {marker}")
    for relative_path in GENERATED_PATHS:
        if (target_root / relative_path).exists():
            raise ProvisionError(f"target already contains course path {relative_path}")
    if (target_root / "explore").exists() or (target_root / "engine").exists():
        raise ProvisionError("student repository must not contain platform or engine source")


def provision_student_workspace(target_root, source_root=None):
    """Copy the student course overlay after all source and target checks pass."""
    source = (
        Path(source_root).resolve()
        if source_root is not None
        else Path(__file__).resolve().parents[1]
    )
    target = Path(target_root).resolve()
    if source == target or source in target.parents or target in source.parents:
        raise ProvisionError("course source and student target must be separate checkouts")

    _validate_source(source)
    _validate_target(target)
    source_revision = _git_revision(source)

    source_sessions = source / "lessons" / "sessions"
    target_sessions = target / "lessons" / "sessions"
    target_sessions.mkdir(parents=True)
    shutil.copy2(source_sessions / "README.md", target_sessions / "README.md")
    shutil.copy2(
        source_sessions / "student-quick-start.md",
        target_sessions / "student-quick-start.md",
    )
    for session_id in SESSION_IDS:
        shutil.copytree(
            source_sessions / session_id / "student",
            target_sessions / session_id / "student",
            ignore=COPY_IGNORE,
        )

    target_examples = target / "examples" / "explorer-packages"
    target_examples.mkdir(parents=True)
    for package_id in EXAMPLE_PACKAGE_IDS:
        shutil.copytree(
            source / "examples" / "explorer-packages" / package_id,
            target_examples / package_id,
            ignore=COPY_IGNORE,
        )

    shutil.copy2(
        source / "classroom" / "requirements-course.txt",
        target / "requirements-course.txt",
    )
    target_docs = target / "docs"
    target_docs.mkdir()
    shutil.copy2(
        source / "docs" / "classroom-student-workspace.md",
        target_docs / "classroom-student-workspace.md",
    )
    target_operations = target_docs / "operations"
    target_operations.mkdir()
    shutil.copy2(
        source / "docs" / REHEARSAL_RECORD,
        target_docs / REHEARSAL_RECORD,
    )
    receipt = {
        "contract_version": "0.1",
        "course_materials_source_commit": source_revision,
        "course_platform_commit": COURSE_PLATFORM_COMMIT,
        "sessions": [1, 30],
    }
    (target / "course-materials.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def main(argv=None):
    """Run the teacher provisioning command."""
    parser = argparse.ArgumentParser(
        description="Add the S01-S30 student course overlay to a clean template repository."
    )
    parser.add_argument("target", type=Path, help="clean student-template repository")
    args = parser.parse_args(argv)
    try:
        receipt = provision_student_workspace(args.target)
    except ProvisionError as error:
        parser.error(str(error))
    print(
        "provisioned S01-S30 student materials " f"from {receipt['course_materials_source_commit']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
