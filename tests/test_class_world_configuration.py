"""Behavior-focused tests for immutable class-world configuration v0.1."""

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
    CLASS_WORLD_DISPLAY_NAME_MAX_LENGTH,
    COHORT_DISPLAY_NAME_MAX_LENGTH,
    SUPPORTED_CLASS_WORLD_CONFIGURATION_SCHEMA_VERSION,
    CharacterCounterResponseRegistrationSpec,
    CharacterEitherToggleResponseRegistrationSpec,
    CharacterRegistration,
    CharacterRegistrationSpec,
    CharacterToggleResponseRegistrationSpec,
    CharacterTwoToggleResponseRegistrationSpec,
    ClassWorldCohort,
    ClassWorldConfigurationIssueCode,
    ClassWorldConfigurationResult,
    ClassWorldConfigurationSpec,
    ClassWorldPackagePin,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    WorldObjectCounterRegistrationSpec,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    WorldObjectToggleRegistrationSpec,
    build_class_world_configuration,
)


def _provenance(
    package_id: str,
    *,
    package_version: str = "1.0.0",
    student_api_version: str = "0.1",
) -> PackageProvenance:
    return PackageProvenance(package_id, package_version, student_api_version)


def _character(
    package_id: str,
    *,
    contribution_id: str = "hero",
    provenance: PackageProvenance | None = None,
    **overrides: Any,
) -> CharacterRegistration:
    values: dict[str, Any] = {
        "qualified_id": f"{package_id}:{contribution_id}",
        "contribution_id": contribution_id,
        "provenance": provenance or _provenance(package_id),
        "character": CharacterRegistrationSpec("Explorer", 10, 20, "gold"),
        "asset_reference": None,
    }
    values.update(overrides)
    return CharacterRegistration(**values)


def _world_object(
    package_id: str,
    *,
    contribution_id: str = "landmark",
    provenance: PackageProvenance | None = None,
    **overrides: Any,
) -> WorldObjectRegistration:
    values: dict[str, Any] = {
        "qualified_id": f"{package_id}:{contribution_id}",
        "contribution_id": contribution_id,
        "provenance": provenance or _provenance(package_id),
        "world_object": WorldObjectRegistrationSpec(
            "Landmark",
            30,
            40,
            "green",
            "Look closer.",
            "You found it!",
        ),
        "asset_reference": None,
    }
    values.update(overrides)
    return WorldObjectRegistration(**values)


def _selected(
    package_id: str,
    *entries: object,
    package_version: str = "1.0.0",
    student_api_version: str = "0.1",
) -> SelectedPackagePlan:
    provenance = _provenance(
        package_id,
        package_version=package_version,
        student_api_version=student_api_version,
    )
    adjusted = tuple(
        (
            replace(entry, provenance=provenance)
            if isinstance(entry, (CharacterRegistration, WorldObjectRegistration))
            else entry
        )
        for entry in entries
    )
    registration_plan = StudentAPIRegistrationPlan(
        provenance=provenance,
        entries=adjusted,  # type: ignore[arg-type]
    )
    return SelectedPackagePlan(
        package_id=package_id,
        package_version=package_version,
        provenance=provenance,
        registration_plan=registration_plan,
    )


def _plan(
    *packages: SelectedPackagePlan,
    student_api_version: str = "0.1",
) -> PackageSetPlan:
    return PackageSetPlan(
        student_api_version=student_api_version,
        packages=packages,
        entries=tuple(entry for package in packages for entry in package.registration_plan.entries),
    )


def _spec(
    plan: PackageSetPlan,
    **overrides: Any,
) -> ClassWorldConfigurationSpec:
    values: dict[str, Any] = {
        "schema_version": "0.1",
        "class_world_id": "expedition-orion-fall-2026",
        "display_name": "Explorer World — Fall 2026",
        "class_world_version": "1.2.3-beta.1+class",
        "engine_version": "0.1.0",
        "student_api_version": "0.1",
        "cohort": ClassWorldCohort("expedition-orion", "Expedition Orion"),
        "packages": tuple(
            ClassWorldPackagePin(package.package_id, package.package_version)
            for package in plan.packages
        ),
    }
    values.update(overrides)
    return ClassWorldConfigurationSpec(**values)


