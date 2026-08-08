"""Immutable diagnostics and results for release-declaration JSON schema v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_release_declaration_models import (
    ClassWorldReleaseDeclaration,
    ClassWorldReleaseDeclarationIssue,
)


class ClassWorldReleaseDeclarationSerializationIssueCode(StrEnum):
    """Stable machine-readable release-declaration serialization issue codes."""

    TEXT_REQUIRED = "TEXT_REQUIRED"
    TEXT_INVALID_TYPE = "TEXT_INVALID_TYPE"
    JSON_INVALID = "JSON_INVALID"
    JSON_DUPLICATE_KEY = "JSON_DUPLICATE_KEY"
    JSON_NONFINITE_NUMBER = "JSON_NONFINITE_NUMBER"
    ROOT_INVALID_TYPE = "ROOT_INVALID_TYPE"
    FIELD_REQUIRED = "FIELD_REQUIRED"
    FIELD_UNKNOWN = "FIELD_UNKNOWN"
    FIELD_INVALID_TYPE = "FIELD_INVALID_TYPE"
    FIELD_INVALID_VALUE = "FIELD_INVALID_VALUE"
    SCHEMA_VERSION_UNSUPPORTED = "SCHEMA_VERSION_UNSUPPORTED"
    CLASS_WORLD_ID_MISMATCH = "CLASS_WORLD_ID_MISMATCH"
    CLASS_WORLD_VERSION_MISMATCH = "CLASS_WORLD_VERSION_MISMATCH"
    ENGINE_VERSION_MISMATCH = "ENGINE_VERSION_MISMATCH"
    STUDENT_API_VERSION_MISMATCH = "STUDENT_API_VERSION_MISMATCH"
    MANIFEST_SCHEMA_VERSION_MISMATCH = "MANIFEST_SCHEMA_VERSION_MISMATCH"
    MANIFEST_TRANSPORT_VERSION_MISMATCH = "MANIFEST_TRANSPORT_VERSION_MISMATCH"
    COHORT_ID_MISMATCH = "COHORT_ID_MISMATCH"
    PACKAGE_COUNT_MISMATCH = "PACKAGE_COUNT_MISMATCH"
    PACKAGE_ID_MISMATCH = "PACKAGE_ID_MISMATCH"
    PACKAGE_VERSION_MISMATCH = "PACKAGE_VERSION_MISMATCH"


@dataclass(frozen=True)
class ClassWorldReleaseDeclarationSerializationIssue:
    """One deterministic release-declaration serialization diagnostic."""

    code: ClassWorldReleaseDeclarationSerializationIssueCode
    message: str
    location: str


@dataclass(frozen=True)
class ClassWorldReleaseDeclarationParseResult:
    """Atomic result of parsing one release declaration against a configuration."""

    declaration: ClassWorldReleaseDeclaration | None
    issues: tuple[ClassWorldReleaseDeclarationSerializationIssue, ...]
    declaration_issues: tuple[ClassWorldReleaseDeclarationIssue, ...]

    @property
    def is_parsed(self) -> bool:
        """Whether one complete immutable release declaration was parsed."""
        return self.declaration is not None and not self.issues and not self.declaration_issues
