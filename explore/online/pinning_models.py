"""Immutable models for exact approved-version Class-World pinning."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from explore.online.models import AssuranceLevel, CohortRole, PackageVersionIdentity
from explore.online.registry_models import RegistryCompatibility
from explore.packages.policy import is_valid_identifier, is_valid_semantic_version

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}", re.ASCII)
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


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase 64-character SHA-256 digest")


def _require_utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field} must use UTC")


@dataclass(frozen=True)
class ClassWorldConfigurationBinding:
    """Immutable server-side fingerprint for one validated configuration identity."""

    class_world_id: str
    class_world_version: str
    configuration_sha256: str
    cohort_id: str
    student_api_version: str

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.class_world_id):
            raise ValueError("class_world_id must be a valid lower-kebab-case identifier")
        if not is_valid_semantic_version(self.class_world_version):
            raise ValueError("class_world_version must be an exact Semantic Version")
        _require_sha256(self.configuration_sha256, "configuration_sha256")
        if not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        _require_text(self.student_api_version, "student_api_version", maximum=64)

    @property
    def identity(self) -> tuple[str, str]:
        return (self.class_world_id, self.class_world_version)


@dataclass(frozen=True)
class ClassWorldPinRequest:
    """Exact pin intent containing no trusted owner, cohort, digest, or state."""

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
class PinAuthoritySnapshot:
    """Authoritative course-admin membership captured at pin time."""

    cohort_id: str
    actor_id: str
    role: CohortRole
    assurance: AssuranceLevel
    granted_by_actor_id: str
    granted_at: datetime
    revision: int
    active: bool

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        _require_uuid(self.actor_id, "actor_id")
        if self.role is not CohortRole.COURSE_ADMIN:
            raise ValueError("pin authority role must be course-admin")
        if self.assurance is not AssuranceLevel.AAL2:
            raise ValueError("pin authority assurance must be AAL2/MFA")
        _require_uuid(self.granted_by_actor_id, "granted_by_actor_id")
        _require_utc(self.granted_at, "granted_at")
        if (
            not isinstance(self.revision, int)
            or isinstance(self.revision, bool)
            or self.revision < 1
        ):
            raise ValueError("revision must be a positive integer")
        if self.active is not True:
            raise ValueError("pin authority snapshot must be active")


@dataclass(frozen=True)
class ClassWorldPackagePinRecord:
    """One immutable binding from a configuration to an approved exact artifact."""

    pin_id: str
    class_world_id: str
    class_world_version: str
    configuration_sha256: str
    package_version: PackageVersionIdentity
    cohort_id: str
    owner_actor_id: str
    compatibility: RegistryCompatibility
    artifact_reference: str
    approval_decision_id: str
    authority: PinAuthoritySnapshot
    pinned_at: datetime
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _require_uuid(self.pin_id, "pin_id", version=4)
        if not is_valid_identifier(self.class_world_id):
            raise ValueError("class_world_id must be a valid lower-kebab-case identifier")
        if not is_valid_semantic_version(self.class_world_version):
            raise ValueError("class_world_version must be an exact Semantic Version")
        _require_sha256(self.configuration_sha256, "configuration_sha256")
        if not isinstance(self.package_version, PackageVersionIdentity):
            raise ValueError("package_version must be a PackageVersionIdentity")
        if not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        _require_uuid(self.owner_actor_id, "owner_actor_id")
        if not isinstance(self.compatibility, RegistryCompatibility):
            raise ValueError("compatibility must be RegistryCompatibility")
        _require_uuid(self.artifact_reference, "artifact_reference", version=4)
        _require_uuid(self.approval_decision_id, "approval_decision_id", version=4)
        if not isinstance(self.authority, PinAuthoritySnapshot):
            raise ValueError("authority must be a PinAuthoritySnapshot")
        if self.authority.cohort_id != self.cohort_id:
            raise ValueError("pin authority cohort must match the package cohort")
        _require_utc(self.pinned_at, "pinned_at")
        _require_text(self.correlation_id, "correlation_id", maximum=128)
        _require_text(self.idempotency_key, "idempotency_key", maximum=128)

    @property
    def configuration_identity(self) -> tuple[str, str]:
        return (self.class_world_id, self.class_world_version)


@dataclass(frozen=True)
class ClassWorldPinReceipt:
    """Result of one authorized exact-version pin operation."""

    pin: ClassWorldPackagePinRecord
    replayed: bool


class PinAuthenticationError(PermissionError):
    """The verified external identity has no immutable actor binding."""


class PinAccessDeniedError(PermissionError):
    """Pinning is denied without revealing package or approval existence."""


class PinConfigurationError(ValueError):
    """The authoritative Class-World configuration is invalid or lacks the pin."""


class PinConflictError(RuntimeError):
    """A pin, replay, or immutable configuration binding conflicts."""


__all__ = [
    "ClassWorldConfigurationBinding",
    "ClassWorldPackagePinRecord",
    "ClassWorldPinReceipt",
    "ClassWorldPinRequest",
    "PinAccessDeniedError",
    "PinAuthenticationError",
    "PinAuthoritySnapshot",
    "PinConfigurationError",
    "PinConflictError",
]
