"""Staff-only OIDC, session, CSRF, HTTP, and sealed pin transport tests."""

from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import jwt
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
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
from explore.online.oidc import OIDCRemote
from explore.online.staff_transport import create_staff_transport_app
from explore.online.transport_models import StaffOIDCProvider, StaffTransportConfig
from explore.online.transport_persistence import SQLiteStaffTransportStore
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

NOW = datetime(2026, 9, 5, 20, 0, tzinfo=UTC)
ORIGIN = "https://studio.example"
PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
KEY_ID = "staff-test-key"


def _b64_integer(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _jwk(private_key=PRIVATE_KEY, *, key_id: str = KEY_ID) -> dict[str, object]:
    numbers = private_key.public_key().public_numbers()
    return {
        "alg": "RS256",
        "e": _b64_integer(numbers.e),
        "kid": key_id,
        "kty": "RSA",
        "n": _b64_integer(numbers.n),
        "use": "sig",
    }


def _b64url_bytes(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _signed_compact_token(payload_json: str) -> str:
    header = _b64url_bytes(
        json.dumps(
            {"alg": "RS256", "kid": KEY_ID, "typ": "JWT"},
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    )
    payload = _b64url_bytes(payload_json.encode())
    signed = f"{header}.{payload}".encode("ascii")
    signature = PRIVATE_KEY.sign(signed, padding.PKCS1v15(), hashes.SHA256())
    return f"{signed.decode('ascii')}.{_b64url_bytes(signature)}"


class FakeOIDCRemote(OIDCRemote):
    def __init__(self) -> None:
        self.nonce = ""
        self.subject = SUBJECTS["course-admin"]
        self.issuer = ISSUER
        self.audience: str | list[str] = "explore-staff"
        self.azp: str | None = None
        self.acr = "urn:example:aal2"
        self.amr: list[str] = ["pwd", "mfa"]
        self.expires_offset = 300
        self.issued_offset = 0
        self.auth_time_offset = 0
        self.private_key = PRIVATE_KEY
        self.key_id = KEY_ID
        self.jwks: dict[str, object] = {"keys": [_jwk()]}
        self.id_token_override: str | None = None
        self.expected_challenge = ""
        self.exchanges = 0

    def exchange_code(
        self,
        provider: StaffOIDCProvider,
        *,
        code: str,
        code_verifier: str,
    ) -> dict[str, object]:
        assert code == "one-time-code"
        actual_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("ascii")).digest())
            .rstrip(b"=")
            .decode("ascii")
        )
        assert actual_challenge == self.expected_challenge
        self.exchanges += 1
        now = int(NOW.timestamp())
        claims: dict[str, object] = {
            "acr": self.acr,
            "amr": self.amr,
            "auth_time": now + self.auth_time_offset,
            "aud": self.audience,
            "exp": now + self.expires_offset,
            "iat": now + self.issued_offset,
            "iss": self.issuer,
            "nonce": self.nonce,
            "sub": self.subject,
        }
        if self.azp is not None:
            claims["azp"] = self.azp
        encoded = self.id_token_override or jwt.encode(
            claims,
            self.private_key,
            algorithm="RS256",
            headers={"kid": self.key_id, "typ": "JWT"},
        )
        return {"access_token": "unused", "id_token": encoded, "token_type": "Bearer"}

    def fetch_jwks(self, provider: StaffOIDCProvider) -> dict[str, object]:
        return self.jwks


