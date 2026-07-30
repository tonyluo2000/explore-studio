"""Behavior-focused tests for Explorer Package contract v0.1."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pytest
import yaml

from explore.packages import (
    MAX_ASSET_SIZE_BYTES,
    IssueCode,
    ValidationReport,
    validate_explorer_package,
)

PROJECT_ROOT = Path(__file__).parents[1]
EXAMPLE_ROOT = PROJECT_ROOT / "examples" / "explorer-packages"

VALID_MANIFEST = """\
schema_version: "0.1"
package:
  id: "river-rescue"
  display_name: "River Rescue"
  version: "1.0.0"
compatibility:
  student_api: "0.1"
contributions:
  - id: "river-guide"
    type: "character"
    path: "character/guide.yaml"
"""


def _write_package(
    root: Path,
    manifest: str | None = VALID_MANIFEST,
    files: Mapping[str, bytes] | None = None,
) -> Path:
    root.mkdir()
    if manifest is not None:
        (root / "manifest.yaml").write_text(manifest, encoding="utf-8")
    for relative_path, content in (files or {"character/guide.yaml": b"name: Guide\n"}).items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return root


def _codes(report: ValidationReport) -> list[IssueCode]:
    return [issue.code for issue in report.issues]


@pytest.mark.parametrize("name", ["nova-character", "crystal-lantern"])
def test_valid_example_packages(name: str) -> None:
    """Both checked-in declarative examples satisfy contract v0.1."""
    report = validate_explorer_package(EXAMPLE_ROOT / name)

    assert report.is_valid
    assert report.issues == ()
    assert report.manifest is not None


def test_valid_package_with_declared_asset(tmp_path: Path) -> None:
    """A supported, explicitly declared PNG asset is accepted."""
    manifest = VALID_MANIFEST + """\
assets:
  - id: "guide-avatar"
    type: "image"
    path: "assets/guide.png"
"""
    package = _write_package(
        tmp_path / "package",
        manifest,
        {
            "character/guide.yaml": b"name: Guide\n",
            "assets/guide.png": b"small inert test asset",
        },
    )

    assert validate_explorer_package(package).is_valid


def test_missing_manifest(tmp_path: Path) -> None:
    """A package directory without manifest.yaml is rejected."""
    package = _write_package(tmp_path / "package", manifest=None)

    assert _codes(validate_explorer_package(package)) == [IssueCode.MANIFEST_MISSING]


def test_invalid_yaml(tmp_path: Path) -> None:
    """Malformed YAML produces one stable loading diagnostic."""
    package = _write_package(tmp_path / "package", manifest="package: [")

    assert _codes(validate_explorer_package(package)) == [IssueCode.MANIFEST_INVALID_YAML]


def test_manifest_must_be_mapping(tmp_path: Path) -> None:
    """A valid YAML scalar is not a valid manifest document."""
    package = _write_package(tmp_path / "package", manifest='"hello"\n')

    assert _codes(validate_explorer_package(package)) == [IssueCode.MANIFEST_INVALID_TYPE]


@pytest.mark.parametrize(
    ("replacement", "expected_code"),
    [
        ('schema_version: "0.1"', IssueCode.SCHEMA_VERSION_UNSUPPORTED),
        ('id: "river-rescue"', IssueCode.PACKAGE_ID_INVALID),
        ('version: "1.0.0"', IssueCode.PACKAGE_VERSION_INVALID),
        ('student_api: "0.1"', IssueCode.STUDENT_API_UNSUPPORTED),
    ],
)
def test_invalid_scalar_contract_values(
    tmp_path: Path,
    replacement: str,
    expected_code: IssueCode,
) -> None:
    """Unsupported schema/API and malformed identity/version values are rejected."""
    invalid_values = {
        IssueCode.SCHEMA_VERSION_UNSUPPORTED: 'schema_version: "9.0"',
        IssueCode.PACKAGE_ID_INVALID: 'id: "River--Rescue-"',
        IssueCode.PACKAGE_VERSION_INVALID: 'version: "1.0"',
        IssueCode.STUDENT_API_UNSUPPORTED: 'student_api: "0.2"',
    }
    package = _write_package(
        tmp_path / "package",
        VALID_MANIFEST.replace(replacement, invalid_values[expected_code]),
    )

    assert expected_code in _codes(validate_explorer_package(package))


def test_duplicate_contribution_id_and_unsupported_type(tmp_path: Path) -> None:
    """Contribution IDs are package-local unique and types are allow-listed."""
    manifest = VALID_MANIFEST + """\
  - id: "river-guide"
    type: "quest"
    path: "quests/guide.yaml"
