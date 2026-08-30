"""Immutable models for materialized output-tree verification v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_assembled_output_manifest_models import (
    ClassWorldAssembledOutputManifest,
)

SUPPORTED_CLASS_WORLD_OUTPUT_TREE_VERIFICATION_CONTRACT_VERSION = "0.1"


class ClassWorldOutputTreeVerificationIssueCode(StrEnum):
    """Stable machine-readable output-tree verification issue codes."""

    VERIFIED_MANIFEST_REQUIRED = "VERIFIED_MANIFEST_REQUIRED"
    VERIFIED_MANIFEST_INVALID = "VERIFIED_MANIFEST_INVALID"
    VERIFIED_MANIFEST_NOT_VERIFIED = "VERIFIED_MANIFEST_NOT_VERIFIED"
    VERIFIED_MANIFEST_INCONSISTENT = "VERIFIED_MANIFEST_INCONSISTENT"
    OUTPUT_ROOT_REQUIRED = "OUTPUT_ROOT_REQUIRED"
    OUTPUT_ROOT_INVALID_TYPE = "OUTPUT_ROOT_INVALID_TYPE"
    OUTPUT_ROOT_NOT_ABSOLUTE = "OUTPUT_ROOT_NOT_ABSOLUTE"
    OUTPUT_ROOT_INVALID = "OUTPUT_ROOT_INVALID"
    OUTPUT_ROOT_NOT_FOUND = "OUTPUT_ROOT_NOT_FOUND"
    OUTPUT_ROOT_SYMLINK_NOT_ALLOWED = "OUTPUT_ROOT_SYMLINK_NOT_ALLOWED"
    OUTPUT_ROOT_NOT_DIRECTORY = "OUTPUT_ROOT_NOT_DIRECTORY"
    OUTPUT_ROOT_INSPECTION_FAILED = "OUTPUT_ROOT_INSPECTION_FAILED"
    DESCRIPTOR_CONFINEMENT_UNAVAILABLE = "DESCRIPTOR_CONFINEMENT_UNAVAILABLE"
    RELATIVE_PATH_INVALID = "RELATIVE_PATH_INVALID"
    RELATIVE_PATH_COLLISION = "RELATIVE_PATH_COLLISION"
    ARTIFACT_OUTSIDE_ROOT = "ARTIFACT_OUTSIDE_ROOT"
    ARTIFACT_NOT_FOUND = "ARTIFACT_NOT_FOUND"
    ARTIFACT_SYMLINK_NOT_ALLOWED = "ARTIFACT_SYMLINK_NOT_ALLOWED"
    ARTIFACT_NOT_REGULAR = "ARTIFACT_NOT_REGULAR"
    ARTIFACT_IDENTITY_DUPLICATE = "ARTIFACT_IDENTITY_DUPLICATE"
    ARTIFACT_TOO_LARGE = "ARTIFACT_TOO_LARGE"
    OUTPUT_TREE_TOO_LARGE = "OUTPUT_TREE_TOO_LARGE"
    ARTIFACT_READ_FAILED = "ARTIFACT_READ_FAILED"
    DIGEST_ALGORITHM_UNSUPPORTED = "DIGEST_ALGORITHM_UNSUPPORTED"
    BYTE_COUNT_MISMATCH = "BYTE_COUNT_MISMATCH"
    DIGEST_MISMATCH = "DIGEST_MISMATCH"
    AGGREGATE_BYTE_TOTAL_MISMATCH = "AGGREGATE_BYTE_TOTAL_MISMATCH"


@dataclass(frozen=True)
class ClassWorldVerifiedOutputArtifact:
    """One manifest-authorized artifact confirmed on disk under the output root."""

    package_id: str
    package_version: str
    relative_path: str
    digest_algorithm: str
    digest_hex: str
    bytes_verified: int


@dataclass(frozen=True)
class ClassWorldOutputTreeVerificationIssue:
    """One deterministic output-tree verification diagnostic."""

    code: ClassWorldOutputTreeVerificationIssueCode
    message: str
    location: str
    package_id: str | None = None
    package_index: int | None = None


@dataclass(frozen=True)
class ClassWorldOutputTreeVerificationResult:
    """Atomic materialized output-tree verification state."""

    contract_version: str
    manifest: ClassWorldAssembledOutputManifest | None
    artifacts: tuple[ClassWorldVerifiedOutputArtifact, ...]
    total_bytes: int | None
    issues: tuple[ClassWorldOutputTreeVerificationIssue, ...]

    @property
    def is_verified(self) -> bool:
        """Whether every manifest-authorized artifact matched on disk."""
        return (
            self.manifest is not None
            and bool(self.artifacts)
            and self.total_bytes is not None
            and not self.issues
        )