@dataclass
class Harness:
    store: SQLiteStaffTransportStore
    remote: FakeOIDCRemote
    client: TestClient
    config: StaffTransportConfig
    current_time: list[datetime]

    def login(self, *, subject: str | None = None) -> tuple[str, object]:
        if subject is not None:
            self.remote.subject = subject
        started = self.client.get("/staff/oidc/login/example", follow_redirects=False)
        assert started.status_code == 302
        query = parse_qs(urlsplit(started.headers["location"]).query)
        assert query["response_type"] == ["code"]
        assert query["scope"] == ["openid"]
        assert query["code_challenge_method"] == ["S256"]
        assert query["acr_values"] == ["urn:example:aal2"]
        assert query["max_age"] == ["0"]
        assert query["prompt"] == ["login"]
        self.remote.nonce = query["nonce"][0]
        self.remote.expected_challenge = query["code_challenge"][0]
        response = self.client.get(
            "/staff/oidc/callback/example",
            params={"code": "one-time-code", "state": query["state"][0]},
        )
        csrf = response.json().get("data", {}).get("csrf_token")
        return csrf, response

    @staticmethod
    def headers(csrf: str, *, key: str = "transport-operation") -> dict[str, str]:
        return {
            "Idempotency-Key": key,
            "Origin": ORIGIN,
            "X-Correlation-ID": f"correlation-{key}",
            "X-CSRF-Token": csrf,
        }


def _seed_store(path: Path) -> SQLiteStaffTransportStore:
    store = SQLiteStaffTransportStore.open(path)
    store.initialize_schema()
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
    store.create_cohort(Cohort(COHORT_ID, "Example Academy", CREATED, CLOSES), admin)
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
        Cohort(OTHER_COHORT_ID, "Example Academy", CREATED, CLOSES),
        other_admin,
    )
    store.create_namespace(PackageNamespace(PACKAGE_ID, COHORT_ID, ACTOR_IDS["student"], CREATED))
    return store


@pytest.fixture
def harness(tmp_path: Path) -> Harness:
    store = _seed_store(tmp_path / "staff-transport.sqlite3")
    provider = StaffOIDCProvider(
        provider_id="example",
        issuer=ISSUER,
        authorization_endpoint=f"{ISSUER}/authorize",
        token_endpoint=f"{ISSUER}/token",
        jwks_uri=f"{ISSUER}/jwks",
        client_id="explore-staff",
        client_secret="test-secret",
        redirect_uri=f"{ORIGIN}/staff/oidc/callback/example",
        aal2_acr_values=frozenset({"urn:example:aal2"}),
    )
    config = StaffTransportConfig(
        providers=(provider,),
        allowed_origin=ORIGIN,
        session_idle_ttl=timedelta(minutes=15),
        session_absolute_ttl=timedelta(hours=1),
        max_request_bytes=1024,
    )
    remote = FakeOIDCRemote()
    current_time = [NOW]
    app = create_staff_transport_app(store, config, remote, clock=lambda: current_time[0])
    with TestClient(app, base_url=ORIGIN) as client:
        yield Harness(store, remote, client, config, current_time)
    store.close()


@pytest.fixture
def archive(tmp_path: Path) -> bytes:
    destination = tmp_path / "nova-character-1.0.0.explorer-package.zip"
    result = export_explorer_package(EXAMPLE_ROOT.resolve(), destination.resolve())
    assert result.is_exported
    return destination.read_bytes()


def test_oidc_authorization_code_pkce_creates_secure_server_side_session(
    harness: Harness,
) -> None:
    csrf, response = harness.login()

    assert response.status_code == 200
    assert isinstance(csrf, str) and csrf
    assert response.json()["data"]["actor_id"] == ACTOR_IDS["course-admin"]
    assert response.json()["data"]["assurance"] == "aal2"
    cookies = response.headers.get_list("set-cookie")
    assert any(
        "__Host-explore-staff=" in cookie
        and "HttpOnly" in cookie
        and "Secure" in cookie
        and "SameSite=lax" in cookie
        and "Path=/" in cookie
        for cookie in cookies
    )
    assert any(
        "__Host-explore-csrf=" in cookie
        and "Secure" in cookie
        and "SameSite=strict" in cookie
        and "HttpOnly" not in cookie
        for cookie in cookies
    )
    status = harness.client.get("/staff/session")
    assert status.status_code == 200
    assert status.json()["data"]["actor_id"] == ACTOR_IDS["course-admin"]
    assert harness.store._connection.execute(
        "SELECT count(*), min(subject), min(assurance) FROM staff_sessions"
    ).fetchone() == (1, SUBJECTS["course-admin"], "aal2")
    session_cookie = harness.client.cookies[harness.config.session_cookie_name]
    assert harness.store._connection.execute(
        "SELECT session_digest FROM staff_sessions"
    ).fetchone() == (hashlib.sha256(session_cookie.encode("utf-8")).hexdigest(),)
    assert harness.store._connection.execute(
        "SELECT count(*) FROM oidc_authorization_transactions"
    ).fetchone() == (0,)


