"""Behavior-focused tests for serialized class-world manifest schema v0.1."""

from __future__ import annotations

import hashlib
import importlib
import json
import socket
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from explore.packages import (
    SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldCohort,
    ClassWorldConfiguration,
    ClassWorldConfigurationSpec,
    ClassWorldManifestIssueCode,
    ClassWorldManifestParseResult,
    ClassWorldPackagePin,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    build_class_world_configuration,
    parse_class_world_manifest,
    serialize_class_world_manifest,
)


def _provenance(package_id: str, package_version: str = "1.0.0") -> PackageProvenance:
    return PackageProvenance(package_id, package_version, "0.1")


def _selected(
    package_id: str,
    entry: CharacterRegistration | WorldObjectRegistration,
    package_version: str = "1.0.0",
) -> SelectedPackagePlan:
    provenance = _provenance(package_id, package_version)
    adjusted = replace(entry, provenance=provenance)
    registration_plan = StudentAPIRegistrationPlan(provenance, (adjusted,))
    return SelectedPackagePlan(
        package_id,
        package_version,
        provenance,
        registration_plan,
    )


def _character(package_id: str) -> CharacterRegistration:
    return CharacterRegistration(
        f"{package_id}:hero",
        "hero",
        _provenance(package_id),
        CharacterRegistrationSpec("Explorer", 10, 20, "gold"),
        None,
    )


def _world_object(package_id: str) -> WorldObjectRegistration:
    return WorldObjectRegistration(
        f"{package_id}:lantern",
        "lantern",
        _provenance(package_id),
        WorldObjectRegistrationSpec(
            "Crystal Lantern",
            30,
            40,
            "green",
            "Look closer.",
            "You found it!",
        ),
        None,
    )


def _plan(*packages: SelectedPackagePlan) -> PackageSetPlan:
    return PackageSetPlan(
        student_api_version="0.1",
        packages=packages,
        entries=tuple(entry for package in packages for entry in package.registration_plan.entries),
    )


def _valid_plan() -> PackageSetPlan:
    return _plan(
        _selected("nova-character", _character("nova-character")),
        _selected("crystal-lantern", _world_object("crystal-lantern")),
    )


def _configuration(
    plan: PackageSetPlan | None = None,
    *,
    display_name: str = "Expedition Orion — Fall 2026",
    cohort_display_name: str = "Expedition Orion",
) -> ClassWorldConfiguration:
    selected_plan = plan or _valid_plan()
    spec = ClassWorldConfigurationSpec(
        schema_version="0.1",
        class_world_id="expedition-orion-fall-2026",
        display_name=display_name,
        class_world_version="1.0.0",
        engine_version="1.0.0",
        student_api_version="0.1",
        cohort=ClassWorldCohort("expedition-orion", cohort_display_name),
        packages=tuple(
            ClassWorldPackagePin(package.package_id, package.package_version)
            for package in selected_plan.packages
        ),
    )
    result = build_class_world_configuration(spec, selected_plan)
    assert result.configuration is not None
    return result.configuration


def _manifest_dict(configuration: ClassWorldConfiguration | None = None) -> dict[str, Any]:
    return json.loads(serialize_class_world_manifest(configuration or _configuration()))


def _parse_dict(
    manifest: dict[str, Any],
    plan: PackageSetPlan | None = None,
) -> ClassWorldManifestParseResult:
    return parse_class_world_manifest(json.dumps(manifest), plan or _valid_plan())


def _codes(result: ClassWorldManifestParseResult) -> list[ClassWorldManifestIssueCode]:
    return [issue.code for issue in result.issues]


def test_canonical_serialization_has_exact_schema_order_format_and_content() -> None:
    text = serialize_class_world_manifest(_configuration())

    assert text == (
        "{\n"
        '  "schema_version": "0.1",\n'
        '  "class_world": {\n'
        '    "id": "expedition-orion-fall-2026",\n'
        '    "display_name": "Expedition Orion — Fall 2026",\n'
        '    "version": "1.0.0"\n'
        "  },\n"
        '  "engine_version": "1.0.0",\n'
        '  "student_api_version": "0.1",\n'
        '  "cohort": {\n'
        '    "id": "expedition-orion",\n'
        '    "display_name": "Expedition Orion"\n'
        "  },\n"
        '  "packages": [\n'
        "    {\n"
        '      "id": "nova-character",\n'
        '      "version": "1.0.0"\n'
        "    },\n"
        "    {\n"
        '      "id": "crystal-lantern",\n'
        '      "version": "1.0.0"\n'
        "    }\n"
        "  ]\n"
        "}\n"
    )
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert "\\u2014" not in text
    assert all(not line.endswith(" ") for line in text.splitlines())


