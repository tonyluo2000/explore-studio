"""Behavior-focused tests for Package-Set Preflight v0.1."""

from __future__ import annotations

import importlib
import socket
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from explore.packages import (
    CharacterRegistration,
    CharacterRegistrationSpec,
    CharacterToggleResponseRegistrationSpec,
    PackageAssetReference,
    PackageProvenance,
    PackageSelection,
    PackageSetIssueCode,
    PackageSetPlanResult,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    WorldObjectToggleRegistrationSpec,
    build_package_set_plan,
)


def _provenance(
    package_id: str,
    *,
    package_version: str = "1.0.0",
    student_api_version: str = "0.1",
) -> PackageProvenance:
    return PackageProvenance(
        package_id=package_id,
        package_version=package_version,
        student_api_version=student_api_version,
    )


def _character(
    package_id: str,
    *,
    contribution_id: str = "hero",
    provenance: PackageProvenance | None = None,
    **overrides: Any,
) -> CharacterRegistration:
    entry_provenance = provenance or _provenance(package_id)
    values: dict[str, Any] = {
        "qualified_id": f"{package_id}:{contribution_id}",
        "contribution_id": contribution_id,
        "provenance": entry_provenance,
        "character": CharacterRegistrationSpec(
            name="Explorer",
            x=10,
            y=20,
            color="gold",
        ),
        "asset_reference": None,
    }
    values.update(overrides)
    return CharacterRegistration(**values)


def _world_object(
    package_id: str,
    *,
    contribution_id: str = "object",
    provenance: PackageProvenance | None = None,
    **overrides: Any,
) -> WorldObjectRegistration:
    entry_provenance = provenance or _provenance(package_id)
    values: dict[str, Any] = {
        "qualified_id": f"{package_id}:{contribution_id}",
        "contribution_id": contribution_id,
        "provenance": entry_provenance,
        "world_object": WorldObjectRegistrationSpec(
            name="Landmark",
            x=30,
            y=40,
            color="green",
            when_near="Look closer.",
            when_interacted="You found it!",
        ),
        "asset_reference": None,
    }
    values.update(overrides)
    return WorldObjectRegistration(**values)


def _plan(
    package_id: str,
    *entries: object,
    package_version: str = "1.0.0",
    student_api_version: str = "0.1",
    provenance: PackageProvenance | None = None,
) -> StudentAPIRegistrationPlan:
    plan_provenance = provenance or _provenance(
        package_id,
        package_version=package_version,
        student_api_version=student_api_version,
    )
    return StudentAPIRegistrationPlan(
        provenance=plan_provenance,
        entries=entries,  # type: ignore[arg-type]
    )


def _selection(
    package_id: str,
    *entries: object,
    package_version: str = "1.0.0",
    student_api_version: str = "0.1",
) -> PackageSelection:
    provenance = _provenance(
        package_id,
        package_version=package_version,
        student_api_version=student_api_version,
    )
    adjusted_entries = tuple(
        (
            replace(entry, provenance=provenance)
            if isinstance(entry, (CharacterRegistration, WorldObjectRegistration))
            else entry
        )
        for entry in entries
    )
    return PackageSelection(
        package_id=package_id,
        package_version=package_version,
        registration_plan=_plan(
            package_id,
            *adjusted_entries,
            package_version=package_version,
            student_api_version=student_api_version,
            provenance=provenance,
        ),
    )


def _codes(result: PackageSetPlanResult) -> list[PackageSetIssueCode]:
    return [issue.code for issue in result.issues]


@pytest.mark.parametrize(
    "selection",
    [
        _selection("nova-character", _character("nova-character")),
        _selection("crystal-lantern", _world_object("crystal-lantern")),
    ],
)
def test_single_valid_package_selection_succeeds(selection: PackageSelection) -> None:
    result = build_package_set_plan((selection,))

    assert result.is_planned
    assert result.issues == ()
    assert result.plan is not None
    assert result.plan.student_api_version == "0.1"
    assert result.plan.packages[0].registration_plan is selection.registration_plan
    assert result.plan.entries == selection.registration_plan.entries


