"""Immutable models for Phase E review, approval, rejection, and revocation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from explore.online.models import AssuranceLevel, CohortRole, PackageVersionIdentity
from explore.packages.policy import is_valid_identifier

REVIEW_REASON_MAX_LENGTH = 2000
REVIEW_RESULT_METADATA_MAX_BYTES = 8192

_CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", re.ASCII)


def _require_text(value: str, field: str, *, maximum: int) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{field} must contain 1 to {maximum} characters")
    if _CONTROL_CHARACTER_PATTERN.search(value) is not None:
        raise ValueError(f"{field} must not contain disallowed control characters")


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


def _require_canonical_metadata(value: str) -> None:
    if not isinstance(value, str) or len(value.encode("utf-8")) > REVIEW_RESULT_METADATA_MAX_BYTES:
        raise ValueError("result_metadata_json exceeds its bounded UTF-8 size")
    try:
        document = json.loads(value)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError("result_metadata_json must be valid JSON") from error
    canonical = json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if not isinstance(document, dict) or canonical != value:
        raise ValueError("result_metadata_json must be a canonical JSON object")


class ReviewState(StrEnum):
    """State derived from an immutable submission and its append-only decisions."""

    REVIEWABLE = "reviewable"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"


class ReviewAction(StrEnum):
    """Supported decision actions."""

    APPROVE = "approve"
    REJECT = "reject"
    REVOKE = "revoke"


_ALLOWED_TRANSITIONS = {
    (ReviewState.REVIEWABLE, ReviewAction.APPROVE): ReviewState.APPROVED,
    (ReviewState.REVIEWABLE, ReviewAction.REJECT): ReviewState.REJECTED,
    (ReviewState.APPROVED, ReviewAction.REVOKE): ReviewState.REVOKED,
}


def review_transition(
    current_state: ReviewState,
    action: ReviewAction,
) -> ReviewState | None:
    """Return the sole allowed target for a state/action pair, otherwise fail closed."""
    if not isinstance(current_state, ReviewState) or not isinstance(action, ReviewAction):
        return None
    return _ALLOWED_TRANSITIONS.get((current_state, action))


@dataclass(frozen=True)
class ReviewDecisionRequest:
    """Bounded reviewer intent containing no trusted state or authority claims."""

    action: ReviewAction
    reason: str
    result_metadata_json: str
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.action, ReviewAction):
            raise ValueError("action must be a ReviewAction")
        _require_text(self.reason, "reason", maximum=REVIEW_REASON_MAX_LENGTH)
        _require_canonical_metadata(self.result_metadata_json)
        _require_text(self.correlation_id, "correlation_id", maximum=128)
        _require_text(self.idempotency_key, "idempotency_key", maximum=128)


@dataclass(frozen=True)
class ReviewerMembershipSnapshot:
    """Authoritative role and membership evidence captured at decision time."""

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
        _require_uuid(self.granted_by_actor_id, "granted_by_actor_id")
        if self.role not in (CohortRole.TEACHER, CohortRole.COURSE_ADMIN):
            raise ValueError("reviewer role must be teacher or course-admin")
        if self.assurance is not AssuranceLevel.AAL2:
            raise ValueError("reviewer assurance must be AAL2/MFA")
        _require_utc(self.granted_at, "granted_at")
        if (
            not isinstance(self.revision, int)
            or isinstance(self.revision, bool)
            or self.revision < 1
        ):
            raise ValueError("revision must be a positive integer")
        if self.active is not True:
            raise ValueError("reviewer membership snapshot must be active")


@dataclass(frozen=True)
class PackageReviewDecision:
    """One immutable append-only transition attached to an exact package version."""

    decision_id: str
    submission_id: str
    sequence: int
    action: ReviewAction
    from_state: ReviewState
    to_state: ReviewState
    package_version: PackageVersionIdentity
    membership: ReviewerMembershipSnapshot
    reason: str
    result_metadata_json: str
    decided_at: datetime
    correlation_id: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _require_uuid(self.decision_id, "decision_id", version=4)
        _require_uuid(self.submission_id, "submission_id", version=4)
        if (
            not isinstance(self.sequence, int)
            or isinstance(self.sequence, bool)
            or self.sequence < 1
        ):
            raise ValueError("sequence must be a positive integer")
        if not isinstance(self.action, ReviewAction):
            raise ValueError("action must be a ReviewAction")
        if not isinstance(self.from_state, ReviewState) or not isinstance(
            self.to_state, ReviewState
        ):
            raise ValueError("from_state and to_state must be ReviewState values")
        if review_transition(self.from_state, self.action) is not self.to_state:
            raise ValueError("decision does not represent an allowed state transition")
        if not isinstance(self.package_version, PackageVersionIdentity):
            raise ValueError("package_version must be a PackageVersionIdentity")
        if not isinstance(self.membership, ReviewerMembershipSnapshot):
            raise ValueError("membership must be a ReviewerMembershipSnapshot")
        _require_text(self.reason, "reason", maximum=REVIEW_REASON_MAX_LENGTH)
        _require_canonical_metadata(self.result_metadata_json)
        _require_utc(self.decided_at, "decided_at")
        _require_text(self.correlation_id, "correlation_id", maximum=128)
        _require_text(self.idempotency_key, "idempotency_key", maximum=128)


@dataclass(frozen=True)
class ReviewDecisionReceipt:
    """Decision result plus current state at the time it was returned."""

    decision: PackageReviewDecision
    current_state: ReviewState
    replayed: bool


class ReviewAuthenticationError(PermissionError):
    """The verified external identity has no immutable actor binding."""


class ReviewAccessDeniedError(PermissionError):
    """Review access is denied without revealing submission existence."""


class ReviewConflictError(RuntimeError):
    """An idempotency request or concurrent decision conflicts with persisted state."""


class ReviewTransitionConflictError(ReviewConflictError):
    """The requested transition is not valid from the current persisted state."""


__all__ = [
    "REVIEW_REASON_MAX_LENGTH",
    "REVIEW_RESULT_METADATA_MAX_BYTES",
    "PackageReviewDecision",
    "ReviewAccessDeniedError",
    "ReviewAction",
    "ReviewAuthenticationError",
    "ReviewConflictError",
    "ReviewDecisionReceipt",
    "ReviewDecisionRequest",
    "ReviewerMembershipSnapshot",
    "ReviewState",
    "ReviewTransitionConflictError",
    "review_transition",
]
