"""Build the deterministic student ZIP distribution for the S01-S30 course.

The ZIP is the primary beginner distribution path: a student unzips one folder,
runs the computer check, installs pinned course tools once, and starts S01. No
Git client, GitHub account, or clone is involved.

This builder does not decide what is student-facing. It provisions a throwaway
template with the canonical
:mod:`scripts.provision_student_workspace` overlay and archives that result, so
the ZIP and the Git-derived student repository always contain the same reviewed
material.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
import zipfile
from pathlib import Path

if __package__ in (None, ""):  # allow `python3 scripts/build_student_zip.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.provision_student_workspace import (
    COURSE_PLATFORM_COMMIT,
    GENERATED_PATHS,
    READINESS_CHECK_TARGET,
    ProvisionError,
    provision_student_workspace,
)

ZIP_ROOT = "explore-studio-course"
ZIP_NAME = f"{ZIP_ROOT}.zip"

#: Provisioned paths deliberately left out of the beginner ZIP.
#: ``requirements-course.txt`` pins the advanced Git-managed workspace through a
#: ``git+https`` URL that needs a Git client, so the ZIP ships only the plain
#: HTTPS ``requirements-student.txt`` pin and one unambiguous install command.
ZIP_EXCLUDED_PATHS = ("requirements-course.txt",)

#: Names and suffixes that must never reach a student ZIP.
EXCLUDED_DIRECTORY_NAMES = frozenset({".git", ".venv", "venv", "__pycache__", "node_modules"})
EXCLUDED_FILE_NAMES = frozenset({".DS_Store", ".env", "Thumbs.db"})
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".whl", ".key", ".pem", ".p12", ".egg-info")

#: Paths that would mean teacher material or platform source leaked into the ZIP.
FORBIDDEN_MEMBER_PARTS = ("teacher-runbook.md", "answer-key", "teacher/")
FORBIDDEN_TOP_LEVEL = ("explore", "engine", "scripts", "tests", ".git")

#: Fixed archive metadata. Every member uses the earliest timestamp the ZIP
#: format can store so the same source commit always produces the same bytes.
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
FILE_MODE = 0o644
EXECUTABLE_MODE = 0o755
EXECUTABLE_MEMBERS = frozenset({READINESS_CHECK_TARGET})


class StudentZipError(ValueError):
    """The staged distribution is not safe to publish to students."""


def _make_staging_template(root: Path) -> Path:
    """Create the minimum student-template markers the provisioner requires.

    The staging template is discarded after provisioning; only the course
    overlay it receives is archived.
    """
    (root / ".git").mkdir(parents=True)
    (root / "explorer-package").mkdir()
    (root / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (root / "requirements-dev.txt").write_text("staging placeholder\n", encoding="utf-8")
    (root / "explorer-package" / "manifest.yaml").write_text(
        'schema_version: "0.1"\n', encoding="utf-8"
    )
    return root


def _is_excluded(relative: Path) -> bool:
    """Return True when a staged path must not be archived."""
    parts = relative.parts
    if any(part in EXCLUDED_DIRECTORY_NAMES for part in parts):
        return True
    if relative.name in EXCLUDED_FILE_NAMES:
        return True
    return any(part.endswith(EXCLUDED_SUFFIXES) for part in parts)


def collect_members(staged_root: Path) -> list[Path]:
    """Return every archivable path under ``staged_root``, sorted for determinism."""
    members: list[Path] = []
    for generated_path in GENERATED_PATHS:
        if generated_path in ZIP_EXCLUDED_PATHS:
            continue
        source = staged_root / generated_path
        if source.is_file():
            members.append(Path(generated_path))
            continue
        for candidate in source.rglob("*"):
            if not candidate.is_file():
                continue
            relative = candidate.relative_to(staged_root)
            if not _is_excluded(relative):
                members.append(relative)
    return sorted(members, key=lambda path: path.as_posix())


def assert_distribution_is_student_safe(members: list[Path]) -> None:
    """Raise when teacher material, platform source, or secrets would ship."""
    for member in members:
        posix = member.as_posix()
        if any(marker in posix for marker in FORBIDDEN_MEMBER_PARTS):
            raise StudentZipError(f"student distribution must not contain {posix}")
        if member.parts[0] in FORBIDDEN_TOP_LEVEL:
            raise StudentZipError(f"student distribution must not contain {posix}")
        if _is_excluded(member):
            raise StudentZipError(f"student distribution must not contain {posix}")
    required = {
        "START-HERE.md",
        READINESS_CHECK_TARGET,
        "requirements-student.txt",
        "course-materials.json",
        "docs/computer-readiness.md",
        "lessons/sessions/student-quick-start.md",
        "lessons/sessions/s01/student/task-card.md",
        "lessons/sessions/s30/student/task-card.md",
    }
    present = {member.as_posix() for member in members}
    missing = sorted(required - present)
    if missing:
        raise StudentZipError(f"student distribution is missing {', '.join(missing)}")


def write_zip(staged_root: Path, members: list[Path], destination: Path) -> None:
    """Write ``members`` into a byte-for-byte reproducible ZIP archive."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for member in members:
            posix = member.as_posix()
            info = zipfile.ZipInfo(f"{ZIP_ROOT}/{posix}", date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            mode = EXECUTABLE_MODE if posix in EXECUTABLE_MEMBERS else FILE_MODE
            info.external_attr = mode << 16
            archive.writestr(info, (staged_root / member).read_bytes())


def build_student_zip(destination, source_root=None) -> dict:
    """Provision, verify, and archive the student ZIP distribution.

    Args:
        destination: Output ``.zip`` path, or a directory to write
            ``explore-studio-course.zip`` into.
        source_root: Explore Studio checkout to build from. Defaults to the
            checkout containing this script.

    Returns:
        A receipt with the archive path, member count, pinned course platform
        commit, and the archive's SHA-256 digest.

    Raises:
        StudentZipError: If the staged distribution is not student-safe.
        ProvisionError: If the course source is not provisionable.
    """
    source = (
        Path(source_root).resolve()
        if source_root is not None
        else Path(__file__).resolve().parents[1]
    )
    destination = Path(destination).resolve()
    if destination.is_dir() or not destination.suffix:
        destination = destination / ZIP_NAME

    with tempfile.TemporaryDirectory(prefix="explore-studio-zip-") as staging:
        staged_root = _make_staging_template(Path(staging) / "student")
        receipt = provision_student_workspace(staged_root, source)
        members = collect_members(staged_root)
        assert_distribution_is_student_safe(members)
        write_zip(staged_root, members, destination)

    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    return {
        "archive": destination,
        "root": ZIP_ROOT,
        "members": len(members),
        "course_materials_source_commit": receipt["course_materials_source_commit"],
        "course_platform_commit": COURSE_PLATFORM_COMMIT,
        "sha256": digest,
    }


def main(argv=None):
    """Run the teacher command that builds the student ZIP distribution."""
    parser = argparse.ArgumentParser(
        description="Build the deterministic S01-S30 student ZIP distribution."
    )
    parser.add_argument(
        "destination",
        type=Path,
        nargs="?",
        default=Path("dist"),
        help="output .zip path or directory (default: dist/)",
    )
    args = parser.parse_args(argv)
    try:
        receipt = build_student_zip(args.destination)
    except (ProvisionError, StudentZipError) as error:
        parser.error(str(error))
    print(f"wrote {receipt['archive']}")
    print(f"  members: {receipt['members']}")
    print(f"  course materials commit: {receipt['course_materials_source_commit']}")
    print(f"  course platform commit:  {receipt['course_platform_commit']}")
    print(f"  sha256: {receipt['sha256']}")
    print(f"Students unzip this file and open {ZIP_ROOT}/START-HERE.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
