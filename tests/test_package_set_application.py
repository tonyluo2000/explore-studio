"""Behavior-focused tests for transactional package-set application v0.1."""

from __future__ import annotations

import importlib
import socket
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from explore import Character, Object, World
from explore.packages import (
    AppliedPackageSetRegistration,
    CharacterRegistration,
    CharacterRegistrationSpec,
    PackageAssetReference,
    PackageProvenance,
    PackageSetApplicationIssueCode,
    PackageSetApplicationResult,
    PackageSetPlan,
    RegistrationApplicationState,
    RegistrationType,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    StudentAPIRegistrationTarget,
    StudentAPIWorldRegistrationTarget,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    apply_package_set_plan,
)


class FakeTarget:
    """Deterministic explicit target with controlled transaction failures."""

    def __init__(
        self,
        *,
        existing_ids: tuple[str, ...] = (),
        character: Character | None = None,
        world_object: Object | None = None,
        fail_add: str | None = None,
        fail_remove: tuple[str, ...] = (),
    ) -> None:
        self.registrations: dict[str, Character | Object] = {
            qualified_id: Object(name="Existing", x=0, y=0) for qualified_id in existing_ids
        }
        self.character = character
        self.world_object = world_object
        self.fail_add = fail_add
        self.fail_remove = frozenset(fail_remove)
        self.mutations: list[tuple[str, str]] = []

    def contains_registration(self, qualified_id: str) -> bool:
        return qualified_id in self.registrations

    def has_character(self) -> bool:
        return self.character is not None

    def has_world_object(self) -> bool:
        return self.world_object is not None

    def add_character(self, qualified_id: str, character: Character) -> None:
        self.mutations.append(("add_character", qualified_id))
        if qualified_id == self.fail_add:
            raise RuntimeError("controlled add failure")
        if self.character is not None or qualified_id in self.registrations:
            raise RuntimeError("character conflict")
        self.character = character
        self.registrations[qualified_id] = character

    def remove_character(self, qualified_id: str, character: Character) -> None:
        self.mutations.append(("remove_character", qualified_id))
        if qualified_id in self.fail_remove:
            raise RuntimeError("controlled remove failure")
        if self.character is not character or self.registrations.get(qualified_id) is not character:
            raise RuntimeError("character identity mismatch")
        self.character = None
        del self.registrations[qualified_id]

    def add_world_object(self, qualified_id: str, world_object: Object) -> None:
        self.mutations.append(("add_world_object", qualified_id))
        if qualified_id == self.fail_add:
            raise RuntimeError("controlled add failure")
        if self.world_object is not None or qualified_id in self.registrations:
            raise RuntimeError("world-object conflict")
        self.world_object = world_object
        self.registrations[qualified_id] = world_object

    def remove_world_object(self, qualified_id: str, world_object: Object) -> None:
        self.mutations.append(("remove_world_object", qualified_id))
        if qualified_id in self.fail_remove:
            raise RuntimeError("controlled remove failure")
        if (
            self.world_object is not world_object
            or self.registrations.get(qualified_id) is not world_object
        ):
            raise RuntimeError("world-object identity mismatch")
        self.world_object = None
        del self.registrations[qualified_id]


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


def _set_plan(
    *packages: SelectedPackagePlan,
    student_api_version: str = "0.1",
) -> PackageSetPlan:
    return PackageSetPlan(
        student_api_version=student_api_version,
        packages=packages,
        entries=tuple(entry for package in packages for entry in package.registration_plan.entries),
    )


def _codes(result: PackageSetApplicationResult) -> list[PackageSetApplicationIssueCode]:
    return [issue.code for issue in result.issues]


@pytest.mark.parametrize(
    "package",
    [
        _selected("nova-character", _character("nova-character")),
        _selected("crystal-lantern", _world_object("crystal-lantern")),
    ],
)
def test_single_package_applies_to_explicit_target(package: SelectedPackagePlan) -> None:
    target = FakeTarget()

    result = apply_package_set_plan(_set_plan(package), target)

    assert result.state is RegistrationApplicationState.APPLIED
    assert result.is_applied
    assert len(result.applied) == 1
    assert result.applied[0].package_id == package.package_id
    assert result.applied[0].package_index == 0
    assert result.applied[0].entry_index == 0