"""
    package = _write_package(
        tmp_path / "package",
        manifest,
        {
            "character/guide.yaml": b"name: Guide\n",
            "quests/guide.yaml": b"title: Guide\n",
        },
    )

    report = validate_explorer_package(package)

    assert IssueCode.CONTRIBUTION_ID_DUPLICATE in _codes(report)
    assert IssueCode.CONTRIBUTION_TYPE_UNSUPPORTED in _codes(report)


@pytest.mark.parametrize(
    ("declared_path", "expected_code"),
    [
        ("/tmp/guide.yaml", IssueCode.PATH_ABSOLUTE),
        ("C:/guide.yaml", IssueCode.PATH_ABSOLUTE),
        ("../guide.yaml", IssueCode.PATH_TRAVERSAL),
        ("character/missing.yaml", IssueCode.FILE_MISSING),
    ],
)
def test_unsafe_or_missing_contribution_paths(
    tmp_path: Path,
    declared_path: str,
    expected_code: IssueCode,
) -> None:
    """Absolute, traversal, and missing declared paths fail safely."""
    manifest = VALID_MANIFEST.replace("character/guide.yaml", declared_path)
    package = _write_package(tmp_path / "package", manifest)

    assert expected_code in _codes(validate_explorer_package(package))


def test_duplicate_asset_id(tmp_path: Path) -> None:
    """Asset identifiers are unique within their package namespace."""
    manifest = VALID_MANIFEST + """\
assets:
  - id: "guide-avatar"
    type: "image"
    path: "assets/guide.png"
  - id: "guide-avatar"
    type: "image"
    path: "assets/guide-alt.png"
"""
    package = _write_package(
        tmp_path / "package",
        manifest,
        {
            "character/guide.yaml": b"name: Guide\n",
            "assets/guide.png": b"png",
            "assets/guide-alt.png": b"png",
        },
    )

    assert IssueCode.ASSET_ID_DUPLICATE in _codes(validate_explorer_package(package))


def test_duplicate_normalized_path(tmp_path: Path) -> None:
    """Syntactically different declarations cannot name the same normalized file."""
    manifest = VALID_MANIFEST + """\
assets:
  - id: "guide-avatar"
    type: "image"
    path: "assets/guide.png"
  - id: "guide-avatar-alt"
    type: "image"
    path: "assets/./guide.png"
"""
    package = _write_package(
        tmp_path / "package",
        manifest,
        {
            "character/guide.yaml": b"name: Guide\n",
            "assets/guide.png": b"png",
        },
    )

    assert IssueCode.PATH_DUPLICATE in _codes(validate_explorer_package(package))


def test_unsupported_asset_extension(tmp_path: Path) -> None:
    """Declared asset type and extension must agree with policy."""
    manifest = VALID_MANIFEST + """\
assets:
  - id: "guide-avatar"
    type: "image"
    path: "assets/guide.jpg"
"""
    package = _write_package(
        tmp_path / "package",
        manifest,
        {
            "character/guide.yaml": b"name: Guide\n",
            "assets/guide.jpg": b"jpg",
        },
    )

    assert IssueCode.FILE_TYPE_UNSUPPORTED in _codes(validate_explorer_package(package))


def test_asset_size_limit(tmp_path: Path) -> None:
    """Assets larger than the named v0.1 policy limit are rejected."""
    manifest = VALID_MANIFEST + """\
