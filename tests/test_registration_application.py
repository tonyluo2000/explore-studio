"""Behavior-focused tests for transactional registration application v0.1."""

from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from explore import Character, Object, World
from explore.packages import (
    AppliedRegistration,
    CharacterRegistration,
    CharacterRegistrationSpec,
    PackageAssetReference,
    PackageProvenance,
    RegistrationApplicationIssueCode,
    RegistrationApplicationResult,
    RegistrationApplicationState,
    RegistrationType,
    StudentAPIRegistrationPlan,
    StudentAPIRegistrationTarget,
    StudentAPIWorldRegistrationTarget,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    apply_student_api_registration_plan,
    build_student_api_registration_plan,
    load_explorer_package,
)

PROJECT_ROOT = Path(__file__).parents[1]
EXAMPLE_ROOT = PROJECT_ROOT / "examples" / "explorer-packages"
PROVENANCE = PackageProvenance(
    package_id="river-rescue",
    package_version="1.0.0",
    student_api_version="0.1",
)


class FakeTarget:
    """Deterministic in-memory implementation of the public target contract."""

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


def _character(**overrides: Any) -> CharacterRegistration:
    values: dict[str, Any] = {
        "qualified_id": "river-rescue:guide",
        "contribution_id": "guide",
        "provenance": PROVENANCE,
        "character": CharacterRegistrationSpec(
            name="River Guide",
            x=12,
            y=34,
            color="blue",
        ),
        "asset_reference": None,
    }
    values.update(overrides)
    return CharacterRegistration(**values)


def _world_object(**overrides: Any) -> WorldObjectRegistration:
    values: dict[str, Any] = {
        "qualified_id": "river-rescue:sign",
        "contribution_id": "sign",
        "provenance": PROVENANCE,
        "world_object": WorldObjectRegistrationSpec(
            name="River Sign",
            x=56,
            y=78,
            color="green",
            when_near="The sign hums.",
            when_interacted="Welcome, Explorer!",
        ),
        "asset_reference": None,
    }
    values.update(overrides)
    return WorldObjectRegistration(**values)


def _plan(
    *entries: object,
    provenance: PackageProvenance = PROVENANCE,
) -> StudentAPIRegistrationPlan:
    return StudentAPIRegistrationPlan(
        provenance=provenance,
        entries=entries,  # type: ignore[arg-type]
    )


def _codes(result: RegistrationApplicationResult) -> list[RegistrationApplicationIssueCode]:
    return [issue.code for issue in result.issues]


def _example_plan(name: str) -> StudentAPIRegistrationPlan:
    loaded = load_explorer_package(EXAMPLE_ROOT / name)
    assert loaded.package is not None
    planned = build_student_api_registration_plan(loaded.package)
    assert planned.plan is not None
    return planned.plan


def test_nova_character_applies_to_explicit_student_world_target() -> None:
    world = World("Package Test")
    target = StudentAPIWorldRegistrationTarget(world)

    result = apply_student_api_registration_plan(_example_plan("nova-character"), target)

    assert result.state is RegistrationApplicationState.APPLIED
    assert result.is_applied
    assert world.character is not None
    assert (world.character.name, world.character.x, world.character.y, world.character.color) == (
        "Nova",
        430,
        270,
        "gold",
    )
    assert result.applied == (
        AppliedRegistration(
            qualified_id="nova-character:nova",
            contribution_id="nova",
            provenance=result.applied[0].provenance,
            registration_type=RegistrationType.CHARACTER,
        ),
    )


def test_crystal_lantern_applies_with_literal_interaction_messages() -> None:
    world = World("Package Test")
    target = StudentAPIWorldRegistrationTarget(world)

    result = apply_student_api_registration_plan(_example_plan("crystal-lantern"), target)

    assert result.is_applied
    assert world.object is not None
    assert (world.object.name, world.object.x, world.object.y, world.object.color) == (
        "Crystal Lantern",
        120,
        460,
        "yellow",
    )
    assert world.object.near_message == "The lantern glows warmly."
    assert world.object.interacted_message == "A tiny crystal spark dances inside!"
    assert result.applied[0].registration_type is RegistrationType.WORLD_OBJECT


