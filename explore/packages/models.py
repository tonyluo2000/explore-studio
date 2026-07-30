"""Immutable models for Explorer Package manifests and validation reports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IssueCode(StrEnum):
    """Stable machine-readable Explorer Package validation issue codes."""

    PACKAGE_ROOT_MISSING = "PACKAGE_ROOT_MISSING"
    PACKAGE_ROOT_NOT_DIRECTORY = "PACKAGE_ROOT_NOT_DIRECTORY"
    MANIFEST_MISSING = "MANIFEST_MISSING"
    MANIFEST_INVALID_YAML = "MANIFEST_INVALID_YAML"
    MANIFEST_INVALID_ENCODING = "MANIFEST_INVALID_ENCODING"
    MANIFEST_READ_ERROR = "MANIFEST_READ_ERROR"
    MANIFEST_INVALID_TYPE = "MANIFEST_INVALID_TYPE"
    MANIFEST_FIELD_REQUIRED = "MANIFEST_FIELD_REQUIRED"
    MANIFEST_FIELD_UNKNOWN = "MANIFEST_FIELD_UNKNOWN"
    SCHEMA_VERSION_UNSUPPORTED = "SCHEMA_VERSION_UNSUPPORTED"
    PACKAGE_ID_INVALID = "PACKAGE_ID_INVALID"
    PACKAGE_DISPLAY_NAME_INVALID = "PACKAGE_DISPLAY_NAME_INVALID"
    PACKAGE_VERSION_INVALID = "PACKAGE_VERSION_INVALID"
    STUDENT_API_UNSUPPORTED = "STUDENT_API_UNSUPPORTED"
    CONTRIBUTIONS_REQUIRED = "CONTRIBUTIONS_REQUIRED"
    CONTRIBUTION_ID_INVALID = "CONTRIBUTION_ID_INVALID"
    CONTRIBUTION_ID_DUPLICATE = "CONTRIBUTION_ID_DUPLICATE"
    CONTRIBUTION_TYPE_UNSUPPORTED = "CONTRIBUTION_TYPE_UNSUPPORTED"
    ASSET_ID_INVALID = "ASSET_ID_INVALID"
    ASSET_ID_DUPLICATE = "ASSET_ID_DUPLICATE"
    ASSET_TYPE_UNSUPPORTED = "ASSET_TYPE_UNSUPPORTED"
    PATH_EMPTY = "PATH_EMPTY"
    PATH_ABSOLUTE = "PATH_ABSOLUTE"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    PATH_FORMAT_UNSUPPORTED = "PATH_FORMAT_UNSUPPORTED"
    PATH_SYMLINK_NOT_ALLOWED = "PATH_SYMLINK_NOT_ALLOWED"
    PATH_OUTSIDE_PACKAGE = "PATH_OUTSIDE_PACKAGE"
    PATH_DUPLICATE = "PATH_DUPLICATE"
    FILE_MISSING = "FILE_MISSING"
    FILE_NOT_REGULAR = "FILE_NOT_REGULAR"
    FILE_TYPE_UNSUPPORTED = "FILE_TYPE_UNSUPPORTED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"


@dataclass(frozen=True)
class PackageMetadata:
    """Identity and version metadata for one Explorer Package."""

    id: str
    display_name: str
    version: str


@dataclass(frozen=True)
class Compatibility:
    """Platform compatibility declared by an Explorer Package."""

    student_api: str


@dataclass(frozen=True)
class ContributionDeclaration:
    """One declarative contribution exported by a package."""

    id: str
    type: str
    path: str


@dataclass(frozen=True)
class AssetDeclaration:
    """One media asset explicitly declared by a package."""

    id: str
    type: str
    path: str


@dataclass(frozen=True)
class ExplorerPackageManifest:
    """Typed representation of an Explorer Package manifest v0.1."""

    schema_version: str
    package: PackageMetadata
    compatibility: Compatibility
    contributions: tuple[ContributionDeclaration, ...]
    assets: tuple[AssetDeclaration, ...] = ()


@dataclass(frozen=True)
class ValidationIssue:
    """One deterministic, actionable package validation diagnostic."""

    code: IssueCode
    message: str
    location: str


@dataclass(frozen=True)
class ValidationReport:
    """Complete validation result for one Explorer Package directory."""

    manifest: ExplorerPackageManifest | None
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        """Whether validation completed without any issues."""
        return not self.issues