def test_two_packages_commit_in_package_then_entry_order() -> None:
    object_package = _selected(
        "forest-guide",
        _world_object("forest-guide", contribution_id="sign"),
    )
    character_package = _selected(
        "nova-character",
        _character("nova-character", contribution_id="nova"),
    )
    target = FakeTarget()

    result = apply_package_set_plan(
        _set_plan(object_package, character_package),
        target,
    )

    assert result.is_applied
    assert target.mutations == [
        ("add_world_object", "forest-guide:sign"),
        ("add_character", "nova-character:nova"),
    ]
    assert [item.qualified_id for item in result.applied] == [
        "forest-guide:sign",
        "nova-character:nova",
    ]
    assert [(item.package_index, item.entry_index) for item in result.applied] == [
        (0, 0),
        (1, 0),
    ]


def test_reversing_package_order_reverses_valid_commit_order() -> None:
    character_package = _selected("nova-character", _character("nova-character"))
    object_package = _selected("forest-guide", _world_object("forest-guide"))
    target = FakeTarget()

    result = apply_package_set_plan(
        _set_plan(character_package, object_package),
        target,
    )

    assert result.is_applied
    assert [item[0] for item in target.mutations] == ["add_character", "add_world_object"]


def test_entry_order_within_one_package_is_preserved() -> None:
    package = _selected(
        "river-rescue",
        _world_object("river-rescue", contribution_id="sign"),
        _character("river-rescue", contribution_id="guide"),
    )
    target = FakeTarget()

    result = apply_package_set_plan(_set_plan(package), target)

    assert result.is_applied
    assert [item[1] for item in target.mutations] == [
        "river-rescue:sign",
        "river-rescue:guide",
    ]
    assert [item.entry_index for item in result.applied] == [0, 1]


def test_runtime_values_interaction_text_and_asset_metadata_are_preserved() -> None:
    asset = PackageAssetReference(
        id="lantern-image",
        type="image",
        path="assets/lantern.png",
    )
    text = '__import__("pathlib").Path("marker").touch()'
    entry = _world_object(
        "crystal-lantern",
        world_object=WorldObjectRegistrationSpec(
            name="Crystal Lantern",
            x=12,
            y=34,
            color="yellow",
            when_near="Warm light.",
            when_interacted=text,
        ),
        asset_reference=asset,
    )
    target = FakeTarget()

    result = apply_package_set_plan(
        _set_plan(_selected("crystal-lantern", entry)),
        target,
    )

    assert result.is_applied
    assert target.world_object is not None
    assert (
        target.world_object.name,
        target.world_object.x,
        target.world_object.y,
        target.world_object.color,
    ) == ("Crystal Lantern", 12, 34, "yellow")
    assert target.world_object.near_message == "Warm light."
    assert target.world_object.interacted_message == text
    assert result.applied[0].asset_reference is asset
    assert not hasattr(target.world_object, "asset")


def test_applied_metadata_preserves_package_and_entry_ownership() -> None:
    package = _selected(
        "nova-character",
        _character("nova-character", contribution_id="nova"),
        package_version="1.2.3",
    )

    result = apply_package_set_plan(_set_plan(package), FakeTarget())

    assert result.applied == (
        AppliedPackageSetRegistration(
            package_id="nova-character",
            package_version="1.2.3",
            package_index=0,
            entry_index=0,
            qualified_id="nova-character:nova",
            contribution_id="nova",
            provenance=package.provenance,
            registration_type=RegistrationType.CHARACTER,
        ),
    )


def test_valid_set_applies_to_world_through_one_retained_adapter() -> None:
    world = World("Package Set")
    target = StudentAPIWorldRegistrationTarget(world)
    plan = _set_plan(
        _selected("nova-character", _character("nova-character")),
        _selected("crystal-lantern", _world_object("crystal-lantern")),
    )

    result = apply_package_set_plan(plan, target)

    assert result.is_applied
    assert world.character is not None
    assert world.object is not None
    assert target.contains_registration("nova-character:hero")
    assert target.contains_registration("crystal-lantern:object")


