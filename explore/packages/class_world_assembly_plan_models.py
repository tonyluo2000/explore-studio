"""Immutable models for deterministic class-world assembly input planning v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_artifact_inventory_models import ClassWorldArtifactInventory

SUPPORTED_CLASS_WORLD_ASSEMBLY_PLAN_CONTRACT_VERSION = "0.1"
SUPPORTED_CLASS_WORLD_ASSEMBLY_INPUT_DIGEST_ALGORITHM = "sha256"


class ClassWorldAssemblyPlanIssueCode(StrEnum):
    """Stable machine-readable assembly-plan issue codes."""

    INVENTORY_RESULT_REQUIRED = "INVENTORY_RESULT_REQUIRED"
    INVENTORY_RESULT_INVALID = "INVENTORY_RESULT_INVALID"
    INVENTORY_NOT_BUILT = "INVENTORY_NOT_BUILT"
    INVENTORY_INVALID = "INVENTORY_INVALID"


@dataclass(frozen=True)
class ClassWorldAssemblyInputDigest:
    """Content identity of one canonical assembly input plan."""

    algorithm: str
    hex_digest: str


@dataclass(frozen=True)
class ClassWorldAssemblyPlan:
    """Canonical, immutable inputs for a later class-world assembly operation."""

    contract_version: str
    inventory: ClassWorldArtifactInventory
    input_digest: ClassWorldAssemblyInputDigest


@dataclass(frozen=True)
class ClassWorldAssemblyPlanIssue:
    """One deterministic assembly-plan diagnostic."""

    code: ClassWorldAssemblyPlanIssueCode
    message: str
    location: str


@dataclass(frozen=True)
class ClassWorldAssemblyPlanResult:
    """Atomic result of planning one class-world assembly input set."""

    plan: ClassWorldAssemblyPlan | None
    issues: tuple[ClassWorldAssemblyPlanIssue, ...]

    @property
    def is_planned(self) -> bool:
        """Whether one complete immutable assembly plan was built."""
        return self.plan is not None and not self.issues