assets:
  - id: "guide-avatar"
    type: "image"
    path: "assets/guide.png"
"""
    package = _write_package(tmp_path / "package", manifest)
    asset = package / "assets" / "guide.png"
    asset.parent.mkdir()
    with asset.open("wb") as stream:
        stream.truncate(MAX_ASSET_SIZE_BYTES + 1)

    assert IssueCode.FILE_TOO_LARGE in _codes(validate_explorer_package(package))


def test_symlink_is_rejected_without_following_it(tmp_path: Path) -> None:
    """Declared symlinks are rejected on platforms that support creating them."""
    outside = tmp_path / "outside.yaml"
    outside.write_text("name: Outside\n", encoding="utf-8")
    package = _write_package(
        tmp_path / "package",
        VALID_MANIFEST.replace("character/guide.yaml", "character/link.yaml"),
    )
    link = package / "character" / "link.yaml"
    try:
        link.symlink_to(outside)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Symlinks are unavailable on this platform: {error}")

    assert IssueCode.PATH_SYMLINK_NOT_ALLOWED in _codes(validate_explorer_package(package))


def test_safe_yaml_loader_does_not_construct_python_objects(tmp_path: Path) -> None:
    """Python-specific YAML tags are rejected without invoking their callable."""
    marker = tmp_path / "yaml-executed"
    manifest = f'!!python/object/apply:os.system ["touch {marker}"]\n'
    package = _write_package(tmp_path / "package", manifest)

    report = validate_explorer_package(package)

    assert _codes(report) == [IssueCode.MANIFEST_INVALID_YAML]
    assert not marker.exists()


def test_validation_never_executes_declared_python(tmp_path: Path) -> None:
    """Even a declared Python file remains inert and is rejected by extension."""
    marker = tmp_path / "python-executed"
    python_source = f"from pathlib import Path\nPath({str(marker)!r}).touch()\n".encode()
    manifest = VALID_MANIFEST.replace("character/guide.yaml", "character/guide.py")
    package = _write_package(
        tmp_path / "package",
        manifest,
        {"character/guide.py": python_source},
    )

    report = validate_explorer_package(package)

    assert IssueCode.FILE_TYPE_UNSUPPORTED in _codes(report)
    assert not marker.exists()


def test_diagnostics_are_deterministic_and_machine_independent(tmp_path: Path) -> None:
    """Repeated validation is equal and normal messages do not leak absolute paths."""
    manifest = VALID_MANIFEST.replace('schema_version: "0.1"', 'schema_version: "0.2"')
    manifest = manifest.replace('id: "river-rescue"', 'id: "River--Rescue"')
    manifest = manifest.replace('version: "1.0.0"', 'version: "1"')
    manifest = manifest.replace('student_api: "0.1"', 'student_api: "0.2"')
    package = _write_package(tmp_path / "package", manifest)

    first = validate_explorer_package(package)
    second = validate_explorer_package(package)

    assert first == second
    assert _codes(first) == [
        IssueCode.SCHEMA_VERSION_UNSUPPORTED,
        IssueCode.PACKAGE_ID_INVALID,
        IssueCode.PACKAGE_VERSION_INVALID,
        IssueCode.STUDENT_API_UNSUPPORTED,
    ]
    assert all(str(tmp_path) not in issue.message for issue in first.issues)


def test_public_report_and_manifest_are_immutable(tmp_path: Path) -> None:
    """The public result graph uses frozen value objects."""
    package = _write_package(tmp_path / "package")
    report = validate_explorer_package(package)
    assert report.manifest is not None

    with pytest.raises((AttributeError, TypeError)):
        report.manifest.package.id = "changed"  # type: ignore[misc]


def test_validator_source_uses_safe_yaml_api() -> None:
    """The parser is wired to PyYAML's safe loader, not the unsafe loader."""
    from explore.packages import manifest as manifest_module

    assert manifest_module.yaml.safe_load is yaml.safe_load