@pytest.mark.parametrize(
    ("plan", "target", "expected"),
    [
        (None, FakeTarget(), PackageSetApplicationIssueCode.PACKAGE_SET_PLAN_REQUIRED),
        (
            _set_plan(_selected("nova-character", _character("nova-character"))),
            None,
            PackageSetApplicationIssueCode.TARGET_REQUIRED,
        ),
        (
            _set_plan(_selected("nova-character", _character("nova-character"))),
            object(),
            PackageSetApplicationIssueCode.TARGET_INCOMPATIBLE,
        ),
    ],
)
def test_required_inputs_and_target_contract_are_structured(
    plan: PackageSetPlan | None,
    target: object | None,
    expected: PackageSetApplicationIssueCode,
) -> None:
    result = apply_package_set_plan(plan, target)  # type: ignore[arg-type]

    assert result.state is RegistrationApplicationState.NOT_APPLIED
    assert expected in _codes(result)
    assert result.applied == ()


def test_package_set_and_selected_metadata_must_agree_exactly() -> None:
    package = _selected("nova-character", _character("nova-character"))
    invalid_package = replace(package, package_version="2.0.0")
    invalid_version = replace(
        _set_plan(package),
        student_api_version="0.2",
    )

    mismatch = apply_package_set_plan(_set_plan(invalid_package), FakeTarget())
    unsupported = apply_package_set_plan(invalid_version, FakeTarget())

    assert PackageSetApplicationIssueCode.SELECTED_PACKAGE_MISMATCH in _codes(mismatch)
    assert PackageSetApplicationIssueCode.STUDENT_API_VERSION_UNSUPPORTED in _codes(unsupported)


def test_nested_plan_and_flattened_entries_must_agree_exactly() -> None:
    character_package = _selected("nova-character", _character("nova-character"))
    object_package = _selected("forest-guide", _world_object("forest-guide"))
    plan = _set_plan(character_package, object_package)
    invalid = replace(plan, entries=tuple(reversed(plan.entries)))
    target = FakeTarget()

    result = apply_package_set_plan(invalid, target)

    assert PackageSetApplicationIssueCode.PACKAGE_SET_STRUCTURE_INVALID in _codes(result)
    assert target.mutations == []


def test_manual_entry_provenance_identity_and_duplicates_are_rejected() -> None:
    first = _selected("nova-character", _character("nova-character"))
    other_provenance = _provenance("forest-guide")
    malformed = _world_object(
        "forest-guide",
        qualified_id="nova-character:hero",
        contribution_id="hero",
        provenance=other_provenance,
    )
    second = _selected("forest-guide", malformed)
    target = FakeTarget()

    result = apply_package_set_plan(_set_plan(first, second), target)

    assert PackageSetApplicationIssueCode.ENTRY_DUPLICATE in _codes(result)
    assert PackageSetApplicationIssueCode.ENTRY_IDENTITY_INVALID in _codes(result)
    assert target.mutations == []


def test_entry_provenance_mismatch_is_rejected() -> None:
    package = _selected("nova-character", _character("nova-character"))
    wrong = replace(
        package.registration_plan.entries[0],
        provenance=_provenance("other-package"),
    )
    invalid_plan = replace(
        package.registration_plan,
        entries=(wrong,),
    )
    invalid_package = replace(package, registration_plan=invalid_plan)
    target = FakeTarget()

    result = apply_package_set_plan(_set_plan(invalid_package), target)

    assert PackageSetApplicationIssueCode.ENTRY_PROVENANCE_MISMATCH in _codes(result)
    assert target.mutations == []


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        (object(), PackageSetApplicationIssueCode.ENTRY_TYPE_UNSUPPORTED),
        (
            _character(
                "nova-character",
                character=CharacterRegistrationSpec(name="", x=-1, y=True, color="magenta"),
            ),
            PackageSetApplicationIssueCode.ENTRY_VALUE_INVALID,
        ),
        (
            _character(
                "nova-character",
                asset_reference=PackageAssetReference(
                    id="voice",
                    type="audio",
                    path="assets/voice.wav",
                ),
            ),
            PackageSetApplicationIssueCode.ENTRY_ASSET_TYPE_MISMATCH,
        ),
    ],
)
def test_unsupported_or_invalid_entries_fail_before_mutation(
    entry: object,
    expected: PackageSetApplicationIssueCode,
) -> None:
    package = _selected("nova-character", entry)
    target = FakeTarget()

    result = apply_package_set_plan(_set_plan(package), target)

    assert expected in _codes(result)
    assert result.state is RegistrationApplicationState.NOT_APPLIED
    assert target.mutations == []


