"""Approved-only registry projection, authorization, and concurrency tests."""

from __future__ import annotations

import inspect
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier
from uuid import UUID

import pytest

from explore.online import (
    Actor,
    ApprovedRegistryService,
    AssuranceLevel,
    AuditEvent,
    AuthenticatedOIDCIdentity,
    Cohort,
    CohortMembership,
    CohortRole,
    IdentityProvider,
    PackageNamespace,
    PackageReviewService,
    PackageSubmissionService,
    PrincipalKind,
    PublicationAcknowledgment,
    PublicationAuthority,
    PublicationPolicy,
    RegistryAccessDeniedError,
    RegistryConflictError,
    RegistryExactLookup,
    RegistryScope,
    ReviewAction,
    ReviewDecisionRequest,
    SQLiteRegistryStore,
)
from explore.packages import export_explorer_package

NOW = datetime(2026, 9, 5, 18, 0, tzinfo=UTC)
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
    "other-student": "00000000-0000-4000-8000-000000000004",
    "other-teacher": "00000000-0000-4000-8000-000000000005",
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
    expected = AssuranceLevel.AAL1 if "student" in name else AssuranceLevel.AAL2
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


def _open_seeded_store(path: Path) -> SQLiteRegistryStore:
    store = SQLiteRegistryStore.open(path)
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
    store.grant_membership(_membership("other-student", CohortRole.STUDENT))
    store.grant_membership(_membership("teacher", CohortRole.TEACHER))

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
def store(tmp_path: Path) -> SQLiteRegistryStore:
    value = _open_seeded_store(tmp_path / "registry.sqlite3")
    yield value
    value.close()


def _publish(store: SQLiteRegistryStore, archive: bytes):
    return (
        PackageSubmissionService(
            store,
            PUBLICATION_POLICY,
            clock=lambda: NOW,
        )
        .submit(
            identity=_identity("student"),
            filename="nova-character-1.0.0.explorer-package.zip",
            archive_bytes=archive,
            idempotency_key="publish-nova-v1",
            acknowledgment=ACKNOWLEDGMENT,
        )
        .submission
    )


def _decision_request(action: ReviewAction, key: str) -> ReviewDecisionRequest:
    return ReviewDecisionRequest(
        action=action,
        reason="Reviewed against the course package policy.",
        result_metadata_json='{"rubric_version":"review-v1"}',
        correlation_id=f"review-{key}",
        idempotency_key=key,
    )


def _decide(
    store: SQLiteRegistryStore,
    submission_id: str,
    action: ReviewAction,
    *,
    actor: str = "teacher",
    key: str | None = None,
):
    selected_key = key or f"{action.value}-nova-v1"
    return PackageReviewService(store, clock=lambda: NOW).decide(
        identity=_identity(actor),
        submission_id=submission_id,
        request=_decision_request(action, selected_key),
    )


def _lookup(*, key: str = "registry-nova-v1") -> RegistryExactLookup:
    return RegistryExactLookup(
        package_id=PACKAGE_ID,
        semantic_version="1.0.0",
        correlation_id="future-pin-read-001",
        idempotency_key=key,
    )


def _read(
    store: SQLiteRegistryStore,
    *,
    actor: str = "teacher",
    lookup: RegistryExactLookup | None = None,
):
    return ApprovedRegistryService(store, clock=lambda: NOW).read_exact(
        identity=_identity(actor),
        lookup=lookup or _lookup(),
    )


def test_current_approval_projects_complete_exact_registry_entry(
    store: SQLiteRegistryStore,
    archive: bytes,
) -> None:
    submission = _publish(store, archive)
    approval = _decide(store, submission.submission_id, ReviewAction.APPROVE).decision

    receipt = _read(store)
    entry = receipt.entry

    assert not receipt.replayed
    assert entry.package_version == submission.package_version
    assert entry.owner_actor_id == ACTOR_IDS["student"]
    assert entry.cohort_id == COHORT_ID
    assert entry.scope is RegistryScope.COHORT
    assert entry.compatibility.student_api_version == "0.1"
    assert entry.artifact_reference == submission.submission_id
    assert entry.approval_decision_id == approval.decision_id
    assert entry.approved_at == approval.decided_at


