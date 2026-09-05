"""Trusted application service for append-only package review decisions."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from explore.online.authorization import AuthorizationAction, AuthorizationResource, authorize
from explore.online.models import AuditEvent, CohortMembership, IdempotencyRecord, PrincipalKind
from explore.online.persistence import PersistenceConflictError
from explore.online.review_models import (
    PackageReviewDecision,
    ReviewAccessDeniedError,
    ReviewAction,
    ReviewAuthenticationError,
    ReviewConflictError,
    ReviewDecisionReceipt,
    ReviewDecisionRequest,
    ReviewerMembershipSnapshot,
    ReviewState,
    ReviewTransitionConflictError,
    review_transition,
)
from explore.online.review_persistence import SQLiteReviewStore
from explore.online.submission_models import AuthenticatedOIDCIdentity, PackageSubmission

_REVIEW_OPERATION = "package.review-decision"
_AUDIT_EVENT_TYPE = "package.review-decision"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _add_calendar_years(value: datetime, years: int) -> datetime:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def _request_sha256(submission_id: str, request: ReviewDecisionRequest) -> str:
    document = {
        "action": request.action.value,
        "correlation_id": request.correlation_id,
        "reason": request.reason,
        "result_metadata_json": request.result_metadata_json,
        "submission_id": submission_id,
    }
    canonical = json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _authorization_action(action: ReviewAction) -> AuthorizationAction:
    if action in (ReviewAction.APPROVE, ReviewAction.REJECT):
        return AuthorizationAction.APPROVE
    return AuthorizationAction.REVOKE


class PackageReviewService:
    """Authorize and atomically append review state transitions.

    State is derived from the immutable submission plus this service's decision
    log. No submission field or artifact byte is updated by a decision.
    """

    def __init__(
        self,
        store: SQLiteReviewStore,
        *,
        clock: Callable[[], datetime] = _utc_now,
        uuid_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        if not isinstance(store, SQLiteReviewStore):
            raise TypeError("store must be a SQLiteReviewStore")
        if not callable(clock) or not callable(uuid_factory):
            raise TypeError("clock and uuid_factory must be callable")
        self._store = store
        self._clock = clock
        self._uuid_factory = uuid_factory

    def _actor_id(self, identity: AuthenticatedOIDCIdentity) -> str:
        if not isinstance(identity, AuthenticatedOIDCIdentity):
            raise TypeError("identity must be an AuthenticatedOIDCIdentity")
        actor = self._store.resolve_federated_actor(identity.issuer, identity.subject)
        if actor is None:
            raise ReviewAuthenticationError("authenticated identity is not bound")
        return actor.actor_id

    def _load_authorized(
        self,
        *,
        actor_id: str,
        identity: AuthenticatedOIDCIdentity,
        submission_id: str,
        action: ReviewAction,
    ) -> tuple[PackageSubmission, ReviewState, CohortMembership]:
        submission = self._store.load_submission(submission_id)
        if submission is None:
            raise ReviewAccessDeniedError("review decision is not authorized")
        namespace = self._store.load_namespace(submission.package_version.package_id)
        if namespace is None or namespace.cohort_id != submission.cohort_id:
            raise ReviewAccessDeniedError("review decision is not authorized")
        current_state = self._store.load_review_state(submission_id)
        principal = self._store.load_human_principal(actor_id, identity.assurance)
        policy = authorize(
            principal,
            _authorization_action(action),
            AuthorizationResource(
                cohort_id=submission.cohort_id,
                package_id=submission.package_version.package_id,
                package_version=submission.package_version,
                owner_actor_id=namespace.owner_actor_id,
                submitted_by_actor_id=submission.submitted_by_actor_id,
                approved=current_state in (ReviewState.APPROVED, ReviewState.REVOKED),
                revoked=current_state is ReviewState.REVOKED,
            ),
        )
        if not policy.allowed:
            raise ReviewAccessDeniedError("review decision is not authorized")
        membership = next(
            (
                item
                for item in principal.memberships
                if item.cohort_id == submission.cohort_id and item.active
            ),
            None,
        )
        if membership is None:
            raise ReviewAccessDeniedError("review decision is not authorized")
        return submission, current_state, membership

    def _load_replay(
        self,
        *,
        actor_id: str,
        identity: AuthenticatedOIDCIdentity,
        result_reference: str,
        request: ReviewDecisionRequest,
    ) -> ReviewDecisionReceipt:
        decision = self._store.load_review_decision(result_reference)
        if decision is None or decision.membership.actor_id != actor_id:
            raise RuntimeError("idempotency record references a missing review decision")
        _, current_state, _ = self._load_authorized(
            actor_id=actor_id,
            identity=identity,
            submission_id=decision.submission_id,
            action=request.action,
        )
        return ReviewDecisionReceipt(decision, current_state, replayed=True)

    def decide(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        submission_id: str,
        request: ReviewDecisionRequest,
    ) -> ReviewDecisionReceipt:
        """Append one authorized reviewable/approved state transition."""
        if not isinstance(request, ReviewDecisionRequest):
            raise TypeError("request must be a ReviewDecisionRequest")
        if not isinstance(submission_id, str):
            raise ReviewAccessDeniedError("review decision is not authorized")
        actor_id = self._actor_id(identity)
        request_sha256 = _request_sha256(submission_id, request)
        now = self._clock()
        if (
            not isinstance(now, datetime)
            or now.tzinfo is None
            or now.utcoffset() != UTC.utcoffset(now)
        ):
            raise RuntimeError("trusted clock must return a timezone-aware UTC datetime")

        try:
            with self._store.transaction():
                locked_actor_id = self._actor_id(identity)
                if locked_actor_id != actor_id:
                    raise ReviewAuthenticationError("authenticated identity changed")
                prior = self._store.load_idempotency_record(
                    principal_kind=PrincipalKind.ACTOR,
                    principal_id=actor_id,
                    operation=_REVIEW_OPERATION,
                    idempotency_key=request.idempotency_key,
                )
                if prior is not None:
                    if prior.request_sha256 != request_sha256:
                        raise ReviewConflictError(
                            "idempotency key conflicts with prior review request"
                        )
                    return self._load_replay(
                        actor_id=actor_id,
                        identity=identity,
                        result_reference=prior.result_reference,
                        request=request,
                    )

                submission, current_state, membership = self._load_authorized(
                    actor_id=actor_id,
                    identity=identity,
                    submission_id=submission_id,
                    action=request.action,
                )
                target_state = review_transition(current_state, request.action)
                if target_state is None:
                    raise ReviewTransitionConflictError(
                        "requested decision conflicts with current review state"
                    )
                snapshot = ReviewerMembershipSnapshot(
                    cohort_id=membership.cohort_id,
                    actor_id=membership.actor_id,
                    role=membership.role,
                    assurance=identity.assurance,
                    granted_by_actor_id=membership.granted_by_actor_id,
                    granted_at=membership.granted_at,
                    revision=membership.revision,
                    active=membership.active,
                )
                decision = PackageReviewDecision(
                    decision_id=str(self._uuid_factory()),
                    submission_id=submission.submission_id,
                    sequence=self._store.next_review_sequence(submission.submission_id),
                    action=request.action,
                    from_state=current_state,
                    to_state=target_state,
                    package_version=submission.package_version,
                    membership=snapshot,
                    reason=request.reason,
                    result_metadata_json=request.result_metadata_json,
                    decided_at=now,
                    correlation_id=request.correlation_id,
                    idempotency_key=request.idempotency_key,
                )
                self._store.append_review_decision(decision)

                closes_at = self._store.load_cohort_closes_at(submission.cohort_id)
                if closes_at is None:
                    raise ReviewAccessDeniedError("review decision is not authorized")
                retention_basis = max(closes_at, now)
                audit_details = json.dumps(
                    {
                        "action": decision.action.value,
                        "correlation_id": decision.correlation_id,
                        "decision_id": decision.decision_id,
                        "from_state": decision.from_state.value,
                        "membership_revision": snapshot.revision,
                        "package_id": decision.package_version.package_id,
                        "raw_zip_sha256": decision.package_version.raw_zip_sha256,
                        "reason_sha256": hashlib.sha256(
                            decision.reason.encode("utf-8")
                        ).hexdigest(),
                        "result_metadata_sha256": hashlib.sha256(
                            decision.result_metadata_json.encode("utf-8")
                        ).hexdigest(),
                        "reviewer_role": snapshot.role.value,
                        "semantic_version": decision.package_version.package_version,
                        "to_state": decision.to_state.value,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                self._store.append_audit_event(
                    AuditEvent(
                        event_id=str(self._uuid_factory()),
                        occurred_at=now,
                        retention_until=_add_calendar_years(retention_basis, 2),
                        principal_kind=PrincipalKind.ACTOR,
                        principal_id=actor_id,
                        event_type=_AUDIT_EVENT_TYPE,
                        object_type="package-review-decision",
                        object_id=decision.decision_id,
                        cohort_id=submission.cohort_id,
                        idempotency_key=request.idempotency_key,
                        details_json=audit_details,
                    )
                )
                self._store.record_idempotent_result(
                    IdempotencyRecord(
                        principal_kind=PrincipalKind.ACTOR,
                        principal_id=actor_id,
                        operation=_REVIEW_OPERATION,
                        idempotency_key=request.idempotency_key,
                        request_sha256=request_sha256,
                        result_reference=decision.decision_id,
                        created_at=now,
                    )
                )
        except PersistenceConflictError as error:
            raise ReviewConflictError(str(error)) from error

        return ReviewDecisionReceipt(decision, decision.to_state, replayed=False)


__all__ = ["PackageReviewService"]
