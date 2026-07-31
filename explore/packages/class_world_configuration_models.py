"""Immutable in-memory models for class-world configuration v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from explore.packages.package_set_models import PackageSetPlan

SUPPORTED_CLASS_WORLD_CONFIGURATION_SCHEMA_VERSION = "0.1"
CLASS_WORLD_DISPLAY_NAME_MAX_LENGTH = 100
COHORT_DISPLAY_NAME_MAX_LENGTH = 100


class ClassWorldConfigurationIssueCode(StrEnum):
    """Stable machine-readable class-world configuration issue codes."""

    CONFIGURATION_SPEC_REQUIRED = "CONFIGURATION_SPEC_REQUIRED"
    PACKAGE_SET_PLAN_REQUIRED = "PACKAGE_SET_PLAN_REQUIRED"
    SCHEMA_VERSION_UNSUPPORTED = "SCHEMA_VERSION_UNSUPPORTED"
    CLASS_WORLD_ID_INVALID = "CLASS_WORLD_ID_INVALID"
    CLASS_WORLD_DISPLAY_NAME_INVALID = "CLASS_WORLD_DISPLAY_NAME_INVALID"
    CLASS_WORLD_VERSION_INVALID = "CLASS_WORLD_VERSION_INVALID"
    ENGINE_VERSION_INVALID = "ENGINE_VERSION_INVALID"
    STUDENT_API_VERSION_UNSUPPORTED = "STUDENT_API_VERSION_UNSUPPORTED"
    COHORT_INVALID = "COHORT_INVALID"
    COHORT_ID_INVALID = "COHORT_ID_INVALID"
    COHORT_DISPLAY_NAME_INVALID = "COHORT_DISPLAY_NAME_INVALID"
    PACKAGE_SET_REQUIRED = "PACKAGE_SET_REQUIRED"
    PACKAGE_PIN_INVALID_TYPE = "PACKAGE_PIN_INVALID_TYPE"
    PACKAGE_PIN_ID_INVALID = "PACKAGE_PIN_ID_INVALID"
    PACKAGE_PIN_VERSION_INVALID = "PACKAGE_PIN_VERSION_INVALID"
    PACKAGE_PIN_DUPLICATE = "PACKAGE_PIN_DUPLICATE"
    PACKAGE_PIN_VERSION_CONFLICT = "PACKAGE_PIN_VERSION_CONFLICT"
    PACKAGE_COUNT_MISMATCH = "PACKAGE_COUNT_MISMATCH"
    PACKAGE_ORDER_MISMATCH = "PACKAGE_ORDER_MISMATCH"
    PACKAGE_ID_MISMATCH = "PACKAGE_ID_MISMATCH"
    PACKAGE_VERSION_MISMATCH = "PACKAGE_VERSION_MISMATCH"
    PACKAGE_PROVENANCE_MISMATCH = "PACKAGE_PROVENANCE_MISMATCH"
    PACKAGE_SET_STRUCTURE_INVALID = "PACKAGE_SET_STRUCTURE_INVALID"


@dataclass(frozen=True)
class ClassWorldPackagePin:
    """One exact Explorer Package pin in declared class-world order."""

    package_id: str
    package_version: str


@dataclass(frozen=True)
class ClassWorldCohort:
    """Minimal non-personal metadata for one class-world cohort."""

    cohort_id: str
    display_name: str


@dataclass(frozen=True)
class ClassWorldConfigurationSpec:
    """Caller-supplied immutable class-world configuration request."""

    schema_version: str
    class_world_id: str
    display_name: str
    class_world_version: str
    engine_version: str
    student_api_version: str
    cohort: ClassWorldCohort
    packages: tuple[ClassWorldPackagePin, ...]


@dataclass(frozen=True)
class ClassWorldConfiguration:
    """Validated intended composition of one class world.

    ``package_set_plan`` is the canonical source of package and entry
    composition. ``packages`` derives exact ordered pins from that plan so the
    validated model cannot retain a second, independently mutable source of
    package truth.
    """

    schema_version: str
    class_world_id: str
    display_name: str
    class_world_version: str
    engine_version: str
    student_api_version: str
    cohort: ClassWorldCohort
    package_set_plan: PackageSetPlan

    @property
    def identity(self) -> tuple[str, str]:
        """Return the declared v0.1 identity without generating artifact identity."""
        return (self.class_world_id, self.class_world_version)

    @property
    def packages(self) -> tuple[ClassWorldPackagePin, ...]:
        """Return exact package pins in canonical package-set-plan order."""
        return tuple(
            ClassWorldPackagePin(
                package_id=package.package_id,
                package_version=package.package_version,
            )
            for package in self.package_set_plan.packages
        )


@dataclass(frozen=True)
class ClassWorldConfigurationIssue:
    """One deterministic class-world configuration diagnostic."""

    code: ClassWorldConfigurationIssueCode
    message: str
    location: str
    package_id: str | None = None
    package_index: int | None = None
    field: str | None = None


@dataclass(frozen=True)
class ClassWorldConfigurationResult:
    """Atomic result of class-world configuration construction."""

    configuration: ClassWorldConfiguration | None
    issues: tuple[ClassWorldConfigurationIssue, ...]

    @property
    def is_configured(self) -> bool:
        """Whether one complete validated configuration was constructed."""
        return self.configuration is not None and not self.issues