@pytest.mark.parametrize("terminal", [None, ReviewAction.REJECT])
def test_reviewable_and_rejected_versions_are_not_registry_entries(
    store: SQLiteRegistryStore,
    archive: bytes,
    terminal: ReviewAction | None,
) -> None:
    submission = _publish(store, archive)
    if terminal is not None:
        _decide(store, submission.submission_id, terminal)

    assert store.project_approved_entry(PACKAGE_ID, "1.0.0") is None
    with pytest.raises(RegistryAccessDeniedError, match="not available"):
        _read(store)


def test_revocation_removes_future_projection_without_mutating_history(
    store: SQLiteRegistryStore,
    archive: bytes,
) -> None:
    submission = _publish(store, archive)
    artifact_before = store.load_submission_artifact(submission.submission_id)
    version_before = store.load_package_version(PACKAGE_ID, "1.0.0")
    approval = _decide(store, submission.submission_id, ReviewAction.APPROVE).decision
    lookup = _lookup()
    _read(store, lookup=lookup)
    revocation = _decide(
        store,
        submission.submission_id,
        ReviewAction.REVOKE,
        actor="course-admin",
    ).decision

    assert store.project_approved_entry(PACKAGE_ID, "1.0.0") is None
    with pytest.raises(RegistryAccessDeniedError, match="not available"):
        _read(store, lookup=lookup)
    assert store.load_submission(submission.submission_id) == submission
    assert store.load_submission_artifact(submission.submission_id) == artifact_before == archive
    assert store.load_package_version(PACKAGE_ID, "1.0.0") == version_before
    assert store.load_review_decision(approval.decision_id) == approval
    assert store.load_review_decision(revocation.decision_id) == revocation


def test_same_cohort_student_can_read_approved_entry(
    store: SQLiteRegistryStore,
    archive: bytes,
) -> None:
    submission = _publish(store, archive)
    _decide(store, submission.submission_id, ReviewAction.APPROVE)

    receipt = _read(store, actor="other-student", lookup=_lookup(key="peer-read"))

    assert receipt.entry.cohort_id == COHORT_ID


def test_cross_cohort_and_unknown_exact_versions_have_same_bola_denial(
    store: SQLiteRegistryStore,
    archive: bytes,
) -> None:
    submission = _publish(store, archive)
    _decide(store, submission.submission_id, ReviewAction.APPROVE)

    with pytest.raises(RegistryAccessDeniedError) as cross_cohort:
        _read(store, actor="other-teacher")
    with pytest.raises(RegistryAccessDeniedError) as unknown:
        _read(
            store,
            actor="other-teacher",
            lookup=RegistryExactLookup(
                PACKAGE_ID,
                "9.9.9",
                "future-pin-read-unknown",
                "unknown-version-read",
            ),
        )

    assert str(cross_cohort.value) == str(unknown.value) == "registry entry is not available"


def test_current_membership_and_privileged_assurance_are_rechecked(
    store: SQLiteRegistryStore,
    archive: bytes,
) -> None:
    submission = _publish(store, archive)
    _decide(store, submission.submission_id, ReviewAction.APPROVE)
    service = ApprovedRegistryService(store, clock=lambda: NOW)

    with pytest.raises(RegistryAccessDeniedError):
        service.read_exact(
            identity=_identity("teacher", assurance=AssuranceLevel.AAL1),
            lookup=_lookup(key="non-mfa-read"),
        )
    store._connection.execute(
        """
        UPDATE cohort_memberships SET active = 0, revision = 2
        WHERE cohort_id = ? AND actor_id = ?
        """,
        (COHORT_ID, ACTOR_IDS["teacher"]),
    )
    with pytest.raises(RegistryAccessDeniedError):
        _read(store, lookup=_lookup(key="inactive-read"))


@pytest.mark.parametrize("value", ["latest", "1.x", "^1.0.0", ">=1.0.0"])
def test_lookup_rejects_latest_and_floating_versions(value: str) -> None:
    with pytest.raises(ValueError, match="exact Semantic Version"):
        RegistryExactLookup(PACKAGE_ID, value, "correlation", "idempotency")


def test_read_api_accepts_no_client_owner_cohort_digest_state_or_approval_claims() -> None:
    assert set(inspect.signature(ApprovedRegistryService.read_exact).parameters) == {
        "self",
        "identity",
        "lookup",
    }
    assert set(inspect.signature(RegistryExactLookup).parameters) == {
        "package_id",
        "semantic_version",
        "correlation_id",
        "idempotency_key",
    }