@pytest.mark.parametrize(
    ("target", "package", "expected"),
    [
        (
            FakeTarget(existing_ids=("nova-character:hero",)),
            _selected("nova-character", _character("nova-character")),
            PackageSetApplicationIssueCode.TARGET_DUPLICATE,
        ),
        (
            FakeTarget(character=Character(name="Existing")),
            _selected("nova-character", _character("nova-character")),
            PackageSetApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED,
        ),
        (
            FakeTarget(world_object=Object(name="Existing", x=0, y=0)),
            _selected("forest-guide", _world_object("forest-guide")),
            PackageSetApplicationIssueCode.TARGET_WORLD_OBJECT_LIMIT_EXCEEDED,
        ),
    ],
)
def test_target_state_conflicts_fail_without_replacement(
    target: FakeTarget,
    package: SelectedPackagePlan,
    expected: PackageSetApplicationIssueCode,
) -> None:
    original_character = target.character
    original_object = target.world_object

    result = apply_package_set_plan(_set_plan(package), target)

    assert expected in _codes(result)
    assert target.mutations == []
    assert target.character is original_character
    assert target.world_object is original_object


def test_aggregate_cardinality_is_defensively_revalidated() -> None:
    first = _selected("first-character", _character("first-character"))
    second = _selected("second-character", _character("second-character"))
    target = FakeTarget()

    result = apply_package_set_plan(_set_plan(first, second), target)

    assert _codes(result).count(PackageSetApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED) == 2
    assert target.mutations == []


def test_target_state_inspection_failure_is_structured() -> None:
    class BrokenTarget(FakeTarget):
        def has_character(self) -> bool:
            raise RuntimeError("/machine/path at 0x1234")

    result = apply_package_set_plan(
        _set_plan(_selected("nova-character", _character("nova-character"))),
        BrokenTarget(),
    )

    assert result.state is RegistrationApplicationState.NOT_APPLIED
    assert PackageSetApplicationIssueCode.TARGET_INCOMPATIBLE in _codes(result)
    assert all("/machine/path" not in issue.message for issue in result.issues)
    assert all("0x1234" not in issue.message for issue in result.issues)


def test_complete_preflight_prevents_runtime_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _selected(
        "nova-character",
        _character(
            "nova-character",
            character=CharacterRegistrationSpec(name="", x=1, y=2, color="gold"),
        ),
    )
    target = FakeTarget()

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("constructor must not run")

    monkeypatch.setattr(Character, "__init__", fail)

    result = apply_package_set_plan(_set_plan(package), target)

    assert PackageSetApplicationIssueCode.ENTRY_VALUE_INVALID in _codes(result)
    assert target.mutations == []


