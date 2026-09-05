"""Security, state-machine, replay, and concurrency tests for Phase E review."""

from __future__ import annotations

import inspect
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier

import pytest

from explore.online import (
    Actor,
    AssuranceLevel,
    AuditEvent,
    AuthenticatedOIDCIdentity,
    Cohort,
    CohortMembership,
    CohortRole,
    IdentityProvider,
    NamespaceGrant,
    NamespacePermission,
    PackageNamespace,
    PackageReviewService,
    PackageSubmissionService,
    PrincipalKind,
    PublicationAcknowledgment,
    PublicationAuthority,
    PublicationPolicy,
    ReviewAccessDeniedError,
    ReviewAction,
    ReviewAuthenticationError,
    ReviewConflictError,
    ReviewDecisionRequest,
    ReviewPersistenceConflictError,
    ReviewState,
    ReviewTransitionConflictError,
    SQLiteReviewStore,
    SubmissionState,
    review_transition,
)
from explore.packages import export_explorer_package

NOW = datetime(2026, 9, 5, 16, 0, tzinfo=UTC)
CREATED = datetime(2026, 9, 1, 14, 0, tzinfo=UTC)
CLOSES = datetime(2027, 6, 30, 23, 59, tzinfo=UTC)
ISSUER = "https://identity.example.edu"
COHORT_ID = "fall-explorers"
OTHER_COHORT_ID = "winter-explorers"
PACKAGE_ID = "nova-character"
ACTOR_IDS = {
    "student": "00000000-0000-4000-8000-000000000001",
    "teacher": "00000000-0000-4000-8000-000000000002",
    "course-admin": "00000000-0000-4000-8000-000000000003",
    "second-teacher": "00000000-0000-4000-8000-000000000005",
    "other-teacher": "00000000-0000-4000-8000-000000000006",
}
SUBJECTS = {name: f"provider-{name}" for name in ACTOR_IDS}
PUBLICATION_POLICY = PublicationPolicy("terms-2026-09", "license-policy-2026-09")
ACKNOWLEDGMENT = PublicationAcknowledgment(
    PUBLICATION_POLICY.terms_version,
    PUBLICATION_POLICY.license_policy_version,
    PublicationAuthority.SELF,
)
PROJECT_ROOT = Path(__file__).parents[1]
EXAMPLE_ROOT = PROJECT_ROOT / "examples" / "explorer-packages" / PACKAGE_ID


def _identity(
    name: str,
    *,
    assurance: AssuranceLevel | None = None,
) -> AuthenticatedOIDCIdentity:
    expected = AssuranceLevel.AAL1 if name == "student" else AssuranceLevel.AAL2
    return AuthenticatedOIDCIdentity(ISSUER, SUBJECTS[name], assurance or expected)


def _membership(
    name: str,
    role: CohortRole,
    *,
    cohort_id: str = COHORT_ID,
) -> CohortMembership:
    return CohortMembership(
        cohort_id=cohort_id,
        actor_id=ACTOR_IDS[name],
        role=role,
        granted_by_actor_id=ACTOR_IDS["course-admin"],
        granted_at=CREATED,
    )


def _open_seeded_store(path: Path) -> SQLiteReviewStore:
    store = SQLiteReviewStore.open(path)
    store.initialize_schema()
    store.approve_identity_provider(IdentityProvider(ISSUER))
    for name, actor_id in ACTOR_IDS.items():
        store.bind_federated_actor(
            issuer=ISSUER,
            subject=SUBJECTS[name],
            proposed_actor=Actor(actor_id, CREATED),
        )
    admin = _membership("course-admin", CohortRole.COURSE_ADMIN)
    store.create_cohort(Cohort(COHORT_ID, "Example Academy", CREATED, CLOSES), admin)
    store.grant_membership(_membership("student", CohortRole.STUDENT))
    store.grant_membership(_membership("teacher", CohortRole.TEACHER))
    store.grant_membership(_membership("second-teacher", CohortRole.TEACHER))

    other_admin = _membership(
        "course-admin",
        CohortRole.COURSE_ADMIN,
        cohort_id=OTHER_COHORT_ID,
    )
    store.create_cohort(
        Cohort(OTHER_COHORT_ID, "Example Academy", CREATED, CLOSES),
        other_admin,
    )
    store.grant_membership(
        _membership("other-teacher", CohortRole.TEACHER, cohort_id=OTHER_COHORT_ID)
    )
    store.create_namespace(PackageNamespace(PACKAGE_ID, COHORT_ID, ACTOR_IDS["student"], CREATED))
    return store


