"""Validation-first local loading for declarative Explorer Packages."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

from explore.packages.contribution_models import (
    LoadedCharacter,
    LoadedContribution,
    LoadedExplorerPackage,
    LoadedWorldObject,
    PackageAssetReference,
    PackageLoadIssue,
    PackageLoadIssueCode,
    PackageLoadResult,
    PackageProvenance,
)
from explore.packages.contribution_parser import parse_contribution_file
from explore.packages.validator import validate_explorer_package


def _duplicate_issue(contribution_id: str, index: int) -> PackageLoadIssue:
    location = f"contributions[{index}].id"
    return PackageLoadIssue(
        code=PackageLoadIssueCode.CONTRIBUTION_DUPLICATE,
        message=f'Contribution identity "{contribution_id}" was encountered more than once.',
        location=location,
    )


def _conditional_reference_issues(
    contributions: tuple[LoadedContribution, ...],
) -> tuple[PackageLoadIssue, ...]:
    by_id: dict[str, list[LoadedContribution]] = {}
    for contribution in contributions:
        by_id.setdefault(contribution.contribution_id, []).append(contribution)
    issues: list[PackageLoadIssue] = []
    for contribution in contributions:
        if not isinstance(contribution, LoadedCharacter) or contribution.respond_to_toggle is None:
            continue
        reference = contribution.respond_to_toggle
        location = f"{contribution.source_path}.respond_to_toggle.object_id"
        matches = by_id.get(reference.object_id, [])
        target = matches[0] if len(matches) == 1 else None
        if len(matches) != 1:
            message = f"{location} must resolve exactly once within this package."
        elif not isinstance(target, LoadedWorldObject):
            message = f"{location} must reference a world object in this package."
        elif target.toggle is None:
            message = f"{location} must reference a world object with toggle metadata."
        else:
            continue
        issues.append(
            PackageLoadIssue(
                code=PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID,
                message=message,
                location=location,
            )
        )
    return tuple(issues)


def load_explorer_package(package_root: str | os.PathLike[str]) -> PackageLoadResult:
    """Validate and atomically load one unpacked Explorer Package.

    Validation is always the first gate. If package validation fails, no
    contribution file is read. Validator-approved contribution files are then
    parsed as strict safe YAML in manifest order. Any loading issue prevents a
    partially loaded package from being returned.

    Args:
        package_root: Directory containing the unpacked Explorer Package.

    Returns:
        An immutable result containing the validation report, a fully loaded
        package on success, and deterministic contribution loading issues.
    """
    validation_report = validate_explorer_package(package_root)
    manifest = validation_report.manifest
    if not validation_report.is_valid or manifest is None:
        return PackageLoadResult(
            validation_report=validation_report,
            package=None,
            issues=(),
        )

    resolved_root = Path(package_root).resolve(strict=True)
    provenance = PackageProvenance(
        package_id=manifest.package.id,
        package_version=manifest.package.version,
        student_api_version=manifest.compatibility.student_api,
    )
    assets = tuple(
        PackageAssetReference(id=asset.id, type=asset.type, path=asset.path)
        for asset in manifest.assets
    )
    assets_by_id = {asset.id: asset for asset in assets}

    loaded: list[LoadedContribution] = []
    issues: list[PackageLoadIssue] = []
    seen_identities: set[str] = set()
    for index, declaration in enumerate(manifest.contributions):
        qualified_id = f"{provenance.package_id}:{declaration.id}"
        if qualified_id in seen_identities:
            issues.append(_duplicate_issue(qualified_id, index))
            continue
        seen_identities.add(qualified_id)

        relative_path = PurePosixPath(declaration.path)
        contribution_path = resolved_root.joinpath(*relative_path.parts)
        contribution, contribution_issues = parse_contribution_file(
            contribution_path,
            declaration,
            provenance,
            assets_by_id,
        )
        issues.extend(contribution_issues)
        if contribution is not None:
            loaded.append(contribution)

    issues.extend(_conditional_reference_issues(tuple(loaded)))
    if issues:
        return PackageLoadResult(
            validation_report=validation_report,
            package=None,
            issues=tuple(issues),
        )

    return PackageLoadResult(
        validation_report=validation_report,
        package=LoadedExplorerPackage(
            metadata=manifest.package,
            compatibility=manifest.compatibility,
            provenance=provenance,
            contributions=tuple(loaded),
            assets=assets,
        ),
        issues=(),
    )