def test_later_package_constructor_failure_stages_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _selected("nova-character", _character("nova-character"))
    second = _selected("forest-guide", _world_object("forest-guide"))
    target = FakeTarget()
    character_calls = 0
    original_character_init = Character.__init__

    def count_character(self: Character, *args: object, **kwargs: object) -> None:
        nonlocal character_calls
        character_calls += 1
        original_character_init(self, *args, **kwargs)

    def fail_object(*args: object, **kwargs: object) -> None:
        raise RuntimeError("/private/tmp/failure at 0x1234")

    monkeypatch.setattr(Character, "__init__", count_character)
    monkeypatch.setattr(Object, "__init__", fail_object)

    result = apply_package_set_plan(_set_plan(first, second), target)

    assert result.state is RegistrationApplicationState.NOT_APPLIED
    assert _codes(result) == [PackageSetApplicationIssueCode.INSTANCE_CONSTRUCTION_FAILED]
    assert result.issues[0].package_id == "forest-guide"
    assert result.issues[0].package_index == 1
    assert result.issues[0].entry_index == 0
    assert character_calls == 1
    assert target.mutations == []
    assert all("/private/tmp" not in issue.message for issue in result.issues)


def test_later_package_add_failure_rolls_back_across_package_boundary() -> None:
    first = _selected("nova-character", _character("nova-character"))
    second = _selected("forest-guide", _world_object("forest-guide"))
    target = FakeTarget(fail_add="forest-guide:object")

    result = apply_package_set_plan(_set_plan(first, second), target)

    assert result.state is RegistrationApplicationState.ROLLED_BACK
    assert not result.is_applied
    assert result.applied == ()
    assert result.unreverted == ()
    assert target.registrations == {}
    assert target.mutations == [
        ("add_character", "nova-character:hero"),
        ("add_world_object", "forest-guide:object"),
        ("remove_character", "nova-character:hero"),
    ]
    assert _codes(result) == [PackageSetApplicationIssueCode.TARGET_ADD_FAILED]
    assert result.issues[0].package_id == "forest-guide"


def test_first_add_failure_attempts_no_later_entry_or_rollback() -> None:
    first = _selected("nova-character", _character("nova-character"))
    second = _selected("forest-guide", _world_object("forest-guide"))
    target = FakeTarget(fail_add="nova-character:hero")

    result = apply_package_set_plan(_set_plan(first, second), target)

    assert result.state is RegistrationApplicationState.ROLLED_BACK
    assert target.mutations == [("add_character", "nova-character:hero")]


def test_rollback_preserves_preexisting_target_identity_state() -> None:
    target = FakeTarget(
        existing_ids=("other-package:tree",),
        fail_add="forest-guide:object",
    )
    plan = _set_plan(
        _selected("nova-character", _character("nova-character")),
        _selected("forest-guide", _world_object("forest-guide")),
    )

    result = apply_package_set_plan(plan, target)

    assert result.state is RegistrationApplicationState.ROLLED_BACK
    assert tuple(target.registrations) == ("other-package:tree",)
    assert target.registrations["other-package:tree"].name == "Existing"


def test_rollback_failure_reports_package_aware_unreverted_metadata() -> None:
    first = _selected("nova-character", _character("nova-character"))
    second = _selected("forest-guide", _world_object("forest-guide"))
    target = FakeTarget(
        fail_add="forest-guide:object",
        fail_remove=("nova-character:hero",),
    )

    result = apply_package_set_plan(_set_plan(first, second), target)

    assert result.state is RegistrationApplicationState.ROLLBACK_INCOMPLETE
    assert result.target_may_be_partially_modified
    assert not result.is_applied
    assert result.applied == ()
    assert _codes(result) == [
        PackageSetApplicationIssueCode.TARGET_ADD_FAILED,
        PackageSetApplicationIssueCode.TARGET_REMOVE_FAILED,
    ]
    assert result.unreverted == (
        AppliedPackageSetRegistration(
            package_id="nova-character",
            package_version="1.0.0",
            package_index=0,
            entry_index=0,
            qualified_id="nova-character:hero",
            contribution_id="hero",
            provenance=first.provenance,
            registration_type=RegistrationType.CHARACTER,
        ),
    )
    assert result.issues[1].package_id == "nova-character"
    assert result.issues[1].qualified_id == "nova-character:hero"


