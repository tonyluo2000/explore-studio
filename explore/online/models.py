"""Immutable identity, ownership, and audit models for trusted online services."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from urllib.parse import urlsplit
from uuid import UUID

from explore.packages.policy import is_valid_identifier, is_valid_semantic_version

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}", re.ASCII)
_CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x1f\x7f]", re.ASCII)
_SENSITIVE_AUDIT_KEYS = frozenset({"date_of_birth", "email", "provider_subject", "subject"})


class AssuranceLevel(StrEnum):
    """NIST-aligned assurance levels accepted from the configured IdP."""

    AAL1 = "aal1"
    AAL2 = "aal2"


class CohortRole(StrEnum):
    """Approved human roles, each scoped to one cohort."""

    STUDENT = "student"
    TEACHER = "teacher"
    COURSE_ADMIN = "course-admin"


class NamespacePermission(StrEnum):
    """Explicit permissions grantable for one package namespace."""

    SUBMIT = "submit"


class PrincipalKind(StrEnum):
    """Kinds of authenticated principals recorded by trusted services."""

    ACTOR = "actor"
    SERVICE = "service"


def _require_text(value: str, field: str, *, maximum: int) -> None:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{field} must contain 1 to {maximum} characters")
    if _CONTROL_CHARACTER_PATTERN.search(value) is not None:
        raise ValueError(f"{field} must not contain control characters")


def _require_actor_id(value: str, field: str = "actor_id") -> None:
    _require_text(value, field, maximum=36)
    try:
        parsed = UUID(value)
    except ValueError as error:
        raise ValueError(f"{field} must be a canonical UUID") from error
    if str(parsed) != value:
        raise ValueError(f"{field} must be a canonical lowercase UUID")


def _require_utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field} must use UTC")


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase 64-character SHA-256 digest")


@dataclass(frozen=True)
class IdentityProvider:
    """One explicitly approved federated OIDC issuer."""

    issuer: str
    privileged_assurance: AssuranceLevel = AssuranceLevel.AAL2

    def __post_init__(self) -> None:
        _require_text(self.issuer, "issuer", maximum=512)
        parsed = urlsplit(self.issuer)
        if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("issuer must be an absolute HTTPS URL without query or fragment")
        if not isinstance(self.privileged_assurance, AssuranceLevel):
            raise ValueError("privileged_assurance must be an AssuranceLevel")
        if self.privileged_assurance is not AssuranceLevel.AAL2:
            raise ValueError("privileged_assurance must require AAL2/MFA")


@dataclass(frozen=True)
class Actor:
    """One stable internal human identity, independent of mutable profile fields."""

    actor_id: str
    created_at: datetime

    def __post_init__(self) -> None:
        _require_actor_id(self.actor_id)
        _require_utc(self.created_at, "created_at")


@dataclass(frozen=True)
class FederatedIdentity:
    """Immutable binding from one approved issuer/subject pair to an actor."""

    actor_id: str
    issuer: str
    subject: str

    def __post_init__(self) -> None:
        _require_actor_id(self.actor_id)
        _require_text(self.issuer, "issuer", maximum=512)
        _require_text(self.subject, "subject", maximum=512)


@dataclass(frozen=True)
class Cohort:
    """A course boundary governed by one institution-managed account authority."""

    cohort_id: str
    account_authority: str
    created_at: datetime
    closes_at: datetime

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        _require_text(self.account_authority, "account_authority", maximum=256)
        _require_utc(self.created_at, "created_at")
        _require_utc(self.closes_at, "closes_at")
        if self.closes_at <= self.created_at:
            raise ValueError("closes_at must be after created_at")


@dataclass(frozen=True)
class CohortMembership:
    """One current, explicitly assigned role for an actor in one cohort."""

    cohort_id: str
    actor_id: str
    role: CohortRole
    granted_by_actor_id: str
    granted_at: datetime
    active: bool = True
    revision: int = 1

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        _require_actor_id(self.actor_id)
        _require_actor_id(self.granted_by_actor_id, "granted_by_actor_id")
        if not isinstance(self.role, CohortRole):
            raise ValueError("role must be a CohortRole")
        _require_utc(self.granted_at, "granted_at")
        if not isinstance(self.active, bool):
            raise ValueError("active must be a bool")
        if (
            not isinstance(self.revision, int)
            or isinstance(self.revision, bool)
            or self.revision < 1
        ):
            raise ValueError("revision must be a positive integer")


@dataclass(frozen=True)
class PackageNamespace:
    """Global package identity with one cohort and one explicit human owner."""

    package_id: str
    cohort_id: str
    owner_actor_id: str
    created_at: datetime
    revision: int = 1

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.package_id):
            raise ValueError("package_id must be a valid lower-kebab-case identifier")
        if not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        _require_actor_id(self.owner_actor_id, "owner_actor_id")
        _require_utc(self.created_at, "created_at")
        if (
            not isinstance(self.revision, int)
            or isinstance(self.revision, bool)
            or self.revision < 1
        ):
            raise ValueError("revision must be a positive integer")


@dataclass(frozen=True)
class NamespaceGrant:
    """An explicit actor grant for one global package namespace."""

    package_id: str
    cohort_id: str
    actor_id: str
    permission: NamespacePermission
    granted_by_actor_id: str
    granted_at: datetime

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.package_id):
            raise ValueError("package_id must be a valid lower-kebab-case identifier")
        if not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        _require_actor_id(self.actor_id)
        _require_actor_id(self.granted_by_actor_id, "granted_by_actor_id")
        if not isinstance(self.permission, NamespacePermission):
            raise ValueError("permission must be a NamespacePermission")
        _require_utc(self.granted_at, "granted_at")


@dataclass(frozen=True)
class PackageVersionIdentity:
    """Immutable identity of exact deterministic Explorer Package ZIP bytes."""

    package_id: str
    package_version: str
    raw_zip_sha256: str

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.package_id):
            raise ValueError("package_id must be a valid lower-kebab-case identifier")
        if not is_valid_semantic_version(self.package_version):
            raise ValueError("package_version must be Semantic Versioning 2.0.0")
        _require_sha256(self.raw_zip_sha256, "raw_zip_sha256")


@dataclass(frozen=True)
class StoredPackageVersion:
    """Persisted immutable package identity with its original actor and cohort."""

    identity: PackageVersionIdentity
    cohort_id: str
    created_by_actor_id: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.identity, PackageVersionIdentity):
            raise ValueError("identity must be a PackageVersionIdentity")
        if not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        _require_actor_id(self.created_by_actor_id, "created_by_actor_id")
        _require_utc(self.created_at, "created_at")


@dataclass(frozen=True)
class HumanPrincipal:
    """Trusted server-side snapshot of one authenticated human principal."""

    actor_id: str
    assurance: AssuranceLevel
    memberships: tuple[CohortMembership, ...] = ()
    namespace_grants: tuple[NamespaceGrant, ...] = ()

    def __post_init__(self) -> None:
        _require_actor_id(self.actor_id)
        if not isinstance(self.assurance, AssuranceLevel):
            raise ValueError("assurance must be an AssuranceLevel")
        if any(membership.actor_id != self.actor_id for membership in self.memberships):
            raise ValueError("every membership must belong to the principal actor")
        cohort_ids = [membership.cohort_id for membership in self.memberships]
        if len(set(cohort_ids)) != len(cohort_ids):
            raise ValueError("a principal may have only one membership per cohort")
        if any(grant.actor_id != self.actor_id for grant in self.namespace_grants):
            raise ValueError("every namespace grant must belong to the principal actor")


@dataclass(frozen=True)
class ServicePrincipal:
    """Workload identity restricted to explicit exact-version registry reads."""

    service_principal_id: str
    exact_registry_read_grants: tuple[PackageVersionIdentity, ...] = ()

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.service_principal_id):
            raise ValueError("service_principal_id must be a valid lower-kebab-case identifier")


@dataclass(frozen=True)
class AuditEvent:
    """Append-only security/provenance event with a canonical JSON detail object."""

    event_id: str
    occurred_at: datetime
    retention_until: datetime
    principal_kind: PrincipalKind
    principal_id: str
    event_type: str
    object_type: str
    object_id: str
    idempotency_key: str
    details_json: str
    cohort_id: str | None = None
    initiating_actor_id: str | None = None

    def __post_init__(self) -> None:
        _require_actor_id(self.event_id, "event_id")
        _require_utc(self.occurred_at, "occurred_at")
        _require_utc(self.retention_until, "retention_until")
        if self.retention_until <= self.occurred_at:
            raise ValueError("retention_until must be after occurred_at")
        if not isinstance(self.principal_kind, PrincipalKind):
            raise ValueError("principal_kind must be a PrincipalKind")
        if self.principal_kind is PrincipalKind.ACTOR:
            _require_actor_id(self.principal_id, "principal_id")
        else:
            if not is_valid_identifier(self.principal_id):
                raise ValueError("service principal_id must be a valid lower-kebab-case identifier")
        _require_text(self.event_type, "event_type", maximum=128)
        _require_text(self.object_type, "object_type", maximum=128)
        _require_text(self.object_id, "object_id", maximum=512)
        _require_text(self.idempotency_key, "idempotency_key", maximum=128)
        if self.cohort_id is not None and not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        if self.initiating_actor_id is not None:
            _require_actor_id(self.initiating_actor_id, "initiating_actor_id")
        try:
            details = json.loads(self.details_json)
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("details_json must be valid JSON") from error
        if not isinstance(details, dict):
            raise ValueError("details_json must contain a JSON object")
        sensitive_keys = _collect_sensitive_audit_keys(details)
        if sensitive_keys:
            rendered = ", ".join(sorted(sensitive_keys))
            raise ValueError(f"details_json must not contain mutable profile data: {rendered}")
        canonical = json.dumps(details, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        if canonical != self.details_json:
            raise ValueError("details_json must use canonical sorted compact JSON")


@dataclass(frozen=True)
class IdempotencyRecord:
    """Immutable completed-operation record used to make retries safe."""

    principal_kind: PrincipalKind
    principal_id: str
    operation: str
    idempotency_key: str
    request_sha256: str
    result_reference: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.principal_kind, PrincipalKind):
            raise ValueError("principal_kind must be a PrincipalKind")
        if self.principal_kind is PrincipalKind.ACTOR:
            _require_actor_id(self.principal_id, "principal_id")
        elif not is_valid_identifier(self.principal_id):
            raise ValueError("service principal_id must be a valid lower-kebab-case identifier")
        _require_text(self.operation, "operation", maximum=128)
        _require_text(self.idempotency_key, "idempotency_key", maximum=128)
        _require_sha256(self.request_sha256, "request_sha256")
        _require_text(self.result_reference, "result_reference", maximum=512)
        _require_utc(self.created_at, "created_at")


def _collect_sensitive_audit_keys(value: object) -> frozenset[str]:
    if isinstance(value, dict):
        found = {key for key in value if key.casefold() in _SENSITIVE_AUDIT_KEYS}
        for nested in value.values():
            found.update(_collect_sensitive_audit_keys(nested))
        return frozenset(found)
    if isinstance(value, list):
        found: set[str] = set()
        for nested in value:
            found.update(_collect_sensitive_audit_keys(nested))
        return frozenset(found)
    return frozenset()