def _valid_mixed_plan() -> PackageSetPlan:
    return _plan(
        _selected("nova-character", _character("nova-character")),
        _selected("crystal-lantern", _world_object("crystal-lantern")),
    )


def _codes(result: ClassWorldConfigurationResult) -> list[ClassWorldConfigurationIssueCode]:
    return [issue.code for issue in result.issues]


@pytest.mark.parametrize(
    "plan",
    [
        _plan(_selected("nova-character", _character("nova-character"))),
        _plan(_selected("crystal-lantern", _world_object("crystal-lantern"))),
        _valid_mixed_plan(),
    ],
)
def test_valid_configuration_succeeds_for_supported_package_compositions(
    plan: PackageSetPlan,
) -> None:
    spec = _spec(plan)

    result = build_class_world_configuration(spec, plan)

    assert result.is_configured
    assert result.issues == ()
    assert result.configuration is not None
    assert result.configuration.package_set_plan is plan
    assert result.configuration.packages == spec.packages


def test_configuration_preserves_metadata_versions_identity_and_order_exactly() -> None:
    plan = _valid_mixed_plan()
    spec = _spec(plan)

    result = build_class_world_configuration(spec, plan)

    assert result.configuration is not None
    configuration = result.configuration
    assert configuration.schema_version == SUPPORTED_CLASS_WORLD_CONFIGURATION_SCHEMA_VERSION
    assert configuration.class_world_id == spec.class_world_id
    assert configuration.display_name == spec.display_name
    assert configuration.class_world_version == spec.class_world_version
    assert configuration.engine_version == spec.engine_version
    assert configuration.student_api_version == spec.student_api_version
    assert configuration.cohort is spec.cohort
    assert configuration.identity == (spec.class_world_id, spec.class_world_version)
    assert [pin.package_id for pin in configuration.packages] == [
        "nova-character",
        "crystal-lantern",
    ]
    assert configuration.package_set_plan.entries == plan.entries
    assert not hasattr(configuration, "uuid")
    assert not hasattr(configuration, "timestamp")
    assert not hasattr(configuration, "hash")


def test_equivalent_construction_is_equal_and_reversed_matching_order_is_distinct() -> None:
    plan = _valid_mixed_plan()
    first = build_class_world_configuration(_spec(plan), plan)
    second = build_class_world_configuration(_spec(plan), plan)
    reversed_plan = replace(
        plan,
        packages=tuple(reversed(plan.packages)),
        entries=tuple(reversed(plan.entries)),
    )
    reversed_result = build_class_world_configuration(_spec(reversed_plan), reversed_plan)

    assert first == second
    assert reversed_result.is_configured
    assert first != reversed_result


@pytest.mark.parametrize("spec", [None, object(), "configuration"])
def test_missing_or_wrong_specification_type_is_structured(spec: object) -> None:
    result = build_class_world_configuration(spec, _valid_mixed_plan())  # type: ignore[arg-type]

    assert result.configuration is None
    assert _codes(result) == [ClassWorldConfigurationIssueCode.CONFIGURATION_SPEC_REQUIRED]


@pytest.mark.parametrize("plan", [None, object(), "plan"])
def test_missing_or_wrong_package_set_plan_type_is_structured(plan: object) -> None:
    valid_plan = _valid_mixed_plan()
    result = build_class_world_configuration(_spec(valid_plan), plan)  # type: ignore[arg-type]

    assert result.configuration is None
    assert _codes(result) == [ClassWorldConfigurationIssueCode.PACKAGE_SET_PLAN_REQUIRED]


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("schema_version", "0.2", ClassWorldConfigurationIssueCode.SCHEMA_VERSION_UNSUPPORTED),
        ("class_world_id", "Bad World", ClassWorldConfigurationIssueCode.CLASS_WORLD_ID_INVALID),
        (
            "display_name",
            " ",
            ClassWorldConfigurationIssueCode.CLASS_WORLD_DISPLAY_NAME_INVALID,
        ),
        (
            "display_name",
            "x" * (CLASS_WORLD_DISPLAY_NAME_MAX_LENGTH + 1),
            ClassWorldConfigurationIssueCode.CLASS_WORLD_DISPLAY_NAME_INVALID,
        ),
        (
            "class_world_version",
            "1.0",
            ClassWorldConfigurationIssueCode.CLASS_WORLD_VERSION_INVALID,
        ),
        ("engine_version", "latest", ClassWorldConfigurationIssueCode.ENGINE_VERSION_INVALID),
        (
            "student_api_version",
            "0.2",
            ClassWorldConfigurationIssueCode.STUDENT_API_VERSION_UNSUPPORTED,
        ),
    ],
)
def test_world_metadata_is_validated_in_documented_order(
    field: str,
    value: object,
    expected: ClassWorldConfigurationIssueCode,
) -> None:
    plan = _valid_mixed_plan()

    result = build_class_world_configuration(_spec(plan, **{field: value}), plan)

    assert result.configuration is None
    assert expected in _codes(result)


