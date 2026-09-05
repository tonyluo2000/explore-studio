"""Authoritative persistence and loading of immutable Class-World configurations."""

from __future__ import annotations

import hashlib
import io
import json
import tempfile
import zipfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from uuid import UUID, uuid4

from explore.online.authorization import AuthorizationAction, AuthorizationResource, authorize
from explore.online.configuration_models import (
    AuthoritativeClassWorldConfiguration,
    ConfigurationAccessDeniedError,
    ConfigurationAuthenticationError,
    ConfigurationAuthoritySnapshot,
    ConfigurationConflictError,
    ConfigurationCreateReceipt,
    ConfigurationCreateRequest,
    ConfigurationIntegrityError,
    ConfigurationLoadReceipt,
    ConfigurationLoadRequest,
    PreparedClassWorldConfiguration,
    StoredClassWorldConfiguration,
    _loaded,
    _prepared,
)
from explore.online.configuration_persistence import (
    SQLiteClassWorldConfigurationStore,
    StoredPackageArtifact,
)
from explore.online.models import (
    AuditEvent,
    CohortRole,
    IdempotencyRecord,
    PrincipalKind,
)
from explore.online.persistence import PersistenceConflictError
from explore.online.pinning_models import ClassWorldConfigurationBinding
from explore.online.submission_models import AuthenticatedOIDCIdentity
from explore.online.submission_verification import verify_submitted_archive
from explore.packages import (
    MAX_CLASS_WORLD_MANIFEST_BYTES,
    ClassWorldConfiguration,
    PackageSelection,
    StudentAPIRegistrationPlan,
    build_package_set_plan,
    load_explorer_package,
    parse_class_world_manifest,
    plan_loaded_explorer_package,
    serialize_class_world_manifest,
)

_CREATE_OPERATION = "class-world.configuration-create"
_READ_OPERATION = "class-world.configuration-read-for-pinning"
_CREATE_EVENT = "class-world.configuration-create"
_READ_EVENT = "class-world.configuration-read"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _add_calendar_years(value: datetime, years: int) -> datetime:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _request_sha256(operation: str, document: dict[str, object]) -> str:
    return hashlib.sha256(
        _canonical_json({"operation": operation, **document}).encode("utf-8")
    ).hexdigest()


def prepare_class_world_configuration(
    configuration: ClassWorldConfiguration,
) -> PreparedClassWorldConfiguration:
    """Canonicalize a trusted existing Class-World configuration for persistence.

    This is an internal boundary for a future server-owned configuration workflow,
    not a request parser. The existing serializer remains the sole byte authority.
    """
    try:
        canonical_bytes = serialize_class_world_manifest(configuration).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as error:
        raise ConfigurationIntegrityError(
            "configuration failed canonical Class-World validation"
        ) from error
    if len(canonical_bytes) > MAX_CLASS_WORLD_MANIFEST_BYTES:
        raise ConfigurationIntegrityError("canonical configuration exceeds the manifest limit")
    return _prepared(
        configuration,
        canonical_bytes,
        hashlib.sha256(canonical_bytes).hexdigest(),
    )


def _safe_member_path(value: str) -> PurePosixPath | None:
    candidate = PurePosixPath(value)
    if (
        not value
        or candidate.is_absolute()
        or "\\" in value
        or any(part in ("", ".", "..") for part in candidate.parts)
    ):
        return None
    return candidate


def _registration_plan(source: StoredPackageArtifact) -> StudentAPIRegistrationPlan:
    filename = f"{source.package_id}-{source.package_version}.explorer-package.zip"
    if hashlib.sha256(source.archive_bytes).hexdigest() != source.raw_zip_sha256:
        raise ConfigurationIntegrityError("stored package artifact digest mismatch")
    verification = verify_submitted_archive(filename, source.archive_bytes)
    verified = verification.archive
    if (
        not verification.is_valid
        or verified is None
        or verified.package_id != source.package_id
        or verified.semantic_version != source.package_version
        or verified.raw_archive_sha256 != source.raw_zip_sha256
    ):
        raise ConfigurationIntegrityError("stored package artifact failed revalidation")

    try:
        with tempfile.TemporaryDirectory(prefix="explore-configuration-") as directory:
            root = Path(directory)
            with zipfile.ZipFile(
                io.BytesIO(source.archive_bytes), "r", allowZip64=False
            ) as archive:
                for info in archive.infolist():
                    safe_path = _safe_member_path(info.filename)
                    if safe_path is None:
                        raise ConfigurationIntegrityError(
                            "stored package artifact contains an unsafe path"
                        )
                    target = root.joinpath(*safe_path.parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(info))
            planned = plan_loaded_explorer_package(load_explorer_package(root))
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as error:
        if isinstance(error, ConfigurationIntegrityError):
            raise
        raise ConfigurationIntegrityError(
            "stored package artifact could not be reconstructed"
        ) from error
    if planned.plan is None or planned.issues or planned.loader_diagnostics:
        raise ConfigurationIntegrityError("stored package artifact could not be planned")
    return planned.plan


