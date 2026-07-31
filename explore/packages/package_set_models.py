"""Immutable models for package-set preflight planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.contribution_models import PackageProvenance
from explore.packages.registration_models import (
    StudentAPIRegistrationEntry,
    StudentAPIRegistrationPlan,
)


class PackageSetIssueCode(StrEnum):
    """Stable machine-readable package-set preflight issue codes."""

    PACKAGE_SET_REQUIRED = "PACKAGE_SET_REQUIRED"
    SELECTION_INVALID_TYPE = "SELECTION_INVALID_TYPE"
    PACKAGE_ID_INVALID = "PACKAGE_ID_INVALID"
    PACKAGE_VERSION_INVALID = "PACKAGE_VERSION_INVALID"
    PACKAGE_SELECTION_DUPLICATE = "PACKAGE_SELECTION_DUPLICATE"
    PACKAGE_VERSION_CONFLICT = "PACKAGE_VERSION_CONFLICT"
    PACKAGE_PROVENANCE_MISMATCH = "PACKAGE_PROVENANCE_MISMATCH"
    STUDENT_API_VERSION_UNSUPPORTED = "STUDENT_API_VERSION_UNSUPPORTED"
    STUDENT_API_VERSION_MISMATCH = "STUDENT_API_VERSION_MISMATCH"
    REGISTRATION_PLAN_INVALID = "REGISTRATION_PLAN_INVALID"
    ENTRY_PROVENANCE_MISMATCH = "ENTRY_PROVENANCE_MISMATCH"
    ENTRY_IDENTITY_INVALID = "ENTRY_IDENTITY_INVALID"
    ENTRY_IDENTITY_DUPLICATE = "ENTRY_IDENTITY_DUPLICATE"
    ENTRY_TYPE_UNSUPPORTED = "ENTRY_TYPE_UNSUPPORTED"
    ENTRY_VALUE_INVALID = "ENTRY_VALUE_INVALID"
    CHARACTER_CARDINALITY_EXCEEDED = "CHARACTER_CARDINALITY_EXCEEDED"
    WORLD_OBJECT_CARDINALITY_EXCEEDED = "WORLD_OBJECT_CARDINALITY_EXCEEDED"


@dataclass(frozen=True)
class PackageSelection:
    """One exact package-version pin and its completed registration plan."""

    package_id: str
    package_version: str
    registration_plan: StudentAPIRegistrationPlan


@dataclass(frozen=True)
class SelectedPackagePlan:
    """One validated package selection retained in caller-provided order."""

    package_id: str
    package_version: str
    provenance: PackageProvenance
    registration_plan: StudentAPIRegistrationPlan


@dataclass(frozen=True)
class PackageSetPlan:
    """Complete immutable preflighted plan for one ordered package set."""

    student_api_version: str
    packages: tuple[SelectedPackagePlan, ...]
    entries: tuple[StudentAPIRegistrationEntry, ...]


@dataclass(frozen=True)
class PackageSetIssue:
    """One deterministic package-set preflight diagnostic."""

    code: PackageSetIssueCode
    message: str
    location: str
    package_id: str | None = None
    package_index: int | None = None
    qualified_id: str | None = None
    entry_index: int | None = None


@dataclass(frozen=True)
class PackageSetPlanResult:
    """Atomic result of package-set preflight planning."""

    plan: PackageSetPlan | None
    issues: tuple[PackageSetIssue, ...]

    @property
    def is_planned(self) -> bool:
        """Whether a complete package-set plan was built without issues."""
        return self.plan is not None and not self.issues
