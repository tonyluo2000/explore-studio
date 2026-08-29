"""Models for bounded assembled-output manifest file verification v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_assembled_output_manifest_models import (
    ClassWorldAssembledOutputManifest,
    ClassWorldAssembledOutputManifestDigest,
)

MAX_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_BYTES = 1 * 1024 * 1024
SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_FILE_DIGEST_VERIFICATION_CONTRACT_VERSION = "0.1"


class ClassWorldAssembledOutputManifestFileIssueCode(StrEnum):
    """Stable machine-readable manifest readback issue codes."""

    PATH_REQUIRED = "PATH_REQUIRED"
    PATH_INVALID_TYPE = "PATH_INVALID_TYPE"
    EXPECTED_DIGEST_INVALID = "EXPECTED_DIGEST_INVALID"
    MATERIALIZATION_INVALID = "MATERIALIZATION_INVALID"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_SYMLINK_NOT_ALLOWED = "FILE_SYMLINK_NOT_ALLOWED"
    FILE_NOT_REGULAR = "FILE_NOT_REGULAR"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    FILE_READ_FAILED = "FILE_READ_FAILED"
    FILE_BOM_NOT_ALLOWED = "FILE_BOM_NOT_ALLOWED"
    FILE_INVALID_UTF8 = "FILE_INVALID_UTF8"
    JSON_INVALID = "JSON_INVALID"
    JSON_DUPLICATE_KEY = "JSON_DUPLICATE_KEY"
    FIELD_REQUIRED = "FIELD_REQUIRED"
    FIELD_UNKNOWN = "FIELD_UNKNOWN"
    FIELD_INVALID_TYPE = "FIELD_INVALID_TYPE"
    FIELD_INVALID_VALUE = "FIELD_INVALID_VALUE"
    MANIFEST_MISMATCH = "MANIFEST_MISMATCH"


@dataclass(frozen=True)
class ClassWorldAssembledOutputManifestFileIssue:
    """One deterministic readback or verification diagnostic."""

    code: ClassWorldAssembledOutputManifestFileIssueCode
    message: str
    location: str


@dataclass(frozen=True)
class ClassWorldAssembledOutputManifestFileDigestVerificationResult:
    """One bounded manifest read with canonical digest comparison state."""

    manifest: ClassWorldAssembledOutputManifest | None
    expected_digest: ClassWorldAssembledOutputManifestDigest | None
    actual_digest: ClassWorldAssembledOutputManifestDigest | None
    matches: bool | None
    bytes_read: int
    issues: tuple[ClassWorldAssembledOutputManifestFileIssue, ...]

    @property
    def is_verified(self) -> bool:
        """Whether one complete matching canonical manifest was read."""
        return (
            self.manifest is not None
            and self.expected_digest is not None
            and self.actual_digest is not None
            and self.matches is True
            and self.bytes_read > 0
            and not self.issues
        )