def test_reapplication_fails_preflight_but_separate_target_is_allowed() -> None:
    plan = _set_plan(
        _selected("nova-character", _character("nova-character")),
        _selected("forest-guide", _world_object("forest-guide")),
    )
    first_target = FakeTarget()
    second_target = FakeTarget()

    first = apply_package_set_plan(plan, first_target)
    mutation_count = len(first_target.mutations)
    repeated = apply_package_set_plan(plan, first_target)
    separate = apply_package_set_plan(plan, second_target)

    assert first.is_applied
    assert not repeated.is_applied
    assert PackageSetApplicationIssueCode.TARGET_DUPLICATE in _codes(repeated)
    assert len(first_target.mutations) == mutation_count
    assert separate.is_applied


def test_results_issues_and_nested_metadata_are_deeply_immutable() -> None:
    plan = _set_plan(_selected("nova-character", _character("nova-character")))
    success = apply_package_set_plan(plan, FakeTarget())
    failure = apply_package_set_plan(None, FakeTarget())

    assert isinstance(success.applied, tuple)
    assert isinstance(success.issues, tuple)
    assert isinstance(success.unreverted, tuple)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        success.state = RegistrationApplicationState.NOT_APPLIED  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        success.applied[0].package_id = "changed"  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        failure.issues[0].location = "changed"  # type: ignore[misc]


def test_equivalent_failures_and_issue_order_are_deterministic() -> None:
    first = _selected("first-character", _character("first-character"))
    second = _selected("second-character", _character("second-character"))
    plan = _set_plan(first, second)

    result_one = apply_package_set_plan(plan, FakeTarget())
    result_two = apply_package_set_plan(plan, FakeTarget())

    assert result_one == result_two
    assert _codes(result_one) == [
        PackageSetApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED,
        PackageSetApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED,
    ]


def test_target_contract_remains_runtime_checkable() -> None:
    assert isinstance(FakeTarget(), StudentAPIRegistrationTarget)


def test_application_performs_no_forbidden_activity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _set_plan(
        _selected("nova-character", _character("nova-character")),
        _selected("forest-guide", _world_object("forest-guide")),
    )

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("application crossed a forbidden boundary")

    monkeypatch.setattr(Path, "read_text", fail)
    monkeypatch.setattr(Path, "open", fail)
    monkeypatch.setattr(yaml, "safe_load", fail)
    monkeypatch.setattr(importlib, "import_module", fail)
    monkeypatch.setattr(socket, "socket", fail)

    from explore.packages import loader, package_set_planner, registration_adapter, validator

    monkeypatch.setattr(loader, "load_explorer_package", fail)
    monkeypatch.setattr(validator, "validate_explorer_package", fail)
    monkeypatch.setattr(registration_adapter, "build_student_api_registration_plan", fail)
    monkeypatch.setattr(package_set_planner, "build_package_set_plan", fail)

    import pygame

    monkeypatch.setattr(pygame, "init", fail)
    monkeypatch.setattr(pygame.display, "set_mode", fail)

    result = apply_package_set_plan(plan, FakeTarget())

    assert result.is_applied


def test_public_exports_preserve_the_complete_package_pipeline() -> None:
    import explore.packages as packages

    expected = {
        "AppliedPackageSetRegistration",
        "PackageSetApplicationIssue",
        "PackageSetApplicationIssueCode",
        "PackageSetApplicationResult",
        "RegistrationApplicationState",
        "apply_package_set_plan",
        "apply_student_api_registration_plan",
        "build_package_set_plan",
        "build_student_api_registration_plan",
        "load_explorer_package",
        "plan_loaded_explorer_package",
        "validate_explorer_package",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)


def test_source_has_no_forbidden_dependencies_or_orchestration_calls() -> None:
    from explore.packages import package_set_application

    source = Path(package_set_application.__file__).read_text(encoding="utf-8")

    assert "import yaml" not in source
    assert "from engine" not in source
    assert "import engine" not in source
    assert "import pygame" not in source
    assert "load_explorer_package" not in source
    assert "validate_explorer_package" not in source
    assert "build_student_api_registration_plan" not in source
    assert "build_package_set_plan" not in source
    assert "apply_student_api_registration_plan" not in source
    assert "eval(" not in source
    assert "exec(" not in source
