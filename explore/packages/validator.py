"""Safe, deterministic validation for Explorer Package directories."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath, PureWindowsPath

from explore.packages.manifest import load_manifest_document, parse_manifest_document
from explore.packages.models import (
    AssetDeclaration,
    ContributionDeclaration,
    ExplorerPackageManifest,
    IssueCode,
    ValidationIssue,
    ValidationReport,
)
from explore.packages.policy import (
    ASSET_FILE_EXTENSIONS,
    CONTRIBUTION_FILE_EXTENSIONS,
    MAX_ASSET_SIZE_BYTES,
)


def _issue(code: IssueCode, message: str, location: str) -> ValidationIssue:
    return ValidationIssue(code=code, message=message, location=location)


def _normalize_declared_path(
    value: str,
    *,
    package_root: Path,
    location: str,
) -> tuple[PurePosixPath | None, ValidationIssue | None]:
    if not value.strip() or value == ".":
        return None, _issue(
            IssueCode.PATH_EMPTY,
            f"{location} must name a file inside the package.",
            location,
        )
    posix_path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if posix_path.is_absolute() or windows_path.is_absolute() or bool(windows_path.drive):
        return None, _issue(
            IssueCode.PATH_ABSOLUTE,
            f"{location} must be relative to the package root.",
            location,
        )
    if "\x00" in value or "\\" in value:
        return None, _issue(
            IssueCode.PATH_FORMAT_UNSUPPORTED,
            f"{location} must use a portable relative path with forward slashes.",
            location,
        )
    if ".." in posix_path.parts:
        return None, _issue(
            IssueCode.PATH_TRAVERSAL,
            f"{location} must not contain parent-directory traversal ('..').",
            location,
        )

    normalized = PurePosixPath(*posix_path.parts)
    if not normalized.parts:
        return None, _issue(
            IssueCode.PATH_EMPTY,
            f"{location} must name a file inside the package.",
            location,
        )

    # Report the stricter symlink policy in the filesystem phase before
    # canonical resolution can turn a symlink escape into a generic outside-root issue.
    if _contains_symlink(package_root, normalized):
        return normalized, None

    resolved_candidate = package_root.joinpath(*normalized.parts).resolve(strict=False)
    if not resolved_candidate.is_relative_to(package_root):
        return None, _issue(
            IssueCode.PATH_OUTSIDE_PACKAGE,
            f"{location} resolves outside the package root.",
            location,
        )
    return normalized, None


def _contains_symlink(package_root: Path, relative_path: PurePosixPath) -> bool:
    current = package_root
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _validate_declared_file(
    declaration: ContributionDeclaration | AssetDeclaration,
    *,
    package_root: Path,
    location: str,
    allowed_extensions: frozenset[str] | None,
    normalized_paths: set[str],
    is_asset: bool,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    path_location = f"{location}.path"
    normalized, path_issue = _normalize_declared_path(
        declaration.path,
        package_root=package_root,
        location=path_location,
    )
    if path_issue is not None:
        return [path_issue]
    assert normalized is not None

    normalized_string = normalized.as_posix()
    if normalized_string in normalized_paths:
        issues.append(
            _issue(
                IssueCode.PATH_DUPLICATE,
                f'{path_location} duplicates the normalized declared path "{normalized_string}".',
                path_location,
            )
        )
    else:
        normalized_paths.add(normalized_string)

    suffix = normalized.suffix.lower()
    if allowed_extensions is not None and suffix not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        issues.append(
            _issue(
                IssueCode.FILE_TYPE_UNSUPPORTED,
                (
                    f'{path_location} has unsupported extension "{suffix or "(none)"}"; '
                    f"choose from: {allowed}."
                ),
                path_location,
            )
        )

    if _contains_symlink(package_root, normalized):
        issues.append(
            _issue(
                IssueCode.PATH_SYMLINK_NOT_ALLOWED,
                f"{path_location} must not refer to a symlink or pass through one.",
                path_location,
            )
        )
        return issues

    candidate = package_root.joinpath(*normalized.parts)
    if not candidate.exists():
        issues.append(
            _issue(
                IssueCode.FILE_MISSING,
                f'{path_location} declares missing file "{normalized_string}".',
                path_location,
            )
        )
        return issues
    if not candidate.is_file():
        issues.append(
            _issue(
                IssueCode.FILE_NOT_REGULAR,
                f'{path_location} must refer to a regular file, not "{normalized_string}".',
                path_location,
            )
        )
        return issues

    if is_asset:
        try:
            asset_size = candidate.stat().st_size
        except OSError:
            issues.append(
                _issue(
                    IssueCode.FILE_NOT_REGULAR,
                    f"{path_location} could not be inspected as a regular file.",
                    path_location,
                )
            )
        else:
            if asset_size > MAX_ASSET_SIZE_BYTES:
                issues.append(
                    _issue(
                        IssueCode.FILE_TOO_LARGE,
                        (
                            f"{path_location} exceeds the v0.1 asset limit of "
                            f"{MAX_ASSET_SIZE_BYTES} bytes."
                        ),
                        path_location,
                    )
                )
    return issues


def _validate_manifest_filesystem(
    manifest: ExplorerPackageManifest,
    package_root: Path,
) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    normalized_paths: set[str] = set()

    for index, contribution in enumerate(manifest.contributions):
        extensions = CONTRIBUTION_FILE_EXTENSIONS.get(contribution.type)
        issues.extend(
            _validate_declared_file(
                contribution,
                package_root=package_root,
                location=f"contributions[{index}]",
                allowed_extensions=extensions,
                normalized_paths=normalized_paths,
                is_asset=False,
            )
        )

    for index, asset in enumerate(manifest.assets):
        extensions = ASSET_FILE_EXTENSIONS.get(asset.type)
        issues.extend(
            _validate_declared_file(
                asset,
                package_root=package_root,
                location=f"assets[{index}]",
                allowed_extensions=extensions,
                normalized_paths=normalized_paths,
                is_asset=True,
            )
        )

    return tuple(issues)


def validate_explorer_package(package_root: str | os.PathLike[str]) -> ValidationReport:
    """Validate one unpacked Explorer Package directory.

    The validator reads only ``manifest.yaml``. It never imports or executes
    package files, follows remote references, installs dependencies, or runs
    package-provided tests.

    Args:
        package_root: Directory containing the required ``manifest.yaml``.

    Returns:
        An immutable report containing the typed manifest when structurally
        parseable and all issues in deterministic order.
    """
    root = Path(package_root)
    if not root.exists():
        return ValidationReport(
            manifest=None,
            issues=(
                _issue(
                    IssueCode.PACKAGE_ROOT_MISSING,
                    "The Explorer Package directory does not exist.",
                    "package",
                ),
            ),
        )
    if not root.is_dir():
        return ValidationReport(
            manifest=None,
            issues=(
                _issue(
                    IssueCode.PACKAGE_ROOT_NOT_DIRECTORY,
                    "The Explorer Package root must be a directory.",
                    "package",
                ),
            ),
        )

    resolved_root = root.resolve(strict=True)
    manifest_path = resolved_root / "manifest.yaml"
    if manifest_path.is_symlink():
        return ValidationReport(
            manifest=None,
            issues=(
                _issue(
                    IssueCode.PATH_SYMLINK_NOT_ALLOWED,
                    "manifest.yaml must be a regular file, not a symlink.",
                    "manifest.yaml",
                ),
            ),
        )
    if not manifest_path.exists():
        return ValidationReport(
            manifest=None,
            issues=(
                _issue(
                    IssueCode.MANIFEST_MISSING,
                    "Explorer Packages require manifest.yaml at the package root.",
                    "manifest.yaml",
                ),
            ),
        )
    if not manifest_path.is_file():
        return ValidationReport(
            manifest=None,
            issues=(
                _issue(
                    IssueCode.FILE_NOT_REGULAR,
                    "manifest.yaml must be a regular file.",
                    "manifest.yaml",
                ),
            ),
        )

    document, load_issues = load_manifest_document(manifest_path)
    if load_issues:
        return ValidationReport(manifest=None, issues=load_issues)

    manifest, manifest_issues = parse_manifest_document(document)
    filesystem_issues = (
        _validate_manifest_filesystem(manifest, resolved_root) if manifest is not None else ()
    )
    return ValidationReport(
        manifest=manifest,
        issues=manifest_issues + filesystem_issues,
    )
