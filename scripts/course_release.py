"""Internal Course Kit contract, artifact validation and phase-aware release gate.

The contract describes approved bytes. State is derived from Git/artifact/live
checks; a hand-edited state string can never certify classroom readiness.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from scripts.build_student_zip import (
    ZIP_ROOT,
    assert_distribution_is_student_safe,
    build_student_zip,
)
from scripts.journey_snapshots import published_sessions, runtime_pin
from scripts.verify_public_zip_provenance import rebuild_from_commit, validate_provenance_commit

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = Path("docs/operations/course-release.json")
PUBLIC = Path("course4teen-website/public/downloads/explore-studio-course.zip")
MATERIALS = f"{ZIP_ROOT}/course-materials.json"
STATES = (
    "BUILDING",
    "REVIEWED",
    "MERGED",
    "COURSE_KIT_PUBLISHED",
    "LIVE_VERIFIED",
    "CLASSROOM_VERIFIED",
)


class ReleaseError(ValueError):
    """Fail-closed release validation error."""


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def clean_source(root: Path) -> None:
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ReleaseError("DIRTY_SOURCE: commit source changes and isolate unrelated files first")


def inspect_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ReleaseError("DUPLICATE_ZIP_MEMBER: rebuild candidate from clean source")
        relative = []
        for info in archive.infolist():
            name = info.filename
            p = PurePosixPath(name)
            if (
                not name.startswith(ZIP_ROOT + "/")
                or ".." in p.parts
                or "\\" in name
                or p.is_absolute()
                or info.is_dir()
                or (info.external_attr >> 16) & 0o170000 == 0o120000
            ):
                raise ReleaseError(f"UNSAFE_ZIP_MEMBER: {name}")
            relative.append(Path(*p.parts[1:]))
        assert_distribution_is_student_safe(relative)
        bad = archive.testzip()
        if bad:
            raise ReleaseError(f"CORRUPT_ZIP_MEMBER: {bad}")
        record = json.loads(archive.read(MATERIALS))
        requirements = archive.read(f"{ZIP_ROOT}/requirements-student.txt").decode()
        pins = re.findall(r"/archive/([a-f0-9]{40})\.tar\.gz", requirements)
        if pins != [record.get("course_platform_commit")]:
            raise ReleaseError("RUNTIME_PIN_MISMATCH: requirements and embedded metadata differ")
        for sid in range(1, 31):
            if f"{ZIP_ROOT}/lessons/sessions/s{sid:02}/student/task-card.md" not in names:
                raise ReleaseError(f"MISSING_LESSON_FILES: S{sid:02}")
        return {
            "expected_runtime_pin": record["course_platform_commit"],
            "expected_course_kit_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "expected_course_kit_members": len(names),
            "materials_provenance": record["course_materials_source_commit"],
            "member_names": sorted(names),
        }


def load_contract(root: Path = ROOT) -> dict:
    c = json.loads((root / CONTRACT).read_text())
    keys = {
        "schema_version",
        "published_session",
        "implementation_head",
        "expected_runtime_pin",
        "expected_course_kit_sha256",
        "expected_course_kit_members",
        "materials_provenance",
        "member_names",
    }
    if set(c) != keys or c["schema_version"] != 1:
        raise ReleaseError("INVALID_RELEASE_CONTRACT: regenerate with prepare_course_release.py")
    for key in ("implementation_head", "expected_runtime_pin", "materials_provenance"):
        if not re.fullmatch(r"[0-9a-f]{40}", str(c[key])):
            raise ReleaseError(f"INVALID_RELEASE_CONTRACT: {key}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(c["expected_course_kit_sha256"])):
        raise ReleaseError("INVALID_RELEASE_CONTRACT: SHA256")
    if (
        c["published_session"] != published_sessions()[-1]
        or c["expected_runtime_pin"] != runtime_pin()
    ):
        raise ReleaseError(
            "RELEASE_CONTRACT_STALE: published session/runtime changed; "
            "run prepare_course_release.py"
        )
    if (
        not isinstance(c["member_names"], list)
        or len(set(c["member_names"])) != len(c["member_names"])
        or len(c["member_names"]) != c["expected_course_kit_members"]
    ):
        raise ReleaseError("INVALID_RELEASE_CONTRACT: member inventory")
    return c


def verify_artifact(path: Path, contract: dict, *, live: bool = False) -> dict:
    actual = inspect_zip(path)
    prefix = "LIVE_COURSE_KIT_STALE" if live else "PRODUCTION_COURSE_KIT_STALE"
    mismatches = [key for key in actual if actual[key] != contract[key]]
    if mismatches:
        raise ReleaseError(
            f"{prefix}: published session {contract['published_session']}\n"
            f"Expected runtime: {contract['expected_runtime_pin']}\n"
            f"Actual ZIP runtime: {actual['expected_runtime_pin']}\n"
            f"Expected SHA256: {contract['expected_course_kit_sha256']}\n"
            f"Actual SHA256: {actual['expected_course_kit_sha256']}\n"
            f"Mismatched fields: {', '.join(mismatches)}\n"
            "Required action: prepare and independently review the Course Kit publication PR; "
            "merge only with owner approval, then verify actual live bytes and isolated acceptance."
        )
    return actual


def compare_builds(first: Path, second: Path) -> None:
    if first.read_bytes() != second.read_bytes():
        raise ReleaseError("NONDETERMINISTIC_COURSE_KIT: two builds differ; publication refused")


def validate_candidate(contract: dict, root: Path = ROOT) -> None:
    """Validate hand-edited contract by rebuilding immutable source twice.

    Also compare today's shipped materials and runtime tree, preventing an old
    but internally valid receipt from disguising newly changed lesson source.
    """
    validate_provenance_commit(contract["implementation_head"], root)
    for key in ("materials_provenance", "expected_runtime_pin"):
        validate_provenance_commit(contract[key], root, head=contract["implementation_head"])
    if git(
        root,
        "diff",
        contract["expected_runtime_pin"],
        "HEAD",
        "--",
        "engine",
        "explore",
        "pyproject.toml",
    ):
        raise ReleaseError(
            "UNPINNED_RUNTIME: pin the approved runtime containing current engine/explore changes"
        )
    with tempfile.TemporaryDirectory(prefix="release-candidate-") as tmp:
        first, second, current = [
            Path(tmp) / f"{name}.zip" for name in ("first", "second", "current")
        ]
        rebuild_from_commit(contract["materials_provenance"], root, first)
        rebuild_from_commit(contract["materials_provenance"], root, second)
        compare_builds(first, second)
        verify_artifact(first, contract)
        build_student_zip(current, root)
        with zipfile.ZipFile(first) as a, zipfile.ZipFile(current) as b:
            if set(a.namelist()) != set(b.namelist()) or any(
                a.read(n) != b.read(n) for n in a.namelist() if n != MATERIALS
            ):
                raise ReleaseError(
                    "CANDIDATE_SOURCE_STALE: regenerate release bundle "
                    "from committed lesson materials"
                )


def publication_diff(files: list[str]) -> None:
    if set(files) != {PUBLIC.as_posix()}:
        raise ReleaseError(
            "UNRELATED_PUBLICATION_DIFF: publication must change exactly the public Course Kit ZIP"
        )


def check_phase(contract: dict, phase: str, files: list[str], root: Path = ROOT) -> str:
    if phase == "publication":
        publication_diff(files)
    elif phase == "implementation" and PUBLIC.as_posix() in files:
        raise ReleaseError(
            "MIXED_PUBLICATION_PHASE: keep implementation and ZIP publication separate"
        )
    validate_candidate(contract, root)
    try:
        verify_artifact(root / PUBLIC, contract)
    except ReleaseError as error:
        if phase != "implementation":
            raise
        return (
            "Implementation candidate validated; production is stale (expected phase lag)\n"
            f"{error}\nClassroom readiness: BLOCKED"
        )
    state = "Publication candidate validated; awaiting owner merge"
    if phase == "main" and published_head(contract, root):
        state = "COURSE KIT PUBLISHED (merged repository bytes)"
    return f"{state}; Live SHA: not verified; Classroom readiness: BLOCKED"


def published_head(contract: dict, root: Path = ROOT) -> str | None:
    """A matching local candidate is not proof of a separately merged publication.

    Fetch origin/main before live verification; stale local refs fail closed.
    """
    try:
        merged_contract = json.loads(
            subprocess.check_output(
                ["git", "show", f"origin/main:{CONTRACT}"],
                cwd=root,
                text=True,
                stderr=subprocess.DEVNULL,
            )
        )
        if merged_contract != contract:
            return None
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", contract["implementation_head"], "origin/main"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        merged_zip = subprocess.check_output(
            ["git", "show", f"origin/main:{PUBLIC}"],
            cwd=root,
            stderr=subprocess.DEVNULL,
        )
        if hashlib.sha256(merged_zip).hexdigest() != contract["expected_course_kit_sha256"]:
            return None
        return git(root, "log", "-1", "--format=%H", "origin/main", "--", PUBLIC.as_posix())
    except (subprocess.CalledProcessError, ValueError, OSError):
        return None
