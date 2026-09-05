"""Centrally authorized exact-version reads from the approved registry."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from explore.online.authorization import AuthorizationAction, AuthorizationResource, authorize
from explore.online.models import AuditEvent, IdempotencyRecord, PrincipalKind
from explore.online.persistence import PersistenceConflictError
from explore.online.registry_models import (
    ApprovedRegistryEntry,
    RegistryAccessDeniedError,
    RegistryAuthenticationError,
    RegistryConflictError,
    RegistryExactLookup,
    RegistryReadReceipt,
)
from explore.online.registry_persistence import SQLiteRegistryStore
from explore.online.submission_models import AuthenticatedOIDCIdentity

_REGISTRY_READ_OPERATION = "registry.read-exact"
_AUDIT_EVENT_TYPE = "registry.read"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _add_calendar_years(value: datetime, years: int) -> datetime:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def _request_sha256(request: RegistryExactLookup) -> str:
    document = {
        "correlation_id": request.correlation_id,
        "package_id": request.package_id,
        "semantic_version": request.semantic_version,
    }
    canonical = json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ApprovedRegistryService:
    """Read an authoritative currently approved projection and audit it atomically."""

    def __init__(
        self,
        store: SQLiteRegistryStore,
        *,
        clock: Callable[[], datetime] = _utc_now,
        uuid_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        if not isinstance(store, SQLiteRegistryStore):
            raise TypeError("store must be a SQLiteRegistryStore")
        if not callable(clock) or not callable(uuid_factory):
            raise TypeError("clock and uuid_factory must be callable")
        self._store = store
        self._clock = clock
        self._uuid_factory = uuid_factory

    def _actor_id(self, identity: AuthenticatedOIDCIdentity) -> str:
        if not isinstance(identity, AuthenticatedOIDCIdentity):
            raise TypeError("identity must be an AuthenticatedOIDCIdentity")
        actor = self._store.resolve_federated_actor(identity.issuer, identity.subject)
        if actor is None:
            raise RegistryAuthenticationError("authenticated identity is not bound")
        return actor.actor_id

    def _load_authorized(
        self,
        *,
        actor_id: str,
        identity: AuthenticatedOIDCIdentity,
        request: RegistryExactLookup,
    ) -> ApprovedRegistryEntry:
        entry = self._store.project_approved_entry(
            request.package_id,
            request.semantic_version,
        )
        if entry is None:
            raise RegistryAccessDeniedError("registry entry is not available")
        principal = self._store.load_human_principal(actor_id, identity.assurance)
        decision = authorize(
            principal,
            AuthorizationAction.REGISTRY_READ,
            AuthorizationResource(
                cohort_id=entry.cohort_id,
                package_id=entry.package_version.package_id,
                package_version=entry.package_version,
                owner_actor_id=entry.owner_actor_id,
                approved=True,
                revoked=False,
            ),
        )
        if not decision.allowed:
            raise RegistryAccessDeniedError("registry entry is not available")
        return entry

    def read_exact(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        lookup: RegistryExactLookup,
    ) -> RegistryReadReceipt:
        """Return one authorized exact approved entry; never list or resolve latest."""
        if not isinstance(lookup, RegistryExactLookup):
            raise TypeError("lookup must be a RegistryExactLookup")
        actor_id = self._actor_id(identity)
        request_sha256 = _request_sha256(lookup)
        now = self._clock()
        if (
            not isinstance(now, datetime)
            or now.tzinfo is None
            or now.utcoffset() != UTC.utcoffset(now)
        ):
            raise RuntimeError("trusted clock must return a timezone-aware UTC datetime")

        try:
            with self._store.transaction():
                locked_actor_id = self._actor_id(identity)
                if locked_actor_id != actor_id:
                    raise RegistryAuthenticationError("authenticated identity changed")
                prior = self._store.load_idempotency_record(
                    principal_kind=PrincipalKind.ACTOR,
                    principal_id=actor_id,
                    operation=_REGISTRY_READ_OPERATION,
                    idempotency_key=lookup.idempotency_key,
                )
                if prior is not None and prior.request_sha256 != request_sha256:
                    raise RegistryConflictError(
                        "idempotency key conflicts with prior registry read"
                    )

                entry = self._load_authorized(
                    actor_id=actor_id,
                    identity=identity,
                    request=lookup,
                )
                if prior is not None:
                    if prior.result_reference != entry.approval_decision_id:
                        raise RegistryConflictError(
                            "registry projection conflicts with prior read result"
                        )
                    return RegistryReadReceipt(entry, replayed=True)

                closes_at = self._store.load_cohort_closes_at(entry.cohort_id)
                if closes_at is None:
                    raise RegistryAccessDeniedError("registry entry is not available")
                audit_details = json.dumps(
                    {
                        "approval_decision_id": entry.approval_decision_id,
                        "artifact_reference": entry.artifact_reference,
                        "compatibility": {
                            "student_api_version": entry.compatibility.student_api_version
                        },
                        "correlation_id": lookup.correlation_id,
                        "owner_actor_id": entry.owner_actor_id,
                        "package_id": entry.package_version.package_id,
                        "raw_zip_sha256": entry.package_version.raw_zip_sha256,
                        "scope": entry.scope.value,
                        "semantic_version": entry.package_version.package_version,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                self._store.append_audit_event(
                    AuditEvent(
                        event_id=str(self._uuid_factory()),
                        occurred_at=now,
                        retention_until=_add_calendar_years(max(closes_at, now), 2),
                        principal_kind=PrincipalKind.ACTOR,
                        principal_id=actor_id,
                        event_type=_AUDIT_EVENT_TYPE,
                        object_type="approved-package-version",
                        object_id=entry.approval_decision_id,
                        cohort_id=entry.cohort_id,
                        idempotency_key=lookup.idempotency_key,
                        details_json=audit_details,
                    )
                )
                self._store.record_idempotent_result(
                    IdempotencyRecord(
                        principal_kind=PrincipalKind.ACTOR,
                        principal_id=actor_id,
                        operation=_REGISTRY_READ_OPERATION,
                        idempotency_key=lookup.idempotency_key,
                        request_sha256=request_sha256,
                        result_reference=entry.approval_decision_id,
                        created_at=now,
                    )
                )
        except PersistenceConflictError as error:
            raise RegistryConflictError(str(error)) from error

        return RegistryReadReceipt(entry, replayed=False)


__all__ = ["ApprovedRegistryService"]
