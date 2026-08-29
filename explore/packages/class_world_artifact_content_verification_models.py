"""Immutable models for class-world artifact content verification v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_artifact_inventory_models import (
    ClassWorldPackageArtifactDeclaration,
)
from explore.packages.class_world_assembly_plan_models import ClassWorldAssemblyPlan

SUPPORTED_CLASS_WORLD_ARTIFACT_CONTENT_VERIFICATION_CONTRACT_VERSION = "0.1"


class ClassWorldArtifactContentVerificationIssueCode(StrEnum):
    """Stable machine-readable artifact-content verification issue codes."""

    PLAN_RESULT_REQUIRED = "PLAN_RESULT_REQUIRED"
    PLAN_RESULT_INVALID = "PLAN_RESULT_INVALID"
    PLAN_NOT_BUILT = "PLAN_NOT_BUILT"
    PLAN_INVALID = "PLAN_INVALID"
    ARTIFACT_CONTENTS_REQUIRED = "ARTIFACT_CONTENTS_REQUIRED"
    ARTIFACT_CONTENT_COUNT_MISMATCH = "ARTIFACT_CONTENT_COUNT_MISMATCH"
    ARTIFACT_CONTENT_INVALID_TYPE = "ARTIFACT_CONTENT_INVALID_TYPE"


@dataclass(frozen=True)
class ClassWorldPackageArtifactContentDigest:
    """Recomputed content digest for one supplied package artifact payload."""

    algorithm: str
    hex_digest: str


@dataclass(frozen=True)
class ClassWorldPackageArtifactContentVerification:
    """Expected declaration and recomputed digest equality for one package."""

    artifact: ClassWorldPackageArtifactDeclaration
    actual_digest: ClassWorldPackageArtifactContentDigest
    matches: bool


@dataclass(frozen=True)
class ClassWorldArtifactContentVerification:
    """Complete ordered verification state for one assembly input plan."""

    contract_version: str
    plan: ClassWorldAssemblyPlan
    packages: tuple[ClassWorldPackageArtifactContentVerification, ...]

    @property
    def all_match(self) -> bool:
        """Whether every supplied package artifact matches its declaration."""
        return bool(self.packages) and all(package.matches for package in self.packages)


@dataclass(frozen=True)
class ClassWorldArtifactContentVerificationIssue:
    """One deterministic artifact-content verification diagnostic."""

    code: ClassWorldArtifactContentVerificationIssueCode
    message: str
    location: str
    artifact_index: int | None = None


@dataclass(frozen=True)
class ClassWorldArtifactContentVerificationResult:
    """Atomic result of verifying one complete ordered artifact content set."""

    verification: ClassWorldArtifactContentVerification | None
    issues: tuple[ClassWorldArtifactContentVerificationIssue, ...]

    @property
    def is_complete(self) -> bool:
        """Whether all supplied artifact contents were hashed and compared."""
        return self.verification is not None and not self.issues