def test_mixed_package_set_preserves_package_and_flattened_entry_order() -> None:
    object_selection = _selection(
        "forest-guide",
        _world_object("forest-guide", contribution_id="sign"),
    )
    character_selection = _selection(
        "nova-character",
        _character("nova-character", contribution_id="nova"),
    )

    result = build_package_set_plan([object_selection, character_selection])

    assert result.plan is not None
    assert [package.package_id for package in result.plan.packages] == [
        "forest-guide",
        "nova-character",
    ]
    assert [entry.qualified_id for entry in result.plan.entries] == [
        "forest-guide:sign",
        "nova-character:nova",
    ]
    assert result.plan.packages[0].provenance == object_selection.registration_plan.provenance


def test_entry_order_within_one_registration_plan_is_preserved() -> None:
    selection = _selection(
        "river-rescue",
        _world_object("river-rescue", contribution_id="sign"),
        _character("river-rescue", contribution_id="guide"),
    )

    result = build_package_set_plan((selection,))

    assert result.plan is not None
    assert [entry.qualified_id for entry in result.plan.entries] == [
        "river-rescue:sign",
        "river-rescue:guide",
    ]


def test_ordered_generator_input_is_consumed_once_and_preserved() -> None:
    ordered = (
        _selection("forest-guide", _world_object("forest-guide")),
        _selection("nova-character", _character("nova-character")),
    )

    result = build_package_set_plan(selection for selection in ordered)

    assert result.plan is not None
    assert tuple(package.package_id for package in result.plan.packages) == (
        "forest-guide",
        "nova-character",
    )


def test_same_local_id_across_packages_is_valid_when_qualified_ids_differ() -> None:
    result = build_package_set_plan(
        (
            _selection("nova-character", _character("nova-character", contribution_id="hero")),
            _selection("forest-guide", _world_object("forest-guide", contribution_id="hero")),
        )
    )

    assert result.is_planned
    assert result.plan is not None
    assert [entry.contribution_id for entry in result.plan.entries] == ["hero", "hero"]
    assert [entry.qualified_id for entry in result.plan.entries] == [
        "nova-character:hero",
        "forest-guide:hero",
    ]


def test_exact_package_and_version_pins_and_provenance_are_preserved() -> None:
    selection = _selection(
        "nova-character",
        _character("nova-character"),
        package_version="1.2.3-beta.1+class",
    )

    result = build_package_set_plan((selection,))

    assert result.plan is not None
    selected = result.plan.packages[0]
    assert (selected.package_id, selected.package_version) == (
        "nova-character",
        "1.2.3-beta.1+class",
    )
    assert selected.provenance is selection.registration_plan.provenance


def test_repeated_planning_with_identical_ordered_inputs_is_equal() -> None:
    selections = (
        _selection("nova-character", _character("nova-character")),
        _selection("forest-guide", _world_object("forest-guide")),
    )

    assert build_package_set_plan(selections) == build_package_set_plan(selections)


def test_empty_package_set_is_a_structured_failure() -> None:
    result = build_package_set_plan(())

    assert result.plan is None
    assert _codes(result) == [PackageSetIssueCode.PACKAGE_SET_REQUIRED]
    assert result.issues[0].location == "selections"


@pytest.mark.parametrize("invalid", [None, 42, "nova-character", b"package"])
def test_non_iterable_or_text_api_misuse_raises_type_error(invalid: object) -> None:
    with pytest.raises(TypeError, match="iterable of PackageSelection"):
        build_package_set_plan(invalid)  # type: ignore[arg-type]


def test_invalid_selection_object_is_structured() -> None:
    result = build_package_set_plan((_selection("nova", _character("nova")), object()))

    assert result.plan is None
    assert PackageSetIssueCode.SELECTION_INVALID_TYPE in _codes(result)
    assert result.issues[0].package_index == 1


