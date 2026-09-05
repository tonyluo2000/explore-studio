"""Security- and constraint-focused tests for the Phase E online foundation."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier

import pytest

from explore.online import (
    Actor,
    AssuranceLevel,
    AuditEvent,
    AuthorizationAction,
    AuthorizationDecisionCode,
    AuthorizationResource,
    Cohort,
    CohortMembership,
    CohortRole,
    HumanPrincipal,
    IdempotencyConflictError,
    IdempotencyRecord,
    IdentityProvider,
    NamespaceGrant,
    NamespacePermission,
    PackageNamespace,
    PackageVersionIdentity,
    PersistenceAuthorizationError,
    PersistenceConflictError,
    PrincipalKind,
    ServicePrincipal,
    SQLiteFoundationStore,
    StoredPackageVersion,
    authorize,
)

NOW = datetime(2026, 9, 5, 3, 0, tzinfo=UTC)
COHORT_CLOSE = datetime(2027, 6, 30, 23, 59, tzinfo=UTC)
AUDIT_RETENTION = datetime(2029, 6, 30, 23, 59, tzinfo=UTC)
ISSUER = "https://identity.example.edu"
COHORT_ID = "fall-explorers"
OTHER_COHORT_ID = "winter-explorers"
PACKAGE_ID = "river-rescue"
ACTOR_IDS = {
    "student": "00000000-0000-4000-8000-000000000001",
    "teacher": "00000000-0000-4000-8000-000000000002",
    "course-admin": "00000000-0000-4000-8000-000000000003",
    "other-student": "00000000-0000-4000-8000-000000000004",
}
VERSION_IDENTITY = PackageVersionIdentity(PACKAGE_ID, "1.2.3", "a" * 64)
PROJECT_ROOT = Path(__file__).parents[1]


def _membership(
    actor_id: str,
    role: CohortRole,
    *,
    cohort_id: str = COHORT_ID,
    active: bool = True,
) -> CohortMembership:
    return CohortMembership(
        cohort_id=cohort_id,
        actor_id=actor_id,
        role=role,
        granted_by_actor_id=ACTOR_IDS["course-admin"],
        granted_at=NOW,
        active=active,
    )


def _human(
    role: CohortRole,
    *,
    actor_id: str | None = None,
    cohort_id: str = COHORT_ID,
    assurance: AssuranceLevel | None = None,
    active: bool = True,
    grants: tuple[NamespaceGrant, ...] = (),
) -> HumanPrincipal:
    selected_actor_id = actor_id or ACTOR_IDS[role.value]
    selected_assurance = assurance or (
        AssuranceLevel.AAL1 if role is CohortRole.STUDENT else AssuranceLevel.AAL2
    )
    return HumanPrincipal(
        selected_actor_id,
        selected_assurance,
        (_membership(selected_actor_id, role, cohort_id=cohort_id, active=active),),
        grants,
    )


def _resource(
    *,
    cohort_id: str = COHORT_ID,
    owner_actor_id: str = ACTOR_IDS["student"],
    submitted_by_actor_id: str = ACTOR_IDS["student"],
    approved: bool = True,
    revoked: bool = False,
    package_version: PackageVersionIdentity | None = VERSION_IDENTITY,
) -> AuthorizationResource:
    return AuthorizationResource(
        cohort_id=cohort_id,
        package_id=PACKAGE_ID,
        package_version=package_version,
        owner_actor_id=owner_actor_id,
        submitted_by_actor_id=submitted_by_actor_id,
        approved=approved,
        revoked=revoked,
    )


@pytest.mark.parametrize(
    ("principal", "allowed_actions"),
    [
        (
            _human(CohortRole.STUDENT),
            {AuthorizationAction.SUBMIT, AuthorizationAction.REGISTRY_READ},
        ),
        (
            _human(CohortRole.TEACHER),
            {
                AuthorizationAction.REVIEW,
                AuthorizationAction.APPROVE,
                AuthorizationAction.REGISTRY_READ,
                AuthorizationAction.PIN,
            },
        ),
        (
            _human(CohortRole.COURSE_ADMIN),
            {
                AuthorizationAction.REVIEW,
                AuthorizationAction.APPROVE,
                AuthorizationAction.REVOKE,
                AuthorizationAction.REGISTRY_READ,
                AuthorizationAction.PIN,
                AuthorizationAction.CONFIGURE,
            },
        ),
        (
            ServicePrincipal("class-world-builder", (VERSION_IDENTITY,)),
            {AuthorizationAction.REGISTRY_READ},
        ),
    ],
)
def test_owner_approved_authorization_matrix(
    principal: HumanPrincipal | ServicePrincipal,
    allowed_actions: set[AuthorizationAction],
) -> None:
    decisions = {
        action: authorize(principal, action, _resource()).allowed for action in AuthorizationAction
    }

    assert {action for action, allowed in decisions.items() if allowed} == allowed_actions


def test_local_runtime_and_package_tooling_do_not_import_online_foundation() -> None:
    local_sources = [
        *PROJECT_ROOT.joinpath("engine").rglob("*.py"),
        *(
            path
            for path in PROJECT_ROOT.joinpath("explore").rglob("*.py")
            if "online" not in path.relative_to(PROJECT_ROOT / "explore").parts
        ),
    ]

    assert local_sources
    assert all("explore.online" not in path.read_text(encoding="utf-8") for path in local_sources)


def test_cross_cohort_direct_object_access_is_denied_for_every_human_role() -> None:
    for role in CohortRole:
        principal = _human(role, cohort_id=OTHER_COHORT_ID)
        for action in AuthorizationAction:
            decision = authorize(principal, action, _resource())

            assert not decision.allowed
            assert decision.code is AuthorizationDecisionCode.MEMBERSHIP_REQUIRED


def test_guessed_private_package_is_not_readable_or_submittable_by_another_student() -> None:
    attacker = _human(CohortRole.STUDENT, actor_id=ACTOR_IDS["other-student"])
    private_resource = _resource(approved=False)

    read = authorize(attacker, AuthorizationAction.REGISTRY_READ, private_resource)
    submit = authorize(attacker, AuthorizationAction.SUBMIT, private_resource)

    assert not read.allowed
    assert read.code is AuthorizationDecisionCode.ROLE_FORBIDDEN
    assert not submit.allowed
    assert submit.code is AuthorizationDecisionCode.NAMESPACE_GRANT_REQUIRED


def test_inactive_membership_fails_closed_before_role_or_ownership_checks() -> None:
    principal = _human(CohortRole.STUDENT, active=False)

    decision = authorize(principal, AuthorizationAction.SUBMIT, _resource())

    assert not decision.allowed
    assert decision.code is AuthorizationDecisionCode.MEMBERSHIP_REQUIRED


@pytest.mark.parametrize("role", [CohortRole.TEACHER, CohortRole.COURSE_ADMIN])
@pytest.mark.parametrize("relationship", ["owner", "submitter"])
def test_privileged_human_cannot_self_approve(
    role: CohortRole,
    relationship: str,
) -> None:
    teacher = _human(role)
    overrides = {
        "owner_actor_id": (teacher.actor_id if relationship == "owner" else ACTOR_IDS["student"]),
        "submitted_by_actor_id": (
            teacher.actor_id if relationship == "submitter" else ACTOR_IDS["student"]
        ),
    }

    decision = authorize(teacher, AuthorizationAction.APPROVE, _resource(**overrides))

    assert not decision.allowed
    assert decision.code is AuthorizationDecisionCode.SELF_APPROVAL_FORBIDDEN


@pytest.mark.parametrize(
    "action",
    [
        AuthorizationAction.REVIEW,
        AuthorizationAction.APPROVE,
        AuthorizationAction.REVOKE,
        AuthorizationAction.PIN,
    ],
)
def test_version_actions_fail_closed_without_exact_immutable_identity(
    action: AuthorizationAction,
) -> None:
    admin = _human(CohortRole.COURSE_ADMIN)

    decision = authorize(admin, action, _resource(package_version=None))

    assert not decision.allowed
    assert decision.code is AuthorizationDecisionCode.EXACT_VERSION_REQUIRED


@pytest.mark.parametrize("role", [CohortRole.TEACHER, CohortRole.COURSE_ADMIN])
def test_privileged_role_requires_mfa_assurance(role: CohortRole) -> None:
    principal = _human(role, assurance=AssuranceLevel.AAL1)

    decision = authorize(principal, AuthorizationAction.REGISTRY_READ, _resource())

    assert not decision.allowed
    assert decision.code is AuthorizationDecisionCode.PRIVILEGED_ASSURANCE_REQUIRED


def test_explicit_same_cohort_namespace_grant_enables_submit_without_role_inheritance() -> None:
    teacher_id = ACTOR_IDS["teacher"]
    grant = NamespaceGrant(
        PACKAGE_ID,
        COHORT_ID,
        teacher_id,
        NamespacePermission.SUBMIT,
        ACTOR_IDS["course-admin"],
        NOW,
    )
    teacher = _human(CohortRole.TEACHER, grants=(grant,))

    assert authorize(teacher, AuthorizationAction.SUBMIT, _resource()).allowed


def test_service_principal_cannot_list_or_read_an_ungranted_exact_version() -> None:
    service = ServicePrincipal("class-world-builder", (VERSION_IDENTITY,))
    other_version = PackageVersionIdentity(PACKAGE_ID, "1.2.4", "b" * 64)

    broad = authorize(
        service,
        AuthorizationAction.REGISTRY_READ,
        _resource(package_version=None),
    )
    guessed = authorize(
        service,
        AuthorizationAction.REGISTRY_READ,
        _resource(package_version=other_version),
    )

    assert broad.code is AuthorizationDecisionCode.APPROVED_VERSION_REQUIRED
    assert guessed.code is AuthorizationDecisionCode.EXACT_SERVICE_GRANT_REQUIRED


def test_revoked_version_remains_historically_readable_but_cannot_be_newly_pinned() -> None:
    teacher = _human(CohortRole.TEACHER)
    revoked = _resource(revoked=True)

    assert authorize(teacher, AuthorizationAction.REGISTRY_READ, revoked).allowed
    pin = authorize(teacher, AuthorizationAction.PIN, revoked)
    assert not pin.allowed
    assert pin.code is AuthorizationDecisionCode.VERSION_REVOKED


def test_models_reject_mutation_and_invalid_external_identity_values() -> None:
    actor = Actor(ACTOR_IDS["student"], NOW)

    with pytest.raises(FrozenInstanceError):
        actor.actor_id = ACTOR_IDS["teacher"]  # type: ignore[misc]
    with pytest.raises(ValueError, match="absolute HTTPS"):
        IdentityProvider("http://identity.example.edu")
    with pytest.raises(ValueError, match="Semantic Versioning"):
        PackageVersionIdentity(PACKAGE_ID, "latest", "a" * 64)
    with pytest.raises(ValueError, match="lowercase 64-character"):
        PackageVersionIdentity(PACKAGE_ID, "1.2.3", "A" * 64)


def _bind_actor(store: SQLiteFoundationStore, label: str) -> Actor:
    actor = Actor(ACTOR_IDS[label], NOW)
    return store.bind_federated_actor(
        issuer=ISSUER,
        subject=f"{label}-subject",
        proposed_actor=actor,
    )


def _seed_store(path: Path) -> SQLiteFoundationStore:
    store = SQLiteFoundationStore.open(path)
    store.initialize_schema()
    store.approve_identity_provider(IdentityProvider(ISSUER))
    for label in ACTOR_IDS:
        _bind_actor(store, label)
    store.create_cohort(
        Cohort(COHORT_ID, "Example School", NOW, COHORT_CLOSE),
        _membership(ACTOR_IDS["course-admin"], CohortRole.COURSE_ADMIN),
    )
    store.create_cohort(
        Cohort(OTHER_COHORT_ID, "Example School", NOW, COHORT_CLOSE),
        _membership(
            ACTOR_IDS["course-admin"],
            CohortRole.COURSE_ADMIN,
            cohort_id=OTHER_COHORT_ID,
        ),
    )
    store.grant_membership(_membership(ACTOR_IDS["teacher"], CohortRole.TEACHER))
    store.grant_membership(_membership(ACTOR_IDS["student"], CohortRole.STUDENT))
    store.grant_membership(_membership(ACTOR_IDS["other-student"], CohortRole.STUDENT))
    store.create_namespace(PackageNamespace(PACKAGE_ID, COHORT_ID, ACTOR_IDS["student"], NOW))
    return store


def test_federated_binding_is_stable_and_excludes_mutable_profile_identity(tmp_path: Path) -> None:
    store = SQLiteFoundationStore.open(tmp_path / "foundation.db")
    store.initialize_schema()
    store.approve_identity_provider(IdentityProvider(ISSUER))
    original = Actor(ACTOR_IDS["student"], NOW)
    different_proposal = Actor(ACTOR_IDS["other-student"], NOW)

    first = store.bind_federated_actor(
        issuer=ISSUER,
        subject="opaque-provider-subject",
        proposed_actor=original,
    )
    replay = store.bind_federated_actor(
        issuer=ISSUER,
        subject="opaque-provider-subject",
        proposed_actor=different_proposal,
    )

    assert first == original
    assert replay == original
    connection = sqlite3.connect(tmp_path / "foundation.db")
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(federated_identities)").fetchall()
    }
    assert "email" not in columns
    assert "display_name" not in columns
    connection.close()
    store.close()


def test_concurrent_federated_binding_creates_only_one_internal_actor(tmp_path: Path) -> None:
    database = tmp_path / "concurrent.db"
    setup = SQLiteFoundationStore.open(database)
    setup.initialize_schema()
    setup.approve_identity_provider(IdentityProvider(ISSUER))
    setup.close()
    barrier = Barrier(2)

    def bind(actor_id: str) -> str:
        store = SQLiteFoundationStore.open(database)
        barrier.wait()
        actor = store.bind_federated_actor(
            issuer=ISSUER,
            subject="same-subject",
            proposed_actor=Actor(actor_id, NOW),
        )
        store.close()
        return actor.actor_id

    with ThreadPoolExecutor(max_workers=2) as executor:
        actor_ids = set(executor.map(bind, (ACTOR_IDS["student"], ACTOR_IDS["other-student"])))

    assert len(actor_ids) == 1
    connection = sqlite3.connect(database)
    assert connection.execute("SELECT count(*) FROM actors").fetchone() == (1,)
    assert connection.execute("SELECT count(*) FROM federated_identities").fetchone() == (1,)
    connection.close()


def test_database_enforces_global_namespace_and_same_cohort_ownership(tmp_path: Path) -> None:
    store = _seed_store(tmp_path / "foundation.db")

    with pytest.raises(sqlite3.IntegrityError):
        store.create_namespace(
            PackageNamespace(PACKAGE_ID, OTHER_COHORT_ID, ACTOR_IDS["course-admin"], NOW)
        )
    with pytest.raises(PersistenceAuthorizationError, match="active cohort member"):
        store.create_namespace(
            PackageNamespace("cross-cohort-owner", OTHER_COHORT_ID, ACTOR_IDS["student"], NOW)
        )
    store.close()


def test_database_enforces_one_approved_role_per_actor_and_cohort(tmp_path: Path) -> None:
    store = _seed_store(tmp_path / "foundation.db")

    with pytest.raises(sqlite3.IntegrityError):
        store.grant_membership(_membership(ACTOR_IDS["student"], CohortRole.TEACHER))
    store.close()


def test_new_membership_and_namespace_ownership_require_active_cohort_state(
    tmp_path: Path,
) -> None:
    database = tmp_path / "foundation.db"
    store = _seed_store(database)

    with pytest.raises(ValueError, match="active at revision 1"):
        store.grant_membership(
            _membership(
                ACTOR_IDS["other-student"],
                CohortRole.STUDENT,
                cohort_id=OTHER_COHORT_ID,
                active=False,
            )
        )

    raw = sqlite3.connect(database, isolation_level=None)
    raw.execute(
        """
        UPDATE cohort_memberships SET active = 0, revision = revision + 1
        WHERE cohort_id = ? AND actor_id = ?
        """,
        (COHORT_ID, ACTOR_IDS["teacher"]),
    )
    raw.close()
    with pytest.raises(PersistenceAuthorizationError, match="active cohort member"):
        store.create_namespace(
            PackageNamespace("inactive-owner", COHORT_ID, ACTOR_IDS["teacher"], NOW)
        )
    store.close()


def test_only_course_admin_can_assign_membership_or_namespace_grants(tmp_path: Path) -> None:
    store = _seed_store(tmp_path / "foundation.db")
    unauthorized_membership = CohortMembership(
        COHORT_ID,
        ACTOR_IDS["other-student"],
        CohortRole.TEACHER,
        ACTOR_IDS["student"],
        NOW,
    )

    with pytest.raises(PersistenceAuthorizationError, match="course-admin"):
        store.grant_membership(unauthorized_membership)
    with pytest.raises(PersistenceAuthorizationError, match="course-admin"):
        store.grant_membership(
            CohortMembership(
                OTHER_COHORT_ID,
                ACTOR_IDS["other-student"],
                CohortRole.STUDENT,
                ACTOR_IDS["student"],
                NOW,
            )
        )
    with pytest.raises(PersistenceAuthorizationError, match="course-admin"):
        store.grant_namespace(
            NamespaceGrant(
                PACKAGE_ID,
                COHORT_ID,
                ACTOR_IDS["teacher"],
                NamespacePermission.SUBMIT,
                ACTOR_IDS["student"],
                NOW,
            )
        )
    store.close()


def test_cohort_provisioning_requires_matching_initial_course_admin(tmp_path: Path) -> None:
    store = SQLiteFoundationStore.open(tmp_path / "foundation.db")
    store.initialize_schema()
    store.approve_identity_provider(IdentityProvider(ISSUER))
    for label in ACTOR_IDS:
        _bind_actor(store, label)
    cohort = Cohort(COHORT_ID, "Example School", NOW, COHORT_CLOSE)

    with pytest.raises(PersistenceAuthorizationError, match="initial membership"):
        store.create_cohort(
            cohort,
            _membership(ACTOR_IDS["student"], CohortRole.STUDENT),
        )
    store.create_cohort(
        cohort,
        _membership(ACTOR_IDS["course-admin"], CohortRole.COURSE_ADMIN),
    )
    store.close()


def test_membership_and_namespace_updates_require_next_optimistic_revision(
    tmp_path: Path,
) -> None:
    database = tmp_path / "foundation.db"
    store = _seed_store(database)
    raw = sqlite3.connect(database, isolation_level=None)
    raw.execute("PRAGMA foreign_keys = ON")

    with pytest.raises(sqlite3.IntegrityError, match="optimistic revision"):
        raw.execute(
            """
            UPDATE cohort_memberships SET active = 0
            WHERE cohort_id = ? AND actor_id = ?
            """,
            (COHORT_ID, ACTOR_IDS["student"]),
        )
    with pytest.raises(sqlite3.IntegrityError, match="optimistic revision"):
        raw.execute(
            "UPDATE package_namespaces SET owner_actor_id = ? WHERE package_id = ?",
            (ACTOR_IDS["teacher"], PACKAGE_ID),
        )

    raw.execute(
        """
        UPDATE package_namespaces SET owner_actor_id = ?, revision = revision + 1
        WHERE package_id = ? AND revision = 1
        """,
        (ACTOR_IDS["teacher"], PACKAGE_ID),
    )
    assert raw.execute(
        "SELECT owner_actor_id, revision FROM package_namespaces WHERE package_id = ?",
        (PACKAGE_ID,),
    ).fetchone() == (ACTOR_IDS["teacher"], 2)
    raw.close()
    store.close()


def test_persisted_principal_snapshot_contains_only_authoritative_scoped_grants(
    tmp_path: Path,
) -> None:
    store = _seed_store(tmp_path / "foundation.db")
    grant = NamespaceGrant(
        PACKAGE_ID,
        COHORT_ID,
        ACTOR_IDS["teacher"],
        NamespacePermission.SUBMIT,
        ACTOR_IDS["course-admin"],
        NOW,
    )
    store.grant_namespace(grant)

    principal = store.load_human_principal(ACTOR_IDS["teacher"], AssuranceLevel.AAL2)

    assert principal.memberships == (_membership(ACTOR_IDS["teacher"], CohortRole.TEACHER),)
    assert principal.namespace_grants == (grant,)
    assert authorize(principal, AuthorizationAction.SUBMIT, _resource()).allowed
    store.close()


def test_package_id_and_version_cannot_be_rebound_to_different_zip_bytes(tmp_path: Path) -> None:
    database = tmp_path / "foundation.db"
    store = _seed_store(database)
    package = StoredPackageVersion(
        VERSION_IDENTITY,
        COHORT_ID,
        ACTOR_IDS["student"],
        NOW,
    )

    assert store.record_package_version(package) == package
    assert store.record_package_version(package) == package
    conflicting = StoredPackageVersion(
        PackageVersionIdentity(PACKAGE_ID, "1.2.3", "b" * 64),
        COHORT_ID,
        ACTOR_IDS["student"],
        NOW,
    )
    with pytest.raises(PersistenceConflictError, match="different immutable bytes"):
        store.record_package_version(conflicting)

    raw = sqlite3.connect(database, isolation_level=None)
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        raw.execute(
            "UPDATE package_versions SET raw_zip_sha256 = ? WHERE package_id = ?",
            ("c" * 64, PACKAGE_ID),
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        raw.execute("DELETE FROM package_versions WHERE package_id = ?", (PACKAGE_ID,))
    raw.close()
    store.close()


def test_audit_events_are_append_only_and_operation_keys_are_unique(tmp_path: Path) -> None:
    database = tmp_path / "foundation.db"
    store = _seed_store(database)
    event = AuditEvent(
        event_id="00000000-0000-4000-8000-000000000101",
        occurred_at=NOW,
        retention_until=AUDIT_RETENTION,
        principal_kind=PrincipalKind.ACTOR,
        principal_id=ACTOR_IDS["course-admin"],
        event_type="namespace.created",
        object_type="package-namespace",
        object_id=PACKAGE_ID,
        cohort_id=COHORT_ID,
        idempotency_key="create-river-rescue",
        details_json='{"owner_actor_id":"00000000-0000-4000-8000-000000000001"}',
    )
    store.append_audit_event(event)

    with pytest.raises(sqlite3.IntegrityError):
        store.append_audit_event(
            AuditEvent(
                event_id="00000000-0000-4000-8000-000000000102",
                occurred_at=NOW,
                retention_until=AUDIT_RETENTION,
                principal_kind=PrincipalKind.ACTOR,
                principal_id=ACTOR_IDS["course-admin"],
                event_type=event.event_type,
                object_type=event.object_type,
                object_id="different-object",
                cohort_id=COHORT_ID,
                idempotency_key=event.idempotency_key,
                details_json="{}",
            )
        )

    raw = sqlite3.connect(database, isolation_level=None)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        raw.execute(
            "UPDATE audit_events SET details_json = '{}' WHERE event_id = ?", (event.event_id,)
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        raw.execute("DELETE FROM audit_events WHERE event_id = ?", (event.event_id,))
    raw.close()
    store.close()


def test_completed_idempotency_record_replays_and_rejects_key_reuse(tmp_path: Path) -> None:
    store = _seed_store(tmp_path / "foundation.db")
    record = IdempotencyRecord(
        PrincipalKind.ACTOR,
        ACTOR_IDS["student"],
        "package-version.record",
        "request-123",
        "d" * 64,
        "package:river-rescue@1.2.3",
        NOW,
    )

    assert store.record_idempotent_result(record) == record
    assert store.record_idempotent_result(record) == record
    with pytest.raises(IdempotencyConflictError, match="different request bytes"):
        store.record_idempotent_result(
            IdempotencyRecord(
                record.principal_kind,
                record.principal_id,
                record.operation,
                record.idempotency_key,
                "e" * 64,
                record.result_reference,
                NOW,
            )
        )
    store.close()


def test_mutation_audit_and_idempotency_can_commit_or_rollback_atomically(tmp_path: Path) -> None:
    database = tmp_path / "foundation.db"
    store = _seed_store(database)
    prior = IdempotencyRecord(
        PrincipalKind.ACTOR,
        ACTOR_IDS["student"],
        "package-version.record",
        "atomic-request",
        "d" * 64,
        "prior-result",
        NOW,
    )
    store.record_idempotent_result(prior)
    package = StoredPackageVersion(
        VERSION_IDENTITY,
        COHORT_ID,
        ACTOR_IDS["student"],
        NOW,
    )
    event = AuditEvent(
        "00000000-0000-4000-8000-000000000104",
        NOW,
        AUDIT_RETENTION,
        PrincipalKind.ACTOR,
        ACTOR_IDS["student"],
        "package-version.recorded",
        "package-version",
        "river-rescue@1.2.3",
        "atomic-request",
        "{}",
        COHORT_ID,
    )

    with pytest.raises(IdempotencyConflictError), store.transaction():
        store.record_package_version(package)
        store.append_audit_event(event)
        store.record_idempotent_result(
            IdempotencyRecord(
                prior.principal_kind,
                prior.principal_id,
                prior.operation,
                prior.idempotency_key,
                "e" * 64,
                "new-result",
                NOW,
            )
        )

    raw = sqlite3.connect(database)
    assert raw.execute("SELECT count(*) FROM package_versions").fetchone() == (0,)
    assert raw.execute("SELECT count(*) FROM audit_events").fetchone() == (0,)
    raw.close()
    store.close()


def test_audit_details_must_be_canonical_json_without_implicit_profile_data() -> None:
    values = {
        "event_id": "00000000-0000-4000-8000-000000000103",
        "occurred_at": NOW,
        "retention_until": AUDIT_RETENTION,
        "principal_kind": PrincipalKind.SERVICE,
        "principal_id": "class-world-builder",
        "event_type": "registry.read",
        "object_type": "package-version",
        "object_id": "river-rescue@1.2.3",
        "idempotency_key": "build-read-1",
    }

    with pytest.raises(ValueError, match="mutable profile data"):
        AuditEvent(**values, details_json='{"email":"student@example.edu"}')
    with pytest.raises(ValueError, match="canonical"):
        AuditEvent(**values, details_json='{ "safe": "value" }')
    assert AuditEvent(**values, details_json="{}").details_json == "{}"
