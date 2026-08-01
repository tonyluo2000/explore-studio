"""Immutable diagnostics and results for class-world manifest file transport v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_configuration_models import ClassWorldConfiguration
from explore.packages.class_world_manifest_models import ClassWorldManifestIssue

MAX_CLASS_WORLD_MANIFEST_BYTES = 1 * 1024 * 1024


class ClassWorldManifestFileIssueCode(StrEnum):
    """Stable machine-readable manifest file-transport issue codes."""

    PATH_REQUIRED = "PATH_REQUIRED"
    PATH_INVALID_TYPE = "PATH_INVALID_TYPE"
    PARENT_NOT_FOUND = "PARENT_NOT_FOUND"
    PARENT_NOT_DIRECTORY = "PARENT_NOT_DIRECTORY"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_NOT_REGULAR = "FILE_NOT_REGULAR"
    FILE_SYMLINK_NOT_ALLOWED = "FILE_SYMLINK_NOT_ALLOWED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FILE_READ_FAILED = "FILE_READ_FAILED"
    FILE_INVALID_UTF8 = "FILE_INVALID_UTF8"
    MANIFEST_BOM_NOT_ALLOWED = "MANIFEST_BOM_NOT_ALLOWED"
    MANIFEST_INVALID = "MANIFEST_INVALID"
    DESTINATION_IS_DIRECTORY = "DESTINATION_IS_DIRECTORY"
    DESTINATION_NOT_REGULAR = "DESTINATION_NOT_REGULAR"
    TEMP_FILE_CREATE_FAILED = "TEMP_FILE_CREATE_FAILED"
    FILE_WRITE_FAILED = "FILE_WRITE_FAILED"
    FILE_FLUSH_FAILED = "FILE_FLUSH_FAILED"
    FILE_SYNC_FAILED = "FILE_SYNC_FAILED"
    ATOMIC_REPLACE_FAILED = "ATOMIC_REPLACE_FAILED"
    TEMP_FILE_CLEANUP_FAILED = "TEMP_FILE_CLEANUP_FAILED"


@dataclass(frozen=True)
class ClassWorldManifestFileIssue:
    """One deterministic class-world manifest file-transport diagnostic."""

    code: ClassWorldManifestFileIssueCode
    message: str
    location: str


@dataclass(frozen=True)
class ClassWorldManifestFileReadResult:
    """Atomic result of reading and parsing one local manifest file."""

    configuration: ClassWorldConfiguration | None
    issues: tuple[ClassWorldManifestFileIssue, ...]
    manifest_issues: tuple[ClassWorldManifestIssue, ...]

    @property
    def is_read(self) -> bool:
        """Whether a complete validated configuration was read."""
        return self.configuration is not None and not self.issues and not self.manifest_issues


@dataclass(frozen=True)
class ClassWorldManifestFileWriteResult:
    """Atomic result of writing one canonical local manifest file."""

    bytes_written: int
    issues: tuple[ClassWorldManifestFileIssue, ...]

    @property
    def is_written(self) -> bool:
        """Whether the complete encoded manifest replaced the destination."""
        return self.bytes_written > 0 and not self.issues