def test_oidc_provider_configuration_is_static_https_and_rs256_only() -> None:
    values = {
        "provider_id": "example",
        "issuer": ISSUER,
        "authorization_endpoint": f"{ISSUER}/authorize",
        "token_endpoint": f"{ISSUER}/token",
        "jwks_uri": f"{ISSUER}/jwks",
        "client_id": "explore-staff",
        "client_secret": "test-secret",
        "redirect_uri": f"{ORIGIN}/staff/oidc/callback/example",
        "aal2_acr_values": frozenset({"urn:example:aal2"}),
    }
    with pytest.raises(ValueError, match="HTTPS"):
        StaffOIDCProvider(**{**values, "issuer": "http://identity.example.edu"})
    with pytest.raises(ValueError, match="RS256"):
        StaffOIDCProvider(**values, signing_algorithms=("HS256",))


@pytest.mark.parametrize(
    "mutation",
    [
        "nonce",
        "issuer",
        "audience",
        "authorized-party",
        "multi-audience-no-authorized-party",
        "expired",
        "future-issued-at",
        "stale-auth",
        "signature",
        "kid",
    ],
)
def test_oidc_rejects_invalid_signed_claims_and_jwks(
    harness: Harness,
    mutation: str,
) -> None:
    started = harness.client.get("/staff/oidc/login/example", follow_redirects=False)
    query = parse_qs(urlsplit(started.headers["location"]).query)
    harness.remote.nonce = query["nonce"][0]
    harness.remote.expected_challenge = query["code_challenge"][0]
    if mutation == "nonce":
        harness.remote.nonce = "wrong-nonce"
    elif mutation == "issuer":
        harness.remote.issuer = "https://attacker.example"
    elif mutation == "audience":
        harness.remote.audience = "another-client"
    elif mutation == "authorized-party":
        harness.remote.azp = "another-client"
    elif mutation == "multi-audience-no-authorized-party":
        harness.remote.audience = ["explore-staff", "another-client"]
    elif mutation == "expired":
        harness.remote.expires_offset = -120
    elif mutation == "future-issued-at":
        harness.remote.issued_offset = 120
    elif mutation == "stale-auth":
        harness.remote.auth_time_offset = -3600
    elif mutation == "signature":
        harness.remote.private_key = OTHER_PRIVATE_KEY
    elif mutation == "kid":
        harness.remote.key_id = "unknown-key"

    response = harness.client.get(
        "/staff/oidc/callback/example",
        params={"code": "one-time-code", "state": query["state"][0]},
    )

    assert response.status_code == 401
    assert response.json() == {"error": {"code": "AUTHENTICATION_REQUIRED"}}
    assert harness.store._connection.execute("SELECT count(*) FROM staff_sessions").fetchone() == (
        0,
    )


def test_oidc_rejects_a_validly_signed_token_with_duplicate_claim_keys(
    harness: Harness,
) -> None:
    started = harness.client.get("/staff/oidc/login/example", follow_redirects=False)
    query = parse_qs(urlsplit(started.headers["location"]).query)
    harness.remote.nonce = query["nonce"][0]
    harness.remote.expected_challenge = query["code_challenge"][0]
    now = int(NOW.timestamp())
    subject_claim = f'"sub":"{SUBJECTS["course-admin"]}"'
    payload = json.dumps(
        {
            "acr": "urn:example:aal2",
            "amr": ["mfa"],
            "auth_time": now,
            "aud": "explore-staff",
            "exp": now + 300,
            "iat": now,
            "iss": ISSUER,
            "nonce": harness.remote.nonce,
            "sub": SUBJECTS["course-admin"],
        },
        separators=(",", ":"),
    ).replace(subject_claim, f"{subject_claim},{subject_claim}")
    harness.remote.id_token_override = _signed_compact_token(payload)

    response = harness.client.get(
        "/staff/oidc/callback/example",
        params={"code": "one-time-code", "state": query["state"][0]},
    )

    assert response.status_code == 401
    assert harness.store._connection.execute("SELECT count(*) FROM staff_sessions").fetchone() == (
        0,
    )


