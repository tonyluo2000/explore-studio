"""Behavior tests for deterministic Explorer Package export v0.1."""

from __future__ import annotations

import hashlib
import json
import shutil
import stat
import zipfile
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from explore.packages import (
    EXPLORER_PACKAGE_EXPORT_FILE_MODE,
    SUPPORTED_EXPLORER_PACKAGE_EXPORT_CONTRACT_VERSION,
    ExplorerPackageExportIssueCode,
    export_explorer_package,
    load_explorer_package,
    serialize_explorer_package_export_result,
)
from explore.packages.cli import main

PROJECT_ROOT = Path(__file__).parents[1]
TEMPLATE_ROOT = PROJECT_ROOT / "templates" / "student-repository"
_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def _write_package(root: Path, *, extra: bool = False, asset: bool = False) -> Path:
    root.mkdir(parents=True)
    asset_yaml = ""
    if asset:
        asset_yaml = """\
assets:
  - id: "beacon-image"
    type: "image"
    path: "assets/beacon.png"
"""
    (root / "manifest.yaml").write_text(
        """\
schema_version: "0.1"
package:
  id: "student-beacon"
  display_name: "Student Beacon"
  version: "1.0.0"
compatibility:
  student_api: "0.1"
contributions:
  - id: "beacon"
    type: "world_object"
    path: "objects/beacon.yaml"
""" + asset_yaml,
        encoding="utf-8",
    )
    (root / "objects").mkdir()
    (root / "objects" / "beacon.yaml").write_text(
        'name: "Beacon"\nx: 12\ny: 16\ncolor: "yellow"\n', encoding="utf-8"
    )
    if asset:
        (root / "assets").mkdir()
        (root / "assets" / "beacon.png").write_bytes(b"inert test image")
    if extra:
        (root / "notes.txt").write_text("not declared\n", encoding="utf-8")
    return root


def _destination(parent: Path) -> Path:
    return parent / "student-beacon-1.0.0.explorer-package.zip"


def _codes(result) -> list[ExplorerPackageExportIssueCode]:
    return [issue.code for issue in result.issues]


def test_exports_only_declared_members_in_canonical_order_and_metadata(tmp_path: Path) -> None:
    package = _write_package(tmp_path / "package", extra=True, asset=True)
    destination = _destination(tmp_path)

    result = export_explorer_package(package, destination)

    assert result.is_exported
    assert result.issues == ()
    assert result.artifact is not None and result.digest is not None
    assert result.artifact.contract_version == SUPPORTED_EXPLORER_PACKAGE_EXPORT_CONTRACT_VERSION
    assert [entry.relative_path for entry in result.artifact.entries] == [
        "manifest.yaml",
        "objects/beacon.yaml",
        "assets/beacon.png",
    ]
    assert result.artifact.total_content_bytes == sum(
        entry.bytes_written for entry in result.artifact.entries
    )
    assert result.digest.algorithm == "sha256"
    assert result.digest.hex_digest == hashlib.sha256(destination.read_bytes()).hexdigest()
    assert result.bytes_written == destination.stat().st_size
    assert stat.S_IMODE(destination.stat().st_mode) == EXPLORER_PACKAGE_EXPORT_FILE_MODE

    with zipfile.ZipFile(destination) as archive:
        members = archive.infolist()
        assert [member.filename for member in members] == [
            "manifest.yaml",
            "objects/beacon.yaml",
            "assets/beacon.png",
        ]
        assert archive.comment == b""
        assert all(member.date_time == _TIMESTAMP for member in members)
        assert all(member.create_system == 3 for member in members)
        assert all(member.compress_type == zipfile.ZIP_STORED for member in members)
        assert all(member.extra == b"" and member.comment == b"" for member in members)
        assert all((member.external_attr >> 16) == stat.S_IFREG | 0o644 for member in members)