def test_identical_replay_rechecks_projection_and_converges_without_duplicate_audit(
    store: SQLiteRegistryStore,
    archive: bytes,
) -> None:
    submission = _publish(store, archive)
    _decide(store, submission.submission_id, ReviewAction.APPROVE)
    lookup = _lookup()

    first = _read(store, lookup=lookup)
    replay = _read(store, lookup=lookup)

    assert replay.replayed
    assert replay.entry == first.entry
    assert store._connection.execute(
        "SELECT count(*) FROM audit_events WHERE event_type = 'registry.read'"
    ).fetchone() == (1,)
    assert store._connection.execute(
        "SELECT count(*) FROM idempotency_records WHERE operation = 'registry.read-exact'"
    ).fetchone() == (1,)


def test_identical_replay_rechecks_current_membership_authority(
    store: SQLiteRegistryStore,
    archive: bytes,
) -> None:
    submission = _publish(store, archive)
    _decide(store, submission.submission_id, ReviewAction.APPROVE)
    lookup = _lookup(key="authority-recheck-read")
    _read(store, lookup=lookup)
    store._connection.execute(
        """
        UPDATE cohort_memberships SET active = 0, revision = 2
        WHERE cohort_id = ? AND actor_id = ?
        """,
        (COHORT_ID, ACTOR_IDS["teacher"]),
    )

    with pytest.raises(RegistryAccessDeniedError):
        _read(store, lookup=lookup)

    assert store._connection.execute(
        "SELECT count(*) FROM audit_events WHERE event_type = 'registry.read'"
    ).fetchone() == (1,)


def test_idempotency_key_reuse_for_another_exact_lookup_fails_closed(
    store: SQLiteRegistryStore,
    archive: bytes,
) -> None:
    submission = _publish(store, archive)
    _decide(store, submission.submission_id, ReviewAction.APPROVE)
    _read(store, lookup=_lookup(key="shared-registry-key"))
    changed = RegistryExactLookup(
        PACKAGE_ID,
        "1.0.1",
        "future-pin-read-001",
        "shared-registry-key",
    )

    with pytest.raises(RegistryConflictError, match="idempotency key"):
        _read(store, lookup=changed)


def test_concurrent_identical_reads_converge_to_one_audit(
    tmp_path: Path,
    archive: bytes,
) -> None:
    database = tmp_path / "concurrent-registry.sqlite3"
    seeded = _open_seeded_store(database)
    submission = _publish(seeded, archive)
    _decide(seeded, submission.submission_id, ReviewAction.APPROVE)
    seeded.close()
    barrier = Barrier(2)

    def read() -> tuple[str, bool]:
        local = SQLiteRegistryStore.open(database)
        try:
            barrier.wait()
            receipt = _read(local, lookup=_lookup(key="concurrent-read"))
            return receipt.entry.approval_decision_id, receipt.replayed
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(lambda _: read(), range(2)))

    check = SQLiteRegistryStore.open(database)
    try:
        assert len({result[0] for result in results}) == 1
        assert sorted(result[1] for result in results) == [False, True]
        assert check._connection.execute(
            "SELECT count(*) FROM audit_events WHERE event_type = 'registry.read'"
        ).fetchone() == (1,)
    finally:
        check.close()


def test_concurrent_approval_and_read_are_serialized_to_one_coherent_snapshot(
    tmp_path: Path,
    archive: bytes,
) -> None:
    database = tmp_path / "approval-read.sqlite3"
    seeded = _open_seeded_store(database)
    submission = _publish(seeded, archive)
    seeded.close()
    barrier = Barrier(2)

    def approve() -> str:
        local = SQLiteRegistryStore.open(database)
        try:
            barrier.wait()
            _decide(local, submission.submission_id, ReviewAction.APPROVE)
            return "approved"
        finally:
            local.close()

    def read() -> str:
        local = SQLiteRegistryStore.open(database)
        try:
            barrier.wait()
            try:
                _read(local, lookup=_lookup(key="approval-race-read"))
            except RegistryAccessDeniedError:
                return "denied-before-approval"
            return "read-approved"
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        approve_future = executor.submit(approve)
        read_future = executor.submit(read)
        results = (approve_future.result(), read_future.result())

    check = SQLiteRegistryStore.open(database)
    try:
        assert results[0] == "approved"
        assert results[1] in ("denied-before-approval", "read-approved")
        assert check.project_approved_entry(PACKAGE_ID, "1.0.0") is not None
        expected_reads = 1 if results[1] == "read-approved" else 0
        assert check._connection.execute(
            "SELECT count(*) FROM audit_events WHERE event_type = 'registry.read'"
        ).fetchone() == (expected_reads,)
    finally:
        check.close()


