"""Server-owned configuration and secret boundaries for a synthetic staff pilot."""

from __future__ import annotations

import ipaddress
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from enum import StrEnum
from pathlib import Path
from typing import Protocol
from urllib.parse import urlsplit

from explore.online.transport_models import StaffOIDCProvider, StaffTransportConfig

_ENVIRONMENT_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.ASCII)
_SEED_ID = re.compile(r"[a-z0-9]+(?:[._/-][a-z0-9]+)*", re.ASCII)
_SHA256 = re.compile(r"[0-9a-f]{64}", re.ASCII)
_SECRET_REFERENCE = re.compile(r"env:(EXPLORE_STAFF_SECRET_[A-Z0-9_]{1,96})", re.ASCII)
_CONTROL_CHARACTER = re.compile(r"[\x00-\x1f\x7f]", re.ASCII)


class PilotTLSMode(StrEnum):
    """How the pilot process receives authenticated HTTPS transport metadata."""

    DIRECT = "direct-tls"
    TRUSTED_PROXY = "trusted-proxy"


@dataclass(frozen=True, repr=False)
class LoadedSecret:
    """A deliberately non-printing secret returned by a deployment adapter."""

    value: str = field(repr=False)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or not 16 <= len(self.value) <= 4096
            or _CONTROL_CHARACTER.search(self.value) is not None
        ):
            raise ValueError("loaded secret must contain 16 to 4096 safe characters")


class SecretLoader(Protocol):
    """Resolve an opaque reference without placing credentials in configuration."""

    def load(self, reference: str) -> LoadedSecret: ...


class EnvironmentSecretLoader:
    """Minimal pilot adapter for explicitly named, process-injected secrets."""

    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        self._environment = os.environ if environment is None else environment

    def load(self, reference: str) -> LoadedSecret:
        if not isinstance(reference, str):
            raise ValueError("secret reference is invalid")
        match = _SECRET_REFERENCE.fullmatch(reference)
        if match is None:
            raise ValueError("secret reference must use the approved environment namespace")
        value = self._environment.get(match.group(1))
        if value is None:
            raise RuntimeError("required staff pilot secret is unavailable")
        return LoadedSecret(value)


@dataclass(frozen=True)
class PilotOIDCProviderConfig:
    """Non-secret, approved provider metadata plus one opaque credential reference."""

    provider_id: str
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str
    client_id: str
    client_secret_reference: str
    redirect_uri: str
    aal2_acr_values: frozenset[str]
    aal2_amr_values: frozenset[str] = frozenset({"mfa", "otp", "hwk", "swk"})

    def __post_init__(self) -> None:
        if (
            not isinstance(self.client_secret_reference, str)
            or _SECRET_REFERENCE.fullmatch(self.client_secret_reference) is None
        ):
            raise ValueError("client_secret_reference must use the approved environment namespace")
        StaffOIDCProvider(
            provider_id=self.provider_id,
            issuer=self.issuer,
            authorization_endpoint=self.authorization_endpoint,
            token_endpoint=self.token_endpoint,
            jwks_uri=self.jwks_uri,
            client_id=self.client_id,
            client_secret="configuration-validation-placeholder",
            redirect_uri=self.redirect_uri,
            aal2_acr_values=self.aal2_acr_values,
            aal2_amr_values=self.aal2_amr_values,
        )

    def resolve(self, secrets: SecretLoader) -> StaffOIDCProvider:
        if not callable(getattr(secrets, "load", None)):
            raise TypeError("secrets must implement SecretLoader")
        loaded = secrets.load(self.client_secret_reference)
        if not isinstance(loaded, LoadedSecret):
            raise TypeError("secret loader must return LoadedSecret")
        return StaffOIDCProvider(
            provider_id=self.provider_id,
            issuer=self.issuer,
            authorization_endpoint=self.authorization_endpoint,
            token_endpoint=self.token_endpoint,
            jwks_uri=self.jwks_uri,
            client_id=self.client_id,
            client_secret=loaded.value,
            redirect_uri=self.redirect_uri,
            aal2_acr_values=self.aal2_acr_values,
            aal2_amr_values=self.aal2_amr_values,
        )