@pytest.mark.parametrize(
    ("package_id", "package_version", "expected"),
    [
        ("Bad ID", "1.0.0", PackageSetIssueCode.PACKAGE_ID_INVALID),
        ("nova-character", "1.0", PackageSetIssueCode.PACKAGE_VERSION_INVALID),
    ],
)
def test_selection_identity_and_exact_version_are_validated(
    package_id: str,
    package_version: str,
    expected: PackageSetIssueCode,
) -> None:
    plan = _plan("nova-character", _character("nova-character"))
    selection = PackageSelection(package_id, package_version, plan)

    result = build_package_set_plan((selection,))

    assert result.plan is None
    assert expected in _codes(result)


def test_registration_plan_has_an_explicit_runtime_type_contract() -> None:
    selection = PackageSelection(
        package_id="nova-character",
        package_version="1.0.0",
        registration_plan=object(),  # type: ignore[arg-type]
    )

    result = build_package_set_plan((selection,))

    assert _codes(result) == [PackageSetIssueCode.REGISTRATION_PLAN_INVALID]


@pytest.mark.parametrize("entries", [(), [_character("nova-character")]])
def test_registration_plan_entries_must_be_a_nonempty_tuple(entries: object) -> None:
    plan = StudentAPIRegistrationPlan(
        provenance=_provenance("nova-character"),
        entries=entries,  # type: ignore[arg-type]
    )
    selection = PackageSelection("nova-character", "1.0.0", plan)

    result = build_package_set_plan((selection,))

    assert result.plan is None
    assert _codes(result) == [PackageSetIssueCode.REGISTRATION_PLAN_INVALID]


def test_unsupported_and_mixed_student_api_versions_are_rejected() -> None:
    selections = (
        _selection("nova-character", _character("nova-character")),
        _selection(
            "forest-guide",
            _world_object("forest-guide"),
            student_api_version="0.2",
        ),
    )

    result = build_package_set_plan(selections)

    assert result.plan is None
    assert PackageSetIssueCode.STUDENT_API_VERSION_UNSUPPORTED in _codes(result)
    assert PackageSetIssueCode.STUDENT_API_VERSION_MISMATCH in _codes(result)


@pytest.mark.parametrize("mismatch", ["package_id", "package_version"])
def test_selection_pin_must_match_registration_plan_provenance(mismatch: str) -> None:
    plan = _plan("nova-character", _character("nova-character"))
    selection = PackageSelection(
        package_id="other-package" if mismatch == "package_id" else "nova-character",
        package_version="2.0.0" if mismatch == "package_version" else "1.0.0",
        registration_plan=plan,
    )

    result = build_package_set_plan((selection,))

    assert result.plan is None
    assert PackageSetIssueCode.PACKAGE_PROVENANCE_MISMATCH in _codes(result)


def test_malformed_manual_plan_provenance_is_structured() -> None:
    plan = StudentAPIRegistrationPlan(
        provenance=object(),  # type: ignore[arg-type]
        entries=(_character("nova-character"),),
    )
    selection = PackageSelection("nova-character", "1.0.0", plan)

    result = build_package_set_plan((selection,))

    assert result.plan is None
    assert PackageSetIssueCode.PACKAGE_PROVENANCE_MISMATCH in _codes(result)


def test_plan_and_entry_provenance_are_checked_independently() -> None:
    other = _provenance("nova-character", package_version="2.0.0")
    selection = PackageSelection(
        package_id="nova-character",
        package_version="1.0.0",
        registration_plan=_plan(
            "nova-character",
            _character("nova-character", provenance=other),
        ),
    )

    result = build_package_set_plan((selection,))

    assert result.plan is None
    assert _codes(result) == [PackageSetIssueCode.ENTRY_PROVENANCE_MISMATCH]


