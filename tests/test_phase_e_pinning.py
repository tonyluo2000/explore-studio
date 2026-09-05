"""Authorization, registry binding, replay, and concurrency tests for pinning."""

from __future__ import annotations

import hashlib
import inspect
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier
from uuid import UUID

import pytest

from explore.online import (
    Actor,
    AssuranceLevel,
    AuditEvent,
    AuthenticatedOIDCIdentity,
    ClassWorldPinningService,
    ClassWorldPinRequest,
    Cohort,
    CohortMembership,
    CohortRole,
    IdentityProvider,
    PackageNamespace,
    PackageReviewService,
    PackageSubmissionService,
    PinAccessDeniedError,
    PinConfigurationError,
    PinConflictError,
    PrincipalKind,
    PublicationAcknowledgment,
    PublicationAuthority,
    PublicationPolicy,
    ReviewAction,
    ReviewDecisionRequest,
    SQLitePinningStore,
)
from explore.packages import (
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldCohort,
    ClassWorldConfiguration,
    ClassWorldConfigurationSpec,
    ClassWorldPackagePin,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    build_class_world_configuration,
    export_explorer_package,
    serialize_class_world_manifest,
)

NOW = datetime(2026, 9, 5, 20, 0, tzinfo=UTC)
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
    "other-admin": "00000000-0000-4000-8000-000000000004",
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
    grantor: str = "course-admin",
) -> CohortMembership:
    return CohortMembership(
        cohort_id=cohort_id,
        actor_id=ACTOR_IDS[name],
        role=role,
        granted_by_actor_id=ACTOR_IDS[grantor],
        granted_at=CREATED,
    )