def test_display_names_are_preserved_without_identifier_normalization() -> None:
    plan = _valid_mixed_plan()
    display_name = "  Expedition Orion — Saturday Explorers  "
    cohort = ClassWorldCohort("fall-2026", "  Fall 2026 Saturday Explorers  ")

    result = build_class_world_configuration(
        _spec(plan, display_name=display_name, cohort=cohort),
        plan,
    )

    assert result.configuration is not None
    assert result.configuration.display_name == display_name
    assert result.configuration.cohort.display_name == cohort.display_name


@pytest.mark.parametrize(
    ("cohort", "expected"),
    [
        (object(), ClassWorldConfigurationIssueCode.COHORT_INVALID),
        (
            ClassWorldCohort("Bad_Cohort", "Expedition Orion"),
            ClassWorldConfigurationIssueCode.COHORT_ID_INVALID,
        ),
        (
            ClassWorldCohort("expedition-orion", " "),
            ClassWorldConfigurationIssueCode.COHORT_DISPLAY_NAME_INVALID,
        ),
        (
            ClassWorldCohort(
                "expedition-orion",
                "x" * (COHORT_DISPLAY_NAME_MAX_LENGTH + 1),
            ),
            ClassWorldConfigurationIssueCode.COHORT_DISPLAY_NAME_INVALID,
        ),
    ],
)
def test_cohort_metadata_is_minimal_and_validated(
    cohort: object,
    expected: ClassWorldConfigurationIssueCode,
) -> None:
    plan = _valid_mixed_plan()

    result = build_class_world_configuration(_spec(plan, cohort=cohort), plan)

    assert result.configuration is None
    assert expected in _codes(result)


@pytest.mark.parametrize(
    ("packages", "expected"),
    [
        ((), ClassWorldConfigurationIssueCode.PACKAGE_SET_REQUIRED),
        ((object(),), ClassWorldConfigurationIssueCode.PACKAGE_PIN_INVALID_TYPE),
        (
            (ClassWorldPackagePin("Bad Package", "1.0.0"),),
            ClassWorldConfigurationIssueCode.PACKAGE_PIN_ID_INVALID,
        ),
        (
            (ClassWorldPackagePin("nova-character", "1.0"),),
            ClassWorldConfigurationIssueCode.PACKAGE_PIN_VERSION_INVALID,
        ),
        (
            (
                ClassWorldPackagePin("nova-character", "1.0.0"),
                ClassWorldPackagePin("nova-character", "1.0.0"),
            ),
            ClassWorldConfigurationIssueCode.PACKAGE_PIN_DUPLICATE,
        ),
        (
            (
                ClassWorldPackagePin("nova-character", "1.0.0"),
                ClassWorldPackagePin("nova-character", "2.0.0"),
            ),
            ClassWorldConfigurationIssueCode.PACKAGE_PIN_VERSION_CONFLICT,
        ),
    ],
)
def test_package_pin_values_and_duplicates_are_defensively_rejected(
    packages: tuple[object, ...],
    expected: ClassWorldConfigurationIssueCode,
) -> None:
    plan = _valid_mixed_plan()

    result = build_class_world_configuration(_spec(plan, packages=packages), plan)

    assert result.configuration is None
    assert expected in _codes(result)


