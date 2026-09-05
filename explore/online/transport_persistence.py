"""SQLite persistence for one-time OIDC transactions and opaque staff sessions."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from explore.online.configuration_persistence import SQLiteClassWorldConfigurationStore
from explore.online.models import AssuranceLevel, CohortRole
from explore.online.transport_models import OIDCAuthorizationTransaction, StaffSession

TRANSPORT_SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS transport_schema_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1)
) STRICT;

INSERT OR IGNORE INTO transport_schema_metadata (singleton, schema_version) VALUES (1, 1);

CREATE TABLE IF NOT EXISTS oidc_authorization_transactions (
    state_digest TEXT PRIMARY KEY CHECK (length(state_digest) = 64),
    browser_digest TEXT NOT NULL UNIQUE CHECK (length(browser_digest) = 64),
    provider_id TEXT NOT NULL,
    nonce TEXT NOT NULL,
    code_verifier TEXT NOT NULL,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    expires_at TEXT NOT NULL CHECK (
        substr(expires_at, -1) = 'Z' AND expires_at > created_at
    )
) STRICT;

CREATE TABLE IF NOT EXISTS staff_sessions (
    session_digest TEXT PRIMARY KEY CHECK (length(session_digest) = 64),
    actor_id TEXT NOT NULL,
    issuer TEXT NOT NULL,
    subject TEXT NOT NULL,
    assurance TEXT NOT NULL CHECK (assurance IN ('aal1', 'aal2')),
    csrf_digest TEXT NOT NULL CHECK (length(csrf_digest) = 64),
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    idle_expires_at TEXT NOT NULL CHECK (
        substr(idle_expires_at, -1) = 'Z' AND idle_expires_at > created_at
    ),
    absolute_expires_at TEXT NOT NULL CHECK (
        substr(absolute_expires_at, -1) = 'Z' AND absolute_expires_at >= idle_expires_at
    ),
    last_seen_at TEXT NOT NULL CHECK (
        substr(last_seen_at, -1) = 'Z' AND last_seen_at >= created_at
    ),
    revoked_at TEXT CHECK (
        revoked_at IS NULL OR (substr(revoked_at, -1) = 'Z' AND revoked_at >= created_at)
    ),
    FOREIGN KEY (actor_id) REFERENCES actors (actor_id) ON DELETE RESTRICT,
    FOREIGN KEY (issuer, subject)
        REFERENCES federated_identities (issuer, subject) ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER IF NOT EXISTS staff_sessions_binding_guard
BEFORE INSERT ON staff_sessions
WHEN NOT EXISTS (
    SELECT 1 FROM federated_identities
    WHERE issuer = NEW.issuer AND subject = NEW.subject AND actor_id = NEW.actor_id
)
BEGIN
    SELECT RAISE(ABORT, 'staff session identity must match an immutable actor binding');
END;

CREATE INDEX IF NOT EXISTS staff_sessions_actor_active
ON staff_sessions (actor_id, revoked_at, absolute_expires_at);

CREATE TRIGGER IF NOT EXISTS staff_sessions_guard_update
BEFORE UPDATE ON staff_sessions
WHEN NEW.session_digest != OLD.session_digest
    OR NEW.actor_id != OLD.actor_id
    OR NEW.issuer != OLD.issuer
    OR NEW.subject != OLD.subject
    OR NEW.assurance != OLD.assurance
    OR NEW.csrf_digest != OLD.csrf_digest
    OR NEW.created_at != OLD.created_at
    OR NEW.absolute_expires_at != OLD.absolute_expires_at
    OR NEW.last_seen_at < OLD.last_seen_at
    OR NEW.idle_expires_at < OLD.idle_expires_at
    OR NEW.idle_expires_at > NEW.absolute_expires_at
    OR (OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS NOT OLD.revoked_at)
BEGIN
    SELECT RAISE(ABORT, 'staff session identity and revocation are immutable');
END;
"""


