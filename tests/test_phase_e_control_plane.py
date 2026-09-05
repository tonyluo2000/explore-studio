"""Security, replay, atomicity, and concurrency tests for the Phase E control plane."""

from __future__ import annotations

import inspect
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

from explore.online import (
    Actor,
    AssuranceLevel,
    AuthenticatedOIDCIdentity,
    AuthorizationAction,
    AuthorizationResource,
    Cohort,
    CohortMembership,
    CohortRole,
    ControlPlaneAccessDeniedError,
    ControlPlaneAction,
    ControlPlaneConflictError,
    ControlPlaneService,
    IdentityProvider,
    MembershipChangeRequest,
    MembershipCreateRequest,
    MembershipRevokeRequest,
    NamespaceClaimRequest,
    NamespaceGrantRequest,
    NamespaceGrantRevokeRequest,
    NamespaceTransferRequest,
    PackageNamespace,
    PackageVersionIdentity,
    SQLiteControlPlaneStore,
    StoredPackageVersion,
    authorize,
    authorize_control_plane,
)

NOW = datetime(2026, 9, 5, 21, 0, tzinfo=UTC)
CREATED = datetime(2026, 9, 1, 14, 0, tzinfo=UTC)
CLOSES = datetime(2027, 6, 30, 23, 59, tzinfo=UTC)
ISSUER = "https://identity.example.edu"
COHORT_ID = "fall-explorers"
OTHER_COHORT_ID = "winter-explorers"
PACKAGE_ID = "nova-character"
OTHER_PACKAGE_ID = "winter-lantern"
ACTOR_IDS = {
    "student": "00000000-0000-4000-8000-000000000001",
    "teacher": "00000000-0000-4000-8000-000000000002",
    "admin": "00000000-0000-4000-8000-000000000003",
    "admin-two": "00000000-0000-4000-8000-000000000004",
    "new-student": "00000000-0000-4000-8000-000000000005",
    "other-admin": "00000000-0000-4000-8000-000000000006",
}
SUBJECTS = {name: f"provider-{name}" for name in ACTOR_IDS}


def _identity(
    name: str,
    *,
    assurance: AssuranceLevel | None = None,
) -> AuthenticatedOIDCIdentity:
    expected = AssuranceLevel.AAL1 if name in {"student", "new-student"} else AssuranceLevel.AAL2
    return AuthenticatedOIDCIdentity(ISSUER, SUBJECTS[name], assurance or expected)


def _membership(
    name: str,
    role: CohortRole,
    *,
    cohort_id: str = COHORT_ID,
    grantor: str = "admin",
) -> CohortMembership:
    return CohortMembership(
        cohort_id=cohort_id,
        actor_id=ACTOR_IDS[name],
        role=role,
        granted_by_actor_id=ACTOR_IDS[grantor],
        granted_at=CREATED,
    )


def _open_seeded_store(path: Path) -> SQLiteControlPlaneStore:
    store = SQLiteControlPlaneStore.open(path)
    store.initialize_schema()
    store.approve_identity_provider(IdentityProvider(ISSUER))
    for name, actor_id in ACTOR_IDS.items():
        store.bind_federated_actor(
            issuer=ISSUER,
            subject=SUBJECTS[name],
            proposed_actor=Actor(actor_id, CREATED),
        )
    store.create_cohort(
        Cohort(COHORT_ID, "Example Academy", CREATED, CLOSES),
        _membership("admin", CohortRole.COURSE_ADMIN),
    )
    store.grant_membership(_membership("admin-two", CohortRole.COURSE_ADMIN))
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
    store.create_namespace(
        PackageNamespace(
            OTHER_PACKAGE_ID,
            OTHER_COHORT_ID,
            ACTOR_IDS["other-admin"],
            CREATED,
        )
    )
    return store


@pytest.fixture
def store(tmp_path: Path) -> SQLiteControlPlaneStore:
    value = _open_seeded_store(tmp_path / "control-plane.sqlite3")
    yield value
    value.close()