def test_serialization_preserves_display_whitespace_package_order_and_determinism() -> None:
    configuration = _configuration(
        display_name="  Expedition Ω — Fall 2026  ",
        cohort_display_name="  Orion Cohort  ",
    )

    first = serialize_class_world_manifest(configuration)
    second = serialize_class_world_manifest(
        _configuration(
            display_name="  Expedition Ω — Fall 2026  ",
            cohort_display_name="  Orion Cohort  ",
        )
    )

    assert first == second
    assert "  Expedition Ω — Fall 2026  " in first
    assert "  Orion Cohort  " in first
    assert first.index("nova-character") < first.index("crystal-lantern")
    for forbidden in (
        "timestamp",
        "uuid",
        "hash",
        "signature",
        "registration_plan",
        "entries",
        "asset",
        "repository",
    ):
        assert forbidden not in first


def test_canonical_and_noncanonical_json_parse_to_the_expected_configuration() -> None:
    configuration = _configuration()
    canonical = serialize_class_world_manifest(configuration)
    reordered = {
        "packages": _manifest_dict()["packages"],
        "cohort": {"display_name": "Expedition Orion", "id": "expedition-orion"},
        "student_api_version": "0.1",
        "engine_version": "1.0.0",
        "class_world": {
            "version": "1.0.0",
            "display_name": "Expedition Orion — Fall 2026",
            "id": "expedition-orion-fall-2026",
        },
        "schema_version": "0.1",
    }

    results = (
        parse_class_world_manifest(canonical, configuration.package_set_plan),
        parse_class_world_manifest(json.dumps(reordered, separators=(",", ":")), _valid_plan()),
    )

    assert all(result.is_parsed for result in results)
    assert all(result.configuration == configuration for result in results)
    assert results[0] == parse_class_world_manifest(canonical, configuration.package_set_plan)


def test_round_trip_preserves_configuration_and_canonical_text() -> None:
    configuration = _configuration(
        display_name="  Expedition Ω — Fall 2026  ",
        cohort_display_name="  Expedition Orion  ",
    )
    text_one = serialize_class_world_manifest(configuration)

    parsed = parse_class_world_manifest(text_one, configuration.package_set_plan)

    assert parsed.configuration == configuration
    assert parsed.configuration is not None
    assert serialize_class_world_manifest(parsed.configuration) == text_one


def test_reordered_matching_plan_and_manifest_form_a_distinct_valid_round_trip() -> None:
    original = _valid_plan()
    reversed_plan = replace(
        original,
        packages=tuple(reversed(original.packages)),
        entries=tuple(reversed(original.entries)),
    )
    configuration = _configuration(reversed_plan)

    parsed = parse_class_world_manifest(
        serialize_class_world_manifest(configuration),
        reversed_plan,
    )

    assert parsed.configuration == configuration
    assert parsed.configuration is not None
    assert [pin.package_id for pin in parsed.configuration.packages] == [
        "crystal-lantern",
        "nova-character",
    ]


@pytest.mark.parametrize("manifest_text", [None, object(), b"{}", "", " \n\t"])
def test_missing_or_non_string_manifest_text_is_structured(manifest_text: object) -> None:
    result = parse_class_world_manifest(manifest_text, _valid_plan())  # type: ignore[arg-type]

    assert result.configuration is None
    assert _codes(result) == [ClassWorldManifestIssueCode.MANIFEST_TEXT_REQUIRED]


@pytest.mark.parametrize("plan", [None, object(), "plan"])
def test_missing_or_wrong_package_set_plan_is_structured(plan: object) -> None:
    result = parse_class_world_manifest("{}", plan)  # type: ignore[arg-type]

    assert result.configuration is None
    assert _codes(result) == [ClassWorldManifestIssueCode.PACKAGE_SET_PLAN_REQUIRED]


