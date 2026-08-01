"""Strict JSON parsing and canonical serialization for class-world manifests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from explore.packages.class_world_configuration import build_class_world_configuration
from explore.packages.class_world_configuration_models import (
    ClassWorldCohort,
    ClassWorldConfiguration,
    ClassWorldConfigurationIssue,
    ClassWorldConfigurationIssueCode,
    ClassWorldConfigurationSpec,
    ClassWorldPackagePin,
)
from explore.packages.class_world_manifest_models import (
    SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION,
    ClassWorldManifestIssue,
    ClassWorldManifestIssueCode,
    ClassWorldManifestParseResult,
)
from explore.packages.package_set_models import PackageSetPlan

_ROOT_FIELDS = (
    "schema_version",
    "class_world",
    "engine_version",
    "student_api_version",
    "cohort",
    "packages",
)
_CLASS_WORLD_FIELDS = ("id", "display_name", "version")
_COHORT_FIELDS = ("id", "display_name")
_PACKAGE_FIELDS = ("id", "version")


@dataclass(frozen=True)
class _JSONObject:
    pairs: tuple[tuple[str, object], ...]


class _NonFiniteNumberError(ValueError):
    pass


def _object_pairs(pairs: list[tuple[str, object]]) -> _JSONObject:
    return _JSONObject(tuple(pairs))


def _reject_non_finite_number(value: str) -> object:
    raise _NonFiniteNumberError(value)


def _issue(
    code: ClassWorldManifestIssueCode,
    message: str,
    location: str,
) -> ClassWorldManifestIssue:
    return ClassWorldManifestIssue(code=code, message=message, location=location)


def _duplicate_issues(value: object, location: str = "") -> list[ClassWorldManifestIssue]:
    issues: list[ClassWorldManifestIssue] = []
    if isinstance(value, _JSONObject):
        seen: set[str] = set()
        for key, child in value.pairs:
            child_location = f"{location}.{key}" if location else key
            if key in seen:
                issues.append(
                    _issue(
                        ClassWorldManifestIssueCode.MANIFEST_DUPLICATE_KEY,
                        f'Duplicate JSON key "{key}" is not permitted.',
                        child_location,
                    )
                )
            else:
                seen.add(key)
            issues.extend(_duplicate_issues(child, child_location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_duplicate_issues(child, f"{location}[{index}]"))
    return issues


def _to_json_value(value: object) -> object:
    if isinstance(value, _JSONObject):
        return {key: _to_json_value(child) for key, child in value.pairs}
    if isinstance(value, list):
        return [_to_json_value(child) for child in value]
    return value


def _required_issue(location: str) -> ClassWorldManifestIssue:
    return _issue(
        ClassWorldManifestIssueCode.MANIFEST_FIELD_REQUIRED,
        f"{location} is required.",
        location,
    )


def _type_issue(location: str, expected: str) -> ClassWorldManifestIssue:
    return _issue(
        ClassWorldManifestIssueCode.MANIFEST_FIELD_INVALID_TYPE,
        f"{location} must be a JSON {expected}.",
        location,
    )


def _is_utf8_compatible(value: str) -> bool:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _invalid_unicode_issue(location: str) -> ClassWorldManifestIssue:
    return _issue(
        ClassWorldManifestIssueCode.MANIFEST_FIELD_INVALID_VALUE,
        f"{location} must contain UTF-8-compatible Unicode text.",
        location,
    )


def _unknown_issues(
    value: dict[str, object],
    allowed: tuple[str, ...],
    location: str = "",
) -> list[ClassWorldManifestIssue]:
    allowed_names = frozenset(allowed)
    return [
        _issue(
            ClassWorldManifestIssueCode.MANIFEST_FIELD_UNKNOWN,
            f"{field_location} is not a recognized manifest field.",
            field_location,
        )
        for key in sorted(value.keys() - allowed_names)
        for field_location in (f"{location}.{key}" if location else key,)
    ]


def _validate_string_fields(
    value: dict[str, object],
    fields: tuple[str, ...],
    location: str,
) -> list[ClassWorldManifestIssue]:
    issues: list[ClassWorldManifestIssue] = []
    for field in fields:
        field_location = f"{location}.{field}"
        if field not in value:
            issues.append(_required_issue(field_location))
        elif not isinstance(value[field], str):
            issues.append(_type_issue(field_location, "string"))
        elif not _is_utf8_compatible(value[field]):
            issues.append(_invalid_unicode_issue(field_location))
    issues.extend(_unknown_issues(value, fields, location))
    return issues


def _validate_structure(root: dict[str, object]) -> list[ClassWorldManifestIssue]:
    issues: list[ClassWorldManifestIssue] = []
    expected_types: dict[str, tuple[type, str]] = {
        "schema_version": (str, "string"),
        "class_world": (dict, "object"),
        "engine_version": (str, "string"),
        "student_api_version": (str, "string"),
        "cohort": (dict, "object"),
        "packages": (list, "array"),
    }
    for field in _ROOT_FIELDS:
        if field not in root:
            issues.append(_required_issue(field))
            continue
        expected_type, description = expected_types[field]
        if not isinstance(root[field], expected_type):
            issues.append(_type_issue(field, description))
        elif isinstance(root[field], str) and not _is_utf8_compatible(root[field]):
            issues.append(_invalid_unicode_issue(field))
        elif (
            field == "schema_version"
            and root[field] != SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION
        ):
            issues.append(
                _issue(
                    ClassWorldManifestIssueCode.MANIFEST_SCHEMA_UNSUPPORTED,
                    (
                        "schema_version must be exactly "
                        f'"{SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION}".'
                    ),
                    "schema_version",
                )
            )
    issues.extend(_unknown_issues(root, _ROOT_FIELDS))

    class_world = root.get("class_world")
    if isinstance(class_world, dict):
        issues.extend(_validate_string_fields(class_world, _CLASS_WORLD_FIELDS, "class_world"))

    cohort = root.get("cohort")
    if isinstance(cohort, dict):
        issues.extend(_validate_string_fields(cohort, _COHORT_FIELDS, "cohort"))

    packages = root.get("packages")
    if isinstance(packages, list):
        for package_index, package in enumerate(packages):
            location = f"packages[{package_index}]"
            if not isinstance(package, dict):
                issues.append(_type_issue(location, "object"))
                continue
            issues.extend(_validate_string_fields(package, _PACKAGE_FIELDS, location))
    return issues


def _manifest_location(configuration_location: str) -> str:
    exact_locations = {
        "spec.schema_version": "schema_version",
        "spec.class_world_id": "class_world.id",
        "spec.display_name": "class_world.display_name",
        "spec.class_world_version": "class_world.version",
        "spec.engine_version": "engine_version",
        "spec.student_api_version": "student_api_version",
        "spec.cohort": "cohort",
        "spec.cohort.cohort_id": "cohort.id",
        "spec.cohort.display_name": "cohort.display_name",
        "spec.packages": "packages",
    }
    if configuration_location in exact_locations:
        return exact_locations[configuration_location]
    if configuration_location.startswith("spec.packages["):
        return (
            configuration_location.removeprefix("spec.")
            .replace(".package_id", ".id")
            .replace(".package_version", ".version")
        )
    return configuration_location


def _configuration_issue(issue: ClassWorldConfigurationIssue) -> ClassWorldManifestIssue:
    code_map = {
        ClassWorldConfigurationIssueCode.PACKAGE_COUNT_MISMATCH: (
            ClassWorldManifestIssueCode.MANIFEST_PACKAGE_COUNT_MISMATCH
        ),
        ClassWorldConfigurationIssueCode.PACKAGE_ORDER_MISMATCH: (
            ClassWorldManifestIssueCode.MANIFEST_PACKAGE_ORDER_MISMATCH
        ),
        ClassWorldConfigurationIssueCode.PACKAGE_ID_MISMATCH: (
            ClassWorldManifestIssueCode.MANIFEST_PACKAGE_ID_MISMATCH
        ),
        ClassWorldConfigurationIssueCode.PACKAGE_VERSION_MISMATCH: (
            ClassWorldManifestIssueCode.MANIFEST_PACKAGE_VERSION_MISMATCH
        ),
    }
    code = code_map.get(issue.code, ClassWorldManifestIssueCode.CONFIGURATION_INVALID)
    return _issue(
        code,
        f"{issue.code}: {issue.message}",
        _manifest_location(issue.location),
    )


def _spec_from_root(root: dict[str, object]) -> ClassWorldConfigurationSpec:
    class_world = root["class_world"]
    cohort = root["cohort"]
    packages = root["packages"]
    assert isinstance(class_world, dict)
    assert isinstance(cohort, dict)
    assert isinstance(packages, list)
    return ClassWorldConfigurationSpec(
        schema_version=root["schema_version"],  # type: ignore[arg-type]
        class_world_id=class_world["id"],  # type: ignore[arg-type]
        display_name=class_world["display_name"],  # type: ignore[arg-type]
        class_world_version=class_world["version"],  # type: ignore[arg-type]
        engine_version=root["engine_version"],  # type: ignore[arg-type]
        student_api_version=root["student_api_version"],  # type: ignore[arg-type]
        cohort=ClassWorldCohort(
            cohort_id=cohort["id"],  # type: ignore[arg-type]
            display_name=cohort["display_name"],  # type: ignore[arg-type]
        ),
        packages=tuple(
            ClassWorldPackagePin(
                package_id=package["id"],
                package_version=package["version"],
            )
            for package in packages
        ),
    )


def parse_class_world_manifest(
    manifest_text: str,
    package_set_plan: PackageSetPlan,
) -> ClassWorldManifestParseResult:
    """Parse manifest text against one existing validated package-set plan.

    The operation performs strict, duplicate-aware JSON parsing and returns no
    partial configuration. It performs no file, package-pipeline, or runtime
    activity.
    """
    input_issues: list[ClassWorldManifestIssue] = []
    if not isinstance(manifest_text, str) or not manifest_text.strip():
        input_issues.append(
            _issue(
                ClassWorldManifestIssueCode.MANIFEST_TEXT_REQUIRED,
                "manifest_text must be a non-empty string.",
                "manifest_text",
            )
        )
    if not isinstance(package_set_plan, PackageSetPlan):
        input_issues.append(
            _issue(
                ClassWorldManifestIssueCode.PACKAGE_SET_PLAN_REQUIRED,
                "package_set_plan must be a PackageSetPlan.",
                "package_set_plan",
            )
        )
    if input_issues:
        return ClassWorldManifestParseResult(configuration=None, issues=tuple(input_issues))

    try:
        decoded = json.loads(
            manifest_text,
            object_pairs_hook=_object_pairs,
            parse_constant=_reject_non_finite_number,
        )
    except json.JSONDecodeError as error:
        return ClassWorldManifestParseResult(
            configuration=None,
            issues=(
                _issue(
                    ClassWorldManifestIssueCode.MANIFEST_INVALID_JSON,
                    f"Invalid JSON at line {error.lineno}, column {error.colno}.",
                    "manifest_text",
                ),
            ),
        )
    except _NonFiniteNumberError:
        return ClassWorldManifestParseResult(
            configuration=None,
            issues=(
                _issue(
                    ClassWorldManifestIssueCode.MANIFEST_INVALID_JSON,
                    "Invalid JSON: non-finite numeric constants are not permitted.",
                    "manifest_text",
                ),
            ),
        )

    duplicate_issues = _duplicate_issues(decoded)
    if duplicate_issues:
        return ClassWorldManifestParseResult(
            configuration=None,
            issues=tuple(duplicate_issues),
        )
    if not isinstance(decoded, _JSONObject):
        return ClassWorldManifestParseResult(
            configuration=None,
            issues=(
                _issue(
                    ClassWorldManifestIssueCode.MANIFEST_ROOT_INVALID,
                    "The manifest root must be a JSON object.",
                    "$",
                ),
            ),
        )

    root = _to_json_value(decoded)
    assert isinstance(root, dict)
    structure_issues = _validate_structure(root)
    if structure_issues:
        return ClassWorldManifestParseResult(
            configuration=None,
            issues=tuple(structure_issues),
        )

    configuration_result = build_class_world_configuration(
        _spec_from_root(root),
        package_set_plan,
    )
    if configuration_result.issues:
        return ClassWorldManifestParseResult(
            configuration=None,
            issues=tuple(_configuration_issue(issue) for issue in configuration_result.issues),
        )
    return ClassWorldManifestParseResult(
        configuration=configuration_result.configuration,
        issues=(),
    )


def serialize_class_world_manifest(configuration: ClassWorldConfiguration) -> str:
    """Return canonical JSON text for one valid immutable configuration.

    Raises:
        TypeError: If *configuration* is not a ``ClassWorldConfiguration``.
        ValueError: If a manually constructed configuration is inconsistent.
    """
    if not isinstance(configuration, ClassWorldConfiguration):
        raise TypeError("configuration must be a ClassWorldConfiguration")
    try:
        pins = configuration.packages
    except (AttributeError, TypeError):
        raise ValueError("configuration contains an invalid package-set structure") from None

    spec = ClassWorldConfigurationSpec(
        schema_version=configuration.schema_version,
        class_world_id=configuration.class_world_id,
        display_name=configuration.display_name,
        class_world_version=configuration.class_world_version,
        engine_version=configuration.engine_version,
        student_api_version=configuration.student_api_version,
        cohort=configuration.cohort,
        packages=pins,
    )
    validation = build_class_world_configuration(spec, configuration.package_set_plan)
    if validation.issues:
        first = validation.issues[0]
        raise ValueError(f"configuration is invalid: {first.code} at {first.location}")
    if validation.configuration != configuration:
        raise ValueError("configuration is inconsistent with its validated package-set plan")

    text_values = (
        ("schema_version", configuration.schema_version),
        ("class_world.id", configuration.class_world_id),
        ("class_world.display_name", configuration.display_name),
        ("class_world.version", configuration.class_world_version),
        ("engine_version", configuration.engine_version),
        ("student_api_version", configuration.student_api_version),
        ("cohort.id", configuration.cohort.cohort_id),
        ("cohort.display_name", configuration.cohort.display_name),
        *((f"packages[{index}].id", package.package_id) for index, package in enumerate(pins)),
        *(
            (f"packages[{index}].version", package.package_version)
            for index, package in enumerate(pins)
        ),
    )
    for location, value in text_values:
        if not _is_utf8_compatible(value):
            raise ValueError(f"configuration contains non-UTF-8-compatible text at {location}")

    manifest: dict[str, Any] = {
        "schema_version": configuration.schema_version,
        "class_world": {
            "id": configuration.class_world_id,
            "display_name": configuration.display_name,
            "version": configuration.class_world_version,
        },
        "engine_version": configuration.engine_version,
        "student_api_version": configuration.student_api_version,
        "cohort": {
            "id": configuration.cohort.cohort_id,
            "display_name": configuration.cohort.display_name,
        },
        "packages": [
            {
                "id": package.package_id,
                "version": package.package_version,
            }
            for package in pins
        ],
    }
    return (
        json.dumps(
            manifest,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=False,
        )
        + "\n"
    )