@pytest.fixture
def archive(tmp_path: Path) -> bytes:
    destination = tmp_path / "nova-character-1.0.0.explorer-package.zip"
    result = export_explorer_package(EXAMPLE_ROOT.resolve(), destination.resolve())
    assert result.is_exported
    return destination.read_bytes()


@pytest.fixture
def store(tmp_path: Path) -> SQLiteReviewStore:
    value = _open_seeded_store(tmp_path / "review.sqlite3")
    yield value
    value.close()


def _publish(
    store: SQLiteReviewStore,
    archive: bytes,
    *,
    actor: str = "student",
    key: str = "publish-nova-v1",
):
    return PackageSubmissionService(
        store,
        PUBLICATION_POLICY,
        clock=lambda: NOW,
    ).submit(
        identity=_identity(actor),
        filename="nova-character-1.0.0.explorer-package.zip",
        archive_bytes=archive,
        idempotency_key=key,
        acknowledgment=ACKNOWLEDGMENT,
    )


def _request(
    action: ReviewAction,
    *,
    key: str | None = None,
    reason: str = "Reviewed against the course package policy.",
    correlation_id: str = "course-review-2026-001",
) -> ReviewDecisionRequest:
    return ReviewDecisionRequest(
        action=action,
        reason=reason,
        result_metadata_json='{"rubric_version":"review-v1"}',
        correlation_id=correlation_id,
        idempotency_key=key or f"{action.value}-nova-v1",
    )


def _decide(
    store: SQLiteReviewStore,
    submission_id: str,
    action: ReviewAction,
    *,
    actor: str = "teacher",
    request: ReviewDecisionRequest | None = None,
):
    return PackageReviewService(store, clock=lambda: NOW).decide(
        identity=_identity(actor),
        submission_id=submission_id,
        request=request or _request(action),
    )


def test_state_machine_allows_only_owner_approved_transitions() -> None:
    assert review_transition(ReviewState.REVIEWABLE, ReviewAction.APPROVE) is ReviewState.APPROVED
    assert review_transition(ReviewState.REVIEWABLE, ReviewAction.REJECT) is ReviewState.REJECTED
    assert review_transition(ReviewState.APPROVED, ReviewAction.REVOKE) is ReviewState.REVOKED

    allowed = {
        (ReviewState.REVIEWABLE, ReviewAction.APPROVE),
        (ReviewState.REVIEWABLE, ReviewAction.REJECT),
        (ReviewState.APPROVED, ReviewAction.REVOKE),
    }
    assert all(
        review_transition(state, action) is None
        for state in ReviewState
        for action in ReviewAction
        if (state, action) not in allowed
    )


