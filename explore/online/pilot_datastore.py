"""Isolated, single-process SQLite bootstrap for the synthetic staff pilot."""

from __future__ import annotations

import fcntl
import os
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType

from explore.online.models import AssuranceLevel
from explore.online.pilot_config import PilotDatastoreConfig
from explore.online.transport_persistence import (
    TRANSPORT_SCHEMA_VERSION,
    SQLiteStaffTransportStore,
)

PILOT_DATASTORE_SCHEMA_VERSION = 2
_CLASSIFICATION = "synthetic-non-minor"
_MARKER_SCHEMA = """
CREATE TABLE IF NOT EXISTS staff_pilot_datastore_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    schema_version INTEGER NOT NULL CHECK (schema_version = 2),
    environment_id TEXT NOT NULL,
    data_classification TEXT NOT NULL CHECK (data_classification = 'synthetic-non-minor'),
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z')
) STRICT;

CREATE TRIGGER IF NOT EXISTS staff_pilot_datastore_metadata_no_update
BEFORE UPDATE ON staff_pilot_datastore_metadata
BEGIN
    SELECT RAISE(ABORT, 'staff pilot datastore identity is immutable');
END;

CREATE TRIGGER IF NOT EXISTS staff_pilot_datastore_metadata_no_delete
BEFORE DELETE ON staff_pilot_datastore_metadata
BEGIN
    SELECT RAISE(ABORT, 'staff pilot datastore identity is immutable');
END;

CREATE TABLE IF NOT EXISTS staff_pilot_seed_attestation (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    provenance TEXT NOT NULL,
    seed_version TEXT NOT NULL,
    seed_sha256 TEXT NOT NULL CHECK (
        length(seed_sha256) = 64 AND seed_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    attested_at TEXT NOT NULL CHECK (substr(attested_at, -1) = 'Z')
) STRICT;

CREATE TRIGGER IF NOT EXISTS staff_pilot_seed_attestation_no_update
BEFORE UPDATE ON staff_pilot_seed_attestation
BEGIN
    SELECT RAISE(ABORT, 'staff pilot seed attestation is immutable');
END;

CREATE TRIGGER IF NOT EXISTS staff_pilot_seed_attestation_no_delete
BEFORE DELETE ON staff_pilot_seed_attestation
BEGIN
    SELECT RAISE(ABORT, 'staff pilot seed attestation is immutable');
END;
"""


class PilotDatastoreUnavailableError(RuntimeError):
    """The isolated synthetic datastore cannot be safely opened."""


class PilotWorkerTopologyError(RuntimeError):
    """The runtime was inherited by an unsupported worker process."""


def _serialize(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError("trusted clock must return timezone-aware UTC")
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _secure_open_lock(path: Path) -> int:
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError) as error:
        if "descriptor" in locals():
            os.close(descriptor)
        raise PilotDatastoreUnavailableError(
            "synthetic staff pilot datastore is already in use or cannot be locked"
        ) from error
    return descriptor


def _existing_marker(path: Path) -> tuple[object, ...] | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            table = connection.execute("""
                SELECT 1 FROM sqlite_master
                WHERE type = 'table' AND name = 'staff_pilot_datastore_metadata'
                """).fetchone()
            if table is None:
                raise PilotDatastoreUnavailableError(
                    "existing datastore is not an isolated synthetic staff pilot database"
                )
            marker = connection.execute("""
                SELECT schema_version, environment_id, data_classification
                FROM staff_pilot_datastore_metadata WHERE singleton = 1
                """).fetchone()
            if marker is None:
                raise PilotDatastoreUnavailableError("pilot datastore marker is missing")
            return marker
        finally:
            connection.close()
    except sqlite3.Error as error:
        raise PilotDatastoreUnavailableError("pilot datastore marker cannot be verified") from error


