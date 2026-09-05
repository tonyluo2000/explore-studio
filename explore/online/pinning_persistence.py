"""Append-only SQLite persistence for exact Class-World package pins."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from explore.online.models import AssuranceLevel, CohortRole, PackageVersionIdentity
from explore.online.persistence import PersistenceConflictError
from explore.online.pinning_models import (
    ClassWorldConfigurationBinding,
    ClassWorldPackagePinRecord,
    PinAuthoritySnapshot,
)
from explore.online.registry_models import RegistryCompatibility
from explore.online.registry_persistence import SQLiteRegistryStore

PINNING_SCHEMA_VERSION = 1

_PINNING_SCHEMA = """
CREATE TABLE IF NOT EXISTS pinning_schema_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1)
) STRICT;

INSERT OR IGNORE INTO pinning_schema_metadata (singleton, schema_version) VALUES (1, 1);

CREATE TABLE IF NOT EXISTS class_world_configuration_bindings (
    class_world_id TEXT NOT NULL,
    class_world_version TEXT NOT NULL,
    configuration_sha256 TEXT NOT NULL CHECK (
        length(configuration_sha256) = 64
        AND configuration_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    cohort_id TEXT NOT NULL,
    student_api_version TEXT NOT NULL,
    PRIMARY KEY (class_world_id, class_world_version),
    UNIQUE (
        class_world_id, class_world_version, configuration_sha256,
        cohort_id, student_api_version
    ),
    FOREIGN KEY (cohort_id) REFERENCES cohorts (cohort_id) ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER IF NOT EXISTS class_world_configuration_bindings_no_update
BEFORE UPDATE ON class_world_configuration_bindings
BEGIN
    SELECT RAISE(ABORT, 'class-world configuration bindings are immutable');
END;

CREATE TRIGGER IF NOT EXISTS class_world_configuration_bindings_no_delete
BEFORE DELETE ON class_world_configuration_bindings
BEGIN
    SELECT RAISE(ABORT, 'class-world configuration bindings are immutable');
END;

CREATE TABLE IF NOT EXISTS class_world_package_pins (
    pin_id TEXT PRIMARY KEY CHECK (length(pin_id) = 36),
    class_world_id TEXT NOT NULL,
    class_world_version TEXT NOT NULL,
    configuration_sha256 TEXT NOT NULL CHECK (
        length(configuration_sha256) = 64
        AND configuration_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    package_id TEXT NOT NULL,
    package_version TEXT NOT NULL,
    raw_zip_sha256 TEXT NOT NULL CHECK (
        length(raw_zip_sha256) = 64
        AND raw_zip_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    cohort_id TEXT NOT NULL,
    owner_actor_id TEXT NOT NULL,
    student_api_version TEXT NOT NULL,
    artifact_reference TEXT NOT NULL,
    approval_decision_id TEXT NOT NULL,
    pinned_by_actor_id TEXT NOT NULL,
    pin_authority_role TEXT NOT NULL CHECK (pin_authority_role = 'course-admin'),
    pin_authority_assurance TEXT NOT NULL CHECK (pin_authority_assurance = 'aal2'),
    membership_granted_by_actor_id TEXT NOT NULL,
    membership_granted_at TEXT NOT NULL CHECK (substr(membership_granted_at, -1) = 'Z'),
    membership_revision INTEGER NOT NULL CHECK (membership_revision >= 1),
    membership_active INTEGER NOT NULL CHECK (membership_active = 1),
    pinned_at TEXT NOT NULL CHECK (substr(pinned_at, -1) = 'Z'),
    correlation_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    UNIQUE (class_world_id, class_world_version, package_id),
    FOREIGN KEY (
        class_world_id, class_world_version, configuration_sha256,
        cohort_id, student_api_version
    ) REFERENCES class_world_configuration_bindings (
        class_world_id, class_world_version, configuration_sha256,
        cohort_id, student_api_version
    ) ON DELETE RESTRICT,
    FOREIGN KEY (
        artifact_reference, package_id, package_version, raw_zip_sha256, cohort_id
    ) REFERENCES package_submissions (
        submission_id, package_id, package_version, raw_zip_sha256, cohort_id
    ) ON DELETE RESTRICT,
    FOREIGN KEY (approval_decision_id)
        REFERENCES package_review_decisions (decision_id) ON DELETE RESTRICT,
    FOREIGN KEY (owner_actor_id) REFERENCES actors (actor_id) ON DELETE RESTRICT,
    FOREIGN KEY (pinned_by_actor_id) REFERENCES actors (actor_id) ON DELETE RESTRICT,
    FOREIGN KEY (membership_granted_by_actor_id)
        REFERENCES actors (actor_id) ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER IF NOT EXISTS class_world_package_pins_no_update
BEFORE UPDATE ON class_world_package_pins
BEGIN
    SELECT RAISE(ABORT, 'class-world package pins are append-only');
END;

CREATE TRIGGER IF NOT EXISTS class_world_package_pins_no_delete
BEFORE DELETE ON class_world_package_pins
BEGIN
    SELECT RAISE(ABORT, 'class-world package pins are append-only');
END;
"""


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class PinPersistenceConflictError(PersistenceConflictError):
    """An immutable configuration/package pin binding conflicts."""


class SQLitePinningStore(SQLiteRegistryStore):
    """Registry store extended only with immutable Class-World pin evidence."""

    @classmethod
    def open(cls, path: str | Path) -> SQLitePinningStore:
        return super().open(path)

    def initialize_schema(self) -> None:
        super().initialize_schema()
        self._connection.executescript(_PINNING_SCHEMA)
        row = self._connection.execute(
            "SELECT schema_version FROM pinning_schema_metadata WHERE singleton = 1"
        ).fetchone()
        if row != (PINNING_SCHEMA_VERSION,):
            raise RuntimeError("unsupported Phase E pinning schema version")

    def append_class_world_pin(self, pin: ClassWorldPackagePinRecord) -> None:
        """Append one immutable pin binding without changing a configuration."""
        if not isinstance(pin, ClassWorldPackagePinRecord):
            raise TypeError("pin must be a ClassWorldPackagePinRecord")
        projected = self.project_approved_entry(
            pin.package_version.package_id,
            pin.package_version.package_version,
        )
        if (
            projected is None
            or projected.package_version != pin.package_version
            or projected.cohort_id != pin.cohort_id
            or projected.owner_actor_id != pin.owner_actor_id
            or projected.compatibility != pin.compatibility
            or projected.artifact_reference != pin.artifact_reference
            or projected.approval_decision_id != pin.approval_decision_id
        ):
            raise PinPersistenceConflictError(
                "pin does not match the current approved registry projection"
            )
        authority = pin.authority
        package = pin.package_version
        try:
            self._connection.execute(
                """
                INSERT INTO class_world_package_pins (
                    pin_id, class_world_id, class_world_version,
                    configuration_sha256, package_id, package_version,
                    raw_zip_sha256, cohort_id, owner_actor_id,
                    student_api_version, artifact_reference, approval_decision_id,
                    pinned_by_actor_id, pin_authority_role,
                    pin_authority_assurance, membership_granted_by_actor_id,
                    membership_granted_at, membership_revision, membership_active,
                    pinned_at, correlation_id, idempotency_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pin.pin_id,
                    pin.class_world_id,
                    pin.class_world_version,
                    pin.configuration_sha256,
                    package.package_id,
                    package.package_version,
                    package.raw_zip_sha256,
                    pin.cohort_id,
                    pin.owner_actor_id,
                    pin.compatibility.student_api_version,
                    pin.artifact_reference,
                    pin.approval_decision_id,
                    authority.actor_id,
                    authority.role.value,
                    authority.assurance.value,
                    authority.granted_by_actor_id,
                    _serialize_datetime(authority.granted_at),
                    authority.revision,
                    int(authority.active),
                    _serialize_datetime(pin.pinned_at),
                    pin.correlation_id,
                    pin.idempotency_key,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise PinPersistenceConflictError(
                "pin conflicts with an immutable configuration/package binding"
            ) from error

    def bind_class_world_configuration(
        self,
        binding: ClassWorldConfigurationBinding,
    ) -> ClassWorldConfigurationBinding:
        """Insert or replay one immutable canonical configuration fingerprint."""
        if not isinstance(binding, ClassWorldConfigurationBinding):
            raise TypeError("binding must be a ClassWorldConfigurationBinding")
        existing = self.load_class_world_configuration_binding(
            binding.class_world_id,
            binding.class_world_version,
        )
        if existing is not None:
            if existing != binding:
                raise PinPersistenceConflictError(
                    "configuration identity is already bound to different canonical bytes"
                )
            return existing
        try:
            self._connection.execute(
                """
                INSERT INTO class_world_configuration_bindings (
                    class_world_id, class_world_version, configuration_sha256,
                    cohort_id, student_api_version
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    binding.class_world_id,
                    binding.class_world_version,
                    binding.configuration_sha256,
                    binding.cohort_id,
                    binding.student_api_version,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise PinPersistenceConflictError(
                "configuration identity conflicts with immutable binding"
            ) from error
        return binding

    def load_class_world_configuration_binding(
        self,
        class_world_id: str,
        class_world_version: str,
    ) -> ClassWorldConfigurationBinding | None:
        """Load one immutable canonical configuration fingerprint."""
        row = self._connection.execute(
            """
            SELECT class_world_id, class_world_version, configuration_sha256,
                cohort_id, student_api_version
            FROM class_world_configuration_bindings
            WHERE class_world_id = ? AND class_world_version = ?
            """,
            (class_world_id, class_world_version),
        ).fetchone()
        if row is None:
            return None
        return ClassWorldConfigurationBinding(row[0], row[1], row[2], row[3], row[4])

    def load_class_world_pin(
        self,
        class_world_id: str,
        class_world_version: str,
        package_id: str,
    ) -> ClassWorldPackagePinRecord | None:
        """Load the sole immutable pin for one configuration/package identity."""
        row = self._connection.execute(
            """
            SELECT pin_id, class_world_id, class_world_version,
                configuration_sha256, package_id, package_version,
                raw_zip_sha256, cohort_id, owner_actor_id,
                student_api_version, artifact_reference, approval_decision_id,
                pinned_by_actor_id, pin_authority_role,
                pin_authority_assurance, membership_granted_by_actor_id,
                membership_granted_at, membership_revision, membership_active,
                pinned_at, correlation_id, idempotency_key
            FROM class_world_package_pins
            WHERE class_world_id = ? AND class_world_version = ? AND package_id = ?
            """,
            (class_world_id, class_world_version, package_id),
        ).fetchone()
        if row is None:
            return None
        return ClassWorldPackagePinRecord(
            pin_id=row[0],
            class_world_id=row[1],
            class_world_version=row[2],
            configuration_sha256=row[3],
            package_version=PackageVersionIdentity(row[4], row[5], row[6]),
            cohort_id=row[7],
            owner_actor_id=row[8],
            compatibility=RegistryCompatibility(row[9]),
            artifact_reference=row[10],
            approval_decision_id=row[11],
            authority=PinAuthoritySnapshot(
                cohort_id=row[7],
                actor_id=row[12],
                role=CohortRole(row[13]),
                assurance=AssuranceLevel(row[14]),
                granted_by_actor_id=row[15],
                granted_at=_parse_datetime(row[16]),
                revision=row[17],
                active=bool(row[18]),
            ),
            pinned_at=_parse_datetime(row[19]),
            correlation_id=row[20],
            idempotency_key=row[21],
        )

    def load_class_world_pin_by_id(self, pin_id: str) -> ClassWorldPackagePinRecord | None:
        """Load one immutable pin identity without adding alternate resolution semantics."""
        row = self._connection.execute(
            """
            SELECT class_world_id, class_world_version, package_id
            FROM class_world_package_pins WHERE pin_id = ?
            """,
            (pin_id,),
        ).fetchone()
        if row is None:
            return None
        return self.load_class_world_pin(row[0], row[1], row[2])


__all__ = [
    "PINNING_SCHEMA_VERSION",
    "PinPersistenceConflictError",
    "SQLitePinningStore",
]
