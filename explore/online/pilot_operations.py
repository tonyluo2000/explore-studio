"""Bounded JWKS resilience, maintenance, and redacted pilot observability."""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import logging
import math
import threading
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from explore.online.oidc import OIDCAuthenticationError, OIDCRemote
from explore.online.pilot_config import PilotJWKSCacheConfig, PilotMaintenanceConfig
from explore.online.transport_models import StaffOIDCProvider
from explore.online.transport_persistence import SQLiteStaffTransportStore

_OBSERVABLE_ROUTES = frozenset(
    {
        "/health/live",
        "/health/ready",
        "/staff/oidc/login/{provider_id}",
        "/staff/oidc/callback/{provider_id}",
        "/staff/session",
        "/staff/logout",
        "/staff/control-plane/memberships",
        "/staff/control-plane/memberships/{cohort_id}/{actor_id}",
        "/staff/control-plane/namespaces",
        "/staff/control-plane/namespaces/{package_id}/grants",
        "/staff/control-plane/namespaces/{package_id}/grants/{actor_id}",
        "/staff/control-plane/namespaces/{package_id}/transfer",
        "/staff/registry/{package_id}/{semantic_version}",
        "/staff/pins",
    }
)


@dataclass(frozen=True)
class PilotCleanupResult:
    expired_oidc_transactions: int
    inactive_sessions: int
    completed_at: datetime


