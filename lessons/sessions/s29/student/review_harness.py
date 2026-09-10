"""S29 evidence helpers for behavior-preserving capstone review."""

from __future__ import annotations

import hashlib
from pathlib import Path

from explore.packages.classroom_trail import plan_local_classroom_trail
from explore.packages.loader import load_explorer_package

PROJECT_ROOT = Path(__file__).parents[4]
STUDENT_ROOT = Path(__file__).parent
PACKAGE_ROOT = STUDENT_ROOT / "explorer-package"
PLAYER_PACKAGE_ROOT = PROJECT_ROOT / "examples" / "explorer-packages" / "nova-character"
PLAYER_ID = "nova-character:nova"


class ReviewEvidenceError(ValueError):
    """The reviewed package cannot supply valid regression evidence."""


def snapshot_package(package_root=PACKAGE_ROOT):
    """Return a stable path/size/SHA-256 snapshot without changing the package."""
    root = Path(package_root).resolve()
    if not root.is_dir():
        raise ReviewEvidenceError(f"package directory is missing: {root.name}")

    snapshot = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            raise ReviewEvidenceError(f"package file escapes review root: {path.name}")
        payload = resolved.read_bytes()
        snapshot.append(
            {
                "path": resolved.relative_to(root).as_posix(),
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return tuple(snapshot)


def compare_snapshots(before, after):
    """Return stable paths whose presence or byte evidence changed."""
    before_by_path = {entry["path"]: entry for entry in before}
    after_by_path = {entry["path"]: entry for entry in after}
    paths = sorted(before_by_path.keys() | after_by_path.keys())
    return tuple(path for path in paths if before_by_path.get(path) != after_by_path.get(path))


def validate_and_plan(package_root=PACKAGE_ROOT):
    """Validate and plan the reviewed package without launching or mutating Trail."""
    root = Path(package_root)
    loaded = load_explorer_package(root)
    if not loaded.is_loaded:
        details = "; ".join(
            f"{issue.code.value}:{issue.location}:{issue.message}" for issue in loaded.all_issues
        )
        raise ReviewEvidenceError(f"package validation failed: {details}")

    planned = plan_local_classroom_trail(
        (PLAYER_PACKAGE_ROOT, root),
        player_qualified_id=PLAYER_ID,
    )
    if not planned.is_planned:
        details = "; ".join(
            f"{issue.code.value}:{issue.location}:{issue.message}" for issue in planned.issues
        )
        raise ReviewEvidenceError(f"Trail planning failed: {details}")
    return loaded, planned
