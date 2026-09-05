"""Immutable models for the approved-only Phase E registry projection."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from explore.online.models import PackageVersionIdentity
from explore.packages.policy import is_valid_identifier, is_valid_semantic_version

_CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x1f\x7f]", re.ASCII)


def _require_text(value: str, field: str, *, maximum: int) -> None:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{field} must contain 1 to {maximum} characters")
    if _CONTROL_CHARACTER_PATTERN.search(value) is not None:
        raise ValueError(f"{field} must not contain control characters")


def _require_uuid(value: str, field: str, *, version: int | None = None) -> None:
    _require_text(value, field, maximum=36)
    try:
        parsed = UUID(value)
    except ValueError as error:
        raise ValueError(f"{field} must be a canonical UUID") from error
    if str(parsed) != value or (version is not None and parsed.version != version):
        qualifier = f" version {version}" if version is not None else ""
        raise ValueError(f"{field} must be a canonical lowercase UUID{qualifier}")


def _require_utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field} must use UTC")


class RegistryScope(StrEnum):
    """Approved registry visibility boundary."""

    COHORT = "cohort"


@dataclass(frozen=True)
class RegistryCompatibility:
    """Validated compatibility projected from immutable submission provenance."""

    student_api_version: str

    def __post_init__(self) -> None:
        _require_text(self.student_api_version, "student_api_version", maximum=64)


@dataclass(frozen=True)
class ApprovedRegistryEntry:
    """One currently approved exact-version projection; never a mutable record."""

    package_version: PackageVersionIdentity
    owner_actor_id: str
    cohort_id: str
    scope: RegistryScope
    compatibility: RegistryCompatibility
    artifact_reference: str
    approval_decision_id: str
    approved_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.package_version, PackageVersionIdentity):
            raise ValueError("package_version must be a PackageVersionIdentity")
        _require_uuid(self.owner_actor_id, "owner_actor_id")
        if not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        if self.scope is not RegistryScope.COHORT:
            raise ValueError("scope must be cohort")
        if not isinstance(self.compatibility, RegistryCompatibility):
            raise ValueError("compatibility must be RegistryCompatibility")
        _require_uuid(self.artifact_reference, "artifact_reference", version=4)
        _require_uuid(self.approval_decision_id, "approval_decision_id", version=4)
        _require_utc(self.approved_at, "approved_at")


@dataclass(frozen=True)
class RegistryExactLookup:
    """Exact lookup intent with no trusted owner, cohort, digest, or state claims."""

    package_id: str
    semantic_version: str
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.package_id):
            raise ValueError("package_id must be a valid lower-kebab-case identifier")
        if not is_valid_semantic_version(self.semantic_version):
            raise ValueError("semantic_version must be an exact Semantic Version")
        _require_text(self.correlation_id, "correlation_id", maximum=128)
        _require_text(self.idempotency_key, "idempotency_key", maximum=128)


@dataclass(frozen=True)
class RegistryReadReceipt:
    """One authorized exact projection read."""

    entry: ApprovedRegistryEntry
    replayed: bool


class RegistryAuthenticationError(PermissionError):
    """The verified external identity has no immutable actor binding."""


class RegistryAccessDeniedError(PermissionError):
    """Lookup is denied without revealing package or approval existence."""


class RegistryConflictError(RuntimeError):
    """An idempotency replay conflicts with a completed registry read."""


__all__ = [
    "ApprovedRegistryEntry",
    "RegistryAccessDeniedError",
    "RegistryAuthenticationError",
    "RegistryCompatibility",
    "RegistryConflictError",
    "RegistryExactLookup",
    "RegistryReadReceipt",
    "RegistryScope",
]
