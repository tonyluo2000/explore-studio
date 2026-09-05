"""Staff-only HTTP transport over the trusted Phase E application services."""

from __future__ import annotations

import json
import re
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import NoReturn
from urllib.parse import urlsplit

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Route

from explore.online.configuration import AuthoritativeClassWorldConfigurationService
from explore.online.configuration_models import (
    ConfigurationAccessDeniedError,
    ConfigurationAuthenticationError,
    ConfigurationConflictError,
    ConfigurationIntegrityError,
    ConfigurationLoadRequest,
)
from explore.online.control_plane import ControlPlaneService
from explore.online.control_plane_models import (
    ControlPlaneAccessDeniedError,
    ControlPlaneAuthenticationError,
    ControlPlaneConflictError,
    MembershipChangeRequest,
    MembershipCreateRequest,
    MembershipRevokeRequest,
    NamespaceClaimRequest,
    NamespaceGrantRequest,
    NamespaceGrantRevokeRequest,
    NamespaceTransferRequest,
)
from explore.online.models import AssuranceLevel, CohortRole
from explore.online.oidc import (
    OIDCAuthenticationError,
    OIDCProtocol,
    OIDCRemote,
    UrllibOIDCRemote,
)
from explore.online.persistence import PersistenceConflictError
from explore.online.pinning import ClassWorldPinningService
from explore.online.pinning_models import (
    ClassWorldPinRequest,
    PinAccessDeniedError,
    PinAuthenticationError,
    PinConfigurationError,
    PinConflictError,
)
from explore.online.registry import ApprovedRegistryService
from explore.online.registry_models import (
    RegistryAccessDeniedError,
    RegistryAuthenticationError,
    RegistryConflictError,
    RegistryExactLookup,
)
from explore.online.session import (
    AuthenticatedStaffSession,
    CSRFValidationError,
    SessionAuthenticationError,
    StaffSessionManager,
)
from explore.online.transport_models import StaffTransportConfig
from explore.online.transport_persistence import SQLiteStaffTransportStore

_CONTROL_CHARACTER = re.compile(r"[\x00-\x1f\x7f]", re.ASCII)
_BOLA_ERRORS = (
    ControlPlaneAccessDeniedError,
    RegistryAccessDeniedError,
    ConfigurationAccessDeniedError,
    PinAccessDeniedError,
)
_AUTHENTICATION_ERRORS = (
    SessionAuthenticationError,
    OIDCAuthenticationError,
    ControlPlaneAuthenticationError,
    RegistryAuthenticationError,
    ConfigurationAuthenticationError,
    PinAuthenticationError,
)
_CONFLICT_ERRORS = (
    ControlPlaneConflictError,
    RegistryConflictError,
    ConfigurationConflictError,
    ConfigurationIntegrityError,
    PinConfigurationError,
    PinConflictError,
    PersistenceConflictError,
)


class TransportRequestError(ValueError):
    def __init__(self, code: str, status_code: int = 400) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class _Runtime:
    store: SQLiteStaffTransportStore
    config: StaffTransportConfig
    oidc: OIDCProtocol
    sessions: StaffSessionManager
    control_plane: ControlPlaneService
    registry: ApprovedRegistryService
    configurations: AuthoritativeClassWorldConfigurationService
    pinning: ClassWorldPinningService
    operation_lock: threading.RLock


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _error(code: str, status_code: int, correlation_id: str | None = None) -> JSONResponse:
    document: dict[str, object] = {"error": {"code": code}}
    if correlation_id is not None:
        document["correlation_id"] = correlation_id
    return JSONResponse(document, status_code=status_code)


def _header(request: Request, name: str, *, required: bool, maximum: int) -> str | None:
    values = request.headers.getlist(name)
    if len(values) > 1:
        raise TransportRequestError("INVALID_REQUEST")
    if not values:
        if required:
            raise TransportRequestError("INVALID_REQUEST")
        return None
    value = values[0]
    if not value or len(value) > maximum or _CONTROL_CHARACTER.search(value) is not None:
        raise TransportRequestError("INVALID_REQUEST")
    return value


