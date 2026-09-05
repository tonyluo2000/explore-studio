"""Strict OIDC authorization-code/PKCE verification for staff transport."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import math
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

import jwt
from jwt.algorithms import RSAAlgorithm

from explore.online.models import AssuranceLevel
from explore.online.submission_models import AuthenticatedOIDCIdentity
from explore.online.transport_models import OIDCAuthorizationTransaction, StaffOIDCProvider
from explore.online.transport_persistence import SQLiteStaffTransportStore

_OPAQUE_TOKEN = re.compile(r"[A-Za-z0-9_-]{32,512}", re.ASCII)
_AUTHORIZATION_CODE = re.compile(r"[\x21-\x7e]{1,1024}", re.ASCII)
_BASE64URL_SEGMENT = re.compile(r"[A-Za-z0-9_-]+", re.ASCII)


class OIDCAuthenticationError(PermissionError):
    """OIDC exchange or validation failed without exposing sensitive detail."""


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _strict_json_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    document: dict[str, object] = {}
    for key, value in pairs:
        if key in document:
            raise OIDCAuthenticationError("identity provider response was rejected")
        document[key] = value
    return document


def _reject_json_constant(_value: str):
    raise OIDCAuthenticationError("identity provider response was rejected")


def _strict_jwt_json(segment: str) -> dict[str, object]:
    if len(segment) > 16_384 or _BASE64URL_SEGMENT.fullmatch(segment) is None:
        raise OIDCAuthenticationError("ID token was rejected")
    try:
        raw = base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
    except (ValueError, binascii.Error) as error:
        raise OIDCAuthenticationError("ID token was rejected") from error
    canonical = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    if not hmac.compare_digest(segment, canonical):
        raise OIDCAuthenticationError("ID token was rejected")
    try:
        document = json.loads(
            raw,
            object_pairs_hook=_strict_json_pairs,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise OIDCAuthenticationError("ID token was rejected") from error
    if not isinstance(document, dict) or not all(isinstance(key, str) for key in document):
        raise OIDCAuthenticationError("ID token was rejected")
    return document


class OIDCRemote(Protocol):
    def exchange_code(
        self,
        provider: StaffOIDCProvider,
        *,
        code: str,
        code_verifier: str,
    ) -> dict[str, object]: ...

    def fetch_jwks(self, provider: StaffOIDCProvider) -> dict[str, object]: ...


class UrllibOIDCRemote:
    """Bounded HTTPS client for configured token and JWKS endpoints."""

    def __init__(self, *, timeout_seconds: float = 5.0, max_response_bytes: int = 1_048_576):
        if timeout_seconds <= 0 or max_response_bytes < 1024:
            raise ValueError("OIDC HTTP bounds must be positive")
        self._timeout_seconds = timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._opener = urllib.request.build_opener(_RejectRedirects())

    def _json_request(self, request: urllib.request.Request) -> dict[str, object]:
        try:
            with self._opener.open(request, timeout=self._timeout_seconds) as response:
                content_type = response.headers.get_content_type()
                if content_type not in ("application/json", "application/jwk-set+json"):
                    raise OIDCAuthenticationError("identity provider response was rejected")
                if response.headers.get("Content-Encoding", "identity") != "identity":
                    raise OIDCAuthenticationError("identity provider response was rejected")
                body = response.read(self._max_response_bytes + 1)
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as error:
            raise OIDCAuthenticationError("identity provider response was rejected") from error
        if len(body) > self._max_response_bytes:
            raise OIDCAuthenticationError("identity provider response was rejected")
        try:
            document = json.loads(
                body,
                object_pairs_hook=_strict_json_pairs,
                parse_constant=_reject_json_constant,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
            raise OIDCAuthenticationError("identity provider response was rejected") from error
        if not isinstance(document, dict) or not all(isinstance(key, str) for key in document):
            raise OIDCAuthenticationError("identity provider response was rejected")
        return document

    def exchange_code(
        self,
        provider: StaffOIDCProvider,
        *,
        code: str,
        code_verifier: str,
    ) -> dict[str, object]:
        encoded = urllib.parse.urlencode(
            {
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": provider.redirect_uri,
            }
        ).encode("ascii")
        escaped_client_id = urllib.parse.quote(provider.client_id, safe="~")
        escaped_client_secret = urllib.parse.quote(provider.client_secret, safe="~")
        basic_credentials = base64.b64encode(
            f"{escaped_client_id}:{escaped_client_secret}".encode()
        ).decode("ascii")
        request = urllib.request.Request(
            provider.token_endpoint,
            data=encoded,
            headers={
                "Accept": "application/json",
                "Authorization": f"Basic {basic_credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        return self._json_request(request)

    def fetch_jwks(self, provider: StaffOIDCProvider) -> dict[str, object]:
        request = urllib.request.Request(
            provider.jwks_uri,
            headers={"Accept": "application/json"},
            method="GET",
        )
        return self._json_request(request)


@dataclass(frozen=True)
class OIDCAuthorizationStart:
    authorization_url: str
    browser_token: str


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _b64url_sha256(value: str) -> str:
    return (
        base64.urlsafe_b64encode(hashlib.sha256(value.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )


def _token_response_id_token(document: dict[str, object]) -> str:
    if document.get("token_type") != "Bearer":
        raise OIDCAuthenticationError("identity provider response was rejected")
    id_token = document.get("id_token")
    if not isinstance(id_token, str) or not id_token or len(id_token) > 16_384:
        raise OIDCAuthenticationError("identity provider response was rejected")
    if "error" in document:
        raise OIDCAuthenticationError("identity provider response was rejected")
    return id_token


class OIDCProtocol:
    """Creates one-time PKCE transactions and verifies signed ID tokens."""

    def __init__(
        self,
        store: SQLiteStaffTransportStore,
        remote: OIDCRemote,
        *,
        authorization_ttl,
        id_token_max_age,
        clock_skew,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        token_factory: Callable[[int], str] = secrets.token_urlsafe,
    ) -> None:
        self._store = store
        self._remote = remote
        self._authorization_ttl = authorization_ttl
        self._id_token_max_age = id_token_max_age
        self._clock_skew = clock_skew
        self._clock = clock
        self._token_factory = token_factory

    def start(self, provider: StaffOIDCProvider) -> OIDCAuthorizationStart:
        now = self._clock()
        state = self._token_factory(32)
        browser_token = self._token_factory(32)
        nonce = self._token_factory(32)
        code_verifier = self._token_factory(64)
        if not 43 <= len(code_verifier) <= 128:
            raise RuntimeError("trusted token factory returned an invalid PKCE verifier")
        transaction = OIDCAuthorizationTransaction(
            provider_id=provider.provider_id,
            state_digest=_digest(state),
            browser_digest=_digest(browser_token),
            nonce=nonce,
            code_verifier=code_verifier,
            created_at=now,
            expires_at=now + self._authorization_ttl,
        )
        self._store.append_authorization_transaction(transaction)
        query = urllib.parse.urlencode(
            {
                "acr_values": " ".join(sorted(provider.aal2_acr_values)),
                "client_id": provider.client_id,
                "code_challenge": _b64url_sha256(code_verifier),
                "code_challenge_method": "S256",
                "max_age": "0",
                "nonce": nonce,
                "prompt": "login",
                "redirect_uri": provider.redirect_uri,
                "response_type": "code",
                "scope": "openid",
                "state": state,
            }
        )
        return OIDCAuthorizationStart(
            authorization_url=f"{provider.authorization_endpoint}?{query}",
            browser_token=browser_token,
        )

    def complete(
        self,
        provider: StaffOIDCProvider,
        *,
        code: str,
        state: str,
        browser_token: str,
    ) -> AuthenticatedOIDCIdentity:
        if (
            not isinstance(code, str)
            or _AUTHORIZATION_CODE.fullmatch(code) is None
            or not isinstance(state, str)
            or _OPAQUE_TOKEN.fullmatch(state) is None
            or not isinstance(browser_token, str)
            or _OPAQUE_TOKEN.fullmatch(browser_token) is None
        ):
            raise OIDCAuthenticationError("OIDC callback was rejected")
        now = self._clock()
        transaction = self._store.consume_authorization_transaction(
            state_digest=_digest(state),
            browser_digest=_digest(browser_token),
            provider_id=provider.provider_id,
            now=now,
        )
        if transaction is None:
            raise OIDCAuthenticationError("OIDC callback was rejected")
        token_response = self._remote.exchange_code(
            provider,
            code=code,
            code_verifier=transaction.code_verifier,
        )
        id_token = _token_response_id_token(token_response)
        jwks = self._remote.fetch_jwks(provider)
        return self._validate_id_token(
            provider,
            id_token=id_token,
            nonce=transaction.nonce,
            jwks=jwks,
            now=now,
        )

    def _validate_id_token(
        self,
        provider: StaffOIDCProvider,
        *,
        id_token: str,
        nonce: str,
        jwks: dict[str, object],
        now: datetime,
    ) -> AuthenticatedOIDCIdentity:
        segments = id_token.split(".")
        if len(segments) != 3 or _BASE64URL_SEGMENT.fullmatch(segments[2]) is None:
            raise OIDCAuthenticationError("ID token was rejected")
        try:
            signature = base64.urlsafe_b64decode(segments[2] + "=" * (-len(segments[2]) % 4))
        except (ValueError, binascii.Error) as error:
            raise OIDCAuthenticationError("ID token was rejected") from error
        if not hmac.compare_digest(
            segments[2],
            base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii"),
        ):
            raise OIDCAuthenticationError("ID token was rejected")
        header = _strict_jwt_json(segments[0])
        unsigned_claims = _strict_jwt_json(segments[1])
        if not isinstance(header, dict) or not set(header).issubset({"alg", "kid", "typ"}):
            raise OIDCAuthenticationError("ID token was rejected")
        algorithm = header.get("alg")
        key_id = header.get("kid")
        token_type = header.get("typ")
        if (
            algorithm not in provider.signing_algorithms
            or not isinstance(key_id, str)
            or not key_id
            or len(key_id) > 256
            or re.fullmatch(r"[\x21-\x7e]+", key_id, re.ASCII) is None
            or (token_type is not None and token_type != "JWT")
        ):
            raise OIDCAuthenticationError("ID token was rejected")
        keys = jwks.get("keys")
        if not isinstance(keys, list) or not 1 <= len(keys) <= 32:
            raise OIDCAuthenticationError("JWKS was rejected")
        candidates = [
            key
            for key in keys
            if isinstance(key, dict)
            and key.get("kid") == key_id
            and key.get("kty") == "RSA"
            and key.get("alg") in (None, algorithm)
            and key.get("use") in (None, "sig")
            and all(
                prohibited not in key
                for prohibited in ("d", "p", "q", "dp", "dq", "qi", "oth", "x5u")
            )
        ]
        if len(candidates) != 1:
            raise OIDCAuthenticationError("JWKS was rejected")
        key_ops = candidates[0].get("key_ops")
        if key_ops is not None and (
            not isinstance(key_ops, list)
            or not key_ops
            or not all(isinstance(operation, str) for operation in key_ops)
            or len(set(key_ops)) != len(key_ops)
            or "verify" not in key_ops
        ):
            raise OIDCAuthenticationError("JWKS was rejected")
        try:
            public_key = RSAAlgorithm.from_jwk(json.dumps(candidates[0]))
            if public_key.key_size < 2048:
                raise ValueError("RSA verification keys must contain at least 2048 bits")
            claims = jwt.decode(
                id_token,
                public_key,
                algorithms=[str(algorithm)],
                audience=provider.client_id,
                issuer=provider.issuer,
                options={
                    "require": ["aud", "auth_time", "exp", "iat", "iss", "nonce", "sub"],
                    "verify_exp": False,
                    "verify_iat": False,
                    "verify_nbf": False,
                },
            )
        except (jwt.PyJWTError, ValueError, TypeError) as error:
            raise OIDCAuthenticationError("ID token was rejected") from error
        if claims != unsigned_claims:
            raise OIDCAuthenticationError("ID token was rejected")
        self._validate_claims(provider, claims=claims, nonce=nonce, now=now)
        return AuthenticatedOIDCIdentity(
            issuer=provider.issuer,
            subject=str(claims["sub"]),
            assurance=self._assurance(provider, claims),
        )

    def _validate_claims(
        self,
        provider: StaffOIDCProvider,
        *,
        claims: dict[str, object],
        nonce: str,
        now: datetime,
    ) -> None:
        subject = claims.get("sub")
        token_nonce = claims.get("nonce")
        if (
            not isinstance(subject, str)
            or not subject
            or len(subject) > 512
            or not isinstance(token_nonce, str)
            or not hmac.compare_digest(token_nonce, nonce)
        ):
            raise OIDCAuthenticationError("ID token was rejected")
        audience = claims.get("aud")
        authorized_party = claims.get("azp")
        if authorized_party is not None and authorized_party != provider.client_id:
            raise OIDCAuthenticationError("ID token was rejected")
        if isinstance(audience, list) and len(audience) > 1 and authorized_party is None:
            raise OIDCAuthenticationError("ID token was rejected")
        for name in ("auth_time", "exp", "iat"):
            value = claims.get(name)
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
            ):
                raise OIDCAuthenticationError("ID token was rejected")
        now_timestamp = now.timestamp()
        if float(claims["exp"]) <= now_timestamp - self._clock_skew.total_seconds():
            raise OIDCAuthenticationError("ID token was rejected")
        if float(claims["iat"]) > now_timestamp + self._clock_skew.total_seconds():
            raise OIDCAuthenticationError("ID token was rejected")
        if float(claims["iat"]) < (
            now_timestamp
            - self._id_token_max_age.total_seconds()
            - self._clock_skew.total_seconds()
        ):
            raise OIDCAuthenticationError("ID token was rejected")
        if (
            float(claims["auth_time"]) > now_timestamp + self._clock_skew.total_seconds()
            or float(claims["auth_time"]) > float(claims["iat"]) + self._clock_skew.total_seconds()
            or float(claims["auth_time"])
            < now_timestamp
            - self._id_token_max_age.total_seconds()
            - self._clock_skew.total_seconds()
        ):
            raise OIDCAuthenticationError("ID token was rejected")
        not_before = claims.get("nbf")
        if not_before is not None and (
            not isinstance(not_before, (int, float))
            or isinstance(not_before, bool)
            or not math.isfinite(not_before)
            or float(not_before) > now_timestamp + self._clock_skew.total_seconds()
        ):
            raise OIDCAuthenticationError("ID token was rejected")

    @staticmethod
    def _assurance(
        provider: StaffOIDCProvider,
        claims: dict[str, object],
    ) -> AssuranceLevel:
        acr = claims.get("acr")
        amr = claims.get("amr")
        if (
            isinstance(acr, str)
            and acr in provider.aal2_acr_values
            and isinstance(amr, list)
            and all(isinstance(value, str) for value in amr)
            and provider.aal2_amr_values.intersection(amr)
        ):
            return AssuranceLevel.AAL2
        return AssuranceLevel.AAL1


__all__ = [
    "OIDCAuthenticationError",
    "OIDCAuthorizationStart",
    "OIDCProtocol",
    "OIDCRemote",
    "UrllibOIDCRemote",
]
