"""Immutable models for deterministic assembled-output manifests v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_verified_materialization_models import (
    ClassWorldVerifiedMaterialization,
)

SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_CONTRACT_VERSION = "0.1"
SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_DIGEST_ALGORITHM = "sha256"


class ClassWorldAssembledOutputManifestIssueCode(StrEnum):
    """Stable machine-readable assembled-output manifest issue codes."""

    MATERIALIZATION_RESULT_REQUIRED = "MATERIALIZATION_RESULT_REQUIRED"
    MATERIALIZATION_RESULT_INVALID = "MATERIALIZATION_RESULT_INVALID"
    MATERIALIZATION_NOT_COMPLETE = "MATERIALIZATION_NOT_COMPLETE"
    MATERIALIZATION_INCONSISTENT = "MATERIALIZATION_INCONSISTENT"


@dataclass(frozen=True)
class ClassWorldAssembledOutputPackage:
    """One exact plan-authorized package in the published output."""

    package_id: str
    package_version: str
    digest_algorithm: str
    digest_hex: str
    relative_path: str
    bytes_written: int


@dataclass(frozen=True)
class ClassWorldAssembledOutputManifest:
    """Canonical package identity and path projection of one materialization."""

    contract_version: str
    materialization: ClassWorldVerifiedMaterialization
    packages: tuple[ClassWorldAssembledOutputPackage, ...]
    total_bytes: int


@dataclass(frozen=True)
class ClassWorldAssembledOutputManifestDigest:
    """SHA-256 identity of one canonical assembled-output manifest."""

    algorithm: str
    hex_digest: str


@dataclass(frozen=True)
class ClassWorldAssembledOutputManifestIssue:
    """One deterministic assembled-output manifest diagnostic."""

    code: ClassWorldAssembledOutputManifestIssueCode
    message: str
    location: str


@dataclass(frozen=True)
class ClassWorldAssembledOutputManifestResult:
    """Atomic manifest and digest composition result."""

    manifest: ClassWorldAssembledOutputManifest | None
    digest: ClassWorldAssembledOutputManifestDigest | None
    issues: tuple[ClassWorldAssembledOutputManifestIssue, ...]

    @property
    def is_built(self) -> bool:
        """Whether one complete manifest and digest were composed."""
        return self.manifest is not None and self.digest is not None and not self.issues
