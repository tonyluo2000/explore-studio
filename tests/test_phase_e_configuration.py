"""Authoritative Class-World configuration persistence and loading tests."""

from __future__ import annotations

import hashlib
import inspect
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier
from uuid import UUID

import pytest

from explore.online import (
    AuditEvent,
    AuthoritativeClassWorldConfiguration,
    AuthoritativeClassWorldConfigurationService,
    ClassWorldPinningService,
    ConfigurationAccessDeniedError,
    ConfigurationConflictError,
    ConfigurationCreateRequest,
    ConfigurationIntegrityError,
    ConfigurationLoadRequest,
    PreparedClassWorldConfiguration,
    PrincipalKind,
    SQLiteClassWorldConfigurationStore,
    prepare_class_world_configuration,
)
from explore.packages import export_explorer_package, serialize_class_world_manifest
from tests.test_phase_e_pinning import (
    ACTOR_IDS,
    CLOSES,
    COHORT_ID,
    EXAMPLE_ROOT,
    NOW,
    _approved_submission,
    _configuration,
    _identity,
    _open_seeded_store,
    _publish,
    _request,
)


@pytest.fixture
def store(tmp_path: Path) -> SQLiteClassWorldConfigurationStore:
    value = _open_seeded_store(tmp_path / "configuration.sqlite3")
    yield value
    value.close()


@pytest.fixture
def archive(tmp_path: Path) -> bytes:
    destination = tmp_path / "nova-character-1.0.0.explorer-package.zip"
    result = export_explorer_package(EXAMPLE_ROOT.resolve(), destination.resolve())
    assert result.is_exported
    return destination.read_bytes()


def _service(
    store: SQLiteClassWorldConfigurationStore,
    *,
    uuid_factory=None,
) -> AuthoritativeClassWorldConfigurationService:
    options = {} if uuid_factory is None else {"uuid_factory": uuid_factory}
    return AuthoritativeClassWorldConfigurationService(store, clock=lambda: NOW, **options)


def _create(
    store: SQLiteClassWorldConfigurationStore,
    *,
    configuration=None,
    actor: str = "course-admin",
    key: str = "configuration-create",
    correlation_id: str = "configuration-create-correlation",
):
    selected = configuration or _configuration()
    return _service(store).create(
        identity=_identity(actor),
        prepared=prepare_class_world_configuration(selected),
        request=ConfigurationCreateRequest(0, correlation_id, key),
    )


def _load(
    store: SQLiteClassWorldConfigurationStore,
    locator: str,
    *,
    actor: str = "course-admin",
    key: str = "configuration-load",
    correlation_id: str = "configuration-load-correlation",
):
    return _service(store).load_for_pinning(
        identity=_identity(actor),
        request=ConfigurationLoadRequest(locator, correlation_id, key),
    )


def test_persists_server_canonical_bytes_and_reconstructs_exact_configuration(
    store: SQLiteClassWorldConfigurationStore,
    archive: bytes,
) -> None:
    _publish(store, archive)
    configuration = _configuration()
    canonical = serialize_class_world_manifest(configuration).encode("utf-8")

    created = _create(store, configuration=configuration)
    loaded = _load(store, created.record.locator)

    assert not created.replayed and not loaded.replayed
    assert created.record.identity == ("expedition-orion", "1.0.0")
    assert created.record.canonical_bytes == canonical
    assert created.record.configuration_sha256 == hashlib.sha256(canonical).hexdigest()
    assert created.record.cohort_id == COHORT_ID
    assert loaded.loaded.record == created.record
    assert serialize_class_world_manifest(loaded.loaded.configuration).encode("utf-8") == canonical
    assert loaded.loaded.configuration.package_set_plan != configuration.package_set_plan
    rebuilt_entry = loaded.loaded.configuration.package_set_plan.entries[0]
    assert rebuilt_entry.character.x == 430  # type: ignore[union-attr]
    assert rebuilt_entry.character.y == 270  # type: ignore[union-attr]
    assert store.load_configuration_record(created.record.locator) == created.record
    assert store._connection.execute(
        "SELECT count(*) FROM class_world_configurations"
    ).fetchone() == (1,)


