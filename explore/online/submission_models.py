"""Immutable models for bounded Phase E package submission."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from urllib.parse import urlsplit
from uuid import UUID

from explore.online.models import AssuranceLevel, PackageVersionIdentity
from explore.packages.policy import is_valid_identifier, is_valid_semantic_version

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}", re.ASCII)
_CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x1f\x7f]", re.ASCII)


def _require_text(value: str, field: str, *, maximum: int) -> None:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{field} must contain 1 to {maximum} characters")
    if _CONTROL_CHARACTER_PATTERN.search(value) is not None:
        raise ValueError(f"{field} must not contain control characters")


def _require_uuid(value: str, field: str, *, version: int | None = None) -> None:
    _require_text(value, field, maximum=36)
    try:
        parsed = UUID(value)
    except ValueError as error:
        raise ValueError(f"{field} must be a canonical UUID") from error
    if str(parsed) != value or (version is not None and parsed.version != version):
        qualifier = f" version {version}" if version is not None else ""
        raise ValueError(f"{field} must be a canonical lowercase UUID{qualifier}")


def _require_utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field} must use UTC")


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase 64-character SHA-256 digest")


class PublicationAuthority(StrEnum):
    """Authority represented by the authenticated publishing actor."""

    SELF = "self"
    INSTITUTION_COURSE_OPERATOR = "institution-course-operator"


class SubmissionState(StrEnum):
    """The only lifecycle state created by this bounded submission slice."""

    REVIEWABLE = "reviewable"


class SubmissionValidationOutcome(StrEnum):
    """Persisted validation result for an accepted submission."""

    VALID = "valid"


class SubmissionVerificationIssueCode(StrEnum):
    """Stable fail-closed archive verification outcomes."""

    FILENAME_INVALID = "FILENAME_INVALID"
    ARCHIVE_REQUIRED = "ARCHIVE_REQUIRED"
    ARCHIVE_TOO_LARGE = "ARCHIVE_TOO_LARGE"
    ARCHIVE_INVALID = "ARCHIVE_INVALID"
    MEMBER_COUNT_EXCEEDED = "MEMBER_COUNT_EXCEEDED"
    MANIFEST_INVALID = "MANIFEST_INVALID"
    ARCHIVE_STRUCTURE_INVALID = "ARCHIVE_STRUCTURE_INVALID"
    MEMBER_TOO_LARGE = "MEMBER_TOO_LARGE"
    CONTENT_TOO_LARGE = "CONTENT_TOO_LARGE"
    ARCHIVE_NOT_DETERMINISTIC = "ARCHIVE_NOT_DETERMINISTIC"
    PACKAGE_CONTENT_INVALID = "PACKAGE_CONTENT_INVALID"


@dataclass(frozen=True)
class AuthenticatedOIDCIdentity:
    """Claims already verified by the trusted OIDC adapter.

    The submission service resolves this immutable issuer/subject pair to the
    internal actor. Request handlers must never construct it from unverified
    request fields.
    """

    issuer: str
    subject: str
    assurance: AssuranceLevel

    def __post_init__(self) -> None:
        _require_text(self.issuer, "issuer", maximum=512)
        parsed = urlsplit(self.issuer)
        if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("issuer must be an absolute HTTPS URL without query or fragment")
        _require_text(self.subject, "subject", maximum=512)
        if not isinstance(self.assurance, AssuranceLevel):
            raise ValueError("assurance must be an AssuranceLevel")


@dataclass(frozen=True)
class PublicationPolicy:
    """Trusted service configuration for per-version publication acknowledgment."""

    terms_version: str
    license_policy_version: str

    def __post_init__(self) -> None:
        _require_text(self.terms_version, "terms_version", maximum=128)
        _require_text(self.license_policy_version, "license_policy_version", maximum=128)


@dataclass(frozen=True)
class PublicationAcknowledgment:
    """Explicit acknowledgment attached to one submitted immutable version."""

    terms_version: str
    license_policy_version: str
    represented_authority: PublicationAuthority

    def __post_init__(self) -> None:
        _require_text(self.terms_version, "terms_version", maximum=128)
        _require_text(self.license_policy_version, "license_policy_version", maximum=128)
        if not isinstance(self.represented_authority, PublicationAuthority):
            raise ValueError("represented_authority must be a PublicationAuthority")


@dataclass(frozen=True)
class SubmissionVerificationIssue:
    """One deterministic archive or package-content diagnostic."""

    code: SubmissionVerificationIssueCode
    message: str
    location: str


@dataclass(frozen=True)
class SubmittedArchiveMember:
    """Digest provenance for one canonical archive member."""

    relative_path: str
    bytes_read: int
    sha256: str

    def __post_init__(self) -> None:
        _require_text(self.relative_path, "relative_path", maximum=1024)
        if not isinstance(self.bytes_read, int) or isinstance(self.bytes_read, bool):
            raise ValueError("bytes_read must be an integer")
        if self.bytes_read < 0:
            raise ValueError("bytes_read must not be negative")
        _require_sha256(self.sha256, "sha256")


@dataclass(frozen=True)
class VerifiedSubmittedArchive:
    """Trusted identity and provenance derived only from canonical archive bytes."""

    package_id: str
    semantic_version: str
    student_api_version: str
    raw_archive_sha256: str
    archive_bytes: int
    members: tuple[SubmittedArchiveMember, ...]

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.package_id):
            raise ValueError("package_id must be a valid lower-kebab-case identifier")
        if not is_valid_semantic_version(self.semantic_version):
            raise ValueError("semantic_version must be Semantic Versioning 2.0.0")
        _require_text(self.student_api_version, "student_api_version", maximum=64)
        _require_sha256(self.raw_archive_sha256, "raw_archive_sha256")
        if not isinstance(self.archive_bytes, int) or isinstance(self.archive_bytes, bool):
            raise ValueError("archive_bytes must be an integer")
        if self.archive_bytes <= 0:
            raise ValueError("archive_bytes must be positive")
        if not self.members:
            raise ValueError("members must not be empty")

    def provenance_json(self) -> str:
        """Return stable validation provenance suitable for append-only storage."""
        document = {
            "archive_bytes": self.archive_bytes,
            "archive_format": "deterministic-explorer-package-zip-v0.1",
            "members": [
                {
                    "bytes": member.bytes_read,
                    "path": member.relative_path,
                    "sha256": member.sha256,
                }
                for member in self.members
            ],
            "package_id": self.package_id,
            "raw_archive_sha256": self.raw_archive_sha256,
            "semantic_version": self.semantic_version,
            "student_api_version": self.student_api_version,
            "validation_outcome": SubmissionValidationOutcome.VALID.value,
        }
        return json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


@dataclass(frozen=True)
class SubmittedArchiveVerification:
    """Atomic verification result; invalid archives expose no trusted identity."""

    archive: VerifiedSubmittedArchive | None
    issues: tuple[SubmissionVerificationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return self.archive is not None and not self.issues


@dataclass(frozen=True)
class PackageSubmission:
    """Opaque immutable review-lifecycle record for one accepted package version."""

    submission_id: str
    package_version: PackageVersionIdentity
    cohort_id: str
    submitted_by_actor_id: str
    submitted_at: datetime
    artifact_retention_until: datetime
    state: SubmissionState
    validation_outcome: SubmissionValidationOutcome
    validation_provenance_json: str
    acknowledgment: PublicationAcknowledgment

    def __post_init__(self) -> None:
        _require_uuid(self.submission_id, "submission_id", version=4)
        if not isinstance(self.package_version, PackageVersionIdentity):
            raise ValueError("package_version must be a PackageVersionIdentity")
        if not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        _require_uuid(self.submitted_by_actor_id, "submitted_by_actor_id")
        _require_utc(self.submitted_at, "submitted_at")
        _require_utc(self.artifact_retention_until, "artifact_retention_until")
        if self.artifact_retention_until <= self.submitted_at:
            raise ValueError("artifact_retention_until must be after submitted_at")
        if self.state is not SubmissionState.REVIEWABLE:
            raise ValueError("a new submission must be reviewable only")
        if self.validation_outcome is not SubmissionValidationOutcome.VALID:
            raise ValueError("an accepted submission must have a valid outcome")
        try:
            provenance = json.loads(self.validation_provenance_json)
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("validation_provenance_json must be valid JSON") from error
        canonical = json.dumps(
            provenance, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        )
        if not isinstance(provenance, dict) or canonical != self.validation_provenance_json:
            raise ValueError("validation_provenance_json must be a canonical JSON object")
        expected_provenance = {
            "package_id": self.package_version.package_id,
            "semantic_version": self.package_version.package_version,
            "raw_archive_sha256": self.package_version.raw_zip_sha256,
            "validation_outcome": self.validation_outcome.value,
        }
        if any(provenance.get(key) != value for key, value in expected_provenance.items()):
            raise ValueError("validation provenance must match immutable package identity")
        if not isinstance(self.acknowledgment, PublicationAcknowledgment):
            raise ValueError("acknowledgment must be a PublicationAcknowledgment")


@dataclass(frozen=True)
class SubmissionReceipt:
    """Minimal successful result; it confers no approval or release status."""

    submission: PackageSubmission
    replayed: bool


class SubmissionAuthenticationError(PermissionError):
    """The verified external identity has no immutable internal actor binding."""


class SubmissionAccessDeniedError(PermissionError):
    """Submission access is denied without revealing namespace existence."""


class SubmissionConflictError(RuntimeError):
    """An idempotency key or exact package version conflicts with stored bytes."""


class SubmissionPolicyError(ValueError):
    """The publication acknowledgment does not match trusted current policy."""


class SubmissionValidationError(ValueError):
    """The archive failed bounded deterministic verification."""

    def __init__(self, verification: SubmittedArchiveVerification) -> None:
        super().__init__("submitted archive failed deterministic validation")
        self.verification = verification
