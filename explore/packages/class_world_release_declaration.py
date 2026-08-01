"""Pure construction of class-world release identity and declared provenance."""

from __future__ import annotations

from explore.packages.class_world_configuration import build_class_world_configuration
from explore.packages.class_world_configuration_models import (
    ClassWorldConfiguration,
    ClassWorldConfigurationIssue,
    ClassWorldConfigurationSpec,
)
from explore.packages.class_world_manifest_models import (
    SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION,
)
from explore.packages.class_world_manifest_transport_models import (
    SUPPORTED_CLASS_WORLD_MANIFEST_TRANSPORT_CONTRACT_VERSION,
)
from explore.packages.class_world_release_declaration_models import (
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION,
    ClassWorldReleaseDeclaration,
    ClassWorldReleaseDeclarationIssue,
    ClassWorldReleaseDeclarationIssueCode,
    ClassWorldReleaseDeclarationResult,
    ClassWorldReleaseIdentity,
    ClassWorldReleaseProvenance,
)
from explore.packages.policy import is_valid_identifier, is_valid_semantic_version


def _issue(
    code: ClassWorldReleaseDeclarationIssueCode,
    message: str,
    location: str,
) -> ClassWorldReleaseDeclarationIssue:
    return ClassWorldReleaseDeclarationIssue(code=code, message=message, location=location)


def _configuration_location(location: str) -> str:
    exact_locations = {
        "spec.schema_version": "configuration.schema_version",
        "spec.class_world_id": "configuration.class_world.id",
        "spec.display_name": "configuration.class_world.display_name",
        "spec.class_world_version": "configuration.class_world.version",
        "spec.engine_version": "configuration.engine_version",
        "spec.student_api_version": "configuration.student_api_version",
        "spec.cohort": "configuration.cohort",
        "spec.cohort.cohort_id": "configuration.cohort.id",
        "spec.cohort.display_name": "configuration.cohort.display_name",
        "spec.packages": "configuration.package_set_plan.packages",
    }
    if location in exact_locations:
        return exact_locations[location]
    if location.startswith("spec.packages["):
        return (
            location.removeprefix("spec.")
            .replace("packages", "configuration.package_set_plan.packages", 1)
            .replace(".package_id", ".id")
            .replace(".package_version", ".version")
        )
    if location.startswith("package_set_plan"):
        return f"configuration.{location}"
    return "configuration"


def _configuration_issue(
    issue: ClassWorldConfigurationIssue,
) -> ClassWorldReleaseDeclarationIssue:
    return _issue(
        ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID,
        f"Configuration validation failed: {issue.code}. {issue.message}",
        _configuration_location(issue.location),
    )


def _validate_configuration(
    configuration: ClassWorldConfiguration,
) -> tuple[ClassWorldReleaseDeclarationIssue, ...]:
    try:
        specification = ClassWorldConfigurationSpec(
            schema_version=configuration.schema_version,
            class_world_id=configuration.class_world_id,
            display_name=configuration.display_name,
            class_world_version=configuration.class_world_version,
            engine_version=configuration.engine_version,
            student_api_version=configuration.student_api_version,
            cohort=configuration.cohort,
            packages=configuration.packages,
        )
        validation = build_class_world_configuration(
            specification,
            configuration.package_set_plan,
        )
    except (AttributeError, TypeError):
        return (
            _issue(
                ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID,
                "configuration must retain valid immutable class-world structure.",
                "configuration",
            ),
        )

    if validation.issues:
        return tuple(_configuration_issue(issue) for issue in validation.issues)
    if validation.configuration != configuration:
        return (
            _issue(
                ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID,
                "configuration must agree exactly with its validated package-set plan.",
                "configuration",
            ),
        )
    return ()


def _release_id_issues(release_id: object) -> tuple[ClassWorldReleaseDeclarationIssue, ...]:
    if release_id is None or (isinstance(release_id, str) and not release_id.strip()):
        return (
            _issue(
                ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_REQUIRED,
                "release_id must contain non-whitespace text.",
                "release_id",
            ),
        )
    if not isinstance(release_id, str) or not is_valid_identifier(release_id):
        return (
            _issue(
                ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID,
                "release_id must be a valid lower-kebab-case identifier.",
                "release_id",
            ),
        )
    return ()


def _release_version_issues(
    release_version: object,
) -> tuple[ClassWorldReleaseDeclarationIssue, ...]:
    if release_version is None or (
        isinstance(release_version, str) and not release_version.strip()
    ):
        return (
            _issue(
                ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_REQUIRED,
                "release_version must contain non-whitespace text.",
                "release_version",
            ),
        )
    if not isinstance(release_version, str) or not is_valid_semantic_version(release_version):
        return (
            _issue(
                ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID,
                "release_version must be an exact Semantic Version.",
                "release_version",
            ),
        )
    return ()


def build_class_world_release_declaration(
    configuration: ClassWorldConfiguration | None,
    *,
    release_id: str,
    release_version: str,
) -> ClassWorldReleaseDeclarationResult:
    """Build immutable release identity and declared provenance from a configuration.

    The operation is pure and all-or-nothing. It derives every class-world and
    provenance value from the supplied configuration, preserves exact package
    order, and performs no serialization, file transport, hashing, assembly,
    publication, or deployment.

    Args:
        configuration: One existing immutable class-world configuration.
        release_id: Explicit lower-kebab-case release identifier.
        release_version: Explicit exact Semantic Version.

    Returns:
        A complete immutable declaration or deterministic structured issues.
    """
    if configuration is None:
        configuration_issues = (
            _issue(
                ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_REQUIRED,
                "configuration is required.",
                "configuration",
            ),
        )
    elif not isinstance(configuration, ClassWorldConfiguration):
        configuration_issues = (
            _issue(
                ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID_TYPE,
                "configuration must be a ClassWorldConfiguration.",
                "configuration",
            ),
        )
    else:
        configuration_issues = _validate_configuration(configuration)

    issues = (
        *configuration_issues,
        *_release_id_issues(release_id),
        *_release_version_issues(release_version),
    )
    if issues:
        return ClassWorldReleaseDeclarationResult(declaration=None, issues=issues)

    assert configuration is not None
    assert isinstance(release_id, str)
    assert isinstance(release_version, str)
    declaration = ClassWorldReleaseDeclaration(
        declaration_version=SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION,
        identity=ClassWorldReleaseIdentity(
            release_id=release_id,
            release_version=release_version,
            class_world_id=configuration.class_world_id,
            class_world_version=configuration.class_world_version,
        ),
        provenance=ClassWorldReleaseProvenance(
            engine_version=configuration.engine_version,
            student_api_version=configuration.student_api_version,
            class_world_manifest_schema_version=(SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION),
            manifest_transport_contract_version=(
                SUPPORTED_CLASS_WORLD_MANIFEST_TRANSPORT_CONTRACT_VERSION
            ),
            cohort_id=configuration.cohort.cohort_id,
            package_pins=configuration.packages,
        ),
        configuration=configuration,
    )
    return ClassWorldReleaseDeclarationResult(declaration=declaration, issues=())