def _open_seeded_store(path: Path) -> SQLitePinningStore:
    store = SQLitePinningStore.open(path)
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

    other_admin = _membership(
        "other-admin",
        CohortRole.COURSE_ADMIN,
        cohort_id=OTHER_COHORT_ID,
        grantor="other-admin",
    )
    store.create_cohort(
        Cohort(OTHER_COHORT_ID, "Example Academy", CREATED, CLOSES),
        other_admin,
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
def store(tmp_path: Path) -> SQLitePinningStore:
    value = _open_seeded_store(tmp_path / "pinning.sqlite3")
    yield value
    value.close()


def _configuration(
    *,
    package_version: str = "1.0.0",
    cohort_id: str = COHORT_ID,
    class_world_version: str = "1.0.0",
) -> ClassWorldConfiguration:
    provenance = PackageProvenance(PACKAGE_ID, package_version, "0.1")
    registration = CharacterRegistration(
        qualified_id=f"{PACKAGE_ID}:nova",
        contribution_id="nova",
        provenance=provenance,
        character=CharacterRegistrationSpec("Nova", 10, 20, "gold"),
        asset_reference=None,
    )
    registration_plan = StudentAPIRegistrationPlan(provenance, (registration,))
    selected = SelectedPackagePlan(PACKAGE_ID, package_version, provenance, registration_plan)
    plan = PackageSetPlan("0.1", (selected,), (registration,))
    spec = ClassWorldConfigurationSpec(
        schema_version="0.1",
        class_world_id="expedition-orion",
        display_name="Explorer World — Fall 2026",
        class_world_version=class_world_version,
        engine_version="0.1.0",
        student_api_version="0.1",
        cohort=ClassWorldCohort(cohort_id, "Expedition Orion"),
        packages=(ClassWorldPackagePin(PACKAGE_ID, package_version),),
    )
    result = build_class_world_configuration(spec, plan)
    assert result.is_configured and result.configuration is not None
    return result.configuration


def _publish(store: SQLitePinningStore, archive: bytes):
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


def _decide(
    store: SQLitePinningStore,
    submission_id: str,
    action: ReviewAction,
    *,
    key: str | None = None,
):
    selected_key = key or f"{action.value}-nova-v1"
    return PackageReviewService(store, clock=lambda: NOW).decide(
        identity=_identity("course-admin" if action is ReviewAction.REVOKE else "teacher"),
        submission_id=submission_id,
        request=ReviewDecisionRequest(
            action=action,
            reason="Reviewed against the course package policy.",
            result_metadata_json='{"rubric_version":"review-v1"}',
            correlation_id=f"review-{selected_key}",
            idempotency_key=selected_key,
        ),
    )


def _request(
    *,
    package_version: str = "1.0.0",
    key: str = "pin-nova-v1",
    correlation_id: str = "class-world-config-pin-001",
) -> ClassWorldPinRequest:
    return ClassWorldPinRequest(PACKAGE_ID, package_version, correlation_id, key)


def _pin(
    store: SQLitePinningStore,
    configuration: ClassWorldConfiguration,
    *,
    actor: str = "course-admin",
    request: ClassWorldPinRequest | None = None,
):
    return ClassWorldPinningService(store, clock=lambda: NOW).pin_exact(
        identity=_identity(actor),
        configuration=configuration,
        request=request or _request(),
    )


def _approved_submission(store: SQLitePinningStore, archive: bytes):
    submission = _publish(store, archive)
    approval = _decide(store, submission.submission_id, ReviewAction.APPROVE).decision
    return submission, approval


def test_course_admin_pins_exact_registry_identity_to_unchanged_configuration(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    submission, approval = _approved_submission(store, archive)
    configuration = _configuration()
    canonical_before = serialize_class_world_manifest(configuration)

    receipt = _pin(store, configuration)
    pin = receipt.pin

    assert not receipt.replayed
    assert pin.configuration_identity == configuration.identity
    assert pin.configuration_sha256 == hashlib.sha256(canonical_before.encode("utf-8")).hexdigest()
    assert pin.package_version == submission.package_version
    assert pin.package_version.raw_zip_sha256 == submission.package_version.raw_zip_sha256
    assert pin.approval_decision_id == approval.decision_id
    assert pin.artifact_reference == submission.submission_id
    assert pin.cohort_id == COHORT_ID
    assert pin.compatibility.student_api_version == configuration.student_api_version
    assert pin.authority.actor_id == ACTOR_IDS["course-admin"]
    assert pin.authority.role is CohortRole.COURSE_ADMIN
    assert pin.authority.assurance is AssuranceLevel.AAL2
    assert serialize_class_world_manifest(configuration) == canonical_before


@pytest.mark.parametrize("actor", ["student", "teacher"])
def test_only_course_admin_can_pin(
    store: SQLitePinningStore,
    archive: bytes,
    actor: str,
) -> None:
    _approved_submission(store, archive)

    with pytest.raises(PinAccessDeniedError):
        _pin(store, _configuration(), actor=actor)


def test_course_admin_requires_current_same_cohort_aal2_authority(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    _approved_submission(store, archive)
    service = ClassWorldPinningService(store, clock=lambda: NOW)

    with pytest.raises(PinAccessDeniedError):
        service.pin_exact(
            identity=_identity("course-admin", assurance=AssuranceLevel.AAL1),
            configuration=_configuration(),
            request=_request(key="non-mfa-pin"),
        )
    with pytest.raises(PinAccessDeniedError):
        _pin(store, _configuration(), actor="other-admin", request=_request(key="cross-pin"))


def test_cross_cohort_and_unknown_registry_objects_have_same_bola_denial(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    _approved_submission(store, archive)

    with pytest.raises(PinAccessDeniedError) as cross_cohort:
        _pin(
            store,
            _configuration(cohort_id=OTHER_COHORT_ID),
            actor="other-admin",
            request=_request(key="cross-cohort-pin"),
        )
    with pytest.raises(PinAccessDeniedError) as unknown:
        _pin(
            store,
            _configuration(package_version="9.9.9", cohort_id=OTHER_COHORT_ID),
            actor="other-admin",
            request=_request(package_version="9.9.9", key="unknown-pin"),
        )

    assert str(cross_cohort.value) == str(unknown.value) == "class-world pin is not authorized"


@pytest.mark.parametrize("decision", [None, ReviewAction.REJECT])
def test_reviewable_and_rejected_versions_cannot_be_pinned(
    store: SQLitePinningStore,
    archive: bytes,
    decision: ReviewAction | None,
) -> None:
    submission = _publish(store, archive)
    if decision is not None:
        _decide(store, submission.submission_id, decision)

    with pytest.raises(PinAccessDeniedError):
        _pin(store, _configuration())
    assert store._connection.execute(
        "SELECT count(*) FROM class_world_package_pins"
    ).fetchone() == (0,)
    assert store._connection.execute(
        "SELECT count(*) FROM class_world_configuration_bindings"
    ).fetchone() == (0,)


def test_revocation_blocks_future_pin_but_preserves_historical_pin_and_configuration(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    submission, approval = _approved_submission(store, archive)
    configuration = _configuration()
    historical = _pin(store, configuration).pin
    config_before = serialize_class_world_manifest(configuration)
    artifact_before = store.load_submission_artifact(submission.submission_id)
    revocation = _decide(store, submission.submission_id, ReviewAction.REVOKE).decision

    with pytest.raises(PinAccessDeniedError):
        _pin(store, configuration)

    assert store.load_class_world_pin_by_id(historical.pin_id) == historical
    assert store.load_review_decision(approval.decision_id) == approval
    assert store.load_review_decision(revocation.decision_id) == revocation
    assert store.load_submission_artifact(submission.submission_id) == artifact_before == archive
    assert serialize_class_world_manifest(configuration) == config_before


def test_stale_registry_read_cannot_authorize_a_pin_after_revocation(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    submission, _ = _approved_submission(store, archive)
    stale_entry = store.project_approved_entry(PACKAGE_ID, "1.0.0")
    assert stale_entry is not None
    _decide(store, submission.submission_id, ReviewAction.REVOKE)

    with pytest.raises(PinAccessDeniedError):
        _pin(store, _configuration(), request=_request(key="stale-entry-pin"))


@pytest.mark.parametrize("value", ["latest", "1.x", "^1.0.0", ">=1.0.0"])
def test_pin_request_rejects_latest_ranges_and_fallback_values(value: str) -> None:
    with pytest.raises(ValueError, match="exact Semantic Version"):
        _request(package_version=value)


def test_configuration_must_already_contain_the_requested_exact_pin(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    _approved_submission(store, archive)

    with pytest.raises(PinConfigurationError, match="does not contain"):
        _pin(
            store,
            _configuration(package_version="2.0.0"),
            request=_request(package_version="1.0.0"),
        )


def test_pin_api_accepts_no_client_owner_cohort_digest_or_approval_claims() -> None:
    assert set(inspect.signature(ClassWorldPinningService.pin_exact).parameters) == {
        "self",
        "identity",
        "configuration",
        "request",
    }
    assert set(inspect.signature(ClassWorldPinRequest).parameters) == {
        "package_id",
        "semantic_version",
        "correlation_id",
        "idempotency_key",
    }


def test_identical_replay_returns_one_pin_and_one_audit(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    _approved_submission(store, archive)
    configuration = _configuration()
    request = _request()

    first = _pin(store, configuration, request=request)
    replay = _pin(store, configuration, request=request)

    assert replay.replayed
    assert replay.pin == first.pin
    assert store._connection.execute(
        "SELECT count(*) FROM class_world_package_pins"
    ).fetchone() == (1,)
    assert store._connection.execute(
        "SELECT count(*) FROM audit_events WHERE event_type = 'class-world.pin'"
    ).fetchone() == (1,)
    assert store._connection.execute(
        "SELECT count(*) FROM idempotency_records WHERE operation = 'class-world.pin-exact'"
    ).fetchone() == (1,)


def test_duplicate_identical_pin_with_new_key_reuses_immutable_pin_identity(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    _approved_submission(store, archive)
    configuration = _configuration()
    first = _pin(store, configuration).pin
    duplicate = _pin(
        store,
        configuration,
        request=_request(key="duplicate-pin", correlation_id="duplicate-attempt"),
    )

    assert duplicate.replayed
    assert duplicate.pin == first
    assert store._connection.execute(
        "SELECT count(*) FROM class_world_package_pins"
    ).fetchone() == (1,)
    assert store._connection.execute(
        "SELECT count(*) FROM audit_events WHERE event_type = 'class-world.pin'"
    ).fetchone() == (2,)


def test_configuration_identity_cannot_be_rebound_to_changed_configuration_bytes(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    _approved_submission(store, archive)
    configuration = _configuration()
    _pin(store, configuration)
    changed = replace(configuration, display_name="Changed configuration declaration")

    with pytest.raises(PinConflictError, match="different canonical bytes"):
        _pin(store, changed, request=_request(key="changed-configuration-pin"))


def test_changed_replay_under_same_key_fails_closed(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    _approved_submission(store, archive)
    configuration = _configuration()
    _pin(store, configuration, request=_request(key="shared-pin-key"))

    with pytest.raises(PinConflictError, match="idempotency key"):
        _pin(
            store,
            configuration,
            request=_request(key="shared-pin-key", correlation_id="changed-correlation"),
        )


def test_replay_rechecks_current_course_admin_authority(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    _approved_submission(store, archive)
    configuration = _configuration()
    request = _request(key="authority-recheck-pin")
    _pin(store, configuration, request=request)
    store._connection.execute(
        """
        UPDATE cohort_memberships SET active = 0, revision = 2
        WHERE cohort_id = ? AND actor_id = ?
        """,
        (COHORT_ID, ACTOR_IDS["course-admin"]),
    )

    with pytest.raises(PinAccessDeniedError):
        _pin(store, configuration, request=request)


def test_concurrent_identical_pins_converge_to_one_record_and_audit(
    tmp_path: Path,
    archive: bytes,
) -> None:
    database = tmp_path / "concurrent-pinning.sqlite3"
    seeded = _open_seeded_store(database)
    _approved_submission(seeded, archive)
    seeded.close()
    barrier = Barrier(2)
    configuration = _configuration()
    request = _request(key="concurrent-pin")

    def pin() -> tuple[str, bool]:
        local = SQLitePinningStore.open(database)
        try:
            barrier.wait()
            receipt = _pin(local, configuration, request=request)
            return receipt.pin.pin_id, receipt.replayed
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(lambda _: pin(), range(2)))

    check = SQLitePinningStore.open(database)
    try:
        assert len({item[0] for item in results}) == 1
        assert sorted(item[1] for item in results) == [False, True]
        assert check._connection.execute(
            "SELECT count(*) FROM class_world_package_pins"
        ).fetchone() == (1,)
        assert check._connection.execute(
            "SELECT count(*) FROM audit_events WHERE event_type = 'class-world.pin'"
        ).fetchone() == (1,)
    finally:
        check.close()


def test_concurrent_revocation_and_pin_are_serialized_without_post_revocation_pin(
    tmp_path: Path,
    archive: bytes,
) -> None:
    database = tmp_path / "revocation-pinning.sqlite3"
    seeded = _open_seeded_store(database)
    submission, _ = _approved_submission(seeded, archive)
    seeded.close()
    barrier = Barrier(2)
    configuration = _configuration()

    def revoke() -> str:
        local = SQLitePinningStore.open(database)
        try:
            barrier.wait()
            _decide(local, submission.submission_id, ReviewAction.REVOKE)
            return "revoked"
        finally:
            local.close()

    def pin() -> str:
        local = SQLitePinningStore.open(database)
        try:
            barrier.wait()
            try:
                _pin(local, configuration, request=_request(key="revocation-race-pin"))
            except PinAccessDeniedError:
                return "denied-after-revocation"
            return "pinned-before-revocation"
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        revoke_future = executor.submit(revoke)
        pin_future = executor.submit(pin)
        results = (revoke_future.result(), pin_future.result())

    check = SQLitePinningStore.open(database)
    try:
        assert results[0] == "revoked"
        assert results[1] in ("denied-after-revocation", "pinned-before-revocation")
        expected_pins = 1 if results[1] == "pinned-before-revocation" else 0
        assert check._connection.execute(
            "SELECT count(*) FROM class_world_package_pins"
        ).fetchone() == (expected_pins,)
        assert check.project_approved_entry(PACKAGE_ID, "1.0.0") is None
    finally:
        check.close()


def test_audit_failure_rolls_back_pin_and_idempotency_atomically(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    _approved_submission(store, archive)
    duplicate_id = "00000000-0000-4000-8000-000000000099"
    store.append_audit_event(
        AuditEvent(
            event_id=duplicate_id,
            occurred_at=NOW,
            retention_until=CLOSES.replace(year=CLOSES.year + 2),
            principal_kind=PrincipalKind.ACTOR,
            principal_id=ACTOR_IDS["course-admin"],
            event_type="test.pin-reserved",
            object_type="test",
            object_id="reserved",
            cohort_id=COHORT_ID,
            idempotency_key="reserved-pin-audit",
            details_json="{}",
        )
    )
    service = ClassWorldPinningService(
        store,
        clock=lambda: NOW,
        uuid_factory=lambda: UUID(duplicate_id),
    )

    with pytest.raises(sqlite3.IntegrityError):
        service.pin_exact(
            identity=_identity("course-admin"),
            configuration=_configuration(),
            request=_request(key="failed-pin"),
        )

    assert store._connection.execute(
        "SELECT count(*) FROM class_world_package_pins"
    ).fetchone() == (0,)
    assert store._connection.execute(
        "SELECT count(*) FROM idempotency_records WHERE operation = 'class-world.pin-exact'"
    ).fetchone() == (0,)


def test_pin_and_audit_records_are_append_only(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    _approved_submission(store, archive)
    pin = _pin(store, _configuration()).pin

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store._connection.execute(
            """
            UPDATE class_world_package_pins
            SET package_version = package_version WHERE pin_id = ?
            """,
            (pin.pin_id,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store._connection.execute(
            "DELETE FROM class_world_package_pins WHERE pin_id = ?",
            (pin.pin_id,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        store._connection.execute(
            """
            UPDATE class_world_configuration_bindings
            SET configuration_sha256 = configuration_sha256
            WHERE class_world_id = ? AND class_world_version = ?
            """,
            pin.configuration_identity,
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        store._connection.execute(
            """
            DELETE FROM class_world_configuration_bindings
            WHERE class_world_id = ? AND class_world_version = ?
            """,
            pin.configuration_identity,
        )
    audit_id = store._connection.execute(
        "SELECT event_id FROM audit_events WHERE event_type = 'class-world.pin'"
    ).fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store._connection.execute("DELETE FROM audit_events WHERE event_id = ?", (audit_id,))


def test_pin_audit_contains_exact_configuration_registry_and_approval_binding(
    store: SQLitePinningStore,
    archive: bytes,
) -> None:
    submission, approval = _approved_submission(store, archive)
    configuration = _configuration()
    pin = _pin(store, configuration).pin
    row = store._connection.execute(
        "SELECT object_id, details_json FROM audit_events WHERE event_type = 'class-world.pin'"
    ).fetchone()

    assert row is not None and row[0] == pin.pin_id
    details = json.loads(row[1])
    assert details["class_world_id"] == configuration.class_world_id
    assert details["class_world_version"] == configuration.class_world_version
    assert details["package_id"] == PACKAGE_ID
    assert details["semantic_version"] == "1.0.0"
    assert details["raw_zip_sha256"] == submission.package_version.raw_zip_sha256
    assert details["approval_decision_id"] == approval.decision_id


def test_pinning_slice_does_not_change_build_or_cross_deferred_boundaries() -> None:
    from explore.online import pinning as module

    source = inspect.getsource(module).lower()
    forbidden = (
        "build_class_world_configuration",
        "build_package_set_plan",
        "apply_package_set",
        "flask",
        "fastapi",
        "requests",
        "subprocess",
        "signing",
        "deployment",
        "moderation",
        "exec(",
        "eval(",
    )

    assert all(token not in source for token in forbidden)
