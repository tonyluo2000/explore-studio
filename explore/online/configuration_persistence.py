"""Immutable SQLite persistence for authoritative Class-World configurations."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from explore.online.configuration_models import (
    ConfigurationAuthoritySnapshot,
    StoredClassWorldConfiguration,
)
from explore.online.control_plane_persistence import SQLiteControlPlaneStore
from explore.online.models import AssuranceLevel, CohortRole
from explore.online.persistence import PersistenceConflictError

CONFIGURATION_SCHEMA_VERSION = 1

_CONFIGURATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS configuration_schema_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1)
) STRICT;

INSERT OR IGNORE INTO configuration_schema_metadata (singleton, schema_version)
VALUES (1, 1);

CREATE TABLE IF NOT EXISTS class_world_configurations (
    locator TEXT PRIMARY KEY CHECK (length(locator) = 36),
    class_world_id TEXT NOT NULL,
    class_world_version TEXT NOT NULL,
    configuration_sha256 TEXT NOT NULL CHECK (
        length(configuration_sha256) = 64
        AND configuration_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    cohort_id TEXT NOT NULL,
    student_api_version TEXT NOT NULL,
    canonical_size INTEGER NOT NULL CHECK (canonical_size > 0),
    canonical_bytes BLOB NOT NULL CHECK (
        typeof(canonical_bytes) = 'blob' AND length(canonical_bytes) = canonical_size
    ),
    created_by_actor_id TEXT NOT NULL,
    authority_role TEXT NOT NULL CHECK (authority_role = 'course-admin'),
    authority_assurance TEXT NOT NULL CHECK (authority_assurance = 'aal2'),
    membership_granted_by_actor_id TEXT NOT NULL,
    membership_granted_at TEXT NOT NULL CHECK (substr(membership_granted_at, -1) = 'Z'),
    membership_revision INTEGER NOT NULL CHECK (membership_revision >= 1),
    membership_active INTEGER NOT NULL CHECK (membership_active = 1),
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    correlation_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    UNIQUE (class_world_id, class_world_version),
    UNIQUE (
        class_world_id, class_world_version, configuration_sha256,
        cohort_id, student_api_version
    ),
    FOREIGN KEY (
        class_world_id, class_world_version, configuration_sha256,
        cohort_id, student_api_version
    ) REFERENCES class_world_configuration_bindings (
        class_world_id, class_world_version, configuration_sha256,
        cohort_id, student_api_version
    ) ON DELETE RESTRICT,
    FOREIGN KEY (cohort_id) REFERENCES cohorts (cohort_id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by_actor_id) REFERENCES actors (actor_id) ON DELETE RESTRICT,
    FOREIGN KEY (membership_granted_by_actor_id)
        REFERENCES actors (actor_id) ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER IF NOT EXISTS class_world_configurations_no_update
BEFORE UPDATE ON class_world_configurations
BEGIN
    SELECT RAISE(ABORT, 'class-world configurations are immutable');
END;

CREATE TRIGGER IF NOT EXISTS class_world_configurations_no_delete
BEFORE DELETE ON class_world_configurations
BEGIN
    SELECT RAISE(ABORT, 'class-world configurations are immutable');
END;
"""


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class StoredPackageArtifact:
    """Exact immutable package artifact used to reconstruct a configuration plan."""

    submission_id: str
    package_id: str
    package_version: str
    raw_zip_sha256: str
    cohort_id: str
    archive_bytes: bytes


class ConfigurationPersistenceConflictError(PersistenceConflictError):
    """An immutable Class-World configuration persistence invariant conflicts."""