@pytest.mark.parametrize(
    "manifest_text",
    [
        "{",
        '{"schema_version":"0.1",}',
        '{"schema_version":/* no */"0.1"}',
        '{"value":NaN}',
        '{"value":Infinity}',
        '{"value":-Infinity}',
    ],
)
def test_malformed_and_non_finite_json_is_rejected(manifest_text: str) -> None:
    result = parse_class_world_manifest(manifest_text, _valid_plan())

    assert result.configuration is None
    assert _codes(result) == [ClassWorldManifestIssueCode.MANIFEST_INVALID_JSON]
    assert "/Users/" not in result.issues[0].message
    assert "0x" not in result.issues[0].message


@pytest.mark.parametrize("root", [[], "manifest", 1, 1.5, True, False, None])
def test_non_object_json_roots_are_rejected(root: object) -> None:
    result = parse_class_world_manifest(json.dumps(root), _valid_plan())

    assert result.configuration is None
    assert _codes(result) == [ClassWorldManifestIssueCode.MANIFEST_ROOT_INVALID]
    assert result.issues[0].location == "$"


@pytest.mark.parametrize(
    ("manifest_text", "location"),
    [
        ('{"schema_version":"0.1","schema_version":"0.2"}', "schema_version"),
        (
            '{"class_world":{"id":"one","id":"two"}}',
            "class_world.id",
        ),
        (
            '{"cohort":{"display_name":"one","display_name":"two"}}',
            "cohort.display_name",
        ),
        (
            '{"packages":[{}, {"version":"1.0.0","version":"2.0.0"}]}',
            "packages[1].version",
        ),
    ],
)
def test_duplicate_keys_are_rejected_with_precise_locations(
    manifest_text: str,
    location: str,
) -> None:
    first = parse_class_world_manifest(manifest_text, _valid_plan())
    second = parse_class_world_manifest(manifest_text, _valid_plan())

    assert first == second
    assert first.configuration is None
    assert _codes(first) == [ClassWorldManifestIssueCode.MANIFEST_DUPLICATE_KEY]
    assert first.issues[0].location == location


def test_multiple_duplicate_keys_are_reported_in_stable_decode_order() -> None:
    text = '{"cohort":{"id":"a","id":"b"},"packages":[{"id":"a","id":"b"}]}'

    result = parse_class_world_manifest(text, _valid_plan())

    assert [issue.location for issue in result.issues] == ["cohort.id", "packages[0].id"]


@pytest.mark.parametrize(
    ("mutation", "location"),
    [
        (lambda value: value.pop("schema_version"), "schema_version"),
        (lambda value: value.pop("class_world"), "class_world"),
        (lambda value: value["class_world"].pop("id"), "class_world.id"),
        (
            lambda value: value["class_world"].pop("display_name"),
            "class_world.display_name",
        ),
        (lambda value: value["class_world"].pop("version"), "class_world.version"),
        (lambda value: value.pop("engine_version"), "engine_version"),
        (lambda value: value.pop("student_api_version"), "student_api_version"),
        (lambda value: value.pop("cohort"), "cohort"),
        (lambda value: value["cohort"].pop("id"), "cohort.id"),
        (lambda value: value["cohort"].pop("display_name"), "cohort.display_name"),
        (lambda value: value.pop("packages"), "packages"),
        (lambda value: value["packages"][0].pop("id"), "packages[0].id"),
        (lambda value: value["packages"][0].pop("version"), "packages[0].version"),
    ],
)
def test_every_missing_field_is_rejected(
    mutation: Any,
    location: str,
) -> None:
    manifest = _manifest_dict()
    mutation(manifest)

    result = _parse_dict(manifest)

    assert result.configuration is None
    assert ClassWorldManifestIssueCode.MANIFEST_FIELD_REQUIRED in _codes(result)
    assert location in [issue.location for issue in result.issues]


