"""Behavior-focused tests for Local Explorer Package Loader v0.1."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest
import yaml

from explore.packages import (
    Compatibility,
    ContributionDeclaration,
    ExplorerPackageManifest,
    LoadedCharacter,
    LoadedWorldObject,
    PackageLoadIssueCode,
    PackageMetadata,
    ValidationReport,
    load_explorer_package,
)

PROJECT_ROOT = Path(__file__).parents[1]
EXAMPLE_ROOT = PROJECT_ROOT / "examples" / "explorer-packages"


def _write_package(
    root: Path,
    *,
    contributions: list[dict[str, str]] | None = None,
    files: dict[str, bytes] | None = None,
    assets: list[dict[str, str]] | None = None,
) -> Path:
    declarations = contributions or [
        {
            "id": "river-guide",
            "type": "character",
            "path": "character/guide.yaml",
        }
    ]
    manifest: dict[str, Any] = {
        "schema_version": "0.1",
        "package": {
            "id": "river-rescue",
            "display_name": "River Rescue",
            "version": "1.0.0",
        },
        "compatibility": {"student_api": "0.1"},
        "contributions": declarations,
    }
    if assets is not None:
        manifest["assets"] = assets

    root.mkdir()
    (root / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
    )
    package_files = files or {"character/guide.yaml": b'name: "River Guide"\n'}
    for relative_path, content in package_files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return root


def _load_codes(package: Path) -> list[PackageLoadIssueCode]:
    return [issue.code for issue in load_explorer_package(package).issues]


@pytest.mark.parametrize(
    ("name", "loaded_type", "contribution_id"),
    [
        ("nova-character", LoadedCharacter, "nova"),
        ("crystal-lantern", LoadedWorldObject, "lantern"),
    ],
)
def test_example_packages_load(
    name: str,
    loaded_type: type[LoadedCharacter] | type[LoadedWorldObject],
    contribution_id: str,
) -> None:
    """Both validated examples load into their expected typed contribution."""
    result = load_explorer_package(EXAMPLE_ROOT / name)

    assert result.is_loaded
    assert result.package is not None
    assert len(result.package.contributions) == 1
    assert isinstance(result.package.contributions[0], loaded_type)
    assert result.package.contributions[0].contribution_id == contribution_id


def test_loaded_metadata_and_provenance_match_manifest() -> None:
    """Loaded package and contribution identity retain exact manifest provenance."""
    result = load_explorer_package(EXAMPLE_ROOT / "nova-character")
    assert result.package is not None

    assert result.package.metadata == PackageMetadata(
        id="nova-character",
        display_name="Nova the Explorer",
        version="1.0.0",
    )
    character = result.package.characters[0]
    assert character.provenance == result.package.provenance
    assert character.provenance.package_id == "nova-character"
    assert character.provenance.package_version == "1.0.0"
    assert character.provenance.student_api_version == "0.1"
    assert character.qualified_id == "nova-character:nova"


def test_contribution_order_follows_manifest_order(tmp_path: Path) -> None:
    """Mixed loaded contributions retain declaration order without registration."""
    package = _write_package(
        tmp_path / "package",
        contributions=[
            {"id": "guide", "type": "character", "path": "character/guide.yaml"},
            {"id": "sign", "type": "world_object", "path": "objects/sign.yaml"},
            {"id": "friend", "type": "character", "path": "character/friend.yaml"},
        ],
        files={
            "character/guide.yaml": b'name: "Guide"\n',
            "objects/sign.yaml": b'name: "Sign"\nx: 10\ny: 20\n',
            "character/friend.yaml": b'name: "Friend"\n',
        },
    )

    result = load_explorer_package(package)
    assert result.package is not None

    assert [item.contribution_id for item in result.package.contributions] == [
        "guide",
        "sign",
        "friend",
    ]
    assert [item.contribution_id for item in result.package.characters] == [
        "guide",
        "friend",
    ]
    assert [item.contribution_id for item in result.package.world_objects] == ["sign"]


def test_repeated_and_pathlike_loading_are_equal(tmp_path: Path) -> None:
    """Repeated loads and str/Path inputs produce equal immutable value graphs."""
    package = _write_package(tmp_path / "package")

    first = load_explorer_package(package)
    second = load_explorer_package(str(package))

    assert first == second
    assert first.is_loaded


def test_loading_does_not_initialize_pygame(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pure package loading never initializes a window, display, or Pygame."""
    import pygame

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("Pygame initialization is outside the loader boundary")

    monkeypatch.setattr(pygame, "init", fail)
    monkeypatch.setattr(pygame.display, "set_mode", fail)

    assert load_explorer_package(EXAMPLE_ROOT / "nova-character").is_loaded