class SQLiteClassWorldConfigurationStore(SQLiteControlPlaneStore):
    """Full Phase E store extended with authoritative configuration bytes."""

    @classmethod
    def open(cls, path: str | Path) -> SQLiteClassWorldConfigurationStore:
        return super().open(path)

    def initialize_schema(self) -> None:
        super().initialize_schema()
        self._connection.executescript(_CONFIGURATION_SCHEMA)
        row = self._connection.execute(
            "SELECT schema_version FROM configuration_schema_metadata WHERE singleton = 1"
        ).fetchone()
        if row != (CONFIGURATION_SCHEMA_VERSION,):
            raise RuntimeError("unsupported Phase E configuration schema version")

    def append_class_world_configuration(
        self,
        record: StoredClassWorldConfiguration,
    ) -> None:
        """Append one canonical immutable configuration record."""
        if not isinstance(record, StoredClassWorldConfiguration):
            raise TypeError("record must be a StoredClassWorldConfiguration")
        if hashlib.sha256(record.canonical_bytes).hexdigest() != record.configuration_sha256:
            raise ConfigurationPersistenceConflictError(
                "canonical configuration bytes do not match the server-derived digest"
            )
        authority = record.authority
        try:
            self._connection.execute(
                """
                INSERT INTO class_world_configurations (
                    locator, class_world_id, class_world_version,
                    configuration_sha256, cohort_id, student_api_version,
                    canonical_size, canonical_bytes, created_by_actor_id,
                    authority_role, authority_assurance,
                    membership_granted_by_actor_id, membership_granted_at,
                    membership_revision, membership_active, created_at,
                    correlation_id, idempotency_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.locator,
                    record.class_world_id,
                    record.class_world_version,
                    record.configuration_sha256,
                    record.cohort_id,
                    record.student_api_version,
                    len(record.canonical_bytes),
                    record.canonical_bytes,
                    authority.actor_id,
                    authority.role.value,
                    authority.assurance.value,
                    authority.granted_by_actor_id,
                    _serialize_datetime(authority.granted_at),
                    authority.revision,
                    int(authority.active),
                    _serialize_datetime(record.created_at),
                    record.correlation_id,
                    record.idempotency_key,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ConfigurationPersistenceConflictError(
                "configuration conflicts with immutable identity or locator"
            ) from error

    def load_configuration_record(
        self,
        locator: str,
    ) -> StoredClassWorldConfiguration | None:
        """Load only one opaque exact locator; no alternate resolution is provided."""
        row = self._connection.execute(
            """
            SELECT locator, class_world_id, class_world_version,
                configuration_sha256, cohort_id, student_api_version,
                canonical_bytes, created_by_actor_id, authority_role,
                authority_assurance, membership_granted_by_actor_id,
                membership_granted_at, membership_revision, membership_active,
                created_at, correlation_id, idempotency_key
            FROM class_world_configurations WHERE locator = ?
            """,
            (locator,),
        ).fetchone()
        if row is None:
            return None
        return StoredClassWorldConfiguration(
            locator=row[0],
            class_world_id=row[1],
            class_world_version=row[2],
            configuration_sha256=row[3],
            cohort_id=row[4],
            student_api_version=row[5],
            canonical_bytes=bytes(row[6]),
            authority=ConfigurationAuthoritySnapshot(
                cohort_id=row[4],
                actor_id=row[7],
                role=CohortRole(row[8]),
                assurance=AssuranceLevel(row[9]),
                granted_by_actor_id=row[10],
                granted_at=_parse_datetime(row[11]),
                revision=row[12],
                active=bool(row[13]),
            ),
            created_at=_parse_datetime(row[14]),
            correlation_id=row[15],
            idempotency_key=row[16],
        )

    def _load_configuration_record_by_identity(
        self,
        class_world_id: str,
        class_world_version: str,
    ) -> StoredClassWorldConfiguration | None:
        """Resolve an exact identity for internal create-conflict handling only."""
        row = self._connection.execute(
            """
            SELECT locator FROM class_world_configurations
            WHERE class_world_id = ? AND class_world_version = ?
            """,
            (class_world_id, class_world_version),
        ).fetchone()
        return None if row is None else self.load_configuration_record(row[0])

    def load_exact_package_artifact(
        self,
        package_id: str,
        package_version: str,
    ) -> StoredPackageArtifact | None:
        """Load one exact immutable submission artifact for trusted reconstruction."""
        row = self._connection.execute(
            """
            SELECT submission_id, package_id, package_version, raw_zip_sha256,
                cohort_id, archive_bytes
            FROM package_submissions
            WHERE package_id = ? AND package_version = ?
            """,
            (package_id, package_version),
        ).fetchone()
        if row is None:
            return None
        return StoredPackageArtifact(row[0], row[1], row[2], row[3], row[4], bytes(row[5]))


__all__ = [
    "CONFIGURATION_SCHEMA_VERSION",
    "ConfigurationPersistenceConflictError",
    "SQLiteClassWorldConfigurationStore",
    "StoredPackageArtifact",
]
