"""S30 final validation, deterministic export, and M16 rehearsal evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from explore.curriculum.missions import MISSION_16_ID
from explore.packages import export_explorer_package
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from explore.packages.loader import load_explorer_package

PROJECT_ROOT = Path(__file__).parents[4]
STUDENT_ROOT = Path(__file__).parent
PACKAGE_ROOT = STUDENT_ROOT / "explorer-package"
PLAYER_PACKAGE_ROOT = PROJECT_ROOT / "examples" / "explorer-packages" / "nova-character"
PLAYER_ID = "nova-character:nova"


class PremiereEvidenceError(ValueError):
    """Final evidence could not be collected from the reviewed package."""


@dataclass(frozen=True)
class PremiereEvidence:
    """Small, explainable receipt for the S30 technical demonstration."""

    package_id: str
    package_version: str
    member_paths: tuple[str, ...]
    world_object_ids: tuple[str, ...]
    archive_bytes: int
    first_sha256: str
    second_sha256: str
    exports_match: bool
    mission_id: str


def _issue_text(issues):
    return "; ".join(f"{issue.code.value}:{issue.location}:{issue.message}" for issue in issues)


def collect_premiere_evidence(output_root, package_root=PACKAGE_ROOT):
    """Validate, plan M16, export twice, and return deterministic evidence."""
    package_path = Path(package_root).resolve()
    output_path = Path(output_root).resolve()

    loaded = load_explorer_package(package_path)
    if not loaded.is_loaded or loaded.package is None:
        raise PremiereEvidenceError(f"package validation failed: {_issue_text(loaded.all_issues)}")

    planned = plan_local_classroom_trail(
        (PLAYER_PACKAGE_ROOT, package_path),
        player_qualified_id=PLAYER_ID,
    )
    if not planned.is_planned or planned.plan is None:
        raise PremiereEvidenceError(f"Trail planning failed: {_issue_text(planned.issues)}")

    scene = create_classroom_trail_scene(
        object(),
        planned.plan,
        mission_id=MISSION_16_ID,
    )

    archive_name = (
        f"{loaded.package.metadata.id}-{loaded.package.metadata.version}" ".explorer-package.zip"
    )
    destinations = []
    results = []
    for run_name in ("first", "second"):
        run_root = output_path / run_name
        run_root.mkdir(parents=True, exist_ok=False)
        destination = run_root / archive_name
        result = export_explorer_package(package_path, destination)
        if not result.is_exported:
            raise PremiereEvidenceError(f"export failed: {_issue_text(result.issues)}")
        destinations.append(destination)
        results.append(result)

    first, second = results
    assert first.artifact is not None and first.digest is not None
    assert second.artifact is not None and second.digest is not None
    return PremiereEvidence(
        package_id=first.artifact.package_id,
        package_version=first.artifact.package_version,
        member_paths=tuple(entry.relative_path for entry in first.artifact.entries),
        world_object_ids=tuple(item.qualified_id for item in scene.objects),
        archive_bytes=first.bytes_written,
        first_sha256=first.digest.hex_digest,
        second_sha256=second.digest.hex_digest,
        exports_match=(
            first.artifact == second.artifact
            and first.digest == second.digest
            and destinations[0].read_bytes() == destinations[1].read_bytes()
        ),
        mission_id=scene.mission.mission_id,
    )
