"""Immutable models returned by the local Explorer Package loader."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.models import (
    Compatibility,
    PackageMetadata,
    ValidationIssue,
    ValidationReport,
)


class PackageLoadIssueCode(StrEnum):
    """Stable machine-readable contribution loading issue codes."""

    CONTRIBUTION_INVALID_YAML = "CONTRIBUTION_INVALID_YAML"
    CONTRIBUTION_INVALID_ENCODING = "CONTRIBUTION_INVALID_ENCODING"
    CONTRIBUTION_READ_ERROR = "CONTRIBUTION_READ_ERROR"
    CONTRIBUTION_INVALID_TYPE = "CONTRIBUTION_INVALID_TYPE"
    CONTRIBUTION_FIELD_REQUIRED = "CONTRIBUTION_FIELD_REQUIRED"
    CONTRIBUTION_FIELD_UNKNOWN = "CONTRIBUTION_FIELD_UNKNOWN"
    CONTRIBUTION_VALUE_INVALID = "CONTRIBUTION_VALUE_INVALID"
    CONTRIBUTION_ASSET_UNKNOWN = "CONTRIBUTION_ASSET_UNKNOWN"
    CONTRIBUTION_ASSET_TYPE_MISMATCH = "CONTRIBUTION_ASSET_TYPE_MISMATCH"
    CONTRIBUTION_DUPLICATE = "CONTRIBUTION_DUPLICATE"


@dataclass(frozen=True)
class PackageLoadIssue:
    """One deterministic, student-facing contribution loading diagnostic."""

    code: PackageLoadIssueCode
    message: str
    location: str


@dataclass(frozen=True)
class PackageProvenance:
    """Package identity attached to every loaded contribution."""

    package_id: str
    package_version: str
    student_api_version: str


@dataclass(frozen=True)
class PackageAssetReference:
    """A declared package asset retained by safe package-relative identity."""

    id: str
    type: str
    path: str


@dataclass(frozen=True)
class LoadedWorldObjectToggle:
    """Strict two-color toggle presentation loaded from inert package data."""

    off_color: str
    on_color: str


@dataclass(frozen=True)
class LoadedWorldObjectCounter:
    """Bounded interaction goal loaded from inert package data."""

    goal: int
    when_goal_reached: str


@dataclass(frozen=True)
class LoadedCharacterToggleResponse:
    """Fixed two-branch response to one package-local toggle object."""

    object_id: str
    when_off: str
    when_on: str


@dataclass(frozen=True)
class LoadedCharacterTwoToggleResponse:
    """Fixed Boolean-and response to exactly two package-local toggles."""

    object_ids: tuple[str, str]
    when_not_all_on: str
    when_all_on: str


@dataclass(frozen=True)
class LoadedCharacter:
    """One declarative character plus optional inert trail conversation."""

    contribution_id: str
    qualified_id: str
    source_path: str
    provenance: PackageProvenance
    name: str
    x: int
    y: int
    color: str
    image: PackageAssetReference | None = None
    greeting: str | None = None
    conversation: tuple[str, ...] | None = None
    respond_to_toggle: LoadedCharacterToggleResponse | None = None
    respond_to_two_toggles: LoadedCharacterTwoToggleResponse | None = None


@dataclass(frozen=True)
class LoadedWorldObject:
    """One declarative world object mapped to Student API v0.1 configuration."""

    contribution_id: str
    qualified_id: str
    source_path: str
    provenance: PackageProvenance
    name: str
    x: int
    y: int
    color: str
    image: PackageAssetReference | None = None
    when_near: str | None = None
    when_interacted: str | None = None
    toggle: LoadedWorldObjectToggle | None = None
    counter: LoadedWorldObjectCounter | None = None


LoadedContribution = LoadedCharacter | LoadedWorldObject


@dataclass(frozen=True)
class LoadedExplorerPackage:
    """A fully validated and atomically loaded Explorer Package."""

    metadata: PackageMetadata
    compatibility: Compatibility
    provenance: PackageProvenance
    contributions: tuple[LoadedContribution, ...]
    assets: tuple[PackageAssetReference, ...] = ()

    @property
    def characters(self) -> tuple[LoadedCharacter, ...]:
        """Loaded character contributions in manifest order."""
        return tuple(
            contribution
            for contribution in self.contributions
            if isinstance(contribution, LoadedCharacter)
        )

    @property
    def world_objects(self) -> tuple[LoadedWorldObject, ...]:
        """Loaded world-object contributions in manifest order."""
        return tuple(
            contribution
            for contribution in self.contributions
            if isinstance(contribution, LoadedWorldObject)
        )


@dataclass(frozen=True)
class PackageLoadResult:
    """Complete validation and local loading result for one package directory."""

    validation_report: ValidationReport
    package: LoadedExplorerPackage | None
    issues: tuple[PackageLoadIssue, ...]

    @property
    def is_loaded(self) -> bool:
        """Whether validation and atomic contribution loading both succeeded."""
        return self.validation_report.is_valid and self.package is not None and not self.issues

    @property
    def all_issues(self) -> tuple[ValidationIssue | PackageLoadIssue, ...]:
        """Validation issues followed by contribution issues in stable order."""
        return (*self.validation_report.issues, *self.issues)
