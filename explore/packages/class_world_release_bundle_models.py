"""Immutable models for deterministic Class-World release bundles v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_assembled_output_manifest_models import (
    ClassWorldAssembledOutputManifest,
    ClassWorldAssembledOutputManifestDigest,
)
from explore.packages.class_world_release_declaration_digest_models import (
    ClassWorldReleaseDeclarationDigest,
)
from explore.packages.class_world_release_declaration_models import (
    ClassWorldReleaseDeclaration,
)

SUPPORTED_CLASS_WORLD_RELEASE_BUNDLE_CONTRACT_VERSION = "0.1"
SUPPORTED_CLASS_WORLD_RELEASE_BUNDLE_DIGEST_ALGORITHM = "sha256"
CLASS_WORLD_RELEASE_BUNDLE_DECLARATION_PATH = "metadata/class-world.release.json"
CLASS_WORLD_RELEASE_BUNDLE_OUTPUT_MANIFEST_PATH = "metadata/assembled-output.manifest.json"
CLASS_WORLD_RELEASE_BUNDLE_FILE_MODE = 0o644
MAX_CLASS_WORLD_RELEASE_BUNDLE_BYTES = 260 * 1024 * 1024


class ClassWorldReleaseBundleIssueCode(StrEnum):
    """Stable machine-readable release-bundle diagnostics."""

    OUTPUT_TREE_RESULT_REQUIRED = "OUTPUT_TREE_RESULT_REQUIRED"
    OUTPUT_TREE_RESULT_INVALID = "OUTPUT_TREE_RESULT_INVALID"
    OUTPUT_TREE_NOT_VERIFIED = "OUTPUT_TREE_NOT_VERIFIED"
    OUTPUT_TREE_INCONSISTENT = "OUTPUT_TREE_INCONSISTENT"
    OUTPUT_ROOT_REQUIRED = "OUTPUT_ROOT_REQUIRED"
    OUTPUT_ROOT_INVALID_TYPE = "OUTPUT_ROOT_INVALID_TYPE"
    OUTPUT_ROOT_NOT_ABSOLUTE = "OUTPUT_ROOT_NOT_ABSOLUTE"
    OUTPUT_ROOT_INVALID = "OUTPUT_ROOT_INVALID"
    OUTPUT_ROOT_NOT_FOUND = "OUTPUT_ROOT_NOT_FOUND"
    OUTPUT_ROOT_SYMLINK_NOT_ALLOWED = "OUTPUT_ROOT_SYMLINK_NOT_ALLOWED"
    OUTPUT_ROOT_NOT_DIRECTORY = "OUTPUT_ROOT_NOT_DIRECTORY"
    OUTPUT_ROOT_INSPECTION_FAILED = "OUTPUT_ROOT_INSPECTION_FAILED"
    DESCRIPTOR_CONFINEMENT_UNAVAILABLE = "DESCRIPTOR_CONFINEMENT_UNAVAILABLE"
    PAYLOAD_READ_FAILED = "PAYLOAD_READ_FAILED"
    PAYLOAD_MISMATCH = "PAYLOAD_MISMATCH"
    DESTINATION_REQUIRED = "DESTINATION_REQUIRED"
    DESTINATION_INVALID_TYPE = "DESTINATION_INVALID_TYPE"
    DESTINATION_NOT_ABSOLUTE = "DESTINATION_NOT_ABSOLUTE"
    DESTINATION_INVALID = "DESTINATION_INVALID"
    DESTINATION_PARENT_NOT_FOUND = "DESTINATION_PARENT_NOT_FOUND"
    DESTINATION_PARENT_SYMLINK_NOT_ALLOWED = "DESTINATION_PARENT_SYMLINK_NOT_ALLOWED"
    DESTINATION_PARENT_NOT_DIRECTORY = "DESTINATION_PARENT_NOT_DIRECTORY"
    DESTINATION_EXISTS = "DESTINATION_EXISTS"
    ARCHIVE_WRITE_FAILED = "ARCHIVE_WRITE_FAILED"
    ARCHIVE_PUBLISH_FAILED = "ARCHIVE_PUBLISH_FAILED"
    ARCHIVE_CLEANUP_FAILED = "ARCHIVE_CLEANUP_FAILED"
    PATH_REQUIRED = "PATH_REQUIRED"
    PATH_INVALID_TYPE = "PATH_INVALID_TYPE"
    PATH_NOT_ABSOLUTE = "PATH_NOT_ABSOLUTE"
    PATH_INVALID = "PATH_INVALID"
    EXPECTED_DIGEST_INVALID = "EXPECTED_DIGEST_INVALID"
    ARCHIVE_NOT_FOUND = "ARCHIVE_NOT_FOUND"
    ARCHIVE_SYMLINK_NOT_ALLOWED = "ARCHIVE_SYMLINK_NOT_ALLOWED"
    ARCHIVE_NOT_REGULAR = "ARCHIVE_NOT_REGULAR"
    ARCHIVE_TOO_LARGE = "ARCHIVE_TOO_LARGE"
    ARCHIVE_READ_FAILED = "ARCHIVE_READ_FAILED"
    ARCHIVE_INVALID = "ARCHIVE_INVALID"
    ARCHIVE_MEMBER_MISMATCH = "ARCHIVE_MEMBER_MISMATCH"
    ARCHIVE_METADATA_MISMATCH = "ARCHIVE_METADATA_MISMATCH"
    ARCHIVE_CONTENT_MISMATCH = "ARCHIVE_CONTENT_MISMATCH"


@dataclass(frozen=True)
class ClassWorldReleaseBundleEntry:
    """One canonical regular-file member in release-bundle order."""

    relative_path: str
    digest_algorithm: str
    digest_hex: str
    bytes_written: int
    mode: int


@dataclass(frozen=True)
class ClassWorldReleaseBundle:
    """Canonical metadata and member projection for one release archive."""

    contract_version: str
    declaration: ClassWorldReleaseDeclaration
    declaration_digest: ClassWorldReleaseDeclarationDigest
    output_manifest: ClassWorldAssembledOutputManifest
    output_manifest_digest: ClassWorldAssembledOutputManifestDigest
    entries: tuple[ClassWorldReleaseBundleEntry, ...]
    total_content_bytes: int


@dataclass(frozen=True)
class ClassWorldReleaseBundleDigest:
    """SHA-256 identity of the complete deterministic archive bytes."""

    algorithm: str
    hex_digest: str


@dataclass(frozen=True)
class ClassWorldReleaseBundleIssue:
    """One deterministic release-bundle diagnostic."""

    code: ClassWorldReleaseBundleIssueCode
    message: str
    location: str
    package_id: str | None = None
    package_index: int | None = None


@dataclass(frozen=True)
class ClassWorldReleaseBundleWriteResult:
    """Atomic deterministic release-bundle write result."""

    bundle: ClassWorldReleaseBundle | None
    digest: ClassWorldReleaseBundleDigest | None
    bytes_written: int
    issues: tuple[ClassWorldReleaseBundleIssue, ...]

    @property
    def is_written(self) -> bool:
        """Whether one complete bundle was atomically published."""
        return (
            self.bundle is not None
            and self.digest is not None
            and self.bytes_written > 0
            and not self.issues
        )


@dataclass(frozen=True)
class ClassWorldReleaseBundleVerificationResult:
    """Bounded release-bundle readback and digest-comparison result."""

    bundle: ClassWorldReleaseBundle | None
    expected_digest: ClassWorldReleaseBundleDigest | None
    actual_digest: ClassWorldReleaseBundleDigest | None
    matches: bool | None
    bytes_read: int
    issues: tuple[ClassWorldReleaseBundleIssue, ...]

    @property
    def is_verified(self) -> bool:
        """Whether structure, contents, metadata, and whole-bundle digest match."""
        return (
            self.bundle is not None
            and self.expected_digest is not None
            and self.actual_digest is not None
            and self.matches is True
            and self.bytes_read > 0
            and not self.issues
        )