def _operation_headers(request: Request) -> tuple[str, str]:
    correlation_id = _header(request, "x-correlation-id", required=True, maximum=128)
    idempotency_key = _header(request, "idempotency-key", required=True, maximum=96)
    assert correlation_id is not None and idempotency_key is not None
    return correlation_id, idempotency_key


def _correlation_for_error(request: Request) -> str | None:
    try:
        return _header(request, "x-correlation-id", required=False, maximum=128)
    except TransportRequestError:
        return None


def _strict_object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise TransportRequestError("INVALID_REQUEST")
        result[key] = value
    return result


def _reject_constant(_value: str) -> NoReturn:
    raise TransportRequestError("INVALID_REQUEST")


async def _bounded_body(request: Request, maximum: int) -> bytes:
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > maximum:
            raise TransportRequestError("REQUEST_TOO_LARGE", 413)
        body.extend(chunk)
    return bytes(body)


async def _json_body(
    request: Request,
    config: StaffTransportConfig,
    *,
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> dict[str, object]:
    content_lengths = request.headers.getlist("content-length")
    if len(content_lengths) > 1:
        raise TransportRequestError("INVALID_REQUEST")
    if content_lengths:
        try:
            content_length = int(content_lengths[0])
        except ValueError as error:
            raise TransportRequestError("INVALID_REQUEST") from error
        if content_length < 0 or content_length > config.max_request_bytes:
            raise TransportRequestError("REQUEST_TOO_LARGE", 413)
    content_type = request.headers.get("content-type", "")
    media_type, _, parameters = content_type.partition(";")
    if media_type.strip().lower() != "application/json":
        raise TransportRequestError("INVALID_REQUEST")
    if parameters and parameters.strip().lower() not in ("charset=utf-8", 'charset="utf-8"'):
        raise TransportRequestError("INVALID_REQUEST")
    body = await _bounded_body(request, config.max_request_bytes)
    try:
        document = json.loads(
            body,
            object_pairs_hook=_strict_object_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise TransportRequestError("INVALID_REQUEST") from error
    if not isinstance(document, dict) or set(document) != required | optional:
        raise TransportRequestError("INVALID_REQUEST")
    if not required.issubset(document):
        raise TransportRequestError("INVALID_REQUEST")
    return document


async def _empty_body(request: Request, config: StaffTransportConfig) -> None:
    content_lengths = request.headers.getlist("content-length")
    if len(content_lengths) > 1:
        raise TransportRequestError("INVALID_REQUEST")
    if content_lengths:
        try:
            content_length = int(content_lengths[0])
        except ValueError as error:
            raise TransportRequestError("INVALID_REQUEST") from error
        if content_length != 0:
            raise TransportRequestError("INVALID_REQUEST")
    body = await _bounded_body(request, config.max_request_bytes)
    if body:
        raise TransportRequestError("INVALID_REQUEST")


def _string(document: dict[str, object], name: str) -> str:
    value = document.get(name)
    if not isinstance(value, str):
        raise TransportRequestError("INVALID_REQUEST")
    return value


def _integer(document: dict[str, object], name: str) -> int:
    value = document.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TransportRequestError("INVALID_REQUEST")
    return value


def _staff_role(document: dict[str, object], name: str = "role") -> CohortRole:
    role = CohortRole(_string(document, name))
    if role not in (CohortRole.TEACHER, CohortRole.COURSE_ADMIN):
        raise TransportRequestError("INVALID_REQUEST")
    return role


def _require_staff_membership(
    store: SQLiteStaffTransportStore,
    *,
    cohort_id: str,
    actor_id: str,
) -> None:
    membership = store.load_membership(cohort_id, actor_id)
    if (
        membership is None
        or not membership.active
        or membership.role not in (CohortRole.TEACHER, CohortRole.COURSE_ADMIN)
    ):
        raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")


def _cookie(request: Request, name: str) -> str | None:
    cookie_headers = request.headers.getlist("cookie")
    if len(cookie_headers) > 1:
        raise SessionAuthenticationError("staff authentication is required")
    occurrences = 0
    if cookie_headers:
        occurrences = sum(
            1
            for component in cookie_headers[0].split(";")
            if component.strip().partition("=")[0] == name
        )
    if occurrences > 1:
        raise SessionAuthenticationError("staff authentication is required")
    value = request.cookies.get(name)
    if value is not None and (not value or len(value) > 512):
        raise SessionAuthenticationError("staff authentication is required")
    return value


def _authenticate(
    request: Request,
    runtime: _Runtime,
    *,
    csrf: bool,
    aal2: bool = True,
) -> AuthenticatedStaffSession:
    with runtime.operation_lock:
        authenticated = runtime.sessions.authenticate(
            _cookie(request, runtime.config.session_cookie_name)
        )
    if aal2:
        runtime.sessions.require_aal2(authenticated)
    if csrf:
        origin = _header(request, "origin", required=True, maximum=2048)
        if origin != runtime.config.allowed_origin:
            raise CSRFValidationError("CSRF validation failed")
        runtime.sessions.verify_csrf(
            authenticated,
            _header(request, "x-csrf-token", required=True, maximum=512),
        )
    return authenticated


def _transition_response(receipt, correlation_id: str) -> JSONResponse:
    transition = receipt.transition
    return JSONResponse(
        {
            "correlation_id": correlation_id,
            "data": {
                "action": transition.action.value,
                "cohort_id": transition.cohort_id,
                "object_id": transition.object_id,
                "object_type": transition.object_type,
                "occurred_at": _iso(transition.occurred_at),
                "replayed": receipt.replayed,
                "transition_id": transition.transition_id,
            },
        }
    )


def create_staff_transport_app(
    store: SQLiteStaffTransportStore,
    config: StaffTransportConfig,
    oidc_remote: OIDCRemote | None = None,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    token_factory=None,
    operation_lock=None,
) -> Starlette:
    """Create the bounded ASGI app; deployment and server selection remain external."""
    if not isinstance(store, SQLiteStaffTransportStore):
        raise TypeError("store must be a SQLiteStaffTransportStore")
    if not isinstance(config, StaffTransportConfig):
        raise TypeError("config must be a StaffTransportConfig")
    token_options = {} if token_factory is None else {"token_factory": token_factory}
    shared_operation_lock = operation_lock or threading.RLock()
    if not callable(getattr(shared_operation_lock, "acquire", None)) or not callable(
        getattr(shared_operation_lock, "release", None)
    ):
        raise TypeError("operation_lock must provide acquire and release")
    remote = oidc_remote or UrllibOIDCRemote(max_response_bytes=config.oidc_response_max_bytes)
    oidc = OIDCProtocol(
        store,
        remote,
        authorization_ttl=config.authorization_ttl,
        id_token_max_age=config.id_token_max_age,
        clock_skew=config.clock_skew,
        clock=clock,
        **token_options,
    )
    sessions = StaffSessionManager(store, config, clock=clock, **token_options)
    runtime = _Runtime(
        store=store,
        config=config,
        oidc=oidc,
        sessions=sessions,
        control_plane=ControlPlaneService(store, clock=clock),
        registry=ApprovedRegistryService(store, clock=clock),
        configurations=AuthoritativeClassWorldConfigurationService(store, clock=clock),
        pinning=ClassWorldPinningService(store, clock=clock),
        operation_lock=shared_operation_lock,
    )

    async def oidc_login(request: Request) -> Response:
        provider = config.provider(request.path_params["provider_id"])
        if provider is None:
            return _error("RESOURCE_NOT_AVAILABLE", 404)
        with runtime.operation_lock:
            if store.identity_provider_assurance(provider.issuer) is not AssuranceLevel.AAL2:
                return _error("RESOURCE_NOT_AVAILABLE", 404)
            started = oidc.start(provider)
        response = RedirectResponse(started.authorization_url, status_code=302)
        response.set_cookie(
            config.transaction_cookie_name,
            started.browser_token,
            max_age=int(config.authorization_ttl.total_seconds()),
            path="/",
            secure=True,
            httponly=True,
            samesite="lax",
        )
        return response

    async def oidc_callback(request: Request) -> Response:
        provider = config.provider(request.path_params["provider_id"])
        if provider is None:
            raise OIDCAuthenticationError("OIDC callback was rejected")
        if set(request.query_params) != {"code", "state"}:
            raise OIDCAuthenticationError("OIDC callback was rejected")
        if (
            len(request.query_params.getlist("code")) != 1
            or len(request.query_params.getlist("state")) != 1
        ):
            raise OIDCAuthenticationError("OIDC callback was rejected")
        with runtime.operation_lock:
            identity = oidc.complete(
                provider,
                code=request.query_params["code"],
                state=request.query_params["state"],
                browser_token=_cookie(request, config.transaction_cookie_name) or "",
            )
            created = sessions.create(identity)
        response = JSONResponse(
            {
                "data": {
                    "actor_id": created.session.actor_id,
                    "assurance": created.session.assurance.value,
                    "csrf_token": created.csrf_token,
                    "expires_at": _iso(created.session.absolute_expires_at),
                }
            }
        )
        response.set_cookie(
            config.session_cookie_name,
            created.session_token,
            max_age=int(config.session_absolute_ttl.total_seconds()),
            path="/",
            secure=True,
            httponly=True,
            samesite="lax",
        )
        response.set_cookie(
            config.csrf_cookie_name,
            created.csrf_token,
            max_age=int(config.session_absolute_ttl.total_seconds()),
            path="/",
            secure=True,
            httponly=False,
            samesite="strict",
        )
        response.delete_cookie(
            config.transaction_cookie_name, path="/", secure=True, httponly=True, samesite="lax"
        )
        return response

    async def session_status(request: Request) -> Response:
        authenticated = _authenticate(request, runtime, csrf=False, aal2=False)
        return JSONResponse(
            {
                "data": {
                    "actor_id": authenticated.session.actor_id,
                    "assurance": authenticated.identity.assurance.value,
                    "expires_at": _iso(authenticated.session.absolute_expires_at),
                }
            }
        )

    async def logout(request: Request) -> Response:
        authenticated = _authenticate(request, runtime, csrf=True, aal2=False)
        await _empty_body(request, config)
        with runtime.operation_lock:
            authenticated = _authenticate(request, runtime, csrf=True, aal2=False)
            sessions.revoke(authenticated)
        response = JSONResponse({"data": {"logged_out": True}})
        response.delete_cookie(
            config.session_cookie_name, path="/", secure=True, httponly=True, samesite="lax"
        )
        response.delete_cookie(
            config.csrf_cookie_name,
            path="/",
            secure=True,
            httponly=False,
            samesite="strict",
        )
        return response

    async def membership_create(request: Request) -> Response:
        authenticated = _authenticate(request, runtime, csrf=True)
        correlation_id, key = _operation_headers(request)
        body = await _json_body(
            request,
            config,
            required=frozenset({"cohort_id", "target_actor_id", "role", "expected_revision"}),
        )
        command = MembershipCreateRequest(
            cohort_id=_string(body, "cohort_id"),
            target_actor_id=_string(body, "target_actor_id"),
            role=_staff_role(body),
            expected_revision=_integer(body, "expected_revision"),
            correlation_id=correlation_id,
            idempotency_key=key,
        )
        with runtime.operation_lock:
            authenticated = _authenticate(request, runtime, csrf=True)
            if not store.actor_is_current_staff(command.target_actor_id, now=clock()):
                raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
            receipt = runtime.control_plane.create_membership(
                identity=authenticated.identity, request=command
            )
        return _transition_response(receipt, correlation_id)

    async def membership_change(request: Request) -> Response:
        authenticated = _authenticate(request, runtime, csrf=True)
        correlation_id, key = _operation_headers(request)
        body = await _json_body(request, config, required=frozenset({"role", "expected_revision"}))
        command = MembershipChangeRequest(
            cohort_id=request.path_params["cohort_id"],
            target_actor_id=request.path_params["actor_id"],
            role=_staff_role(body),
            expected_revision=_integer(body, "expected_revision"),
            correlation_id=correlation_id,
            idempotency_key=key,
        )
        with runtime.operation_lock:
            authenticated = _authenticate(request, runtime, csrf=True)
            _require_staff_membership(
                store,
                cohort_id=command.cohort_id,
                actor_id=command.target_actor_id,
            )
            receipt = runtime.control_plane.change_membership(
                identity=authenticated.identity, request=command
            )
            store.revoke_actor_sessions(actor_id=command.target_actor_id, now=clock())
        return _transition_response(receipt, correlation_id)

    async def membership_revoke(request: Request) -> Response:
        authenticated = _authenticate(request, runtime, csrf=True)
        correlation_id, key = _operation_headers(request)
        body = await _json_body(request, config, required=frozenset({"expected_revision"}))
        command = MembershipRevokeRequest(
            cohort_id=request.path_params["cohort_id"],
            target_actor_id=request.path_params["actor_id"],
            expected_revision=_integer(body, "expected_revision"),
            correlation_id=correlation_id,
            idempotency_key=key,
        )
        with runtime.operation_lock:
            authenticated = _authenticate(request, runtime, csrf=True)
            _require_staff_membership(
                store,
                cohort_id=command.cohort_id,
                actor_id=command.target_actor_id,
            )
            receipt = runtime.control_plane.revoke_membership(
                identity=authenticated.identity, request=command
            )
            store.revoke_actor_sessions(actor_id=command.target_actor_id, now=clock())
        return _transition_response(receipt, correlation_id)

    async def namespace_claim(request: Request) -> Response:
        authenticated = _authenticate(request, runtime, csrf=True)
        correlation_id, key = _operation_headers(request)
        body = await _json_body(
            request,
            config,
            required=frozenset({"cohort_id", "package_id", "owner_actor_id", "expected_revision"}),
        )
        command = NamespaceClaimRequest(
            cohort_id=_string(body, "cohort_id"),
            package_id=_string(body, "package_id"),
            owner_actor_id=_string(body, "owner_actor_id"),
            expected_revision=_integer(body, "expected_revision"),
            correlation_id=correlation_id,
            idempotency_key=key,
        )
        with runtime.operation_lock:
            authenticated = _authenticate(request, runtime, csrf=True)
            _require_staff_membership(
                store,
                cohort_id=command.cohort_id,
                actor_id=command.owner_actor_id,
            )
            receipt = runtime.control_plane.claim_namespace(
                identity=authenticated.identity, request=command
            )
        return _transition_response(receipt, correlation_id)

    async def namespace_grant(request: Request) -> Response:
        authenticated = _authenticate(request, runtime, csrf=True)
        correlation_id, key = _operation_headers(request)
        body = await _json_body(
            request,
            config,
            required=frozenset(
                {"target_actor_id", "expected_namespace_revision", "expected_grant_revision"}
            ),
        )
        command = NamespaceGrantRequest(
            package_id=request.path_params["package_id"],
            target_actor_id=_string(body, "target_actor_id"),
            expected_namespace_revision=_integer(body, "expected_namespace_revision"),
            expected_grant_revision=_integer(body, "expected_grant_revision"),
            correlation_id=correlation_id,
            idempotency_key=key,
        )
        with runtime.operation_lock:
            authenticated = _authenticate(request, runtime, csrf=True)
            namespace = store.load_namespace(command.package_id)
            if namespace is None:
                raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
            _require_staff_membership(
                store,
                cohort_id=namespace.cohort_id,
                actor_id=command.target_actor_id,
            )
            receipt = runtime.control_plane.grant_namespace(
                identity=authenticated.identity, request=command
            )
        return _transition_response(receipt, correlation_id)

    async def namespace_grant_revoke(request: Request) -> Response:
        authenticated = _authenticate(request, runtime, csrf=True)
        correlation_id, key = _operation_headers(request)
        body = await _json_body(
            request,
            config,
            required=frozenset({"expected_namespace_revision", "expected_grant_revision"}),
        )
        command = NamespaceGrantRevokeRequest(
            package_id=request.path_params["package_id"],
            target_actor_id=request.path_params["actor_id"],
            expected_namespace_revision=_integer(body, "expected_namespace_revision"),
            expected_grant_revision=_integer(body, "expected_grant_revision"),
            correlation_id=correlation_id,
            idempotency_key=key,
        )
        with runtime.operation_lock:
            authenticated = _authenticate(request, runtime, csrf=True)
            namespace = store.load_namespace(command.package_id)
            if namespace is None:
                raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
            _require_staff_membership(
                store,
                cohort_id=namespace.cohort_id,
                actor_id=command.target_actor_id,
            )
            receipt = runtime.control_plane.revoke_namespace_grant(
                identity=authenticated.identity, request=command
            )
        return _transition_response(receipt, correlation_id)

    async def namespace_transfer(request: Request) -> Response:
        authenticated = _authenticate(request, runtime, csrf=True)
        correlation_id, key = _operation_headers(request)
        body = await _json_body(
            request,
            config,
            required=frozenset({"new_owner_actor_id", "expected_revision"}),
        )
        command = NamespaceTransferRequest(
            package_id=request.path_params["package_id"],
            new_owner_actor_id=_string(body, "new_owner_actor_id"),
            expected_revision=_integer(body, "expected_revision"),
            correlation_id=correlation_id,
            idempotency_key=key,
        )
        with runtime.operation_lock:
            authenticated = _authenticate(request, runtime, csrf=True)
            namespace = store.load_namespace(command.package_id)
            if namespace is None:
                raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
            _require_staff_membership(
                store,
                cohort_id=namespace.cohort_id,
                actor_id=command.new_owner_actor_id,
            )
            receipt = runtime.control_plane.transfer_namespace(
                identity=authenticated.identity, request=command
            )
        return _transition_response(receipt, correlation_id)

    async def registry_exact(request: Request) -> Response:
        authenticated = _authenticate(request, runtime, csrf=False)
        correlation_id, key = _operation_headers(request)
        lookup = RegistryExactLookup(
            package_id=request.path_params["package_id"],
            semantic_version=request.path_params["semantic_version"],
            correlation_id=correlation_id,
            idempotency_key=key,
        )
        with runtime.operation_lock:
            authenticated = _authenticate(request, runtime, csrf=False)
            receipt = runtime.registry.read_exact(identity=authenticated.identity, lookup=lookup)
        entry = receipt.entry
        return JSONResponse(
            {
                "correlation_id": correlation_id,
                "data": {
                    "approval_decision_id": entry.approval_decision_id,
                    "approved_at": _iso(entry.approved_at),
                    "artifact_reference": entry.artifact_reference,
                    "cohort_id": entry.cohort_id,
                    "package_id": entry.package_version.package_id,
                    "raw_zip_sha256": entry.package_version.raw_zip_sha256,
                    "replayed": receipt.replayed,
                    "semantic_version": entry.package_version.package_version,
                    "student_api_version": entry.compatibility.student_api_version,
                },
            }
        )

    async def pin_exact(request: Request) -> Response:
        authenticated = _authenticate(request, runtime, csrf=True)
        correlation_id, key = _operation_headers(request)
        body = await _json_body(
            request,
            config,
            required=frozenset({"configuration_locator", "package_id", "semantic_version"}),
        )
        locator = _string(body, "configuration_locator")
        package_id = _string(body, "package_id")
        semantic_version = _string(body, "semantic_version")
        with runtime.operation_lock:
            authenticated = _authenticate(request, runtime, csrf=True)
            loaded = runtime.configurations.load_for_pinning(
                identity=authenticated.identity,
                request=ConfigurationLoadRequest(locator, correlation_id, f"{key}:load"),
            )
            receipt = runtime.pinning.pin_exact(
                identity=authenticated.identity,
                configuration=loaded.loaded,
                request=ClassWorldPinRequest(
                    package_id,
                    semantic_version,
                    correlation_id,
                    f"{key}:pin",
                ),
            )
        pin = receipt.pin
        return JSONResponse(
            {
                "correlation_id": correlation_id,
                "data": {
                    "approval_decision_id": pin.approval_decision_id,
                    "class_world_id": pin.class_world_id,
                    "class_world_version": pin.class_world_version,
                    "cohort_id": pin.cohort_id,
                    "configuration_sha256": pin.configuration_sha256,
                    "package_id": pin.package_version.package_id,
                    "pin_id": pin.pin_id,
                    "pinned_at": _iso(pin.pinned_at),
                    "raw_zip_sha256": pin.package_version.raw_zip_sha256,
                    "replayed": receipt.replayed,
                    "semantic_version": pin.package_version.package_version,
                },
            }
        )

    routes = [
        Route("/staff/oidc/login/{provider_id}", oidc_login, methods=["GET"]),
        Route("/staff/oidc/callback/{provider_id}", oidc_callback, methods=["GET"]),
        Route("/staff/session", session_status, methods=["GET"]),
        Route("/staff/logout", logout, methods=["POST"]),
        Route("/staff/control-plane/memberships", membership_create, methods=["POST"]),
        Route(
            "/staff/control-plane/memberships/{cohort_id}/{actor_id}",
            membership_change,
            methods=["PATCH"],
        ),
        Route(
            "/staff/control-plane/memberships/{cohort_id}/{actor_id}",
            membership_revoke,
            methods=["DELETE"],
        ),
        Route("/staff/control-plane/namespaces", namespace_claim, methods=["POST"]),
        Route(
            "/staff/control-plane/namespaces/{package_id}/grants",
            namespace_grant,
            methods=["POST"],
        ),
        Route(
            "/staff/control-plane/namespaces/{package_id}/grants/{actor_id}",
            namespace_grant_revoke,
            methods=["DELETE"],
        ),
        Route(
            "/staff/control-plane/namespaces/{package_id}/transfer",
            namespace_transfer,
            methods=["POST"],
        ),
        Route(
            "/staff/registry/{package_id}/{semantic_version}",
            registry_exact,
            methods=["GET"],
        ),
        Route("/staff/pins", pin_exact, methods=["POST"]),
    ]
    app = Starlette(routes=routes)

    async def transport_error(request: Request, error: TransportRequestError) -> JSONResponse:
        return _error(error.code, error.status_code, _correlation_for_error(request))

    async def csrf_error(request: Request, _error_value: CSRFValidationError) -> JSONResponse:
        return _error("REQUEST_NOT_AUTHORIZED", 403, _correlation_for_error(request))

    async def mapped_error(request: Request, error: Exception) -> JSONResponse:
        correlation_id = _correlation_for_error(request)
        if isinstance(error, _BOLA_ERRORS):
            return _error("RESOURCE_NOT_AVAILABLE", 404, correlation_id)
        if isinstance(error, _AUTHENTICATION_ERRORS):
            return _error("AUTHENTICATION_REQUIRED", 401, correlation_id)
        if isinstance(error, _CONFLICT_ERRORS):
            return _error("CONFLICT", 409, correlation_id)
        if isinstance(error, (ValueError, TypeError, KeyError)):
            return _error("INVALID_REQUEST", 400, correlation_id)
        return _error("INTERNAL_ERROR", 500, correlation_id)

    async def framework_error(request: Request, error: HTTPException) -> JSONResponse:
        if error.status_code == 404:
            return _error("RESOURCE_NOT_AVAILABLE", 404, _correlation_for_error(request))
        if error.status_code == 405:
            return _error("INVALID_REQUEST", 405, _correlation_for_error(request))
        return _error("INVALID_REQUEST", error.status_code, _correlation_for_error(request))

    app.add_exception_handler(TransportRequestError, transport_error)
    app.add_exception_handler(CSRFValidationError, csrf_error)
    app.add_exception_handler(HTTPException, framework_error)
    for handled_error in (
        *_BOLA_ERRORS,
        *_AUTHENTICATION_ERRORS,
        *_CONFLICT_ERRORS,
        ValueError,
        TypeError,
        KeyError,
    ):
        app.add_exception_handler(handled_error, mapped_error)
    app.add_exception_handler(Exception, mapped_error)

    async def security_headers(request: Request, call_next) -> Response:
        host_headers = request.headers.getlist("host")
        invalid_shape = (
            request.url.scheme != "https"
            or len(host_headers) != 1
            or host_headers[0] != urlsplit(config.allowed_origin).netloc
            or (
                bool(request.url.query) and not request.url.path.startswith("/staff/oidc/callback/")
            )
            or (
                request.method in ("GET", "HEAD")
                and request.headers.get("content-length") not in (None, "0")
            )
        )
        if invalid_shape:
            response = _error(
                "INVALID_REQUEST",
                400,
                _correlation_for_error(request),
            )
        else:
            response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=security_headers)

    return app


__all__ = ["TransportRequestError", "create_staff_transport_app"]
