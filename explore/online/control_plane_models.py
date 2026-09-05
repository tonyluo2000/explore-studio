"""Immutable models for authenticated Phase E control-plane transitions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from explore.online.models import AssuranceLevel, CohortRole, NamespacePermission
from explore.packages.policy import is_valid_identifier

_CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x1f\x7f]", re.ASCII)
_MAX_CHANGE_BYTES = 8192


def _require_text(value: str, field: str, *, maximum: int) -> None:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{field} must contain 1 to {maximum} characters")
    if _CONTROL_CHARACTER_PATTERN.search(value) is not None:
        raise ValueError(f"{field} must not contain control characters")


def _require_identifier(value: str, field: str) -> None:
    if not is_valid_identifier(value):
        raise ValueError(f"{field} must be a valid lower-kebab-case identifier")


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


def _require_revision(value: int, field: str, *, allow_zero: bool = False) -> None:
    minimum = 0 if allow_zero else 1
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{field} must be a {qualifier} integer")


def _require_common(correlation_id: str, idempotency_key: str) -> None:
    _require_text(correlation_id, "correlation_id", maximum=128)
    _require_text(idempotency_key, "idempotency_key", maximum=128)


def _require_canonical_change(value: str) -> None:
    if not isinstance(value, str) or len(value.encode("utf-8")) > _MAX_CHANGE_BYTES:
        raise ValueError("change_json exceeds its bounded UTF-8 size")
    try:
        document = json.loads(value)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError("change_json must be valid JSON") from error
    canonical = json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if not isinstance(document, dict) or canonical != value:
        raise ValueError("change_json must be a canonical JSON object")


class ControlPlaneAction(StrEnum):
    """The complete bounded set of Phase E administrative transitions."""

    MEMBERSHIP_CREATE = "membership-create"
    MEMBERSHIP_CHANGE = "membership-change"
    MEMBERSHIP_REVOKE = "membership-revoke"
    NAMESPACE_CLAIM = "namespace-claim"
    NAMESPACE_GRANT = "namespace-grant"
    NAMESPACE_GRANT_REVOKE = "namespace-grant-revoke"
    NAMESPACE_TRANSFER = "namespace-transfer"


@dataclass(frozen=True)
class MembershipCreateRequest:
    """Intent to create one same-cohort membership at revision one."""

    cohort_id: str
    target_actor_id: str
    role: CohortRole
    expected_revision: int
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _require_identifier(self.cohort_id, "cohort_id")
        _require_uuid(self.target_actor_id, "target_actor_id")
        if not isinstance(self.role, CohortRole):
            raise ValueError("role must be a CohortRole")
        _require_revision(self.expected_revision, "expected_revision", allow_zero=True)
        if self.expected_revision != 0:
            raise ValueError("membership creation requires expected_revision 0")
        _require_common(self.correlation_id, self.idempotency_key)


@dataclass(frozen=True)
class MembershipChangeRequest:
    """Intent to replace the role of one current active membership."""

    cohort_id: str
    target_actor_id: str
    role: CohortRole
    expected_revision: int
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _require_identifier(self.cohort_id, "cohort_id")
        _require_uuid(self.target_actor_id, "target_actor_id")
        if not isinstance(self.role, CohortRole):
            raise ValueError("role must be a CohortRole")
        _require_revision(self.expected_revision, "expected_revision")
        _require_common(self.correlation_id, self.idempotency_key)


@dataclass(frozen=True)
class MembershipRevokeRequest:
    """Intent to deactivate one current membership without deleting identity."""

    cohort_id: str
    target_actor_id: str
    expected_revision: int
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _require_identifier(self.cohort_id, "cohort_id")
        _require_uuid(self.target_actor_id, "target_actor_id")
        _require_revision(self.expected_revision, "expected_revision")
        _require_common(self.correlation_id, self.idempotency_key)


@dataclass(frozen=True)
class NamespaceClaimRequest:
    """Intent to claim one globally absent package ID for a cohort member."""

    cohort_id: str
    package_id: str
    owner_actor_id: str
    expected_revision: int
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _require_identifier(self.cohort_id, "cohort_id")
        _require_identifier(self.package_id, "package_id")
        _require_uuid(self.owner_actor_id, "owner_actor_id")
        _require_revision(self.expected_revision, "expected_revision", allow_zero=True)
        if self.expected_revision != 0:
            raise ValueError("namespace claim requires expected_revision 0")
        _require_common(self.correlation_id, self.idempotency_key)


@dataclass(frozen=True)
class NamespaceGrantRequest:
    """Intent to create or reactivate an explicit submit grant."""

    package_id: str
    target_actor_id: str
    expected_namespace_revision: int
    expected_grant_revision: int
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _require_identifier(self.package_id, "package_id")
        _require_uuid(self.target_actor_id, "target_actor_id")
        _require_revision(self.expected_namespace_revision, "expected_namespace_revision")
        _require_revision(
            self.expected_grant_revision,
            "expected_grant_revision",
            allow_zero=True,
        )
        _require_common(self.correlation_id, self.idempotency_key)


@dataclass(frozen=True)
class NamespaceGrantRevokeRequest:
    """Intent to deactivate one explicit submit grant."""

    package_id: str
    target_actor_id: str
    expected_namespace_revision: int
    expected_grant_revision: int
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _require_identifier(self.package_id, "package_id")
        _require_uuid(self.target_actor_id, "target_actor_id")
        _require_revision(self.expected_namespace_revision, "expected_namespace_revision")
        _require_revision(self.expected_grant_revision, "expected_grant_revision")
        _require_common(self.correlation_id, self.idempotency_key)


@dataclass(frozen=True)
class NamespaceTransferRequest:
    """Intent to transfer only current ownership of one global package ID."""

    package_id: str
    new_owner_actor_id: str
    expected_revision: int
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _require_identifier(self.package_id, "package_id")
        _require_uuid(self.new_owner_actor_id, "new_owner_actor_id")
        _require_revision(self.expected_revision, "expected_revision")
        _require_common(self.correlation_id, self.idempotency_key)


@dataclass(frozen=True)
class ControlPlaneAuthoritySnapshot:
    """Current course-admin authority captured at transition time."""

    cohort_id: str
    actor_id: str
    role: CohortRole
    assurance: AssuranceLevel
    granted_by_actor_id: str
    granted_at: datetime
    revision: int
    active: bool

    def __post_init__(self) -> None:
        _require_identifier(self.cohort_id, "cohort_id")
        _require_uuid(self.actor_id, "actor_id")
        if self.role is not CohortRole.COURSE_ADMIN:
            raise ValueError("control-plane authority must be course-admin")
        if self.assurance is not AssuranceLevel.AAL2:
            raise ValueError("control-plane authority must be AAL2/MFA")
        _require_uuid(self.granted_by_actor_id, "granted_by_actor_id")
        _require_utc(self.granted_at, "granted_at")
        _require_revision(self.revision, "revision")
        if self.active is not True:
            raise ValueError("control-plane authority snapshot must be active")


@dataclass(frozen=True)
class NamespaceGrantState:
    """Optimistic current state for an explicit namespace permission."""

    package_id: str
    cohort_id: str
    actor_id: str
    permission: NamespacePermission
    active: bool
    revision: int

    def __post_init__(self) -> None:
        _require_identifier(self.package_id, "package_id")
        _require_identifier(self.cohort_id, "cohort_id")
        _require_uuid(self.actor_id, "actor_id")
        if self.permission is not NamespacePermission.SUBMIT:
            raise ValueError("only the submit namespace permission is supported")
        if not isinstance(self.active, bool):
            raise ValueError("active must be a bool")
        _require_revision(self.revision, "revision")


@dataclass(frozen=True)
class ControlPlaneTransition:
    """One immutable successful administrative state transition."""

    transition_id: str
    action: ControlPlaneAction
    object_type: str
    object_id: str
    cohort_id: str
    authority: ControlPlaneAuthoritySnapshot
    occurred_at: datetime
    correlation_id: str
    idempotency_key: str
    change_json: str

    def __post_init__(self) -> None:
        _require_uuid(self.transition_id, "transition_id", version=4)
        if not isinstance(self.action, ControlPlaneAction):
            raise ValueError("action must be a ControlPlaneAction")
        _require_text(self.object_type, "object_type", maximum=64)
        _require_text(self.object_id, "object_id", maximum=512)
        _require_identifier(self.cohort_id, "cohort_id")
        if not isinstance(self.authority, ControlPlaneAuthoritySnapshot):
            raise ValueError("authority must be a ControlPlaneAuthoritySnapshot")
        if self.authority.cohort_id != self.cohort_id:
            raise ValueError("authority cohort must match transition cohort")
        _require_utc(self.occurred_at, "occurred_at")
        _require_common(self.correlation_id, self.idempotency_key)
        _require_canonical_change(self.change_json)


@dataclass(frozen=True)
class ControlPlaneReceipt:
    """Result of one successful or safely replayed control-plane transition."""

    transition: ControlPlaneTransition
    replayed: bool


class ControlPlaneAuthenticationError(PermissionError):
    """The verified external identity has no immutable actor binding."""


class ControlPlaneAccessDeniedError(PermissionError):
    """Control-plane access is denied without revealing target existence."""


class ControlPlaneConflictError(RuntimeError):
    """A revision, immutable identity, or idempotency request conflicts."""


__all__ = [
    "ControlPlaneAccessDeniedError",
    "ControlPlaneAction",
    "ControlPlaneAuthenticationError",
    "ControlPlaneAuthoritySnapshot",
    "ControlPlaneConflictError",
    "ControlPlaneReceipt",
    "ControlPlaneTransition",
    "MembershipChangeRequest",
    "MembershipCreateRequest",
    "MembershipRevokeRequest",
    "NamespaceClaimRequest",
    "NamespaceGrantRequest",
    "NamespaceGrantRevokeRequest",
    "NamespaceGrantState",
    "NamespaceTransferRequest",
]