def test_member_metadata_digests_match_exported_content(tmp_path: Path) -> None:
    package = _write_package(tmp_path / "package")
    destination = _destination(tmp_path)
    result = export_explorer_package(package, destination)
    assert result.artifact is not None

    with zipfile.ZipFile(destination) as archive:
        for entry in result.artifact.entries:
            content = archive.read(entry.relative_path)
            assert entry.digest_algorithm == "sha256"
            assert entry.digest_hex == hashlib.sha256(content).hexdigest()
            assert entry.bytes_written == len(content)
            assert entry.mode == 0o644


def test_equivalent_packages_produce_byte_identical_archives(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first_package = _write_package(first_root / "package")
    second_package = _write_package(second_root / "package")

    first = export_explorer_package(first_package, _destination(first_root))
    second = export_explorer_package(second_package, _destination(second_root))

    assert _destination(first_root).read_bytes() == _destination(second_root).read_bytes()
    assert first.artifact == second.artifact
    assert first.digest == second.digest


def test_undeclared_files_do_not_change_export_bytes(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first_package = _write_package(first_root / "package")
    second_package = _write_package(second_root / "package", extra=True)

    export_explorer_package(first_package, _destination(first_root))
    export_explorer_package(second_package, _destination(second_root))

    assert _destination(first_root).read_bytes() == _destination(second_root).read_bytes()


def test_result_models_are_frozen_and_json_is_stable(tmp_path: Path) -> None:
    result = export_explorer_package(_write_package(tmp_path / "package"), _destination(tmp_path))
    assert result.artifact is not None

    with pytest.raises(FrozenInstanceError):
        result.bytes_written = 0  # type: ignore[misc]
    document = json.loads(serialize_explorer_package_export_result(result))
    assert document["exported"] is True
    assert document["artifact"]["package_id"] == "student-beacon"
    assert document["artifact"]["package_version"] == "1.0.0"
    assert document["digest"]["hex_digest"] == result.digest.hex_digest  # type: ignore[union-attr]
    assert serialize_explorer_package_export_result(result).endswith("\n")


def test_invalid_package_fails_before_destination_write(tmp_path: Path) -> None:
    package = _write_package(tmp_path / "package")
    (package / "manifest.yaml").write_text("invalid: true\n", encoding="utf-8")

    result = export_explorer_package(package, _destination(tmp_path))

    assert _codes(result) == [ExplorerPackageExportIssueCode.PACKAGE_NOT_VALID]
    assert not _destination(tmp_path).exists()


def test_semantically_invalid_contribution_is_not_exported(tmp_path: Path) -> None:
    package = _write_package(tmp_path / "package")
    (package / "objects" / "beacon.yaml").write_text("name: ''\nx: 1\ny: 2\n", encoding="utf-8")

    result = export_explorer_package(package, _destination(tmp_path))

    assert _codes(result) == [ExplorerPackageExportIssueCode.PACKAGE_NOT_LOADED]


def test_rejects_relative_roots_and_destinations(tmp_path: Path) -> None:
    package = _write_package(tmp_path / "package")

    root_result = export_explorer_package("package", _destination(tmp_path))
    destination_result = export_explorer_package(package, "package.zip")

    assert _codes(root_result) == [ExplorerPackageExportIssueCode.PACKAGE_ROOT_NOT_ABSOLUTE]
    assert _codes(destination_result) == [ExplorerPackageExportIssueCode.DESTINATION_NOT_ABSOLUTE]


def test_requires_canonical_filename(tmp_path: Path) -> None:
    package = _write_package(tmp_path / "package")

    result = export_explorer_package(package, tmp_path / "wrong.zip")

    assert _codes(result) == [ExplorerPackageExportIssueCode.DESTINATION_NAME_MISMATCH]


def test_existing_destination_is_never_replaced(tmp_path: Path) -> None:
    package = _write_package(tmp_path / "package")
    destination = _destination(tmp_path)
    destination.write_bytes(b"existing")

    result = export_explorer_package(package, destination)

    assert _codes(result) == [ExplorerPackageExportIssueCode.DESTINATION_EXISTS]
    assert destination.read_bytes() == b"existing"


def test_symlinked_member_is_rejected(tmp_path: Path) -> None:
    package = _write_package(tmp_path / "package")
    target = package / "objects" / "target.yaml"
    target.write_text('name: "Target"\nx: 1\ny: 2\n', encoding="utf-8")
    member = package / "objects" / "beacon.yaml"
    member.unlink()
    member.symlink_to(target.name)

    result = export_explorer_package(package, _destination(tmp_path))

    assert _codes(result) == [ExplorerPackageExportIssueCode.PACKAGE_NOT_VALID]


def test_change_during_validation_and_reread_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from explore.packages import explorer_package_export as module

    package = _write_package(tmp_path / "package")
    original = module.load_explorer_package
    calls = 0

    def mutate_on_second_load(root: Path):
        nonlocal calls
        calls += 1
        if calls == 2:
            path = root / "objects" / "beacon.yaml"
            path.write_bytes(path.read_bytes() + b"\n")
        return original(root)

    monkeypatch.setattr(module, "load_explorer_package", mutate_on_second_load)

    result = export_explorer_package(package, _destination(tmp_path))

    assert _codes(result) == [ExplorerPackageExportIssueCode.PACKAGE_CHANGED]
    assert not _destination(tmp_path).exists()


def test_bounded_member_read_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from explore.packages import explorer_package_export as module

    package = _write_package(tmp_path / "package")
    monkeypatch.setattr(module, "MAX_EXPLORER_PACKAGE_EXPORT_MEMBER_BYTES", 8)

    result = export_explorer_package(package, _destination(tmp_path))

    assert _codes(result) == [ExplorerPackageExportIssueCode.MEMBER_TOO_LARGE]


def test_cli_validate_and_export_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    package = _write_package(tmp_path / "package")
    destination = _destination(tmp_path)

    assert main(["validate", str(package), "--json"]) == 0
    validated = json.loads(capsys.readouterr().out)
    assert validated == {
        "issues": [],
        "package": {
            "id": "student-beacon",
            "student_api_version": "0.1",
            "version": "1.0.0",
        },
        "valid": True,
    }
    assert main(["export", str(package), "--output", str(destination), "--json"]) == 0
    exported = json.loads(capsys.readouterr().out)
    assert exported["exported"] is True
    assert exported["digest"]["algorithm"] == "sha256"


def test_cli_validation_includes_declarative_loading(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    package = _write_package(tmp_path / "package")
    (package / "objects" / "beacon.yaml").write_text("name: ''\nx: 1\ny: 2\n", encoding="utf-8")

    assert main(["validate", str(package), "--json"]) == 1

    document = json.loads(capsys.readouterr().out)
    assert document["valid"] is False
    assert document["issues"][0]["location"] == "objects/beacon.yaml.name"


def test_student_repository_template_is_asset_free_and_loads() -> None:
    package_root = TEMPLATE_ROOT / "explorer-package"

    result = load_explorer_package(package_root)

    assert result.is_loaded
    assert result.package is not None
    assert result.package.assets == ()
    assert (TEMPLATE_ROOT / "tests" / "test_package.py").is_file()
    assert not (TEMPLATE_ROOT / "explore").exists()
    assert not (TEMPLATE_ROOT / "engine").exists()


def test_pristine_student_template_supports_documented_dist_export(tmp_path: Path) -> None:
    assert (TEMPLATE_ROOT / "dist" / ".gitkeep").is_file()
    checkout = tmp_path / "student-repository"
    shutil.copytree(TEMPLATE_ROOT, checkout)
    destination = checkout / "dist" / "student-beacon-1.0.0.explorer-package.zip"

    result = export_explorer_package(checkout / "explorer-package", destination)

    assert result.is_exported
    assert destination.is_file()


def test_export_contract_does_not_cross_forbidden_boundaries() -> None:
    import inspect

    from explore.packages import explorer_package_export as module

    source = inspect.getsource(module).lower()
    forbidden = (
        "subprocess",
        "requests",
        "authentication",
        "approval",
        "publication",
        "deployment",
        "exec(",
        "eval(",
    )
    assert all(token not in source for token in forbidden)
