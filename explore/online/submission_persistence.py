"""Atomic SQLite persistence for bounded Phase E package submission."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from explore.online.models import (
    Actor,
    IdempotencyRecord,
    PackageNamespace,
    PackageVersionIdentity,
    PrincipalKind,
)
from explore.online.persistence import PersistenceConflictError, SQLiteFoundationStore
from explore.online.submission_models import (
    PackageSubmission,
    PublicationAcknowledgment,
    PublicationAuthority,
    SubmissionState,
    SubmissionValidationOutcome,
)

SUBMISSION_SCHEMA_VERSION = 1

_SUBMISSION_SCHEMA = """
CREATE TABLE IF NOT EXISTS submission_schema_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1)
) STRICT;

INSERT OR IGNORE INTO submission_schema_metadata (singleton, schema_version) VALUES (1, 1);

CREATE UNIQUE INDEX IF NOT EXISTS package_versions_exact_digest
ON package_versions (package_id, package_version, raw_zip_sha256);

CREATE TABLE IF NOT EXISTS package_submissions (
    submission_id TEXT PRIMARY KEY CHECK (length(submission_id) = 36),
    package_id TEXT NOT NULL,
    package_version TEXT NOT NULL,
    raw_zip_sha256 TEXT NOT NULL CHECK (
        length(raw_zip_sha256) = 64
        AND raw_zip_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    cohort_id TEXT NOT NULL,
    submitted_by_actor_id TEXT NOT NULL,
    submitted_at TEXT NOT NULL CHECK (substr(submitted_at, -1) = 'Z'),
    artifact_retention_until TEXT NOT NULL CHECK (
        substr(artifact_retention_until, -1) = 'Z'
        AND artifact_retention_until > submitted_at
    ),
    state TEXT NOT NULL CHECK (state = 'reviewable'),
    validation_outcome TEXT NOT NULL CHECK (validation_outcome = 'valid'),
    validation_provenance_json TEXT NOT NULL,
    terms_version TEXT NOT NULL,
    license_policy_version TEXT NOT NULL,
    represented_authority TEXT NOT NULL CHECK (
        represented_authority IN ('self', 'institution-course-operator')
    ),
    archive_size INTEGER NOT NULL CHECK (archive_size > 0),
    archive_bytes BLOB NOT NULL CHECK (
        typeof(archive_bytes) = 'blob' AND length(archive_bytes) = archive_size
    ),
    UNIQUE (package_id, package_version),
    FOREIGN KEY (package_id, package_version, raw_zip_sha256)
        REFERENCES package_versions (package_id, package_version, raw_zip_sha256)
        ON DELETE RESTRICT,
    FOREIGN KEY (package_id, cohort_id)
        REFERENCES package_namespaces (package_id, cohort_id) ON DELETE RESTRICT,
    FOREIGN KEY (cohort_id, submitted_by_actor_id)
        REFERENCES cohort_memberships (cohort_id, actor_id) ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER IF NOT EXISTS package_submissions_no_update
BEFORE UPDATE ON package_submissions
BEGIN
    SELECT RAISE(ABORT, 'package submissions are immutable');
END;

CREATE TRIGGER IF NOT EXISTS package_submissions_no_delete
BEFORE DELETE ON package_submissions
BEGIN
    SELECT RAISE(ABORT, 'package submissions are immutable');
END;
"""


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class SubmissionPersistenceConflictError(PersistenceConflictError):
    """A submission identity or artifact conflicts with immutable storage."""


class SQLiteSubmissionStore(SQLiteFoundationStore):
    """Foundation store extended only with immutable submission persistence."""

    @classmethod
    def open(cls, path: str | Path) -> SQLiteSubmissionStore:
        return super().open(path)

    def initialize_schema(self) -> None:
        """Initialize foundation and submission schemas without changing foundation v1."""
        super().initialize_schema()
        self._connection.executescript(_SUBMISSION_SCHEMA)
        row = self._connection.execute(
            "SELECT schema_version FROM submission_schema_metadata WHERE singleton = 1"
        ).fetchone()
        if row != (SUBMISSION_SCHEMA_VERSION,):
            raise RuntimeError("unsupported Phase E submission schema version")

    def resolve_federated_actor(self, issuer: str, subject: str) -> Actor | None:
        """Resolve an existing immutable issuer/subject binding; never create one."""
        row = self._connection.execute(
            """
            SELECT actors.actor_id, actors.created_at
            FROM federated_identities
            JOIN actors USING (actor_id)
            WHERE federated_identities.issuer = ? AND federated_identities.subject = ?
            """,
            (issuer, subject),
        ).fetchone()
        if row is None:
            return None
        return Actor(row[0], _parse_datetime(row[1]))

    def load_namespace(self, package_id: str) -> PackageNamespace | None:
        """Load authoritative namespace ownership and cohort scope."""
        row = self._connection.execute(
            """
            SELECT package_id, cohort_id, owner_actor_id, created_at, revision
            FROM package_namespaces WHERE package_id = ?
            """,
            (package_id,),
        ).fetchone()
        if row is None:
            return None
        return PackageNamespace(row[0], row[1], row[2], _parse_datetime(row[3]), row[4])

    def load_cohort_closes_at(self, cohort_id: str) -> datetime | None:
        """Load the trusted cohort close time used to make namespace activity explicit."""
        row = self._connection.execute(
            "SELECT closes_at FROM cohorts WHERE cohort_id = ?",
            (cohort_id,),
        ).fetchone()
        return None if row is None else _parse_datetime(row[0])

    def load_idempotency_record(
        self,
        *,
        principal_kind: PrincipalKind,
        principal_id: str,
        operation: str,
        idempotency_key: str,
    ) -> IdempotencyRecord | None:
        """Load one immutable completed result for safe replay."""
        row = self._connection.execute(
            """
            SELECT request_sha256, result_reference, created_at
            FROM idempotency_records
            WHERE principal_kind = ? AND principal_id = ?
                AND operation = ? AND idempotency_key = ?
            """,
            (principal_kind.value, principal_id, operation, idempotency_key),
        ).fetchone()
        if row is None:
            return None
        return IdempotencyRecord(
            principal_kind,
            principal_id,
            operation,
            idempotency_key,
            row[0],
            row[1],
            _parse_datetime(row[2]),
        )

    def load_package_version(
        self,
        package_id: str,
        semantic_version: str,
    ) -> PackageVersionIdentity | None:
        """Load the immutable exact-version digest identity."""
        row = self._connection.execute(
            """
            SELECT raw_zip_sha256 FROM package_versions
            WHERE package_id = ? AND package_version = ?
            """,
            (package_id, semantic_version),
        ).fetchone()
        if row is None:
            return None
        return PackageVersionIdentity(package_id, semantic_version, row[0])

    def record_submission(
        self,
        submission: PackageSubmission,
        archive_bytes: bytes,
    ) -> None:
        """Insert one immutable reviewable submission and its exact artifact bytes."""
        if not isinstance(submission, PackageSubmission):
            raise TypeError("submission must be a PackageSubmission")
        if type(archive_bytes) is not bytes or not archive_bytes:
            raise TypeError("archive_bytes must be non-empty bytes")
        if hashlib.sha256(archive_bytes).hexdigest() != submission.package_version.raw_zip_sha256:
            raise SubmissionPersistenceConflictError(
                "artifact bytes do not match the immutable package-version digest"
            )
        provenance = json.loads(submission.validation_provenance_json)
        if provenance.get("archive_bytes") != len(archive_bytes):
            raise SubmissionPersistenceConflictError(
                "artifact bytes do not match persisted validation provenance"
            )
        try:
            self._connection.execute(
                """
                INSERT INTO package_submissions (
                    submission_id, package_id, package_version, raw_zip_sha256,
                    cohort_id, submitted_by_actor_id, submitted_at,
                    artifact_retention_until, state, validation_outcome,
                    validation_provenance_json, terms_version,
                    license_policy_version, represented_authority,
                    archive_size, archive_bytes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    submission.submission_id,
                    submission.package_version.package_id,
                    submission.package_version.package_version,
                    submission.package_version.raw_zip_sha256,
                    submission.cohort_id,
                    submission.submitted_by_actor_id,
                    _serialize_datetime(submission.submitted_at),
                    _serialize_datetime(submission.artifact_retention_until),
                    submission.state.value,
                    submission.validation_outcome.value,
                    submission.validation_provenance_json,
                    submission.acknowledgment.terms_version,
                    submission.acknowledgment.license_policy_version,
                    submission.acknowledgment.represented_authority.value,
                    len(archive_bytes),
                    archive_bytes,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise SubmissionPersistenceConflictError(
                "submission ID or exact package version already exists"
            ) from error

    def load_submission(self, submission_id: str) -> PackageSubmission | None:
        """Load immutable submission metadata without exposing artifact bytes."""
        row = self._connection.execute(
            """
            SELECT submission_id, package_id, package_version, raw_zip_sha256,
                cohort_id, submitted_by_actor_id, submitted_at,
                artifact_retention_until, state, validation_outcome,
                validation_provenance_json, terms_version,
                license_policy_version, represented_authority
            FROM package_submissions WHERE submission_id = ?
            """,
            (submission_id,),
        ).fetchone()
        if row is None:
            return None
        return PackageSubmission(
            submission_id=row[0],
            package_version=PackageVersionIdentity(row[1], row[2], row[3]),
            cohort_id=row[4],
            submitted_by_actor_id=row[5],
            submitted_at=_parse_datetime(row[6]),
            artifact_retention_until=_parse_datetime(row[7]),
            state=SubmissionState(row[8]),
            validation_outcome=SubmissionValidationOutcome(row[9]),
            validation_provenance_json=row[10],
            acknowledgment=PublicationAcknowledgment(
                row[11], row[12], PublicationAuthority(row[13])
            ),
        )

    def load_submission_artifact(self, submission_id: str) -> bytes | None:
        """Load exact immutable bytes for trusted review infrastructure."""
        row = self._connection.execute(
            "SELECT archive_bytes FROM package_submissions WHERE submission_id = ?",
            (submission_id,),
        ).fetchone()
        return None if row is None else bytes(row[0])


__all__ = [
    "SUBMISSION_SCHEMA_VERSION",
    "SQLiteSubmissionStore",
    "SubmissionPersistenceConflictError",
]