def test_package_pin_count_order_id_and_version_must_match_exactly() -> None:
    plan = _valid_mixed_plan()
    pins = _spec(plan).packages

    missing = build_class_world_configuration(_spec(plan, packages=pins[:-1]), plan)
    extra = build_class_world_configuration(
        _spec(plan, packages=(*pins, ClassWorldPackagePin("extra-package", "1.0.0"))),
        plan,
    )
    reordered = build_class_world_configuration(
        _spec(plan, packages=tuple(reversed(pins))),
        plan,
    )
    wrong_id = build_class_world_configuration(
        _spec(plan, packages=(ClassWorldPackagePin("other-package", "1.0.0"), pins[1])),
        plan,
    )
    wrong_version = build_class_world_configuration(
        _spec(plan, packages=(replace(pins[0], package_version="2.0.0"), pins[1])),
        plan,
    )

    assert ClassWorldConfigurationIssueCode.PACKAGE_COUNT_MISMATCH in _codes(missing)
    assert ClassWorldConfigurationIssueCode.PACKAGE_COUNT_MISMATCH in _codes(extra)
    assert _codes(reordered).count(ClassWorldConfigurationIssueCode.PACKAGE_ORDER_MISMATCH) == 2
    assert ClassWorldConfigurationIssueCode.PACKAGE_ID_MISMATCH in _codes(wrong_id)
    assert ClassWorldConfigurationIssueCode.PACKAGE_VERSION_MISMATCH in _codes(wrong_version)
    assert all(result.configuration is None for result in (missing, extra, reordered, wrong_id))


def test_unsupported_plan_and_all_provenance_versions_are_rejected() -> None:
    unsupported_package = _selected(
        "nova-character",
        _character("nova-character"),
        student_api_version="0.2",
    )
    plan = _plan(unsupported_package, student_api_version="0.2")

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.configuration is None
    assert (
        _codes(result).count(ClassWorldConfigurationIssueCode.STUDENT_API_VERSION_UNSUPPORTED) >= 3
    )


def test_selected_and_nested_registration_provenance_are_checked_independently() -> None:
    plan = _valid_mixed_plan()
    first = plan.packages[0]
    selected_mismatch = replace(first, provenance=_provenance("other-package"))
    selected_result = build_class_world_configuration(
        _spec(replace(plan, packages=(selected_mismatch, plan.packages[1]))),
        replace(plan, packages=(selected_mismatch, plan.packages[1])),
    )

    nested_plan = replace(first.registration_plan, provenance=_provenance("other-package"))
    nested_mismatch = replace(first, registration_plan=nested_plan)
    nested_set = replace(plan, packages=(nested_mismatch, plan.packages[1]))
    nested_result = build_class_world_configuration(_spec(nested_set), nested_set)

    assert ClassWorldConfigurationIssueCode.PACKAGE_PROVENANCE_MISMATCH in _codes(selected_result)
    assert ClassWorldConfigurationIssueCode.PACKAGE_PROVENANCE_MISMATCH in _codes(nested_result)
    assert selected_result.configuration is None
    assert nested_result.configuration is None


@pytest.mark.parametrize("mutation", ["omit", "extra", "reverse"])
def test_flattened_entries_must_exactly_match_nested_entries(mutation: str) -> None:
    plan = _valid_mixed_plan()
    if mutation == "omit":
        entries = plan.entries[:-1]
    elif mutation == "extra":
        entries = (*plan.entries, plan.entries[-1])
    else:
        entries = tuple(reversed(plan.entries))
    invalid = replace(plan, entries=entries)

    result = build_class_world_configuration(_spec(invalid), invalid)

    assert result.configuration is None
    assert ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID in _codes(result)


def test_qualified_identity_duplicate_package_id_and_cardinality_are_revalidated() -> None:
    base = _valid_mixed_plan()
    first = base.packages[0]
    duplicate_identity_entry = replace(
        base.packages[1].registration_plan.entries[0],
        qualified_id=first.registration_plan.entries[0].qualified_id,
        contribution_id=first.registration_plan.entries[0].contribution_id,
    )
    second_registration = replace(
        base.packages[1].registration_plan,
        entries=(duplicate_identity_entry,),
    )
    duplicate_identity_package = replace(
        base.packages[1],
        registration_plan=second_registration,
    )
    identity_plan = _plan(first, duplicate_identity_package)

    duplicate_package_plan = _plan(first, first)
    second_character = _selected("second-character", _character("second-character"))
    cardinality_plan = _plan(first, second_character)

    for invalid in (identity_plan, duplicate_package_plan, cardinality_plan):
        result = build_class_world_configuration(_spec(invalid), invalid)
        assert result.configuration is None
        assert ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID in _codes(result)


