"""Immutable models for transactional package-set application."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.contribution_models import (
    PackageAssetReference,
    PackageProvenance,
)
from explore.packages.registration_application_models import (
    RegistrationApplicationState,
    RegistrationType,
)


class PackageSetApplicationIssueCode(StrEnum):
    """Stable machine-readable package-set application issue codes."""

    PACKAGE_SET_PLAN_REQUIRED = "PACKAGE_SET_PLAN_REQUIRED"
    TARGET_REQUIRED = "TARGET_REQUIRED"
    TARGET_INCOMPATIBLE = "TARGET_INCOMPATIBLE"
    STUDENT_API_VERSION_UNSUPPORTED = "STUDENT_API_VERSION_UNSUPPORTED"
    PACKAGE_SET_STRUCTURE_INVALID = "PACKAGE_SET_STRUCTURE_INVALID"
    SELECTED_PACKAGE_MISMATCH = "SELECTED_PACKAGE_MISMATCH"
    ENTRY_PROVENANCE_MISMATCH = "ENTRY_PROVENANCE_MISMATCH"
    ENTRY_IDENTITY_INVALID = "ENTRY_IDENTITY_INVALID"
    ENTRY_DUPLICATE = "ENTRY_DUPLICATE"
    TARGET_DUPLICATE = "TARGET_DUPLICATE"
    TARGET_CHARACTER_LIMIT_EXCEEDED = "TARGET_CHARACTER_LIMIT_EXCEEDED"
    TARGET_WORLD_OBJECT_LIMIT_EXCEEDED = "TARGET_WORLD_OBJECT_LIMIT_EXCEEDED"
    ENTRY_TYPE_UNSUPPORTED = "ENTRY_TYPE_UNSUPPORTED"
    ENTRY_VALUE_INVALID = "ENTRY_VALUE_INVALID"
    ENTRY_ASSET_TYPE_MISMATCH = "ENTRY_ASSET_TYPE_MISMATCH"
    INSTANCE_CONSTRUCTION_FAILED = "INSTANCE_CONSTRUCTION_FAILED"
    TARGET_ADD_FAILED = "TARGET_ADD_FAILED"
    TARGET_REMOVE_FAILED = "TARGET_REMOVE_FAILED"


@dataclass(frozen=True)
class PackageSetApplicationIssue:
    """One deterministic package-aware application diagnostic."""

    code: PackageSetApplicationIssueCode
    message: str
    location: str
    package_id: str | None = None
    package_index: int | None = None
    qualified_id: str | None = None
    contribution_id: str | None = None
    entry_index: int | None = None


@dataclass(frozen=True)
class AppliedPackageSetRegistration:
    """Immutable package and entry metadata for one committed registration."""

    package_id: str
    package_version: str
    package_index: int
    entry_index: int
    qualified_id: str
    contribution_id: str
    provenance: PackageProvenance
    registration_type: RegistrationType
    asset_reference: PackageAssetReference | None = None


@dataclass(frozen=True)
class PackageSetApplicationResult:
    """Complete immutable result of one package-set application transaction."""

    state: RegistrationApplicationState
    applied: tuple[AppliedPackageSetRegistration, ...] = ()
    issues: tuple[PackageSetApplicationIssue, ...] = ()
    unreverted: tuple[AppliedPackageSetRegistration, ...] = ()

    @property
    def is_applied(self) -> bool:
        """Whether every package and entry committed successfully."""
        return self.state is RegistrationApplicationState.APPLIED

    @property
    def target_may_be_partially_modified(self) -> bool:
        """Whether failed rollback means target consistency is not guaranteed."""
        return self.state is RegistrationApplicationState.ROLLBACK_INCOMPLETE