class PilotObserver:
    """Aggregate bounded metrics and emit logs without request or identity data."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("explore-studio.staff-pilot")
        self._counts: Counter[tuple[str, str, str]] = Counter()
        self._lock = threading.Lock()

    @staticmethod
    def correlation_tag(value: str | None) -> str | None:
        if not isinstance(value, str) or not value or len(value) > 128:
            return None
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

    def record_http(
        self,
        *,
        method: str,
        route: str,
        status_code: int,
        elapsed_ms: int,
        correlation_id: str | None,
    ) -> None:
        safe_method = method if method in {"GET", "POST", "PATCH", "DELETE", "HEAD"} else "OTHER"
        safe_route = route if route in _OBSERVABLE_ROUTES else "unmatched"
        status_class = f"{status_code // 100}xx" if 100 <= status_code <= 599 else "invalid"
        with self._lock:
            self._counts[(safe_method, safe_route, status_class)] += 1
        event = {
            "correlation_tag": self.correlation_tag(correlation_id),
            "elapsed_ms": max(0, min(elapsed_ms, 3_600_000)),
            "event": "staff_pilot_http",
            "method": safe_method,
            "route": safe_route,
            "status_class": status_class,
        }
        self._logger.info(json.dumps(event, separators=(",", ":"), sort_keys=True))

    def record_operation(self, operation: str, outcome: str) -> None:
        if operation not in {"jwks-cache", "maintenance", "readiness", "revocation"}:
            operation = "internal"
        if outcome not in {"hit", "refresh", "stale", "success", "failure"}:
            outcome = "failure"
        with self._lock:
            self._counts[("INTERNAL", operation, outcome)] += 1
        self._logger.info(
            json.dumps(
                {"event": "staff_pilot_operation", "operation": operation, "outcome": outcome},
                separators=(",", ":"),
                sort_keys=True,
            )
        )

    def metrics_snapshot(self) -> dict[tuple[str, str, str], int]:
        """Return aggregate labels only; no tokens, subjects, paths, or object IDs."""
        with self._lock:
            return dict(self._counts)


@dataclass(frozen=True)
class _JWKSCacheEntry:
    document: dict[str, object]
    fetched_at: float


class CachingOIDCRemote:
    """Cache verified-shape JWKS with bounded stale-on-outage and forced rotation."""

    def __init__(
        self,
        remote: OIDCRemote,
        config: PilotJWKSCacheConfig,
        *,
        observer: PilotObserver,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if not callable(getattr(remote, "exchange_code", None)) or not callable(
            getattr(remote, "fetch_jwks", None)
        ):
            raise TypeError("remote must implement OIDCRemote")
        if not isinstance(config, PilotJWKSCacheConfig):
            raise TypeError("config must be PilotJWKSCacheConfig")
        self._remote = remote
        self._config = config
        self._observer = observer
        self._monotonic = monotonic
        self._entries: dict[str, _JWKSCacheEntry] = {}
        self._lock = threading.Lock()

    def exchange_code(
        self,
        provider: StaffOIDCProvider,
        *,
        code: str,
        code_verifier: str,
    ) -> dict[str, object]:
        return self._remote.exchange_code(
            provider,
            code=code,
            code_verifier=code_verifier,
        )

    @staticmethod
    def _validated_shape(document: dict[str, object]) -> dict[str, object]:
        if not isinstance(document, dict):
            raise OIDCAuthenticationError("JWKS was rejected")
        keys = document.get("keys")
        if not isinstance(keys, list) or not 1 <= len(keys) <= 32:
            raise OIDCAuthenticationError("JWKS was rejected")
        try:
            return copy.deepcopy(document)
        except (TypeError, RecursionError) as error:
            raise OIDCAuthenticationError("JWKS was rejected") from error

    def _fetch(self, provider: StaffOIDCProvider, *, force: bool) -> dict[str, object]:
        now = self._monotonic()
        if (
            not isinstance(now, (int, float))
            or isinstance(now, bool)
            or not math.isfinite(now)
            or now < 0
        ):
            raise RuntimeError("trusted monotonic clock returned an invalid value")
        key = provider.provider_id
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None and now < entry.fetched_at:
                entry = None
                self._entries.pop(key, None)
            fresh_seconds = self._config.fresh_ttl.total_seconds()
            stale_seconds = self._config.stale_if_error_ttl.total_seconds()
            if not force and entry is not None and now - entry.fetched_at <= fresh_seconds:
                self._observer.record_operation("jwks-cache", "hit")
                return copy.deepcopy(entry.document)
            try:
                document = self._validated_shape(self._remote.fetch_jwks(provider))
            except OIDCAuthenticationError:
                if entry is not None and now - entry.fetched_at <= fresh_seconds + stale_seconds:
                    self._observer.record_operation("jwks-cache", "stale")
                    return copy.deepcopy(entry.document)
                self._observer.record_operation("jwks-cache", "failure")
                raise
            self._entries[key] = _JWKSCacheEntry(document, float(now))
            self._observer.record_operation("jwks-cache", "refresh")
            return copy.deepcopy(document)

    def fetch_jwks(self, provider: StaffOIDCProvider) -> dict[str, object]:
        return self._fetch(provider, force=False)

    def refresh_jwks(self, provider: StaffOIDCProvider) -> dict[str, object]:
        """Force one refresh after a signed token references an unknown/ambiguous key."""
        return self._fetch(provider, force=True)


class StaffPilotMaintenance:
    """Cleanup and emergency revocation jobs sharing the application operation lock."""

    def __init__(
        self,
        store: SQLiteStaffTransportStore,
        config: PilotMaintenanceConfig,
        *,
        operation_lock: threading.RLock,
        observer: PilotObserver,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._store = store
        self._config = config
        self._operation_lock = operation_lock
        self._observer = observer
        self._clock = clock
        self._state_lock = threading.Lock()
        self._last_success: datetime | None = None

    def run_cleanup(self) -> PilotCleanupResult:
        now = self._clock()
        try:
            with self._operation_lock:
                expired_transactions = self._store.purge_expired_authorization_transactions(now=now)
                inactive_sessions = self._store.purge_inactive_staff_sessions(before=now)
        except Exception:
            self._observer.record_operation("maintenance", "failure")
            raise
        with self._state_lock:
            self._last_success = now
        self._observer.record_operation("maintenance", "success")
        return PilotCleanupResult(expired_transactions, inactive_sessions, now)

    def revoke_actor(self, actor_id: str) -> int:
        with self._operation_lock:
            changed = self._store.revoke_actor_sessions(actor_id=actor_id, now=self._clock())
        self._observer.record_operation("revocation", "success")
        return changed

    def revoke_issuer(self, issuer: str) -> int:
        with self._operation_lock:
            changed = self._store.revoke_issuer_sessions(issuer=issuer, now=self._clock())
        self._observer.record_operation("revocation", "success")
        return changed

    def is_fresh(self) -> bool:
        now = self._clock()
        with self._state_lock:
            last_success = self._last_success
        return (
            last_success is not None
            and now >= last_success
            and now - last_success <= self._config.readiness_max_staleness
        )

    async def run_periodically(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                await asyncio.wait_for(
                    stop.wait(),
                    timeout=self._config.cleanup_interval.total_seconds(),
                )
            except TimeoutError:
                try:
                    await asyncio.to_thread(self.run_cleanup)
                except Exception:
                    # Readiness becomes stale; the bounded loop remains available for recovery.
                    continue


__all__ = [
    "CachingOIDCRemote",
    "PilotCleanupResult",
    "PilotObserver",
    "StaffPilotMaintenance",
]