def _service(store: SQLiteControlPlaneStore) -> ControlPlaneService:
    return ControlPlaneService(store, clock=lambda: NOW)


def _create_request(
    *,
    target: str = "new-student",
    role: CohortRole = CohortRole.STUDENT,
    key: str = "membership-create-new-student",
) -> MembershipCreateRequest:
    return MembershipCreateRequest(
        cohort_id=COHORT_ID,
        target_actor_id=ACTOR_IDS[target],
        role=role,
        expected_revision=0,
        correlation_id=f"correlation-{key}",
        idempotency_key=key,
    )


def test_control_plane_policy_denies_every_non_admin_case(
    store: SQLiteControlPlaneStore,
) -> None:
    admin = store.load_human_principal(ACTOR_IDS["admin"], AssuranceLevel.AAL2)
    teacher = store.load_human_principal(ACTOR_IDS["teacher"], AssuranceLevel.AAL2)
    low_assurance = store.load_human_principal(ACTOR_IDS["admin"], AssuranceLevel.AAL1)
    other_admin = store.load_human_principal(ACTOR_IDS["other-admin"], AssuranceLevel.AAL2)

    assert all(
        authorize_control_plane(admin, action, COHORT_ID).allowed for action in ControlPlaneAction
    )
    assert all(
        not authorize_control_plane(principal, action, COHORT_ID).allowed
        for principal in (teacher, low_assurance, other_admin)
        for action in ControlPlaneAction
    )


def test_membership_create_change_and_revoke_are_exact_audited_transitions(
    store: SQLiteControlPlaneStore,
) -> None:
    service = _service(store)
    created = service.create_membership(identity=_identity("admin"), request=_create_request())
    changed = service.change_membership(
        identity=_identity("admin"),
        request=MembershipChangeRequest(
            COHORT_ID,
            ACTOR_IDS["new-student"],
            CohortRole.TEACHER,
            1,
            "correlation-membership-change",
            "membership-change-new-student",
        ),
    )
    revoked = service.revoke_membership(
        identity=_identity("admin"),
        request=MembershipRevokeRequest(
            COHORT_ID,
            ACTOR_IDS["new-student"],
            2,
            "correlation-membership-revoke",
            "membership-revoke-new-student",
        ),
    )

    assert not created.replayed and not changed.replayed and not revoked.replayed
    membership = store.load_membership(COHORT_ID, ACTOR_IDS["new-student"])
    assert membership is not None
    assert (membership.role, membership.active, membership.revision) == (
        CohortRole.TEACHER,
        False,
        3,
    )
    rows = store._connection.execute("""
        SELECT event_type, details_json FROM audit_events
        WHERE event_type LIKE 'control-plane.%' ORDER BY occurred_at, event_type
        """).fetchall()  # noqa: SLF001 - persistence contract assertion
    assert len(rows) == 3
    details = json.loads(rows[0][1])
    assert details["authority"] == {
        "active": True,
        "actor_id": ACTOR_IDS["admin"],
        "assurance": "aal2",
        "granted_at": "2026-09-01T14:00:00Z",
        "granted_by_actor_id": ACTOR_IDS["admin"],
        "revision": 1,
        "role": "course-admin",
    }
    assert store._connection.execute(  # noqa: SLF001
        "SELECT count(*) FROM control_plane_transitions"
    ).fetchone() == (3,)


