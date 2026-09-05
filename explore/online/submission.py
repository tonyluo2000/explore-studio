"""Trusted application service for bounded package submission and publication."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from explore.online.authorization import AuthorizationAction, AuthorizationResource, authorize
from explore.online.models import (
    AuditEvent,
    IdempotencyRecord,
    PackageVersionIdentity,
    PrincipalKind,
    StoredPackageVersion,
)
from explore.online.persistence import PersistenceConflictError
from explore.online.submission_models import (
    AuthenticatedOIDCIdentity,
    PackageSubmission,
    PublicationAcknowledgment,
    PublicationPolicy,
    SubmissionAccessDeniedError,
    SubmissionAuthenticationError,
    SubmissionConflictError,
    SubmissionPolicyError,
    SubmissionReceipt,
    SubmissionState,
    SubmissionValidationError,
    SubmissionValidationOutcome,
)
from explore.online.submission_persistence import SQLiteSubmissionStore
from explore.online.submission_verification import verify_submitted_archive

_SUBMISSION_OPERATION = "package.submit"
_AUDIT_EVENT_TYPE = "package.submitted"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _add_calendar_years(value: datetime, years: int) -> datetime:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def _request_sha256(
    filename: str,
    archive_bytes: bytes,
    acknowledgment: PublicationAcknowledgment,
) -> str:
    document = {
        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "filename": filename,
        "license_policy_version": acknowledgment.license_policy_version,
        "represented_authority": acknowledgment.represented_authority.value,
        "terms_version": acknowledgment.terms_version,
    }
    canonical = json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class PackageSubmissionService:
    """Authenticate, authorize, validate, and atomically persist one package.

    This service deliberately has no HTTP endpoint and implements no review
    decision, approved-registry projection, release, pin, or execution behavior.
    """

    def __init__(
        self,
        store: SQLiteSubmissionStore,
        publication_policy: PublicationPolicy,
        *,
        clock: Callable[[], datetime] = _utc_now,
        uuid_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        if not isinstance(store, SQLiteSubmissionStore):
            raise TypeError("store must be a SQLiteSubmissionStore")
        if not isinstance(publication_policy, PublicationPolicy):
            raise TypeError("publication_policy must be a PublicationPolicy")
        if not callable(clock) or not callable(uuid_factory):
            raise TypeError("clock and uuid_factory must be callable")
        self._store = store
        self._policy = publication_policy
        self._clock = clock
        self._uuid_factory = uuid_factory

    def _actor_id(self, identity: AuthenticatedOIDCIdentity) -> str:
        if not isinstance(identity, AuthenticatedOIDCIdentity):
            raise TypeError("identity must be an AuthenticatedOIDCIdentity")
        actor = self._store.resolve_federated_actor(identity.issuer, identity.subject)
        if actor is None:
            raise SubmissionAuthenticationError("authenticated identity is not bound")
        return actor.actor_id

    def _authorize(
        self,
        *,
        actor_id: str,
        identity: AuthenticatedOIDCIdentity,
        package_id: str,
        now: datetime,
    ) -> tuple[str, datetime]:
        namespace = self._store.load_namespace(package_id)
        if namespace is None:
            raise SubmissionAccessDeniedError("submission is not authorized")
        closes_at = self._store.load_cohort_closes_at(namespace.cohort_id)
        if closes_at is None:
            raise SubmissionAccessDeniedError("submission is not authorized")
        principal = self._store.load_human_principal(actor_id, identity.assurance)
        decision = authorize(
            principal,
            AuthorizationAction.SUBMIT,
            AuthorizationResource(
                cohort_id=namespace.cohort_id,
                package_id=namespace.package_id,
                owner_actor_id=namespace.owner_actor_id,
                active=now < closes_at,
            ),
        )
        if not decision.allowed:
            raise SubmissionAccessDeniedError("submission is not authorized")
        return namespace.cohort_id, closes_at

    def _load_replay(
        self,
        *,
        actor_id: str,
        identity: AuthenticatedOIDCIdentity,
        result_reference: str,
        now: datetime,
    ) -> SubmissionReceipt:
        submission = self._store.load_submission(result_reference)
        if submission is None or submission.submitted_by_actor_id != actor_id:
            raise RuntimeError("idempotency record references a missing submission")
        self._authorize(
            actor_id=actor_id,
            identity=identity,
            package_id=submission.package_version.package_id,
            now=now,
        )
        return SubmissionReceipt(submission, replayed=True)

    def submit(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        filename: str,
        archive_bytes: bytes,
        idempotency_key: str,
        acknowledgment: PublicationAcknowledgment,
    ) -> SubmissionReceipt:
        """Publish one immutable valid archive into the reviewable-only state."""
        if not isinstance(acknowledgment, PublicationAcknowledgment):
            raise TypeError("acknowledgment must be a PublicationAcknowledgment")
        if (
            not isinstance(idempotency_key, str)
            or not idempotency_key
            or len(idempotency_key) > 128
            or any(ord(character) < 32 or ord(character) == 127 for character in idempotency_key)
        ):
            raise ValueError("idempotency_key must contain 1 to 128 non-control characters")
        if not isinstance(filename, str) or type(archive_bytes) is not bytes:
            verification = verify_submitted_archive(filename, archive_bytes)
            raise SubmissionValidationError(verification)

        actor_id = self._actor_id(identity)
        request_sha256 = _request_sha256(filename, archive_bytes, acknowledgment)
        now = self._clock()
        if (
            not isinstance(now, datetime)
            or now.tzinfo is None
            or now.utcoffset() != UTC.utcoffset(now)
        ):
            raise RuntimeError("trusted clock must return a timezone-aware UTC datetime")

        prior = self._store.load_idempotency_record(
            principal_kind=PrincipalKind.ACTOR,
            principal_id=actor_id,
            operation=_SUBMISSION_OPERATION,
            idempotency_key=idempotency_key,
        )
        if prior is not None:
            with self._store.transaction():
                locked_prior = self._store.load_idempotency_record(
                    principal_kind=PrincipalKind.ACTOR,
                    principal_id=actor_id,
                    operation=_SUBMISSION_OPERATION,
                    idempotency_key=idempotency_key,
                )
                if locked_prior is None:
                    raise RuntimeError("completed idempotency record disappeared")
                if locked_prior.request_sha256 != request_sha256:
                    raise SubmissionConflictError("idempotency key conflicts with prior request")
                return self._load_replay(
                    actor_id=actor_id,
                    identity=identity,
                    result_reference=locked_prior.result_reference,
                    now=now,
                )

        if (
            acknowledgment.terms_version != self._policy.terms_version
            or acknowledgment.license_policy_version != self._policy.license_policy_version
        ):
            raise SubmissionPolicyError(
                "publication acknowledgment does not match current trusted policy"
            )

        verification = verify_submitted_archive(filename, archive_bytes)
        if not verification.is_valid or verification.archive is None:
            raise SubmissionValidationError(verification)
        verified = verification.archive

        try:
            with self._store.transaction():
                # Re-resolve and re-authorize under the write lock. Membership,
                # grants, cohort activity, and namespace ownership are authoritative
                # database state, never request claims.
                locked_actor_id = self._actor_id(identity)
                if locked_actor_id != actor_id:
                    raise SubmissionAuthenticationError("authenticated identity changed")
                prior = self._store.load_idempotency_record(
                    principal_kind=PrincipalKind.ACTOR,
                    principal_id=actor_id,
                    operation=_SUBMISSION_OPERATION,
                    idempotency_key=idempotency_key,
                )
                if prior is not None:
                    if prior.request_sha256 != request_sha256:
                        raise SubmissionConflictError(
                            "idempotency key conflicts with prior request"
                        )
                    return self._load_replay(
                        actor_id=actor_id,
                        identity=identity,
                        result_reference=prior.result_reference,
                        now=now,
                    )

                cohort_id, closes_at = self._authorize(
                    actor_id=actor_id,
                    identity=identity,
                    package_id=verified.package_id,
                    now=now,
                )
                package_identity = PackageVersionIdentity(
                    verified.package_id,
                    verified.semantic_version,
                    verified.raw_archive_sha256,
                )
                self._store.record_package_version(
                    StoredPackageVersion(package_identity, cohort_id, actor_id, now)
                )

                submission = PackageSubmission(
                    submission_id=str(self._uuid_factory()),
                    package_version=package_identity,
                    cohort_id=cohort_id,
                    submitted_by_actor_id=actor_id,
                    submitted_at=now,
                    artifact_retention_until=_add_calendar_years(closes_at, 1),
                    state=SubmissionState.REVIEWABLE,
                    validation_outcome=SubmissionValidationOutcome.VALID,
                    validation_provenance_json=verified.provenance_json(),
                    acknowledgment=acknowledgment,
                )
                self._store.record_submission(submission, archive_bytes)

                audit_details = json.dumps(
                    {
                        "license_policy_version": acknowledgment.license_policy_version,
                        "package_id": package_identity.package_id,
                        "raw_archive_sha256": package_identity.raw_zip_sha256,
                        "represented_authority": acknowledgment.represented_authority.value,
                        "semantic_version": package_identity.package_version,
                        "state": SubmissionState.REVIEWABLE.value,
                        "terms_version": acknowledgment.terms_version,
                        "validation_outcome": SubmissionValidationOutcome.VALID.value,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                self._store.append_audit_event(
                    AuditEvent(
                        event_id=str(self._uuid_factory()),
                        occurred_at=now,
                        retention_until=_add_calendar_years(closes_at, 2),
                        principal_kind=PrincipalKind.ACTOR,
                        principal_id=actor_id,
                        event_type=_AUDIT_EVENT_TYPE,
                        object_type="package-submission",
                        object_id=submission.submission_id,
                        cohort_id=cohort_id,
                        idempotency_key=idempotency_key,
                        details_json=audit_details,
                    )
                )
                self._store.record_idempotent_result(
                    IdempotencyRecord(
                        principal_kind=PrincipalKind.ACTOR,
                        principal_id=actor_id,
                        operation=_SUBMISSION_OPERATION,
                        idempotency_key=idempotency_key,
                        request_sha256=request_sha256,
                        result_reference=submission.submission_id,
                        created_at=now,
                    )
                )
        except PersistenceConflictError as error:
            raise SubmissionConflictError(str(error)) from error

        return SubmissionReceipt(submission, replayed=False)


__all__ = ["PackageSubmissionService"]
