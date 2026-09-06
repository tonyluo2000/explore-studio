"""Behavior-focused tests for Student API Registration Adapter v0.1."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any

import pytest
import yaml

from explore.packages import (
    CharacterRegistration,
    CharacterRegistrationSpec,
    Compatibility,
    IssueCode,
    LoadedCharacter,
    LoadedExplorerPackage,
    LoadedWorldObject,
    LoadedWorldObjectToggle,
    PackageAssetReference,
    PackageLoadIssue,
    PackageLoadIssueCode,
    PackageLoadResult,
    PackageMetadata,
    PackageProvenance,
    RegistrationPlanIssueCode,
    ValidationIssue,
    ValidationReport,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    WorldObjectToggleRegistrationSpec,
    build_student_api_registration_plan,
    load_explorer_package,
    plan_loaded_explorer_package,
)

PROJECT_ROOT = Path(__file__).parents[1]
EXAMPLE_ROOT = PROJECT_ROOT / "examples" / "explorer-packages"
PROVENANCE = PackageProvenance(
    package_id="river-rescue",
    package_version="1.0.0",
    student_api_version="0.1",
)


def _character(**overrides: Any) -> LoadedCharacter:
    values: dict[str, Any] = {
        "contribution_id": "guide",
        "qualified_id": "river-rescue:guide",
        "source_path": "character/guide.yaml",
        "provenance": PROVENANCE,
        "name": "River Guide",
        "x": 12,
        "y": 34,
        "color": "blue",
        "image": None,
    }
    values.update(overrides)
    return LoadedCharacter(**values)


def _world_object(**overrides: Any) -> LoadedWorldObject:
    values: dict[str, Any] = {
        "contribution_id": "sign",
        "qualified_id": "river-rescue:sign",
        "source_path": "objects/sign.yaml",
        "provenance": PROVENANCE,
        "name": "River Sign",
        "x": 56,
        "y": 78,
        "color": "green",
        "image": None,
        "when_near": "The sign hums.",
        "when_interacted": "Welcome, Explorer!",
    }
    values.update(overrides)
    return LoadedWorldObject(**values)


def _package(
    *contributions: object,
    provenance: PackageProvenance = PROVENANCE,
    metadata: PackageMetadata | None = None,
    compatibility: Compatibility | None = None,
    assets: tuple[PackageAssetReference, ...] = (),
) -> LoadedExplorerPackage:
    return LoadedExplorerPackage(
        metadata=metadata
        or PackageMetadata(
            id=provenance.package_id,
            display_name="River Rescue",
            version=provenance.package_version,
        ),
        compatibility=compatibility or Compatibility(student_api=provenance.student_api_version),
        provenance=provenance,
        contributions=contributions,  # type: ignore[arg-type]
        assets=assets,
    )


def _codes(package: LoadedExplorerPackage) -> list[RegistrationPlanIssueCode]:
    return [issue.code for issue in build_student_api_registration_plan(package).issues]


def test_nova_package_produces_exact_character_registration() -> None:
    """Nova maps to one detached Student API-compatible character entry."""
    loaded = load_explorer_package(EXAMPLE_ROOT / "nova-character")
    assert loaded.package is not None

    result = build_student_api_registration_plan(loaded.package)

    assert result.is_planned
    assert result.plan is not None
    assert result.plan.provenance == loaded.package.provenance
    assert result.plan.entries == (
        CharacterRegistration(
            qualified_id="nova-character:nova",
            contribution_id="nova",
            provenance=loaded.package.provenance,
            character=CharacterRegistrationSpec(
                name="Nova",
                x=430,
                y=270,
                color="gold",
            ),
        ),
    )


def test_character_greeting_is_validated_and_preserved() -> None:
    greeting = "Welcome to our trail!"

    result = build_student_api_registration_plan(_package(_character(greeting=greeting)))

    assert result.plan is not None
    entry = result.plan.entries[0]
    assert isinstance(entry, CharacterRegistration)
    assert entry.character.greeting == greeting


def test_character_conversation_is_validated_and_preserved() -> None:
    conversation = ("First", "Second", "Third")

    result = build_student_api_registration_plan(_package(_character(conversation=conversation)))

    assert result.plan is not None
    entry = result.plan.entries[0]
    assert isinstance(entry, CharacterRegistration)
    assert entry.character.conversation == conversation


@pytest.mark.parametrize("conversation", [(), ("Only",), ("One", " "), ("1", "2", "3", "4")])
def test_invalid_character_conversation_is_rejected(conversation: object) -> None:
    result = build_student_api_registration_plan(_package(_character(conversation=conversation)))

    assert result.plan is None
    assert result.issues[0].code is RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID
    assert result.issues[0].field == "conversation"


@pytest.mark.parametrize("greeting", ["", "   ", 42])
def test_invalid_character_greeting_is_rejected(greeting: object) -> None:
    result = build_student_api_registration_plan(_package(_character(greeting=greeting)))

    assert result.plan is None
    assert result.issues[0].code is RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID
    assert result.issues[0].field == "greeting"


def test_crystal_lantern_produces_exact_world_object_registration() -> None:
    """The lantern maps exactly, retaining both inert interaction messages."""
    loaded = load_explorer_package(EXAMPLE_ROOT / "crystal-lantern")
    assert loaded.package is not None

    result = build_student_api_registration_plan(loaded.package)

    assert result.is_planned
    assert result.plan is not None
    assert result.plan.entries == (
        WorldObjectRegistration(
            qualified_id="crystal-lantern:lantern",
            contribution_id="lantern",
            provenance=loaded.package.provenance,
            world_object=WorldObjectRegistrationSpec(
                name="Crystal Lantern",
                x=120,
                y=460,
                color="yellow",
                when_near="The lantern glows warmly.",
                when_interacted="A tiny crystal spark dances inside!",
            ),
        ),
    )


def test_toggle_metadata_is_validated_and_preserved_losslessly() -> None:
    toggle = LoadedWorldObjectToggle(off_color="red", on_color="green")

    result = build_student_api_registration_plan(
        _package(_world_object(color="red", toggle=toggle))
    )

    assert result.plan is not None
    entry = result.plan.entries[0]
    assert isinstance(entry, WorldObjectRegistration)
    assert entry.world_object.toggle == WorldObjectToggleRegistrationSpec(
        off_color="red",
        on_color="green",
    )
    assert entry.world_object.color == "red"


@pytest.mark.parametrize(
    "toggle",
    [
        object(),
        LoadedWorldObjectToggle(off_color="red", on_color="red"),
        LoadedWorldObjectToggle(off_color="cyan", on_color="green"),
        LoadedWorldObjectToggle(off_color="red", on_color="cyan"),
    ],
)
def test_forged_invalid_toggle_metadata_is_rejected(toggle: object) -> None:
    result = build_student_api_registration_plan(
        _package(_world_object(color="red", toggle=toggle))
    )

    assert result.plan is None
    assert result.issues[0].code is RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID
    assert result.issues[0].field == "toggle"


def test_toggle_off_color_must_match_projected_object_color() -> None:
    result = build_student_api_registration_plan(
        _package(
            _world_object(
                color="blue",
                toggle=LoadedWorldObjectToggle(off_color="red", on_color="green"),
            )
        )
    )

    assert result.plan is None
    assert result.issues[0].field == "toggle"


def test_toggle_cannot_retain_image_metadata() -> None:
    image = PackageAssetReference(id="switch", type="image", path="assets/switch.png")
    result = build_student_api_registration_plan(
        _package(
            _world_object(
                color="red",
                image=image,
                toggle=LoadedWorldObjectToggle(off_color="red", on_color="green"),
            ),
            assets=(image,),
        )
    )

    assert result.plan is None
    assert any(issue.field == "toggle" for issue in result.issues)


def test_entry_order_follows_loaded_contribution_order() -> None:
    """Mixed registration entries retain the loaded package order."""
    package = _package(
        _character(),
        _world_object(),
        _character(
            contribution_id="friend",
            qualified_id="river-rescue:friend",
            name="Friend",
        ),
    )

    result = build_student_api_registration_plan(package)

    assert result.plan is not None
    assert [entry.contribution_id for entry in result.plan.entries] == ["guide", "sign", "friend"]
    assert [type(entry) for entry in result.plan.entries] == [
        CharacterRegistration,
        WorldObjectRegistration,
        CharacterRegistration,
    ]


def test_asset_reference_is_preserved_without_materialization() -> None:
    """A loaded image stays the same package-relative immutable value object."""
    image = PackageAssetReference(
        id="portrait",
        type="image",
        path="assets/portrait.png",
    )
    package = _package(_character(image=image), assets=(image,))

    result = build_student_api_registration_plan(package)

    assert result.plan is not None
    entry = result.plan.entries[0]
    assert isinstance(entry, CharacterRegistration)
    assert entry.asset_reference is image
    assert entry.asset_reference.path == "assets/portrait.png"
    assert not Path(entry.asset_reference.path).is_absolute()


def test_repeated_planning_is_equality_comparable_and_deterministic() -> None:
    """The same loaded value graph produces the same complete plan."""
    package = _package(_character(), _world_object())

    first = build_student_api_registration_plan(package)
    second = build_student_api_registration_plan(package)

    assert first == second
    assert first.is_planned


@pytest.mark.parametrize("invalid_input", [None, "package", Path("package")])
def test_primary_builder_requires_loaded_package(invalid_input: object) -> None:
    """Paths and other Python-level contract violations are not package inputs."""
    with pytest.raises(
        TypeError,
        match="loaded_package must be a LoadedExplorerPackage",
    ):
        build_student_api_registration_plan(invalid_input)  # type: ignore[arg-type]


def test_successful_loader_result_convenience_api_delegates() -> None:
    """A successful load result plans identically through the convenience API."""
    loaded = load_explorer_package(EXAMPLE_ROOT / "nova-character")
    assert loaded.package is not None

    assert plan_loaded_explorer_package(loaded) == (
        build_student_api_registration_plan(loaded.package)
    )


def test_failed_loader_result_preserves_original_diagnostics() -> None:
    """Failed validation is retained and never repaired or partially planned."""
    validation_issue = ValidationIssue(
        code=IssueCode.MANIFEST_INVALID_YAML,
        message="manifest.yaml is not valid safe YAML.",
        location="manifest.yaml",
    )
    load_result = PackageLoadResult(
        validation_report=ValidationReport(
            manifest=None,
            issues=(validation_issue,),
        ),
        package=None,
        issues=(),
    )

    result = plan_loaded_explorer_package(load_result)

    assert not result.is_planned
    assert result.plan is None
    assert [issue.code for issue in result.issues] == [
        RegistrationPlanIssueCode.LOADED_PACKAGE_REQUIRED
    ]
    assert result.loader_diagnostics == (validation_issue,)


def test_incomplete_loader_result_with_no_package_cannot_be_planned() -> None:
    """Even a manually inconsistent issue-free result requires a package."""
    load_result = PackageLoadResult(
        validation_report=ValidationReport(manifest=None, issues=()),
        package=None,
        issues=(),
    )

    result = plan_loaded_explorer_package(load_result)

    assert result.plan is None
    assert result.loader_diagnostics == ()
    assert result.issues[0].code == RegistrationPlanIssueCode.LOADED_PACKAGE_REQUIRED


def test_loader_result_must_report_success_before_delegation() -> None:
    """A retained package beside a load issue is not partially used."""
    loaded = load_explorer_package(EXAMPLE_ROOT / "nova-character")
    assert loaded.package is not None
    load_issue = PackageLoadIssue(
        code=PackageLoadIssueCode.CONTRIBUTION_READ_ERROR,
        message="A contribution could not be read.",
        location="character/nova.yaml",
    )
    inconsistent = replace(loaded, issues=(load_issue,))

    result = plan_loaded_explorer_package(inconsistent)

    assert result.plan is None
    assert result.issues[0].code == RegistrationPlanIssueCode.LOAD_RESULT_NOT_LOADED
    assert result.loader_diagnostics == (load_issue,)


def test_unsupported_student_api_version_is_rejected() -> None:
    """Registration planning supports exactly Student API v0.1."""
    provenance = replace(PROVENANCE, student_api_version="0.2")
    character = replace(_character(), provenance=provenance)
    package = _package(character, provenance=provenance)

    assert _codes(package) == [RegistrationPlanIssueCode.STUDENT_API_VERSION_UNSUPPORTED]


def test_empty_loaded_package_is_rejected() -> None:
    """A manually incomplete package cannot produce an empty success plan."""
    assert _codes(_package()) == [RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID]


@pytest.mark.parametrize(
    ("metadata", "compatibility"),
    [
        (
            PackageMetadata(
                id="other-package",
                display_name="River Rescue",
                version="1.0.0",
            ),
            Compatibility(student_api="0.1"),
        ),
        (
            PackageMetadata(
                id="river-rescue",
                display_name="River Rescue",
                version="1.0.0",
            ),
            Compatibility(student_api="0.2"),
        ),
    ],
)
def test_package_metadata_and_compatibility_must_match_provenance(
    metadata: PackageMetadata,
    compatibility: Compatibility,
) -> None:
    """Containing package identity is checked without silent repair."""
    package = _package(
        _character(),
        metadata=metadata,
        compatibility=compatibility,
    )

    assert RegistrationPlanIssueCode.PACKAGE_PROVENANCE_MISMATCH in _codes(package)


def test_contribution_provenance_must_match_package() -> None:
    """Per-entry provenance cannot differ from its containing package."""
    other = replace(PROVENANCE, package_version="2.0.0")
    package = _package(_character(provenance=other))

    assert _codes(package) == [RegistrationPlanIssueCode.CONTRIBUTION_PROVENANCE_MISMATCH]


@pytest.mark.parametrize(
    ("contribution", "expected_count"),
    [
        (_character(contribution_id="Bad ID"), 2),
        (_character(qualified_id="river-rescue:other"), 1),
        (_character(qualified_id=""), 1),
    ],
)
def test_contribution_identity_must_be_valid_and_consistent(
    contribution: LoadedCharacter,
    expected_count: int,
) -> None:
    """Local and qualified contribution identities are verified defensively."""
    result = build_student_api_registration_plan(_package(contribution))

    assert result.plan is None
    assert (
        sum(
            issue.code == RegistrationPlanIssueCode.CONTRIBUTION_ID_INVALID
            for issue in result.issues
        )
        == expected_count
    )


def test_unsupported_loaded_contribution_type_is_rejected() -> None:
    """Only the two explicit loaded v0.1 contribution types are supported."""
    package = _package(_character(), object())

    assert _codes(package) == [RegistrationPlanIssueCode.CONTRIBUTION_TYPE_UNSUPPORTED]


def test_duplicate_qualified_identity_is_detected_late_and_atomically() -> None:
    """A duplicate discovered after valid entries returns no partial plan."""
    duplicate = replace(_character(), name="Duplicate Guide")
    package = _package(_world_object(), _character(), duplicate)

    result = build_student_api_registration_plan(package)

    assert result.plan is None
    assert [issue.code for issue in result.issues] == [
        RegistrationPlanIssueCode.CONTRIBUTION_ID_DUPLICATE
    ]
    assert result.issues[0].location == "contributions[2].qualified_id"


@pytest.mark.parametrize("color", ["magenta", "", 42, None])
def test_invalid_or_unsupported_color_is_rejected(color: object) -> None:
    """Manually constructed models must retain the Student API palette."""
    package = _package(_character(color=color))

    assert _codes(package) == [RegistrationPlanIssueCode.CONTRIBUTION_COLOR_UNSUPPORTED]


@pytest.mark.parametrize(
    "image",
    [
        PackageAssetReference(
            id="voice",
            type="audio",
            path="assets/voice.wav",
        ),
        object(),
    ],
)
def test_asset_type_mismatch_is_rejected(image: object) -> None:
    """Registration images remain typed image references."""
    package = _package(_character(image=image))

    assert _codes(package) == [RegistrationPlanIssueCode.CONTRIBUTION_ASSET_TYPE_MISMATCH]


@pytest.mark.parametrize(
    "contribution",
    [
        _character(name=" "),
        _character(x=True),
        _character(y=-1),
        _world_object(name=""),
        _world_object(x=1.5),
        _world_object(when_near=" "),
        _world_object(when_interacted=42),
    ],
)
def test_inconsistent_required_and_optional_values_are_rejected(
    contribution: LoadedCharacter | LoadedWorldObject,
) -> None:
    """Detached specs are not built from invalid Student API configuration."""
    result = build_student_api_registration_plan(_package(contribution))

    assert result.plan is None
    assert RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID in [
        issue.code for issue in result.issues
    ]


@pytest.mark.parametrize(
    "contributions",
    [
        (_character(), _world_object(y=-1)),
        (_character(x=-1), _world_object()),
        (
            _character(),
            _world_object(provenance=replace(PROVENANCE, package_version="2.0.0")),
        ),
        (
            _character(),
            _world_object(
                image=PackageAssetReference(
                    id="sound",
                    type="audio",
                    path="assets/sound.wav",
                )
            ),
        ),
    ],
)
def test_any_invalid_entry_prevents_a_partial_plan(
    contributions: tuple[LoadedCharacter | LoadedWorldObject, ...],
) -> None:
    """Valid neighbors are discarded whenever one contribution cannot map."""
    result = build_student_api_registration_plan(_package(*contributions))

    assert result.plan is None
    assert result.issues


def test_registration_models_and_nested_collections_are_immutable() -> None:
    """Plans, entries, specs, diagnostics, and nested collections are frozen."""
    result = build_student_api_registration_plan(_package(_character(), _world_object()))
    assert result.plan is not None
    assert isinstance(result.plan.entries, tuple)
    assert isinstance(result.issues, tuple)
    assert isinstance(result.loader_diagnostics, tuple)

    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.plan.provenance = PROVENANCE  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.plan.entries[0].qualified_id = "changed"  # type: ignore[misc]
    first = result.plan.entries[0]
    assert isinstance(first, CharacterRegistration)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        first.character.name = "Changed"  # type: ignore[misc]

    invalid = build_student_api_registration_plan(_package(_character(color="magenta")))
    with pytest.raises((FrozenInstanceError, AttributeError)):
        invalid.issues[0].location = "changed"  # type: ignore[misc]


def test_issue_order_is_stable_and_follows_documented_field_order() -> None:
    """Identity, field, and duplicate issues have one repeatable order."""
    bad = _world_object(
        contribution_id="Bad ID",
        qualified_id="river-rescue:guide",
        provenance=replace(PROVENANCE, package_version="2.0.0"),
        name=" ",
        x=True,
        y=-1,
        color="magenta",
        image=PackageAssetReference(
            id="sound",
            type="audio",
            path="assets/sound.wav",
        ),
        when_near="",
        when_interacted=42,
    )
    package = _package(_character(), bad)

    first = build_student_api_registration_plan(package)
    second = build_student_api_registration_plan(package)

    assert first == second
    assert [issue.code for issue in first.issues] == [
        RegistrationPlanIssueCode.CONTRIBUTION_ID_INVALID,
        RegistrationPlanIssueCode.CONTRIBUTION_PROVENANCE_MISMATCH,
        RegistrationPlanIssueCode.CONTRIBUTION_ID_INVALID,
        RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
        RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
        RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
        RegistrationPlanIssueCode.CONTRIBUTION_COLOR_UNSUPPORTED,
        RegistrationPlanIssueCode.CONTRIBUTION_ASSET_TYPE_MISMATCH,
        RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
        RegistrationPlanIssueCode.CONTRIBUTION_VALUE_INVALID,
        RegistrationPlanIssueCode.CONTRIBUTION_ID_DUPLICATE,
    ]
    assert [issue.field for issue in first.issues] == [
        "contribution_id",
        "provenance",
        "qualified_id",
        "name",
        "x",
        "y",
        "color",
        "image",
        "when_near",
        "when_interacted",
        "qualified_id",
    ]


def test_diagnostics_do_not_leak_loaded_source_paths() -> None:
    """Diagnostics use structural locations, never machine-specific source paths."""
    leaked_path = "/private/tmp/student-package/character/guide.yaml"
    package = _package(
        _character(
            source_path=leaked_path,
            color="magenta",
        )
    )

    result = build_student_api_registration_plan(package)

    assert result.issues
    assert all(
        leaked_path not in issue.location and leaked_path not in issue.message
        for issue in result.issues
    )


def test_planning_performs_no_io_yaml_runtime_or_world_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The in-memory planner cannot cross loading or application boundaries."""
    from explore import Character, Object, World

    loaded = load_explorer_package(EXAMPLE_ROOT / "nova-character")
    assert loaded.package is not None

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("registration planning crossed a forbidden boundary")

    monkeypatch.setattr(Path, "read_text", fail)
    monkeypatch.setattr(Path, "open", fail)
    monkeypatch.setattr(yaml, "safe_load", fail)
    monkeypatch.setattr(Character, "__init__", fail)
    monkeypatch.setattr(Object, "__init__", fail)
    monkeypatch.setattr(World, "add", fail)

    import pygame

    monkeypatch.setattr(pygame, "init", fail)
    monkeypatch.setattr(pygame.display, "set_mode", fail)

    result = build_student_api_registration_plan(loaded.package)

    assert result.is_planned


