"""Strict JSON parsing and canonical serialization for release declarations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from explore.packages.class_world_configuration_models import ClassWorldConfiguration
from explore.packages.class_world_manifest_models import (
    SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION,
)
from explore.packages.class_world_manifest_transport_models import (
    SUPPORTED_CLASS_WORLD_MANIFEST_TRANSPORT_CONTRACT_VERSION,
)
from explore.packages.class_world_release_declaration import (
    build_class_world_release_declaration,
)
from explore.packages.class_world_release_declaration_models import (
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION,
    ClassWorldReleaseDeclaration,
)
from explore.packages.class_world_release_declaration_serialization_models import (
    ClassWorldReleaseDeclarationParseResult,
    ClassWorldReleaseDeclarationSerializationIssue,
    ClassWorldReleaseDeclarationSerializationIssueCode,
)

_ROOT_FIELDS = ("schema_version", "identity", "provenance")
_IDENTITY_FIELDS = (
    "release_id",
    "release_version",
    "class_world_id",
    "class_world_version",
)
_PROVENANCE_FIELDS = (
    "engine_version",
    "student_api_version",
    "class_world_manifest_schema_version",
    "manifest_transport_contract_version",
    "cohort_id",
    "packages",
)
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
    code: ClassWorldReleaseDeclarationSerializationIssueCode,
    message: str,
    location: str,
) -> ClassWorldReleaseDeclarationSerializationIssue:
    return ClassWorldReleaseDeclarationSerializationIssue(
        code=code,
        message=message,
        location=location,
    )


def _failure(
    issues: tuple[ClassWorldReleaseDeclarationSerializationIssue, ...],
) -> ClassWorldReleaseDeclarationParseResult:
    return ClassWorldReleaseDeclarationParseResult(
        declaration=None,
        issues=issues,
        declaration_issues=(),
    )


def _duplicate_issues(
    value: object,
    location: str = "",
) -> list[ClassWorldReleaseDeclarationSerializationIssue]:
    issues: list[ClassWorldReleaseDeclarationSerializationIssue] = []
    if isinstance(value, _JSONObject):
        seen: set[str] = set()
        for key, child in value.pairs:
            child_location = f"{location}.{key}" if location else key
            if key in seen:
                issues.append(
                    _issue(
                        ClassWorldReleaseDeclarationSerializationIssueCode.JSON_DUPLICATE_KEY,
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


def _required_issue(location: str) -> ClassWorldReleaseDeclarationSerializationIssue:
    return _issue(
        ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_REQUIRED,
        f"{location} is required.",
        location,
    )


def _type_issue(
    location: str,
    expected: str,
) -> ClassWorldReleaseDeclarationSerializationIssue:
    return _issue(
        ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_INVALID_TYPE,
        f"{location} must be a JSON {expected}.",
        location,
    )


def _is_utf8_compatible(value: str) -> bool:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _unknown_issues(
    value: dict[str, object],
    allowed: tuple[str, ...],
    location: str = "",
) -> list[ClassWorldReleaseDeclarationSerializationIssue]:
    allowed_names = frozenset(allowed)
    return [
        _issue(
            ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_UNKNOWN,
            f"{field_location} is not a recognized release-declaration field.",
            field_location,
        )
        for key in sorted(value.keys() - allowed_names)
        for field_location in (f"{location}.{key}" if location else key,)
    ]


def _validate_string_fields(
    value: dict[str, object],
    fields: tuple[str, ...],
    location: str,
    *,
    include_unknown: bool = True,
) -> list[ClassWorldReleaseDeclarationSerializationIssue]:
    issues: list[ClassWorldReleaseDeclarationSerializationIssue] = []
    for field in fields:
        field_location = f"{location}.{field}"
        if field not in value:
            issues.append(_required_issue(field_location))
        elif not isinstance(value[field], str):
            issues.append(_type_issue(field_location, "string"))
        elif not _is_utf8_compatible(value[field]):
            issues.append(
                _issue(
                    ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_INVALID_VALUE,
                    f"{field_location} must contain UTF-8-compatible Unicode text.",
                    field_location,
                )
            )
    if include_unknown:
        issues.extend(_unknown_issues(value, fields, location))
    return issues


def _validate_structure(
    root: dict[str, object],
) -> list[ClassWorldReleaseDeclarationSerializationIssue]:
    issues: list[ClassWorldReleaseDeclarationSerializationIssue] = []
    expected_types: dict[str, tuple[type, str]] = {
        "schema_version": (str, "string"),
        "identity": (dict, "object"),
        "provenance": (dict, "object"),
    }
    for field in _ROOT_FIELDS:
        if field not in root:
            issues.append(_required_issue(field))
            continue
        expected_type, description = expected_types[field]
        if not isinstance(root[field], expected_type):
            issues.append(_type_issue(field, description))
        elif isinstance(root[field], str) and not _is_utf8_compatible(root[field]):
            issues.append(
                _issue(
                    ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_INVALID_VALUE,
                    f"{field} must contain UTF-8-compatible Unicode text.",
                    field,
                )
            )
        elif (
            field == "schema_version"
            and root[field] != SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION
        ):
            issues.append(
                _issue(
                    ClassWorldReleaseDeclarationSerializationIssueCode.SCHEMA_VERSION_UNSUPPORTED,
                    (
                        "schema_version must be exactly "
                        f'"{SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION}".'
                    ),
                    "schema_version",
                )
            )
    issues.extend(_unknown_issues(root, _ROOT_FIELDS))

    identity = root.get("identity")
    if isinstance(identity, dict):
        issues.extend(_validate_string_fields(identity, _IDENTITY_FIELDS, "identity"))

    provenance = root.get("provenance")
    if isinstance(provenance, dict):
        issues.extend(
            _validate_string_fields(
                provenance,
                _PROVENANCE_FIELDS[:-1],
                "provenance",
                include_unknown=False,
            )
        )
        if "packages" not in provenance:
            issues.append(_required_issue("provenance.packages"))
        elif not isinstance(provenance["packages"], list):
            issues.append(_type_issue("provenance.packages", "array"))
        issues.extend(_unknown_issues(provenance, _PROVENANCE_FIELDS, "provenance"))

        packages = provenance.get("packages")
        if isinstance(packages, list):
            for package_index, package in enumerate(packages):
                location = f"provenance.packages[{package_index}]"
                if not isinstance(package, dict):
                    issues.append(_type_issue(location, "object"))
                    continue
                issues.extend(_validate_string_fields(package, _PACKAGE_FIELDS, location))
    return issues


def _mismatch_issue(
    code: ClassWorldReleaseDeclarationSerializationIssueCode,
    location: str,
    description: str,
) -> ClassWorldReleaseDeclarationSerializationIssue:
    return _issue(
        code,
        f"{location} must agree exactly with the supplied configuration {description}.",
        location,
    )


def _agreement_issues(
    root: dict[str, object],
    configuration: ClassWorldConfiguration,
) -> list[ClassWorldReleaseDeclarationSerializationIssue]:
    identity = root["identity"]
    provenance = root["provenance"]
    assert isinstance(identity, dict)
    assert isinstance(provenance, dict)
    packages = provenance["packages"]
    assert isinstance(packages, list)

    checks = (
        (
            identity["class_world_id"],
            configuration.class_world_id,
            ClassWorldReleaseDeclarationSerializationIssueCode.CLASS_WORLD_ID_MISMATCH,
            "identity.class_world_id",
            "class-world ID",
        ),
        (
            identity["class_world_version"],
            configuration.class_world_version,
            ClassWorldReleaseDeclarationSerializationIssueCode.CLASS_WORLD_VERSION_MISMATCH,
            "identity.class_world_version",
            "class-world version",
        ),
        (
            provenance["engine_version"],
            configuration.engine_version,
            ClassWorldReleaseDeclarationSerializationIssueCode.ENGINE_VERSION_MISMATCH,
            "provenance.engine_version",
            "engine version",
        ),
        (
            provenance["student_api_version"],
            configuration.student_api_version,
            ClassWorldReleaseDeclarationSerializationIssueCode.STUDENT_API_VERSION_MISMATCH,
            "provenance.student_api_version",
            "Student API version",
        ),
        (
            provenance["class_world_manifest_schema_version"],
            SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION,
            ClassWorldReleaseDeclarationSerializationIssueCode.MANIFEST_SCHEMA_VERSION_MISMATCH,
            "provenance.class_world_manifest_schema_version",
            "supported manifest schema version",
        ),
        (
            provenance["manifest_transport_contract_version"],
            SUPPORTED_CLASS_WORLD_MANIFEST_TRANSPORT_CONTRACT_VERSION,
            ClassWorldReleaseDeclarationSerializationIssueCode.MANIFEST_TRANSPORT_VERSION_MISMATCH,
            "provenance.manifest_transport_contract_version",
            "supported manifest transport contract version",
        ),
        (
            provenance["cohort_id"],
            configuration.cohort.cohort_id,
            ClassWorldReleaseDeclarationSerializationIssueCode.COHORT_ID_MISMATCH,
            "provenance.cohort_id",
            "cohort ID",
        ),
    )
    issues = [
        _mismatch_issue(code, location, description)
        for actual, expected, code, location, description in checks
        if actual != expected
    ]

    expected_packages = configuration.packages
    if len(packages) != len(expected_packages):
        issues.append(
            _mismatch_issue(
                ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_COUNT_MISMATCH,
                "provenance.packages",
                "package count",
            )
        )
        return issues

    for index, (package, expected) in enumerate(zip(packages, expected_packages, strict=True)):
        assert isinstance(package, dict)
        if package["id"] != expected.package_id:
            issues.append(
                _mismatch_issue(
                    ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_ID_MISMATCH,
                    f"provenance.packages[{index}].id",
                    "package ID and order",
                )
            )
        if package["version"] != expected.package_version:
            issues.append(
                _mismatch_issue(
                    ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_VERSION_MISMATCH,
                    f"provenance.packages[{index}].version",
                    "package version",
                )
            )
    return issues


def parse_class_world_release_declaration(
    text: str,
    configuration: ClassWorldConfiguration,
) -> ClassWorldReleaseDeclarationParseResult:
    """Parse declaration JSON against one authoritative immutable configuration.

    The operation is pure and all-or-nothing. It rejects duplicate keys,
    non-standard numeric constants, schema drift, and any disagreement with the
    supplied configuration. Final construction is delegated to the existing
    release-declaration builder.
    """
    if text is None or (isinstance(text, str) and not text.strip()):
        return _failure(
            (
                _issue(
                    ClassWorldReleaseDeclarationSerializationIssueCode.TEXT_REQUIRED,
                    "text must be a non-empty string.",
                    "text",
                ),
            )
        )
    if not isinstance(text, str):
        return _failure(
            (
                _issue(
                    ClassWorldReleaseDeclarationSerializationIssueCode.TEXT_INVALID_TYPE,
                    "text must be a string.",
                    "text",
                ),
            )
        )

    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_object_pairs,
            parse_constant=_reject_non_finite_number,
        )
    except json.JSONDecodeError as error:
        return _failure(
            (
                _issue(
                    ClassWorldReleaseDeclarationSerializationIssueCode.JSON_INVALID,
                    f"Invalid JSON at line {error.lineno}, column {error.colno}.",
                    "text",
                ),
            )
        )
    except _NonFiniteNumberError:
        return _failure(
            (
                _issue(
                    ClassWorldReleaseDeclarationSerializationIssueCode.JSON_NONFINITE_NUMBER,
                    "Invalid JSON: non-finite numeric constants are not permitted.",
                    "text",
                ),
            )
        )

    duplicate_issues = _duplicate_issues(decoded)
    if duplicate_issues:
        return _failure(tuple(duplicate_issues))
    if not isinstance(decoded, _JSONObject):
        return _failure(
            (
                _issue(
                    ClassWorldReleaseDeclarationSerializationIssueCode.ROOT_INVALID_TYPE,
                    "The release-declaration root must be a JSON object.",
                    "$",
                ),
            )
        )

    root = _to_json_value(decoded)
    assert isinstance(root, dict)
    structure_issues = _validate_structure(root)
    if structure_issues:
        return _failure(tuple(structure_issues))

    if isinstance(configuration, ClassWorldConfiguration):
        try:
            agreement_issues = _agreement_issues(root, configuration)
        except (AttributeError, TypeError):
            agreement_issues = []
        if agreement_issues:
            return _failure(tuple(agreement_issues))

    identity = root["identity"]
    assert isinstance(identity, dict)
    declaration_result = build_class_world_release_declaration(
        configuration,
        release_id=identity["release_id"],  # type: ignore[arg-type]
        release_version=identity["release_version"],  # type: ignore[arg-type]
    )
    if declaration_result.issues:
        return ClassWorldReleaseDeclarationParseResult(
            declaration=None,
            issues=(),
            declaration_issues=declaration_result.issues,
        )
    return ClassWorldReleaseDeclarationParseResult(
        declaration=declaration_result.declaration,
        issues=(),
        declaration_issues=(),
    )


def serialize_class_world_release_declaration(
    declaration: ClassWorldReleaseDeclaration,
) -> str:
    """Return canonical JSON text for one valid immutable release declaration.

    Raises:
        TypeError: If *declaration* is not a ``ClassWorldReleaseDeclaration``.
        ValueError: If a manually constructed declaration is inconsistent.
    """
    if not isinstance(declaration, ClassWorldReleaseDeclaration):
        raise TypeError("declaration must be a ClassWorldReleaseDeclaration")
    try:
        rebuilt = build_class_world_release_declaration(
            declaration.configuration,
            release_id=declaration.identity.release_id,
            release_version=declaration.identity.release_version,
        )
    except (AttributeError, TypeError):
        raise ValueError("declaration contains invalid immutable structure") from None
    if rebuilt.issues:
        first = rebuilt.issues[0]
        raise ValueError(f"declaration is invalid: {first.code} at {first.location}")
    if rebuilt.declaration != declaration:
        raise ValueError("declaration is inconsistent with its retained configuration")

    release: dict[str, Any] = {
        "schema_version": declaration.declaration_version,
        "identity": {
            "release_id": declaration.identity.release_id,
            "release_version": declaration.identity.release_version,
            "class_world_id": declaration.identity.class_world_id,
            "class_world_version": declaration.identity.class_world_version,
        },
        "provenance": {
            "engine_version": declaration.provenance.engine_version,
            "student_api_version": declaration.provenance.student_api_version,
            "class_world_manifest_schema_version": (
                declaration.provenance.class_world_manifest_schema_version
            ),
            "manifest_transport_contract_version": (
                declaration.provenance.manifest_transport_contract_version
            ),
            "cohort_id": declaration.provenance.cohort_id,
            "packages": [
                {
                    "id": package.package_id,
                    "version": package.package_version,
                }
                for package in declaration.provenance.package_pins
            ],
        },
    }
    return (
        json.dumps(
            release,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=False,
        )
        + "\n"
    )
