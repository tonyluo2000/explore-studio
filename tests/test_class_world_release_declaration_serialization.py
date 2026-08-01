"""Behavior-focused tests for release-declaration JSON serialization v0.1."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any

import pytest

from explore.packages import (
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldCohort,
    ClassWorldConfiguration,
    ClassWorldConfigurationSpec,
    ClassWorldPackagePin,
    ClassWorldReleaseDeclaration,
    ClassWorldReleaseDeclarationIssueCode,
    ClassWorldReleaseDeclarationParseResult,
    ClassWorldReleaseDeclarationSerializationIssueCode,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    build_class_world_configuration,
    build_class_world_release_declaration,
    parse_class_world_release_declaration,
    serialize_class_world_release_declaration,
)


def _provenance(package_id: str, package_version: str) -> PackageProvenance:
    return PackageProvenance(package_id, package_version, "0.1")


def _selected(
    package_id: str,
    package_version: str,
    entry: CharacterRegistration | WorldObjectRegistration,
) -> SelectedPackagePlan:
    provenance = _provenance(package_id, package_version)
    adjusted = replace(entry, provenance=provenance)
    return SelectedPackagePlan(
        package_id=package_id,
        package_version=package_version,
        provenance=provenance,
        registration_plan=StudentAPIRegistrationPlan(provenance, (adjusted,)),
    )


def _configuration() -> ClassWorldConfiguration:
    first_id = "zeta-character"
    second_id = "alpha-lantern"
    packages = (
        _selected(
            first_id,
            "2.1.0-beta.1+class",
            CharacterRegistration(
                f"{first_id}:hero",
                "hero",
                _provenance(first_id, "2.1.0-beta.1+class"),
                CharacterRegistrationSpec("Exploratrice", 10, 20, "gold"),
                None,
            ),
        ),
        _selected(
            second_id,
            "1.0.0",
            WorldObjectRegistration(
                f"{second_id}:lantern",
                "lantern",
                _provenance(second_id, "1.0.0"),
                WorldObjectRegistrationSpec(
                    "Lanterne",
                    30,
                    40,
                    "green",
                    "Regardez.",
                    "Trouvée!",
                ),
                None,
            ),
        ),
    )
    plan = PackageSetPlan(
        student_api_version="0.1",
        packages=packages,
        entries=tuple(entry for package in packages for entry in package.registration_plan.entries),
    )
    result = build_class_world_configuration(
        ClassWorldConfigurationSpec(
            schema_version="0.1",
            class_world_id="expedition-orion-fall-2026",
            display_name="Expédition Orion — Automne 2026 🚀",
            class_world_version="3.2.1",
            engine_version="1.4.0",
            student_api_version="0.1",
            cohort=ClassWorldCohort("expedition-orion", "Expédition Orion 🚀"),
            packages=tuple(
                ClassWorldPackagePin(package.package_id, package.package_version)
                for package in packages
            ),
        ),
        plan,
    )
    assert result.configuration is not None
    return result.configuration


def _declaration(
    configuration: ClassWorldConfiguration | None = None,
) -> ClassWorldReleaseDeclaration:
    result = build_class_world_release_declaration(
        configuration or _configuration(),
        release_id="spring-showcase",
        release_version="1.2.3-rc.1+school",
    )
    assert result.declaration is not None
    return result.declaration


def _release_dict() -> dict[str, Any]:
    return json.loads(serialize_class_world_release_declaration(_declaration()))


def _parse_dict(
    value: object,
    configuration: ClassWorldConfiguration | None = None,
) -> ClassWorldReleaseDeclarationParseResult:
    return parse_class_world_release_declaration(
        json.dumps(value, ensure_ascii=False),
        configuration or _configuration(),
    )


def _codes(
    result: ClassWorldReleaseDeclarationParseResult,
) -> list[ClassWorldReleaseDeclarationSerializationIssueCode]:
    return [issue.code for issue in result.issues]


def test_serializer_emits_exact_canonical_schema_order_and_format() -> None:
    declaration = _declaration()

    text = serialize_class_world_release_declaration(declaration)

    assert text == """{
  "schema_version": "0.1",
  "identity": {
    "release_id": "spring-showcase",
    "release_version": "1.2.3-rc.1+school",
    "class_world_id": "expedition-orion-fall-2026",
    "class_world_version": "3.2.1"
  },
  "provenance": {
    "engine_version": "1.4.0",
    "student_api_version": "0.1",
    "class_world_manifest_schema_version": "0.1",
    "manifest_transport_contract_version": "0.1",
    "cohort_id": "expedition-orion",
    "packages": [
      {
        "id": "zeta-character",
        "version": "2.1.0-beta.1+class"
      },
      {
        "id": "alpha-lantern",
        "version": "1.0.0"
      }
    ]
  }
}
"""
    decoded = json.loads(text, object_pairs_hook=lambda pairs: pairs)
    assert [key for key, _ in decoded] == ["schema_version", "identity", "provenance"]
    assert [key for key, _ in decoded[1][1]] == [
        "release_id",
        "release_version",
        "class_world_id",
        "class_world_version",
    ]
    assert [key for key, _ in decoded[2][1]] == [
        "engine_version",
        "student_api_version",
        "class_world_manifest_schema_version",
        "manifest_transport_contract_version",
        "cohort_id",
        "packages",
    ]
    assert all(not line.endswith(" ") for line in text.splitlines())
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert not text.startswith("\ufeff")
    assert "display_name" not in text


def test_equivalent_declarations_serialize_identically_without_mutation() -> None:
    first = _declaration()
    equivalent = _declaration()
    snapshot = first

    assert serialize_class_world_release_declaration(first) == (
        serialize_class_world_release_declaration(equivalent)
    )
    assert first == snapshot


@pytest.mark.parametrize("value", [None, object(), "declaration", b"declaration", True])
def test_serializer_rejects_wrong_input_types(value: object) -> None:
    with pytest.raises(TypeError, match="ClassWorldReleaseDeclaration"):
        serialize_class_world_release_declaration(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "changed",
    [
        lambda value: replace(value, declaration_version="9.9"),
        lambda value: replace(value, identity=replace(value.identity, release_id="Bad/ID")),
        lambda value: replace(value, identity=replace(value.identity, class_world_id="other")),
        lambda value: replace(
            value,
            provenance=replace(value.provenance, engine_version="9.9.9"),
        ),
        lambda value: replace(
            value,
            provenance=replace(value.provenance, student_api_version="9.9"),
        ),
        lambda value: replace(value, provenance=replace(value.provenance, cohort_id="other")),
        lambda value: replace(
            value,
            provenance=replace(
                value.provenance,
                package_pins=tuple(reversed(value.provenance.package_pins)),
            ),
        ),
        lambda value: replace(
            value,
            provenance=replace(value.provenance, class_world_manifest_schema_version="9.9"),
        ),
        lambda value: replace(
            value,
            provenance=replace(value.provenance, manifest_transport_contract_version="9.9"),
        ),
    ],
)
def test_serializer_rejects_manually_inconsistent_declarations(changed: Any) -> None:
    with pytest.raises(ValueError):
        serialize_class_world_release_declaration(changed(_declaration()))


def test_canonical_round_trip_retains_exact_configuration_and_text() -> None:
    declaration = _declaration()
    text = serialize_class_world_release_declaration(declaration)

    result = parse_class_world_release_declaration(text, declaration.configuration)

    assert result.is_parsed
    assert result.issues == ()
    assert result.declaration_issues == ()
    assert result.declaration == declaration
    assert result.declaration is not None
    assert result.declaration.configuration is declaration.configuration
    assert serialize_class_world_release_declaration(result.declaration) == text


def test_noncanonical_valid_json_is_accepted_and_canonicalized() -> None:
    declaration = _declaration()
    value = _release_dict()
    noncanonical = json.dumps(
        {
            "provenance": value["provenance"],
            "identity": {
                "class_world_version": value["identity"]["class_world_version"],
                "class_world_id": value["identity"]["class_world_id"],
                "release_version": value["identity"]["release_version"],
                "release_id": "\u0073pring-showcase",
            },
            "schema_version": value["schema_version"],
        },
        separators=(",", ":"),
    )

    result = parse_class_world_release_declaration(
        f" \n{noncanonical}\t",
        declaration.configuration,
    )

    assert result.is_parsed
    assert result.declaration == declaration
    assert result.declaration is not None
    canonical = serialize_class_world_release_declaration(result.declaration)
    assert canonical.startswith('{\n  "schema_version"')


@pytest.mark.parametrize(
    ("text", "code"),
    [
        (None, ClassWorldReleaseDeclarationSerializationIssueCode.TEXT_REQUIRED),
        ("", ClassWorldReleaseDeclarationSerializationIssueCode.TEXT_REQUIRED),
        (" \n\t", ClassWorldReleaseDeclarationSerializationIssueCode.TEXT_REQUIRED),
        (b"{}", ClassWorldReleaseDeclarationSerializationIssueCode.TEXT_INVALID_TYPE),
        (42, ClassWorldReleaseDeclarationSerializationIssueCode.TEXT_INVALID_TYPE),
        (True, ClassWorldReleaseDeclarationSerializationIssueCode.TEXT_INVALID_TYPE),
    ],
)
def test_text_input_contract_is_strict(text: object, code: object) -> None:
    result = parse_class_world_release_declaration(text, _configuration())  # type: ignore[arg-type]

    assert result.declaration is None
    assert _codes(result) == [code]
    assert result.declaration_issues == ()


@pytest.mark.parametrize("text", ["{", "{/*x*/}", '{"x":1,}'])
def test_malformed_json_comments_and_trailing_commas_are_rejected(text: str) -> None:
    result = parse_class_world_release_declaration(text, _configuration())

    assert _codes(result) == [ClassWorldReleaseDeclarationSerializationIssueCode.JSON_INVALID]


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_json_constants_are_rejected_at_json_boundary(constant: str) -> None:
    result = parse_class_world_release_declaration(
        f'{{"schema_version": {constant}}}',
        _configuration(),
    )

    assert _codes(result) == [
        ClassWorldReleaseDeclarationSerializationIssueCode.JSON_NONFINITE_NUMBER
    ]


@pytest.mark.parametrize("root", [[], "text", None, 1, True])
def test_non_object_roots_are_rejected(root: object) -> None:
    result = _parse_dict(root)

    assert _codes(result) == [ClassWorldReleaseDeclarationSerializationIssueCode.ROOT_INVALID_TYPE]
    assert result.issues[0].location == "$"


def test_duplicate_keys_are_rejected_at_precise_nested_locations_in_source_order() -> None:
    text = """{
      "schema_version":"0.1",
      "schema_version":"9.9",
      "identity":{
        "release_id":"spring-showcase",
        "release_id":"other",
        "release_version":"1.2.3-rc.1+school",
        "class_world_id":"expedition-orion-fall-2026",
        "class_world_version":"3.2.1"
      },
      "provenance":{
        "engine_version":"1.4.0",
        "student_api_version":"0.1",
        "class_world_manifest_schema_version":"0.1",
        "manifest_transport_contract_version":"0.1",
        "cohort_id":"expedition-orion",
        "packages":[
          {"id":"zeta-character","id":"other","version":"2.1.0-beta.1+class"},
          {"id":"alpha-lantern","version":"1.0.0","version":"9.9.9"}
        ]
      }
    }"""

    first = parse_class_world_release_declaration(text, _configuration())
    second = parse_class_world_release_declaration(text, _configuration())

    assert first == second
    assert (
        _codes(first) == [ClassWorldReleaseDeclarationSerializationIssueCode.JSON_DUPLICATE_KEY] * 4
    )
    assert [issue.location for issue in first.issues] == [
        "schema_version",
        "identity.release_id",
        "provenance.packages[0].id",
        "provenance.packages[1].version",
    ]


@pytest.mark.parametrize(
    "location",
    [
        "schema_version",
        "identity",
        "provenance",
        "identity.release_id",
        "identity.release_version",
        "identity.class_world_id",
        "identity.class_world_version",
        "provenance.engine_version",
        "provenance.student_api_version",
        "provenance.class_world_manifest_schema_version",
        "provenance.manifest_transport_contract_version",
        "provenance.cohort_id",
        "provenance.packages",
        "provenance.packages[0].id",
        "provenance.packages[0].version",
    ],
)
def test_every_required_field_is_enforced(location: str) -> None:
    value = _release_dict()
    parts = location.split(".")
    target: Any = value
    for part in parts[:-1]:
        target = target["packages"][0] if part == "packages[0]" else target[part]
    target.pop(parts[-1])

    result = _parse_dict(value)

    assert ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_REQUIRED in _codes(result)
    assert location in [issue.location for issue in result.issues]


@pytest.mark.parametrize(
    ("container", "field"),
    [
        ((), "extra_root"),
        (("identity",), "extra_identity"),
        (("provenance",), "extra_provenance"),
        (("provenance", "packages", 0), "extra_package"),
    ],
)
def test_unknown_fields_are_rejected_at_every_object(
    container: tuple[object, ...],
    field: str,
) -> None:
    value = _release_dict()
    target: Any = value
    for part in container:
        target = target[part]
    target[field] = "unknown"

    result = _parse_dict(value)

    assert _codes(result) == [ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_UNKNOWN]


@pytest.mark.parametrize("field", ["identity", "provenance"])
@pytest.mark.parametrize("wrong", [None, True, 1, "object", []])
def test_object_fields_require_exact_json_objects(field: str, wrong: object) -> None:
    value = _release_dict()
    value[field] = wrong

    result = _parse_dict(value)

    assert ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_INVALID_TYPE in _codes(result)


@pytest.mark.parametrize("wrong", [None, True, 1, "array", {}])
def test_packages_requires_exact_json_array(wrong: object) -> None:
    value = _release_dict()
    value["provenance"]["packages"] = wrong

    result = _parse_dict(value)

    assert ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_INVALID_TYPE in _codes(result)


@pytest.mark.parametrize("wrong", [None, True, 1, "object", []])
def test_package_entries_require_exact_json_objects(wrong: object) -> None:
    value = _release_dict()
    value["provenance"]["packages"][0] = wrong

    result = _parse_dict(value)

    assert ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_INVALID_TYPE in _codes(result)


@pytest.mark.parametrize("wrong", [None, True, 1, 1.5, [], {}])
@pytest.mark.parametrize(
    "location",
    [
        "schema_version",
        "identity.release_id",
        "identity.release_version",
        "identity.class_world_id",
        "identity.class_world_version",
        "provenance.engine_version",
        "provenance.student_api_version",
        "provenance.class_world_manifest_schema_version",
        "provenance.manifest_transport_contract_version",
        "provenance.cohort_id",
        "provenance.packages.0.id",
        "provenance.packages.0.version",
    ],
)
def test_string_fields_do_not_coerce(location: str, wrong: object) -> None:
    value = _release_dict()
    target: Any = value
    parts = location.split(".")
    for part in parts[:-1]:
        target = target[int(part)] if part.isdigit() else target[part]
    target[parts[-1]] = wrong

    result = _parse_dict(value)

    assert ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_INVALID_TYPE in _codes(result)


@pytest.mark.parametrize(
    ("location", "changed", "code"),
    [
        (
            "schema_version",
            "9.9",
            ClassWorldReleaseDeclarationSerializationIssueCode.SCHEMA_VERSION_UNSUPPORTED,
        ),
        (
            "identity.class_world_id",
            "other-world",
            ClassWorldReleaseDeclarationSerializationIssueCode.CLASS_WORLD_ID_MISMATCH,
        ),
        (
            "identity.class_world_version",
            "9.9.9",
            ClassWorldReleaseDeclarationSerializationIssueCode.CLASS_WORLD_VERSION_MISMATCH,
        ),
        (
            "provenance.engine_version",
            "9.9.9",
            ClassWorldReleaseDeclarationSerializationIssueCode.ENGINE_VERSION_MISMATCH,
        ),
        (
            "provenance.student_api_version",
            "9.9",
            ClassWorldReleaseDeclarationSerializationIssueCode.STUDENT_API_VERSION_MISMATCH,
        ),
        (
            "provenance.class_world_manifest_schema_version",
            "9.9",
            ClassWorldReleaseDeclarationSerializationIssueCode.MANIFEST_SCHEMA_VERSION_MISMATCH,
        ),
        (
            "provenance.manifest_transport_contract_version",
            "9.9",
            ClassWorldReleaseDeclarationSerializationIssueCode.MANIFEST_TRANSPORT_VERSION_MISMATCH,
        ),
        (
            "provenance.cohort_id",
            "other-cohort",
            ClassWorldReleaseDeclarationSerializationIssueCode.COHORT_ID_MISMATCH,
        ),
        (
            "provenance.packages.0.id",
            "other-package",
            ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_ID_MISMATCH,
        ),
        (
            "provenance.packages.0.version",
            "9.9.9",
            ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_VERSION_MISMATCH,
        ),
    ],
)
def test_schema_versions_and_configuration_derived_values_must_agree(
    location: str,
    changed: str,
    code: ClassWorldReleaseDeclarationSerializationIssueCode,
) -> None:
    value = _release_dict()
    target: Any = value
    parts = location.split(".")
    for part in parts[:-1]:
        target = target[int(part)] if part.isdigit() else target[part]
    target[parts[-1]] = changed

    result = _parse_dict(value)

    assert code in _codes(result)
    assert result.declaration is None
    assert result.declaration_issues == ()


def test_package_count_and_order_are_not_repaired() -> None:
    missing = _release_dict()
    missing["provenance"]["packages"].pop()
    extra = _release_dict()
    extra["provenance"]["packages"].append({"id": "extra", "version": "1.0.0"})
    reordered = _release_dict()
    reordered["provenance"]["packages"].reverse()

    missing_result = _parse_dict(missing)
    extra_result = _parse_dict(extra)
    reordered_result = _parse_dict(reordered)

    assert _codes(missing_result) == [
        ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_COUNT_MISMATCH
    ]
    assert _codes(extra_result) == [
        ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_COUNT_MISMATCH
    ]
    assert _codes(reordered_result) == [
        ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_ID_MISMATCH,
        ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_VERSION_MISMATCH,
        ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_ID_MISMATCH,
        ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_VERSION_MISMATCH,
    ]


@pytest.mark.parametrize(
    ("field", "changed", "expected"),
    [
        (
            "release_id",
            "Bad/ID",
            ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID,
        ),
        (
            "release_version",
            "01.0",
            ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID,
        ),
    ],
)
def test_builder_release_identity_issues_are_preserved_separately(
    field: str,
    changed: str,
    expected: ClassWorldReleaseDeclarationIssueCode,
) -> None:
    value = _release_dict()
    value["identity"][field] = changed

    result = _parse_dict(value)

    assert result.declaration is None
    assert result.issues == ()
    assert [issue.code for issue in result.declaration_issues] == [expected]


@pytest.mark.parametrize(
    ("configuration", "expected"),
    [
        (None, ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_REQUIRED),
        (object(), ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID_TYPE),
    ],
)
def test_configuration_input_issues_are_preserved_from_builder(
    configuration: object,
    expected: ClassWorldReleaseDeclarationIssueCode,
) -> None:
    text = json.dumps(_release_dict())

    result = parse_class_world_release_declaration(
        text,
        configuration,  # type: ignore[arg-type]
    )

    assert result.declaration is None
    assert result.issues == ()
    assert [issue.code for issue in result.declaration_issues] == [expected]


def test_manually_inconsistent_configuration_preserves_builder_issues() -> None:
    configuration = _configuration()
    invalid = replace(
        configuration,
        package_set_plan=replace(configuration.package_set_plan, entries=()),
    )
    value = _release_dict()

    result = _parse_dict(value, invalid)

    assert result.declaration is None
    assert result.issues == ()
    assert ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID in [
        issue.code for issue in result.declaration_issues
    ]


def test_non_utf8_compatible_json_string_is_rejected_structurally() -> None:
    value = _release_dict()
    value["identity"]["release_id"] = "bad\ud800value"

    result = _parse_dict(value)

    assert _codes(result) == [
        ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_INVALID_VALUE
    ]
    assert result.issues[0].location == "identity.release_id"


def test_results_and_issues_are_deeply_immutable_and_deterministic() -> None:
    first = parse_class_world_release_declaration("{}", _configuration())
    second = parse_class_world_release_declaration("{}", _configuration())

    assert first == second
    assert isinstance(first.issues, tuple)
    assert isinstance(first.declaration_issues, tuple)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        first.issues = ()  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        first.issues[0].location = "changed"  # type: ignore[misc]


def test_public_exports_include_only_the_intentional_serialization_surface() -> None:
    import explore.packages as packages

    expected = {
        "serialize_class_world_release_declaration",
        "parse_class_world_release_declaration",
        "ClassWorldReleaseDeclarationParseResult",
        "ClassWorldReleaseDeclarationSerializationIssue",
        "ClassWorldReleaseDeclarationSerializationIssueCode",
        "SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
    assert not any(name.startswith("_") for name in packages.__all__)


def test_serialization_source_stays_inside_the_pure_text_boundary() -> None:
    from explore.packages import class_world_release_declaration_serialization

    source = Path(class_world_release_declaration_serialization.__file__).read_text(
        encoding="utf-8"
    )
    forbidden = (
        "import hashlib",
        "import hmac",
        "import cryptography",
        "import os",
        "import pathlib",
        "import subprocess",
        "import uuid",
        "import random",
        "import secrets",
        "import datetime",
        "import time",
        "import pygame",
        "from engine",
        "serialize_class_world_manifest",
        "parse_class_world_manifest",
        "read_class_world_manifest_file",
        "write_class_world_manifest_file",
        "load_explorer_package",
        "validate_explorer_package",
        "build_package_set_plan",
        "apply_package_set_plan",
        "build_student_api_registration_plan",
        "apply_student_api_registration_plan",
        "World(",
        "Character(",
        "open(",
        "eval(",
        "exec(",
    )

    assert all(term not in source for term in forbidden)
