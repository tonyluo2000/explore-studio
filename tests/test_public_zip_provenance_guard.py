from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts.build_student_zip import ZIP_ROOT
from scripts.verify_public_zip_provenance import (
    COURSE_MATERIALS_MEMBER,
    PROVENANCE_KEY,
    PUBLIC_ZIP_PATH,
    ProvenanceGuardError,
    compare_archives,
    describe_drift,
    read_declared_provenance,
    validate_provenance_commit,
    verify_public_zip_provenance,
)

PROJECT_ROOT = Path(__file__).parents[1]
UNKNOWN_SHA = "0" * 39 + "1"


def write_archive(path: Path, members: dict[str, str]) -> Path:
    """Write a tiny stand-in archive so guard logic is tested without a course build."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return path


def write_declaring_archive(path: Path, declared: str, payload: str = "student content") -> Path:
    return write_archive(
        path,
        {
            COURSE_MATERIALS_MEMBER: json.dumps({PROVENANCE_KEY: declared}),
            f"{ZIP_ROOT}/START-HERE.md": payload,
        },
    )


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture
def two_branch_repo(tmp_path) -> Path:
    """A repo whose ``side`` commit is deliberately not reachable from ``main``."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "guard@example.test")
    git(repo, "config", "user.name", "Guard Test")
    (repo / "course.md").write_text("base\n", encoding="utf-8")
    git(repo, "add", "course.md")
    git(repo, "commit", "-qm", "base")
    git(repo, "checkout", "-q", "-b", "side")
    (repo / "course.md").write_text("side\n", encoding="utf-8")
    git(repo, "commit", "-qam", "side")
    git(repo, "checkout", "-q", "main")
    return repo


def test_committed_public_zip_matches_its_declared_provenance_commit():
    receipt = verify_public_zip_provenance(PROJECT_ROOT)
    assert receipt["declared_provenance_commit"] == read_declared_provenance(
        PROJECT_ROOT / PUBLIC_ZIP_PATH
    )
    assert receipt["committed_sha256"] == receipt["rebuilt_sha256"]
    assert receipt["members"] > 0


def test_declared_provenance_is_read_from_the_committed_archive(tmp_path):
    archive = write_declaring_archive(tmp_path / "course.zip", "a" * 40)
    assert read_declared_provenance(archive) == "a" * 40


@pytest.mark.parametrize(
    "declared",
    ["", "not-a-sha", "f755cec", "F755CECA960B8EAECECB60E226F142EF82140F23", "0" * 41],
)
def test_malformed_provenance_sha_fails(tmp_path, declared):
    archive = write_declaring_archive(tmp_path / "course.zip", declared)
    if declared:
        with pytest.raises(ProvenanceGuardError, match="40 lowercase hex"):
            validate_provenance_commit(read_declared_provenance(archive), PROJECT_ROOT)
    else:
        with pytest.raises(ProvenanceGuardError, match=PROVENANCE_KEY):
            read_declared_provenance(archive)


def test_wrong_provenance_sha_that_is_not_a_commit_fails():
    with pytest.raises(ProvenanceGuardError, match="does not resolve to a commit"):
        validate_provenance_commit(UNKNOWN_SHA, PROJECT_ROOT)


def test_provenance_commit_not_an_ancestor_of_head_fails(two_branch_repo):
    side = git(two_branch_repo, "rev-parse", "side")
    with pytest.raises(ProvenanceGuardError, match="not an ancestor of HEAD"):
        validate_provenance_commit(side, two_branch_repo)


def test_provenance_commit_that_is_an_ancestor_of_head_passes(two_branch_repo):
    base = git(two_branch_repo, "rev-parse", "main")
    assert validate_provenance_commit(base, two_branch_repo) == base


def test_stale_committed_zip_with_valid_provenance_fails(tmp_path, monkeypatch):
    declared = git(PROJECT_ROOT, "rev-parse", "HEAD")
    committed = write_declaring_archive(tmp_path / "committed.zip", declared, "stale content")
    rebuilt = write_declaring_archive(tmp_path / "rebuilt.zip", declared, "fresh content")
    monkeypatch.setattr(
        "scripts.verify_public_zip_provenance.PUBLIC_ZIP_PATH", committed.relative_to(tmp_path)
    )
    monkeypatch.setattr(
        "scripts.verify_public_zip_provenance.rebuild_from_commit",
        lambda commit, root, destination: rebuilt,
    )
    monkeypatch.setattr(
        "scripts.verify_public_zip_provenance.validate_provenance_commit",
        lambda commit, root, head="HEAD": commit,
    )
    with pytest.raises(ProvenanceGuardError) as failure:
        verify_public_zip_provenance(tmp_path)
    message = str(failure.value)
    assert declared in message
    assert "START-HERE.md" in message
    assert "sync_student_downloads.py" in message


def test_comparison_reports_both_digests_and_member_counts(tmp_path):
    committed = write_archive(tmp_path / "committed.zip", {"a.md": "one"})
    rebuilt = write_archive(tmp_path / "rebuilt.zip", {"a.md": "one", "b.md": "two"})
    with pytest.raises(ProvenanceGuardError) as failure:
        compare_archives(committed, rebuilt, "b" * 40)
    message = str(failure.value)
    assert "1 members" in message
    assert "2 members" in message
    assert "only in rebuilt ZIP:   b.md" in message


def test_identical_archives_compare_equal(tmp_path):
    committed = write_archive(tmp_path / "committed.zip", {"a.md": "one"})
    rebuilt = write_archive(tmp_path / "rebuilt.zip", {"a.md": "one"})
    receipt = compare_archives(committed, rebuilt, "c" * 40)
    assert receipt["committed_sha256"] == receipt["rebuilt_sha256"]
    assert receipt["members"] == 1


def test_drift_report_names_changed_and_missing_members(tmp_path):
    committed = write_archive(tmp_path / "committed.zip", {"a.md": "one", "gone.md": "x"})
    rebuilt = write_archive(tmp_path / "rebuilt.zip", {"a.md": "changed"})
    lines = describe_drift(committed, rebuilt)
    assert "only in committed ZIP: gone.md" in lines
    assert "content differs:       a.md" in lines


def test_missing_committed_zip_fails_clearly(tmp_path):
    with pytest.raises(ProvenanceGuardError, match="missing"):
        read_declared_provenance(tmp_path / "absent.zip")


def test_archive_without_course_materials_fails_clearly(tmp_path):
    archive = write_archive(tmp_path / "course.zip", {f"{ZIP_ROOT}/START-HERE.md": "hi"})
    with pytest.raises(
        ProvenanceGuardError, match="no explore-studio-course/course-materials.json"
    ):
        read_declared_provenance(archive)