def test_create_and_load_requests_cannot_supply_configuration_claims() -> None:
    assert set(inspect.signature(ConfigurationCreateRequest).parameters) == {
        "expected_revision",
        "correlation_id",
        "idempotency_key",
    }
    assert set(inspect.signature(ConfigurationLoadRequest).parameters) == {
        "locator",
        "correlation_id",
        "idempotency_key",
    }
    forbidden = {
        "class_world_id",
        "class_world_version",
        "configuration_sha256",
        "cohort_id",
        "student_api_version",
        "packages",
        "package_set_plan",
        "canonical_bytes",
        "content",
    }
    assert forbidden.isdisjoint(inspect.signature(ConfigurationCreateRequest).parameters)
    assert forbidden.isdisjoint(inspect.signature(ConfigurationLoadRequest).parameters)

    with pytest.raises(TypeError, match="trusted boundary"):
        PreparedClassWorldConfiguration(_configuration(), b"{}", "a" * 64, object())
    with pytest.raises(TypeError, match="only by the loader"):
        AuthoritativeClassWorldConfiguration(object(), _configuration(), object())


@pytest.mark.parametrize("value", ["latest", "1.x", "^1.0.0", "expedition-orion@1.0.0"])
def test_loader_rejects_latest_ranges_fallback_and_non_opaque_locators(value: str) -> None:
    with pytest.raises(ValueError, match="canonical UUID"):
        ConfigurationLoadRequest(value, "correlation", "key")


def test_configuration_creation_rejects_stale_or_mutating_revision_intent() -> None:
    with pytest.raises(ValueError, match="expected_revision 0"):
        ConfigurationCreateRequest(1, "correlation", "key")


def test_only_current_same_cohort_aal2_course_admin_can_create_or_load(
    store: SQLiteClassWorldConfigurationStore,
    archive: bytes,
) -> None:
    _publish(store, archive)
    prepared = prepare_class_world_configuration(_configuration())
    service = _service(store)
    for actor in ("student", "teacher", "other-admin"):
        with pytest.raises(ConfigurationAccessDeniedError, match="configuration is not available"):
            service.create(
                identity=_identity(actor),
                prepared=prepared,
                request=ConfigurationCreateRequest(0, f"create-{actor}", f"create-{actor}"),
            )
    created = _create(store)

    with pytest.raises(ConfigurationAccessDeniedError) as cross_cohort:
        _load(store, created.record.locator, actor="other-admin", key="cross-cohort-load")
    with pytest.raises(ConfigurationAccessDeniedError) as unknown:
        _load(
            store,
            "00000000-0000-4000-8000-000000000099",
            key="unknown-locator-load",
        )
    assert str(cross_cohort.value) == str(unknown.value) == "configuration is not available"


def test_matching_create_and_load_replays_are_idempotent_and_reauthorize(
    store: SQLiteClassWorldConfigurationStore,
    archive: bytes,
) -> None:
    _publish(store, archive)
    first = _create(store)
    replay = _create(store)
    loaded = _load(store, first.record.locator)
    load_replay = _load(store, first.record.locator)

    assert replay.replayed and replay.record == first.record
    assert load_replay.replayed and load_replay.loaded == loaded.loaded
    assert store._connection.execute(
        "SELECT count(*) FROM class_world_configurations"
    ).fetchone() == (1,)
    assert (
        store._connection.execute("""
        SELECT event_type, count(*) FROM audit_events
        WHERE event_type IN (
            'class-world.configuration-create', 'class-world.configuration-read'
        ) GROUP BY event_type ORDER BY event_type
        """).fetchall()
        == [
            ("class-world.configuration-create", 1),
            ("class-world.configuration-read", 1),
        ]
    )

    store._connection.execute(
        """
        UPDATE cohort_memberships SET active = 0, revision = 2
        WHERE cohort_id = ? AND actor_id = ?
        """,
        (COHORT_ID, ACTOR_IDS["course-admin"]),
    )
    with pytest.raises(ConfigurationAccessDeniedError):
        _load(store, first.record.locator)


def test_changed_idempotency_and_immutable_identity_rebinding_fail_closed(
    store: SQLiteClassWorldConfigurationStore,
    archive: bytes,
) -> None:
    _publish(store, archive)
    first = _create(store)
    with pytest.raises(ConfigurationConflictError, match="idempotency key"):
        _create(store, correlation_id="changed-correlation")

    changed = replace(_configuration(), display_name="Changed declaration")
    with pytest.raises(ConfigurationConflictError, match="different canonical bytes"):
        _create(store, configuration=changed, key="changed-configuration")
    assert store.load_configuration_record(first.record.locator) == first.record