@dataclass(frozen=True)
class PilotTransportTrustConfig:
    """Fail-closed public origin and TLS termination policy."""

    public_origin: str
    mode: PilotTLSMode
    trusted_proxy_networks: tuple[str, ...] = ()
    hsts_max_age_seconds: int = 31_536_000

    def __post_init__(self) -> None:
        if not isinstance(self.mode, PilotTLSMode):
            raise ValueError("mode must be a PilotTLSMode")
        # Reuse the transport origin validator without retaining this placeholder provider.
        if not isinstance(self.public_origin, str):
            raise ValueError("public_origin must be a string")
        try:
            origin = urlsplit(self.public_origin)
            port = origin.port
        except ValueError as error:
            raise ValueError("public_origin must be an absolute HTTPS origin") from error
        if (
            origin.scheme != "https"
            or origin.hostname is None
            or not origin.netloc
            or any(character.isspace() for character in origin.netloc)
            or origin.username is not None
            or origin.password is not None
            or origin.path
            or origin.query
            or origin.fragment
            or (port is not None and not 1 <= port <= 65535)
        ):
            raise ValueError("public_origin must be an absolute HTTPS origin")
        if self.mode is PilotTLSMode.DIRECT and self.trusted_proxy_networks:
            raise ValueError("direct TLS mode must not configure trusted proxy networks")
        if not isinstance(self.trusted_proxy_networks, tuple):
            raise ValueError("trusted_proxy_networks must be an immutable tuple")
        if self.mode is PilotTLSMode.TRUSTED_PROXY and not self.trusted_proxy_networks:
            raise ValueError("trusted proxy mode requires at least one narrow network")
        for value in self.trusted_proxy_networks:
            try:
                network = ipaddress.ip_network(value, strict=True)
            except (TypeError, ValueError) as error:
                raise ValueError("trusted proxy networks must be canonical CIDR values") from error
            minimum_prefix = 24 if network.version == 4 else 64
            if str(network) != value or network.prefixlen < minimum_prefix:
                raise ValueError("trusted proxy networks must be canonical and narrowly scoped")
        if (
            not isinstance(self.hsts_max_age_seconds, int)
            or isinstance(self.hsts_max_age_seconds, bool)
            or not 86_400 <= self.hsts_max_age_seconds <= 63_072_000
        ):
            raise ValueError("HSTS max age must be between one day and two years")


@dataclass(frozen=True)
class PilotSeedAttestation:
    """Reviewed identity of the only seed artifact allowed for one pilot datastore."""

    provenance: str
    version: str
    sha256: str

    def __post_init__(self) -> None:
        for name in ("provenance", "version"):
            value = getattr(self, name)
            if not isinstance(value, str) or _SEED_ID.fullmatch(value) is None:
                raise ValueError(f"seed {name} must be a canonical lowercase identifier")
        if not isinstance(self.sha256, str) or _SHA256.fullmatch(self.sha256) is None:
            raise ValueError("seed sha256 must be a lowercase SHA-256 digest")


@dataclass(frozen=True)
class PilotDatastoreConfig:
    """One isolated, locally locked SQLite datastore for synthetic pilot records."""

    path: Path
    environment_id: str
    seed_attestation: PilotSeedAttestation
    synthetic_only: bool = True
    worker_count: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path) or not self.path.is_absolute():
            raise ValueError("pilot datastore path must be an absolute Path")
        if self.path.suffix != ".sqlite3" or self.path.name in (".sqlite3", "..sqlite3"):
            raise ValueError("pilot datastore must use an explicit .sqlite3 file")
        if (
            not isinstance(self.environment_id, str)
            or _ENVIRONMENT_ID.fullmatch(self.environment_id) is None
        ):
            raise ValueError("environment_id must be lower-kebab-case")
        if not isinstance(self.seed_attestation, PilotSeedAttestation):
            raise TypeError("seed_attestation must be a PilotSeedAttestation")
        if self.synthetic_only is not True:
            raise ValueError("staff pilot datastore must be explicitly synthetic-only")
        if self.worker_count != 1:
            raise ValueError("SQLite staff pilot requires exactly one application worker")


@dataclass(frozen=True)
class PilotMaintenanceConfig:
    cleanup_interval: timedelta = timedelta(minutes=1)
    readiness_max_staleness: timedelta = timedelta(minutes=3)

    def __post_init__(self) -> None:
        if not isinstance(self.cleanup_interval, timedelta) or not timedelta(
            seconds=10
        ) <= self.cleanup_interval <= timedelta(hours=1):
            raise ValueError("cleanup interval must be between 10 seconds and one hour")
        if (
            not isinstance(self.readiness_max_staleness, timedelta)
            or self.readiness_max_staleness < self.cleanup_interval * 2
        ):
            raise ValueError("readiness staleness must cover at least two cleanup intervals")


@dataclass(frozen=True)
class PilotJWKSCacheConfig:
    fresh_ttl: timedelta = timedelta(minutes=5)
    stale_if_error_ttl: timedelta = timedelta(minutes=10)

    def __post_init__(self) -> None:
        if not isinstance(self.fresh_ttl, timedelta) or not timedelta(
            seconds=10
        ) <= self.fresh_ttl <= timedelta(hours=1):
            raise ValueError("JWKS fresh TTL must be between 10 seconds and one hour")
        if not isinstance(self.stale_if_error_ttl, timedelta) or not timedelta(
            0
        ) <= self.stale_if_error_ttl <= timedelta(hours=1):
            raise ValueError("JWKS outage grace must be between zero and one hour")


