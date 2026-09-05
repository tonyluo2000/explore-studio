"""Authoritative approved-only projection over immutable Phase E records."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from explore.online.models import PackageVersionIdentity
from explore.online.registry_models import (
    ApprovedRegistryEntry,
    RegistryCompatibility,
    RegistryScope,
)
from explore.online.review_persistence import SQLiteReviewStore


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class SQLiteRegistryStore(SQLiteReviewStore):
    """Review store with a derived, non-materialized approved registry view."""

    @classmethod
    def open(cls, path: str | Path) -> SQLiteRegistryStore:
        return super().open(path)

    def project_approved_entry(
        self,
        package_id: str,
        semantic_version: str,
    ) -> ApprovedRegistryEntry | None:
        """Project one exact version only when its latest decision is approval."""
        row = self._connection.execute(
            """
            SELECT s.package_id, s.package_version, s.raw_zip_sha256,
                n.owner_actor_id, s.cohort_id, s.submission_id,
                s.validation_provenance_json, d.decision_id, d.decided_at
            FROM package_submissions AS s
            JOIN package_namespaces AS n
                ON n.package_id = s.package_id AND n.cohort_id = s.cohort_id
            JOIN package_review_decisions AS d
                ON d.submission_id = s.submission_id
            WHERE s.package_id = ? AND s.package_version = ?
                AND d.sequence = (
                    SELECT MAX(latest.sequence)
                    FROM package_review_decisions AS latest
                    WHERE latest.submission_id = s.submission_id
                )
                AND d.action = 'approve'
                AND d.from_state = 'reviewable'
                AND d.to_state = 'approved'
            """,
            (package_id, semantic_version),
        ).fetchone()
        if row is None:
            return None
        provenance = json.loads(row[6])
        student_api_version = provenance.get("student_api_version")
        if not isinstance(student_api_version, str):
            raise RuntimeError("immutable submission provenance lacks compatibility")
        return ApprovedRegistryEntry(
            package_version=PackageVersionIdentity(row[0], row[1], row[2]),
            owner_actor_id=row[3],
            cohort_id=row[4],
            scope=RegistryScope.COHORT,
            compatibility=RegistryCompatibility(student_api_version),
            artifact_reference=row[5],
            approval_decision_id=row[7],
            approved_at=_parse_datetime(row[8]),
        )


__all__ = ["SQLiteRegistryStore"]