def test_invalid_package_does_not_parse_contributions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Package validation is a hard first gate before contribution reads."""
    from explore.packages import loader as loader_module

    package = _write_package(tmp_path / "package")
    manifest_path = package / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = "9.0"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
    )

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("invalid packages must not reach contribution parsing")

    monkeypatch.setattr(loader_module, "parse_contribution_file", fail)

    result = load_explorer_package(package)

    assert not result.is_loaded
    assert result.package is None
    assert result.issues == ()
    assert result.validation_report.issues
    assert result.all_issues == result.validation_report.issues


def test_invalid_manifest_produces_no_partial_package(tmp_path: Path) -> None:
    """Manifest loading issues remain available without a loaded package."""
    package = _write_package(tmp_path / "package")
    (package / "manifest.yaml").write_text("package: [", encoding="utf-8")

    result = load_explorer_package(package)

    assert result.package is None
    assert not result.validation_report.is_valid
    assert [issue.code.value for issue in result.validation_report.issues] == [
        "MANIFEST_INVALID_YAML"
    ]


def test_invalid_contribution_yaml(tmp_path: Path) -> None:
    """Malformed contribution YAML is a structured loading error."""
    package = _write_package(
        tmp_path / "package",
        files={"character/guide.yaml": b"name: ["},
    )

    assert _load_codes(package) == [PackageLoadIssueCode.CONTRIBUTION_INVALID_YAML]


def test_invalid_contribution_encoding(tmp_path: Path) -> None:
    """Non-UTF-8 contribution content is rejected deterministically."""
    package = _write_package(
        tmp_path / "package",
        files={"character/guide.yaml": b"\xff"},
    )

    assert _load_codes(package) == [PackageLoadIssueCode.CONTRIBUTION_INVALID_ENCODING]


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(b"", id="empty"),
        pytest.param(b"[]\n", id="list"),
        pytest.param(b'"hello"\n', id="scalar"),
    ],
)
def test_contribution_root_must_be_mapping(tmp_path: Path, content: bytes) -> None:
    """Empty, scalar, and sequence documents are not contribution mappings."""
    package = _write_package(
        tmp_path / "package",
        files={"character/guide.yaml": content},
    )

    assert _load_codes(package) == [PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE]


def test_missing_required_field(tmp_path: Path) -> None:
    """Missing required fields produce the stable required-field diagnostic."""
    package = _write_package(
        tmp_path / "package",
        files={"character/guide.yaml": b"x: 10\n"},
    )

    result = load_explorer_package(package)

    assert _load_codes(package) == [PackageLoadIssueCode.CONTRIBUTION_FIELD_REQUIRED]
    assert result.issues[0].location == "character/guide.yaml.name"


def test_unknown_field(tmp_path: Path) -> None:
    """Unknown fields are visible rather than silently ignored."""
    package = _write_package(
        tmp_path / "package",
        files={"character/guide.yaml": b'name: "Guide"\nspeed: 4\n'},
    )

    result = load_explorer_package(package)

    assert _load_codes(package) == [PackageLoadIssueCode.CONTRIBUTION_FIELD_UNKNOWN]
    assert result.issues[0].location == "character/guide.yaml.speed"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "12"),
        ("x", '"left"'),
        ("color", "[]"),
        ("asset_id", "42"),
    ],
)
def test_wrong_scalar_types(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    """Known fields reject incompatible scalar and collection types."""
    content = f'name: "Guide"\n{field}: {value}\n'.encode()
    package = _write_package(
        tmp_path / "package",
        files={"character/guide.yaml": content},
    )

    assert PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE in _load_codes(package)


def test_boolean_coordinate_is_rejected(tmp_path: Path) -> None:
    """Boolean values do not pass integer coordinate validation."""
    package = _write_package(
        tmp_path / "package",
        files={"character/guide.yaml": b'name: "Guide"\nx: true\n'},
    )

    assert _load_codes(package) == [PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE]


@pytest.mark.parametrize("value", [".nan", ".inf", "-.inf"])
def test_non_finite_coordinate_is_rejected(tmp_path: Path, value: str) -> None:
    """NaN and infinity are rejected because v0.1 coordinates are integers."""
    package = _write_package(
        tmp_path / "package",
        files={"character/guide.yaml": f'name: "Guide"\nx: {value}\n'.encode()},
    )

    assert _load_codes(package) == [PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE]


def test_unsupported_nested_structure_is_rejected(tmp_path: Path) -> None:
    """Speculative nested position fields are not silently accepted."""
    package = _write_package(
        tmp_path / "package",
        files={
            "character/guide.yaml": (b'name: "Guide"\n' b"position:\n" b"  x: 10\n" b"  y: 20\n")
        },
    )

    result = load_explorer_package(package)

    assert _load_codes(package) == [PackageLoadIssueCode.CONTRIBUTION_FIELD_UNKNOWN]
    assert result.issues[0].location == "character/guide.yaml.position"


def test_unknown_asset_id(tmp_path: Path) -> None:
    """Contribution appearance may reference only declared manifest assets."""
    package = _write_package(
        tmp_path / "package",
        files={"character/guide.yaml": b'name: "Guide"\nasset_id: "missing"\n'},
    )

    assert _load_codes(package) == [PackageLoadIssueCode.CONTRIBUTION_ASSET_UNKNOWN]


def test_asset_type_mismatch(tmp_path: Path) -> None:
    """Audio assets cannot be used as character or world-object images."""
    package = _write_package(
        tmp_path / "package",
        assets=[{"id": "voice", "type": "audio", "path": "assets/voice.wav"}],
        files={
            "character/guide.yaml": b'name: "Guide"\nasset_id: "voice"\n',
            "assets/voice.wav": b"wav",
        },
    )

    assert _load_codes(package) == [PackageLoadIssueCode.CONTRIBUTION_ASSET_TYPE_MISMATCH]


def test_valid_asset_reference_retains_relative_identity(tmp_path: Path) -> None:
    """Valid image references remain typed and package-relative without decoding."""
    package = _write_package(
        tmp_path / "package",
        assets=[{"id": "portrait", "type": "image", "path": "assets/portrait.png"}],
        files={
            "character/guide.yaml": b'name: "Guide"\nasset_id: "portrait"\n',
            "assets/portrait.png": b"not decoded",
        },
    )

    result = load_explorer_package(package)
    assert result.package is not None

    image = result.package.characters[0].image
    assert image is not None
    assert image.id == "portrait"
    assert image.type == "image"
    assert image.path == "assets/portrait.png"
    assert not Path(image.path).is_absolute()
    assert result.package.assets == (image,)


def test_minimal_character_uses_student_api_defaults(tmp_path: Path) -> None:
    """A name-only character maps to the established Student API defaults."""
    package = _write_package(tmp_path / "package")

    result = load_explorer_package(package)
    assert result.package is not None

    character = result.package.characters[0]
    assert (character.name, character.x, character.y, character.color) == (
        "River Guide",
        430,
        270,
        "gold",
    )
    assert character.image is None
    assert character.greeting is None
    assert character.conversation is None


@pytest.mark.parametrize(
    ("content", "expected_code"),
    [
        (
            b'name: "Guide"\nx: -1\n',
            PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID,
        ),
        (
            b'name: "Guide"\ncolor: "magenta"\n',
            PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID,
        ),
        (
            b'name: "Guide"\nspeed: 4\n',
            PackageLoadIssueCode.CONTRIBUTION_FIELD_UNKNOWN,
        ),
        (
            b'name: "Guide"\ngreeting: 42\n',
            PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE,
        ),
        (
            b'name: "Guide"\ngreeting: "   "\n',
            PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID,
        ),
    ],
)
def test_invalid_character_configuration(
    tmp_path: Path,
    content: bytes,
    expected_code: PackageLoadIssueCode,
) -> None:
    """Invalid position, colour, greeting, and deferred fields are rejected."""
    package = _write_package(
        tmp_path / "package",
        files={"character/guide.yaml": content},
    )

    assert _load_codes(package) == [expected_code]


def test_character_maps_exactly_to_typed_model(tmp_path: Path) -> None:
    """All supported character fields map without coercion or engine mutation."""
    package = _write_package(
        tmp_path / "package",
        files={
            "character/guide.yaml": (
                b'name: "  River Guide  "\n'
                b"x: 12\n"
                b"y: 34\n"
                b'color: "blue"\n'
                b'greeting: "  Welcome, explorer!  "\n'
            )
        },
    )

    result = load_explorer_package(package)
    assert result.package is not None

    character = result.package.characters[0]
    assert character.name == "River Guide"
    assert character.x == 12
    assert character.y == 34
    assert character.color == "blue"
    assert character.greeting == "Welcome, explorer!"


def test_character_conversation_preserves_authored_order_and_trims_lines(tmp_path: Path) -> None:
    package = _write_package(
        tmp_path / "package",
        files={
            "character/guide.yaml": (
                b'name: "Guide"\nconversation:\n'
                b'  - "  First line.  "\n'
                b'  - "Second line."\n'
                b'  - " Third line. "\n'
            )
        },
    )

    result = load_explorer_package(package)

    assert result.package is not None
    assert result.package.characters[0].conversation == (
        "First line.",
        "Second line.",
        "Third line.",
    )


@pytest.mark.parametrize(
    "conversation",
    [
        "conversation: []\n",
        'conversation: ["Only one"]\n',
        'conversation: ["One", "Two", "Three", "Four"]\n',
        'conversation: ["One", "   "]\n',
        'conversation: ["One", 2]\n',
    ],
)
def test_character_conversation_requires_two_or_three_nonblank_strings(
    tmp_path: Path,
    conversation: str,
) -> None:
    package = _write_package(
        tmp_path / "package",
        files={"character/guide.yaml": f'name: "Guide"\n{conversation}'.encode()},
    )

    result = load_explorer_package(package)

    assert result.package is None
    assert result.issues


def test_character_rejects_ambiguous_greeting_and_conversation(tmp_path: Path) -> None:
    package = _write_package(
        tmp_path / "package",
        files={
            "character/guide.yaml": (
                b'name: "Guide"\n' b'greeting: "Hello"\n' b'conversation: ["First", "Second"]\n'
            )
        },
    )

    result = load_explorer_package(package)

    assert result.package is None
    assert result.issues[0].location == "character/guide.yaml.conversation"


def test_minimal_world_object(tmp_path: Path) -> None:
    """A world object requires name and position and uses the brown default."""
    package = _write_package(
        tmp_path / "package",
        contributions=[{"id": "sign", "type": "world_object", "path": "objects/sign.yaml"}],
        files={"objects/sign.yaml": b'name: "Sign"\nx: 10\ny: 20\n'},
    )

    result = load_explorer_package(package)
    assert result.package is not None

    world_object = result.package.world_objects[0]
    assert (world_object.name, world_object.x, world_object.y, world_object.color) == (
        "Sign",
        10,
        20,
        "brown",
    )
    assert world_object.when_near is None
    assert world_object.when_interacted is None


@pytest.mark.parametrize("field", ["width", "height", "solid"])
def test_deferred_world_object_fields_are_unknown(tmp_path: Path, field: str) -> None:
    """Dimensions and solidity remain engine-owned and deferred in loader v0.1."""
    package = _write_package(
        tmp_path / "package",
        contributions=[{"id": "sign", "type": "world_object", "path": "objects/sign.yaml"}],
        files={"objects/sign.yaml": (f'name: "Sign"\nx: 10\ny: 20\n{field}: 32\n'.encode())},
    )

    assert _load_codes(package) == [PackageLoadIssueCode.CONTRIBUTION_FIELD_UNKNOWN]


def test_invalid_world_object_bounds(tmp_path: Path) -> None:
    """Negative object placement is rejected without clamping."""
    package = _write_package(
        tmp_path / "package",
        contributions=[{"id": "sign", "type": "world_object", "path": "objects/sign.yaml"}],
        files={"objects/sign.yaml": b'name: "Sign"\nx: 10\ny: -1\n'},
    )

    assert _load_codes(package) == [PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID]


def test_world_object_maps_exactly_to_typed_model(tmp_path: Path) -> None:
    """Supported object fields and messages map into the immutable model."""
    package = _write_package(
        tmp_path / "package",
        contributions=[{"id": "sign", "type": "world_object", "path": "objects/sign.yaml"}],
        files={
            "objects/sign.yaml": (
                b'name: "Sign"\n'
                b"x: 10\n"
                b"y: 20\n"
                b'color: "green"\n'
                b'when_near: "  Read me  "\n'
                b'when_interacted: "  Welcome!  "\n'
            )
        },
    )

    result = load_explorer_package(package)
    assert result.package is not None

    world_object = result.package.world_objects[0]
    assert world_object.name == "Sign"
    assert world_object.color == "green"
    assert world_object.when_near == "Read me"
    assert world_object.when_interacted == "Welcome!"


def test_issue_order_codes_and_locations_are_stable(tmp_path: Path) -> None:
    """Known fields report in contract order, followed by sorted unknown fields."""
    package = _write_package(
        tmp_path / "package",
        contributions=[{"id": "sign", "type": "world_object", "path": "objects/sign.yaml"}],
        assets=[{"id": "sound", "type": "audio", "path": "assets/sound.wav"}],
        files={
            "objects/sign.yaml": (
                b"name: 12\n"
                b"x: true\n"
                b"y: -1\n"
                b'color: "magenta"\n'
                b'asset_id: "sound"\n'
                b"when_near: []\n"
                b"zebra: true\n"
                b"alpha: true\n"
            ),
            "assets/sound.wav": b"wav",
        },
    )

    first = load_explorer_package(package)
    second = load_explorer_package(package)

    assert first == second
    assert [issue.code for issue in first.issues] == [
        PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE,
        PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE,
        PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID,
        PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID,
        PackageLoadIssueCode.CONTRIBUTION_ASSET_TYPE_MISMATCH,
        PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE,
        PackageLoadIssueCode.CONTRIBUTION_FIELD_UNKNOWN,
        PackageLoadIssueCode.CONTRIBUTION_FIELD_UNKNOWN,
    ]
    assert [issue.location for issue in first.issues] == [
        "objects/sign.yaml.name",
        "objects/sign.yaml.x",
        "objects/sign.yaml.y",
        "objects/sign.yaml.color",
        "objects/sign.yaml.asset_id",
        "objects/sign.yaml.when_near",
        "objects/sign.yaml.alpha",
        "objects/sign.yaml.zebra",
    ]
    assert all(str(tmp_path) not in issue.message for issue in first.issues)


def test_loading_is_atomic_when_one_contribution_is_invalid(tmp_path: Path) -> None:
    """A valid contribution is not returned beside an invalid contribution."""
    package = _write_package(
        tmp_path / "package",
        contributions=[
            {"id": "guide", "type": "character", "path": "character/guide.yaml"},
            {"id": "sign", "type": "world_object", "path": "objects/sign.yaml"},
        ],
        files={
            "character/guide.yaml": b'name: "Guide"\n',
            "objects/sign.yaml": b'name: "Sign"\nx: -1\ny: 20\n',
        },
    )

    result = load_explorer_package(package)

    assert not result.is_loaded
    assert result.validation_report.is_valid
    assert result.package is None
    assert result.issues


def test_duplicate_defense_prevents_repeated_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The loader independently guards qualified identities after validation."""
    from explore.packages import loader as loader_module

    package = _write_package(
        tmp_path / "package",
        files={
            "character/guide.yaml": b'name: "Guide"\n',
            "character/other.yaml": b'name: "Other"\n',
        },
    )
    manifest = ExplorerPackageManifest(
        schema_version="0.1",
        package=PackageMetadata(
            id="river-rescue",
            display_name="River Rescue",
            version="1.0.0",
        ),
        compatibility=Compatibility(student_api="0.1"),
        contributions=(
            ContributionDeclaration(
                id="guide",
                type="character",
                path="character/guide.yaml",
            ),
            ContributionDeclaration(
                id="guide",
                type="character",
                path="character/other.yaml",
            ),
        ),
    )
    monkeypatch.setattr(
        loader_module,
        "validate_explorer_package",
        lambda root: ValidationReport(manifest=manifest, issues=()),
    )

    result = load_explorer_package(package)

    assert result.package is None
    assert [issue.code for issue in result.issues] == [PackageLoadIssueCode.CONTRIBUTION_DUPLICATE]