def test_namespace_claim_grant_revoke_and_regrant_are_revisioned(
    store: SQLiteControlPlaneStore,
) -> None:
    service = _service(store)
    service.claim_namespace(
        identity=_identity("admin"),
        request=NamespaceClaimRequest(
            COHORT_ID,
            "crystal-garden",
            ACTOR_IDS["student"],
            0,
            "correlation-claim",
            "claim-crystal-garden",
        ),
    )
    granted = service.grant_namespace(
        identity=_identity("admin"),
        request=NamespaceGrantRequest(
            "crystal-garden",
            ACTOR_IDS["teacher"],
            1,
            0,
            "correlation-grant",
            "grant-crystal-garden",
        ),
    )
    revoked = service.revoke_namespace_grant(
        identity=_identity("admin"),
        request=NamespaceGrantRevokeRequest(
            "crystal-garden",
            ACTOR_IDS["teacher"],
            1,
            1,
            "correlation-revoke-grant",
            "revoke-crystal-garden",
        ),
    )
    revoked_principal = store.load_human_principal(ACTOR_IDS["teacher"], AssuranceLevel.AAL2)
    resource = AuthorizationResource(
        COHORT_ID,
        package_id="crystal-garden",
        owner_actor_id=ACTOR_IDS["student"],
    )
    assert not authorize(
        revoked_principal,
        AuthorizationAction.SUBMIT,
        resource,
    ).allowed
    regranted = service.grant_namespace(
        identity=_identity("admin"),
        request=NamespaceGrantRequest(
            "crystal-garden",
            ACTOR_IDS["teacher"],
            1,
            2,
            "correlation-regrant",
            "regrant-crystal-garden",
        ),
    )

    assert json.loads(granted.transition.change_json)["after"] == {
        "active": True,
        "revision": 1,
    }
    assert json.loads(revoked.transition.change_json)["after"] == {
        "active": False,
        "revision": 2,
    }
    assert json.loads(regranted.transition.change_json)["after"] == {
        "active": True,
        "revision": 3,
    }
    state = store.load_namespace_grant_state("crystal-garden", ACTOR_IDS["teacher"])
    assert state is not None and state.active and state.revision == 3
    principal = store.load_human_principal(ACTOR_IDS["teacher"], AssuranceLevel.AAL2)
    assert [grant.package_id for grant in principal.namespace_grants] == ["crystal-garden"]
    assert authorize(principal, AuthorizationAction.SUBMIT, resource).allowed


def test_transfer_changes_only_current_owner_metadata_and_preserves_version_identity(
    store: SQLiteControlPlaneStore,
) -> None:
    package = StoredPackageVersion(
        PackageVersionIdentity(PACKAGE_ID, "1.0.0", "a" * 64),
        COHORT_ID,
        ACTOR_IDS["student"],
        CREATED,
    )
    store.record_package_version(package)

    receipt = _service(store).transfer_namespace(
        identity=_identity("admin"),
        request=NamespaceTransferRequest(
            PACKAGE_ID,
            ACTOR_IDS["teacher"],
            1,
            "correlation-transfer",
            "transfer-nova",
        ),
    )

    namespace = store.load_namespace(PACKAGE_ID)
    assert namespace is not None
    assert (namespace.owner_actor_id, namespace.revision) == (ACTOR_IDS["teacher"], 2)
    persisted = store._connection.execute(  # noqa: SLF001
        """
        SELECT package_id, package_version, raw_zip_sha256, cohort_id,
            created_by_actor_id, created_at
        FROM package_versions WHERE package_id = ? AND package_version = ?
        """,
        (PACKAGE_ID, "1.0.0"),
    ).fetchone()
    assert persisted == (
        PACKAGE_ID,
        "1.0.0",
        "a" * 64,
        COHORT_ID,
        ACTOR_IDS["student"],
        "2026-09-01T14:00:00.000000Z",
    )
    change = json.loads(receipt.transition.change_json)
    assert change["before"]["owner_actor_id"] == ACTOR_IDS["student"]
    assert change["after"]["owner_actor_id"] == ACTOR_IDS["teacher"]


@pytest.mark.parametrize(
    "identity",
    [
        _identity("student"),
        _identity("teacher"),
        _identity("admin", assurance=AssuranceLevel.AAL1),
    ],
)
def test_only_current_aal2_course_admin_can_assign_privileged_roles(
    store: SQLiteControlPlaneStore,
    identity: AuthenticatedOIDCIdentity,
) -> None:
    with pytest.raises(
        ControlPlaneAccessDeniedError,
        match="control-plane transition is not authorized",
    ):
        _service(store).create_membership(
            identity=identity,
            request=_create_request(role=CohortRole.COURSE_ADMIN),
        )

    assert store.load_membership(COHORT_ID, ACTOR_IDS["new-student"]) is None


