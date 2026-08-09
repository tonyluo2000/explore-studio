"""Immutable models for release-declaration file transport v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_release_declaration_models import (
    ClassWorldReleaseDeclaration,
    ClassWorldReleaseDeclarationIssue,
)
from explore.packages.class_world_release_declaration_serialization_models import (
    ClassWorldReleaseDeclarationSerializationIssue,
)

MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES = 1 * 1024 * 1024
SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_TRANSPORT_CONTRACT_VERSION = "0.1"


class ClassWorldReleaseDeclarationFileIssueCode(StrEnum):
    """Stable machine-readable release-declaration file issue codes."""

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
    DECLARATION_BOM_NOT_ALLOWED = "DECLARATION_BOM_NOT_ALLOWED"
    DECLARATION_INVALID = "DECLARATION_INVALID"
    DESTINATION_IS_DIRECTORY = "DESTINATION_IS_DIRECTORY"
    DESTINATION_NOT_REGULAR = "DESTINATION_NOT_REGULAR"
    TEMP_FILE_CREATE_FAILED = "TEMP_FILE_CREATE_FAILED"
    FILE_WRITE_FAILED = "FILE_WRITE_FAILED"
    FILE_FLUSH_FAILED = "FILE_FLUSH_FAILED"
    FILE_SYNC_FAILED = "FILE_SYNC_FAILED"
    ATOMIC_REPLACE_FAILED = "ATOMIC_REPLACE_FAILED"
    TEMP_FILE_CLEANUP_FAILED = "TEMP_FILE_CLEANUP_FAILED"


@dataclass(frozen=True)
class ClassWorldReleaseDeclarationFileIssue:
    """One deterministic release-declaration file-transport diagnostic."""

    code: ClassWorldReleaseDeclarationFileIssueCode
    message: str
    location: str


@dataclass(frozen=True)
class ClassWorldReleaseDeclarationFileReadResult:
    """Atomic result of reading and parsing one local release declaration."""

    declaration: ClassWorldReleaseDeclaration | None
    issues: tuple[ClassWorldReleaseDeclarationFileIssue, ...]
    serialization_issues: tuple[ClassWorldReleaseDeclarationSerializationIssue, ...]
    declaration_issues: tuple[ClassWorldReleaseDeclarationIssue, ...]

    @property
    def is_read(self) -> bool:
        """Whether one complete validated release declaration was read."""
        return (
            self.declaration is not None
            and not self.issues
            and not self.serialization_issues
            and not self.declaration_issues
        )


@dataclass(frozen=True)
class ClassWorldReleaseDeclarationFileWriteResult:
    """Atomic result of writing one canonical local release declaration."""

    bytes_written: int
    issues: tuple[ClassWorldReleaseDeclarationFileIssue, ...]

    @property
    def is_written(self) -> bool:
        """Whether all encoded bytes atomically replaced the destination."""
        return self.bytes_written > 0 and not self.issues