def test_state_browser_binding_nonce_and_callback_are_one_time(harness: Harness) -> None:
    started = harness.client.get("/staff/oidc/login/example", follow_redirects=False)
    query = parse_qs(urlsplit(started.headers["location"]).query)
    harness.remote.nonce = query["nonce"][0]
    harness.remote.expected_challenge = query["code_challenge"][0]

    wrong = harness.client.get(
        "/staff/oidc/callback/example",
        params={"code": "one-time-code", "state": "wrong-state"},
    )
    assert wrong.status_code == 401

    accepted = harness.client.get(
        "/staff/oidc/callback/example",
        params={"code": "one-time-code", "state": query["state"][0]},
    )
    replay = harness.client.get(
        "/staff/oidc/callback/example",
        params={"code": "one-time-code", "state": query["state"][0]},
    )
    assert accepted.status_code == 200
    assert replay.status_code == 401
    assert harness.remote.exchanges == 1


def test_expired_oidc_transaction_is_rejected_before_token_exchange(harness: Harness) -> None:
    started = harness.client.get("/staff/oidc/login/example", follow_redirects=False)
    query = parse_qs(urlsplit(started.headers["location"]).query)
    harness.remote.nonce = query["nonce"][0]
    harness.remote.expected_challenge = query["code_challenge"][0]
    harness.current_time[0] = NOW + harness.config.authorization_ttl + timedelta(seconds=1)

    response = harness.client.get(
        "/staff/oidc/callback/example",
        params={"code": "one-time-code", "state": query["state"][0]},
    )

    assert response.status_code == 401
    assert harness.remote.exchanges == 0
    assert harness.store._connection.execute(
        "SELECT count(*) FROM oidc_authorization_transactions"
    ).fetchone() == (0,)


def test_oidc_state_is_bound_to_the_secure_browser_cookie(harness: Harness) -> None:
    started = harness.client.get("/staff/oidc/login/example", follow_redirects=False)
    query = parse_qs(urlsplit(started.headers["location"]).query)
    harness.remote.nonce = query["nonce"][0]
    harness.remote.expected_challenge = query["code_challenge"][0]
    harness.client.cookies.set(harness.config.transaction_cookie_name, "wrong-browser")

    response = harness.client.get(
        "/staff/oidc/callback/example",
        params={"code": "one-time-code", "state": query["state"][0]},
    )

    assert response.status_code == 401
    assert harness.remote.exchanges == 0


def test_unbound_and_student_identities_cannot_create_staff_sessions(harness: Harness) -> None:
    _, student = harness.login(subject=SUBJECTS["student"])
    assert student.status_code == 401

    harness.remote.subject = "unknown-provider-subject"
    _, unknown = harness.login()
    assert unknown.status_code == 401
    assert harness.store.resolve_federated_actor(ISSUER, "unknown-provider-subject") is None


def test_aal1_session_cannot_use_privileged_routes(harness: Harness) -> None:
    harness.remote.acr = "urn:example:aal1"
    csrf, login = harness.login()
    assert login.status_code == 200
    assert login.json()["data"]["assurance"] == "aal1"

    response = harness.client.post(
        "/staff/control-plane/namespaces",
        headers=harness.headers(csrf),
        json={
            "cohort_id": COHORT_ID,
            "expected_revision": 0,
            "owner_actor_id": ACTOR_IDS["teacher"],
            "package_id": "aal1-denied",
        },
    )
    assert response.status_code == 401
    assert harness.store.load_namespace("aal1-denied") is None


