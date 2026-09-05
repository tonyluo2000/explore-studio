"""Immutable models for authoritative server-side Class-World configurations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from explore.online.models import AssuranceLevel, CohortRole
from explore.packages import ClassWorldConfiguration
from explore.packages.policy import is_valid_identifier, is_valid_semantic_version

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}", re.ASCII)
_CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x1f\x7f]", re.ASCII)
_AUTHORITATIVE_SEAL = object()


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
class ConfigurationAuthoritySnapshot:
    """Authoritative course-admin membership captured for configuration creation."""

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
            raise ValueError("configuration authority role must be course-admin")
        if self.assurance is not AssuranceLevel.AAL2:
            raise ValueError("configuration authority assurance must be AAL2/MFA")
        _require_uuid(self.granted_by_actor_id, "granted_by_actor_id")
        _require_utc(self.granted_at, "granted_at")
        if (
            not isinstance(self.revision, int)
            or isinstance(self.revision, bool)
            or self.revision < 1
        ):
            raise ValueError("revision must be a positive integer")
        if self.active is not True:
            raise ValueError("configuration authority snapshot must be active")


@dataclass(frozen=True)
class PreparedClassWorldConfiguration:
    """Trusted internal canonicalization result; never a request model."""

    configuration: ClassWorldConfiguration
    canonical_bytes: bytes
    configuration_sha256: str
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _AUTHORITATIVE_SEAL:
            raise TypeError("prepared configurations may be created only by the trusted boundary")
        if not isinstance(self.configuration, ClassWorldConfiguration):
            raise ValueError("configuration must be a ClassWorldConfiguration")
        if type(self.canonical_bytes) is not bytes or not self.canonical_bytes:
            raise ValueError("canonical_bytes must be non-empty immutable bytes")
        _require_sha256(self.configuration_sha256, "configuration_sha256")


@dataclass(frozen=True)
class StoredClassWorldConfiguration:
    """One immutable persisted configuration identity and canonical byte record."""

    locator: str
    class_world_id: str
    class_world_version: str
    configuration_sha256: str
    cohort_id: str
    student_api_version: str
    canonical_bytes: bytes
    authority: ConfigurationAuthoritySnapshot
    created_at: datetime
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _require_uuid(self.locator, "locator", version=4)
        if not is_valid_identifier(self.class_world_id):
            raise ValueError("class_world_id must be a valid lower-kebab-case identifier")
        if not is_valid_semantic_version(self.class_world_version):
            raise ValueError("class_world_version must be an exact Semantic Version")
        _require_sha256(self.configuration_sha256, "configuration_sha256")
        if not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        _require_text(self.student_api_version, "student_api_version", maximum=64)
        if type(self.canonical_bytes) is not bytes or not self.canonical_bytes:
            raise ValueError("canonical_bytes must be non-empty immutable bytes")
        if not isinstance(self.authority, ConfigurationAuthoritySnapshot):
            raise ValueError("authority must be a ConfigurationAuthoritySnapshot")
        if self.authority.cohort_id != self.cohort_id:
            raise ValueError("configuration authority cohort must match configuration cohort")
        _require_utc(self.created_at, "created_at")
        _require_text(self.correlation_id, "correlation_id", maximum=128)
        _require_text(self.idempotency_key, "idempotency_key", maximum=128)

    @property
    def identity(self) -> tuple[str, str]:
        return (self.class_world_id, self.class_world_version)


@dataclass(frozen=True)
class AuthoritativeClassWorldConfiguration:
    """A configuration reconstructed and verified from immutable server state."""

    record: StoredClassWorldConfiguration
    configuration: ClassWorldConfiguration
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _AUTHORITATIVE_SEAL:
            raise TypeError("authoritative configurations may be created only by the loader")
        if not isinstance(self.record, StoredClassWorldConfiguration):
            raise ValueError("record must be a StoredClassWorldConfiguration")
        if not isinstance(self.configuration, ClassWorldConfiguration):
            raise ValueError("configuration must be a ClassWorldConfiguration")
        if self.configuration.identity != self.record.identity:
            raise ValueError("loaded configuration identity must match its immutable record")


@dataclass(frozen=True)
class ConfigurationCreateRequest:
    """Create intent with no caller-controlled configuration fields."""

    expected_revision: int
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        if self.expected_revision != 0:
            raise ValueError("immutable configuration creation requires expected_revision 0")
        _require_text(self.correlation_id, "correlation_id", maximum=128)
        _require_text(self.idempotency_key, "idempotency_key", maximum=128)


@dataclass(frozen=True)
class ConfigurationLoadRequest:
    """Opaque exact load intent for pinning; no latest or mutable claims."""

    locator: str
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _require_uuid(self.locator, "locator", version=4)
        _require_text(self.correlation_id, "correlation_id", maximum=128)
        _require_text(self.idempotency_key, "idempotency_key", maximum=128)


@dataclass(frozen=True)
class ConfigurationCreateReceipt:
    record: StoredClassWorldConfiguration
    replayed: bool


@dataclass(frozen=True)
class ConfigurationLoadReceipt:
    loaded: AuthoritativeClassWorldConfiguration
    replayed: bool


class ConfigurationAuthenticationError(PermissionError):
    """The verified external identity has no immutable actor binding."""


class ConfigurationAccessDeniedError(PermissionError):
    """Configuration access is denied without revealing locator existence."""


class ConfigurationConflictError(RuntimeError):
    """Configuration identity, idempotency, or immutable bytes conflict."""


class ConfigurationIntegrityError(RuntimeError):
    """Persisted configuration state failed authoritative reconstruction."""


def _prepared(
    configuration: ClassWorldConfiguration,
    canonical_bytes: bytes,
    configuration_sha256: str,
) -> PreparedClassWorldConfiguration:
    return PreparedClassWorldConfiguration(
        configuration,
        canonical_bytes,
        configuration_sha256,
        _AUTHORITATIVE_SEAL,
    )


def _loaded(
    record: StoredClassWorldConfiguration,
    configuration: ClassWorldConfiguration,
) -> AuthoritativeClassWorldConfiguration:
    return AuthoritativeClassWorldConfiguration(record, configuration, _AUTHORITATIVE_SEAL)


__all__ = [
    "AuthoritativeClassWorldConfiguration",
    "ConfigurationAccessDeniedError",
    "ConfigurationAuthenticationError",
    "ConfigurationAuthoritySnapshot",
    "ConfigurationConflictError",
    "ConfigurationCreateReceipt",
    "ConfigurationCreateRequest",
    "ConfigurationIntegrityError",
    "ConfigurationLoadReceipt",
    "ConfigurationLoadRequest",
    "PreparedClassWorldConfiguration",
    "StoredClassWorldConfiguration",
]