def test_mixed_plan_commits_in_plan_order_and_maps_exact_instances() -> None:
    target = FakeTarget()

    result = apply_student_api_registration_plan(
        _plan(_world_object(), _character()),
        target,
    )

    assert result.is_applied
    assert target.mutations == [
        ("add_world_object", "river-rescue:sign"),
        ("add_character", "river-rescue:guide"),
    ]
    assert isinstance(target.world_object, Object)
    assert isinstance(target.character, Character)
    assert target.world_object.interacted_message == "Welcome, Explorer!"
    assert target.character.name == "River Guide"
    assert [item.qualified_id for item in result.applied] == [
        "river-rescue:sign",
        "river-rescue:guide",
    ]


def test_asset_reference_remains_application_metadata() -> None:
    asset = PackageAssetReference(
        id="guide-image",
        type="image",
        path="assets/guide.png",
    )
    target = FakeTarget()

    result = apply_student_api_registration_plan(
        _plan(_character(asset_reference=asset)),
        target,
    )

    assert result.is_applied
    assert result.applied[0].asset_reference is asset
    assert target.character is not None
    assert not hasattr(target.character, "asset")


@pytest.mark.parametrize(
    ("plan", "target", "expected_code"),
    [
        (None, FakeTarget(), RegistrationApplicationIssueCode.PLAN_REQUIRED),
        (_plan(_character()), None, RegistrationApplicationIssueCode.TARGET_REQUIRED),
        (_plan(_character()), object(), RegistrationApplicationIssueCode.TARGET_INCOMPATIBLE),
    ],
)
def test_required_inputs_and_target_contract_are_structured_failures(
    plan: StudentAPIRegistrationPlan | None,
    target: object | None,
    expected_code: RegistrationApplicationIssueCode,
) -> None:
    result = apply_student_api_registration_plan(plan, target)  # type: ignore[arg-type]

    assert result.state is RegistrationApplicationState.NOT_APPLIED
    assert _codes(result) == [expected_code]


def test_target_contract_is_runtime_checkable() -> None:
    assert isinstance(FakeTarget(), StudentAPIRegistrationTarget)


def test_unsupported_student_api_version_fails_before_mutation() -> None:
    provenance = replace(PROVENANCE, student_api_version="0.2")
    target = FakeTarget()

    result = apply_student_api_registration_plan(
        _plan(_character(provenance=provenance), provenance=provenance),
        target,
    )

    assert RegistrationApplicationIssueCode.STUDENT_API_VERSION_UNSUPPORTED in _codes(result)
    assert target.mutations == []


def test_plan_and_entry_provenance_are_checked_independently() -> None:
    invalid_plan_provenance = replace(PROVENANCE, package_id="Bad ID")
    other_entry_provenance = replace(PROVENANCE, package_version="2.0.0")

    invalid_plan = apply_student_api_registration_plan(
        _plan(_character(), provenance=invalid_plan_provenance),
        FakeTarget(),
    )
    invalid_entry = apply_student_api_registration_plan(
        _plan(_character(provenance=other_entry_provenance)),
        FakeTarget(),
    )

    assert RegistrationApplicationIssueCode.PLAN_PROVENANCE_MISMATCH in _codes(invalid_plan)
    assert RegistrationApplicationIssueCode.ENTRY_PROVENANCE_MISMATCH in _codes(invalid_entry)


def test_malformed_manual_provenance_types_are_structured() -> None:
    provenance = PackageProvenance(
        package_id=42,  # type: ignore[arg-type]
        package_version=None,  # type: ignore[arg-type]
        student_api_version="0.1",
    )

    result = apply_student_api_registration_plan(
        _plan(_character(provenance=provenance), provenance=provenance),
        FakeTarget(),
    )

    assert RegistrationApplicationIssueCode.PLAN_PROVENANCE_MISMATCH in _codes(result)


def test_qualified_identity_inconsistency_is_rejected() -> None:
    target = FakeTarget()

    result = apply_student_api_registration_plan(
        _plan(_character(qualified_id="river-rescue:other")),
        target,
    )

    assert _codes(result) == [RegistrationApplicationIssueCode.ENTRY_IDENTITY_INVALID]
    assert target.mutations == []


def test_duplicate_qualified_identity_in_manual_plan_is_rejected() -> None:
    target = FakeTarget()

    result = apply_student_api_registration_plan(
        _plan(
            _character(),
            _world_object(
                qualified_id="river-rescue:guide",
                contribution_id="guide",
            ),
        ),
        target,
    )

    assert RegistrationApplicationIssueCode.ENTRY_DUPLICATE in _codes(result)
    assert target.mutations == []


def test_existing_target_identity_is_rejected_without_idempotent_success() -> None:
    target = FakeTarget(existing_ids=("river-rescue:guide",))

    result = apply_student_api_registration_plan(_plan(_character()), target)

    assert RegistrationApplicationIssueCode.TARGET_DUPLICATE in _codes(result)
    assert target.mutations == []
    assert tuple(target.registrations) == ("river-rescue:guide",)


