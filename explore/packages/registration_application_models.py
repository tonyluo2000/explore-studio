"""Immutable models and target contract for registration-plan application."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from explore import Character, Object
from explore.packages.contribution_models import (
    PackageAssetReference,
    PackageProvenance,
)


class RegistrationApplicationState(StrEnum):
    """Stable states for one registration application attempt."""

    NOT_APPLIED = "NOT_APPLIED"
    APPLIED = "APPLIED"
    ROLLED_BACK = "ROLLED_BACK"
    ROLLBACK_INCOMPLETE = "ROLLBACK_INCOMPLETE"


class RegistrationType(StrEnum):
    """Supported Student API registration kinds."""

    CHARACTER = "CHARACTER"
    WORLD_OBJECT = "WORLD_OBJECT"


class RegistrationApplicationIssueCode(StrEnum):
    """Stable machine-readable application diagnostic codes."""

    PLAN_REQUIRED = "PLAN_REQUIRED"
    TARGET_REQUIRED = "TARGET_REQUIRED"
    TARGET_INCOMPATIBLE = "TARGET_INCOMPATIBLE"
    STUDENT_API_VERSION_UNSUPPORTED = "STUDENT_API_VERSION_UNSUPPORTED"
    PLAN_PROVENANCE_MISMATCH = "PLAN_PROVENANCE_MISMATCH"
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
class RegistrationApplicationIssue:
    """One deterministic registration-application diagnostic."""

    code: RegistrationApplicationIssueCode
    message: str
    location: str
    qualified_id: str | None = None
    contribution_id: str | None = None


@dataclass(frozen=True)
class AppliedRegistration:
    """Immutable metadata for one successfully applied registration."""

    qualified_id: str
    contribution_id: str
    provenance: PackageProvenance
    registration_type: RegistrationType
    asset_reference: PackageAssetReference | None = None


@dataclass(frozen=True)
class RegistrationApplicationResult:
    """Complete immutable result of one application transaction."""

    state: RegistrationApplicationState
    applied: tuple[AppliedRegistration, ...] = ()
    issues: tuple[RegistrationApplicationIssue, ...] = ()
    unreverted_qualified_ids: tuple[str, ...] = ()

    @property
    def is_applied(self) -> bool:
        """Whether every planned entry was committed successfully."""
        return self.state is RegistrationApplicationState.APPLIED

    @property
    def target_may_be_partially_modified(self) -> bool:
        """Whether failed rollback means target consistency is not guaranteed."""
        return self.state is RegistrationApplicationState.ROLLBACK_INCOMPLETE


@runtime_checkable
class StudentAPIRegistrationTarget(Protocol):
    """Narrow explicit target required by registration-plan application.

    Each add or remove operation must be atomic for its single entry: if it
    raises, it must leave that entry unchanged. Callers must provide exclusive
    access to the target for the duration of an application attempt.
    """

    def contains_registration(self, qualified_id: str) -> bool:
        """Return whether *qualified_id* is already registered."""

    def has_character(self) -> bool:
        """Return whether the target's single character slot is occupied."""

    def has_world_object(self) -> bool:
        """Return whether the target's single world-object slot is occupied."""

    def add_character(self, qualified_id: str, character: Character) -> None:
        """Add one character under *qualified_id*."""

    def remove_character(self, qualified_id: str, character: Character) -> None:
        """Remove the exact character added under *qualified_id*."""

    def add_world_object(self, qualified_id: str, world_object: Object) -> None:
        """Add one world object under *qualified_id*."""

    def remove_world_object(self, qualified_id: str, world_object: Object) -> None:
        """Remove the exact world object added under *qualified_id*."""
