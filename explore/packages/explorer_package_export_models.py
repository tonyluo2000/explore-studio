"""Immutable models for deterministic Explorer Package exports v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

SUPPORTED_EXPLORER_PACKAGE_EXPORT_CONTRACT_VERSION = "0.1"
SUPPORTED_EXPLORER_PACKAGE_EXPORT_DIGEST_ALGORITHM = "sha256"
EXPLORER_PACKAGE_EXPORT_FILE_MODE = 0o644
MAX_EXPLORER_PACKAGE_EXPORT_MEMBER_BYTES = 64 * 1024 * 1024
MAX_EXPLORER_PACKAGE_EXPORT_CONTENT_BYTES = 256 * 1024 * 1024
MAX_EXPLORER_PACKAGE_EXPORT_ARCHIVE_BYTES = 260 * 1024 * 1024


class ExplorerPackageExportIssueCode(StrEnum):
    """Stable machine-readable export diagnostics."""

    PACKAGE_ROOT_REQUIRED = "PACKAGE_ROOT_REQUIRED"
    PACKAGE_ROOT_INVALID_TYPE = "PACKAGE_ROOT_INVALID_TYPE"
    PACKAGE_ROOT_NOT_ABSOLUTE = "PACKAGE_ROOT_NOT_ABSOLUTE"
    PACKAGE_ROOT_NOT_FOUND = "PACKAGE_ROOT_NOT_FOUND"
    PACKAGE_ROOT_SYMLINK_NOT_ALLOWED = "PACKAGE_ROOT_SYMLINK_NOT_ALLOWED"
    PACKAGE_ROOT_NOT_DIRECTORY = "PACKAGE_ROOT_NOT_DIRECTORY"
    PACKAGE_ROOT_INSPECTION_FAILED = "PACKAGE_ROOT_INSPECTION_FAILED"
    PACKAGE_NOT_VALID = "PACKAGE_NOT_VALID"
    PACKAGE_NOT_LOADED = "PACKAGE_NOT_LOADED"
    DESCRIPTOR_CONFINEMENT_UNAVAILABLE = "DESCRIPTOR_CONFINEMENT_UNAVAILABLE"
    MEMBER_NOT_FOUND = "MEMBER_NOT_FOUND"
    MEMBER_SYMLINK_NOT_ALLOWED = "MEMBER_SYMLINK_NOT_ALLOWED"
    MEMBER_NOT_REGULAR = "MEMBER_NOT_REGULAR"
    MEMBER_TOO_LARGE = "MEMBER_TOO_LARGE"
    CONTENT_TOO_LARGE = "CONTENT_TOO_LARGE"
    MEMBER_READ_FAILED = "MEMBER_READ_FAILED"
    PACKAGE_CHANGED = "PACKAGE_CHANGED"
    DESTINATION_REQUIRED = "DESTINATION_REQUIRED"
    DESTINATION_INVALID_TYPE = "DESTINATION_INVALID_TYPE"
    DESTINATION_NOT_ABSOLUTE = "DESTINATION_NOT_ABSOLUTE"
    DESTINATION_NAME_MISMATCH = "DESTINATION_NAME_MISMATCH"
    DESTINATION_PARENT_NOT_FOUND = "DESTINATION_PARENT_NOT_FOUND"
    DESTINATION_PARENT_SYMLINK_NOT_ALLOWED = "DESTINATION_PARENT_SYMLINK_NOT_ALLOWED"
    DESTINATION_PARENT_NOT_DIRECTORY = "DESTINATION_PARENT_NOT_DIRECTORY"
    DESTINATION_EXISTS = "DESTINATION_EXISTS"
    ARCHIVE_WRITE_FAILED = "ARCHIVE_WRITE_FAILED"
    ARCHIVE_CLEANUP_FAILED = "ARCHIVE_CLEANUP_FAILED"


@dataclass(frozen=True)
class ExplorerPackageExportEntry:
    """One canonical regular-file member in export order."""

    relative_path: str
    digest_algorithm: str
    digest_hex: str
    bytes_written: int
    mode: int


@dataclass(frozen=True)
class ExplorerPackageExportArtifact:
    """Canonical metadata for one Explorer Package export archive."""

    contract_version: str
    package_id: str
    package_version: str
    student_api_version: str
    entries: tuple[ExplorerPackageExportEntry, ...]
    total_content_bytes: int


@dataclass(frozen=True)
class ExplorerPackageExportDigest:
    """SHA-256 identity of the complete raw archive bytes."""

    algorithm: str
    hex_digest: str


@dataclass(frozen=True)
class ExplorerPackageExportIssue:
    """One deterministic export diagnostic."""

    code: ExplorerPackageExportIssueCode
    message: str
    location: str
    member_path: str | None = None
    member_index: int | None = None


@dataclass(frozen=True)
class ExplorerPackageExportResult:
    """Atomic deterministic Explorer Package export result."""

    artifact: ExplorerPackageExportArtifact | None
    digest: ExplorerPackageExportDigest | None
    bytes_written: int
    issues: tuple[ExplorerPackageExportIssue, ...]

    @property
    def is_exported(self) -> bool:
        """Whether one complete archive was atomically written."""
        return (
            self.artifact is not None
            and self.digest is not None
            and self.bytes_written > 0
            and not self.issues
        )