def test_teacher_cannot_use_course_admin_control_plane_routes(harness: Harness) -> None:
    csrf, login = harness.login(subject=SUBJECTS["teacher"])
    assert login.status_code == 200
    response = harness.client.post(
        "/staff/control-plane/namespaces",
        headers=harness.headers(csrf, key="teacher-denied"),
        json={
            "cohort_id": COHORT_ID,
            "expected_revision": 0,
            "owner_actor_id": ACTOR_IDS["teacher"],
            "package_id": "teacher-denied",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"] == {"code": "RESOURCE_NOT_AVAILABLE"}
    assert harness.store.load_namespace("teacher-denied") is None


def test_control_plane_requires_session_origin_csrf_and_strict_schema(harness: Harness) -> None:
    csrf, login = harness.login()
    assert login.status_code == 200
    body = {
        "cohort_id": COHORT_ID,
        "expected_revision": 0,
        "owner_actor_id": ACTOR_IDS["teacher"],
        "package_id": "staff-world",
    }

    with TestClient(harness.client.app, base_url=ORIGIN) as anonymous:
        missing_session = anonymous.post(
            "/staff/control-plane/namespaces",
            headers=harness.headers(csrf),
            json=body,
        )
    bad_origin = harness.headers(csrf)
    bad_origin["Origin"] = "https://attacker.example"
    bad_csrf = harness.headers("wrong-token")
    extra = dict(body, cohort="caller-claimed")
    responses = (
        missing_session,
        harness.client.post("/staff/control-plane/namespaces", headers=bad_origin, json=body),
        harness.client.post("/staff/control-plane/namespaces", headers=bad_csrf, json=body),
        harness.client.post(
            "/staff/control-plane/namespaces",
            headers=harness.headers(csrf),
            json=extra,
        ),
    )

    assert [response.status_code for response in responses] == [401, 403, 403, 400]
    assert harness.store.load_namespace("staff-world") is None
    assert (
        harness.client.get(
            "/staff/oidc/login/example",
            headers={"Host": "attacker.example"},
            follow_redirects=False,
        ).status_code
        == 400
    )


def test_control_plane_transport_cannot_onboard_or_target_student_roles(
    harness: Harness,
) -> None:
    csrf, login = harness.login()
    assert login.status_code == 200
    student_membership = harness.client.post(
        "/staff/control-plane/memberships",
        headers=harness.headers(csrf, key="student-membership"),
        json={
            "cohort_id": COHORT_ID,
            "expected_revision": 0,
            "role": "student",
            "target_actor_id": ACTOR_IDS["other-admin"],
        },
    )
    student_namespace = harness.client.post(
        "/staff/control-plane/namespaces",
        headers=harness.headers(csrf, key="student-namespace"),
        json={
            "cohort_id": COHORT_ID,
            "expected_revision": 0,
            "owner_actor_id": ACTOR_IDS["student"],
            "package_id": "student-target-denied",
        },
    )

    assert student_membership.status_code == 400
    assert student_namespace.status_code == 404
    assert harness.store.load_namespace("student-target-denied") is None


def test_control_plane_endpoint_replay_and_concurrency_converge(harness: Harness) -> None:
    csrf, login = harness.login()
    assert login.status_code == 200
    body = {
        "cohort_id": COHORT_ID,
        "expected_revision": 0,
        "owner_actor_id": ACTOR_IDS["teacher"],
        "package_id": "staff-world",
    }
    headers = harness.headers(csrf, key="namespace-create")

    first = harness.client.post("/staff/control-plane/namespaces", headers=headers, json=body)
    replay = harness.client.post("/staff/control-plane/namespaces", headers=headers, json=body)
    assert first.status_code == replay.status_code == 200
    assert not first.json()["data"]["replayed"]
    assert replay.json()["data"]["replayed"]
    assert first.json()["data"]["transition_id"] == replay.json()["data"]["transition_id"]

    concurrent_body = dict(body, package_id="concurrent-world")
    concurrent_headers = harness.headers(csrf, key="concurrent-create")
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = tuple(
            executor.map(
                lambda _: harness.client.post(
                    "/staff/control-plane/namespaces",
                    headers=concurrent_headers,
                    json=concurrent_body,
                ),
                range(2),
            )
        )
    assert [response.status_code for response in responses] == [200, 200]
    assert len({response.json()["data"]["transition_id"] for response in responses}) == 1


def test_request_size_limit_fails_before_control_plane_mutation(harness: Harness) -> None:
    csrf, login = harness.login()
    assert login.status_code == 200
    response = harness.client.post(
        "/staff/control-plane/namespaces",
        headers={**harness.headers(csrf), "Content-Type": "application/json"},
        content=b"{" + b" " * 2048 + b"}",
    )
    assert response.status_code == 413


def _seed_approved_configuration(
    harness: Harness,
    archive: bytes,
) -> str:
    _approved_submission(harness.store, archive)
    created = AuthoritativeClassWorldConfigurationService(
        harness.store,
        clock=lambda: NOW,
    ).create(
        identity=AuthenticatedOIDCIdentity(
            ISSUER,
            SUBJECTS["course-admin"],
            AssuranceLevel.AAL2,
        ),
        prepared=prepare_class_world_configuration(_configuration()),
        request=ConfigurationCreateRequest(0, "seed-config", "seed-config"),
    )
    return created.record.locator


def test_registry_and_pin_transport_use_exact_authoritative_server_state(
    harness: Harness,
    archive: bytes,
) -> None:
    locator = _seed_approved_configuration(harness, archive)
    csrf, login = harness.login()
    assert login.status_code == 200

    registry = harness.client.get(
        f"/staff/registry/{PACKAGE_ID}/1.0.0",
        headers={
            "Idempotency-Key": "registry-read",
            "X-Correlation-ID": "registry-correlation",
        },
    )
    floating = harness.client.get(
        f"/staff/registry/{PACKAGE_ID}/latest",
        headers={
            "Idempotency-Key": "registry-floating",
            "X-Correlation-ID": "registry-floating-correlation",
        },
    )
    pin = harness.client.post(
        "/staff/pins",
        headers=harness.headers(csrf, key="pin-exact"),
        json={
            "configuration_locator": locator,
            "package_id": PACKAGE_ID,
            "semantic_version": "1.0.0",
        },
    )
    replay = harness.client.post(
        "/staff/pins",
        headers=harness.headers(csrf, key="pin-exact"),
        json={
            "configuration_locator": locator,
            "package_id": PACKAGE_ID,
            "semantic_version": "1.0.0",
        },
    )

    assert registry.status_code == 200
    assert floating.status_code == 400
    assert registry.json()["data"]["package_id"] == PACKAGE_ID
    assert pin.status_code == replay.status_code == 200
    assert pin.json()["data"]["pin_id"] == replay.json()["data"]["pin_id"]
    assert replay.json()["data"]["replayed"]
    assert harness.store._connection.execute(
        "SELECT count(*) FROM audit_events WHERE event_type = 'class-world.configuration-read'"
    ).fetchone() == (1,)
    assert harness.store._connection.execute(
        "SELECT count(*) FROM audit_events WHERE event_type = 'class-world.pin'"
    ).fetchone() == (1,)


def test_pin_request_rejects_all_trusted_configuration_claims(
    harness: Harness,
    archive: bytes,
) -> None:
    locator = _seed_approved_configuration(harness, archive)
    csrf, login = harness.login()
    assert login.status_code == 200
    base = {
        "configuration_locator": locator,
        "package_id": PACKAGE_ID,
        "semantic_version": "1.0.0",
    }
    forbidden = {
        "approval_decision_id": "00000000-0000-4000-8000-000000000099",
        "cohort_id": COHORT_ID,
        "configuration": {},
        "configuration_sha256": "0" * 64,
        "owner_actor_id": ACTOR_IDS["student"],
    }
    for name, value in forbidden.items():
        response = harness.client.post(
            "/staff/pins",
            headers=harness.headers(csrf, key=f"forbidden-{name}"),
            json={**base, name: value},
        )
        assert response.status_code == 400
    assert harness.store._connection.execute(
        "SELECT count(*) FROM class_world_package_pins"
    ).fetchone() == (0,)


def test_unknown_and_cross_cohort_registry_reads_are_bola_indistinguishable(
    harness: Harness,
    archive: bytes,
) -> None:
    _approved_submission(harness.store, archive)
    _, login = harness.login(subject=SUBJECTS["other-admin"])
    assert login.status_code == 200
    headers = {
        "Idempotency-Key": "known-denied",
        "X-Correlation-ID": "known-denied-correlation",
    }
    known = harness.client.get(f"/staff/registry/{PACKAGE_ID}/1.0.0", headers=headers)
    unknown = harness.client.get(
        "/staff/registry/unknown-package/1.0.0",
        headers={
            "Idempotency-Key": "unknown-denied",
            "X-Correlation-ID": "unknown-denied-correlation",
        },
    )
    assert known.status_code == unknown.status_code == 404
    assert known.json()["error"] == unknown.json()["error"] == {"code": "RESOURCE_NOT_AVAILABLE"}


def test_unknown_and_cross_cohort_configuration_locators_are_bola_indistinguishable(
    harness: Harness,
    archive: bytes,
) -> None:
    locator = _seed_approved_configuration(harness, archive)
    csrf, login = harness.login(subject=SUBJECTS["other-admin"])
    assert login.status_code == 200
    body = {"package_id": PACKAGE_ID, "semantic_version": "1.0.0"}
    known = harness.client.post(
        "/staff/pins",
        headers=harness.headers(csrf, key="known-locator-denied"),
        json={**body, "configuration_locator": locator},
    )
    unknown = harness.client.post(
        "/staff/pins",
        headers=harness.headers(csrf, key="unknown-locator-denied"),
        json={
            **body,
            "configuration_locator": "00000000-0000-4000-8000-000000000099",
        },
    )

    assert known.status_code == unknown.status_code == 404
    assert known.json()["error"] == unknown.json()["error"] == {"code": "RESOURCE_NOT_AVAILABLE"}


def test_logout_and_revocation_hooks_invalidate_sessions(harness: Harness) -> None:
    csrf, login = harness.login()
    assert login.status_code == 200
    logout = harness.client.post("/staff/logout", headers=harness.headers(csrf))
    assert logout.status_code == 200
    assert harness.client.get("/staff/session").status_code == 401

    _, second = harness.login()
    assert second.status_code == 200
    changed = harness.store.revoke_actor_sessions(
        actor_id=ACTOR_IDS["course-admin"],
        now=NOW + timedelta(seconds=1),
    )
    assert changed == 1
    assert harness.client.get("/staff/session").status_code == 401
    with pytest.raises(sqlite3.IntegrityError, match="identity and revocation are immutable"):
        harness.store._connection.execute(
            "UPDATE staff_sessions SET revoked_at = NULL WHERE actor_id = ?",
            (ACTOR_IDS["course-admin"],),
        )


def test_idle_session_expiry_fails_closed_and_can_be_purged(harness: Harness) -> None:
    _, login = harness.login()
    assert login.status_code == 200
    harness.current_time[0] = NOW + harness.config.session_idle_ttl + timedelta(seconds=1)

    assert harness.client.get("/staff/session").status_code == 401
    purged = harness.store.purge_inactive_staff_sessions(before=harness.current_time[0])
    assert purged == 1


def test_transport_exposes_no_deferred_routes(harness: Harness) -> None:
    csrf, login = harness.login()
    assert login.status_code == 200
    submission = harness.client.post("/staff/submissions", headers=harness.headers(csrf))
    assert submission.status_code == 404
    assert submission.json()["error"] == {"code": "RESOURCE_NOT_AVAILABLE"}
    assert harness.client.get("/staff/registry").status_code == 404
    assert (
        harness.client.post("/staff/configurations", headers=harness.headers(csrf)).status_code
        == 404
    )