def test_qualified_identity_must_match_package_and_local_id() -> None:
    selection = _selection(
        "nova-character",
        _character("nova-character", qualified_id="nova-character:other"),
    )

    result = build_package_set_plan((selection,))

    assert result.plan is None
    assert _codes(result) == [PackageSetIssueCode.ENTRY_IDENTITY_INVALID]


def test_unsupported_registration_entry_type_is_rejected() -> None:
    result = build_package_set_plan((_selection("nova-character", object()),))

    assert result.plan is None
    assert _codes(result) == [PackageSetIssueCode.ENTRY_TYPE_UNSUPPORTED]


@pytest.mark.parametrize(
    "entry",
    [
        _character(
            "nova-character",
            character=CharacterRegistrationSpec(name="", x=1, y=2, color="gold"),
        ),
        _character(
            "nova-character",
            character=CharacterRegistrationSpec(name="Nova", x=True, y=2, color="gold"),
        ),
        _world_object(
            "nova-character",
            world_object=WorldObjectRegistrationSpec(
                name="Sign",
                x=1,
                y=-1,
                color="green",
                when_near=" ",
            ),
        ),
        _character(
            "nova-character",
            asset_reference=PackageAssetReference(
                id="portrait",
                type="image",
                path="/private/tmp/portrait.png",
            ),
        ),
    ],
)
def test_invalid_manual_registration_specification_is_rejected(
    entry: CharacterRegistration | WorldObjectRegistration,
) -> None:
    result = build_package_set_plan((_selection("nova-character", entry),))

    assert result.plan is None
    assert PackageSetIssueCode.ENTRY_VALUE_INVALID in _codes(result)
    assert all("/private/tmp" not in issue.message for issue in result.issues)


def test_same_package_and_version_selected_twice_is_rejected_without_replacement() -> None:
    selections = (
        _selection("shared-package", _character("shared-package", contribution_id="hero")),
        _selection("shared-package", _world_object("shared-package", contribution_id="sign")),
    )

    result = build_package_set_plan(selections)

    assert result.plan is None
    assert _codes(result) == [PackageSetIssueCode.PACKAGE_SELECTION_DUPLICATE]


def test_same_package_with_two_exact_versions_is_a_version_conflict() -> None:
    selections = (
        _selection("shared-package", _character("shared-package", contribution_id="hero")),
        _selection(
            "shared-package",
            _world_object("shared-package", contribution_id="sign"),
            package_version="2.0.0",
        ),
    )

    result = build_package_set_plan(selections)

    assert result.plan is None
    assert _codes(result) == [PackageSetIssueCode.PACKAGE_VERSION_CONFLICT]


def test_duplicate_package_diagnostic_is_deterministic() -> None:
    selections = (
        _selection("shared-package", _character("shared-package", contribution_id="hero")),
        _selection("shared-package", _world_object("shared-package", contribution_id="sign")),
    )

    first = build_package_set_plan(selections)
    second = build_package_set_plan(selections)

    assert first == second
    assert first.issues[0].package_index == 1
    assert "selections[0]" in first.issues[0].message


def test_duplicate_qualified_identity_within_one_manual_plan_is_rejected() -> None:
    selection = _selection(
        "nova-character",
        _character("nova-character", contribution_id="hero"),
        _world_object(
            "nova-character",
            contribution_id="hero",
            qualified_id="nova-character:hero",
        ),
    )

    result = build_package_set_plan((selection,))

    assert result.plan is None
    assert PackageSetIssueCode.ENTRY_IDENTITY_DUPLICATE in _codes(result)


def test_cross_package_qualified_identity_collision_is_defensively_rejected() -> None:
    colliding = _world_object(
        "forest-guide",
        contribution_id="hero",
        qualified_id="nova-character:hero",
    )
    selections = (
        _selection("nova-character", _character("nova-character", contribution_id="hero")),
        _selection("forest-guide", colliding),
    )

    result = build_package_set_plan(selections)

    assert result.plan is None
    assert PackageSetIssueCode.ENTRY_IDENTITY_INVALID in _codes(result)
    assert PackageSetIssueCode.ENTRY_IDENTITY_DUPLICATE in _codes(result)


