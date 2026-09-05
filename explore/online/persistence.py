"""Constrained SQLite reference persistence for the Phase E foundation."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from explore.online.models import (
    Actor,
    AssuranceLevel,
    AuditEvent,
    Cohort,
    CohortMembership,
    CohortRole,
    FederatedIdentity,
    HumanPrincipal,
    IdempotencyRecord,
    IdentityProvider,
    NamespaceGrant,
    NamespacePermission,
    PackageNamespace,
    PackageVersionIdentity,
    StoredPackageVersion,
)

FOUNDATION_SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS online_schema_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1)
) STRICT;

INSERT OR IGNORE INTO online_schema_metadata (singleton, schema_version) VALUES (1, 1);

CREATE TABLE IF NOT EXISTS identity_providers (
    issuer TEXT PRIMARY KEY,
    privileged_assurance TEXT NOT NULL CHECK (privileged_assurance = 'aal2')
) STRICT;

CREATE TABLE IF NOT EXISTS actors (
    actor_id TEXT PRIMARY KEY CHECK (length(actor_id) = 36),
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z')
) STRICT;

CREATE TABLE IF NOT EXISTS federated_identities (
    issuer TEXT NOT NULL,
    subject TEXT NOT NULL,
    actor_id TEXT NOT NULL UNIQUE,
    PRIMARY KEY (issuer, subject),
    FOREIGN KEY (issuer) REFERENCES identity_providers (issuer) ON DELETE RESTRICT,
    FOREIGN KEY (actor_id) REFERENCES actors (actor_id) ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER IF NOT EXISTS federated_identities_no_update
BEFORE UPDATE ON federated_identities
BEGIN
    SELECT RAISE(ABORT, 'federated identity bindings are immutable');
END;

CREATE TRIGGER IF NOT EXISTS federated_identities_no_delete
BEFORE DELETE ON federated_identities
BEGIN
    SELECT RAISE(ABORT, 'federated identity bindings are immutable');
END;

CREATE TABLE IF NOT EXISTS cohorts (
    cohort_id TEXT PRIMARY KEY,
    account_authority TEXT NOT NULL,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    closes_at TEXT NOT NULL CHECK (
        substr(closes_at, -1) = 'Z' AND closes_at > created_at
    )
) STRICT;

CREATE TABLE IF NOT EXISTS cohort_memberships (
    cohort_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'teacher', 'course-admin')),
    granted_by_actor_id TEXT NOT NULL,
    granted_at TEXT NOT NULL CHECK (substr(granted_at, -1) = 'Z'),
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    PRIMARY KEY (cohort_id, actor_id),
    FOREIGN KEY (cohort_id) REFERENCES cohorts (cohort_id) ON DELETE RESTRICT,
    FOREIGN KEY (actor_id) REFERENCES actors (actor_id) ON DELETE RESTRICT,
    FOREIGN KEY (granted_by_actor_id) REFERENCES actors (actor_id) ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER IF NOT EXISTS cohort_memberships_revision_guard
BEFORE UPDATE ON cohort_memberships
WHEN NEW.cohort_id != OLD.cohort_id
    OR NEW.actor_id != OLD.actor_id
    OR NEW.granted_by_actor_id != OLD.granted_by_actor_id
    OR NEW.granted_at != OLD.granted_at
    OR NEW.revision != OLD.revision + 1
BEGIN
    SELECT RAISE(ABORT, 'membership updates require the next optimistic revision');
END;

CREATE TABLE IF NOT EXISTS package_namespaces (
    package_id TEXT PRIMARY KEY,
    cohort_id TEXT NOT NULL,
    owner_actor_id TEXT NOT NULL,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    UNIQUE (package_id, cohort_id),
    FOREIGN KEY (cohort_id, owner_actor_id)
        REFERENCES cohort_memberships (cohort_id, actor_id) ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER IF NOT EXISTS package_namespaces_revision_guard
BEFORE UPDATE ON package_namespaces
WHEN NEW.package_id != OLD.package_id
    OR NEW.cohort_id != OLD.cohort_id
    OR NEW.created_at != OLD.created_at
    OR NEW.revision != OLD.revision + 1
BEGIN
    SELECT RAISE(ABORT, 'namespace updates require the next optimistic revision');
END;

CREATE TABLE IF NOT EXISTS namespace_grants (
    package_id TEXT NOT NULL,
    cohort_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    permission TEXT NOT NULL CHECK (permission = 'submit'),
    granted_by_actor_id TEXT NOT NULL,
    granted_at TEXT NOT NULL CHECK (substr(granted_at, -1) = 'Z'),
    PRIMARY KEY (package_id, actor_id, permission),
    FOREIGN KEY (package_id, cohort_id)
        REFERENCES package_namespaces (package_id, cohort_id) ON DELETE RESTRICT,
    FOREIGN KEY (cohort_id, actor_id)
        REFERENCES cohort_memberships (cohort_id, actor_id) ON DELETE RESTRICT,
    FOREIGN KEY (cohort_id, granted_by_actor_id)
        REFERENCES cohort_memberships (cohort_id, actor_id) ON DELETE RESTRICT
) STRICT;

CREATE TABLE IF NOT EXISTS package_versions (
    package_id TEXT NOT NULL,
    package_version TEXT NOT NULL,
    raw_zip_sha256 TEXT NOT NULL CHECK (
        length(raw_zip_sha256) = 64
        AND raw_zip_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    cohort_id TEXT NOT NULL,
    created_by_actor_id TEXT NOT NULL,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    PRIMARY KEY (package_id, package_version),
    FOREIGN KEY (package_id, cohort_id)
        REFERENCES package_namespaces (package_id, cohort_id) ON DELETE RESTRICT,
    FOREIGN KEY (cohort_id, created_by_actor_id)
        REFERENCES cohort_memberships (cohort_id, actor_id) ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER IF NOT EXISTS package_versions_no_update
BEFORE UPDATE ON package_versions
BEGIN
    SELECT RAISE(ABORT, 'package version identities are immutable');
END;

CREATE TRIGGER IF NOT EXISTS package_versions_no_delete
BEFORE DELETE ON package_versions
BEGIN
    SELECT RAISE(ABORT, 'package version identities are immutable');
END;

CREATE TABLE IF NOT EXISTS idempotency_records (
    principal_kind TEXT NOT NULL CHECK (principal_kind IN ('actor', 'service')),
    principal_id TEXT NOT NULL,
    operation TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_sha256 TEXT NOT NULL CHECK (
        length(request_sha256) = 64
        AND request_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    result_reference TEXT NOT NULL,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    PRIMARY KEY (principal_kind, principal_id, operation, idempotency_key)
) STRICT;

CREATE TRIGGER IF NOT EXISTS idempotency_records_no_update
BEFORE UPDATE ON idempotency_records
BEGIN
    SELECT RAISE(ABORT, 'completed idempotency records are immutable');
END;

CREATE TRIGGER IF NOT EXISTS idempotency_records_no_delete
BEFORE DELETE ON idempotency_records
BEGIN
    SELECT RAISE(ABORT, 'completed idempotency records are immutable');
END;

CREATE TABLE IF NOT EXISTS audit_events (
    event_id TEXT PRIMARY KEY CHECK (length(event_id) = 36),
    occurred_at TEXT NOT NULL CHECK (substr(occurred_at, -1) = 'Z'),
    retention_until TEXT NOT NULL CHECK (
        substr(retention_until, -1) = 'Z' AND retention_until > occurred_at
    ),
    principal_kind TEXT NOT NULL CHECK (principal_kind IN ('actor', 'service')),
    principal_id TEXT NOT NULL,
    initiating_actor_id TEXT,
    event_type TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    cohort_id TEXT,
    idempotency_key TEXT NOT NULL,
    details_json TEXT NOT NULL,
    UNIQUE (principal_kind, principal_id, event_type, idempotency_key)
) STRICT;

CREATE TRIGGER IF NOT EXISTS audit_events_no_update
BEFORE UPDATE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'audit events are append-only');
END;

CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
BEFORE DELETE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'audit events are append-only');
END;
"""