@dataclass
class SyntheticPilotDatastore:
    """Owned reference store and lifetime lock for exactly one pilot process."""

    config: PilotDatastoreConfig
    store: SQLiteStaffTransportStore
    _lock_descriptor: int
    _owner_pid: int
    _closed: bool = False

    def assert_process_owner(self) -> None:
        """Reject a runtime inherited through preloading or preforking."""
        if self._closed or os.getpid() != self._owner_pid:
            raise PilotWorkerTopologyError(
                "staff pilot runtime must run in its original single worker process"
            )

    def _seed_attestation_row(self) -> tuple[object, ...] | None:
        if self._closed:
            return None
        try:
            return self.store._connection.execute("""
                SELECT provenance, seed_version, seed_sha256
                FROM staff_pilot_seed_attestation WHERE singleton = 1
                """).fetchone()
        except sqlite3.Error:
            return None

    def seed_is_attested(self) -> bool:
        expected = self.config.seed_attestation
        return self._seed_attestation_row() == (
            expected.provenance,
            expected.version,
            expected.sha256,
        )

    def attest_seed(
        self,
        *,
        approved_issuers: tuple[str, ...],
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        """Seal one reviewed seed after verifying its minimum staff-only prerequisites."""
        self.assert_process_owner()
        if not approved_issuers or len(set(approved_issuers)) != len(approved_issuers):
            raise ValueError("approved_issuers must identify the configured providers")
        if self._seed_attestation_row() is not None:
            raise PilotDatastoreUnavailableError("pilot seed is already attested")
        expected = self.config.seed_attestation
        now = clock()
        with self.store.transaction():
            transient_rows = self.store._connection.execute("""
                SELECT
                    (SELECT count(*) FROM oidc_authorization_transactions),
                    (SELECT count(*) FROM staff_sessions)
                """).fetchone()
            if transient_rows != (0, 0):
                raise PilotDatastoreUnavailableError(
                    "pilot seed cannot be attested after runtime session activity"
                )
            if any(
                self.store.identity_provider_assurance(issuer) is not AssuranceLevel.AAL2
                for issuer in approved_issuers
            ):
                raise PilotDatastoreUnavailableError(
                    "pilot seed does not approve every configured staff identity provider"
                )
            self.store._connection.execute(
                """
                INSERT INTO staff_pilot_seed_attestation (
                    singleton, provenance, seed_version, seed_sha256, attested_at
                ) VALUES (1, ?, ?, ?, ?)
                """,
                (expected.provenance, expected.version, expected.sha256, _serialize(now)),
            )

    def is_ready(self) -> bool:
        """Check structural identity and seed attestation without exposing detail."""
        if self._closed:
            return False
        try:
            marker = self.store._connection.execute("""
                SELECT schema_version, environment_id, data_classification
                FROM staff_pilot_datastore_metadata WHERE singleton = 1
                """).fetchone()
            transport = self.store._connection.execute(
                "SELECT schema_version FROM transport_schema_metadata WHERE singleton = 1"
            ).fetchone()
            integrity = self.store._connection.execute("PRAGMA quick_check").fetchone()
        except sqlite3.Error:
            return False
        return (
            marker
            == (
                PILOT_DATASTORE_SCHEMA_VERSION,
                self.config.environment_id,
                _CLASSIFICATION,
            )
            and transport == (TRANSPORT_SCHEMA_VERSION,)
            and integrity == ("ok",)
            and self.seed_is_attested()
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        owns_process = os.getpid() == self._owner_pid
        try:
            self.store.close()
        finally:
            try:
                if owns_process:
                    fcntl.flock(self._lock_descriptor, fcntl.LOCK_UN)
            finally:
                os.close(self._lock_descriptor)

    def __enter__(self) -> SyntheticPilotDatastore:
        return self

    def __exit__(
        self,
        _exception_type: type[BaseException] | None,
        _exception: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        self.close()


def bootstrap_synthetic_pilot_datastore(
    config: PilotDatastoreConfig,
    *,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> SyntheticPilotDatastore:
    """Lock, classify, and migrate one new or previously classified pilot database."""
    if not isinstance(config, PilotDatastoreConfig):
        raise TypeError("config must be PilotDatastoreConfig")
    parent = config.path.parent
    if not parent.exists() or not parent.is_dir() or parent.is_symlink():
        raise PilotDatastoreUnavailableError(
            "pilot datastore parent must be an existing non-symlink directory"
        )
    if config.path.is_symlink():
        raise PilotDatastoreUnavailableError("pilot datastore path must not be a symlink")
    lock_path = config.path.with_suffix(f"{config.path.suffix}.pilot.lock")
    lock_descriptor = _secure_open_lock(lock_path)
    try:
        marker = _existing_marker(config.path)
        if marker is not None and marker != (
            PILOT_DATASTORE_SCHEMA_VERSION,
            config.environment_id,
            _CLASSIFICATION,
        ):
            raise PilotDatastoreUnavailableError(
                "pilot datastore identity or classification does not match configuration"
            )
        store = SQLiteStaffTransportStore.open(config.path)
        try:
            os.chmod(config.path, 0o600)
            store.initialize_schema()
            store._connection.executescript(_MARKER_SCHEMA)
            with store.transaction():
                store._connection.execute(
                    """
                    INSERT OR IGNORE INTO staff_pilot_datastore_metadata (
                        singleton, schema_version, environment_id, data_classification, created_at
                    ) VALUES (1, ?, ?, ?, ?)
                    """,
                    (
                        PILOT_DATASTORE_SCHEMA_VERSION,
                        config.environment_id,
                        _CLASSIFICATION,
                        _serialize(clock()),
                    ),
                )
            result = SyntheticPilotDatastore(config, store, lock_descriptor, os.getpid())
            marker = store._connection.execute("""
                SELECT schema_version, environment_id, data_classification
                FROM staff_pilot_datastore_metadata WHERE singleton = 1
                """).fetchone()
            if marker != (
                PILOT_DATASTORE_SCHEMA_VERSION,
                config.environment_id,
                _CLASSIFICATION,
            ):
                raise PilotDatastoreUnavailableError("pilot datastore failed readiness checks")
            attestation = result._seed_attestation_row()
            if attestation is not None and not result.seed_is_attested():
                raise PilotDatastoreUnavailableError(
                    "pilot seed attestation does not match configuration"
                )
            return result
        except Exception:
            store.close()
            raise
    except Exception:
        try:
            fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
        finally:
            os.close(lock_descriptor)
        raise


__all__ = [
    "PILOT_DATASTORE_SCHEMA_VERSION",
    "PilotDatastoreUnavailableError",
    "PilotWorkerTopologyError",
    "SyntheticPilotDatastore",
    "bootstrap_synthetic_pilot_datastore",
]