@pytest.mark.parametrize(
    ("target", "plan", "expected_code"),
    [
        (
            FakeTarget(character=Character(name="Existing")),
            _plan(_character()),
            RegistrationApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED,
        ),
        (
            FakeTarget(world_object=Object(name="Existing", x=0, y=0)),
            _plan(_world_object()),
            RegistrationApplicationIssueCode.TARGET_WORLD_OBJECT_LIMIT_EXCEEDED,
        ),
        (
            FakeTarget(),
            _plan(
                _character(),
                _character(
                    qualified_id="river-rescue:friend",
                    contribution_id="friend",
                ),
            ),
            RegistrationApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED,
        ),
        (
            FakeTarget(),
            _plan(
                _world_object(),
                _world_object(
                    qualified_id="river-rescue:bridge",
                    contribution_id="bridge",
                ),
            ),
            RegistrationApplicationIssueCode.TARGET_WORLD_OBJECT_LIMIT_EXCEEDED,
        ),
    ],
)
def test_v01_cardinality_never_replaces_or_invents_multiple_entities(
    target: FakeTarget,
    plan: StudentAPIRegistrationPlan,
    expected_code: RegistrationApplicationIssueCode,
) -> None:
    result = apply_student_api_registration_plan(plan, target)

    assert expected_code in _codes(result)
    assert target.mutations == []


def test_unsupported_entry_type_is_rejected() -> None:
    target = FakeTarget()

    result = apply_student_api_registration_plan(_plan(object()), target)

    assert _codes(result) == [RegistrationApplicationIssueCode.ENTRY_TYPE_UNSUPPORTED]
    assert target.mutations == []


@pytest.mark.parametrize(
    "entry",
    [
        _character(character=CharacterRegistrationSpec(name="", x=1, y=2, color="blue")),
        _character(character=CharacterRegistrationSpec(name="Guide", x=True, y=2, color="blue")),
        _world_object(
            world_object=WorldObjectRegistrationSpec(
                name="Sign",
                x=1,
                y=-2,
                color="green",
            )
        ),
        _world_object(
            world_object=WorldObjectRegistrationSpec(
                name="Sign",
                x=1,
                y=2,
                color="magenta",
                when_near=" ",
            )
        ),
    ],
)
def test_constructor_incompatible_values_fail_preflight(
    entry: CharacterRegistration | WorldObjectRegistration,
) -> None:
    target = FakeTarget()

    result = apply_student_api_registration_plan(_plan(entry), target)

    assert RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID in _codes(result)
    assert target.mutations == []


@pytest.mark.parametrize(
    ("asset", "expected_code"),
    [
        (
            PackageAssetReference(id="voice", type="audio", path="assets/voice.wav"),
            RegistrationApplicationIssueCode.ENTRY_ASSET_TYPE_MISMATCH,
        ),
        (
            PackageAssetReference(id="guide-image", type="image", path="/tmp/guide.png"),
            RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
        ),
        (
            PackageAssetReference(id="guide-image", type="image", path="assets/guide.jpg"),
            RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
        ),
        (
            PackageAssetReference(
                id=42,  # type: ignore[arg-type]
                type="image",
                path="assets/guide.png",
            ),
            RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
        ),
    ],
)
def test_invalid_asset_metadata_fails_preflight(
    asset: PackageAssetReference,
    expected_code: RegistrationApplicationIssueCode,
) -> None:
    target = FakeTarget()

    result = apply_student_api_registration_plan(
        _plan(_character(asset_reference=asset)),
        target,
    )

    assert expected_code in _codes(result)
    assert target.mutations == []


def test_invalid_later_entry_causes_zero_construction_and_zero_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = FakeTarget()

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("constructors must not run before complete preflight")

    monkeypatch.setattr(Character, "__init__", fail)

    result = apply_student_api_registration_plan(
        _plan(
            _character(),
            _world_object(
                world_object=WorldObjectRegistrationSpec(
                    name="Sign",
                    x=-1,
                    y=0,
                    color="green",
                )
            ),
        ),
        target,
    )

    assert RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID in _codes(result)
    assert target.mutations == []