@pytest.mark.parametrize(
    ("mutation", "location"),
    [
        (lambda value: value.update(extra=True), "extra"),
        (lambda value: value["class_world"].update(alias="x"), "class_world.alias"),
        (lambda value: value["cohort"].update(name="x"), "cohort.name"),
        (lambda value: value["packages"][0].update(source="x"), "packages[0].source"),
    ],
)
def test_unknown_fields_are_rejected(mutation: Any, location: str) -> None:
    manifest = _manifest_dict()
    mutation(manifest)

    result = _parse_dict(manifest)

    assert result.configuration is None
    assert ClassWorldManifestIssueCode.MANIFEST_FIELD_UNKNOWN in _codes(result)
    assert location in [issue.location for issue in result.issues]


def test_multiple_unknown_fields_are_sorted_deterministically() -> None:
    manifest = _manifest_dict()
    manifest["zeta"] = 1
    manifest["alpha"] = 2

    result = _parse_dict(manifest)

    unknown = [
        issue.location
        for issue in result.issues
        if issue.code is ClassWorldManifestIssueCode.MANIFEST_FIELD_UNKNOWN
    ]
    assert unknown == ["alpha", "zeta"]


@pytest.mark.parametrize(
    ("mutation", "location"),
    [
        (lambda value: value.update(schema_version=1), "schema_version"),
        (lambda value: value.update(schema_version=True), "schema_version"),
        (lambda value: value.update(class_world=[]), "class_world"),
        (lambda value: value["class_world"].update(id=1), "class_world.id"),
        (
            lambda value: value["class_world"].update(display_name=None),
            "class_world.display_name",
        ),
        (lambda value: value["class_world"].update(version=[]), "class_world.version"),
        (lambda value: value.update(engine_version=False), "engine_version"),
        (lambda value: value.update(student_api_version=1), "student_api_version"),
        (lambda value: value.update(cohort=[]), "cohort"),
        (lambda value: value.update(packages={}), "packages"),
        (lambda value: value["packages"].__setitem__(0, "package"), "packages[0]"),
        (lambda value: value["packages"][0].update(id=1), "packages[0].id"),
        (lambda value: value["packages"][0].update(version=None), "packages[0].version"),
    ],
)
def test_strict_json_types_are_enforced(mutation: Any, location: str) -> None:
    manifest = _manifest_dict()
    mutation(manifest)

    result = _parse_dict(manifest)

    assert result.configuration is None
    assert ClassWorldManifestIssueCode.MANIFEST_FIELD_INVALID_TYPE in _codes(result)
    assert location in [issue.location for issue in result.issues]


@pytest.mark.parametrize("version", ["0.1.0", "0.10", "1.0", ""])
def test_only_exact_manifest_schema_version_is_supported(version: str) -> None:
    manifest = _manifest_dict()
    manifest["schema_version"] = version

    result = _parse_dict(manifest)

    assert result.configuration is None
    assert _codes(result) == [ClassWorldManifestIssueCode.MANIFEST_SCHEMA_UNSUPPORTED]


def test_lone_unicode_surrogates_are_not_accepted_as_transport_text() -> None:
    manifest = _manifest_dict()
    manifest["class_world"]["display_name"] = "\ud800"

    result = _parse_dict(manifest)

    assert result.configuration is None
    assert _codes(result) == [ClassWorldManifestIssueCode.MANIFEST_FIELD_INVALID_VALUE]
    assert result.issues[0].location == "class_world.display_name"

    invalid_configuration = replace(_configuration(), display_name="\ud800")
    with pytest.raises(ValueError, match="non-UTF-8-compatible"):
        serialize_class_world_manifest(invalid_configuration)