def test_concurrent_revocation_and_read_never_return_a_post_revocation_entry(
    tmp_path: Path,
    archive: bytes,
) -> None:
    database = tmp_path / "revocation-read.sqlite3"
    seeded = _open_seeded_store(database)
    submission = _publish(seeded, archive)
    _decide(seeded, submission.submission_id, ReviewAction.APPROVE)
    seeded.close()
    barrier = Barrier(2)

    def revoke() -> str:
        local = SQLiteRegistryStore.open(database)
        try:
            barrier.wait()
            _decide(
                local,
                submission.submission_id,
                ReviewAction.REVOKE,
                actor="course-admin",
            )
            return "revoked"
        finally:
            local.close()

    def read() -> str:
        local = SQLiteRegistryStore.open(database)
        try:
            barrier.wait()
            try:
                _read(local, lookup=_lookup(key="revocation-race-read"))
            except RegistryAccessDeniedError:
                return "denied-after-revocation"
            return "read-before-revocation"
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        revoke_future = executor.submit(revoke)
        read_future = executor.submit(read)
        results = (revoke_future.result(), read_future.result())

    check = SQLiteRegistryStore.open(database)
    try:
        assert results[0] == "revoked"
        assert results[1] in ("denied-after-revocation", "read-before-revocation")
        assert check.project_approved_entry(PACKAGE_ID, "1.0.0") is None
        expected_reads = 1 if results[1] == "read-before-revocation" else 0
        assert check._connection.execute(
            "SELECT count(*) FROM audit_events WHERE event_type = 'registry.read'"
        ).fetchone() == (expected_reads,)
    finally:
        check.close()


def test_registry_read_audit_is_append_only_and_pin_ready(
    store: SQLiteRegistryStore,
    archive: bytes,
) -> None:
    submission = _publish(store, archive)
    approval = _decide(store, submission.submission_id, ReviewAction.APPROVE).decision
    entry = _read(store).entry
    row = store._connection.execute("""
        SELECT event_id, object_id, details_json FROM audit_events
        WHERE event_type = 'registry.read'
        """).fetchone()

    assert row is not None
    assert row[1] == approval.decision_id == entry.approval_decision_id
    details = json.loads(row[2])
    assert details["package_id"] == PACKAGE_ID
    assert details["semantic_version"] == "1.0.0"
    assert details["raw_zip_sha256"] == submission.package_version.raw_zip_sha256
    assert details["artifact_reference"] == submission.submission_id
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store._connection.execute("DELETE FROM audit_events WHERE event_id = ?", (row[0],))


def test_audit_failure_rolls_back_registry_read_idempotency(
    store: SQLiteRegistryStore,
    archive: bytes,
) -> None:
    submission = _publish(store, archive)
    _decide(store, submission.submission_id, ReviewAction.APPROVE)
    duplicate_event_id = "00000000-0000-4000-8000-000000000099"
    store.append_audit_event(
        AuditEvent(
            event_id=duplicate_event_id,
            occurred_at=NOW,
            retention_until=CLOSES.replace(year=CLOSES.year + 2),
            principal_kind=PrincipalKind.ACTOR,
            principal_id=ACTOR_IDS["teacher"],
            event_type="test.registry-reserved",
            object_type="test",
            object_id="reserved",
            cohort_id=COHORT_ID,
            idempotency_key="reserved-registry-audit",
            details_json="{}",
        )
    )
    service = ApprovedRegistryService(
        store,
        clock=lambda: NOW,
        uuid_factory=lambda: UUID(duplicate_event_id),
    )

    with pytest.raises(sqlite3.IntegrityError):
        service.read_exact(identity=_identity("teacher"), lookup=_lookup(key="failed-read"))

    assert store._connection.execute(
        "SELECT count(*) FROM idempotency_records WHERE operation = 'registry.read-exact'"
    ).fetchone() == (0,)


def test_registry_slice_does_not_cross_deferred_boundaries() -> None:
    from explore.online import registry as module

    source = inspect.getsource(module).lower()
    forbidden = (
        "flask",
        "fastapi",
        "requests",
        "subprocess",
        "authorizationaction.pin",
        "authorizationaction.configure",
        "signing",
        "deployment",
        "moderation",
        "exec(",
        "eval(",
    )

    assert all(token not in source for token in forbidden)
