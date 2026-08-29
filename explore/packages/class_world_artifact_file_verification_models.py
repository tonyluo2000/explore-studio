"""Immutable models for bounded class-world artifact-file verification v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_artifact_content_verification_models import (
    ClassWorldArtifactContentVerificationResult,
)

MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_CLASS_WORLD_ARTIFACT_SET_BYTES = 256 * 1024 * 1024
SUPPORTED_CLASS_WORLD_ARTIFACT_FILE_VERIFICATION_CONTRACT_VERSION = "0.1"


class ClassWorldArtifactFileVerificationIssueCode(StrEnum):
    """Stable machine-readable artifact-file verification issue codes."""

    PLAN_RESULT_REQUIRED = "PLAN_RESULT_REQUIRED"
    PLAN_RESULT_INVALID = "PLAN_RESULT_INVALID"
    PLAN_NOT_BUILT = "PLAN_NOT_BUILT"
    PLAN_INVALID = "PLAN_INVALID"
    ARTIFACT_ROOT_REQUIRED = "ARTIFACT_ROOT_REQUIRED"
    ARTIFACT_ROOT_INVALID_TYPE = "ARTIFACT_ROOT_INVALID_TYPE"
    ARTIFACT_ROOT_NOT_ABSOLUTE = "ARTIFACT_ROOT_NOT_ABSOLUTE"
    ARTIFACT_ROOT_NOT_FOUND = "ARTIFACT_ROOT_NOT_FOUND"
    ARTIFACT_ROOT_SYMLINK_NOT_ALLOWED = "ARTIFACT_ROOT_SYMLINK_NOT_ALLOWED"
    ARTIFACT_ROOT_NOT_DIRECTORY = "ARTIFACT_ROOT_NOT_DIRECTORY"
    ARTIFACT_ROOT_INSPECTION_FAILED = "ARTIFACT_ROOT_INSPECTION_FAILED"
    BINDINGS_REQUIRED = "BINDINGS_REQUIRED"
    BINDING_INVALID_TYPE = "BINDING_INVALID_TYPE"
    BINDING_PACKAGE_DUPLICATE = "BINDING_PACKAGE_DUPLICATE"
    BINDING_PACKAGE_UNEXPECTED = "BINDING_PACKAGE_UNEXPECTED"
    BINDING_PACKAGE_VERSION_MISMATCH = "BINDING_PACKAGE_VERSION_MISMATCH"
    BINDING_PACKAGE_MISSING = "BINDING_PACKAGE_MISSING"
    BINDING_PATH_REQUIRED = "BINDING_PATH_REQUIRED"
    BINDING_PATH_INVALID_TYPE = "BINDING_PATH_INVALID_TYPE"
    BINDING_PATH_INVALID = "BINDING_PATH_INVALID"
    BINDING_PATH_ABSOLUTE = "BINDING_PATH_ABSOLUTE"
    BINDING_PATH_TRAVERSAL = "BINDING_PATH_TRAVERSAL"
    BINDING_PATH_DUPLICATE = "BINDING_PATH_DUPLICATE"
    FILE_OUTSIDE_ROOT = "FILE_OUTSIDE_ROOT"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_SYMLINK_NOT_ALLOWED = "FILE_SYMLINK_NOT_ALLOWED"
    FILE_NOT_REGULAR = "FILE_NOT_REGULAR"
    FILE_IDENTITY_DUPLICATE = "FILE_IDENTITY_DUPLICATE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    ARTIFACT_SET_TOO_LARGE = "ARTIFACT_SET_TOO_LARGE"
    FILE_READ_FAILED = "FILE_READ_FAILED"


@dataclass(frozen=True)
class ClassWorldPackageArtifactFileBinding:
    """Explicit package identity to canonical artifact-root-relative file path."""

    package_id: str
    package_version: str
    relative_path: str


@dataclass(frozen=True)
class ClassWorldPackageArtifactFileRead:
    """One canonical binding successfully read for delegated verification."""

    binding: ClassWorldPackageArtifactFileBinding
    bytes_read: int


@dataclass(frozen=True)
class ClassWorldArtifactFileVerificationIssue:
    """One deterministic artifact-file binding or read diagnostic."""

    code: ClassWorldArtifactFileVerificationIssueCode
    message: str
    location: str
    package_id: str | None = None
    binding_index: int | None = None


@dataclass(frozen=True)
class ClassWorldArtifactFileVerificationResult:
    """Atomic bounded file-read result with delegated content verification."""

    contract_version: str
    files: tuple[ClassWorldPackageArtifactFileRead, ...]
    content_verification: ClassWorldArtifactContentVerificationResult | None
    issues: tuple[ClassWorldArtifactFileVerificationIssue, ...]

    @property
    def is_complete(self) -> bool:
        """Whether every bound file was read and content verification completed."""
        return (
            bool(self.files)
            and self.content_verification is not None
            and self.content_verification.is_complete
            and not self.issues
        )