class AuthoritativeClassWorldConfigurationService:
    """Create and load immutable configurations through server-owned state only."""

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

    def _now(self) -> datetime:
        value = self._clock()
        if (
            not isinstance(value, datetime)
            or value.tzinfo is None
            or value.utcoffset() != UTC.utcoffset(value)
        ):
            raise RuntimeError("trusted clock must return a timezone-aware UTC datetime")
        return value

    def _actor_id(self, identity: AuthenticatedOIDCIdentity) -> str:
        if not isinstance(identity, AuthenticatedOIDCIdentity):
            raise TypeError("identity must be an AuthenticatedOIDCIdentity")
        actor = self._store.resolve_federated_actor(identity.issuer, identity.subject)
        if actor is None:
            raise ConfigurationAuthenticationError("authenticated identity is not bound")
        return actor.actor_id

    def _authority(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        actor_id: str,
        cohort_id: str,
    ) -> ConfigurationAuthoritySnapshot:
        principal = self._store.load_human_principal(actor_id, identity.assurance)
        decision = authorize(
            principal,
            AuthorizationAction.CONFIGURE,
            AuthorizationResource(cohort_id=cohort_id),
        )
        membership = next(
            (
                item
                for item in principal.memberships
                if item.cohort_id == cohort_id
                and item.active
                and item.role is CohortRole.COURSE_ADMIN
            ),
            None,
        )
        if not decision.allowed or membership is None:
            raise ConfigurationAccessDeniedError("configuration is not available")
        return ConfigurationAuthoritySnapshot(
            cohort_id=membership.cohort_id,
            actor_id=membership.actor_id,
            role=membership.role,
            assurance=identity.assurance,
            granted_by_actor_id=membership.granted_by_actor_id,
            granted_at=membership.granted_at,
            revision=membership.revision,
            active=membership.active,
        )

    def _append_audit(
        self,
        *,
        record: StoredClassWorldConfiguration,
        actor_id: str,
        occurred_at: datetime,
        event_type: str,
        correlation_id: str,
        idempotency_key: str,
        replayed_existing: bool,
    ) -> None:
        closes_at = self._store.load_cohort_closes_at(record.cohort_id)
        if closes_at is None:
            raise ConfigurationAccessDeniedError("configuration is not available")
        details = _canonical_json(
            {
                "class_world_id": record.class_world_id,
                "class_world_version": record.class_world_version,
                "configuration_sha256": record.configuration_sha256,
                "correlation_id": correlation_id,
                "locator": record.locator,
                "purpose": "pinning" if event_type == _READ_EVENT else "configuration-create",
                "reused_existing_configuration": replayed_existing,
                "student_api_version": record.student_api_version,
            }
        )
        self._store.append_audit_event(
            AuditEvent(
                event_id=str(self._uuid_factory()),
                occurred_at=occurred_at,
                retention_until=_add_calendar_years(max(closes_at, occurred_at), 2),
                principal_kind=PrincipalKind.ACTOR,
                principal_id=actor_id,
                event_type=event_type,
                object_type="class-world-configuration",
                object_id=record.locator,
                cohort_id=record.cohort_id,
                idempotency_key=idempotency_key,
                details_json=details,
            )
        )

    def _reconstruct(
        self,
        record: StoredClassWorldConfiguration,
    ) -> AuthoritativeClassWorldConfiguration:
        canonical = record.canonical_bytes
        if (
            not canonical
            or len(canonical) > MAX_CLASS_WORLD_MANIFEST_BYTES
            or hashlib.sha256(canonical).hexdigest() != record.configuration_sha256
        ):
            raise ConfigurationIntegrityError("stored configuration digest mismatch")
        try:
            text = canonical.decode("utf-8", errors="strict")
            document = json.loads(text)
            package_documents = document["packages"]
            pins = tuple((item["id"], item["version"]) for item in package_documents)
        except (UnicodeDecodeError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
            raise ConfigurationIntegrityError(
                "stored configuration is not canonical JSON"
            ) from error
        if not pins:
            raise ConfigurationIntegrityError("stored configuration contains no exact package pins")

        selections: list[PackageSelection] = []
        for package_id, package_version in pins:
            if not isinstance(package_id, str) or not isinstance(package_version, str):
                raise ConfigurationIntegrityError("stored configuration package pin is invalid")
            source = self._store.load_exact_package_artifact(package_id, package_version)
            if source is None or source.cohort_id != record.cohort_id:
                raise ConfigurationIntegrityError(
                    "stored configuration package source is absent or cross-cohort"
                )
            plan = _registration_plan(source)
            selections.append(PackageSelection(package_id, package_version, plan))
        planned = build_package_set_plan(tuple(selections))
        if not planned.is_planned or planned.plan is None:
            raise ConfigurationIntegrityError("stored configuration package set failed preflight")
        parsed = parse_class_world_manifest(text, planned.plan)
        configuration = parsed.configuration
        if not parsed.is_parsed or configuration is None:
            raise ConfigurationIntegrityError("stored configuration failed Class-World parsing")
        try:
            rebuilt = serialize_class_world_manifest(configuration).encode("utf-8")
        except (TypeError, ValueError, UnicodeEncodeError) as error:
            raise ConfigurationIntegrityError(
                "stored configuration failed canonical reconstruction"
            ) from error
        if (
            rebuilt != canonical
            or configuration.identity != record.identity
            or configuration.cohort.cohort_id != record.cohort_id
            or configuration.student_api_version != record.student_api_version
        ):
            raise ConfigurationIntegrityError(
                "stored configuration does not match its immutable identity and scope"
            )
        return _loaded(record, configuration)

    def create(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        prepared: PreparedClassWorldConfiguration,
        request: ConfigurationCreateRequest,
    ) -> ConfigurationCreateReceipt:
        """Persist one trusted canonical configuration at immutable revision zero."""
        if not isinstance(prepared, PreparedClassWorldConfiguration):
            raise TypeError("prepared must be a PreparedClassWorldConfiguration")
        if not isinstance(request, ConfigurationCreateRequest):
            raise TypeError("request must be a ConfigurationCreateRequest")
        configuration = prepared.configuration
        expected = prepare_class_world_configuration(configuration)
        if expected != prepared:
            raise ConfigurationIntegrityError("prepared configuration changed before persistence")
        now = self._now()
        request_sha256 = _request_sha256(
            _CREATE_OPERATION,
            {
                "configuration_sha256": prepared.configuration_sha256,
                "correlation_id": request.correlation_id,
                "expected_revision": request.expected_revision,
            },
        )

        try:
            with self._store.transaction():
                actor_id = self._actor_id(identity)
                authority = self._authority(
                    identity=identity,
                    actor_id=actor_id,
                    cohort_id=configuration.cohort.cohort_id,
                )
                prior = self._store.load_idempotency_record(
                    principal_kind=PrincipalKind.ACTOR,
                    principal_id=actor_id,
                    operation=_CREATE_OPERATION,
                    idempotency_key=request.idempotency_key,
                )
                if prior is not None:
                    if prior.request_sha256 != request_sha256:
                        raise ConfigurationConflictError(
                            "idempotency key conflicts with prior configuration create"
                        )
                    record = self._store.load_configuration_record(prior.result_reference)
                    if (
                        record is None
                        or record.configuration_sha256 != prepared.configuration_sha256
                        or record.identity != configuration.identity
                        or record.cohort_id != configuration.cohort.cohort_id
                        or record.student_api_version != configuration.student_api_version
                        or record.canonical_bytes != prepared.canonical_bytes
                    ):
                        raise ConfigurationConflictError(
                            "idempotency result conflicts with immutable configuration"
                        )
                    self._reconstruct(record)
                    return ConfigurationCreateReceipt(record, replayed=True)

                existing = self._store._load_configuration_record_by_identity(  # noqa: SLF001
                    *configuration.identity
                )
                reused = existing is not None
                if existing is not None:
                    if (
                        existing.configuration_sha256 != prepared.configuration_sha256
                        or existing.cohort_id != configuration.cohort.cohort_id
                        or existing.student_api_version != configuration.student_api_version
                        or existing.canonical_bytes != prepared.canonical_bytes
                    ):
                        raise ConfigurationConflictError(
                            "configuration identity is already bound to different canonical bytes"
                        )
                    record = existing
                else:
                    record = StoredClassWorldConfiguration(
                        locator=str(self._uuid_factory()),
                        class_world_id=configuration.class_world_id,
                        class_world_version=configuration.class_world_version,
                        configuration_sha256=prepared.configuration_sha256,
                        cohort_id=configuration.cohort.cohort_id,
                        student_api_version=configuration.student_api_version,
                        canonical_bytes=prepared.canonical_bytes,
                        authority=authority,
                        created_at=now,
                        correlation_id=request.correlation_id,
                        idempotency_key=request.idempotency_key,
                    )
                    self._store.bind_class_world_configuration(
                        ClassWorldConfigurationBinding(
                            record.class_world_id,
                            record.class_world_version,
                            record.configuration_sha256,
                            record.cohort_id,
                            record.student_api_version,
                        )
                    )
                    self._store.append_class_world_configuration(record)
                self._reconstruct(record)
                self._append_audit(
                    record=record,
                    actor_id=actor_id,
                    occurred_at=now,
                    event_type=_CREATE_EVENT,
                    correlation_id=request.correlation_id,
                    idempotency_key=request.idempotency_key,
                    replayed_existing=reused,
                )
                self._store.record_idempotent_result(
                    IdempotencyRecord(
                        principal_kind=PrincipalKind.ACTOR,
                        principal_id=actor_id,
                        operation=_CREATE_OPERATION,
                        idempotency_key=request.idempotency_key,
                        request_sha256=request_sha256,
                        result_reference=record.locator,
                        created_at=now,
                    )
                )
        except PersistenceConflictError as error:
            raise ConfigurationConflictError(str(error)) from error
        return ConfigurationCreateReceipt(record, replayed=reused)

    def load_for_pinning(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        request: ConfigurationLoadRequest,
    ) -> ConfigurationLoadReceipt:
        """Authorize, reconstruct, validate, and audit one opaque exact load."""
        if not isinstance(request, ConfigurationLoadRequest):
            raise TypeError("request must be a ConfigurationLoadRequest")
        now = self._now()
        request_sha256 = _request_sha256(
            _READ_OPERATION,
            {"correlation_id": request.correlation_id, "locator": request.locator},
        )
        try:
            with self._store.transaction():
                actor_id = self._actor_id(identity)
                record = self._store.load_configuration_record(request.locator)
                if record is None:
                    raise ConfigurationAccessDeniedError("configuration is not available")
                self._authority(
                    identity=identity,
                    actor_id=actor_id,
                    cohort_id=record.cohort_id,
                )
                loaded = self._reconstruct(record)
                prior = self._store.load_idempotency_record(
                    principal_kind=PrincipalKind.ACTOR,
                    principal_id=actor_id,
                    operation=_READ_OPERATION,
                    idempotency_key=request.idempotency_key,
                )
                if prior is not None:
                    if prior.request_sha256 != request_sha256:
                        raise ConfigurationConflictError(
                            "idempotency key conflicts with prior configuration load"
                        )
                    if prior.result_reference != record.locator:
                        raise ConfigurationConflictError(
                            "idempotency result conflicts with immutable configuration"
                        )
                    return ConfigurationLoadReceipt(loaded, replayed=True)
                self._append_audit(
                    record=record,
                    actor_id=actor_id,
                    occurred_at=now,
                    event_type=_READ_EVENT,
                    correlation_id=request.correlation_id,
                    idempotency_key=request.idempotency_key,
                    replayed_existing=False,
                )
                self._store.record_idempotent_result(
                    IdempotencyRecord(
                        principal_kind=PrincipalKind.ACTOR,
                        principal_id=actor_id,
                        operation=_READ_OPERATION,
                        idempotency_key=request.idempotency_key,
                        request_sha256=request_sha256,
                        result_reference=record.locator,
                        created_at=now,
                    )
                )
        except PersistenceConflictError as error:
            raise ConfigurationConflictError(str(error)) from error
        return ConfigurationLoadReceipt(loaded, replayed=False)


__all__ = [
    "AuthoritativeClassWorldConfigurationService",
    "prepare_class_world_configuration",
]