def test_course_admin_cannot_rebind_own_authority_snapshot(
    store: SQLiteControlPlaneStore,
) -> None:
    with pytest.raises(ControlPlaneAccessDeniedError):
        _service(store).change_membership(
            identity=_identity("admin"),
            request=MembershipChangeRequest(
                COHORT_ID,
                ACTOR_IDS["admin"],
                CohortRole.TEACHER,
                1,
                "correlation-self-change",
                "self-change",
            ),
        )


def test_cross_cohort_and_unknown_namespaces_share_bola_safe_denial(
    store: SQLiteControlPlaneStore,
) -> None:
    service = _service(store)
    errors = []
    for package_id in (OTHER_PACKAGE_ID, "unknown-package"):
        with pytest.raises(ControlPlaneAccessDeniedError) as caught:
            service.transfer_namespace(
                identity=_identity("admin"),
                request=NamespaceTransferRequest(
                    package_id,
                    ACTOR_IDS["teacher"],
                    1,
                    "correlation-bola",
                    f"bola-{package_id}",
                ),
            )
        errors.append(str(caught.value))

    assert errors == ["control-plane transition is not authorized"] * 2


def test_stale_membership_namespace_and_grant_revisions_fail_closed(
    store: SQLiteControlPlaneStore,
) -> None:
    service = _service(store)
    with pytest.raises(ControlPlaneConflictError, match="expected active revision"):
        service.change_membership(
            identity=_identity("admin"),
            request=MembershipChangeRequest(
                COHORT_ID,
                ACTOR_IDS["student"],
                CohortRole.TEACHER,
                9,
                "correlation-stale-member",
                "stale-member",
            ),
        )
    with pytest.raises(ControlPlaneConflictError, match="transferable revision"):
        service.transfer_namespace(
            identity=_identity("admin"),
            request=NamespaceTransferRequest(
                PACKAGE_ID,
                ACTOR_IDS["teacher"],
                9,
                "correlation-stale-namespace",
                "stale-namespace",
            ),
        )
    with pytest.raises(ControlPlaneConflictError, match="namespace changed"):
        service.grant_namespace(
            identity=_identity("admin"),
            request=NamespaceGrantRequest(
                PACKAGE_ID,
                ACTOR_IDS["teacher"],
                9,
                0,
                "correlation-stale-grant",
                "stale-grant",
            ),
        )

    assert store._connection.execute(  # noqa: SLF001
        "SELECT count(*) FROM control_plane_transitions"
    ).fetchone() == (0,)


def test_identical_replay_converges_without_duplicate_transition_or_audit(
    store: SQLiteControlPlaneStore,
) -> None:
    service = _service(store)
    request = _create_request()
    first = service.create_membership(identity=_identity("admin"), request=request)
    replay = service.create_membership(identity=_identity("admin"), request=request)

    assert replay.replayed
    assert replay.transition == first.transition
    assert store._connection.execute(  # noqa: SLF001
        "SELECT count(*) FROM control_plane_transitions"
    ).fetchone() == (1,)
    assert store._connection.execute(  # noqa: SLF001
        "SELECT count(*) FROM audit_events WHERE event_type = 'control-plane.membership-create'"
    ).fetchone() == (1,)


def test_replay_rechecks_current_course_admin_authority(
    store: SQLiteControlPlaneStore,
) -> None:
    service = _service(store)
    request = _create_request()
    service.create_membership(identity=_identity("admin"), request=request)
    service.revoke_membership(
        identity=_identity("admin-two"),
        request=MembershipRevokeRequest(
            COHORT_ID,
            ACTOR_IDS["admin"],
            1,
            "correlation-revoke-admin",
            "revoke-admin",
        ),
    )

    with pytest.raises(ControlPlaneAccessDeniedError):
        service.create_membership(identity=_identity("admin"), request=request)