@dataclass(frozen=True)
class StaffPilotConfig:
    """Complete non-secret production configuration for the bounded pilot."""

    providers: tuple[PilotOIDCProviderConfig, ...]
    trust: PilotTransportTrustConfig
    datastore: PilotDatastoreConfig
    maintenance: PilotMaintenanceConfig = PilotMaintenanceConfig()
    jwks_cache: PilotJWKSCacheConfig = PilotJWKSCacheConfig()
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
            or any(not isinstance(provider, PilotOIDCProviderConfig) for provider in self.providers)
        ):
            raise ValueError("staff pilot requires approved OIDC providers")
        if not isinstance(self.trust, PilotTransportTrustConfig):
            raise TypeError("trust must be PilotTransportTrustConfig")
        if not isinstance(self.datastore, PilotDatastoreConfig):
            raise TypeError("datastore must be PilotDatastoreConfig")
        if not isinstance(self.maintenance, PilotMaintenanceConfig):
            raise TypeError("maintenance must be PilotMaintenanceConfig")
        if not isinstance(self.jwks_cache, PilotJWKSCacheConfig):
            raise TypeError("jwks_cache must be PilotJWKSCacheConfig")
        if self.session_idle_ttl > timedelta(minutes=30):
            raise ValueError("pilot session idle TTL must not exceed 30 minutes")
        if self.session_absolute_ttl > timedelta(hours=8):
            raise ValueError("pilot session absolute TTL must not exceed eight hours")
        if self.authorization_ttl > timedelta(minutes=5):
            raise ValueError("pilot OIDC transaction TTL must not exceed five minutes")
        if self.id_token_max_age > timedelta(minutes=10):
            raise ValueError("pilot ID token age must not exceed ten minutes")
        if self.clock_skew > timedelta(minutes=2):
            raise ValueError("pilot OIDC clock skew must not exceed two minutes")
        if self.max_request_bytes > 65_536:
            raise ValueError("pilot request limit must not exceed 64 KiB")
        if self.oidc_response_max_bytes > 1_048_576:
            raise ValueError("pilot OIDC response limit must not exceed 1 MiB")
        placeholder_providers = tuple(
            StaffOIDCProvider(
                provider_id=provider.provider_id,
                issuer=provider.issuer,
                authorization_endpoint=provider.authorization_endpoint,
                token_endpoint=provider.token_endpoint,
                jwks_uri=provider.jwks_uri,
                client_id=provider.client_id,
                client_secret="configuration-validation-placeholder",
                redirect_uri=provider.redirect_uri,
                aal2_acr_values=provider.aal2_acr_values,
                aal2_amr_values=provider.aal2_amr_values,
            )
            for provider in self.providers
        )
        StaffTransportConfig(
            providers=placeholder_providers,
            allowed_origin=self.trust.public_origin,
            session_idle_ttl=self.session_idle_ttl,
            session_absolute_ttl=self.session_absolute_ttl,
            authorization_ttl=self.authorization_ttl,
            id_token_max_age=self.id_token_max_age,
            clock_skew=self.clock_skew,
            max_request_bytes=self.max_request_bytes,
            oidc_response_max_bytes=self.oidc_response_max_bytes,
        )
        expected_redirects = {
            f"{self.trust.public_origin}/staff/oidc/callback/{provider.provider_id}"
            for provider in self.providers
        }
        actual_redirects = {provider.redirect_uri for provider in self.providers}
        if actual_redirects != expected_redirects:
            raise ValueError("OIDC redirect URIs must use their exact public pilot callback")
        references = [provider.client_secret_reference for provider in self.providers]
        if len(set(references)) != len(references):
            raise ValueError("each OIDC provider must use a distinct client secret reference")

    def resolve_transport(self, secrets: SecretLoader) -> StaffTransportConfig:
        """Resolve credentials once and produce the existing immutable transport policy."""
        return StaffTransportConfig(
            providers=tuple(provider.resolve(secrets) for provider in self.providers),
            allowed_origin=self.trust.public_origin,
            session_idle_ttl=self.session_idle_ttl,
            session_absolute_ttl=self.session_absolute_ttl,
            authorization_ttl=self.authorization_ttl,
            id_token_max_age=self.id_token_max_age,
            clock_skew=self.clock_skew,
            max_request_bytes=self.max_request_bytes,
            oidc_response_max_bytes=self.oidc_response_max_bytes,
        )


__all__ = [
    "EnvironmentSecretLoader",
    "LoadedSecret",
    "PilotDatastoreConfig",
    "PilotJWKSCacheConfig",
    "PilotMaintenanceConfig",
    "PilotOIDCProviderConfig",
    "PilotSeedAttestation",
    "PilotTLSMode",
    "PilotTransportTrustConfig",
    "SecretLoader",
    "StaffPilotConfig",
]