def test_constructor_failure_is_structured_and_never_mutates_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = FakeTarget()

    def fail(*args: object, **kwargs: object) -> None:
        raise RuntimeError("/private/tmp/constructor failure at 0x1234")

    monkeypatch.setattr(Character, "__init__", fail)

    result = apply_student_api_registration_plan(_plan(_character()), target)

    assert _codes(result) == [RegistrationApplicationIssueCode.INSTANCE_CONSTRUCTION_FAILED]
    assert target.mutations == []
    assert "/private/tmp" not in result.issues[0].message
    assert "0x1234" not in result.issues[0].message


def test_later_commit_failure_rolls_back_earlier_entry() -> None:
    target = FakeTarget(fail_add="river-rescue:sign")

    result = apply_student_api_registration_plan(
        _plan(_character(), _world_object()),
        target,
    )

    assert result.state is RegistrationApplicationState.ROLLED_BACK
    assert not result.is_applied
    assert result.applied == ()
    assert result.unreverted_qualified_ids == ()
    assert target.character is None
    assert target.world_object is None
    assert target.registrations == {}
    assert target.mutations == [
        ("add_character", "river-rescue:guide"),
        ("add_world_object", "river-rescue:sign"),
        ("remove_character", "river-rescue:guide"),
    ]
    assert _codes(result) == [RegistrationApplicationIssueCode.TARGET_ADD_FAILED]


def test_rollback_preserves_preexisting_target_state() -> None:
    target = FakeTarget(
        existing_ids=("other-package:tree",),
        fail_add="river-rescue:sign",
    )

    result = apply_student_api_registration_plan(
        _plan(_character(), _world_object()),
        target,
    )

    assert result.state is RegistrationApplicationState.ROLLED_BACK
    assert tuple(target.registrations) == ("other-package:tree",)
    assert target.registrations["other-package:tree"].name == "Existing"


def test_rollback_failure_is_honest_and_identifies_unreverted_registration() -> None:
    target = FakeTarget(
        fail_add="river-rescue:sign",
        fail_remove=("river-rescue:guide",),
    )

    result = apply_student_api_registration_plan(
        _plan(_character(), _world_object()),
        target,
    )

    assert result.state is RegistrationApplicationState.ROLLBACK_INCOMPLETE
    assert result.target_may_be_partially_modified
    assert not result.is_applied
    assert result.applied == ()
    assert result.unreverted_qualified_ids == ("river-rescue:guide",)
    assert target.character is not None
    assert _codes(result) == [
        RegistrationApplicationIssueCode.TARGET_ADD_FAILED,
        RegistrationApplicationIssueCode.TARGET_REMOVE_FAILED,
    ]
    assert result.issues[0].qualified_id == "river-rescue:sign"
    assert result.issues[1].qualified_id == "river-rescue:guide"


def test_second_application_fails_preflight_without_mutation() -> None:
    target = FakeTarget()
    plan = _plan(_character())

    first = apply_student_api_registration_plan(plan, target)
    mutation_count = len(target.mutations)
    second = apply_student_api_registration_plan(plan, target)

    assert first.is_applied
    assert not second.is_applied
    assert RegistrationApplicationIssueCode.TARGET_DUPLICATE in _codes(second)
    assert RegistrationApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED in _codes(second)
    assert len(target.mutations) == mutation_count


def test_world_target_observes_direct_preexisting_entities() -> None:
    world = World("Existing")
    existing = Character(name="Existing")
    world.add(existing)
    target = StudentAPIWorldRegistrationTarget(world)

    result = apply_student_api_registration_plan(_plan(_character()), target)

    assert RegistrationApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED in _codes(result)
    assert world.character is existing


def test_world_target_removal_is_exact_and_not_student_facing() -> None:
    world = World("Rollback")
    target = StudentAPIWorldRegistrationTarget(world)
    character = Character(name="Guide")
    target.add_character("river-rescue:guide", character)

    with pytest.raises(Exception, match="exact entity"):
        target.remove_character("river-rescue:guide", Character(name="Other"))

    assert world.character is character
    assert not hasattr(world, "remove")


def test_target_state_query_failure_is_a_compatibility_diagnostic() -> None:
    class BrokenTarget(FakeTarget):
        def has_character(self) -> bool:
            raise RuntimeError("/machine/path")

    result = apply_student_api_registration_plan(_plan(_character()), BrokenTarget())

    assert result.state is RegistrationApplicationState.NOT_APPLIED
    assert _codes(result)[0] is RegistrationApplicationIssueCode.TARGET_INCOMPATIBLE
    assert "/machine/path" not in result.issues[0].message


