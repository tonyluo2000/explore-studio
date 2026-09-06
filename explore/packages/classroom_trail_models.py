"""Immutable models for the additive local Classroom Trail contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.package_set_models import SelectedPackagePlan
from explore.packages.registration_models import (
    CharacterRegistration,
    WorldObjectRegistration,
)

SUPPORTED_CLASSROOM_TRAIL_CONTRACT_VERSION = "0.4"


class ClassroomTrailPlanIssueCode(StrEnum):
    """Stable machine-readable Classroom Trail planning issue codes."""

    PACKAGE_SET_REQUIRED = "PACKAGE_SET_REQUIRED"
    PACKAGE_INVALID = "PACKAGE_INVALID"
    PLAYER_REQUIRED = "PLAYER_REQUIRED"
    PLAYER_SELECTION_REQUIRED = "PLAYER_SELECTION_REQUIRED"
    PLAYER_SELECTION_NOT_FOUND = "PLAYER_SELECTION_NOT_FOUND"
    PLAYER_CARDINALITY_EXCEEDED = "PLAYER_CARDINALITY_EXCEEDED"
    WORLD_OBJECT_REQUIRED = "WORLD_OBJECT_REQUIRED"


@dataclass(frozen=True)
class ClassroomTrailPlanIssue:
    """One deterministic Classroom Trail planning diagnostic."""

    code: ClassroomTrailPlanIssueCode
    message: str
    location: str
    package_id: str | None = None
    qualified_id: str | None = None


@dataclass(frozen=True)
class ClassroomTrailPlan:
    """Canonical local runtime projection for one player, NPCs, and objects."""

    contract_version: str
    packages: tuple[SelectedPackagePlan, ...]
    player: CharacterRegistration
    npcs: tuple[CharacterRegistration, ...]
    world_objects: tuple[WorldObjectRegistration, ...]


@dataclass(frozen=True)
class ClassroomTrailPlanResult:
    """Atomic result of planning one local Classroom Trail."""

    plan: ClassroomTrailPlan | None
    issues: tuple[ClassroomTrailPlanIssue, ...]

    @property
    def is_planned(self) -> bool:
        return self.plan is not None and not self.issues