def test_cross_cohort_package_source_rejects_configuration_atomically(
    store: SQLiteClassWorldConfigurationStore,
    archive: bytes,
) -> None:
    _publish(store, archive)
    cross_cohort = _configuration(cohort_id="winter-explorers")

    with pytest.raises(ConfigurationIntegrityError, match="cross-cohort"):
        _create(
            store,
            configuration=cross_cohort,
            actor="other-admin",
            key="cross-cohort-configuration",
        )
    assert store._connection.execute(
        "SELECT count(*) FROM class_world_configurations"
    ).fetchone() == (0,)
    assert store._connection.execute(
        "SELECT count(*) FROM class_world_configuration_bindings"
    ).fetchone() == (0,)


def test_configuration_bytes_and_package_artifact_tamper_fail_authoritative_load(
    store: SQLiteClassWorldConfigurationStore,
    archive: bytes,
) -> None:
    submission = _publish(store, archive)
    created = _create(store)

    store._connection.execute("DROP TRIGGER class_world_configurations_no_update")
    tampered = b"[" + created.record.canonical_bytes[1:]
    store._connection.execute(
        "UPDATE class_world_configurations SET canonical_bytes = ? WHERE locator = ?",
        (tampered, created.record.locator),
    )
    with pytest.raises(ConfigurationIntegrityError, match="digest mismatch"):
        _load(store, created.record.locator, key="tampered-configuration-load")
    with pytest.raises(ConfigurationConflictError, match="idempotency result conflicts"):
        _create(store)
    assert store._connection.execute(
        "SELECT count(*) FROM audit_events WHERE event_type = 'class-world.configuration-read'"
    ).fetchone() == (0,)

    store._connection.execute("DROP TRIGGER package_submissions_no_update")
    store._connection.execute(
        "UPDATE class_world_configurations SET canonical_bytes = ? WHERE locator = ?",
        (created.record.canonical_bytes, created.record.locator),
    )
    damaged_archive = b"X" + archive[1:]
    store._connection.execute(
        "UPDATE package_submissions SET archive_bytes = ? WHERE submission_id = ?",
        (damaged_archive, submission.submission_id),
    )
    with pytest.raises(ConfigurationIntegrityError, match="artifact digest mismatch"):
        _load(store, created.record.locator, key="tampered-artifact-load")


