"""Immutable diagnostics and results for class-world manifest schema v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.class_world_configuration_models import ClassWorldConfiguration

SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION = "0.1"


class ClassWorldManifestIssueCode(StrEnum):
    """Stable machine-readable class-world manifest issue codes."""

    MANIFEST_TEXT_REQUIRED = "MANIFEST_TEXT_REQUIRED"
    PACKAGE_SET_PLAN_REQUIRED = "PACKAGE_SET_PLAN_REQUIRED"
    MANIFEST_INVALID_JSON = "MANIFEST_INVALID_JSON"
    MANIFEST_DUPLICATE_KEY = "MANIFEST_DUPLICATE_KEY"
    MANIFEST_ROOT_INVALID = "MANIFEST_ROOT_INVALID"
    MANIFEST_FIELD_REQUIRED = "MANIFEST_FIELD_REQUIRED"
    MANIFEST_FIELD_UNKNOWN = "MANIFEST_FIELD_UNKNOWN"
    MANIFEST_FIELD_INVALID_TYPE = "MANIFEST_FIELD_INVALID_TYPE"
    MANIFEST_FIELD_INVALID_VALUE = "MANIFEST_FIELD_INVALID_VALUE"
    MANIFEST_SCHEMA_UNSUPPORTED = "MANIFEST_SCHEMA_UNSUPPORTED"
    MANIFEST_PACKAGE_COUNT_MISMATCH = "MANIFEST_PACKAGE_COUNT_MISMATCH"
    MANIFEST_PACKAGE_ORDER_MISMATCH = "MANIFEST_PACKAGE_ORDER_MISMATCH"
    MANIFEST_PACKAGE_ID_MISMATCH = "MANIFEST_PACKAGE_ID_MISMATCH"
    MANIFEST_PACKAGE_VERSION_MISMATCH = "MANIFEST_PACKAGE_VERSION_MISMATCH"
    CONFIGURATION_INVALID = "CONFIGURATION_INVALID"


@dataclass(frozen=True)
class ClassWorldManifestIssue:
    """One deterministic class-world manifest diagnostic."""

    code: ClassWorldManifestIssueCode
    message: str
    location: str


@dataclass(frozen=True)
class ClassWorldManifestParseResult:
    """Atomic result of parsing and validating one class-world manifest."""

    configuration: ClassWorldConfiguration | None
    issues: tuple[ClassWorldManifestIssue, ...]

    @property
    def is_parsed(self) -> bool:
        """Whether a complete validated configuration was parsed."""
        return self.configuration is not None and not self.issues
