"""Immutable models for verified class-world artifact materialization v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_artifact_file_verification_models import (
    ClassWorldArtifactFileVerificationResult,
)
from explore.packages.class_world_materialization_plan_models import (
    ClassWorldMaterializationPlan,
    ClassWorldPackageMaterialization,
)

SUPPORTED_CLASS_WORLD_VERIFIED_MATERIALIZATION_CONTRACT_VERSION = "0.1"


class ClassWorldVerifiedMaterializationIssueCode(StrEnum):
    """Stable machine-readable verified-materialization issue codes."""

    PLAN_RESULT_REQUIRED = "PLAN_RESULT_REQUIRED"
    PLAN_RESULT_INVALID = "PLAN_RESULT_INVALID"
    PLAN_NOT_BUILT = "PLAN_NOT_BUILT"
    PLAN_INCONSISTENT = "PLAN_INCONSISTENT"
    OUTPUT_ROOT_REQUIRED = "OUTPUT_ROOT_REQUIRED"
    OUTPUT_ROOT_INVALID_TYPE = "OUTPUT_ROOT_INVALID_TYPE"
    OUTPUT_ROOT_NOT_ABSOLUTE = "OUTPUT_ROOT_NOT_ABSOLUTE"
    OUTPUT_ROOT_INVALID = "OUTPUT_ROOT_INVALID"
    OUTPUT_PARENT_NOT_FOUND = "OUTPUT_PARENT_NOT_FOUND"
    OUTPUT_PARENT_SYMLINK_NOT_ALLOWED = "OUTPUT_PARENT_SYMLINK_NOT_ALLOWED"
    OUTPUT_PARENT_NOT_DIRECTORY = "OUTPUT_PARENT_NOT_DIRECTORY"
    OUTPUT_PARENT_UNSAFE = "OUTPUT_PARENT_UNSAFE"
    OUTPUT_DESTINATION_EXISTS = "OUTPUT_DESTINATION_EXISTS"
    OUTPUT_OVERLAPS_SOURCE = "OUTPUT_OVERLAPS_SOURCE"
    SOURCE_VERIFICATION_FAILED = "SOURCE_VERIFICATION_FAILED"
    SOURCE_CONTENT_MISMATCH = "SOURCE_CONTENT_MISMATCH"
    SOURCE_SNAPSHOT_INCONSISTENT = "SOURCE_SNAPSHOT_INCONSISTENT"
    STAGING_CREATE_FAILED = "STAGING_CREATE_FAILED"
    DESTINATION_WRITE_FAILED = "DESTINATION_WRITE_FAILED"
    ATOMIC_PUBLISH_FAILED = "ATOMIC_PUBLISH_FAILED"
    STAGING_CLEANUP_FAILED = "STAGING_CLEANUP_FAILED"


@dataclass(frozen=True)
class ClassWorldMaterializedPackage:
    """One plan-authorized package destination written from verified bytes."""

    package: ClassWorldPackageMaterialization
    bytes_written: int


@dataclass(frozen=True)
class ClassWorldVerifiedMaterialization:
    """One atomically published class-world package artifact tree."""

    contract_version: str
    plan: ClassWorldMaterializationPlan
    source_verification: ClassWorldArtifactFileVerificationResult
    packages: tuple[ClassWorldMaterializedPackage, ...]
    total_bytes: int


@dataclass(frozen=True)
class ClassWorldVerifiedMaterializationIssue:
    """One deterministic verified-materialization diagnostic."""

    code: ClassWorldVerifiedMaterializationIssueCode
    message: str
    location: str
    package_id: str | None = None
    package_index: int | None = None


@dataclass(frozen=True)
class ClassWorldVerifiedMaterializationResult:
    """Atomic verified-materialization result with fresh source verification."""

    materialization: ClassWorldVerifiedMaterialization | None
    source_verification: ClassWorldArtifactFileVerificationResult | None
    issues: tuple[ClassWorldVerifiedMaterializationIssue, ...]

    @property
    def is_materialized(self) -> bool:
        """Whether one complete output tree was atomically published."""
        return self.materialization is not None and not self.issues