def test_application_performs_no_loading_validation_yaml_or_runtime_initialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan(_character(), _world_object())
    target = FakeTarget()

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("application crossed a forbidden boundary")

    monkeypatch.setattr(Path, "read_text", fail)
    monkeypatch.setattr(Path, "open", fail)
    monkeypatch.setattr(yaml, "safe_load", fail)

    from explore.packages import loader, validator

    monkeypatch.setattr(loader, "load_explorer_package", fail)
    monkeypatch.setattr(validator, "validate_explorer_package", fail)
    monkeypatch.setattr(importlib, "import_module", fail)

    import pygame

    monkeypatch.setattr(pygame, "init", fail)
    monkeypatch.setattr(pygame.display, "set_mode", fail)

    result = apply_student_api_registration_plan(plan, target)

    assert result.is_applied


@pytest.mark.parametrize(
    ("field", "text"),
    [
        ("when_near", 'eval("2 + 2")'),
        ("when_interacted", '__import__("pathlib").Path("marker").touch()'),
    ],
)
def test_python_looking_interaction_text_remains_inert(
    tmp_path: Path,
    field: str,
    text: str,
) -> None:
    marker = tmp_path / "marker"
    dangerous_text = text.replace('"marker"', repr(str(marker)))
    spec = replace(
        _world_object().world_object,
        **{field: dangerous_text},
    )
    target = FakeTarget()

    result = apply_student_api_registration_plan(
        _plan(_world_object(world_object=spec)),
        target,
    )

    assert result.is_applied
    assert target.world_object is not None
    stored = (
        target.world_object.near_message
        if field == "when_near"
        else target.world_object.interacted_message
    )
    assert stored == dangerous_text
    assert not marker.exists()


def test_results_issues_and_applied_metadata_are_deeply_immutable() -> None:
    success = apply_student_api_registration_plan(_plan(_character()), FakeTarget())
    failure = apply_student_api_registration_plan(None, FakeTarget())

    assert isinstance(success.applied, tuple)
    assert isinstance(success.issues, tuple)
    assert isinstance(success.unreverted_qualified_ids, tuple)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        success.state = RegistrationApplicationState.NOT_APPLIED  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        success.applied[0].qualified_id = "changed"  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        failure.issues[0].location = "changed"  # type: ignore[misc]


def test_equivalent_preflight_failures_and_issue_order_are_deterministic() -> None:
    plan = _plan(
        _character(
            qualified_id="wrong",
            character=CharacterRegistrationSpec(name="", x=-1, y=True, color="magenta"),
        ),
        _character(
            qualified_id="wrong",
            contribution_id="friend",
        ),
    )

    first = apply_student_api_registration_plan(plan, FakeTarget())
    second = apply_student_api_registration_plan(plan, FakeTarget())

    assert first == second
    assert _codes(first) == [
        RegistrationApplicationIssueCode.ENTRY_IDENTITY_INVALID,
        RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
        RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
        RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
        RegistrationApplicationIssueCode.ENTRY_VALUE_INVALID,
        RegistrationApplicationIssueCode.ENTRY_IDENTITY_INVALID,
        RegistrationApplicationIssueCode.ENTRY_DUPLICATE,
        RegistrationApplicationIssueCode.TARGET_CHARACTER_LIMIT_EXCEEDED,
    ]


def test_diagnostics_never_include_raw_target_exception_details() -> None:
    target = FakeTarget(fail_add="river-rescue:guide")

    result = apply_student_api_registration_plan(_plan(_character()), target)

    assert result.state is RegistrationApplicationState.ROLLED_BACK
    assert all("controlled" not in issue.message for issue in result.issues)
    assert all("0x" not in issue.message for issue in result.issues)


def test_application_public_exports_are_importable() -> None:
    import explore.packages as packages

    expected = {
        "AppliedRegistration",
        "RegistrationApplicationIssue",
        "RegistrationApplicationIssueCode",
        "RegistrationApplicationResult",
        "RegistrationApplicationState",
        "RegistrationType",
        "StudentAPIRegistrationTarget",
        "StudentAPIWorldRegistrationTarget",
        "apply_student_api_registration_plan",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)


def test_application_source_has_no_loader_validator_engine_or_pygame_imports() -> None:
    from explore.packages import registration_application

    source = Path(registration_application.__file__).read_text(encoding="utf-8")

    assert "import yaml" not in source
    assert "from engine" not in source
    assert "import engine" not in source
    assert "import pygame" not in source
    assert "load_explorer_package" not in source
    assert "validate_explorer_package" not in source
    assert "eval(" not in source
    assert "exec(" not in source