def _serialize(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must use UTC")


def _session(row: sqlite3.Row | tuple[object, ...]) -> StaffSession:
    return StaffSession(
        session_digest=str(row[0]),
        actor_id=str(row[1]),
        issuer=str(row[2]),
        subject=str(row[3]),
        assurance=AssuranceLevel(str(row[4])),
        csrf_digest=str(row[5]),
        created_at=_parse(str(row[6])),
        idle_expires_at=_parse(str(row[7])),
        absolute_expires_at=_parse(str(row[8])),
        last_seen_at=_parse(str(row[9])),
        revoked_at=None if row[10] is None else _parse(str(row[10])),
    )


class SQLiteStaffTransportStore(SQLiteClassWorldConfigurationStore):
    """Full Phase E reference store plus transport-only ephemeral state."""

    @classmethod
    def open(cls, path: str | Path) -> SQLiteStaffTransportStore:
        if not isinstance(path, (str, Path)):
            raise TypeError("path must be a string or Path")
        connection = sqlite3.connect(
            str(path),
            timeout=30.0,
            isolation_level=None,
            check_same_thread=False,
        )
        return cls(connection)

    def initialize_schema(self) -> None:
        super().initialize_schema()
        self._connection.executescript(_SCHEMA)
        row = self._connection.execute(
            "SELECT schema_version FROM transport_schema_metadata WHERE singleton = 1"
        ).fetchone()
        if row != (TRANSPORT_SCHEMA_VERSION,):
            raise RuntimeError("unsupported staff transport schema version")

    def identity_provider_assurance(self, issuer: str) -> AssuranceLevel | None:
        row = self._connection.execute(
            "SELECT privileged_assurance FROM identity_providers WHERE issuer = ?",
            (issuer,),
        ).fetchone()
        return None if row is None else AssuranceLevel(str(row[0]))

    def append_authorization_transaction(
        self,
        transaction: OIDCAuthorizationTransaction,
    ) -> None:
        with self.transaction():
            self._connection.execute(
                """
                INSERT INTO oidc_authorization_transactions (
                    state_digest, browser_digest, provider_id, nonce, code_verifier,
                    created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction.state_digest,
                    transaction.browser_digest,
                    transaction.provider_id,
                    transaction.nonce,
                    transaction.code_verifier,
                    _serialize(transaction.created_at),
                    _serialize(transaction.expires_at),
                ),
            )

    def consume_authorization_transaction(
        self,
        *,
        state_digest: str,
        browser_digest: str,
        provider_id: str,
        now: datetime,
    ) -> OIDCAuthorizationTransaction | None:
        _require_utc(now, "now")
        with self.transaction():
            row = self._connection.execute(
                """
                SELECT provider_id, state_digest, browser_digest, nonce, code_verifier,
                       created_at, expires_at
                FROM oidc_authorization_transactions
                WHERE state_digest = ? AND browser_digest = ? AND provider_id = ?
                """,
                (state_digest, browser_digest, provider_id),
            ).fetchone()
            if row is None:
                return None
            if _parse(str(row[6])) <= now:
                self._connection.execute(
                    "DELETE FROM oidc_authorization_transactions WHERE state_digest = ?",
                    (state_digest,),
                )
                return None
            changed = self._connection.execute(
                """
                DELETE FROM oidc_authorization_transactions WHERE state_digest = ?
                """,
                (state_digest,),
            ).rowcount
            if changed != 1:
                return None
            return OIDCAuthorizationTransaction(
                provider_id=str(row[0]),
                state_digest=str(row[1]),
                browser_digest=str(row[2]),
                nonce=str(row[3]),
                code_verifier=str(row[4]),
                created_at=_parse(str(row[5])),
                expires_at=_parse(str(row[6])),
                consumed_at=now,
            )

    def purge_expired_authorization_transactions(self, *, now: datetime) -> int:
        """Remove expired PKCE verifiers and nonces through an internal lifecycle hook."""
        _require_utc(now, "now")
        with self.transaction():
            return self._connection.execute(
                "DELETE FROM oidc_authorization_transactions WHERE expires_at <= ?",
                (_serialize(now),),
            ).rowcount

    def append_staff_session(self, session: StaffSession) -> bool:
        """Create only while the immutable binding and staff authority are current."""
        with self.transaction():
            return (
                self._connection.execute(
                    """
                INSERT INTO staff_sessions (
                    session_digest, actor_id, issuer, subject, assurance, csrf_digest,
                    created_at, idle_expires_at, absolute_expires_at, last_seen_at, revoked_at
                )
                SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL
                WHERE EXISTS (
                    SELECT 1 FROM identity_providers
                    WHERE issuer = ? AND privileged_assurance = ?
                )
                AND EXISTS (
                    SELECT 1 FROM federated_identities
                    WHERE issuer = ? AND subject = ? AND actor_id = ?
                )
                AND EXISTS (
                    SELECT 1 FROM cohort_memberships
                    JOIN cohorts USING (cohort_id)
                    WHERE actor_id = ? AND active = 1
                      AND role IN (?, ?) AND closes_at > ?
                )
                """,
                    (
                        session.session_digest,
                        session.actor_id,
                        session.issuer,
                        session.subject,
                        session.assurance.value,
                        session.csrf_digest,
                        _serialize(session.created_at),
                        _serialize(session.idle_expires_at),
                        _serialize(session.absolute_expires_at),
                        _serialize(session.last_seen_at),
                        session.issuer,
                        AssuranceLevel.AAL2.value,
                        session.issuer,
                        session.subject,
                        session.actor_id,
                        session.actor_id,
                        CohortRole.TEACHER.value,
                        CohortRole.COURSE_ADMIN.value,
                        _serialize(session.created_at),
                    ),
                ).rowcount
                == 1
            )

    def load_active_staff_session(
        self,
        *,
        session_digest: str,
        now: datetime,
        idle_ttl: timedelta,
    ) -> StaffSession | None:
        _require_utc(now, "now")
        with self.transaction():
            row = self._connection.execute(
                """
                SELECT session_digest, actor_id, issuer, subject, assurance, csrf_digest,
                       created_at, idle_expires_at, absolute_expires_at, last_seen_at, revoked_at
                FROM staff_sessions WHERE session_digest = ?
                """,
                (session_digest,),
            ).fetchone()
            if row is None:
                return None
            current = _session(row)
            if (
                current.revoked_at is not None
                or current.idle_expires_at <= now
                or current.absolute_expires_at <= now
            ):
                if current.revoked_at is None:
                    self._connection.execute(
                        "UPDATE staff_sessions SET revoked_at = ? WHERE session_digest = ?",
                        (_serialize(now), session_digest),
                    )
                return None
            next_idle = min(now + idle_ttl, current.absolute_expires_at)
            self._connection.execute(
                """
                UPDATE staff_sessions SET idle_expires_at = ?, last_seen_at = ?
                WHERE session_digest = ? AND revoked_at IS NULL
                """,
                (_serialize(next_idle), _serialize(now), session_digest),
            )
            return StaffSession(
                session_digest=current.session_digest,
                actor_id=current.actor_id,
                issuer=current.issuer,
                subject=current.subject,
                assurance=current.assurance,
                csrf_digest=current.csrf_digest,
                created_at=current.created_at,
                idle_expires_at=next_idle,
                absolute_expires_at=current.absolute_expires_at,
                last_seen_at=now,
            )

    def revoke_staff_session(self, *, session_digest: str, now: datetime) -> bool:
        _require_utc(now, "now")
        with self.transaction():
            return (
                self._connection.execute(
                    """
                    UPDATE staff_sessions SET revoked_at = ?
                    WHERE session_digest = ? AND revoked_at IS NULL
                    """,
                    (_serialize(now), session_digest),
                ).rowcount
                == 1
            )

    def revoke_actor_sessions(self, *, actor_id: str, now: datetime) -> int:
        """Revocation hook for membership, recovery, or incident workflows."""
        _require_utc(now, "now")
        with self.transaction():
            return self._connection.execute(
                """
                UPDATE staff_sessions SET revoked_at = ?
                WHERE actor_id = ? AND revoked_at IS NULL
                """,
                (_serialize(now), actor_id),
            ).rowcount

    def revoke_issuer_sessions(self, *, issuer: str, now: datetime) -> int:
        """Revocation hook for an IdP compromise or deconfiguration event."""
        _require_utc(now, "now")
        with self.transaction():
            return self._connection.execute(
                """
                UPDATE staff_sessions SET revoked_at = ?
                WHERE issuer = ? AND revoked_at IS NULL
                """,
                (_serialize(now), issuer),
            ).rowcount

    def purge_inactive_staff_sessions(self, *, before: datetime) -> int:
        """Remove expired or revoked session material through an internal lifecycle hook."""
        _require_utc(before, "before")
        with self.transaction():
            return self._connection.execute(
                """
                DELETE FROM staff_sessions
                WHERE absolute_expires_at <= ? OR (revoked_at IS NOT NULL AND revoked_at <= ?)
                """,
                (_serialize(before), _serialize(before)),
            ).rowcount

    def actor_is_current_staff(self, actor_id: str, *, now: datetime) -> bool:
        _require_utc(now, "now")
        row = self._connection.execute(
            """
            SELECT 1 FROM cohort_memberships
            JOIN cohorts USING (cohort_id)
            WHERE actor_id = ? AND active = 1
              AND role IN (?, ?) AND closes_at > ?
            LIMIT 1
            """,
            (
                actor_id,
                CohortRole.TEACHER.value,
                CohortRole.COURSE_ADMIN.value,
                _serialize(now),
            ),
        ).fetchone()
        return row is not None


__all__ = ["TRANSPORT_SCHEMA_VERSION", "SQLiteStaffTransportStore"]
