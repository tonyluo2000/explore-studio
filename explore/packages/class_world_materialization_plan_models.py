"""Immutable models for deterministic class-world materialization planning v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_artifact_file_verification_models import (
    ClassWorldArtifactFileVerificationResult,
    ClassWorldPackageArtifactFileRead,
)
from explore.packages.class_world_artifact_inventory_models import (
    ClassWorldPackageArtifactDeclaration,
)

SUPPORTED_CLASS_WORLD_MATERIALIZATION_PLAN_CONTRACT_VERSION = "0.1"


class ClassWorldMaterializationPlanIssueCode(StrEnum):
    """Stable machine-readable materialization-plan issue codes."""

    FILE_VERIFICATION_RESULT_REQUIRED = "FILE_VERIFICATION_RESULT_REQUIRED"
    FILE_VERIFICATION_RESULT_INVALID = "FILE_VERIFICATION_RESULT_INVALID"
    FILE_VERIFICATION_NOT_COMPLETE = "FILE_VERIFICATION_NOT_COMPLETE"
    FILE_VERIFICATION_INCONSISTENT = "FILE_VERIFICATION_INCONSISTENT"
    ARTIFACT_CONTENT_MISMATCH = "ARTIFACT_CONTENT_MISMATCH"


@dataclass(frozen=True)
class ClassWorldPackageMaterialization:
    """One verified package artifact assigned to one canonical output path."""

    artifact: ClassWorldPackageArtifactDeclaration
    source: ClassWorldPackageArtifactFileRead
    relative_path: str


@dataclass(frozen=True)
class ClassWorldMaterializationPlan:
    """Canonical output layout for one complete matching artifact-file set."""

    contract_version: str
    file_verification: ClassWorldArtifactFileVerificationResult
    packages: tuple[ClassWorldPackageMaterialization, ...]
    total_bytes: int


@dataclass(frozen=True)
class ClassWorldMaterializationPlanIssue:
    """One deterministic materialization-plan diagnostic."""

    code: ClassWorldMaterializationPlanIssueCode
    message: str
    location: str
    package_id: str | None = None
    package_index: int | None = None


@dataclass(frozen=True)
class ClassWorldMaterializationPlanResult:
    """Atomic result of planning one class-world materialization layout."""

    plan: ClassWorldMaterializationPlan | None
    issues: tuple[ClassWorldMaterializationPlanIssue, ...]

    @property
    def is_planned(self) -> bool:
        """Whether one complete immutable materialization plan was built."""
        return self.plan is not None and not self.issues
