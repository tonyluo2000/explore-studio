"""Safe parsing for declarative Explorer Package contributions."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TypeVar

import yaml

from explore._colors import valid_color_names
from explore.packages.contribution_models import (
    LoadedCharacter,
    LoadedContribution,
    LoadedWorldObject,
    PackageAssetReference,
    PackageLoadIssue,
    PackageLoadIssueCode,
    PackageProvenance,
)
from explore.packages.models import ContributionDeclaration

_CHARACTER_FIELDS = frozenset({"name", "x", "y", "color", "asset_id", "greeting", "conversation"})
_WORLD_OBJECT_FIELDS = frozenset(
    {
        "name",
        "x",
        "y",
        "color",
        "asset_id",
        "when_near",
        "when_interacted",
    }
)
_VALID_COLORS = frozenset(valid_color_names())
_MISSING = object()
_T = TypeVar("_T")


def _issue(
    code: PackageLoadIssueCode,
    message: str,
    location: str,
) -> PackageLoadIssue:
    return PackageLoadIssue(code=code, message=message, location=location)


def _field_location(source_path: str, field: str) -> str:
    return f"{source_path}.{field}"


def _unknown_fields(
    mapping: Mapping[object, object],
    allowed: frozenset[str],
    source_path: str,
    issues: list[PackageLoadIssue],
) -> None:
    unknown = sorted(str(key) for key in mapping if not isinstance(key, str) or key not in allowed)
    for field in unknown:
        location = _field_location(source_path, field)
        issues.append(
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_FIELD_UNKNOWN,
                f"{location} is not part of the declarative contribution contract v0.1.",
                location,
            )
        )


def _text(
    mapping: Mapping[object, object],
    field: str,
    source_path: str,
    issues: list[PackageLoadIssue],
    *,
    required: bool,
    default: _T,
) -> str | _T | None:
    value = mapping.get(field, _MISSING)
    location = _field_location(source_path, field)
    if value is _MISSING:
        if required:
            issues.append(
                _issue(
                    PackageLoadIssueCode.CONTRIBUTION_FIELD_REQUIRED,
                    f"{location} is required.",
                    location,
                )
            )
            return None
        return default
    if not isinstance(value, str):
        issues.append(
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE,
                f"{location} must be a string.",
                location,
            )
        )
        return None
    if not value.strip():
        issues.append(
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location} must not be empty or whitespace-only.",
                location,
            )
        )
        return None
    return value.strip()


def _coordinate(
    mapping: Mapping[object, object],
    field: str,
    source_path: str,
    issues: list[PackageLoadIssue],
    *,
    required: bool,
    default: int,
) -> int | None:
    value = mapping.get(field, _MISSING)
    location = _field_location(source_path, field)
    if value is _MISSING:
        if required:
            issues.append(
                _issue(
                    PackageLoadIssueCode.CONTRIBUTION_FIELD_REQUIRED,
                    f"{location} is required.",
                    location,
                )
            )
            return None
        return default
    if isinstance(value, bool) or not isinstance(value, int):
        issues.append(
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE,
                f"{location} must be a whole number of 0 or greater.",
                location,
            )
        )
        return None
    if value < 0:
        issues.append(
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location} must be a whole number of 0 or greater.",
                location,
            )
        )
        return None
    return value


def _conversation(
    mapping: Mapping[object, object],
    source_path: str,
    issues: list[PackageLoadIssue],
) -> tuple[str, ...] | None:
    value = mapping.get("conversation", _MISSING)
    location = _field_location(source_path, "conversation")
    if value is _MISSING:
        return None
    if not isinstance(value, list):
        issues.append(
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE,
                f"{location} must be an ordered list of 2 or 3 strings.",
                location,
            )
        )
        return None
    if not 2 <= len(value) <= 3:
        issues.append(
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location} must contain exactly 2 or 3 lines.",
                location,
            )
        )
        return None
    lines: list[str] = []
    for index, line in enumerate(value):
        line_location = f"{location}[{index}]"
        if not isinstance(line, str):
            issues.append(
                _issue(
                    PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE,
                    f"{line_location} must be a string.",
                    line_location,
                )
            )
        elif not line.strip():
            issues.append(
                _issue(
                    PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID,
                    f"{line_location} must not be empty or whitespace-only.",
                    line_location,
                )
            )
        else:
            lines.append(line.strip())
    return tuple(lines) if len(lines) == len(value) else None


def _color(
    mapping: Mapping[object, object],
    source_path: str,
    issues: list[PackageLoadIssue],
    *,
    default: str,
) -> str | None:
    color = _text(
        mapping,
        "color",
        source_path,
        issues,
        required=False,
        default=default,
    )
    if not isinstance(color, str):
        return None
    if color not in _VALID_COLORS:
        location = _field_location(source_path, "color")
        options = ", ".join(sorted(_VALID_COLORS))
        issues.append(
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID,
                f'{location} "{color}" is not a valid colour; choose from: {options}.',
                location,
            )
        )
        return None
    return color


def _asset_reference(
    mapping: Mapping[object, object],
    source_path: str,
    assets_by_id: Mapping[str, PackageAssetReference],
    issues: list[PackageLoadIssue],
) -> PackageAssetReference | None:
    asset_id = _text(
        mapping,
        "asset_id",
        source_path,
        issues,
        required=False,
        default=None,
    )
    if asset_id is None:
        return None
    if not isinstance(asset_id, str):
        return None

    location = _field_location(source_path, "asset_id")
    asset = assets_by_id.get(asset_id)
    if asset is None:
        issues.append(
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_ASSET_UNKNOWN,
                f'{location} references undeclared asset ID "{asset_id}".',
                location,
            )
        )
        return None
    if asset.type != "image":
        issues.append(
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_ASSET_TYPE_MISMATCH,
                (
                    f'{location} references asset "{asset_id}" of type "{asset.type}"; '
                    'character and world-object appearance requires type "image".'
                ),
                location,
            )
        )
        return None
    return asset


def _parse_character(
    mapping: Mapping[object, object],
    declaration: ContributionDeclaration,
    provenance: PackageProvenance,
    assets_by_id: Mapping[str, PackageAssetReference],
) -> tuple[LoadedCharacter | None, tuple[PackageLoadIssue, ...]]:
    issues: list[PackageLoadIssue] = []
    source_path = declaration.path
    name = _text(mapping, "name", source_path, issues, required=True, default=None)
    x = _coordinate(mapping, "x", source_path, issues, required=False, default=430)
    y = _coordinate(mapping, "y", source_path, issues, required=False, default=270)
    color = _color(mapping, source_path, issues, default="gold")
    image = _asset_reference(mapping, source_path, assets_by_id, issues)
    greeting = _text(
        mapping,
        "greeting",
        source_path,
        issues,
        required=False,
        default=None,
    )
    conversation = _conversation(mapping, source_path, issues)
    if greeting is not None and conversation is not None:
        location = _field_location(source_path, "conversation")
        issues.append(
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_VALUE_INVALID,
                f"{location} cannot be combined with greeting.",
                location,
            )
        )
    _unknown_fields(mapping, _CHARACTER_FIELDS, source_path, issues)

    if issues:
        return None, tuple(issues)
    assert isinstance(name, str)
    assert x is not None
    assert y is not None
    assert color is not None
    assert greeting is None or isinstance(greeting, str)
    assert conversation is None or isinstance(conversation, tuple)
    return (
        LoadedCharacter(
            contribution_id=declaration.id,
            qualified_id=f"{provenance.package_id}:{declaration.id}",
            source_path=source_path,
            provenance=provenance,
            name=name,
            x=x,
            y=y,
            color=color,
            image=image,
            greeting=greeting,
            conversation=conversation,
        ),
        (),
    )


def _parse_world_object(
    mapping: Mapping[object, object],
    declaration: ContributionDeclaration,
    provenance: PackageProvenance,
    assets_by_id: Mapping[str, PackageAssetReference],
) -> tuple[LoadedWorldObject | None, tuple[PackageLoadIssue, ...]]:
    issues: list[PackageLoadIssue] = []
    source_path = declaration.path
    name = _text(mapping, "name", source_path, issues, required=True, default=None)
    x = _coordinate(mapping, "x", source_path, issues, required=True, default=0)
    y = _coordinate(mapping, "y", source_path, issues, required=True, default=0)
    color = _color(mapping, source_path, issues, default="brown")
    image = _asset_reference(mapping, source_path, assets_by_id, issues)
    when_near = _text(
        mapping,
        "when_near",
        source_path,
        issues,
        required=False,
        default=None,
    )
    when_interacted = _text(
        mapping,
        "when_interacted",
        source_path,
        issues,
        required=False,
        default=None,
    )
    _unknown_fields(mapping, _WORLD_OBJECT_FIELDS, source_path, issues)

    if issues:
        return None, tuple(issues)
    assert isinstance(name, str)
    assert x is not None
    assert y is not None
    assert color is not None
    assert when_near is None or isinstance(when_near, str)
    assert when_interacted is None or isinstance(when_interacted, str)
    return (
        LoadedWorldObject(
            contribution_id=declaration.id,
            qualified_id=f"{provenance.package_id}:{declaration.id}",
            source_path=source_path,
            provenance=provenance,
            name=name,
            x=x,
            y=y,
            color=color,
            image=image,
            when_near=when_near,
            when_interacted=when_interacted,
        ),
        (),
    )


def parse_contribution_file(
    contribution_path: Path,
    declaration: ContributionDeclaration,
    provenance: PackageProvenance,
    assets_by_id: Mapping[str, PackageAssetReference],
) -> tuple[LoadedContribution | None, tuple[PackageLoadIssue, ...]]:
    """Safely parse one validator-approved declarative contribution file."""
    source_path = declaration.path
    try:
        text = contribution_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None, (
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_INVALID_ENCODING,
                f"{source_path} must be encoded as UTF-8.",
                source_path,
            ),
        )
    except OSError:
        return None, (
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_READ_ERROR,
                f"{source_path} could not be read.",
                source_path,
            ),
        )

    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError:
        return None, (
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_INVALID_YAML,
                f"{source_path} is not valid safe YAML.",
                source_path,
            ),
        )

    if not isinstance(document, Mapping):
        return None, (
            _issue(
                PackageLoadIssueCode.CONTRIBUTION_INVALID_TYPE,
                f"{source_path} must contain a YAML mapping.",
                source_path,
            ),
        )

    if declaration.type == "character":
        return _parse_character(document, declaration, provenance, assets_by_id)
    return _parse_world_object(document, declaration, provenance, assets_by_id)
