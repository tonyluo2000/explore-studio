"""Synthetic-only staff pilot configuration, operations, and staging E2E tests."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from starlette.testclient import TestClient

from explore.online import (
    Actor,
    AssuranceLevel,
    AuthenticatedOIDCIdentity,
    AuthoritativeClassWorldConfigurationService,
    Cohort,
    CohortMembership,
    CohortRole,
    ConfigurationCreateRequest,
    IdentityProvider,
    PackageNamespace,
    prepare_class_world_configuration,
)
from explore.online.oidc import OIDCAuthenticationError, OIDCRemote
from explore.online.pilot import StaffPilotRuntime, create_staff_pilot_runtime
from explore.online.pilot_config import (
    EnvironmentSecretLoader,
    LoadedSecret,
    PilotDatastoreConfig,
    PilotJWKSCacheConfig,
    PilotMaintenanceConfig,
    PilotOIDCProviderConfig,
    PilotTLSMode,
    PilotTransportTrustConfig,
    StaffPilotConfig,
)
from explore.online.pilot_datastore import (
    PilotDatastoreUnavailableError,
    bootstrap_synthetic_pilot_datastore,
)
from explore.online.pilot_operations import CachingOIDCRemote, PilotObserver
from explore.packages import export_explorer_package
from tests.test_phase_e_pinning import (
    ACTOR_IDS,
    CLOSES,
    COHORT_ID,
    CREATED,
    EXAMPLE_ROOT,
    ISSUER,
    OTHER_COHORT_ID,
    PACKAGE_ID,
    SUBJECTS,
    _approved_submission,
    _configuration,
)
from tests.test_phase_e_staff_transport import (
    NOW,
    ORIGIN,
    OTHER_PRIVATE_KEY,
    FakeOIDCRemote,
    _jwk,
)

SECRET_NAME = "EXPLORE_STAFF_SECRET_EXAMPLE_OIDC"
SECRET_VALUE = "synthetic-pilot-client-secret"


def _pilot_config(
    path: Path,
    *,
    tls_mode: PilotTLSMode = PilotTLSMode.DIRECT,
    proxy_networks: tuple[str, ...] = (),
) -> StaffPilotConfig:
    return StaffPilotConfig(
        providers=(
            PilotOIDCProviderConfig(
                provider_id="example",
                issuer=ISSUER,
                authorization_endpoint=f"{ISSUER}/authorize",
                token_endpoint=f"{ISSUER}/token",
                jwks_uri=f"{ISSUER}/jwks",
                client_id="explore-staff",
                client_secret_reference=f"env:{SECRET_NAME}",
                redirect_uri=f"{ORIGIN}/staff/oidc/callback/example",
                aal2_acr_values=frozenset({"urn:example:aal2"}),
            ),
        ),
        trust=PilotTransportTrustConfig(
            public_origin=ORIGIN,
            mode=tls_mode,
            trusted_proxy_networks=proxy_networks,
        ),
        datastore=PilotDatastoreConfig(
            path=path,
            environment_id="staff-pilot-staging",
        ),
        maintenance=PilotMaintenanceConfig(
            cleanup_interval=timedelta(seconds=10),
            readiness_max_staleness=timedelta(seconds=30),
        ),
        jwks_cache=PilotJWKSCacheConfig(
            fresh_ttl=timedelta(seconds=10),
            stale_if_error_ttl=timedelta(seconds=20),
        ),
        session_idle_ttl=timedelta(minutes=15),
        session_absolute_ttl=timedelta(hours=1),
        max_request_bytes=1024,
    )


def _seed_synthetic_store(runtime: StaffPilotRuntime) -> None:
    store = runtime.datastore.store
    store.approve_identity_provider(IdentityProvider(ISSUER))
    for name, actor_id in ACTOR_IDS.items():
        store.bind_federated_actor(
            issuer=ISSUER,
            subject=SUBJECTS[name],
            proposed_actor=Actor(actor_id, CREATED),
        )
    admin = CohortMembership(
        COHORT_ID,
        ACTOR_IDS["course-admin"],
        CohortRole.COURSE_ADMIN,
        ACTOR_IDS["course-admin"],
        CREATED,
    )
    store.create_cohort(Cohort(COHORT_ID, "Synthetic Academy", CREATED, CLOSES), admin)
    store.grant_membership(
        CohortMembership(
            COHORT_ID,
            ACTOR_IDS["student"],
            CohortRole.STUDENT,
            ACTOR_IDS["course-admin"],
            CREATED,
        )
    )
    store.grant_membership(
        CohortMembership(
            COHORT_ID,
            ACTOR_IDS["teacher"],
            CohortRole.TEACHER,
            ACTOR_IDS["course-admin"],
            CREATED,
        )
    )
    other_admin = CohortMembership(
        OTHER_COHORT_ID,
        ACTOR_IDS["other-admin"],
        CohortRole.COURSE_ADMIN,
        ACTOR_IDS["other-admin"],
        CREATED,
    )
    store.create_cohort(
        Cohort(OTHER_COHORT_ID, "Other Synthetic Academy", CREATED, CLOSES),
        other_admin,
    )
    store.create_namespace(PackageNamespace(PACKAGE_ID, COHORT_ID, ACTOR_IDS["student"], CREATED))


@dataclass
class PilotHarness:
    runtime: StaffPilotRuntime
    client: TestClient
    remote: FakeOIDCRemote
    current_time: list
    monotonic: list[float]

    def login(self) -> tuple[str, object]:
        started = self.client.get("/staff/oidc/login/example", follow_redirects=False)
        assert started.status_code == 302
        query = parse_qs(urlsplit(started.headers["location"]).query)
        self.remote.nonce = query["nonce"][0]
        self.remote.expected_challenge = query["code_challenge"][0]
        response = self.client.get(
            "/staff/oidc/callback/example",
            params={"code": "one-time-code", "state": query["state"][0]},
        )
        return response.json().get("data", {}).get("csrf_token"), response

    @staticmethod
    def headers(csrf: str, key: str) -> dict[str, str]:
        return {
            "Idempotency-Key": key,
            "Origin": ORIGIN,
            "X-Correlation-ID": f"correlation-{key}",
            "X-CSRF-Token": csrf,
        }


@pytest.fixture
def pilot_harness(tmp_path: Path) -> PilotHarness:
    current_time = [NOW]
    monotonic = [100.0]
    remote = FakeOIDCRemote()
    runtime = create_staff_pilot_runtime(
        _pilot_config(tmp_path / "staff-pilot.sqlite3"),
        EnvironmentSecretLoader({SECRET_NAME: SECRET_VALUE}),
        oidc_remote=remote,
        clock=lambda: current_time[0],
        monotonic=lambda: monotonic[0],
    )
    _seed_synthetic_store(runtime)
    with TestClient(runtime.app, base_url=ORIGIN) as client:
        yield PilotHarness(runtime, client, remote, current_time, monotonic)
    runtime.close()


@pytest.fixture
def pilot_archive(tmp_path: Path) -> bytes:
    destination = tmp_path / "nova-character-1.0.0.explorer-package.zip"
    result = export_explorer_package(EXAMPLE_ROOT.resolve(), destination.resolve())
    assert result.is_exported
    return destination.read_bytes()


def _seed_approved_configuration(harness: PilotHarness, archive: bytes) -> str:
    store = harness.runtime.datastore.store
    _approved_submission(store, archive)
    created = AuthoritativeClassWorldConfigurationService(store, clock=lambda: NOW).create(
        identity=AuthenticatedOIDCIdentity(
            ISSUER,
            SUBJECTS["course-admin"],
            AssuranceLevel.AAL2,
        ),
        prepared=prepare_class_world_configuration(_configuration()),
        request=ConfigurationCreateRequest(0, "pilot-seed-config", "pilot-seed-config"),
    )
    return created.record.locator


def test_staff_only_staging_e2e_composes_entire_pilot_boundary(
    pilot_harness: PilotHarness,
    pilot_archive: bytes,
) -> None:
    locator = _seed_approved_configuration(pilot_harness, pilot_archive)
    client = pilot_harness.client

    assert client.get("/health/live").json() == {"status": "ok"}
    readiness = client.get("/health/ready")
    assert readiness.status_code == 200
    assert readiness.json() == {"status": "ready"}

    csrf, login = pilot_harness.login()
    assert login.status_code == 200
    assert client.get("/staff/session").status_code == 200

    request = {
        "cohort_id": COHORT_ID,
        "expected_revision": 0,
        "owner_actor_id": ACTOR_IDS["teacher"],
        "package_id": "pilot-staff-world",
    }
    denied = client.post(
        "/staff/control-plane/namespaces",
        headers=pilot_harness.headers("wrong-token", "csrf-denied"),
        json=request,
    )
    created = client.post(
        "/staff/control-plane/namespaces",
        headers=pilot_harness.headers(csrf, "namespace-create"),
        json=request,
    )
    registry = client.get(
        f"/staff/registry/{PACKAGE_ID}/1.0.0",
        headers={
            "Idempotency-Key": "registry-exact",
            "X-Correlation-ID": "correlation-registry-exact",
        },
    )
    pin = client.post(
        "/staff/pins",
        headers=pilot_harness.headers(csrf, "pin-exact"),
        json={
            "configuration_locator": locator,
            "package_id": PACKAGE_ID,
            "semantic_version": "1.0.0",
        },
    )

    assert denied.status_code == 403
    assert created.status_code == 200
    assert registry.status_code == 200
    assert pin.status_code == 200
    assert pin.json()["data"]["configuration_sha256"]
    store = pilot_harness.runtime.datastore.store
    assert store._connection.execute(
        "SELECT count(*) FROM audit_events WHERE event_type = 'class-world.configuration-read'"
    ).fetchone() == (1,)
    assert client.get("/staff/registry").status_code == 404
    assert (
        client.post(
            "/staff/submissions", headers=pilot_harness.headers(csrf, "no-submission")
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/staff/configurations", headers=pilot_harness.headers(csrf, "no-authoring")
        ).status_code
        == 404
    )

    logout = client.post("/staff/logout", headers=pilot_harness.headers(csrf, "logout"))
    assert logout.status_code == 200
    assert client.get("/staff/session").status_code == 401


def test_configuration_uses_secret_references_and_never_prints_credentials(tmp_path: Path) -> None:
    config = _pilot_config(tmp_path / "staff-pilot.sqlite3")
    loader = EnvironmentSecretLoader({SECRET_NAME: SECRET_VALUE})
    resolved = config.resolve_transport(loader)

    assert resolved.providers[0].client_secret == SECRET_VALUE
    assert SECRET_VALUE not in repr(config)
    assert SECRET_VALUE not in repr(LoadedSecret(SECRET_VALUE))
    with pytest.raises(RuntimeError, match="unavailable"):
        config.resolve_transport(EnvironmentSecretLoader({}))
    with pytest.raises(ValueError, match="approved environment namespace"):
        EnvironmentSecretLoader({}).load("file:/tmp/client-secret")


def test_pilot_configuration_rejects_unsafe_origin_proxy_and_datastore_modes(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="HTTPS origin"):
        PilotTransportTrustConfig("http://studio.example", PilotTLSMode.DIRECT)
    with pytest.raises(ValueError, match="requires at least one"):
        PilotTransportTrustConfig(ORIGIN, PilotTLSMode.TRUSTED_PROXY)
    with pytest.raises(ValueError, match="immutable tuple"):
        PilotTransportTrustConfig(  # type: ignore[arg-type]
            ORIGIN,
            PilotTLSMode.TRUSTED_PROXY,
            ["10.20.30.0/24"],
        )
    with pytest.raises(ValueError, match="narrowly scoped"):
        PilotTransportTrustConfig(
            ORIGIN,
            PilotTLSMode.TRUSTED_PROXY,
            ("0.0.0.0/0",),
        )
    with pytest.raises(ValueError, match="exactly one"):
        PilotDatastoreConfig(
            tmp_path / "pilot.sqlite3",
            "pilot",
            worker_count=2,
        )
    with pytest.raises(ValueError, match="synthetic-only"):
        PilotDatastoreConfig(
            tmp_path / "pilot.sqlite3",
            "pilot",
            synthetic_only=False,
        )


def test_direct_tls_rejects_forwarded_metadata_and_wrong_host(
    pilot_harness: PilotHarness,
) -> None:
    forwarded = pilot_harness.client.get(
        "/health/live",
        headers={"X-Forwarded-Host": "studio.example", "X-Forwarded-Proto": "https"},
    )
    wrong_host = pilot_harness.client.get(
        "/health/live",
        headers={"Host": "attacker.example"},
    )

    assert forwarded.status_code == wrong_host.status_code == 400
    assert forwarded.json() == wrong_host.json() == {"error": {"code": "INVALID_REQUEST"}}


def test_readiness_fails_closed_until_configured_issuer_is_approved(tmp_path: Path) -> None:
    runtime = create_staff_pilot_runtime(
        _pilot_config(tmp_path / "unseeded-pilot.sqlite3"),
        EnvironmentSecretLoader({SECRET_NAME: SECRET_VALUE}),
        oidc_remote=FakeOIDCRemote(),
        clock=lambda: NOW,
    )
    try:
        with TestClient(runtime.app, base_url=ORIGIN) as client:
            response = client.get("/health/ready")
            assert response.status_code == 503
            assert response.json() == {"status": "unavailable"}
    finally:
        runtime.close()


def test_trusted_proxy_metadata_requires_exact_source_scheme_and_host(tmp_path: Path) -> None:
    runtime = create_staff_pilot_runtime(
        _pilot_config(
            tmp_path / "proxy-pilot.sqlite3",
            tls_mode=PilotTLSMode.TRUSTED_PROXY,
            proxy_networks=("10.20.30.0/24",),
        ),
        EnvironmentSecretLoader({SECRET_NAME: SECRET_VALUE}),
        oidc_remote=FakeOIDCRemote(),
        clock=lambda: NOW,
    )
    try:
        scope = {
            "type": "http",
            "scheme": "http",
            "client": ("10.20.30.4", 1234),
            "headers": [
                (b"host", b"studio.example"),
                (b"x-forwarded-host", b"studio.example"),
                (b"x-forwarded-proto", b"https"),
            ],
        }
        trusted = runtime.app._trusted_http_scope(scope)
        assert trusted is not None and trusted["scheme"] == "https"
        assert trusted["headers"] == [(b"host", b"studio.example")]
        assert runtime.app._trusted_http_scope({**scope, "client": ("10.20.31.4", 1234)}) is None
        assert (
            runtime.app._trusted_http_scope(
                {
                    **scope,
                    "headers": [
                        (b"host", b"studio.example"),
                        (b"x-forwarded-host", b"studio.example"),
                        (b"x-forwarded-proto", b"http"),
                    ],
                }
            )
            is None
        )
    finally:
        runtime.close()


def test_datastore_is_classified_private_and_process_exclusive(tmp_path: Path) -> None:
    config = PilotDatastoreConfig(tmp_path / "pilot.sqlite3", "pilot-test")
    datastore = bootstrap_synthetic_pilot_datastore(config, clock=lambda: NOW)
    try:
        assert datastore.is_ready()
        assert config.path.stat().st_mode & 0o777 == 0o600
        assert datastore.store._connection.execute("""
            SELECT environment_id, data_classification
            FROM staff_pilot_datastore_metadata WHERE singleton = 1
            """).fetchone() == ("pilot-test", "synthetic-non-minor")
        with pytest.raises(PilotDatastoreUnavailableError, match="already in use"):
            bootstrap_synthetic_pilot_datastore(config, clock=lambda: NOW)
    finally:
        datastore.close()

    reopened = bootstrap_synthetic_pilot_datastore(config, clock=lambda: NOW)
    reopened.close()


def test_datastore_refuses_to_adopt_an_unclassified_existing_database(tmp_path: Path) -> None:
    path = tmp_path / "existing.sqlite3"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE unrelated (value TEXT)")
    connection.close()

    with pytest.raises(PilotDatastoreUnavailableError, match="not an isolated synthetic"):
        bootstrap_synthetic_pilot_datastore(
            PilotDatastoreConfig(path, "pilot-test"),
            clock=lambda: NOW,
        )


class SequencedJWKSRemote(OIDCRemote):
    def __init__(self, responses: list[dict[str, object] | Exception]) -> None:
        self.responses = responses
        self.fetches = 0

    def exchange_code(self, provider, *, code: str, code_verifier: str) -> dict[str, object]:
        raise AssertionError("token exchange is not used in this cache test")

    def fetch_jwks(self, provider) -> dict[str, object]:
        response = self.responses[self.fetches]
        self.fetches += 1
        if isinstance(response, Exception):
            raise response
        return response


class RotatingFakeOIDCRemote(FakeOIDCRemote):
    def __init__(self) -> None:
        super().__init__()
        self.private_key = OTHER_PRIVATE_KEY
        self.key_id = "rotated-key"
        self._jwks = [
            {"keys": [_jwk()]},
            {"keys": [_jwk(OTHER_PRIVATE_KEY, key_id="rotated-key")]},
        ]
        self.fetches = 0

    def fetch_jwks(self, provider) -> dict[str, object]:
        document = self._jwks[min(self.fetches, len(self._jwks) - 1)]
        self.fetches += 1
        return document


def test_jwks_cache_handles_hits_rotation_and_bounded_outage(tmp_path: Path) -> None:
    provider = (
        _pilot_config(tmp_path / "pilot.sqlite3")
        .resolve_transport(EnvironmentSecretLoader({SECRET_NAME: SECRET_VALUE}))
        .providers[0]
    )
    first = {"keys": [{"kid": "first"}]}
    rotated = {"keys": [{"kid": "rotated"}]}
    remote = SequencedJWKSRemote(
        [
            first,
            rotated,
            OIDCAuthenticationError("outage"),
            OIDCAuthenticationError("outage"),
        ]
    )
    monotonic = [0.0]
    cache = CachingOIDCRemote(
        remote,
        PilotJWKSCacheConfig(timedelta(seconds=10), timedelta(seconds=20)),
        observer=PilotObserver(logging.getLogger("test.jwks")),
        monotonic=lambda: monotonic[0],
    )

    assert cache.fetch_jwks(provider) == first
    monotonic[0] = 5.0
    assert cache.fetch_jwks(provider) == first
    assert remote.fetches == 1
    assert cache.refresh_jwks(provider) == rotated
    monotonic[0] = 16.0
    assert cache.fetch_jwks(provider) == rotated
    monotonic[0] = 41.0
    with pytest.raises(OIDCAuthenticationError, match="outage"):
        cache.fetch_jwks(provider)


def test_unknown_signed_key_forces_one_jwks_rotation_refresh(tmp_path: Path) -> None:
    remote = RotatingFakeOIDCRemote()
    runtime = create_staff_pilot_runtime(
        _pilot_config(tmp_path / "rotation-pilot.sqlite3"),
        EnvironmentSecretLoader({SECRET_NAME: SECRET_VALUE}),
        oidc_remote=remote,
        clock=lambda: NOW,
    )
    _seed_synthetic_store(runtime)
    try:
        with TestClient(runtime.app, base_url=ORIGIN) as client:
            started = client.get("/staff/oidc/login/example", follow_redirects=False)
            query = parse_qs(urlsplit(started.headers["location"]).query)
            remote.nonce = query["nonce"][0]
            remote.expected_challenge = query["code_challenge"][0]
            response = client.get(
                "/staff/oidc/callback/example",
                params={"code": "one-time-code", "state": query["state"][0]},
            )
            assert response.status_code == 200
            assert remote.fetches == 2
    finally:
        runtime.close()


def test_maintenance_cleanup_revocation_and_readiness_are_effective(
    pilot_harness: PilotHarness,
) -> None:
    csrf, login = pilot_harness.login()
    assert login.status_code == 200
    pilot_harness.runtime.maintenance.revoke_issuer(ISSUER)
    assert pilot_harness.client.get("/staff/session").status_code == 401

    started = pilot_harness.client.get("/staff/oidc/login/example", follow_redirects=False)
    assert started.status_code == 302
    pilot_harness.current_time[0] = NOW + timedelta(minutes=6)
    assert pilot_harness.client.get("/health/ready").status_code == 503
    cleanup = pilot_harness.runtime.maintenance.run_cleanup()
    assert cleanup.expired_oidc_transactions == 1
    assert cleanup.inactive_sessions == 1
    assert pilot_harness.client.get("/health/ready").status_code == 200
    assert csrf


def test_maintenance_removes_idle_expired_session_material(
    pilot_harness: PilotHarness,
) -> None:
    _, login = pilot_harness.login()
    assert login.status_code == 200

    pilot_harness.current_time[0] = NOW + timedelta(minutes=16)
    cleanup = pilot_harness.runtime.maintenance.run_cleanup()

    assert cleanup.inactive_sessions == 1
    assert pilot_harness.client.get("/staff/session").status_code == 401


def test_health_and_observability_do_not_expose_sensitive_state(
    pilot_harness: PilotHarness,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="explore-studio.staff-pilot")
    csrf, login = pilot_harness.login()
    assert login.status_code == 200
    response = pilot_harness.client.get(
        "/health/ready",
        headers={"X-Correlation-ID": "operator-correlation"},
    )

    assert response.json() == {"status": "ready"}
    assert "Strict-Transport-Security" in response.headers
    rendered = "\n".join(record.getMessage() for record in caplog.records)
    assert SECRET_VALUE not in rendered
    assert SUBJECTS["course-admin"] not in rendered
    assert pilot_harness.client.cookies.get("__Host-explore-staff") not in rendered
    assert "operator-correlation" not in rendered
    assert csrf not in rendered
    assert pilot_harness.runtime.observer.metrics_snapshot()