@pytest.mark.parametrize(
    ("selections", "code"),
    [
        (
            (
                _selection("nova-character", _character("nova-character")),
                _selection("forest-guide", _character("forest-guide")),
            ),
            PackageSetIssueCode.CHARACTER_CARDINALITY_EXCEEDED,
        ),
        (
            (
                _selection("nova-character", _world_object("nova-character")),
                _selection("forest-guide", _world_object("forest-guide")),
            ),
            PackageSetIssueCode.WORLD_OBJECT_CARDINALITY_EXCEEDED,
        ),
        (
            (
                _selection(
                    "nova-character",
                    _character("nova-character", contribution_id="hero"),
                    _character("nova-character", contribution_id="friend"),
                ),
            ),
            PackageSetIssueCode.CHARACTER_CARDINALITY_EXCEEDED,
        ),
        (
            (
                _selection(
                    "nova-character",
                    _world_object("nova-character", contribution_id="sign"),
                    _world_object("nova-character", contribution_id="bridge"),
                ),
            ),
            PackageSetIssueCode.WORLD_OBJECT_CARDINALITY_EXCEEDED,
        ),
    ],
)
def test_aggregate_student_api_v01_cardinality_rejects_every_conflicting_entry(
    selections: tuple[PackageSelection, ...],
    code: PackageSetIssueCode,
) -> None:
    result = build_package_set_plan(selections)

    assert result.plan is None
    conflicts = [issue for issue in result.issues if issue.code is code]
    assert len(conflicts) == 2
    assert [(issue.package_index, issue.entry_index) for issue in conflicts] == [
        (0, 0),
        (1, 0) if len(selections) == 2 else (0, 1),
    ]


def test_valid_character_plus_world_object_package_set_succeeds() -> None:
    result = build_package_set_plan(
        (
            _selection("nova-character", _character("nova-character")),
            _selection("forest-guide", _world_object("forest-guide")),
        )
    )

    assert result.is_planned
    assert result.plan is not None
    assert len(result.plan.entries) == 2


def test_valid_toggle_metadata_survives_package_set_preflight() -> None:
    toggle = WorldObjectToggleRegistrationSpec(off_color="red", on_color="green")
    entry = _world_object(
        "switch-package",
        world_object=WorldObjectRegistrationSpec(
            name="Switch",
            x=30,
            y=40,
            color="red",
            toggle=toggle,
        ),
    )

    result = build_package_set_plan((_selection("switch-package", entry),))

    assert result.plan is not None
    planned = result.plan.entries[0]
    assert isinstance(planned, WorldObjectRegistration)
    assert planned.world_object.toggle is toggle


def test_valid_conditional_reference_survives_package_set_preflight() -> None:
    conditional = CharacterToggleResponseRegistrationSpec("switch", "Off", "On")
    character = _character(
        "magic",
        contribution_id="guide",
        character=CharacterRegistrationSpec(
            name="Guide",
            x=10,
            y=20,
            color="gold",
            respond_to_toggle=conditional,
        ),
    )
    world_object = _world_object(
        "magic",
        contribution_id="switch",
        world_object=WorldObjectRegistrationSpec(
            name="Switch",
            x=30,
            y=40,
            color="red",
            toggle=WorldObjectToggleRegistrationSpec("red", "green"),
        ),
    )

    result = build_package_set_plan((_selection("magic", character, world_object),))

    assert result.is_planned
    assert result.plan is not None
    planned = result.plan.entries[0]
    assert isinstance(planned, CharacterRegistration)
    assert planned.character.respond_to_toggle is conditional