def test_python_syntax_in_interaction_text_remains_inert(tmp_path: Path) -> None:
    """Interaction strings are retained exactly and are never executed."""
    marker = tmp_path / "executed"
    text = f'__import__("pathlib").Path("{marker}").touch()'
    package = _package(_world_object(when_interacted=text))

    result = build_student_api_registration_plan(package)

    assert result.plan is not None
    entry = result.plan.entries[0]
    assert isinstance(entry, WorldObjectRegistration)
    assert entry.world_object.when_interacted == text
    assert not marker.exists()


def test_adapter_source_has_no_runtime_or_loading_dependencies() -> None:
    """The planner imports neither YAML/filesystem nor engine/Pygame modules."""
    from explore.packages import registration_adapter

    source = Path(registration_adapter.__file__).read_text(encoding="utf-8")

    assert "import yaml" not in source
    assert "from pathlib" not in source
    assert "from engine" not in source
    assert "import engine" not in source
    assert "import pygame" not in source


def test_registration_planning_public_exports() -> None:
    """Only the intentional registration-planning API is publicly exported."""
    import explore.packages as packages

    expected = {
        "CharacterRegistration",
        "CharacterRegistrationSpec",
        "RegistrationPlanIssue",
        "RegistrationPlanIssueCode",
        "RegistrationPlanResult",
        "StudentAPIRegistrationEntry",
        "StudentAPIRegistrationPlan",
        "WorldObjectRegistration",
        "WorldObjectRegistrationSpec",
        "build_student_api_registration_plan",
        "plan_loaded_explorer_package",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
