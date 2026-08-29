"""Immutable models for deterministic class-world package artifact inventory v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_release_declaration_digest_models import (
    ClassWorldReleaseDeclarationDigest,
)
from explore.packages.class_world_release_declaration_models import (
    ClassWorldReleaseDeclaration,
)

SUPPORTED_CLASS_WORLD_ARTIFACT_INVENTORY_CONTRACT_VERSION = "0.1"
SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM = "sha256"


class ClassWorldArtifactInventoryIssueCode(StrEnum):
    """Stable machine-readable package artifact inventory issue codes."""

    VERIFICATION_RESULT_REQUIRED = "VERIFICATION_RESULT_REQUIRED"
    VERIFICATION_RESULT_INVALID = "VERIFICATION_RESULT_INVALID"
    DECLARATION_NOT_VERIFIED = "DECLARATION_NOT_VERIFIED"
    ARTIFACT_DECLARATIONS_REQUIRED = "ARTIFACT_DECLARATIONS_REQUIRED"
    ARTIFACT_DECLARATION_INVALID_TYPE = "ARTIFACT_DECLARATION_INVALID_TYPE"
    ARTIFACT_PACKAGE_ID_INVALID = "ARTIFACT_PACKAGE_ID_INVALID"
    ARTIFACT_PACKAGE_VERSION_INVALID = "ARTIFACT_PACKAGE_VERSION_INVALID"
    ARTIFACT_DIGEST_ALGORITHM_INVALID = "ARTIFACT_DIGEST_ALGORITHM_INVALID"
    ARTIFACT_DIGEST_INVALID = "ARTIFACT_DIGEST_INVALID"
    ARTIFACT_PACKAGE_DUPLICATE = "ARTIFACT_PACKAGE_DUPLICATE"
    ARTIFACT_PACKAGE_UNEXPECTED = "ARTIFACT_PACKAGE_UNEXPECTED"
    ARTIFACT_PACKAGE_VERSION_MISMATCH = "ARTIFACT_PACKAGE_VERSION_MISMATCH"
    ARTIFACT_PACKAGE_MISSING = "ARTIFACT_PACKAGE_MISSING"


@dataclass(frozen=True)
class ClassWorldPackageArtifactDeclaration:
    """One content-addressed Explorer Package artifact at one exact package pin."""

    package_id: str
    package_version: str
    digest_algorithm: str
    digest_hex: str


@dataclass(frozen=True)
class ClassWorldArtifactInventory:
    """Canonical package artifact inputs for one verified release declaration."""

    contract_version: str
    declaration: ClassWorldReleaseDeclaration
    declaration_digest: ClassWorldReleaseDeclarationDigest
    artifacts: tuple[ClassWorldPackageArtifactDeclaration, ...]


@dataclass(frozen=True)
class ClassWorldArtifactInventoryIssue:
    """One deterministic package artifact inventory diagnostic."""

    code: ClassWorldArtifactInventoryIssueCode
    message: str
    location: str
    package_id: str | None = None
    artifact_index: int | None = None


@dataclass(frozen=True)
class ClassWorldArtifactInventoryResult:
    """Atomic result of building one package artifact inventory."""

    inventory: ClassWorldArtifactInventory | None
    issues: tuple[ClassWorldArtifactInventoryIssue, ...]

    @property
    def is_built(self) -> bool:
        """Whether one complete immutable inventory was built."""
        return self.inventory is not None and not self.issues
