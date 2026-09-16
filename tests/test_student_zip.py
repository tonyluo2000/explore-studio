from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts.build_student_zip import (
    EXCLUDED_DIRECTORY_NAMES,
    FIXED_TIMESTAMP,
    ZIP_EXCLUDED_PATHS,
    ZIP_NAME,
    ZIP_ROOT,
    StudentZipError,
    assert_distribution_is_student_safe,
    build_student_zip,
    collect_members,
)
from scripts.provision_student_workspace import COURSE_PLATFORM_COMMIT, SESSION_IDS

PROJECT_ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def student_zip(tmp_path_factory) -> Path:
    destination = tmp_path_factory.mktemp("student-zip") / ZIP_NAME
    build_student_zip(destination, PROJECT_ROOT)
    return destination


def member_names(archive_path: Path) -> list[str]:
    with zipfile.ZipFile(archive_path) as archive:
        return archive.namelist()


def course_paths(archive_path: Path) -> list[str]:
    prefix = f"{ZIP_ROOT}/"
    return [name[len(prefix) :] for name in member_names(archive_path)]


def test_zip_has_one_named_root_and_every_student_entry_point(student_zip):
    names = member_names(student_zip)
    assert names, "the student archive must not be empty"
    assert {name.split("/", 1)[0] for name in names} == {ZIP_ROOT}

    paths = set(course_paths(student_zip))
    assert "START-HERE.md" in paths
    assert "check-my-computer.py" in paths
    assert "requirements-student.txt" in paths
    assert "course-materials.json" in paths
    assert "docs/computer-readiness.md" in paths
    assert "lessons/sessions/student-quick-start.md" in paths


def test_zip_carries_every_s01_s30_student_material_and_no_s31(student_zip):
    paths = set(course_paths(student_zip))
    for session_id in SESSION_IDS:
        assert f"lessons/sessions/{session_id}/student/task-card.md" in paths
    assert not any(path.startswith("lessons/sessions/s31") for path in paths)
    for package_id in ("crystal-lantern", "forest-guide", "nova-character", "river-fountain"):
        assert f"examples/explorer-packages/{package_id}/manifest.yaml" in paths


def test_zip_excludes_teacher_material_platform_source_and_environment_noise(student_zip):
    paths = course_paths(student_zip)
    for path in paths:
        assert "teacher-runbook.md" not in path
        assert "answer-key" not in path
        assert not path.endswith((".pyc", ".pyo", ".whl", ".key", ".pem"))
        assert Path(path).name not in {".DS_Store", ".env", "Thumbs.db"}
        parts = Path(path).parts
        assert not any(part in EXCLUDED_DIRECTORY_NAMES for part in parts)
        assert parts[0] not in {"explore", "engine", "scripts", "tests", ".git", ".venv"}


def test_zip_ships_only_the_no_git_dependency_pin(student_zip):
    paths = set(course_paths(student_zip))
    for excluded in ZIP_EXCLUDED_PATHS:
        assert excluded not in paths

    with zipfile.ZipFile(student_zip) as archive:
        pin = archive.read(f"{ZIP_ROOT}/requirements-student.txt").decode("utf-8")
    assert COURSE_PLATFORM_COMMIT in pin
    assert "git+" not in pin, "the student pin must install without a Git client"
    assert "https://" in pin


def test_zip_receipt_records_provenance_without_personal_data(student_zip):
    with zipfile.ZipFile(student_zip) as archive:
        receipt = json.loads(archive.read(f"{ZIP_ROOT}/course-materials.json"))
    assert receipt["course_platform_commit"] == COURSE_PLATFORM_COMMIT
    assert receipt["sessions"] == [1, 30]
    assert set(receipt) == {
        "contract_version",
        "course_materials_source_commit",
        "course_platform_commit",
        "sessions",
    }


def test_zip_is_byte_identical_when_built_twice_from_the_same_source(tmp_path):
    first = build_student_zip(tmp_path / "first.zip", PROJECT_ROOT)
    second = build_student_zip(tmp_path / "second.zip", PROJECT_ROOT)

    assert first["sha256"] == second["sha256"]
    assert hashlib.sha256((tmp_path / "first.zip").read_bytes()).hexdigest() == first["sha256"]
    assert member_names(tmp_path / "first.zip") == member_names(tmp_path / "second.zip")


def test_zip_members_are_sorted_with_fixed_timestamps_and_modes(student_zip):
    with zipfile.ZipFile(student_zip) as archive:
        infos = archive.infolist()

    assert [info.filename for info in infos] == sorted(info.filename for info in infos)
    for info in infos:
        assert info.date_time == FIXED_TIMESTAMP
        mode = info.external_attr >> 16
        expected = 0o755 if info.filename.endswith("check-my-computer.py") else 0o644
        assert mode == expected


def test_destination_directory_receives_the_named_archive(tmp_path):
    receipt = build_student_zip(tmp_path, PROJECT_ROOT)

    assert receipt["archive"] == (tmp_path / ZIP_NAME).resolve()
    assert receipt["archive"].is_file()
    assert receipt["root"] == ZIP_ROOT
    assert receipt["members"] > 0


def test_safety_gate_rejects_teacher_platform_and_cache_members():
    safe = collect_members_of_reference()
    for leaked in (
        Path("lessons/sessions/s01/teacher-runbook.md"),
        Path("engine/app.py"),
        Path("scripts/build_student_zip.py"),
        Path("lessons/__pycache__/x.pyc"),
        Path(".git/config"),
    ):
        with pytest.raises(StudentZipError, match="must not contain"):
            assert_distribution_is_student_safe([*safe, leaked])


def test_safety_gate_rejects_a_distribution_missing_a_student_entry_point():
    safe = collect_members_of_reference()
    without_start_here = [member for member in safe if member.as_posix() != "START-HERE.md"]

    with pytest.raises(StudentZipError, match="missing START-HERE.md"):
        assert_distribution_is_student_safe(without_start_here)


def collect_members_of_reference() -> list[Path]:
    """Return a member list known to pass the safety gate."""
    return [
        Path("START-HERE.md"),
        Path("check-my-computer.py"),
        Path("course-materials.json"),
        Path("requirements-student.txt"),
        Path("docs/computer-readiness.md"),
        Path("lessons/sessions/student-quick-start.md"),
        Path("lessons/sessions/s01/student/task-card.md"),
        Path("lessons/sessions/s30/student/task-card.md"),
    ]


def test_collect_members_skips_caches_and_generated_metadata(tmp_path):
    staged = tmp_path / "staged"
    (staged / "lessons" / "__pycache__").mkdir(parents=True)
    (staged / "lessons" / "__pycache__" / "x.pyc").write_bytes(b"")
    (staged / "lessons" / "keep.md").write_text("keep", encoding="utf-8")
    (staged / "lessons" / ".DS_Store").write_bytes(b"")
    (staged / "docs").mkdir()
    (staged / "docs" / "note.md").write_text("note", encoding="utf-8")
    (staged / "course-materials.json").write_text("{}", encoding="utf-8")

    collected = {member.as_posix() for member in collect_members(staged)}

    assert collected == {"lessons/keep.md", "docs/note.md", "course-materials.json"}