class PersistenceConflictError(RuntimeError):
    """A persisted immutable identity conflicts with a requested value."""


class IdempotencyConflictError(PersistenceConflictError):
    """An idempotency key was reused for different request bytes."""


class PersistenceAuthorizationError(PermissionError):
    """A foundational administrative write lacks authoritative course-admin scope."""


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@contextmanager
def _immediate_transaction(connection: sqlite3.Connection) -> Iterator[None]:
    owns_transaction = not connection.in_transaction
    if owns_transaction:
        connection.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        if owns_transaction:
            connection.rollback()
        raise
    else:
        if owns_transaction:
            connection.commit()


class SQLiteFoundationStore:
    """Reference store whose constraints define the Phase E persistence boundary."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        if not isinstance(connection, sqlite3.Connection):
            raise TypeError("connection must be a sqlite3.Connection")
        if connection.in_transaction:
            raise RuntimeError("connection must not have an active transaction")
        connection.isolation_level = None
        connection.execute("PRAGMA foreign_keys = ON")
        foreign_keys = connection.execute("PRAGMA foreign_keys").fetchone()
        if foreign_keys != (1,):
            raise RuntimeError("SQLite foreign-key enforcement is required")
        self._connection = connection

    @classmethod
    def open(cls, path: str | Path) -> SQLiteFoundationStore:
        """Open a store without creating directories or accepting URI filenames."""
        if not isinstance(path, (str, Path)):
            raise TypeError("path must be a string or Path")
        connection = sqlite3.connect(str(path), timeout=30.0, isolation_level=None)
        return cls(connection)

    def close(self) -> None:
        """Close the owned database connection."""
        self._connection.close()

    def initialize_schema(self) -> None:
        """Create the versioned foundation schema idempotently."""
        self._connection.executescript(_SCHEMA)
        row = self._connection.execute(
            "SELECT schema_version FROM online_schema_metadata WHERE singleton = 1"
        ).fetchone()
        if row != (FOUNDATION_SCHEMA_VERSION,):
            raise RuntimeError("unsupported Phase E foundation schema version")

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Atomically group a mutation, its audit event, and idempotency result."""
        with _immediate_transaction(self._connection):
            yield

    def approve_identity_provider(self, provider: IdentityProvider) -> None:
        """Persist one configured OIDC issuer and its privileged assurance rule."""
        if not isinstance(provider, IdentityProvider):
            raise TypeError("provider must be an IdentityProvider")
        with _immediate_transaction(self._connection):
            existing = self._connection.execute(
                "SELECT privileged_assurance FROM identity_providers WHERE issuer = ?",
                (provider.issuer,),
            ).fetchone()
            if existing is not None:
                if existing != (provider.privileged_assurance.value,):
                    raise PersistenceConflictError("identity provider assurance conflicts")
                return
            self._connection.execute(
                "INSERT INTO identity_providers (issuer, privileged_assurance) VALUES (?, ?)",
                (provider.issuer, provider.privileged_assurance.value),
            )

    def bind_federated_actor(
        self,
        *,
        issuer: str,
        subject: str,
        proposed_actor: Actor,
    ) -> Actor:
        """Resolve or atomically create the immutable actor for an issuer/subject."""
        if not isinstance(proposed_actor, Actor):
            raise TypeError("proposed_actor must be an Actor")
        binding = FederatedIdentity(proposed_actor.actor_id, issuer, subject)
        with _immediate_transaction(self._connection):
            existing = self._connection.execute(
                """
                SELECT actors.actor_id, actors.created_at
                FROM federated_identities
                JOIN actors USING (actor_id)
                WHERE federated_identities.issuer = ? AND federated_identities.subject = ?
                """,
                (binding.issuer, binding.subject),
            ).fetchone()
            if existing is not None:
                return Actor(existing[0], _parse_datetime(existing[1]))
            self._connection.execute(
                "INSERT INTO actors (actor_id, created_at) VALUES (?, ?)",
                (proposed_actor.actor_id, _serialize_datetime(proposed_actor.created_at)),
            )
            self._connection.execute(
                "INSERT INTO federated_identities (issuer, subject, actor_id) VALUES (?, ?, ?)",
                (binding.issuer, binding.subject, binding.actor_id),
            )
        return proposed_actor

    def create_cohort(
        self,
        cohort: Cohort,
        initial_admin: CohortMembership,
    ) -> None:
        """Atomically provision a cohort and its operator-selected initial admin."""
        if not isinstance(cohort, Cohort):
            raise TypeError("cohort must be a Cohort")
        if not isinstance(initial_admin, CohortMembership):
            raise TypeError("initial_admin must be a CohortMembership")
        if (
            initial_admin.cohort_id != cohort.cohort_id
            or initial_admin.role is not CohortRole.COURSE_ADMIN
            or initial_admin.actor_id != initial_admin.granted_by_actor_id
            or not initial_admin.active
            or initial_admin.revision != 1
        ):
            raise PersistenceAuthorizationError(
                "initial membership must be an active self-recorded course-admin at revision 1"
            )
        with _immediate_transaction(self._connection):
            self._connection.execute(
                """
                INSERT INTO cohorts (
                    cohort_id, account_authority, created_at, closes_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    cohort.cohort_id,
                    cohort.account_authority,
                    _serialize_datetime(cohort.created_at),
                    _serialize_datetime(cohort.closes_at),
                ),
            )
            self._insert_membership(initial_admin)

    def grant_membership(self, membership: CohortMembership) -> None:
        """Insert one explicit cohort role; replacement requires a later audited command."""
        if not isinstance(membership, CohortMembership):
            raise TypeError("membership must be a CohortMembership")
        if not membership.active or membership.revision != 1:
            raise ValueError("a new membership must be active at revision 1")
        with _immediate_transaction(self._connection):
            grantor = self._connection.execute(
                """
                SELECT role, active FROM cohort_memberships
                WHERE cohort_id = ? AND actor_id = ?
                """,
                (membership.cohort_id, membership.granted_by_actor_id),
            ).fetchone()
            if grantor != (CohortRole.COURSE_ADMIN.value, 1):
                raise PersistenceAuthorizationError(
                    "only an active course-admin may assign cohort membership"
                )
            self._insert_membership(membership)

    def _insert_membership(self, membership: CohortMembership) -> None:
        self._connection.execute(
            """
            INSERT INTO cohort_memberships (
                cohort_id, actor_id, role, granted_by_actor_id, granted_at, active, revision
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                membership.cohort_id,
                membership.actor_id,
                membership.role.value,
                membership.granted_by_actor_id,
                _serialize_datetime(membership.granted_at),
                int(membership.active),
                membership.revision,
            ),
        )

    def create_namespace(self, namespace: PackageNamespace) -> None:
        """Claim one globally unique package ID for a current cohort member."""
        if not isinstance(namespace, PackageNamespace):
            raise TypeError("namespace must be a PackageNamespace")
        with _immediate_transaction(self._connection):
            owner = self._connection.execute(
                """
                SELECT active FROM cohort_memberships
                WHERE cohort_id = ? AND actor_id = ?
                """,
                (namespace.cohort_id, namespace.owner_actor_id),
            ).fetchone()
            if owner != (1,):
                raise PersistenceAuthorizationError(
                    "a package namespace owner must be an active cohort member"
                )
            self._connection.execute(
                """
                INSERT INTO package_namespaces (
                    package_id, cohort_id, owner_actor_id, created_at, revision
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    namespace.package_id,
                    namespace.cohort_id,
                    namespace.owner_actor_id,
                    _serialize_datetime(namespace.created_at),
                    namespace.revision,
                ),
            )

    def grant_namespace(self, grant: NamespaceGrant) -> None:
        """Insert an explicit namespace permission for a same-cohort actor."""
        if not isinstance(grant, NamespaceGrant):
            raise TypeError("grant must be a NamespaceGrant")
        with _immediate_transaction(self._connection):
            grantor = self._connection.execute(
                """
                SELECT role, active FROM cohort_memberships
                WHERE cohort_id = ? AND actor_id = ?
                """,
                (grant.cohort_id, grant.granted_by_actor_id),
            ).fetchone()
            if grantor != (CohortRole.COURSE_ADMIN.value, 1):
                raise PersistenceAuthorizationError(
                    "only an active course-admin may grant namespace permissions"
                )
            grantee = self._connection.execute(
                """
                SELECT active FROM cohort_memberships
                WHERE cohort_id = ? AND actor_id = ?
                """,
                (grant.cohort_id, grant.actor_id),
            ).fetchone()
            if grantee != (1,):
                raise PersistenceAuthorizationError(
                    "a namespace grantee must be an active cohort member"
                )
            self._connection.execute(
                """
                INSERT INTO namespace_grants (
                    package_id, cohort_id, actor_id, permission,
                    granted_by_actor_id, granted_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    grant.package_id,
                    grant.cohort_id,
                    grant.actor_id,
                    grant.permission.value,
                    grant.granted_by_actor_id,
                    _serialize_datetime(grant.granted_at),
                ),
            )

    def record_package_version(self, package: StoredPackageVersion) -> StoredPackageVersion:
        """Insert or replay one exact package ID/version/digest identity."""
        if not isinstance(package, StoredPackageVersion):
            raise TypeError("package must be a StoredPackageVersion")
        identity = package.identity
        with _immediate_transaction(self._connection):
            existing = self._connection.execute(
                """
                SELECT raw_zip_sha256, cohort_id, created_by_actor_id, created_at
                FROM package_versions
                WHERE package_id = ? AND package_version = ?
                """,
                (identity.package_id, identity.package_version),
            ).fetchone()
            if existing is not None:
                persisted = StoredPackageVersion(
                    PackageVersionIdentity(
                        identity.package_id, identity.package_version, existing[0]
                    ),
                    existing[1],
                    existing[2],
                    _parse_datetime(existing[3]),
                )
                if (
                    persisted.identity != package.identity
                    or persisted.cohort_id != package.cohort_id
                    or persisted.created_by_actor_id != package.created_by_actor_id
                ):
                    raise PersistenceConflictError(
                        "package ID/version already identifies different immutable bytes "
                        "or provenance"
                    )
                return persisted
            self._connection.execute(
                """
                INSERT INTO package_versions (
                    package_id, package_version, raw_zip_sha256,
                    cohort_id, created_by_actor_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    identity.package_id,
                    identity.package_version,
                    identity.raw_zip_sha256,
                    package.cohort_id,
                    package.created_by_actor_id,
                    _serialize_datetime(package.created_at),
                ),
            )
        return package

    def append_audit_event(self, event: AuditEvent) -> None:
        """Append one immutable event; duplicate IDs or operation keys fail closed."""
        if not isinstance(event, AuditEvent):
            raise TypeError("event must be an AuditEvent")
        with _immediate_transaction(self._connection):
            self._connection.execute(
                """
                INSERT INTO audit_events (
                    event_id, occurred_at, retention_until, principal_kind, principal_id,
                    initiating_actor_id, event_type, object_type, object_id,
                    cohort_id, idempotency_key, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    _serialize_datetime(event.occurred_at),
                    _serialize_datetime(event.retention_until),
                    event.principal_kind.value,
                    event.principal_id,
                    event.initiating_actor_id,
                    event.event_type,
                    event.object_type,
                    event.object_id,
                    event.cohort_id,
                    event.idempotency_key,
                    event.details_json,
                ),
            )

    def record_idempotent_result(self, record: IdempotencyRecord) -> IdempotencyRecord:
        """Store a completed mutation result or replay its identical prior result."""
        if not isinstance(record, IdempotencyRecord):
            raise TypeError("record must be an IdempotencyRecord")
        key = (
            record.principal_kind.value,
            record.principal_id,
            record.operation,
            record.idempotency_key,
        )
        with _immediate_transaction(self._connection):
            existing = self._connection.execute(
                """
                SELECT request_sha256, result_reference, created_at
                FROM idempotency_records
                WHERE principal_kind = ? AND principal_id = ?
                    AND operation = ? AND idempotency_key = ?
                """,
                key,
            ).fetchone()
            if existing is not None:
                if existing[0] != record.request_sha256:
                    raise IdempotencyConflictError(
                        "idempotency key was already used for different request bytes"
                    )
                return IdempotencyRecord(
                    record.principal_kind,
                    record.principal_id,
                    record.operation,
                    record.idempotency_key,
                    existing[0],
                    existing[1],
                    _parse_datetime(existing[2]),
                )
            self._connection.execute(
                """
                INSERT INTO idempotency_records (
                    principal_kind, principal_id, operation, idempotency_key,
                    request_sha256, result_reference, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    *key,
                    record.request_sha256,
                    record.result_reference,
                    _serialize_datetime(record.created_at),
                ),
            )
        return record

    def load_human_principal(
        self,
        actor_id: str,
        assurance: AssuranceLevel,
    ) -> HumanPrincipal:
        """Load authoritative membership and namespace grants for policy evaluation."""
        memberships = tuple(
            CohortMembership(
                cohort_id=row[0],
                actor_id=row[1],
                role=CohortRole(row[2]),
                granted_by_actor_id=row[3],
                granted_at=_parse_datetime(row[4]),
                active=bool(row[5]),
                revision=row[6],
            )
            for row in self._connection.execute(
                """
                SELECT cohort_id, actor_id, role, granted_by_actor_id,
                    granted_at, active, revision
                FROM cohort_memberships
                WHERE actor_id = ?
                ORDER BY cohort_id
                """,
                (actor_id,),
            )
        )
        grants = tuple(
            NamespaceGrant(
                package_id=row[0],
                cohort_id=row[1],
                actor_id=row[2],
                permission=NamespacePermission(row[3]),
                granted_by_actor_id=row[4],
                granted_at=_parse_datetime(row[5]),
            )
            for row in self._connection.execute(
                """
                SELECT package_id, cohort_id, actor_id, permission,
                    granted_by_actor_id, granted_at
                FROM namespace_grants
                WHERE actor_id = ?
                ORDER BY package_id, permission
                """,
                (actor_id,),
            )
        )
        return HumanPrincipal(actor_id, assurance, memberships, grants)
