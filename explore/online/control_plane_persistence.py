"""Atomic SQLite persistence for authenticated Phase E control-plane transitions."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from explore.online.control_plane_models import (
    ControlPlaneAction,
    ControlPlaneAuthoritySnapshot,
    ControlPlaneTransition,
    NamespaceGrantState,
)
from explore.online.models import (
    AssuranceLevel,
    CohortMembership,
    CohortRole,
    NamespaceGrant,
    NamespacePermission,
    PackageNamespace,
)
from explore.online.persistence import PersistenceConflictError
from explore.online.pinning_persistence import SQLitePinningStore

CONTROL_PLANE_SCHEMA_VERSION = 1

_CONTROL_PLANE_SCHEMA = """
CREATE TABLE IF NOT EXISTS control_plane_schema_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1)
) STRICT;

INSERT OR IGNORE INTO control_plane_schema_metadata (singleton, schema_version) VALUES (1, 1);

CREATE TRIGGER IF NOT EXISTS control_plane_actors_no_update
BEFORE UPDATE ON actors
BEGIN
    SELECT RAISE(ABORT, 'actor identities are immutable');
END;

CREATE TRIGGER IF NOT EXISTS control_plane_actors_no_delete
BEFORE DELETE ON actors
BEGIN
    SELECT RAISE(ABORT, 'actor identities are immutable');
END;

CREATE TRIGGER IF NOT EXISTS control_plane_memberships_no_delete
BEFORE DELETE ON cohort_memberships
BEGIN
    SELECT RAISE(ABORT, 'membership identities must be revoked, not deleted');
END;

CREATE TRIGGER IF NOT EXISTS control_plane_namespaces_no_delete
BEFORE DELETE ON package_namespaces
BEGIN
    SELECT RAISE(ABORT, 'package namespace identities are immutable');
END;