@pytest.mark.parametrize(
    ("mutation", "configuration_code"),
    [
        (lambda value: value["class_world"].update(id="Bad World"), "CLASS_WORLD_ID_INVALID"),
        (
            lambda value: value["class_world"].update(display_name=" "),
            "CLASS_WORLD_DISPLAY_NAME_INVALID",
        ),
        (
            lambda value: value["class_world"].update(display_name="x" * 101),
            "CLASS_WORLD_DISPLAY_NAME_INVALID",
        ),
        (
            lambda value: value["class_world"].update(version="1.0"),
            "CLASS_WORLD_VERSION_INVALID",
        ),
        (lambda value: value.update(engine_version="latest"), "ENGINE_VERSION_INVALID"),
        (
            lambda value: value.update(student_api_version="0.1.0"),
            "STUDENT_API_VERSION_UNSUPPORTED",
        ),
        (lambda value: value["cohort"].update(id="Bad_Cohort"), "COHORT_ID_INVALID"),
        (
            lambda value: value["cohort"].update(display_name=" "),
            "COHORT_DISPLAY_NAME_INVALID",
        ),
        (
            lambda value: value["cohort"].update(display_name="x" * 101),
            "COHORT_DISPLAY_NAME_INVALID",
        ),
        (lambda value: value["packages"][0].update(id="Bad Package"), "PACKAGE_PIN_ID_INVALID"),
        (
            lambda value: value["packages"][0].update(version="1.0"),
            "PACKAGE_PIN_VERSION_INVALID",
        ),
    ],
)
def test_configuration_validation_diagnostics_are_preserved(
    mutation: Any,
    configuration_code: str,
) -> None:
    manifest = _manifest_dict()
    mutation(manifest)

    result = _parse_dict(manifest)

    assert result.configuration is None
    assert ClassWorldManifestIssueCode.CONFIGURATION_INVALID in _codes(result)
    assert any(configuration_code in issue.message for issue in result.issues)


def test_package_count_order_id_and_version_must_match_the_supplied_plan() -> None:
    manifest = _manifest_dict()
    missing = dict(manifest, packages=manifest["packages"][:-1])
    extra = dict(
        manifest,
        packages=[*manifest["packages"], {"id": "extra-package", "version": "1.0.0"}],
    )
    reordered = dict(manifest, packages=list(reversed(manifest["packages"])))
    wrong_id = _manifest_dict()
    wrong_id["packages"][0]["id"] = "other-package"
    wrong_version = _manifest_dict()
    wrong_version["packages"][0]["version"] = "2.0.0"

    results = [
        _parse_dict(missing),
        _parse_dict(extra),
        _parse_dict(reordered),
        _parse_dict(wrong_id),
        _parse_dict(wrong_version),
    ]

    assert all(result.configuration is None for result in results)
    assert ClassWorldManifestIssueCode.MANIFEST_PACKAGE_COUNT_MISMATCH in _codes(results[0])
    assert ClassWorldManifestIssueCode.MANIFEST_PACKAGE_COUNT_MISMATCH in _codes(results[1])
    assert ClassWorldManifestIssueCode.MANIFEST_PACKAGE_ORDER_MISMATCH in _codes(results[2])
    assert ClassWorldManifestIssueCode.MANIFEST_PACKAGE_ID_MISMATCH in _codes(results[3])
    assert ClassWorldManifestIssueCode.MANIFEST_PACKAGE_VERSION_MISMATCH in _codes(results[4])


def test_duplicate_and_conflicting_manifest_package_pins_are_not_corrected() -> None:
    duplicate = _manifest_dict()
    duplicate["packages"][1] = dict(duplicate["packages"][0])
    conflict = _manifest_dict()
    conflict["packages"][1] = {"id": "nova-character", "version": "2.0.0"}

    duplicate_result = _parse_dict(duplicate)
    conflict_result = _parse_dict(conflict)

    assert duplicate_result.configuration is None
    assert conflict_result.configuration is None
    assert any("PACKAGE_PIN_DUPLICATE" in issue.message for issue in duplicate_result.issues)
    assert any("PACKAGE_PIN_VERSION_CONFLICT" in issue.message for issue in conflict_result.issues)


def test_parser_rejects_a_manually_inconsistent_package_set_plan() -> None:
    plan = _valid_plan()
    invalid_plan = replace(plan, entries=tuple(reversed(plan.entries)))

    result = parse_class_world_manifest(
        serialize_class_world_manifest(_configuration(plan)),
        invalid_plan,
    )

    assert result.configuration is None
    assert ClassWorldManifestIssueCode.CONFIGURATION_INVALID in _codes(result)
    assert any("PACKAGE_SET_STRUCTURE_INVALID" in issue.message for issue in result.issues)


