"""Append-only SQLite persistence for Phase E review decisions."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from explore.online.models import AssuranceLevel, CohortRole, PackageVersionIdentity
from explore.online.persistence import PersistenceConflictError
from explore.online.review_models import (
    PackageReviewDecision,
    ReviewAction,
    ReviewerMembershipSnapshot,
    ReviewState,
)
from explore.online.submission_persistence import SQLiteSubmissionStore

REVIEW_SCHEMA_VERSION = 1

_REVIEW_SCHEMA = """
CREATE TABLE IF NOT EXISTS review_schema_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1)
) STRICT;

INSERT OR IGNORE INTO review_schema_metadata (singleton, schema_version) VALUES (1, 1);

CREATE UNIQUE INDEX IF NOT EXISTS package_submissions_exact_identity
ON package_submissions (
    submission_id, package_id, package_version, raw_zip_sha256, cohort_id
);

CREATE TABLE IF NOT EXISTS package_review_decisions (
    decision_id TEXT PRIMARY KEY CHECK (length(decision_id) = 36),
    submission_id TEXT NOT NULL,
    sequence INTEGER NOT NULL CHECK (sequence >= 1),
    action TEXT NOT NULL CHECK (action IN ('approve', 'reject', 'revoke')),
    from_state TEXT NOT NULL CHECK (
        from_state IN ('reviewable', 'approved', 'rejected', 'revoked')
    ),
    to_state TEXT NOT NULL CHECK (
        to_state IN ('reviewable', 'approved', 'rejected', 'revoked')
    ),
    package_id TEXT NOT NULL,
    package_version TEXT NOT NULL,
    raw_zip_sha256 TEXT NOT NULL CHECK (
        length(raw_zip_sha256) = 64
        AND raw_zip_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    cohort_id TEXT NOT NULL,
    decided_by_actor_id TEXT NOT NULL,
    reviewer_role TEXT NOT NULL CHECK (reviewer_role IN ('teacher', 'course-admin')),
    reviewer_assurance TEXT NOT NULL CHECK (reviewer_assurance = 'aal2'),
    membership_granted_by_actor_id TEXT NOT NULL,
    membership_granted_at TEXT NOT NULL CHECK (substr(membership_granted_at, -1) = 'Z'),
    membership_revision INTEGER NOT NULL CHECK (membership_revision >= 1),
    membership_active INTEGER NOT NULL CHECK (membership_active = 1),
    reason TEXT NOT NULL,
    result_metadata_json TEXT NOT NULL,
    decided_at TEXT NOT NULL CHECK (substr(decided_at, -1) = 'Z'),
    correlation_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    UNIQUE (submission_id, sequence),
    CHECK (
        (action = 'approve' AND from_state = 'reviewable' AND to_state = 'approved')
        OR (action = 'reject' AND from_state = 'reviewable' AND to_state = 'rejected')
        OR (action = 'revoke' AND from_state = 'approved' AND to_state = 'revoked')
    ),
    FOREIGN KEY (
        submission_id, package_id, package_version, raw_zip_sha256, cohort_id
    ) REFERENCES package_submissions (
        submission_id, package_id, package_version, raw_zip_sha256, cohort_id
    ) ON DELETE RESTRICT,
    FOREIGN KEY (decided_by_actor_id) REFERENCES actors (actor_id) ON DELETE RESTRICT,
    FOREIGN KEY (membership_granted_by_actor_id) REFERENCES actors (actor_id) ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER IF NOT EXISTS package_review_decisions_no_update
BEFORE UPDATE ON package_review_decisions
BEGIN
    SELECT RAISE(ABORT, 'package review decisions are append-only');
END;

CREATE TRIGGER IF NOT EXISTS package_review_decisions_no_delete
BEFORE DELETE ON package_review_decisions
BEGIN
    SELECT RAISE(ABORT, 'package review decisions are append-only');
END;
"""


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ReviewPersistenceConflictError(PersistenceConflictError):
    """A decision conflicts with the append-only transition log."""


class SQLiteReviewStore(SQLiteSubmissionStore):
    """Submission store extended only with immutable review decisions."""

    @classmethod
    def open(cls, path: str | Path) -> SQLiteReviewStore:
        return super().open(path)

    def initialize_schema(self) -> None:
        super().initialize_schema()
        self._connection.executescript(_REVIEW_SCHEMA)
        row = self._connection.execute(
            "SELECT schema_version FROM review_schema_metadata WHERE singleton = 1"
        ).fetchone()
        if row != (REVIEW_SCHEMA_VERSION,):
            raise RuntimeError("unsupported Phase E review schema version")

    def load_review_state(self, submission_id: str) -> ReviewState:
        """Derive current state from the immutable submission and decision log."""
        row = self._connection.execute(
            """
            SELECT to_state FROM package_review_decisions
            WHERE submission_id = ? ORDER BY sequence DESC LIMIT 1
            """,
            (submission_id,),
        ).fetchone()
        return ReviewState.REVIEWABLE if row is None else ReviewState(row[0])

    def next_review_sequence(self, submission_id: str) -> int:
        """Return the next sequence while the caller holds the write transaction."""
        row = self._connection.execute(
            """
            SELECT COALESCE(MAX(sequence), 0) + 1
            FROM package_review_decisions WHERE submission_id = ?
            """,
            (submission_id,),
        ).fetchone()
        assert row is not None
        return int(row[0])

    def append_review_decision(self, decision: PackageReviewDecision) -> None:
        """Append one immutable state transition; never update submission or artifact."""
        if not isinstance(decision, PackageReviewDecision):
            raise TypeError("decision must be a PackageReviewDecision")
        current_state = self.load_review_state(decision.submission_id)
        next_sequence = self.next_review_sequence(decision.submission_id)
        if decision.from_state is not current_state or decision.sequence != next_sequence:
            raise ReviewPersistenceConflictError(
                "decision conflicts with the current append-only transition log"
            )
        membership = decision.membership
        package = decision.package_version
        try:
            self._connection.execute(
                """
                INSERT INTO package_review_decisions (
                    decision_id, submission_id, sequence, action, from_state, to_state,
                    package_id, package_version, raw_zip_sha256, cohort_id,
                    decided_by_actor_id, reviewer_role, reviewer_assurance,
                    membership_granted_by_actor_id, membership_granted_at,
                    membership_revision, membership_active, reason,
                    result_metadata_json, decided_at, correlation_id, idempotency_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.decision_id,
                    decision.submission_id,
                    decision.sequence,
                    decision.action.value,
                    decision.from_state.value,
                    decision.to_state.value,
                    package.package_id,
                    package.package_version,
                    package.raw_zip_sha256,
                    membership.cohort_id,
                    membership.actor_id,
                    membership.role.value,
                    membership.assurance.value,
                    membership.granted_by_actor_id,
                    _serialize_datetime(membership.granted_at),
                    membership.revision,
                    int(membership.active),
                    decision.reason,
                    decision.result_metadata_json,
                    _serialize_datetime(decision.decided_at),
                    decision.correlation_id,
                    decision.idempotency_key,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ReviewPersistenceConflictError(
                "decision conflicts with the current append-only transition log"
            ) from error

    def load_review_decision(self, decision_id: str) -> PackageReviewDecision | None:
        """Load one immutable review decision by opaque identity."""
        row = self._connection.execute(
            """
            SELECT decision_id, submission_id, sequence, action, from_state, to_state,
                package_id, package_version, raw_zip_sha256, cohort_id,
                decided_by_actor_id, reviewer_role, reviewer_assurance,
                membership_granted_by_actor_id, membership_granted_at,
                membership_revision, membership_active, reason,
                result_metadata_json, decided_at, correlation_id, idempotency_key
            FROM package_review_decisions WHERE decision_id = ?
            """,
            (decision_id,),
        ).fetchone()
        if row is None:
            return None
        return PackageReviewDecision(
            decision_id=row[0],
            submission_id=row[1],
            sequence=row[2],
            action=ReviewAction(row[3]),
            from_state=ReviewState(row[4]),
            to_state=ReviewState(row[5]),
            package_version=PackageVersionIdentity(row[6], row[7], row[8]),
            membership=ReviewerMembershipSnapshot(
                cohort_id=row[9],
                actor_id=row[10],
                role=CohortRole(row[11]),
                assurance=AssuranceLevel(row[12]),
                granted_by_actor_id=row[13],
                granted_at=_parse_datetime(row[14]),
                revision=row[15],
                active=bool(row[16]),
            ),
            reason=row[17],
            result_metadata_json=row[18],
            decided_at=_parse_datetime(row[19]),
            correlation_id=row[20],
            idempotency_key=row[21],
        )


__all__ = [
    "REVIEW_SCHEMA_VERSION",
    "ReviewPersistenceConflictError",
    "SQLiteReviewStore",
]