def test_changed_request_under_same_key_fails_without_second_mutation(
    store: SQLiteControlPlaneStore,
) -> None:
    service = _service(store)
    service.create_membership(identity=_identity("admin"), request=_create_request())

    with pytest.raises(ControlPlaneConflictError, match="idempotency key conflicts"):
        service.create_membership(
            identity=_identity("admin"),
            request=_create_request(role=CohortRole.TEACHER),
        )

    membership = store.load_membership(COHORT_ID, ACTOR_IDS["new-student"])
    assert membership is not None and membership.role is CohortRole.STUDENT


def test_concurrent_identical_membership_creation_converges(tmp_path: Path) -> None:
    database = tmp_path / "concurrent-identical.sqlite3"
    setup = _open_seeded_store(database)
    setup.close()
    request = _create_request()

    def create() -> tuple[str, bool]:
        local = SQLiteControlPlaneStore.open(database)
        receipt = _service(local).create_membership(
            identity=_identity("admin"),
            request=request,
        )
        local.close()
        return receipt.transition.transition_id, receipt.replayed

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: create(), range(2)))

    assert len({transition_id for transition_id, _replayed in results}) == 1
    assert sorted(replayed for _transition_id, replayed in results) == [False, True]
    connection = sqlite3.connect(database)
    assert connection.execute("SELECT count(*) FROM control_plane_transitions").fetchone() == (1,)
    assert connection.execute(
        "SELECT count(*) FROM audit_events WHERE event_type = 'control-plane.membership-create'"
    ).fetchone() == (1,)
    connection.close()


def test_concurrent_conflicting_transfers_commit_one_exact_revision(tmp_path: Path) -> None:
    database = tmp_path / "concurrent-transfer.sqlite3"
    setup = _open_seeded_store(database)
    setup.grant_membership(_membership("new-student", CohortRole.STUDENT))
    setup.close()

    def transfer(target: str) -> str:
        local = SQLiteControlPlaneStore.open(database)
        try:
            _service(local).transfer_namespace(
                identity=_identity("admin"),
                request=NamespaceTransferRequest(
                    PACKAGE_ID,
                    ACTOR_IDS[target],
                    1,
                    f"correlation-transfer-{target}",
                    f"transfer-{target}",
                ),
            )
            return "committed"
        except ControlPlaneConflictError:
            return "conflict"
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(transfer, ("teacher", "new-student")))

    assert sorted(outcomes) == ["committed", "conflict"]
    connection = sqlite3.connect(database)
    owner, revision = connection.execute(
        "SELECT owner_actor_id, revision FROM package_namespaces WHERE package_id = ?",
        (PACKAGE_ID,),
    ).fetchone()
    assert owner in {ACTOR_IDS["teacher"], ACTOR_IDS["new-student"]}
    assert revision == 2
    assert connection.execute(
        "SELECT count(*) FROM control_plane_transitions WHERE action = 'namespace-transfer'"
    ).fetchone() == (1,)
    connection.close()