def test_mutable_or_invalid_nested_registration_values_cannot_enter_configuration() -> None:
    entry = _character(
        "nova-character",
        character=["mutable"],  # type: ignore[arg-type]
    )
    package = _selected("nova-character", entry)
    plan = _plan(package)

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.configuration is None
    assert ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID in _codes(result)


def test_invalid_character_greeting_cannot_enter_configuration() -> None:
    entry = _character(
        "nova-character",
        character=CharacterRegistrationSpec(name="Nova", x=1, y=2, color="gold", greeting=" "),
    )
    package = _selected("nova-character", entry)
    plan = _plan(package)

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.configuration is None
    assert ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID in _codes(result)


def test_invalid_character_conversation_cannot_enter_configuration() -> None:
    entry = _character(
        "nova-character",
        character=CharacterRegistrationSpec(
            name="Nova",
            x=1,
            y=2,
            color="gold",
            conversation=("Only one",),
        ),
    )
    package = _selected("nova-character", entry)
    plan = _plan(package)

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.configuration is None
    assert ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID in _codes(result)


def test_valid_toggle_metadata_is_retained_by_class_world_configuration() -> None:
    toggle = WorldObjectToggleRegistrationSpec(off_color="red", on_color="green")
    entry = _world_object(
        "switch-package",
        world_object=WorldObjectRegistrationSpec(
            name="Switch",
            x=1,
            y=2,
            color="red",
            toggle=toggle,
        ),
    )
    package = _selected("switch-package", entry)
    plan = _plan(package)

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.configuration is not None
    configured = result.configuration.package_set_plan.entries[0]
    assert isinstance(configured, WorldObjectRegistration)
    assert configured.world_object.toggle is toggle


def test_invalid_toggle_metadata_cannot_enter_class_world_configuration() -> None:
    entry = _world_object(
        "switch-package",
        world_object=WorldObjectRegistrationSpec(
            name="Switch",
            x=1,
            y=2,
            color="blue",
            toggle=WorldObjectToggleRegistrationSpec(off_color="red", on_color="green"),
        ),
    )
    package = _selected("switch-package", entry)
    plan = _plan(package)

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.configuration is None
    assert ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID in _codes(result)


def test_valid_counter_metadata_is_retained_by_class_world_configuration() -> None:
    counter = WorldObjectCounterRegistrationSpec(3, "Fully powered!")
    entry = _world_object(
        "power-package",
        world_object=WorldObjectRegistrationSpec(
            name="Core",
            x=1,
            y=2,
            color="blue",
            counter=counter,
        ),
    )
    package = _selected("power-package", entry)
    plan = _plan(package)

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.configuration is not None
    configured = result.configuration.package_set_plan.entries[0]
    assert isinstance(configured, WorldObjectRegistration)
    assert configured.world_object.counter is counter


def test_invalid_counter_metadata_cannot_enter_class_world_configuration() -> None:
    entry = _world_object(
        "power-package",
        world_object=WorldObjectRegistrationSpec(
            name="Core",
            x=1,
            y=2,
            color="blue",
            counter=WorldObjectCounterRegistrationSpec(True, "Ready"),
        ),
    )
    package = _selected("power-package", entry)
    plan = _plan(package)

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.configuration is None
    assert ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID in _codes(result)


def test_valid_conditional_metadata_is_retained_by_class_world_configuration() -> None:
    conditional = CharacterToggleResponseRegistrationSpec("switch", "Off", "On")
    character = _character(
        "magic-package",
        contribution_id="guide",
        character=CharacterRegistrationSpec("Guide", 1, 2, "gold", respond_to_toggle=conditional),
    )
    world_object = _world_object(
        "magic-package",
        contribution_id="switch",
        world_object=WorldObjectRegistrationSpec(
            "Switch",
            30,
            40,
            "red",
            toggle=WorldObjectToggleRegistrationSpec("red", "green"),
        ),
    )
    package = _selected("magic-package", character, world_object)
    plan = _plan(package)

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.configuration is not None
    configured = result.configuration.package_set_plan.entries[0]
    assert isinstance(configured, CharacterRegistration)
    assert configured.character.respond_to_toggle is conditional


