"""Course-admin adapter for exact approved-version Class-World pins."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from explore.online.authorization import AuthorizationAction, AuthorizationResource, authorize
from explore.online.configuration_models import AuthoritativeClassWorldConfiguration
from explore.online.configuration_persistence import SQLiteClassWorldConfigurationStore
from explore.online.models import (
    AuditEvent,
    CohortMembership,
    CohortRole,
    IdempotencyRecord,
    PrincipalKind,
)
from explore.online.persistence import PersistenceConflictError
from explore.online.pinning_models import (
    ClassWorldPackagePinRecord,
    ClassWorldPinReceipt,
    ClassWorldPinRequest,
    PinAccessDeniedError,
    PinAuthenticationError,
    PinAuthoritySnapshot,
    PinConfigurationError,
    PinConflictError,
)
from explore.online.registry_models import ApprovedRegistryEntry
from explore.online.submission_models import AuthenticatedOIDCIdentity
from explore.packages import ClassWorldConfiguration, serialize_class_world_manifest

_PIN_OPERATION = "class-world.pin-exact"
_AUDIT_EVENT_TYPE = "class-world.pin"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _add_calendar_years(value: datetime, years: int) -> datetime:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def _configuration_digest(configuration: ClassWorldConfiguration) -> str:
    try:
        canonical = serialize_class_world_manifest(configuration)
    except (TypeError, ValueError) as error:
        raise PinConfigurationError("configuration must be authoritative and valid") from error
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _request_sha256(
    configuration: ClassWorldConfiguration,
    configuration_sha256: str,
    request: ClassWorldPinRequest,
) -> str:
    document = {
        "class_world_id": configuration.class_world_id,
        "class_world_version": configuration.class_world_version,
        "configuration_sha256": configuration_sha256,
        "correlation_id": request.correlation_id,
        "package_id": request.package_id,
        "semantic_version": request.semantic_version,
    }
    canonical = json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _binding_matches(
    pin: ClassWorldPackagePinRecord,
    configuration: ClassWorldConfiguration,
    configuration_sha256: str,
    entry: ApprovedRegistryEntry,
) -> bool:
    return (
        pin.configuration_identity == configuration.identity
        and pin.configuration_sha256 == configuration_sha256
        and pin.package_version == entry.package_version
        and pin.cohort_id == entry.cohort_id
        and pin.owner_actor_id == entry.owner_actor_id
        and pin.compatibility == entry.compatibility
        and pin.artifact_reference == entry.artifact_reference
        and pin.approval_decision_id == entry.approval_decision_id
    )


class ClassWorldPinningService:
    """Authorize and atomically append exact immutable Class-World pin evidence."""

    def __init__(
        self,
        store: SQLiteClassWorldConfigurationStore,
        *,
        clock: Callable[[], datetime] = _utc_now,
        uuid_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        if not isinstance(store, SQLiteClassWorldConfigurationStore):
            raise TypeError("store must be a SQLiteClassWorldConfigurationStore")
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
            raise PinAuthenticationError("authenticated identity is not bound")
        return actor.actor_id

    def _authorize(
        self,
        *,
        actor_id: str,
        identity: AuthenticatedOIDCIdentity,
        configuration: ClassWorldConfiguration,
        request: ClassWorldPinRequest,
    ) -> tuple[ApprovedRegistryEntry, CohortMembership]:
        entry = self._store.project_approved_entry(
            request.package_id,
            request.semantic_version,
        )
        if (
            entry is None
            or configuration.cohort.cohort_id != entry.cohort_id
            or configuration.student_api_version != entry.compatibility.student_api_version
        ):
            raise PinAccessDeniedError("class-world pin is not authorized")
        principal = self._store.load_human_principal(actor_id, identity.assurance)
        membership = next(
            (
                candidate
                for candidate in principal.memberships
                if candidate.cohort_id == entry.cohort_id and candidate.active
            ),
            None,
        )
        if membership is None or membership.role is not CohortRole.COURSE_ADMIN:
            raise PinAccessDeniedError("class-world pin is not authorized")
        policy = authorize(
            principal,
            AuthorizationAction.PIN,
            AuthorizationResource(
                cohort_id=entry.cohort_id,
                package_id=entry.package_version.package_id,
                package_version=entry.package_version,
                owner_actor_id=entry.owner_actor_id,
                approved=True,
                revoked=False,
            ),
        )
        if not policy.allowed:
            raise PinAccessDeniedError("class-world pin is not authorized")
        return entry, membership

    def _audit_and_record_result(
        self,
        *,
        actor_id: str,
        pin: ClassWorldPackagePinRecord,
        request_sha256: str,
        now: datetime,
        replayed: bool,
    ) -> None:
        closes_at = self._store.load_cohort_closes_at(pin.cohort_id)
        if closes_at is None:
            raise PinAccessDeniedError("class-world pin is not authorized")
        details = json.dumps(
            {
                "approval_decision_id": pin.approval_decision_id,
                "artifact_reference": pin.artifact_reference,
                "class_world_id": pin.class_world_id,
                "class_world_version": pin.class_world_version,
                "configuration_sha256": pin.configuration_sha256,
                "correlation_id": pin.correlation_id,
                "package_id": pin.package_version.package_id,
                "raw_zip_sha256": pin.package_version.raw_zip_sha256,
                "reused_existing_pin": replayed,
                "semantic_version": pin.package_version.package_version,
                "student_api_version": pin.compatibility.student_api_version,
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
                object_type="class-world-package-pin",
                object_id=pin.pin_id,
                cohort_id=pin.cohort_id,
                idempotency_key=pin.idempotency_key,
                details_json=details,
            )
        )
        self._store.record_idempotent_result(
            IdempotencyRecord(
                principal_kind=PrincipalKind.ACTOR,
                principal_id=actor_id,
                operation=_PIN_OPERATION,
                idempotency_key=pin.idempotency_key,
                request_sha256=request_sha256,
                result_reference=pin.pin_id,
                created_at=now,
            )
        )

    def pin_exact(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        configuration: AuthoritativeClassWorldConfiguration,
        request: ClassWorldPinRequest,
    ) -> ClassWorldPinReceipt:
        """Bind one existing configuration pin to a currently approved exact version."""
        if not isinstance(request, ClassWorldPinRequest):
            raise TypeError("request must be a ClassWorldPinRequest")
        if not isinstance(configuration, AuthoritativeClassWorldConfiguration):
            raise TypeError(
                "configuration must be an AuthoritativeClassWorldConfiguration loaded by the server"
            )
        authoritative_record = self._store.load_configuration_record(configuration.record.locator)
        if authoritative_record != configuration.record:
            raise PinConfigurationError("configuration is not authoritative server state")
        validated_configuration = configuration.configuration
        configuration_sha256 = _configuration_digest(validated_configuration)
        if configuration_sha256 != authoritative_record.configuration_sha256:
            raise PinConfigurationError("configuration digest does not match authoritative state")
        if not any(
            pin.package_id == request.package_id and pin.package_version == request.semantic_version
            for pin in validated_configuration.packages
        ):
            raise PinConfigurationError(
                "configuration does not contain the requested exact package pin"
            )
        actor_id = self._actor_id(identity)
        request_sha256 = _request_sha256(
            validated_configuration,
            configuration_sha256,
            request,
        )
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
                    raise PinAuthenticationError("authenticated identity changed")
                prior = self._store.load_idempotency_record(
                    principal_kind=PrincipalKind.ACTOR,
                    principal_id=actor_id,
                    operation=_PIN_OPERATION,
                    idempotency_key=request.idempotency_key,
                )
                if prior is not None and prior.request_sha256 != request_sha256:
                    raise PinConflictError("idempotency key conflicts with prior pin request")

                entry, membership = self._authorize(
                    actor_id=actor_id,
                    identity=identity,
                    configuration=validated_configuration,
                    request=request,
                )
                binding = self._store.load_class_world_configuration_binding(
                    validated_configuration.class_world_id,
                    validated_configuration.class_world_version,
                )
                if binding is None or (
                    binding.configuration_sha256 != configuration_sha256
                    or binding.cohort_id != entry.cohort_id
                    or binding.student_api_version != entry.compatibility.student_api_version
                ):
                    raise PinConfigurationError(
                        "configuration is not bound to authoritative server state"
                    )
                existing = self._store.load_class_world_pin(
                    validated_configuration.class_world_id,
                    validated_configuration.class_world_version,
                    request.package_id,
                )
                if existing is not None:
                    if not _binding_matches(
                        existing,
                        validated_configuration,
                        configuration_sha256,
                        entry,
                    ):
                        raise PinConflictError(
                            "configuration/package identity already has a different pin"
                        )
                    if prior is not None:
                        if prior.result_reference != existing.pin_id:
                            raise PinConflictError(
                                "idempotency result conflicts with immutable pin identity"
                            )
                        return ClassWorldPinReceipt(existing, replayed=True)
                    duplicate = ClassWorldPackagePinRecord(
                        pin_id=existing.pin_id,
                        class_world_id=existing.class_world_id,
                        class_world_version=existing.class_world_version,
                        configuration_sha256=existing.configuration_sha256,
                        package_version=existing.package_version,
                        cohort_id=existing.cohort_id,
                        owner_actor_id=existing.owner_actor_id,
                        compatibility=existing.compatibility,
                        artifact_reference=existing.artifact_reference,
                        approval_decision_id=existing.approval_decision_id,
                        authority=existing.authority,
                        pinned_at=existing.pinned_at,
                        correlation_id=request.correlation_id,
                        idempotency_key=request.idempotency_key,
                    )
                    self._audit_and_record_result(
                        actor_id=actor_id,
                        pin=duplicate,
                        request_sha256=request_sha256,
                        now=now,
                        replayed=True,
                    )
                    return ClassWorldPinReceipt(existing, replayed=True)

                if prior is not None:
                    raise PinConflictError("idempotency result references a missing pin")
                authority = PinAuthoritySnapshot(
                    cohort_id=membership.cohort_id,
                    actor_id=membership.actor_id,
                    role=membership.role,
                    assurance=identity.assurance,
                    granted_by_actor_id=membership.granted_by_actor_id,
                    granted_at=membership.granted_at,
                    revision=membership.revision,
                    active=membership.active,
                )
                pin = ClassWorldPackagePinRecord(
                    pin_id=str(self._uuid_factory()),
                    class_world_id=validated_configuration.class_world_id,
                    class_world_version=validated_configuration.class_world_version,
                    configuration_sha256=configuration_sha256,
                    package_version=entry.package_version,
                    cohort_id=entry.cohort_id,
                    owner_actor_id=entry.owner_actor_id,
                    compatibility=entry.compatibility,
                    artifact_reference=entry.artifact_reference,
                    approval_decision_id=entry.approval_decision_id,
                    authority=authority,
                    pinned_at=now,
                    correlation_id=request.correlation_id,
                    idempotency_key=request.idempotency_key,
                )
                self._store.append_class_world_pin(pin)
                self._audit_and_record_result(
                    actor_id=actor_id,
                    pin=pin,
                    request_sha256=request_sha256,
                    now=now,
                    replayed=False,
                )
        except PersistenceConflictError as error:
            raise PinConflictError(str(error)) from error

        return ClassWorldPinReceipt(pin, replayed=False)


__all__ = ["ClassWorldPinningService"]