def test_audit_failure_rolls_back_transition_state_and_idempotency(
    store: SQLiteControlPlaneStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_audit(_event: object) -> None:
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(store, "append_audit_event", fail_audit)

    with pytest.raises(RuntimeError, match="audit unavailable"):
        _service(store).create_membership(
            identity=_identity("admin"),
            request=_create_request(),
        )

    assert store.load_membership(COHORT_ID, ACTOR_IDS["new-student"]) is None
    assert store._connection.execute(  # noqa: SLF001
        "SELECT count(*) FROM control_plane_transitions"
    ).fetchone() == (0,)
    assert store._connection.execute(  # noqa: SLF001
        "SELECT count(*) FROM idempotency_records WHERE operation LIKE 'control-plane.%'"
    ).fetchone() == (0,)


def test_transition_and_grant_state_ledgers_are_append_only(
    store: SQLiteControlPlaneStore,
) -> None:
    service = _service(store)
    receipt = service.grant_namespace(
        identity=_identity("admin"),
        request=NamespaceGrantRequest(
            PACKAGE_ID,
            ACTOR_IDS["teacher"],
            1,
            0,
            "correlation-ledger",
            "grant-ledger",
        ),
    )

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store._connection.execute(  # noqa: SLF001
            "UPDATE control_plane_transitions SET change_json = '{}' WHERE transition_id = ?",
            (receipt.transition.transition_id,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        store._connection.execute(  # noqa: SLF001
            "DELETE FROM control_plane_transitions WHERE transition_id = ?",
            (receipt.transition.transition_id,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="next revision"):
        store._connection.execute(  # noqa: SLF001
            """
            UPDATE namespace_grant_states SET active = 0
            WHERE package_id = ? AND actor_id = ?
            """,
            (PACKAGE_ID, ACTOR_IDS["teacher"]),
        )


def test_actor_membership_and_namespace_identities_cannot_be_rebound_or_deleted(
    store: SQLiteControlPlaneStore,
) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="actor identities are immutable"):
        store._connection.execute(  # noqa: SLF001
            "UPDATE actors SET created_at = ? WHERE actor_id = ?",
            (NOW.isoformat().replace("+00:00", "Z"), ACTOR_IDS["new-student"]),
        )
    with pytest.raises(sqlite3.IntegrityError, match="actor identities are immutable"):
        store._connection.execute(  # noqa: SLF001
            "DELETE FROM actors WHERE actor_id = ?",
            (ACTOR_IDS["new-student"],),
        )
    with pytest.raises(sqlite3.IntegrityError, match="must be revoked"):
        store._connection.execute(  # noqa: SLF001
            "DELETE FROM cohort_memberships WHERE cohort_id = ? AND actor_id = ?",
            (COHORT_ID, ACTOR_IDS["teacher"]),
        )
    with pytest.raises(sqlite3.IntegrityError, match="namespace identities are immutable"):
        store._connection.execute(  # noqa: SLF001
            "DELETE FROM package_namespaces WHERE package_id = ?",
            (PACKAGE_ID,),
        )


def test_domain_api_accepts_intent_but_no_current_authority_claims() -> None:
    methods = (
        ControlPlaneService.create_membership,
        ControlPlaneService.change_membership,
        ControlPlaneService.revoke_membership,
        ControlPlaneService.claim_namespace,
        ControlPlaneService.grant_namespace,
        ControlPlaneService.revoke_namespace_grant,
        ControlPlaneService.transfer_namespace,
    )
    assert all(
        set(inspect.signature(method).parameters) == {"self", "identity", "request"}
        for method in methods
    )
    forbidden = {
        "assurance",
        "current_role",
        "current_owner_actor_id",
        "granted_by_actor_id",
        "membership_revision",
    }
    request_types = (
        MembershipCreateRequest,
        MembershipChangeRequest,
        MembershipRevokeRequest,
        NamespaceClaimRequest,
        NamespaceGrantRequest,
        NamespaceGrantRevokeRequest,
        NamespaceTransferRequest,
    )
    assert all(
        forbidden.isdisjoint(inspect.signature(request_type).parameters)
        for request_type in request_types
    )


def test_control_plane_does_not_cross_transport_or_execution_boundaries() -> None:
    from explore.online import control_plane as service_module
    from explore.online import control_plane_persistence as persistence_module

    source = (inspect.getsource(service_module) + inspect.getsource(persistence_module)).lower()
    forbidden = (
        "flask",
        "fastapi",
        "requests",
        "subprocess",
        "session",
        "csrf",
        "signing",
        "deployment",
        "moderation",
        "exec(",
        "eval(",
    )
    assert all(token not in source for token in forbidden)
