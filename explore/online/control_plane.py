"""Authenticated application services for bounded Phase E control-plane transitions."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from explore.online.authorization import authorize_control_plane
from explore.online.control_plane_models import (
    ControlPlaneAccessDeniedError,
    ControlPlaneAction,
    ControlPlaneAuthenticationError,
    ControlPlaneAuthoritySnapshot,
    ControlPlaneConflictError,
    ControlPlaneReceipt,
    ControlPlaneTransition,
    MembershipChangeRequest,
    MembershipCreateRequest,
    MembershipRevokeRequest,
    NamespaceClaimRequest,
    NamespaceGrantRequest,
    NamespaceGrantRevokeRequest,
    NamespaceTransferRequest,
)
from explore.online.control_plane_persistence import SQLiteControlPlaneStore
from explore.online.models import (
    AuditEvent,
    CohortMembership,
    CohortRole,
    IdempotencyRecord,
    NamespaceGrant,
    NamespacePermission,
    PackageNamespace,
    PrincipalKind,
)
from explore.online.persistence import PersistenceConflictError
from explore.online.submission_models import AuthenticatedOIDCIdentity

_Prepare = Callable[[str], tuple[str, object]]
_Mutate = Callable[
    [str, ControlPlaneAuthoritySnapshot, datetime, object],
    tuple[str, str, dict[str, object]],
]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _add_calendar_years(value: datetime, years: int) -> datetime:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(year=value.year + years, day=28)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _request_sha256(action: ControlPlaneAction, document: dict[str, object]) -> str:
    envelope = {"action": action.value, **document}
    return hashlib.sha256(_canonical_json(envelope).encode("utf-8")).hexdigest()


def _membership_state(membership: CohortMembership | None) -> object:
    if membership is None:
        return None
    return {
        "active": membership.active,
        "revision": membership.revision,
        "role": membership.role.value,
    }


class ControlPlaneService:
    """Authorize and atomically persist course-admin control-plane transitions."""

    def __init__(
        self,
        store: SQLiteControlPlaneStore,
        *,
        clock: Callable[[], datetime] = _utc_now,
        uuid_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        if not isinstance(store, SQLiteControlPlaneStore):
            raise TypeError("store must be a SQLiteControlPlaneStore")
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
            raise ControlPlaneAuthenticationError("authenticated identity is not bound")
        return actor.actor_id

    def _authority(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        actor_id: str,
        action: ControlPlaneAction,
        cohort_id: str,
    ) -> ControlPlaneAuthoritySnapshot:
        principal = self._store.load_human_principal(actor_id, identity.assurance)
        decision = authorize_control_plane(
            principal,
            action,
            cohort_id,
        )
        if not decision.allowed:
            raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
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
        if membership is None:
            raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
        return ControlPlaneAuthoritySnapshot(
            cohort_id=membership.cohort_id,
            actor_id=membership.actor_id,
            role=membership.role,
            assurance=identity.assurance,
            granted_by_actor_id=membership.granted_by_actor_id,
            granted_at=membership.granted_at,
            revision=membership.revision,
            active=membership.active,
        )

    def _audit_and_record(
        self,
        *,
        transition: ControlPlaneTransition,
        request_sha256: str,
    ) -> None:
        closes_at = self._store.load_cohort_closes_at(transition.cohort_id)
        if closes_at is None:
            raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
        authority = transition.authority
        audit_details = _canonical_json(
            {
                "action": transition.action.value,
                "authority": {
                    "actor_id": authority.actor_id,
                    "active": authority.active,
                    "assurance": authority.assurance.value,
                    "granted_at": authority.granted_at.isoformat().replace("+00:00", "Z"),
                    "granted_by_actor_id": authority.granted_by_actor_id,
                    "revision": authority.revision,
                    "role": authority.role.value,
                },
                "change": json.loads(transition.change_json),
                "correlation_id": transition.correlation_id,
                "transition_id": transition.transition_id,
            }
        )
        operation = f"control-plane.{transition.action.value}"
        self._store.append_audit_event(
            AuditEvent(
                event_id=str(self._uuid_factory()),
                occurred_at=transition.occurred_at,
                retention_until=_add_calendar_years(
                    max(closes_at, transition.occurred_at),
                    2,
                ),
                principal_kind=PrincipalKind.ACTOR,
                principal_id=authority.actor_id,
                event_type=operation,
                object_type=transition.object_type,
                object_id=transition.object_id,
                cohort_id=transition.cohort_id,
                idempotency_key=transition.idempotency_key,
                details_json=audit_details,
            )
        )
        self._store.record_idempotent_result(
            IdempotencyRecord(
                principal_kind=PrincipalKind.ACTOR,
                principal_id=authority.actor_id,
                operation=operation,
                idempotency_key=transition.idempotency_key,
                request_sha256=request_sha256,
                result_reference=transition.transition_id,
                created_at=transition.occurred_at,
            )
        )

    def _run(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        action: ControlPlaneAction,
        idempotency_key: str,
        correlation_id: str,
        request_document: dict[str, object],
        prepare: _Prepare,
        mutate: _Mutate,
    ) -> ControlPlaneReceipt:
        request_sha256 = _request_sha256(action, request_document)
        now = self._clock()
        if (
            not isinstance(now, datetime)
            or now.tzinfo is None
            or now.utcoffset() != UTC.utcoffset(now)
        ):
            raise RuntimeError("trusted clock must return a timezone-aware UTC datetime")
        operation = f"control-plane.{action.value}"

        try:
            with self._store.transaction():
                actor_id = self._actor_id(identity)
                prior = self._store.load_idempotency_record(
                    principal_kind=PrincipalKind.ACTOR,
                    principal_id=actor_id,
                    operation=operation,
                    idempotency_key=idempotency_key,
                )
                if prior is not None:
                    if prior.request_sha256 != request_sha256:
                        raise ControlPlaneConflictError(
                            "idempotency key conflicts with prior control-plane request"
                        )
                    transition = self._store.load_control_plane_transition(prior.result_reference)
                    if (
                        transition is None
                        or transition.action is not action
                        or transition.authority.actor_id != actor_id
                    ):
                        raise RuntimeError(
                            "idempotency record references a missing control-plane transition"
                        )
                    self._authority(
                        identity=identity,
                        actor_id=actor_id,
                        action=action,
                        cohort_id=transition.cohort_id,
                    )
                    return ControlPlaneReceipt(transition, replayed=True)

                cohort_id, context = prepare(actor_id)
                authority = self._authority(
                    identity=identity,
                    actor_id=actor_id,
                    action=action,
                    cohort_id=cohort_id,
                )
                object_type, object_id, change = mutate(actor_id, authority, now, context)
                transition = ControlPlaneTransition(
                    transition_id=str(self._uuid_factory()),
                    action=action,
                    object_type=object_type,
                    object_id=object_id,
                    cohort_id=cohort_id,
                    authority=authority,
                    occurred_at=now,
                    correlation_id=correlation_id,
                    idempotency_key=idempotency_key,
                    change_json=_canonical_json(change),
                )
                self._store.append_control_plane_transition(transition)
                self._audit_and_record(
                    transition=transition,
                    request_sha256=request_sha256,
                )
        except PersistenceConflictError as error:
            raise ControlPlaneConflictError(str(error)) from error

        return ControlPlaneReceipt(transition, replayed=False)

    def _prepare_cohort(self, cohort_id: str) -> _Prepare:
        def prepare(_actor_id: str) -> tuple[str, object]:
            if self._store.load_cohort_closes_at(cohort_id) is None:
                raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
            return cohort_id, None

        return prepare

    def _prepare_namespace(self, package_id: str) -> _Prepare:
        def prepare(_actor_id: str) -> tuple[str, object]:
            namespace = self._store.load_namespace(package_id)
            if namespace is None:
                raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
            return namespace.cohort_id, namespace

        return prepare

    def create_membership(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        request: MembershipCreateRequest,
    ) -> ControlPlaneReceipt:
        """Create one same-cohort role assignment at revision one."""
        if not isinstance(request, MembershipCreateRequest):
            raise TypeError("request must be a MembershipCreateRequest")

        def mutate(
            actor_id: str,
            _authority: ControlPlaneAuthoritySnapshot,
            now: datetime,
            _context: object,
        ) -> tuple[str, str, dict[str, object]]:
            if not self._store.actor_exists(request.target_actor_id):
                raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
            membership = CohortMembership(
                cohort_id=request.cohort_id,
                actor_id=request.target_actor_id,
                role=request.role,
                granted_by_actor_id=actor_id,
                granted_at=now,
                active=True,
                revision=1,
            )
            self._store.insert_membership(membership)
            return (
                "cohort-membership",
                f"{request.cohort_id}:{request.target_actor_id}",
                {
                    "after": _membership_state(membership),
                    "before": None,
                    "target_actor_id": request.target_actor_id,
                },
            )

        return self._run(
            identity=identity,
            action=ControlPlaneAction.MEMBERSHIP_CREATE,
            idempotency_key=request.idempotency_key,
            correlation_id=request.correlation_id,
            request_document={
                "cohort_id": request.cohort_id,
                "correlation_id": request.correlation_id,
                "expected_revision": request.expected_revision,
                "role": request.role.value,
                "target_actor_id": request.target_actor_id,
            },
            prepare=self._prepare_cohort(request.cohort_id),
            mutate=mutate,
        )

    def change_membership(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        request: MembershipChangeRequest,
    ) -> ControlPlaneReceipt:
        """Change one other actor's active same-cohort role at the next revision."""
        if not isinstance(request, MembershipChangeRequest):
            raise TypeError("request must be a MembershipChangeRequest")

        def mutate(
            actor_id: str,
            _authority: ControlPlaneAuthoritySnapshot,
            _now: datetime,
            _context: object,
        ) -> tuple[str, str, dict[str, object]]:
            if actor_id == request.target_actor_id:
                raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
            current = self._store.load_membership(
                request.cohort_id,
                request.target_actor_id,
            )
            if (
                current is None
                or not current.active
                or current.revision != request.expected_revision
                or current.role is request.role
            ):
                raise ControlPlaneConflictError(
                    "membership does not match the expected active revision"
                )
            updated = self._store.update_membership(
                current=current,
                role=request.role,
                active=True,
            )
            return (
                "cohort-membership",
                f"{request.cohort_id}:{request.target_actor_id}",
                {
                    "after": _membership_state(updated),
                    "before": _membership_state(current),
                    "target_actor_id": request.target_actor_id,
                },
            )

        return self._run(
            identity=identity,
            action=ControlPlaneAction.MEMBERSHIP_CHANGE,
            idempotency_key=request.idempotency_key,
            correlation_id=request.correlation_id,
            request_document={
                "cohort_id": request.cohort_id,
                "correlation_id": request.correlation_id,
                "expected_revision": request.expected_revision,
                "role": request.role.value,
                "target_actor_id": request.target_actor_id,
            },
            prepare=self._prepare_cohort(request.cohort_id),
            mutate=mutate,
        )

    def revoke_membership(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        request: MembershipRevokeRequest,
    ) -> ControlPlaneReceipt:
        """Revoke one other actor's current membership at the next revision."""
        if not isinstance(request, MembershipRevokeRequest):
            raise TypeError("request must be a MembershipRevokeRequest")

        def mutate(
            actor_id: str,
            _authority: ControlPlaneAuthoritySnapshot,
            _now: datetime,
            _context: object,
        ) -> tuple[str, str, dict[str, object]]:
            if actor_id == request.target_actor_id:
                raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
            current = self._store.load_membership(
                request.cohort_id,
                request.target_actor_id,
            )
            if (
                current is None
                or not current.active
                or current.revision != request.expected_revision
            ):
                raise ControlPlaneConflictError(
                    "membership does not match the expected active revision"
                )
            updated = self._store.update_membership(
                current=current,
                role=current.role,
                active=False,
            )
            return (
                "cohort-membership",
                f"{request.cohort_id}:{request.target_actor_id}",
                {
                    "after": _membership_state(updated),
                    "before": _membership_state(current),
                    "target_actor_id": request.target_actor_id,
                },
            )

        return self._run(
            identity=identity,
            action=ControlPlaneAction.MEMBERSHIP_REVOKE,
            idempotency_key=request.idempotency_key,
            correlation_id=request.correlation_id,
            request_document={
                "cohort_id": request.cohort_id,
                "correlation_id": request.correlation_id,
                "expected_revision": request.expected_revision,
                "target_actor_id": request.target_actor_id,
            },
            prepare=self._prepare_cohort(request.cohort_id),
            mutate=mutate,
        )

    def claim_namespace(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        request: NamespaceClaimRequest,
    ) -> ControlPlaneReceipt:
        """Claim one global package ID for an active same-cohort owner."""
        if not isinstance(request, NamespaceClaimRequest):
            raise TypeError("request must be a NamespaceClaimRequest")

        def mutate(
            _actor_id: str,
            _authority: ControlPlaneAuthoritySnapshot,
            now: datetime,
            _context: object,
        ) -> tuple[str, str, dict[str, object]]:
            owner = self._store.load_membership(request.cohort_id, request.owner_actor_id)
            if owner is None or not owner.active:
                raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
            namespace = PackageNamespace(
                package_id=request.package_id,
                cohort_id=request.cohort_id,
                owner_actor_id=request.owner_actor_id,
                created_at=now,
                revision=1,
            )
            self._store.insert_namespace(namespace)
            return (
                "package-namespace",
                request.package_id,
                {
                    "after": {
                        "owner_actor_id": namespace.owner_actor_id,
                        "revision": namespace.revision,
                    },
                    "before": None,
                },
            )

        return self._run(
            identity=identity,
            action=ControlPlaneAction.NAMESPACE_CLAIM,
            idempotency_key=request.idempotency_key,
            correlation_id=request.correlation_id,
            request_document={
                "cohort_id": request.cohort_id,
                "correlation_id": request.correlation_id,
                "expected_revision": request.expected_revision,
                "owner_actor_id": request.owner_actor_id,
                "package_id": request.package_id,
            },
            prepare=self._prepare_cohort(request.cohort_id),
            mutate=mutate,
        )

    def grant_namespace(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        request: NamespaceGrantRequest,
    ) -> ControlPlaneReceipt:
        """Create or reactivate one explicit same-cohort submit grant."""
        if not isinstance(request, NamespaceGrantRequest):
            raise TypeError("request must be a NamespaceGrantRequest")

        def mutate(
            actor_id: str,
            _authority: ControlPlaneAuthoritySnapshot,
            now: datetime,
            context: object,
        ) -> tuple[str, str, dict[str, object]]:
            if not isinstance(context, PackageNamespace):
                raise RuntimeError("namespace preparation returned invalid state")
            if context.revision != request.expected_namespace_revision:
                raise ControlPlaneConflictError("namespace changed after the expected revision")
            target = self._store.load_membership(context.cohort_id, request.target_actor_id)
            if target is None or not target.active:
                raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
            before = self._store.load_namespace_grant_state(
                request.package_id,
                request.target_actor_id,
            )
            grant = NamespaceGrant(
                package_id=context.package_id,
                cohort_id=context.cohort_id,
                actor_id=request.target_actor_id,
                permission=NamespacePermission.SUBMIT,
                granted_by_actor_id=actor_id,
                granted_at=now,
            )
            after = self._store.activate_namespace_grant(
                grant=grant,
                expected_revision=request.expected_grant_revision,
            )
            return (
                "namespace-grant",
                f"{request.package_id}:{request.target_actor_id}:submit",
                {
                    "after": {"active": after.active, "revision": after.revision},
                    "before": (
                        None
                        if before is None
                        else {"active": before.active, "revision": before.revision}
                    ),
                    "namespace_revision": context.revision,
                    "target_actor_id": request.target_actor_id,
                },
            )

        return self._run(
            identity=identity,
            action=ControlPlaneAction.NAMESPACE_GRANT,
            idempotency_key=request.idempotency_key,
            correlation_id=request.correlation_id,
            request_document={
                "correlation_id": request.correlation_id,
                "expected_grant_revision": request.expected_grant_revision,
                "expected_namespace_revision": request.expected_namespace_revision,
                "package_id": request.package_id,
                "target_actor_id": request.target_actor_id,
            },
            prepare=self._prepare_namespace(request.package_id),
            mutate=mutate,
        )

    def revoke_namespace_grant(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        request: NamespaceGrantRevokeRequest,
    ) -> ControlPlaneReceipt:
        """Revoke one exact current same-cohort submit grant."""
        if not isinstance(request, NamespaceGrantRevokeRequest):
            raise TypeError("request must be a NamespaceGrantRevokeRequest")

        def mutate(
            _actor_id: str,
            _authority: ControlPlaneAuthoritySnapshot,
            _now: datetime,
            context: object,
        ) -> tuple[str, str, dict[str, object]]:
            if not isinstance(context, PackageNamespace):
                raise RuntimeError("namespace preparation returned invalid state")
            if context.revision != request.expected_namespace_revision:
                raise ControlPlaneConflictError("namespace changed after the expected revision")
            before = self._store.load_namespace_grant_state(
                request.package_id,
                request.target_actor_id,
            )
            if (
                before is None
                or not before.active
                or before.revision != request.expected_grant_revision
            ):
                raise ControlPlaneConflictError(
                    "namespace grant does not match the expected active revision"
                )
            after = self._store.revoke_namespace_grant(state=before)
            return (
                "namespace-grant",
                f"{request.package_id}:{request.target_actor_id}:submit",
                {
                    "after": {"active": after.active, "revision": after.revision},
                    "before": {"active": before.active, "revision": before.revision},
                    "namespace_revision": context.revision,
                    "target_actor_id": request.target_actor_id,
                },
            )

        return self._run(
            identity=identity,
            action=ControlPlaneAction.NAMESPACE_GRANT_REVOKE,
            idempotency_key=request.idempotency_key,
            correlation_id=request.correlation_id,
            request_document={
                "correlation_id": request.correlation_id,
                "expected_grant_revision": request.expected_grant_revision,
                "expected_namespace_revision": request.expected_namespace_revision,
                "package_id": request.package_id,
                "target_actor_id": request.target_actor_id,
            },
            prepare=self._prepare_namespace(request.package_id),
            mutate=mutate,
        )

    def transfer_namespace(
        self,
        *,
        identity: AuthenticatedOIDCIdentity,
        request: NamespaceTransferRequest,
    ) -> ControlPlaneReceipt:
        """Transfer only current ownership metadata for one global package ID."""
        if not isinstance(request, NamespaceTransferRequest):
            raise TypeError("request must be a NamespaceTransferRequest")

        def mutate(
            _actor_id: str,
            _authority: ControlPlaneAuthoritySnapshot,
            _now: datetime,
            context: object,
        ) -> tuple[str, str, dict[str, object]]:
            if not isinstance(context, PackageNamespace):
                raise RuntimeError("namespace preparation returned invalid state")
            if (
                context.revision != request.expected_revision
                or context.owner_actor_id == request.new_owner_actor_id
            ):
                raise ControlPlaneConflictError(
                    "namespace does not match the expected transferable revision"
                )
            new_owner = self._store.load_membership(
                context.cohort_id,
                request.new_owner_actor_id,
            )
            if new_owner is None or not new_owner.active:
                raise ControlPlaneAccessDeniedError("control-plane transition is not authorized")
            updated = self._store.transfer_namespace(
                namespace=context,
                new_owner_actor_id=request.new_owner_actor_id,
            )
            return (
                "package-namespace",
                request.package_id,
                {
                    "after": {
                        "owner_actor_id": updated.owner_actor_id,
                        "revision": updated.revision,
                    },
                    "before": {
                        "owner_actor_id": context.owner_actor_id,
                        "revision": context.revision,
                    },
                },
            )

        return self._run(
            identity=identity,
            action=ControlPlaneAction.NAMESPACE_TRANSFER,
            idempotency_key=request.idempotency_key,
            correlation_id=request.correlation_id,
            request_document={
                "correlation_id": request.correlation_id,
                "expected_revision": request.expected_revision,
                "new_owner_actor_id": request.new_owner_actor_id,
                "package_id": request.package_id,
            },
            prepare=self._prepare_namespace(request.package_id),
            mutate=mutate,
        )


__all__ = ["ControlPlaneService"]