@pytest.mark.parametrize("object_id", ["missing", "other:switch"])
def test_package_set_rejects_invalid_conditional_reference(object_id: str) -> None:
    character = _character(
        "magic",
        contribution_id="guide",
        character=CharacterRegistrationSpec(
            name="Guide",
            x=10,
            y=20,
            color="gold",
            respond_to_toggle=CharacterToggleResponseRegistrationSpec(object_id, "Off", "On"),
        ),
    )
    world_object = _world_object("magic", contribution_id="switch")

    result = build_package_set_plan((_selection("magic", character, world_object),))

    assert result.plan is None
    assert PackageSetIssueCode.ENTRY_VALUE_INVALID in [issue.code for issue in result.issues]


def test_package_set_rejects_forged_toggle_metadata() -> None:
    entry = _world_object(
        "switch-package",
        world_object=WorldObjectRegistrationSpec(
            name="Switch",
            x=30,
            y=40,
            color="blue",
            toggle=WorldObjectToggleRegistrationSpec(off_color="red", on_color="green"),
        ),
    )

    result = build_package_set_plan((_selection("switch-package", entry),))

    assert result.plan is None
    assert result.issues[0].code is PackageSetIssueCode.ENTRY_VALUE_INVALID
    assert result.issues[0].location.endswith("world_object.toggle")


def test_invalid_later_selection_returns_no_partial_package_set_plan() -> None:
    valid = _selection("nova-character", _character("nova-character"))
    invalid = _selection(
        "forest-guide",
        _world_object(
            "forest-guide",
            world_object=WorldObjectRegistrationSpec(
                name="Sign",
                x=-1,
                y=2,
                color="green",
            ),
        ),
    )

    result = build_package_set_plan((valid, invalid))

    assert result.plan is None
    assert result.issues
    assert not hasattr(result, "packages")


def test_multiple_independent_issues_accumulate_in_stable_order() -> None:
    bad_entry = _character(
        "nova-character",
        qualified_id="wrong",
        character=CharacterRegistrationSpec(name="", x=True, y=-1, color="magenta"),
    )
    selections = (
        _selection("nova-character", bad_entry),
        _selection("nova-character", _world_object("nova-character")),
    )

    first = build_package_set_plan(selections)
    second = build_package_set_plan(selections)

    assert first == second
    assert _codes(first) == [
        PackageSetIssueCode.ENTRY_IDENTITY_INVALID,
        PackageSetIssueCode.ENTRY_VALUE_INVALID,
        PackageSetIssueCode.ENTRY_VALUE_INVALID,
        PackageSetIssueCode.ENTRY_VALUE_INVALID,
        PackageSetIssueCode.ENTRY_VALUE_INVALID,
        PackageSetIssueCode.PACKAGE_SELECTION_DUPLICATE,
    ]
    assert all("0x" not in issue.message for issue in first.issues)


def test_invalid_character_greeting_is_rejected_during_package_preflight() -> None:
    entry = _character(
        "nova-character",
        character=CharacterRegistrationSpec(
            name="Nova",
            x=1,
            y=2,
            color="gold",
            greeting=" ",
        ),
    )

    result = build_package_set_plan((_selection("nova-character", entry),))

    assert result.plan is None
    assert _codes(result) == [PackageSetIssueCode.ENTRY_VALUE_INVALID]


@pytest.mark.parametrize("conversation", [("Only",), ("One", " "), ("1", "2", "3", "4")])
def test_invalid_character_conversation_is_rejected_during_package_preflight(
    conversation: tuple[str, ...],
) -> None:
    entry = _character(
        "nova-character",
        character=CharacterRegistrationSpec(
            name="Nova",
            x=1,
            y=2,
            color="gold",
            conversation=conversation,
        ),
    )

    result = build_package_set_plan((_selection("nova-character", entry),))

    assert result.plan is None
    assert _codes(result) == [PackageSetIssueCode.ENTRY_VALUE_INVALID]


def test_diagnostics_do_not_expose_malformed_path_or_address_like_identities() -> None:
    leaked = "/private/tmp/entry-at-0x1234"
    selection = _selection(
        "nova-character",
        _character("nova-character", qualified_id=leaked),
    )

    result = build_package_set_plan((selection,))

    assert result.plan is None
    assert result.issues[0].qualified_id is None
    assert all(
        leaked not in issue.message and leaked not in issue.location for issue in result.issues
    )


