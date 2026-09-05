"""Trusted configuration and immutable state for staff HTTP transport."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit
from uuid import UUID

from explore.online.models import AssuranceLevel

_PROVIDER_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.ASCII)
_COOKIE_NAME = re.compile(r"__Host-[A-Za-z0-9_-]+", re.ASCII)
_CONTROL_CHARACTER = re.compile(r"[\x00-\x1f\x7f]", re.ASCII)


def _text(value: str, field_name: str, *, maximum: int) -> None:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{field_name} must contain 1 to {maximum} characters")
    if _CONTROL_CHARACTER.search(value) is not None:
        raise ValueError(f"{field_name} must not contain control characters")


def _https_url(value: str, field_name: str) -> None:
    _text(value, field_name, maximum=2048)
    try:
        parsed = urlsplit(value)
        parsed_port = parsed.port
    except ValueError as error:
        raise ValueError(f"{field_name} must be an absolute HTTPS URL") from error
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.hostname is None
        or any(character.isspace() for character in parsed.netloc)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or (parsed_port is not None and not 1 <= parsed_port <= 65535)
    ):
        raise ValueError(f"{field_name} must be an absolute HTTPS URL")


@dataclass(frozen=True)
class StaffOIDCProvider:
    """One statically configured OIDC provider; discovery is not request-driven."""

    provider_id: str
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    client_id: str
    client_secret: str = field(repr=False)
    redirect_uri: str
    aal2_acr_values: frozenset[str]
    aal2_amr_values: frozenset[str] = frozenset({"mfa", "otp", "hwk", "swk"})
    signing_algorithms: tuple[str, ...] = ("RS256",)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.provider_id, str)
            or _PROVIDER_ID.fullmatch(self.provider_id) is None
        ):
            raise ValueError("provider_id must be lower-kebab-case")
        for name in ("issuer", "authorization_endpoint", "token_endpoint", "jwks_uri"):
            _https_url(getattr(self, name), name)
        _https_url(self.redirect_uri, "redirect_uri")
        if urlsplit(self.issuer).query or urlsplit(self.authorization_endpoint).query:
            raise ValueError("issuer and authorization_endpoint must not contain a query")
        if urlsplit(self.redirect_uri).query:
            raise ValueError("redirect_uri must not contain a query")
        _text(self.client_id, "client_id", maximum=512)
        _text(self.client_secret, "client_secret", maximum=4096)
        if not isinstance(self.aal2_acr_values, frozenset) or not self.aal2_acr_values:
            raise ValueError("aal2_acr_values must contain configured non-empty values")
        for value in self.aal2_acr_values:
            _text(value, "aal2_acr_value", maximum=256)
        if not isinstance(self.aal2_amr_values, frozenset) or not self.aal2_amr_values:
            raise ValueError("aal2_amr_values must contain configured non-empty values")
        for value in self.aal2_amr_values:
            _text(value, "aal2_amr_value", maximum=64)
        if self.signing_algorithms != ("RS256",):
            raise ValueError("staff OIDC v0.1 supports exactly RS256")


@dataclass(frozen=True)
class StaffTransportConfig:
    """Server-owned transport policy; none of these values come from requests."""

    providers: tuple[StaffOIDCProvider, ...]
    allowed_origin: str
    session_cookie_name: str = "__Host-explore-staff"
    transaction_cookie_name: str = "__Host-explore-oidc"
    csrf_cookie_name: str = "__Host-explore-csrf"
    session_idle_ttl: timedelta = timedelta(minutes=30)
    session_absolute_ttl: timedelta = timedelta(hours=8)
    authorization_ttl: timedelta = timedelta(minutes=5)
    id_token_max_age: timedelta = timedelta(minutes=10)
    clock_skew: timedelta = timedelta(seconds=60)
    max_request_bytes: int = 16_384
    oidc_response_max_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        if (
            not isinstance(self.providers, tuple)
            or not self.providers
            or any(not isinstance(provider, StaffOIDCProvider) for provider in self.providers)
        ):
            raise ValueError("at least one OIDC provider is required")
        provider_ids = [provider.provider_id for provider in self.providers]
        issuers = [provider.issuer for provider in self.providers]
        if len(set(provider_ids)) != len(provider_ids) or len(set(issuers)) != len(issuers):
            raise ValueError("OIDC provider IDs and issuers must be unique")
        _https_url(self.allowed_origin, "allowed_origin")
        parsed_origin = urlsplit(self.allowed_origin)
        if parsed_origin.path or parsed_origin.query:
            raise ValueError("allowed_origin must contain only scheme and authority")
        for name in ("session_cookie_name", "transaction_cookie_name", "csrf_cookie_name"):
            value = getattr(self, name)
            if not isinstance(value, str) or _COOKIE_NAME.fullmatch(value) is None:
                raise ValueError(f"{name} must use a __Host- cookie name")
        if (
            len(
                {
                    self.session_cookie_name,
                    self.transaction_cookie_name,
                    self.csrf_cookie_name,
                }
            )
            != 3
        ):
            raise ValueError("transport cookie names must be unique")
        for name in (
            "session_idle_ttl",
            "session_absolute_ttl",
            "authorization_ttl",
            "id_token_max_age",
            "clock_skew",
        ):
            value = getattr(self, name)
            if not isinstance(value, timedelta) or value <= timedelta(0):
                raise ValueError(f"{name} must be a positive timedelta")
        if self.session_idle_ttl > self.session_absolute_ttl:
            raise ValueError("session idle TTL must not exceed the absolute TTL")
        if (
            not isinstance(self.max_request_bytes, int)
            or isinstance(self.max_request_bytes, bool)
            or self.max_request_bytes < 1024
        ):
            raise ValueError("max_request_bytes must be at least 1024")
        if (
            not isinstance(self.oidc_response_max_bytes, int)
            or isinstance(self.oidc_response_max_bytes, bool)
            or self.oidc_response_max_bytes < 1024
        ):
            raise ValueError("oidc_response_max_bytes must be at least 1024")

    def provider(self, provider_id: str) -> StaffOIDCProvider | None:
        return next(
            (provider for provider in self.providers if provider.provider_id == provider_id),
            None,
        )


@dataclass(frozen=True)
class OIDCAuthorizationTransaction:
    provider_id: str
    state_digest: str
    browser_digest: str
    nonce: str
    code_verifier: str
    created_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.provider_id, str)
            or _PROVIDER_ID.fullmatch(self.provider_id) is None
        ):
            raise ValueError("provider_id must be lower-kebab-case")
        for name in ("state_digest", "browser_digest"):
            value = getattr(self, name)
            if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
                raise ValueError(f"{name} must be a SHA-256 digest")
        _text(self.nonce, "nonce", maximum=256)
        _text(self.code_verifier, "code_verifier", maximum=128)
        for name in ("created_at", "expires_at"):
            value = getattr(self, name)
            if (
                not isinstance(value, datetime)
                or value.tzinfo is None
                or value.utcoffset() != UTC.utcoffset(value)
            ):
                raise ValueError(f"{name} must use UTC")
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")


@dataclass(frozen=True)
class StaffSession:
    session_digest: str
    actor_id: str
    issuer: str
    subject: str
    assurance: AssuranceLevel
    csrf_digest: str
    created_at: datetime
    idle_expires_at: datetime
    absolute_expires_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        for name in ("session_digest", "csrf_digest"):
            value = getattr(self, name)
            if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
                raise ValueError(f"{name} must be a SHA-256 digest")
        try:
            actor_id = UUID(self.actor_id)
        except (TypeError, ValueError) as error:
            raise ValueError("actor_id must be a canonical UUID") from error
        if str(actor_id) != self.actor_id:
            raise ValueError("actor_id must be a canonical lowercase UUID")
        _https_url(self.issuer, "issuer")
        _text(self.subject, "subject", maximum=512)
        if not isinstance(self.assurance, AssuranceLevel):
            raise ValueError("assurance must be an AssuranceLevel")
        for name in (
            "created_at",
            "idle_expires_at",
            "absolute_expires_at",
            "last_seen_at",
        ):
            value = getattr(self, name)
            if (
                not isinstance(value, datetime)
                or value.tzinfo is None
                or value.utcoffset() != UTC.utcoffset(value)
            ):
                raise ValueError(f"{name} must use UTC")
        if not (
            self.created_at <= self.last_seen_at < self.idle_expires_at <= self.absolute_expires_at
        ):
            raise ValueError("staff session timestamps are inconsistent")
        if self.revoked_at is not None and (
            self.revoked_at.tzinfo is None
            or self.revoked_at.utcoffset() != UTC.utcoffset(self.revoked_at)
            or self.revoked_at < self.created_at
        ):
            raise ValueError("revoked_at must use UTC and follow creation")

    @property
    def active(self) -> bool:
        return self.revoked_at is None


__all__ = [
    "OIDCAuthorizationTransaction",
    "StaffOIDCProvider",
    "StaffSession",
    "StaffTransportConfig",
]