CREATE TABLE IF NOT EXISTS namespace_grant_states (
    package_id TEXT NOT NULL,
    cohort_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    permission TEXT NOT NULL CHECK (permission = 'submit'),
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    PRIMARY KEY (package_id, actor_id, permission),
    FOREIGN KEY (package_id, cohort_id)
        REFERENCES package_namespaces (package_id, cohort_id) ON DELETE RESTRICT,
    FOREIGN KEY (cohort_id, actor_id)
        REFERENCES cohort_memberships (cohort_id, actor_id) ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER IF NOT EXISTS namespace_grant_states_revision_guard
BEFORE UPDATE ON namespace_grant_states
WHEN NEW.package_id != OLD.package_id
    OR NEW.cohort_id != OLD.cohort_id
    OR NEW.actor_id != OLD.actor_id
    OR NEW.permission != OLD.permission
    OR NEW.active = OLD.active
    OR NEW.revision != OLD.revision + 1
BEGIN
    SELECT RAISE(ABORT, 'namespace grant updates require one state change and next revision');
END;

CREATE TRIGGER IF NOT EXISTS namespace_grant_states_no_delete
BEFORE DELETE ON namespace_grant_states
BEGIN
    SELECT RAISE(ABORT, 'namespace grant state identities are immutable');
END;

CREATE TABLE IF NOT EXISTS control_plane_transitions (
    transition_id TEXT PRIMARY KEY CHECK (length(transition_id) = 36),
    action TEXT NOT NULL CHECK (action IN (
        'membership-create', 'membership-change', 'membership-revoke',
        'namespace-claim', 'namespace-grant', 'namespace-grant-revoke',
        'namespace-transfer'
    )),
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    cohort_id TEXT NOT NULL,
    acted_by_actor_id TEXT NOT NULL,
    authority_role TEXT NOT NULL CHECK (authority_role = 'course-admin'),
    authority_assurance TEXT NOT NULL CHECK (authority_assurance = 'aal2'),
    authority_granted_by_actor_id TEXT NOT NULL,
    authority_granted_at TEXT NOT NULL CHECK (substr(authority_granted_at, -1) = 'Z'),
    authority_revision INTEGER NOT NULL CHECK (authority_revision >= 1),
    authority_active INTEGER NOT NULL CHECK (authority_active = 1),
    occurred_at TEXT NOT NULL CHECK (substr(occurred_at, -1) = 'Z'),
    correlation_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    change_json TEXT NOT NULL,
    FOREIGN KEY (cohort_id) REFERENCES cohorts (cohort_id) ON DELETE RESTRICT,
    FOREIGN KEY (acted_by_actor_id) REFERENCES actors (actor_id) ON DELETE RESTRICT,
    FOREIGN KEY (authority_granted_by_actor_id)
        REFERENCES actors (actor_id) ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER IF NOT EXISTS control_plane_transitions_no_update
BEFORE UPDATE ON control_plane_transitions
BEGIN
    SELECT RAISE(ABORT, 'control-plane transitions are append-only');
END;

CREATE TRIGGER IF NOT EXISTS control_plane_transitions_no_delete
BEFORE DELETE ON control_plane_transitions
BEGIN
    SELECT RAISE(ABORT, 'control-plane transitions are append-only');
END;
"""


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ControlPlanePersistenceConflictError(PersistenceConflictError):
    """A control-plane transition conflicts with authoritative current state."""


class SQLiteControlPlaneStore(SQLitePinningStore):
    """Full Phase E reference store extended with control-plane state transitions."""

    @classmethod
    def open(cls, path: str | Path) -> SQLiteControlPlaneStore:
        return super().open(path)

    def initialize_schema(self) -> None:
        """Initialize the existing full Phase E stack plus the additive control plane."""
        super().initialize_schema()
        self._connection.executescript(_CONTROL_PLANE_SCHEMA)
        self._connection.execute("""
            INSERT OR IGNORE INTO namespace_grant_states (
                package_id, cohort_id, actor_id, permission, active, revision
            )
            SELECT package_id, cohort_id, actor_id, permission, 1, 1
            FROM namespace_grants
            """)
        row = self._connection.execute(
            "SELECT schema_version FROM control_plane_schema_metadata WHERE singleton = 1"
        ).fetchone()
        if row != (CONTROL_PLANE_SCHEMA_VERSION,):
            raise RuntimeError("unsupported Phase E control-plane schema version")

    def actor_exists(self, actor_id: str) -> bool:
        """Return whether one immutable internal actor identity exists."""
        row = self._connection.execute(
            "SELECT 1 FROM actors WHERE actor_id = ?",
            (actor_id,),
        ).fetchone()
        return row == (1,)

    def load_membership(self, cohort_id: str, actor_id: str) -> CohortMembership | None:
        """Load one authoritative current membership."""
        row = self._connection.execute(
            """
            SELECT cohort_id, actor_id, role, granted_by_actor_id,
                granted_at, active, revision
            FROM cohort_memberships WHERE cohort_id = ? AND actor_id = ?
            """,
            (cohort_id, actor_id),
        ).fetchone()
        if row is None:
            return None
        return CohortMembership(
            cohort_id=row[0],
            actor_id=row[1],
            role=CohortRole(row[2]),
            granted_by_actor_id=row[3],
            granted_at=_parse_datetime(row[4]),
            active=bool(row[5]),
            revision=row[6],
        )

    def insert_membership(self, membership: CohortMembership) -> None:
        """Insert a revision-one membership while an application transaction is held."""
        try:
            self._connection.execute(
                """
                INSERT INTO cohort_memberships (
                    cohort_id, actor_id, role, granted_by_actor_id,
                    granted_at, active, revision
                ) VALUES (?, ?, ?, ?, ?, 1, 1)
                """,
                (
                    membership.cohort_id,
                    membership.actor_id,
                    membership.role.value,
                    membership.granted_by_actor_id,
                    _serialize_datetime(membership.granted_at),
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ControlPlanePersistenceConflictError(
                "membership identity is not absent at expected revision 0"
            ) from error

    def update_membership(
        self,
        *,
        current: CohortMembership,
        role: CohortRole,
        active: bool,
    ) -> CohortMembership:
        """Replace mutable membership state at exactly the next revision."""
        cursor = self._connection.execute(
            """
            UPDATE cohort_memberships
            SET role = ?, active = ?, revision = revision + 1
            WHERE cohort_id = ? AND actor_id = ? AND revision = ?
                AND role = ? AND active = ?
            """,
            (
                role.value,
                int(active),
                current.cohort_id,
                current.actor_id,
                current.revision,
                current.role.value,
                int(current.active),
            ),
        )
        if cursor.rowcount != 1:
            raise ControlPlanePersistenceConflictError(
                "membership changed after the expected revision"
            )
        updated = self.load_membership(current.cohort_id, current.actor_id)
        if updated is None:
            raise RuntimeError("updated membership disappeared")
        return updated

    def insert_namespace(self, namespace: PackageNamespace) -> None:
        """Insert one globally absent immutable package namespace identity."""
        try:
            self._connection.execute(
                """
                INSERT INTO package_namespaces (
                    package_id, cohort_id, owner_actor_id, created_at, revision
                ) VALUES (?, ?, ?, ?, 1)
                """,
                (
                    namespace.package_id,
                    namespace.cohort_id,
                    namespace.owner_actor_id,
                    _serialize_datetime(namespace.created_at),
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ControlPlanePersistenceConflictError(
                "global package namespace is not absent at expected revision 0"
            ) from error

    def transfer_namespace(
        self,
        *,
        namespace: PackageNamespace,
        new_owner_actor_id: str,
    ) -> PackageNamespace:
        """Replace only namespace owner metadata at the exact next revision."""
        try:
            cursor = self._connection.execute(
                """
                UPDATE package_namespaces
                SET owner_actor_id = ?, revision = revision + 1
                WHERE package_id = ? AND cohort_id = ? AND revision = ?
                    AND owner_actor_id = ?
                """,
                (
                    new_owner_actor_id,
                    namespace.package_id,
                    namespace.cohort_id,
                    namespace.revision,
                    namespace.owner_actor_id,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ControlPlanePersistenceConflictError(
                "new namespace owner is outside the authoritative cohort"
            ) from error
        if cursor.rowcount != 1:
            raise ControlPlanePersistenceConflictError(
                "namespace changed after the expected revision"
            )
        updated = self.load_namespace(namespace.package_id)
        if updated is None:
            raise RuntimeError("updated namespace disappeared")
        return updated

    def load_namespace_grant_state(
        self,
        package_id: str,
        actor_id: str,
    ) -> NamespaceGrantState | None:
        """Load the optimistic state of one explicit submit grant."""
        row = self._connection.execute(
            """
            SELECT package_id, cohort_id, actor_id, permission, active, revision
            FROM namespace_grant_states
            WHERE package_id = ? AND actor_id = ? AND permission = 'submit'
            """,
            (package_id, actor_id),
        ).fetchone()
        if row is None:
            return None
        return NamespaceGrantState(
            package_id=row[0],
            cohort_id=row[1],
            actor_id=row[2],
            permission=NamespacePermission(row[3]),
            active=bool(row[4]),
            revision=row[5],
        )

    def activate_namespace_grant(
        self,
        *,
        grant: NamespaceGrant,
        expected_revision: int,
    ) -> NamespaceGrantState:
        """Create or reactivate one submit grant with optimistic state."""
        current = self.load_namespace_grant_state(grant.package_id, grant.actor_id)
        if current is None:
            if expected_revision != 0:
                raise ControlPlanePersistenceConflictError(
                    "namespace grant is absent at the expected revision"
                )
            try:
                self._connection.execute(
                    """
                    INSERT INTO namespace_grant_states (
                        package_id, cohort_id, actor_id, permission, active, revision
                    ) VALUES (?, ?, ?, ?, 1, 1)
                    """,
                    (
                        grant.package_id,
                        grant.cohort_id,
                        grant.actor_id,
                        grant.permission.value,
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise ControlPlanePersistenceConflictError(
                    "namespace grant identity conflicts with authoritative scope"
                ) from error
        else:
            if current.active or current.revision != expected_revision:
                raise ControlPlanePersistenceConflictError(
                    "namespace grant changed after the expected revision"
                )
            cursor = self._connection.execute(
                """
                UPDATE namespace_grant_states
                SET active = 1, revision = revision + 1
                WHERE package_id = ? AND actor_id = ? AND permission = 'submit'
                    AND active = 0 AND revision = ?
                """,
                (grant.package_id, grant.actor_id, expected_revision),
            )
            if cursor.rowcount != 1:
                raise ControlPlanePersistenceConflictError(
                    "namespace grant changed after the expected revision"
                )
        try:
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
        except sqlite3.IntegrityError as error:
            raise ControlPlanePersistenceConflictError(
                "namespace grant is already active or outside authoritative scope"
            ) from error
        state = self.load_namespace_grant_state(grant.package_id, grant.actor_id)
        if state is None:
            raise RuntimeError("activated namespace grant state disappeared")
        return state

    def revoke_namespace_grant(
        self,
        *,
        state: NamespaceGrantState,
    ) -> NamespaceGrantState:
        """Deactivate an exact current grant without deleting its state identity."""
        if not state.active:
            raise ControlPlanePersistenceConflictError("namespace grant is not active")
        deleted = self._connection.execute(
            """
            DELETE FROM namespace_grants
            WHERE package_id = ? AND actor_id = ? AND permission = ?
            """,
            (state.package_id, state.actor_id, state.permission.value),
        )
        if deleted.rowcount != 1:
            raise ControlPlanePersistenceConflictError(
                "namespace grant current state is inconsistent"
            )
        updated = self._connection.execute(
            """
            UPDATE namespace_grant_states
            SET active = 0, revision = revision + 1
            WHERE package_id = ? AND actor_id = ? AND permission = ?
                AND active = 1 AND revision = ?
            """,
            (
                state.package_id,
                state.actor_id,
                state.permission.value,
                state.revision,
            ),
        )
        if updated.rowcount != 1:
            raise ControlPlanePersistenceConflictError(
                "namespace grant changed after the expected revision"
            )
        result = self.load_namespace_grant_state(state.package_id, state.actor_id)
        if result is None:
            raise RuntimeError("revoked namespace grant state disappeared")
        return result

    def append_control_plane_transition(self, transition: ControlPlaneTransition) -> None:
        """Append one immutable successful control-plane transition."""
        if not isinstance(transition, ControlPlaneTransition):
            raise TypeError("transition must be a ControlPlaneTransition")
        authority = transition.authority
        try:
            self._connection.execute(
                """
                INSERT INTO control_plane_transitions (
                    transition_id, action, object_type, object_id, cohort_id,
                    acted_by_actor_id, authority_role, authority_assurance,
                    authority_granted_by_actor_id, authority_granted_at,
                    authority_revision, authority_active, occurred_at,
                    correlation_id, idempotency_key, change_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transition.transition_id,
                    transition.action.value,
                    transition.object_type,
                    transition.object_id,
                    transition.cohort_id,
                    authority.actor_id,
                    authority.role.value,
                    authority.assurance.value,
                    authority.granted_by_actor_id,
                    _serialize_datetime(authority.granted_at),
                    authority.revision,
                    int(authority.active),
                    _serialize_datetime(transition.occurred_at),
                    transition.correlation_id,
                    transition.idempotency_key,
                    transition.change_json,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ControlPlanePersistenceConflictError(
                "control-plane transition identity conflicts"
            ) from error

    def load_control_plane_transition(
        self,
        transition_id: str,
    ) -> ControlPlaneTransition | None:
        """Load one immutable transition for safe idempotent replay."""
        row = self._connection.execute(
            """
            SELECT transition_id, action, object_type, object_id, cohort_id,
                acted_by_actor_id, authority_role, authority_assurance,
                authority_granted_by_actor_id, authority_granted_at,
                authority_revision, authority_active, occurred_at,
                correlation_id, idempotency_key, change_json
            FROM control_plane_transitions WHERE transition_id = ?
            """,
            (transition_id,),
        ).fetchone()
        if row is None:
            return None
        return ControlPlaneTransition(
            transition_id=row[0],
            action=ControlPlaneAction(row[1]),
            object_type=row[2],
            object_id=row[3],
            cohort_id=row[4],
            authority=ControlPlaneAuthoritySnapshot(
                cohort_id=row[4],
                actor_id=row[5],
                role=CohortRole(row[6]),
                assurance=AssuranceLevel(row[7]),
                granted_by_actor_id=row[8],
                granted_at=_parse_datetime(row[9]),
                revision=row[10],
                active=bool(row[11]),
            ),
            occurred_at=_parse_datetime(row[12]),
            correlation_id=row[13],
            idempotency_key=row[14],
            change_json=row[15],
        )


__all__ = [
    "CONTROL_PLANE_SCHEMA_VERSION",
    "ControlPlanePersistenceConflictError",
    "SQLiteControlPlaneStore",
]
