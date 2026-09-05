"""Composition root for the synthetic-only external staff pilot."""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from types import TracebackType
from urllib.parse import urlsplit

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Match
from starlette.types import Receive, Scope, Send

from explore.online.models import AssuranceLevel
from explore.online.oidc import OIDCRemote, UrllibOIDCRemote
from explore.online.pilot_config import (
    PilotTLSMode,
    SecretLoader,
    StaffPilotConfig,
)
from explore.online.pilot_datastore import (
    SyntheticPilotDatastore,
    bootstrap_synthetic_pilot_datastore,
)
from explore.online.pilot_operations import (
    CachingOIDCRemote,
    PilotObserver,
    StaffPilotMaintenance,
)
from explore.online.staff_transport import create_staff_transport_app
from explore.online.transport_persistence import SQLiteStaffTransportStore


def _headers(scope: Scope, name: bytes) -> list[str]:
    values = []
    for header_name, raw_value in scope.get("headers", []):
        if header_name.lower() == name:
            if len(raw_value) > 4096:
                return []
            values.append(raw_value.decode("latin-1"))
    return values


class StaffPilotApplication:
    """Apply trusted transport metadata, safe health checks, and redacted telemetry."""

    def __init__(
        self,
        inner: Starlette,
        config: StaffPilotConfig,
        datastore: SyntheticPilotDatastore,
        maintenance: StaffPilotMaintenance,
        observer: PilotObserver,
        *,
        operation_lock,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._inner = inner
        self._config = config
        self._datastore = datastore
        self._maintenance = maintenance
        self._observer = observer
        self._operation_lock = operation_lock
        self._monotonic = monotonic
        self._proxy_networks = tuple(
            ipaddress.ip_network(value) for value in config.trust.trusted_proxy_networks
        )
        self._stop: asyncio.Event | None = None
        self._maintenance_task: asyncio.Task[None] | None = None

    def _route_template(self, scope: Scope) -> str:
        partial: str | None = None
        for route in self._inner.routes:
            match, _ = route.matches(scope)
            template = getattr(route, "path", None)
            if not isinstance(template, str):
                continue
            if match is Match.FULL:
                return template
            if match is Match.PARTIAL and partial is None:
                partial = template
        return partial or "unmatched"

    def _trusted_http_scope(self, scope: Scope) -> Scope | None:
        expected_host = urlsplit(self._config.trust.public_origin).netloc
        if _headers(scope, b"host") != [expected_host]:
            return None
        forwarded = _headers(scope, b"forwarded")
        forwarded_proto = _headers(scope, b"x-forwarded-proto")
        forwarded_host = _headers(scope, b"x-forwarded-host")
        forwarded_prefix = _headers(scope, b"x-forwarded-prefix")
        forwarded_for = _headers(scope, b"x-forwarded-for")
        forwarded_port = _headers(scope, b"x-forwarded-port")
        if forwarded or forwarded_prefix:
            return None
        if self._config.trust.mode is PilotTLSMode.DIRECT:
            if (
                scope.get("scheme") != "https"
                or forwarded_proto
                or forwarded_host
                or forwarded_for
                or forwarded_port
            ):
                return None
            return scope
        client = scope.get("client")
        if not isinstance(client, tuple) or len(client) != 2:
            return None
        try:
            address = ipaddress.ip_address(client[0])
        except (TypeError, ValueError):
            return None
        if (
            not any(address in network for network in self._proxy_networks)
            or forwarded_proto != ["https"]
            or forwarded_host != [expected_host]
            or (forwarded_port and forwarded_port != ["443"])
            or len(forwarded_for) > 1
        ):
            return None
        trusted_scope = dict(scope)
        trusted_scope["scheme"] = "https"
        untrusted_forwarding_headers = {
            b"forwarded",
            b"x-forwarded-for",
            b"x-forwarded-host",
            b"x-forwarded-port",
            b"x-forwarded-prefix",
            b"x-forwarded-proto",
        }
        trusted_scope["headers"] = [
            (name, value)
            for name, value in scope.get("headers", [])
            if name.lower() not in untrusted_forwarding_headers
        ]
        return trusted_scope

    @staticmethod
    def _correlation_id(scope: Scope) -> str | None:
        values = _headers(scope, b"x-correlation-id")
        return values[0] if len(values) == 1 else None

    def _secure(self, response: JSONResponse) -> JSONResponse:
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Strict-Transport-Security"] = (
            f"max-age={self._config.trust.hsts_max_age_seconds}; includeSubDomains"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    async def _health(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope.get("method") != "GET"
            or scope.get("query_string")
            or _headers(scope, b"content-length") not in ([], ["0"])
            or _headers(scope, b"transfer-encoding")
        ):
            response = self._secure(JSONResponse({"status": "unavailable"}, status_code=400))
        elif scope.get("path") == "/health/live":
            response = self._secure(JSONResponse({"status": "ok"}))
        else:
            ready = False
            try:
                with self._operation_lock:
                    self._datastore.assert_process_owner()
                    ready = self._datastore.is_ready()
                    if ready:
                        ready = all(
                            self._datastore.store.identity_provider_assurance(provider.issuer)
                            is AssuranceLevel.AAL2
                            for provider in self._config.providers
                        )
                    if ready:
                        ready = self._maintenance.is_fresh()
            except Exception:
                # Health responses own dependency failures and never expose their detail.
                ready = False
            self._observer.record_operation("readiness", "success" if ready else "failure")
            response = self._secure(
                JSONResponse(
                    {"status": "ready" if ready else "unavailable"},
                    status_code=200 if ready else 503,
                )
            )
        await response(scope, receive, send)

    async def _lifespan(self, receive: Receive, send: Send) -> None:
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                try:
                    self._datastore.assert_process_owner()
                    await asyncio.to_thread(self._maintenance.run_cleanup)
                    self._stop = asyncio.Event()
                    self._maintenance_task = asyncio.create_task(
                        self._maintenance.run_periodically(self._stop)
                    )
                except Exception:
                    await send(
                        {
                            "type": "lifespan.startup.failed",
                            "message": "staff pilot startup checks failed",
                        }
                    )
                    return
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                if self._stop is not None:
                    self._stop.set()
                if self._maintenance_task is not None:
                    await self._maintenance_task
                await send({"type": "lifespan.shutdown.complete"})
                return

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await self._lifespan(receive, send)
            return
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        if scope["type"] != "http":
            return
        started = self._monotonic()
        trusted_scope = self._trusted_http_scope(scope)
        status_code = 500

        async def observed_send(message: dict[str, object]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = list(message.get("headers", []))
                if not any(name.lower() == b"strict-transport-security" for name, _ in headers):
                    headers.append(
                        (
                            b"strict-transport-security",
                            (
                                f"max-age={self._config.trust.hsts_max_age_seconds}; "
                                "includeSubDomains"
                            ).encode("ascii"),
                        )
                    )
                    message = {**message, "headers": headers}
            await send(message)  # type: ignore[arg-type]

        try:
            self._datastore.assert_process_owner()
            process_owned = True
        except Exception:
            process_owned = False
        if not process_owned:
            self._observer.record_operation("readiness", "failure")
            response = self._secure(JSONResponse({"status": "unavailable"}, status_code=503))
            await response(scope, receive, observed_send)
            route = "unmatched"
        elif trusted_scope is None:
            response = self._secure(
                JSONResponse({"error": {"code": "INVALID_REQUEST"}}, status_code=400)
            )
            await response(scope, receive, observed_send)
            route = "unmatched"
        elif trusted_scope.get("path") in {"/health/live", "/health/ready"}:
            await self._health(trusted_scope, receive, observed_send)
            route = str(trusted_scope["path"])
        else:
            route = self._route_template(trusted_scope)
            await self._inner(trusted_scope, receive, observed_send)
        elapsed_ms = int(max(0.0, self._monotonic() - started) * 1000)
        self._observer.record_http(
            method=str(scope.get("method", "OTHER")),
            route=route,
            status_code=status_code,
            elapsed_ms=elapsed_ms,
            correlation_id=self._correlation_id(scope),
        )


@dataclass
class StaffPilotRuntime:
    """Owned pilot components; close releases the process-exclusive datastore lock."""

    app: StaffPilotApplication
    datastore: SyntheticPilotDatastore
    maintenance: StaffPilotMaintenance
    observer: PilotObserver

    def close(self) -> None:
        self.datastore.close()

    def __enter__(self) -> StaffPilotRuntime:
        return self

    def __exit__(
        self,
        _exception_type: type[BaseException] | None,
        _exception: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        self.close()


def create_staff_pilot_runtime(
    config: StaffPilotConfig,
    secrets: SecretLoader,
    *,
    oidc_remote: OIDCRemote | None = None,
    observer: PilotObserver | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    monotonic: Callable[[], float] = time.monotonic,
    token_factory=None,
    seed_initializer: Callable[[SQLiteStaffTransportStore, bytes], None] | None = None,
    seed_artifact: bytes | None = None,
) -> StaffPilotRuntime:
    """Resolve secrets and compose the existing staff boundary for a synthetic pilot."""
    if not isinstance(config, StaffPilotConfig):
        raise TypeError("config must be StaffPilotConfig")
    if (seed_initializer is None) != (seed_artifact is None):
        raise ValueError("seed_initializer and seed_artifact must be supplied together")
    if seed_artifact is not None:
        if not isinstance(seed_artifact, bytes) or not 1 <= len(seed_artifact) <= 1_048_576:
            raise ValueError("seed_artifact must contain 1 byte to 1 MiB")
        if hashlib.sha256(seed_artifact).hexdigest() != config.datastore.seed_attestation.sha256:
            raise ValueError("seed_artifact does not match its configured SHA-256 attestation")
    transport = config.resolve_transport(secrets)
    pilot_datastore = bootstrap_synthetic_pilot_datastore(config.datastore, clock=clock)
    try:
        if seed_initializer is not None:
            if not callable(seed_initializer):
                raise TypeError("seed_initializer must be callable")
            if pilot_datastore.seed_is_attested():
                raise ValueError("an attested pilot datastore cannot be reseeded")
            seed_initializer(pilot_datastore.store, seed_artifact)
            pilot_datastore.attest_seed(
                approved_issuers=tuple(provider.issuer for provider in config.providers),
                clock=clock,
            )
        operation_lock = threading.RLock()
        active_observer = observer or PilotObserver()
        remote = oidc_remote or UrllibOIDCRemote(
            max_response_bytes=transport.oidc_response_max_bytes
        )
        cached_remote = CachingOIDCRemote(
            remote,
            config.jwks_cache,
            observer=active_observer,
            monotonic=monotonic,
        )
        maintenance = StaffPilotMaintenance(
            pilot_datastore.store,
            config.maintenance,
            operation_lock=operation_lock,
            observer=active_observer,
            clock=clock,
        )
        inner = create_staff_transport_app(
            pilot_datastore.store,
            transport,
            cached_remote,
            clock=clock,
            token_factory=token_factory,
            operation_lock=operation_lock,
        )
        app = StaffPilotApplication(
            inner,
            config,
            pilot_datastore,
            maintenance,
            active_observer,
            operation_lock=operation_lock,
            monotonic=monotonic,
        )
        return StaffPilotRuntime(app, pilot_datastore, maintenance, active_observer)
    except Exception:
        pilot_datastore.close()
        raise


__all__ = ["StaffPilotApplication", "StaffPilotRuntime", "create_staff_pilot_runtime"]
