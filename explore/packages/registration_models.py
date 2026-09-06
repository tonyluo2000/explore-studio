"""Immutable models for Student API registration planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.contribution_models import (
    PackageAssetReference,
    PackageLoadIssue,
    PackageProvenance,
)
from explore.packages.models import ValidationIssue


class RegistrationPlanIssueCode(StrEnum):
    """Stable machine-readable registration-planning issue codes."""

    LOAD_RESULT_NOT_LOADED = "LOAD_RESULT_NOT_LOADED"
    LOADED_PACKAGE_REQUIRED = "LOADED_PACKAGE_REQUIRED"
    STUDENT_API_VERSION_UNSUPPORTED = "STUDENT_API_VERSION_UNSUPPORTED"
    PACKAGE_PROVENANCE_MISMATCH = "PACKAGE_PROVENANCE_MISMATCH"
    CONTRIBUTION_PROVENANCE_MISMATCH = "CONTRIBUTION_PROVENANCE_MISMATCH"
    CONTRIBUTION_TYPE_UNSUPPORTED = "CONTRIBUTION_TYPE_UNSUPPORTED"
    CONTRIBUTION_ID_INVALID = "CONTRIBUTION_ID_INVALID"
    CONTRIBUTION_ID_DUPLICATE = "CONTRIBUTION_ID_DUPLICATE"
    CONTRIBUTION_VALUE_INVALID = "CONTRIBUTION_VALUE_INVALID"
    CONTRIBUTION_COLOR_UNSUPPORTED = "CONTRIBUTION_COLOR_UNSUPPORTED"
    CONTRIBUTION_ASSET_TYPE_MISMATCH = "CONTRIBUTION_ASSET_TYPE_MISMATCH"
    CONDITIONAL_REFERENCE_INVALID = "CONDITIONAL_REFERENCE_INVALID"


@dataclass(frozen=True)
class CharacterToggleResponseRegistrationSpec:
    """Detached fixed response branches for one package-local toggle."""

    object_id: str
    when_off: str
    when_on: str


@dataclass(frozen=True)
class CharacterTwoToggleResponseRegistrationSpec:
    """Detached Boolean-and responses for exactly two package-local toggles."""

    object_ids: tuple[str, str]
    when_not_all_on: str
    when_all_on: str


@dataclass(frozen=True)
class CharacterEitherToggleResponseRegistrationSpec:
    """Detached Boolean-or responses for exactly two package-local toggles."""

    object_ids: tuple[str, str]
    when_both_off: str
    when_either_on: str


@dataclass(frozen=True)
class CharacterCounterResponseRegistrationSpec:
    """Detached fixed responses for one package-local counter comparison."""

    object_id: str
    when_below_goal: str
    when_at_or_above_goal: str


@dataclass(frozen=True)
class RegistrationPlanIssue:
    """One deterministic Student API registration-planning diagnostic."""

    code: RegistrationPlanIssueCode
    message: str
    location: str
    qualified_id: str | None = None
    contribution_id: str | None = None
    field: str | None = None


@dataclass(frozen=True)
class CharacterRegistrationSpec:
    """Detached character configuration plus optional inert trail conversation."""

    name: str
    x: int
    y: int
    color: str
    greeting: str | None = None
    conversation: tuple[str, ...] | None = None
    respond_to_toggle: CharacterToggleResponseRegistrationSpec | None = None
    respond_to_two_toggles: CharacterTwoToggleResponseRegistrationSpec | None = None
    respond_to_either_toggle: CharacterEitherToggleResponseRegistrationSpec | None = None
    respond_to_counter: CharacterCounterResponseRegistrationSpec | None = None


@dataclass(frozen=True)
class WorldObjectToggleRegistrationSpec:
    """Detached strict two-color toggle presentation."""

    off_color: str
    on_color: str


@dataclass(frozen=True)
class WorldObjectCounterRegistrationSpec:
    """Detached bounded interaction goal for one world object."""

    goal: int
    when_goal_reached: str


@dataclass(frozen=True)
class WorldObjectRegistrationSpec:
    """Detached Student API v0.1 configuration for one world object."""

    name: str
    x: int
    y: int
    color: str
    when_near: str | None = None
    when_interacted: str | None = None
    toggle: WorldObjectToggleRegistrationSpec | None = None
    counter: WorldObjectCounterRegistrationSpec | None = None


@dataclass(frozen=True)
class CharacterRegistration:
    """One character entry in a detached registration plan."""

    qualified_id: str
    contribution_id: str
    provenance: PackageProvenance
    character: CharacterRegistrationSpec
    asset_reference: PackageAssetReference | None = None


@dataclass(frozen=True)
class WorldObjectRegistration:
    """One world-object entry in a detached registration plan."""

    qualified_id: str
    contribution_id: str
    provenance: PackageProvenance
    world_object: WorldObjectRegistrationSpec
    asset_reference: PackageAssetReference | None = None


StudentAPIRegistrationEntry = CharacterRegistration | WorldObjectRegistration
LoaderDiagnostic = ValidationIssue | PackageLoadIssue


@dataclass(frozen=True)
class StudentAPIRegistrationPlan:
    """Complete immutable plan for one loaded Explorer Package."""

    provenance: PackageProvenance
    entries: tuple[StudentAPIRegistrationEntry, ...]


@dataclass(frozen=True)
class RegistrationPlanResult:
    """Atomic result of Student API registration planning."""

    plan: StudentAPIRegistrationPlan | None
    issues: tuple[RegistrationPlanIssue, ...]
    loader_diagnostics: tuple[LoaderDiagnostic, ...] = ()

    @property
    def is_planned(self) -> bool:
        """Whether a complete plan was built without any diagnostics."""
        return self.plan is not None and not self.issues and not self.loader_diagnostics