def test_serializer_rejects_wrong_or_manually_inconsistent_configuration() -> None:
    with pytest.raises(TypeError, match="ClassWorldConfiguration"):
        serialize_class_world_manifest(object())  # type: ignore[arg-type]

    invalid_metadata = replace(_configuration(), class_world_id="Bad World")
    with pytest.raises(ValueError, match="CLASS_WORLD_ID_INVALID"):
        serialize_class_world_manifest(invalid_metadata)

    configuration = _configuration()
    invalid_plan = replace(configuration.package_set_plan, entries=())
    with pytest.raises(ValueError, match="PACKAGE_SET_STRUCTURE_INVALID"):
        serialize_class_world_manifest(replace(configuration, package_set_plan=invalid_plan))


def test_invalid_results_are_atomic_deterministic_and_deeply_immutable() -> None:
    manifest = _manifest_dict()
    manifest["class_world"]["id"] = "Bad World"
    text = json.dumps(manifest)

    first = parse_class_world_manifest(text, _valid_plan())
    second = parse_class_world_manifest(text, _valid_plan())

    assert first == second
    assert first.configuration is None
    assert isinstance(first.issues, tuple)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        first.configuration = _configuration()  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        first.issues[0].location = "changed"  # type: ignore[misc]


def test_manifest_apis_perform_no_forbidden_activity(monkeypatch: pytest.MonkeyPatch) -> None:
    configuration = _configuration()

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("class-world manifest crossed a forbidden boundary")

    monkeypatch.setattr(Path, "read_text", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    monkeypatch.setattr(Path, "open", fail)
    monkeypatch.setattr(yaml, "safe_load", fail)
    monkeypatch.setattr(importlib, "import_module", fail)
    monkeypatch.setattr(socket, "socket", fail)
    monkeypatch.setattr(hashlib, "sha256", fail)

    from explore.packages import (
        loader,
        package_set_application,
        package_set_planner,
        registration_adapter,
        registration_application,
        validator,
    )

    monkeypatch.setattr(loader, "load_explorer_package", fail)
    monkeypatch.setattr(validator, "validate_explorer_package", fail)
    monkeypatch.setattr(registration_adapter, "build_student_api_registration_plan", fail)
    monkeypatch.setattr(package_set_planner, "build_package_set_plan", fail)
    monkeypatch.setattr(registration_application, "apply_student_api_registration_plan", fail)
    monkeypatch.setattr(package_set_application, "apply_package_set_plan", fail)

    import pygame

    monkeypatch.setattr(pygame, "init", fail)
    monkeypatch.setattr(pygame.display, "set_mode", fail)

    text = serialize_class_world_manifest(configuration)
    result = parse_class_world_manifest(text, configuration.package_set_plan)

    assert result.configuration == configuration


def test_public_exports_preserve_the_complete_earlier_pipeline() -> None:
    import explore.packages as packages

    expected = {
        "serialize_class_world_manifest",
        "parse_class_world_manifest",
        "ClassWorldManifestParseResult",
        "ClassWorldManifestIssue",
        "ClassWorldManifestIssueCode",
        "SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION",
        "build_class_world_configuration",
        "build_package_set_plan",
        "apply_package_set_plan",
        "apply_student_api_registration_plan",
        "build_student_api_registration_plan",
        "load_explorer_package",
        "validate_explorer_package",
    }

    assert SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION == "0.1"
    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)


def test_manifest_source_has_only_the_permitted_serialization_boundary() -> None:
    from explore.packages import class_world_manifest

    source = Path(class_world_manifest.__file__).read_text(encoding="utf-8")
    forbidden = (
        "import yaml",
        "import hashlib",
        "from engine",
        "import engine",
        "import pygame",
        "load_explorer_package",
        "validate_explorer_package",
        "build_student_api_registration_plan",
        "build_package_set_plan",
        "apply_student_api_registration_plan",
        "apply_package_set_plan",
        "StudentAPIWorldRegistrationTarget",
        "from explore import Character",
        "from explore import Object",
        "from explore import World",
        "open(",
        "eval(",
        "exec(",
        "hashlib",
        "signature",
        "yaml",
    )

    assert all(term not in source for term in forbidden)