def test_public_models_and_nested_collections_are_immutable() -> None:
    selection = _selection("nova-character", _character("nova-character"))
    success = build_package_set_plan((selection,))
    failure = build_package_set_plan(())
    assert success.plan is not None

    assert isinstance(success.plan.packages, tuple)
    assert isinstance(success.plan.entries, tuple)
    assert isinstance(success.issues, tuple)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        selection.package_id = "changed"  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        success.plan.student_api_version = "changed"  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        success.plan.packages[0].package_version = "2.0.0"  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        success.plan.entries[0].qualified_id = "changed"  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        failure.issues[0].location = "changed"  # type: ignore[misc]


def test_preflight_performs_no_io_loading_planning_application_or_runtime_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from explore import Character, Object, World
    from explore.packages import (
        loader,
        registration_adapter,
        registration_application,
        validator,
    )

    selection = _selection("nova-character", _character("nova-character"))

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("package-set preflight crossed a forbidden boundary")

    monkeypatch.setattr(Path, "read_text", fail)
    monkeypatch.setattr(Path, "open", fail)
    monkeypatch.setattr(yaml, "safe_load", fail)
    monkeypatch.setattr(validator, "validate_explorer_package", fail)
    monkeypatch.setattr(loader, "load_explorer_package", fail)
    monkeypatch.setattr(registration_adapter, "build_student_api_registration_plan", fail)
    monkeypatch.setattr(registration_application, "apply_student_api_registration_plan", fail)
    monkeypatch.setattr(Character, "__init__", fail)
    monkeypatch.setattr(Object, "__init__", fail)
    monkeypatch.setattr(World, "add", fail)
    monkeypatch.setattr(importlib, "import_module", fail)
    monkeypatch.setattr(socket, "create_connection", fail)

    import pygame

    monkeypatch.setattr(pygame, "init", fail)
    monkeypatch.setattr(pygame.display, "set_mode", fail)

    result = build_package_set_plan((selection,))

    assert result.is_planned


def test_python_looking_text_remains_inert(tmp_path: Path) -> None:
    marker = tmp_path / "executed"
    text = f'__import__("pathlib").Path("{marker}").touch()'
    entry = _world_object(
        "forest-guide",
        world_object=WorldObjectRegistrationSpec(
            name="Sign",
            x=1,
            y=2,
            color="green",
            when_interacted=text,
        ),
    )

    result = build_package_set_plan((_selection("forest-guide", entry),))

    assert result.is_planned
    assert not marker.exists()


def test_package_set_public_exports_preserve_existing_pipeline_exports() -> None:
    import explore.packages as packages

    expected = {
        "PackageSelection",
        "SelectedPackagePlan",
        "PackageSetPlan",
        "PackageSetPlanResult",
        "PackageSetIssue",
        "PackageSetIssueCode",
        "build_package_set_plan",
        "validate_explorer_package",
        "load_explorer_package",
        "build_student_api_registration_plan",
        "plan_loaded_explorer_package",
        "apply_student_api_registration_plan",
        "StudentAPIWorldRegistrationTarget",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)


def test_package_set_source_has_no_forbidden_dependencies_or_runtime_calls() -> None:
    from explore.packages import package_set_planner

    source = Path(package_set_planner.__file__).read_text(encoding="utf-8")
    forbidden = (
        "import yaml",
        "from engine",
        "import engine",
        "import pygame",
        "load_explorer_package",
        "validate_explorer_package",
        "build_student_api_registration_plan",
        "apply_student_api_registration_plan",
        "StudentAPIWorldRegistrationTarget",
        "World(",
        "Character(",
        "Object(",
        "eval(",
        "exec(",
    )

    assert all(term not in source for term in forbidden)