def test_invalid_conditional_reference_cannot_enter_class_world_configuration() -> None:
    character = _character(
        "magic-package",
        contribution_id="guide",
        character=CharacterRegistrationSpec(
            "Guide",
            1,
            2,
            "gold",
            respond_to_toggle=CharacterToggleResponseRegistrationSpec("missing", "Off", "On"),
        ),
    )
    package = _selected("magic-package", character)
    plan = _plan(package)

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.configuration is None
    assert ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID in _codes(result)


def test_invalid_two_toggle_reference_cannot_enter_class_world_configuration() -> None:
    character = _character(
        "magic-package",
        contribution_id="guide",
        character=CharacterRegistrationSpec(
            "Guide",
            1,
            2,
            "gold",
            respond_to_two_toggles=CharacterTwoToggleResponseRegistrationSpec(
                ("first", "missing"), "Locked", "Unlocked"
            ),
        ),
    )
    package = _selected("magic-package", character)
    plan = _plan(package)

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.configuration is None
    assert ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID in _codes(result)


def test_either_toggle_metadata_is_validated_without_changing_v01_cardinality() -> None:
    conditional = CharacterEitherToggleResponseRegistrationSpec(
        ("first", "second"), "Locked", "Open"
    )
    character = _character(
        "magic-package",
        contribution_id="guide",
        character=CharacterRegistrationSpec(
            "Guide", 1, 2, "gold", respond_to_either_toggle=conditional
        ),
    )
    first = _world_object(
        "magic-package",
        contribution_id="first",
        world_object=WorldObjectRegistrationSpec(
            "First", 10, 20, "red", toggle=WorldObjectToggleRegistrationSpec("red", "green")
        ),
    )
    second = _world_object(
        "magic-package",
        contribution_id="second",
        world_object=WorldObjectRegistrationSpec(
            "Second", 30, 40, "blue", toggle=WorldObjectToggleRegistrationSpec("blue", "yellow")
        ),
    )
    plan = _plan(_selected("magic-package", character, first, second))

    result = build_class_world_configuration(_spec(plan), plan)
    assert result.configuration is None
    assert len(result.issues) == 1
    assert "at most one world object" in result.issues[0].message

    invalid_character = replace(
        character,
        character=replace(
            character.character,
            respond_to_either_toggle=CharacterEitherToggleResponseRegistrationSpec(
                ("first", "missing"), "Locked", "Open"
            ),
        ),
    )
    invalid_plan = _plan(_selected("magic-package", invalid_character, first, second))
    invalid = build_class_world_configuration(_spec(invalid_plan), invalid_plan)
    assert invalid.configuration is None
    assert ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID in _codes(invalid)


def test_counter_comparison_metadata_is_retained_and_reference_validated() -> None:
    response = CharacterCounterResponseRegistrationSpec("core", "More", "Ready")
    character = _character(
        "power-package",
        contribution_id="guide",
        character=CharacterRegistrationSpec("Guide", 1, 2, "gold", respond_to_counter=response),
    )
    counter = _world_object(
        "power-package",
        contribution_id="core",
        world_object=WorldObjectRegistrationSpec(
            "Core", 10, 20, "red", counter=WorldObjectCounterRegistrationSpec(2, "Done")
        ),
    )
    plan = _plan(_selected("power-package", character, counter))

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.configuration is not None
    retained = result.configuration.package_set_plan.entries[0]
    assert isinstance(retained, CharacterRegistration)
    assert retained.character.respond_to_counter is response

    invalid_character = replace(
        character,
        character=replace(
            character.character,
            respond_to_counter=CharacterCounterResponseRegistrationSpec("missing", "More", "Ready"),
        ),
    )
    invalid_plan = _plan(_selected("power-package", invalid_character, counter))
    invalid = build_class_world_configuration(_spec(invalid_plan), invalid_plan)
    assert invalid.configuration is None
    assert ClassWorldConfigurationIssueCode.PACKAGE_SET_STRUCTURE_INVALID in _codes(invalid)