def test_configuration_records_and_bindings_are_immutable(
    store: SQLiteClassWorldConfigurationStore,
    archive: bytes,
) -> None:
    _publish(store, archive)
    record = _create(store).record

    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        store._connection.execute(
            "UPDATE class_world_configurations SET cohort_id = cohort_id WHERE locator = ?",
            (record.locator,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        store._connection.execute(
            "DELETE FROM class_world_configurations WHERE locator = ?",
            (record.locator,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        store._connection.execute(
            """
            UPDATE class_world_configuration_bindings
            SET configuration_sha256 = configuration_sha256
            WHERE class_world_id = ? AND class_world_version = ?
            """,
            record.identity,
        )


def test_audit_failure_rolls_back_configuration_binding_record_and_idempotency(
    store: SQLiteClassWorldConfigurationStore,
    archive: bytes,
) -> None:
    _publish(store, archive)
    duplicate = "00000000-0000-4000-8000-000000000099"
    locator = "00000000-0000-4000-8000-000000000098"
    store.append_audit_event(
        AuditEvent(
            event_id=duplicate,
            occurred_at=NOW,
            retention_until=CLOSES.replace(year=CLOSES.year + 2),
            principal_kind=PrincipalKind.ACTOR,
            principal_id=ACTOR_IDS["course-admin"],
            event_type="test.configuration-reserved",
            object_type="test",
            object_id="reserved",
            cohort_id=COHORT_ID,
            idempotency_key="reserved-configuration-audit",
            details_json="{}",
        )
    )
    values = iter((UUID(locator), UUID(duplicate)))
    service = _service(store, uuid_factory=lambda: next(values))

    with pytest.raises(sqlite3.IntegrityError):
        service.create(
            identity=_identity("course-admin"),
            prepared=prepare_class_world_configuration(_configuration()),
            request=ConfigurationCreateRequest(0, "failed-create", "failed-create"),
        )
    assert store._connection.execute(
        "SELECT count(*) FROM class_world_configurations"
    ).fetchone() == (0,)
    assert store._connection.execute(
        "SELECT count(*) FROM class_world_configuration_bindings"
    ).fetchone() == (0,)
    assert store._connection.execute("""
        SELECT count(*) FROM idempotency_records
        WHERE operation = 'class-world.configuration-create'
        """).fetchone() == (0,)


def test_concurrent_identical_creates_converge_atomically(
    tmp_path: Path,
    archive: bytes,
) -> None:
    database = tmp_path / "concurrent-configuration.sqlite3"
    seeded = _open_seeded_store(database)
    _publish(seeded, archive)
    seeded.close()
    barrier = Barrier(2)

    def create() -> tuple[str, bool]:
        local = SQLiteClassWorldConfigurationStore.open(database)
        try:
            barrier.wait()
            result = _create(local)
            return result.record.locator, result.replayed
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(lambda _: create(), range(2)))

    check = SQLiteClassWorldConfigurationStore.open(database)
    try:
        assert len({item[0] for item in results}) == 1
        assert sorted(item[1] for item in results) == [False, True]
        assert check._connection.execute(
            "SELECT count(*) FROM class_world_configurations"
        ).fetchone() == (1,)
        assert check._connection.execute("""
            SELECT count(*) FROM audit_events
            WHERE event_type = 'class-world.configuration-create'
            """).fetchone() == (1,)
    finally:
        check.close()


def test_concurrent_rebinding_attempts_commit_only_one_immutable_identity(
    tmp_path: Path,
    archive: bytes,
) -> None:
    database = tmp_path / "competing-configuration.sqlite3"
    seeded = _open_seeded_store(database)
    _publish(seeded, archive)
    seeded.close()
    barrier = Barrier(2)
    configurations = (
        _configuration(),
        replace(_configuration(), display_name="Competing immutable declaration"),
    )

    def create(index: int) -> str:
        local = SQLiteClassWorldConfigurationStore.open(database)
        try:
            barrier.wait()
            try:
                _create(
                    local,
                    configuration=configurations[index],
                    key=f"competing-create-{index}",
                    correlation_id=f"competing-correlation-{index}",
                )
            except ConfigurationConflictError:
                return "conflict"
            return "created"
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(create, range(2)))

    check = SQLiteClassWorldConfigurationStore.open(database)
    try:
        assert sorted(results) == ["conflict", "created"]
        assert check._connection.execute(
            "SELECT count(*) FROM class_world_configurations"
        ).fetchone() == (1,)
        assert check._connection.execute("""
            SELECT count(*) FROM audit_events
            WHERE event_type = 'class-world.configuration-create'
            """).fetchone() == (1,)
    finally:
        check.close()


def test_pinning_rejects_raw_configuration_and_accepts_only_authoritative_load(
    store: SQLiteClassWorldConfigurationStore,
    archive: bytes,
) -> None:
    _approved_submission(store, archive)
    raw = _configuration()
    service = ClassWorldPinningService(store, clock=lambda: NOW)
    with pytest.raises(TypeError, match="loaded by the server"):
        service.pin_exact(
            identity=_identity("course-admin"),
            configuration=raw,  # type: ignore[arg-type]
            request=_request(),
        )

    record = _create(store).record
    loaded = _load(store, record.locator).loaded
    pin = service.pin_exact(
        identity=_identity("course-admin"),
        configuration=loaded,
        request=_request(),
    ).pin
    assert pin.configuration_identity == record.identity
    assert pin.configuration_sha256 == record.configuration_sha256


def test_configuration_audit_contains_exact_identity_digest_scope_and_purpose(
    store: SQLiteClassWorldConfigurationStore,
    archive: bytes,
) -> None:
    _publish(store, archive)
    record = _create(store).record
    _load(store, record.locator)
    rows = store._connection.execute("""
        SELECT event_type, object_id, cohort_id, details_json
        FROM audit_events
        WHERE event_type LIKE 'class-world.configuration-%'
        ORDER BY event_type
        """).fetchall()

    assert len(rows) == 2
    for event_type, object_id, cohort_id, details_json in rows:
        details = json.loads(details_json)
        assert object_id == record.locator
        assert cohort_id == record.cohort_id
        assert details["class_world_id"] == record.class_world_id
        assert details["class_world_version"] == record.class_world_version
        assert details["configuration_sha256"] == record.configuration_sha256
        assert details["locator"] == record.locator
        expected = "pinning" if event_type.endswith("read") else "configuration-create"
        assert details["purpose"] == expected


def test_configuration_slice_does_not_cross_transport_or_build_boundaries() -> None:
    from explore.online import configuration as service_module
    from explore.online import configuration_persistence as persistence_module

    source = (inspect.getsource(service_module) + inspect.getsource(persistence_module)).lower()
    forbidden = (
        "flask",
        "fastapi",
        "requests",
        "session",
        "csrf",
        "apply_package_set",
        "signing",
        "deployment",
        "moderation",
        "exec(",
        "eval(",
    )
    assert all(token not in source for token in forbidden)
