"""Immutable identity and declared provenance models for class-world releases."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_configuration_models import (
    ClassWorldConfiguration,
    ClassWorldPackagePin,
)

SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION = "0.1"


class ClassWorldReleaseDeclarationIssueCode(StrEnum):
    """Stable machine-readable class-world release declaration issue codes."""

    CONFIGURATION_REQUIRED = "CONFIGURATION_REQUIRED"
    CONFIGURATION_INVALID_TYPE = "CONFIGURATION_INVALID_TYPE"
    CONFIGURATION_INVALID = "CONFIGURATION_INVALID"
    RELEASE_ID_REQUIRED = "RELEASE_ID_REQUIRED"
    RELEASE_ID_INVALID = "RELEASE_ID_INVALID"
    RELEASE_VERSION_REQUIRED = "RELEASE_VERSION_REQUIRED"
    RELEASE_VERSION_INVALID = "RELEASE_VERSION_INVALID"


@dataclass(frozen=True)
class ClassWorldReleaseIdentity:
    """Explicit identity of one intended class-world release declaration."""

    release_id: str
    release_version: str
    class_world_id: str
    class_world_version: str


@dataclass(frozen=True)
class ClassWorldReleaseProvenance:
    """Authoritative version and ordered package inputs declared for a release."""

    engine_version: str
    student_api_version: str
    class_world_manifest_schema_version: str
    manifest_transport_contract_version: str
    cohort_id: str
    package_pins: tuple[ClassWorldPackagePin, ...]


@dataclass(frozen=True)
class ClassWorldReleaseDeclaration:
    """Immutable release identity and provenance tied to one exact configuration."""

    declaration_version: str
    identity: ClassWorldReleaseIdentity
    provenance: ClassWorldReleaseProvenance
    configuration: ClassWorldConfiguration


@dataclass(frozen=True)
class ClassWorldReleaseDeclarationIssue:
    """One deterministic class-world release declaration diagnostic."""

    code: ClassWorldReleaseDeclarationIssueCode
    message: str
    location: str


@dataclass(frozen=True)
class ClassWorldReleaseDeclarationResult:
    """Atomic result of building one class-world release declaration."""

    declaration: ClassWorldReleaseDeclaration | None
    issues: tuple[ClassWorldReleaseDeclarationIssue, ...]

    @property
    def is_built(self) -> bool:
        """Whether one complete immutable release declaration was built."""
        return self.declaration is not None and not self.issues