def test_valid_early_metadata_and_invalid_late_pin_returns_no_partial_configuration() -> None:
    plan = _valid_mixed_plan()
    invalid_pins = (*_spec(plan).packages[:-1], ClassWorldPackagePin("crystal-lantern", "bad"))

    result = build_class_world_configuration(_spec(plan, packages=invalid_pins), plan)

    assert result.configuration is None
    assert result.issues
    assert not hasattr(result, "packages")


def test_multiple_independent_issues_accumulate_in_stable_documented_order() -> None:
    plan = _valid_mixed_plan()
    spec = _spec(
        plan,
        schema_version="9.0",
        class_world_id="Bad ID",
        display_name=" ",
        cohort=ClassWorldCohort("Bad_Cohort", " "),
        packages=(ClassWorldPackagePin("Bad Pin", "bad"),),
    )

    first = build_class_world_configuration(spec, plan)
    second = build_class_world_configuration(spec, plan)

    assert first == second
    assert first.configuration is None
    assert _codes(first)[:5] == [
        ClassWorldConfigurationIssueCode.SCHEMA_VERSION_UNSUPPORTED,
        ClassWorldConfigurationIssueCode.CLASS_WORLD_ID_INVALID,
        ClassWorldConfigurationIssueCode.CLASS_WORLD_DISPLAY_NAME_INVALID,
        ClassWorldConfigurationIssueCode.COHORT_ID_INVALID,
        ClassWorldConfigurationIssueCode.COHORT_DISPLAY_NAME_INVALID,
    ]
    assert all("/Users/" not in issue.message for issue in first.issues)
    assert all("0x" not in issue.message for issue in first.issues)


def test_public_models_and_canonical_nested_state_are_deeply_immutable() -> None:
    plan = _valid_mixed_plan()
    spec = _spec(plan)
    result = build_class_world_configuration(spec, plan)
    assert result.configuration is not None

    assert isinstance(spec.packages, tuple)
    assert isinstance(result.issues, tuple)
    assert isinstance(result.configuration.packages, tuple)
    assert isinstance(result.configuration.package_set_plan.packages, tuple)
    assert isinstance(result.configuration.package_set_plan.entries, tuple)
    for value, field, replacement in (
        (spec.cohort, "cohort_id", "changed"),
        (spec.packages[0], "package_id", "changed"),
        (spec, "class_world_id", "changed"),
        (result.configuration, "class_world_id", "changed"),
        (result, "issues", ()),
    ):
        with pytest.raises((FrozenInstanceError, AttributeError)):
            setattr(value, field, replacement)

    failure = build_class_world_configuration(None, plan)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        failure.issues[0].location = "changed"  # type: ignore[misc]


def test_builder_performs_no_forbidden_activity(monkeypatch: pytest.MonkeyPatch) -> None:
    plan = _valid_mixed_plan()

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("class-world configuration crossed a forbidden boundary")

    monkeypatch.setattr(Path, "read_text", fail)
    monkeypatch.setattr(Path, "open", fail)
    monkeypatch.setattr(yaml, "safe_load", fail)
    monkeypatch.setattr(json, "loads", fail)
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

    result = build_class_world_configuration(_spec(plan), plan)

    assert result.is_configured


def test_public_exports_preserve_pipeline_and_add_configuration_surface() -> None:
    import explore.packages as packages

    expected = {
        "build_class_world_configuration",
        "ClassWorldConfigurationSpec",
        "ClassWorldConfiguration",
        "ClassWorldConfigurationResult",
        "ClassWorldConfigurationIssue",
        "ClassWorldConfigurationIssueCode",
        "ClassWorldPackagePin",
        "ClassWorldCohort",
        "build_package_set_plan",
        "apply_package_set_plan",
        "apply_student_api_registration_plan",
        "build_student_api_registration_plan",
        "load_explorer_package",
        "validate_explorer_package",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)


def test_configuration_source_has_no_forbidden_dependencies_or_side_effect_calls() -> None:
    from explore.packages import class_world_configuration

    source = Path(class_world_configuration.__file__).read_text(encoding="utf-8")
    forbidden = (
        "import yaml",
        "import json",
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
        "World(",
        "Character(",
        "Object(",
        "open(",
        "eval(",
        "exec(",
        "uuid",
        "timestamp",
        "signature",
    )

    assert all(term not in source for term in forbidden)