def test_submission_starts_reviewable_and_approval_appends_complete_snapshot(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    published = _publish(store, archive)
    submission = published.submission
    artifact_before = store.load_submission_artifact(submission.submission_id)

    receipt = _decide(store, submission.submission_id, ReviewAction.APPROVE)
    decision = receipt.decision

    assert not receipt.replayed
    assert decision.from_state is ReviewState.REVIEWABLE
    assert decision.to_state is ReviewState.APPROVED
    assert receipt.current_state is ReviewState.APPROVED
    assert decision.sequence == 1
    assert decision.package_version == submission.package_version
    assert decision.membership.actor_id == ACTOR_IDS["teacher"]
    assert decision.membership.role is CohortRole.TEACHER
    assert decision.membership.assurance is AssuranceLevel.AAL2
    assert decision.membership.revision == 1
    assert decision.reason == "Reviewed against the course package policy."
    assert json.loads(decision.result_metadata_json) == {"rubric_version": "review-v1"}
    assert decision.decided_at == NOW
    assert decision.correlation_id == "course-review-2026-001"
    assert store.load_submission(submission.submission_id).state is SubmissionState.REVIEWABLE
    assert store.load_submission_artifact(submission.submission_id) == artifact_before == archive


def test_rejection_is_terminal_and_correction_requires_a_new_version(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    submission_id = _publish(store, archive).submission.submission_id
    rejected = _decide(store, submission_id, ReviewAction.REJECT)

    assert rejected.current_state is ReviewState.REJECTED
    for action in (ReviewAction.APPROVE, ReviewAction.REJECT):
        with pytest.raises(ReviewTransitionConflictError):
            _decide(
                store,
                submission_id,
                action,
                request=_request(action, key=f"after-rejection-{action.value}"),
            )
    with pytest.raises(ReviewTransitionConflictError):
        _decide(
            store,
            submission_id,
            ReviewAction.REVOKE,
            actor="course-admin",
            request=_request(ReviewAction.REVOKE, key="revoke-after-rejection"),
        )
    assert store._connection.execute(
        "SELECT count(*) FROM package_review_decisions"
    ).fetchone() == (1,)


def test_revocation_is_admin_only_prospective_and_preserves_historical_identity(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    submission = _publish(store, archive).submission
    artifact_before = store.load_submission_artifact(submission.submission_id)
    identity_before = store.load_package_version(PACKAGE_ID, "1.0.0")
    _decide(store, submission.submission_id, ReviewAction.APPROVE)

    with pytest.raises(ReviewAccessDeniedError):
        _decide(
            store,
            submission.submission_id,
            ReviewAction.REVOKE,
            actor="teacher",
        )
    revoked = _decide(
        store,
        submission.submission_id,
        ReviewAction.REVOKE,
        actor="course-admin",
    )

    assert revoked.decision.from_state is ReviewState.APPROVED
    assert revoked.current_state is ReviewState.REVOKED
    assert revoked.decision.sequence == 2
    assert store.load_package_version(PACKAGE_ID, "1.0.0") == identity_before
    assert store.load_submission_artifact(submission.submission_id) == artifact_before
    assert store.load_submission(submission.submission_id) == submission
    with pytest.raises(ReviewTransitionConflictError):
        _decide(
            store,
            submission.submission_id,
            ReviewAction.APPROVE,
            actor="course-admin",
            request=_request(ReviewAction.APPROVE, key="approve-after-revocation"),
        )


def test_self_approval_is_denied_for_the_submitting_teacher(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    store.grant_namespace(
        NamespaceGrant(
            PACKAGE_ID,
            COHORT_ID,
            ACTOR_IDS["teacher"],
            NamespacePermission.SUBMIT,
            ACTOR_IDS["course-admin"],
            CREATED,
        )
    )
    submission_id = _publish(store, archive, actor="teacher").submission.submission_id

    with pytest.raises(ReviewAccessDeniedError):
        _decide(store, submission_id, ReviewAction.APPROVE, actor="teacher")

    approved = _decide(store, submission_id, ReviewAction.APPROVE, actor="second-teacher")
    assert approved.current_state is ReviewState.APPROVED


def test_student_and_non_mfa_teacher_cannot_make_decisions(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    submission_id = _publish(store, archive).submission.submission_id
    service = PackageReviewService(store, clock=lambda: NOW)

    with pytest.raises(ReviewAccessDeniedError):
        service.decide(
            identity=_identity("student"),
            submission_id=submission_id,
            request=_request(ReviewAction.APPROVE, key="student-review"),
        )
    with pytest.raises(ReviewAccessDeniedError):
        service.decide(
            identity=_identity("teacher", assurance=AssuranceLevel.AAL1),
            submission_id=submission_id,
            request=_request(ReviewAction.APPROVE, key="no-mfa-review"),
        )


def test_unbound_oidc_identity_cannot_enter_review_authorization(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    submission_id = _publish(store, archive).submission.submission_id

    with pytest.raises(ReviewAuthenticationError, match="not bound"):
        PackageReviewService(store, clock=lambda: NOW).decide(
            identity=AuthenticatedOIDCIdentity(
                ISSUER,
                "provider-unbound-reviewer",
                AssuranceLevel.AAL2,
            ),
            submission_id=submission_id,
            request=_request(ReviewAction.APPROVE, key="unbound-review"),
        )


def test_cross_cohort_and_unknown_submission_ids_have_same_bola_denial(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    submission_id = _publish(store, archive).submission.submission_id

    with pytest.raises(ReviewAccessDeniedError) as cross_cohort:
        _decide(
            store,
            submission_id,
            ReviewAction.APPROVE,
            actor="other-teacher",
        )
    with pytest.raises(ReviewAccessDeniedError) as unknown:
        _decide(
            store,
            "00000000-0000-4000-8000-000000000099",
            ReviewAction.APPROVE,
            actor="other-teacher",
            request=_request(ReviewAction.APPROVE, key="unknown-review"),
        )

    assert str(cross_cohort.value) == str(unknown.value) == "review decision is not authorized"


def test_identical_replay_returns_original_decision_without_duplicate_audit(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    submission_id = _publish(store, archive).submission.submission_id
    request = _request(ReviewAction.APPROVE)
    first = _decide(store, submission_id, ReviewAction.APPROVE, request=request)
    replay = _decide(store, submission_id, ReviewAction.APPROVE, request=request)

    assert replay.replayed
    assert replay.decision == first.decision
    assert replay.current_state is ReviewState.APPROVED
    assert store._connection.execute(
        "SELECT count(*) FROM package_review_decisions"
    ).fetchone() == (1,)
    assert store._connection.execute(
        "SELECT count(*) FROM audit_events WHERE event_type = 'package.review-decision'"
    ).fetchone() == (1,)


def test_replay_rechecks_current_membership_authority(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    submission_id = _publish(store, archive).submission.submission_id
    request = _request(ReviewAction.REJECT)
    _decide(store, submission_id, ReviewAction.REJECT, request=request)
    store._connection.execute(
        """
        UPDATE cohort_memberships SET active = 0, revision = 2
        WHERE cohort_id = ? AND actor_id = ?
        """,
        (COHORT_ID, ACTOR_IDS["teacher"]),
    )

    with pytest.raises(ReviewAccessDeniedError):
        _decide(store, submission_id, ReviewAction.REJECT, request=request)


def test_idempotency_key_reuse_with_changed_reason_fails_closed(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    submission_id = _publish(store, archive).submission.submission_id
    first = _request(ReviewAction.APPROVE, key="shared-decision-key")
    _decide(store, submission_id, ReviewAction.APPROVE, request=first)
    changed = _request(
        ReviewAction.APPROVE,
        key="shared-decision-key",
        reason="A different decision reason.",
    )

    with pytest.raises(ReviewConflictError, match="idempotency key"):
        _decide(store, submission_id, ReviewAction.APPROVE, request=changed)


def test_concurrent_identical_decisions_converge_to_one_result(
    tmp_path: Path,
    archive: bytes,
) -> None:
    database = tmp_path / "identical-review.sqlite3"
    seeded = _open_seeded_store(database)
    submission_id = _publish(seeded, archive).submission.submission_id
    seeded.close()
    barrier = Barrier(2)
    request = _request(ReviewAction.APPROVE, key="concurrent-identical-review")

    def approve() -> tuple[str, bool]:
        local = SQLiteReviewStore.open(database)
        try:
            barrier.wait()
            receipt = _decide(
                local,
                submission_id,
                ReviewAction.APPROVE,
                request=request,
            )
            return receipt.decision.decision_id, receipt.replayed
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(lambda _: approve(), range(2)))

    check = SQLiteReviewStore.open(database)
    try:
        assert len({item[0] for item in results}) == 1
        assert sorted(item[1] for item in results) == [False, True]
        assert check._connection.execute(
            "SELECT count(*) FROM package_review_decisions"
        ).fetchone() == (1,)
        assert check._connection.execute(
            "SELECT count(*) FROM audit_events WHERE event_type = 'package.review-decision'"
        ).fetchone() == (1,)
    finally:
        check.close()


def test_concurrent_conflicting_decisions_commit_one_coherent_terminal_state(
    tmp_path: Path,
    archive: bytes,
) -> None:
    database = tmp_path / "conflicting-review.sqlite3"
    seeded = _open_seeded_store(database)
    submission_id = _publish(seeded, archive).submission.submission_id
    seeded.close()
    barrier = Barrier(2)

    def decide(actor: str, action: ReviewAction) -> str:
        local = SQLiteReviewStore.open(database)
        try:
            barrier.wait()
            try:
                receipt = _decide(
                    local,
                    submission_id,
                    action,
                    actor=actor,
                    request=_request(action, key=f"concurrent-{action.value}"),
                )
            except ReviewTransitionConflictError:
                return "conflict"
            return receipt.current_state.value
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = (
            executor.submit(decide, "teacher", ReviewAction.APPROVE),
            executor.submit(decide, "second-teacher", ReviewAction.REJECT),
        )
        results = tuple(future.result() for future in futures)

    check = SQLiteReviewStore.open(database)
    try:
        assert results.count("conflict") == 1
        assert set(results) & {ReviewState.APPROVED.value, ReviewState.REJECTED.value}
        assert check.load_review_state(submission_id) in (
            ReviewState.APPROVED,
            ReviewState.REJECTED,
        )
        assert check._connection.execute(
            "SELECT count(*) FROM package_review_decisions"
        ).fetchone() == (1,)
    finally:
        check.close()


def test_audit_failure_rolls_back_decision_and_idempotency_atomically(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    submission_id = _publish(store, archive).submission.submission_id
    store.append_audit_event(
        AuditEvent(
            event_id="00000000-0000-4000-8000-000000000099",
            occurred_at=NOW,
            retention_until=CLOSES.replace(year=CLOSES.year + 2),
            principal_kind=PrincipalKind.ACTOR,
            principal_id=ACTOR_IDS["teacher"],
            event_type="package.review-decision",
            object_type="test",
            object_id="reserved",
            cohort_id=COHORT_ID,
            idempotency_key="atomic-review-failure",
            details_json="{}",
        )
    )

    with pytest.raises(sqlite3.IntegrityError):
        _decide(
            store,
            submission_id,
            ReviewAction.APPROVE,
            request=_request(ReviewAction.APPROVE, key="atomic-review-failure"),
        )

    assert store.load_review_state(submission_id) is ReviewState.REVIEWABLE
    assert store._connection.execute(
        "SELECT count(*) FROM package_review_decisions"
    ).fetchone() == (0,)
    assert store._connection.execute(
        "SELECT count(*) FROM idempotency_records WHERE operation = 'package.review-decision'"
    ).fetchone() == (0,)


def test_decision_and_audit_rows_are_append_only(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    submission_id = _publish(store, archive).submission.submission_id
    decision = _decide(store, submission_id, ReviewAction.APPROVE).decision

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store._connection.execute(
            "UPDATE package_review_decisions SET reason = reason WHERE decision_id = ?",
            (decision.decision_id,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store._connection.execute(
            "DELETE FROM package_review_decisions WHERE decision_id = ?",
            (decision.decision_id,),
        )
    audit_id = store._connection.execute(
        "SELECT event_id FROM audit_events WHERE event_type = 'package.review-decision'"
    ).fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store._connection.execute(
            "DELETE FROM audit_events WHERE event_id = ?",
            (audit_id,),
        )


def test_persistence_rejects_a_decision_that_does_not_extend_current_state(
    store: SQLiteReviewStore,
    archive: bytes,
) -> None:
    submission_id = _publish(store, archive).submission.submission_id
    approved = _decide(store, submission_id, ReviewAction.APPROVE).decision
    stale_rejection = replace(
        approved,
        decision_id="00000000-0000-4000-8000-000000000099",
        sequence=2,
        action=ReviewAction.REJECT,
        from_state=ReviewState.REVIEWABLE,
        to_state=ReviewState.REJECTED,
        idempotency_key="stale-rejection",
    )

    with pytest.raises(ReviewPersistenceConflictError, match="append-only"):
        store.append_review_decision(stale_rejection)

    assert store.load_review_state(submission_id) is ReviewState.APPROVED


def test_decision_api_accepts_no_client_role_cohort_state_version_or_digest_claims() -> None:
    assert set(inspect.signature(PackageReviewService.decide).parameters) == {
        "self",
        "identity",
        "submission_id",
        "request",
    }


def test_review_slice_does_not_cross_deferred_boundaries() -> None:
    from explore.online import review as module

    source = inspect.getsource(module).lower()
    forbidden = (
        "flask",
        "fastapi",
        "requests",
        "subprocess",
        "registry_read",
        "authorizationaction.pin",
        "authorizationaction.configure",
        "signing",
        "deployment",
        "moderation",
        "exec(",
        "eval(",
    )

    assert all(token not in source for token in forbidden)