def test_python_yaml_tag_is_inert(tmp_path: Path) -> None:
    """Safe YAML rejects Python constructors without invoking their callable."""
    marker = tmp_path / "executed"
    content = f'!!python/object/apply:os.system ["touch {marker}"]\n'.encode()
    package = _write_package(
        tmp_path / "package",
        files={"character/guide.yaml": content},
    )

    result = load_explorer_package(package)

    assert [issue.code for issue in result.issues] == [
        PackageLoadIssueCode.CONTRIBUTION_INVALID_YAML
    ]
    assert not marker.exists()


def test_public_loader_models_are_immutable(tmp_path: Path) -> None:
    """Public result, package, contribution, provenance, and issues are frozen."""
    package = _write_package(tmp_path / "package")
    result = load_explorer_package(package)
    assert result.package is not None

    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.package.characters[0].name = "Changed"  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.package.provenance.package_id = "changed"  # type: ignore[misc]


def test_public_loader_exports() -> None:
    """The intentionally small package-loader surface is publicly importable."""
    import explore.packages as packages

    expected = {
        "LoadedCharacter",
        "LoadedExplorerPackage",
        "LoadedWorldObject",
        "PackageAssetReference",
        "PackageLoadIssue",
        "PackageLoadIssueCode",
        "PackageLoadResult",
        "PackageProvenance",
        "load_explorer_package",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)


def test_parser_uses_safe_yaml_api() -> None:
    """Contribution parsing is wired only to PyYAML's safe loader."""
    from explore.packages import contribution_parser

    assert contribution_parser.yaml.safe_load is yaml.safe_load


def test_loader_does_not_import_engine_or_pygame() -> None:
    """The pure loader boundary contains no engine or rendering imports."""
    from explore.packages import contribution_parser, loader

    sources = [
        Path(contribution_parser.__file__).read_text(encoding="utf-8"),
        Path(loader.__file__).read_text(encoding="utf-8"),
    ]

    assert all("import pygame" not in source for source in sources)
    assert all("from engine" not in source for source in sources)
    assert all("import engine" not in source for source in sources)
