"""Behavior-focused tests for class-world manifest file transport v0.1."""

from __future__ import annotations

import io
import json
import os
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from explore.packages import (
    MAX_CLASS_WORLD_MANIFEST_BYTES,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldCohort,
    ClassWorldConfiguration,
    ClassWorldConfigurationSpec,
    ClassWorldManifestFileIssue,
    ClassWorldManifestFileIssueCode,
    ClassWorldManifestFileReadResult,
    ClassWorldManifestFileWriteResult,
    ClassWorldManifestIssueCode,
    ClassWorldPackagePin,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    build_class_world_configuration,
    parse_class_world_manifest,
    read_class_world_manifest_file,
    serialize_class_world_manifest,
    write_class_world_manifest_file,
)
from explore.packages import class_world_manifest_transport as transport


def _provenance(package_id: str) -> PackageProvenance:
    return PackageProvenance(package_id, "1.0.0", "0.1")


def _selected(
    package_id: str,
    entry: CharacterRegistration | WorldObjectRegistration,
) -> SelectedPackagePlan:
    provenance = _provenance(package_id)
    adjusted = replace(entry, provenance=provenance)
    registration_plan = StudentAPIRegistrationPlan(provenance, (adjusted,))
    return SelectedPackagePlan(package_id, "1.0.0", provenance, registration_plan)


def _plan() -> PackageSetPlan:
    character_package = "nova-character"
    object_package = "crystal-lantern"
    character = CharacterRegistration(
        f"{character_package}:hero",
        "hero",
        _provenance(character_package),
        CharacterRegistrationSpec("Explorer", 10, 20, "gold"),
        None,
    )
    world_object = WorldObjectRegistration(
        f"{object_package}:lantern",
        "lantern",
        _provenance(object_package),
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
    packages = (
        _selected(character_package, character),
        _selected(object_package, world_object),
    )
    return PackageSetPlan(
        student_api_version="0.1",
        packages=packages,
        entries=tuple(entry for package in packages for entry in package.registration_plan.entries),
    )


def _configuration(
    plan: PackageSetPlan | None = None,
    *,
    display_name: str = "Expedition Orion — Fall 2026",
    cohort_display_name: str = "Expedition Orion",
) -> ClassWorldConfiguration:
    selected_plan = plan or _plan()
    result = build_class_world_configuration(
        ClassWorldConfigurationSpec(
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
        ),
        selected_plan,
    )
    assert result.configuration is not None
    return result.configuration


def _codes(
    result: ClassWorldManifestFileReadResult | ClassWorldManifestFileWriteResult,
) -> list[ClassWorldManifestFileIssueCode]:
    return [issue.code for issue in result.issues]


def _private_temps(parent: Path, destination: Path) -> list[Path]:
    return list(parent.glob(f".{destination.name}.*.tmp"))


def _reverse_manifest_packages(text: str) -> str:
    manifest = json.loads(text)
    manifest["packages"] = list(reversed(manifest["packages"]))
    return json.dumps(manifest)


@pytest.mark.parametrize("use_string", [False, True], ids=["path", "str"])
def test_write_creates_exact_canonical_utf8_file_without_bom_or_temp(
    tmp_path: Path,
    use_string: bool,
) -> None:
    configuration = _configuration(
        display_name="  Expedition Ω — Fall 2026  ",
        cohort_display_name="  Orion Cohort  ",
    )
    destination = tmp_path / "class-world.manifest.json"

    result = write_class_world_manifest_file(
        configuration,
        str(destination) if use_string else destination,
    )

    expected = serialize_class_world_manifest(configuration).encode("utf-8")
    assert result == ClassWorldManifestFileWriteResult(len(expected), ())
    assert result.is_written
    assert destination.read_bytes() == expected
    assert not expected.startswith(b"\xef\xbb\xbf")
    assert expected.endswith(b"\n") and not expected.endswith(b"\n\n")
    assert _private_temps(tmp_path, destination) == []


def test_write_atomically_replaces_regular_file_without_backup_or_old_content(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "chosen-name.json"
    destination.write_bytes(b"old content that must disappear")
    configuration = _configuration(display_name="Replacement")

    result = write_class_world_manifest_file(configuration, destination)

    assert result.is_written
    assert destination.read_text(encoding="utf-8") == serialize_class_world_manifest(configuration)
    assert "old content" not in destination.read_text(encoding="utf-8")
    assert sorted(path.name for path in tmp_path.iterdir()) == [destination.name]


@pytest.mark.parametrize("use_string", [False, True], ids=["path", "str"])
def test_read_canonical_manifest_preserves_configuration_and_supplied_plan(
    tmp_path: Path,
    use_string: bool,
) -> None:
    configuration = _configuration(
        display_name="  Expedition Ω — Fall 2026  ",
        cohort_display_name="  Orion Cohort  ",
    )
    path = tmp_path / "manifest.json"
    path.write_bytes(serialize_class_world_manifest(configuration).encode("utf-8"))

    first = read_class_world_manifest_file(
        str(path) if use_string else path,
        configuration.package_set_plan,
    )
    second = read_class_world_manifest_file(path, configuration.package_set_plan)

    assert first.is_read
    assert first.configuration == configuration
    assert first.configuration is not None
    assert first.configuration.package_set_plan is configuration.package_set_plan
    assert first.configuration.display_name == "  Expedition Ω — Fall 2026  "
    assert [pin.package_id for pin in first.configuration.packages] == [
        "nova-character",
        "crystal-lantern",
    ]
    assert first == second


def test_read_accepts_noncanonical_valid_json_and_round_trip_is_stable(tmp_path: Path) -> None:
    configuration = _configuration()
    manifest = json.loads(serialize_class_world_manifest(configuration))
    reordered = {
        "packages": manifest["packages"],
        "cohort": manifest["cohort"],
        "student_api_version": "0.1",
        "engine_version": "1.0.0",
        "class_world": manifest["class_world"],
        "schema_version": "0.1",
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(reordered, separators=(",", ":")), encoding="utf-8")

    result = read_class_world_manifest_file(path, configuration.package_set_plan)

    assert result.configuration == configuration
    assert result.configuration is not None
    assert serialize_class_world_manifest(result.configuration) == serialize_class_world_manifest(
        configuration
    )


def test_configuration_file_configuration_round_trip_and_replacement(tmp_path: Path) -> None:
    destination = tmp_path / "manifest.json"
    first = _configuration(display_name="First World")
    second = _configuration(display_name="Second World")

    assert write_class_world_manifest_file(first, destination).is_written
    assert (
        read_class_world_manifest_file(destination, first.package_set_plan).configuration == first
    )
    assert write_class_world_manifest_file(second, destination).is_written
    read_back = read_class_world_manifest_file(destination, second.package_set_plan)

    assert read_back.configuration == second
    assert b"First World" not in destination.read_bytes()


@pytest.mark.parametrize(
    ("path", "code"),
    [
        (None, ClassWorldManifestFileIssueCode.PATH_REQUIRED),
        ("", ClassWorldManifestFileIssueCode.PATH_REQUIRED),
        (" \n\t", ClassWorldManifestFileIssueCode.PATH_REQUIRED),
        (b"manifest.json", ClassWorldManifestFileIssueCode.PATH_INVALID_TYPE),
        (object(), ClassWorldManifestFileIssueCode.PATH_INVALID_TYPE),
    ],
)
def test_invalid_path_inputs_return_structured_issues(path: object, code: object) -> None:
    read_result = read_class_world_manifest_file(path, _plan())  # type: ignore[arg-type]
    write_result = write_class_world_manifest_file(  # type: ignore[arg-type]
        _configuration(),
        path,
    )

    assert _codes(read_result) == [code]
    assert _codes(write_result) == [code]


def test_invalid_plan_is_preserved_as_a_manifest_issue_without_reading(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"

    result = read_class_world_manifest_file(missing, object())  # type: ignore[arg-type]

    assert result.issues == ()
    assert [issue.code for issue in result.manifest_issues] == [
        ClassWorldManifestIssueCode.PACKAGE_SET_PLAN_REQUIRED
    ]
    assert result.configuration is None


def test_write_requires_existing_directory_parent(tmp_path: Path) -> None:
    missing_parent = tmp_path / "missing" / "manifest.json"
    file_parent = tmp_path / "parent-file"
    file_parent.write_text("file", encoding="utf-8")

    missing = write_class_world_manifest_file(_configuration(), missing_parent)
    not_directory = write_class_world_manifest_file(_configuration(), file_parent / "manifest")

    assert _codes(missing) == [ClassWorldManifestFileIssueCode.PARENT_NOT_FOUND]
    assert _codes(not_directory) == [ClassWorldManifestFileIssueCode.PARENT_NOT_DIRECTORY]
    assert not missing_parent.parent.exists()


def test_read_missing_and_non_regular_paths_are_rejected(tmp_path: Path) -> None:
    missing = read_class_world_manifest_file(tmp_path / "missing.json", _plan())
    directory = read_class_world_manifest_file(tmp_path, _plan())

    assert _codes(missing) == [ClassWorldManifestFileIssueCode.FILE_NOT_FOUND]
    assert _codes(directory) == [ClassWorldManifestFileIssueCode.FILE_NOT_REGULAR]


def test_write_rejects_existing_directory(tmp_path: Path) -> None:
    result = write_class_world_manifest_file(_configuration(), tmp_path)

    assert _codes(result) == [ClassWorldManifestFileIssueCode.DESTINATION_IS_DIRECTORY]


@pytest.mark.parametrize("target_exists", [True, False], ids=["target", "broken"])
def test_read_rejects_final_path_symlinks(tmp_path: Path, target_exists: bool) -> None:
    target = tmp_path / "target.json"
    if target_exists:
        target.write_text("{}", encoding="utf-8")
    link = tmp_path / "manifest.json"
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Symlinks are unavailable on this platform: {error}")

    result = read_class_world_manifest_file(link, _plan())

    assert _codes(result) == [ClassWorldManifestFileIssueCode.FILE_SYMLINK_NOT_ALLOWED]


def test_write_rejects_destination_symlink_without_changing_target(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_bytes(b"target stays unchanged")
    link = tmp_path / "manifest.json"
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Symlinks are unavailable on this platform: {error}")

    result = write_class_world_manifest_file(_configuration(), link)

    assert _codes(result) == [ClassWorldManifestFileIssueCode.FILE_SYMLINK_NOT_ALLOWED]
    assert target.read_bytes() == b"target stays unchanged"
    assert link.is_symlink()


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs are unavailable")
def test_non_regular_fifo_is_rejected_without_opening(tmp_path: Path) -> None:
    fifo = tmp_path / "manifest.pipe"
    os.mkfifo(fifo)

    read_result = read_class_world_manifest_file(fifo, _plan())
    write_result = write_class_world_manifest_file(_configuration(), fifo)

    assert _codes(read_result) == [ClassWorldManifestFileIssueCode.FILE_NOT_REGULAR]
    assert _codes(write_result) == [ClassWorldManifestFileIssueCode.DESTINATION_NOT_REGULAR]


@pytest.mark.parametrize(
    "content",
    [
        b"\xff{}",
        b'{"name":"\xe2\x82"}',
        "{}".encode("utf-16"),
        "{}".encode("utf-32"),
    ],
)
def test_invalid_or_non_utf8_content_is_rejected_without_decode_error(
    tmp_path: Path,
    content: bytes,
) -> None:
    path = tmp_path / "manifest.json"
    path.write_bytes(content)

    result = read_class_world_manifest_file(path, _plan())

    assert _codes(result) == [ClassWorldManifestFileIssueCode.FILE_INVALID_UTF8]


def test_utf8_bom_is_rejected_separately(tmp_path: Path) -> None:
    configuration = _configuration()
    path = tmp_path / "manifest.json"
    path.write_bytes(b"\xef\xbb\xbf" + serialize_class_world_manifest(configuration).encode())

    result = read_class_world_manifest_file(path, configuration.package_set_plan)

    assert _codes(result) == [ClassWorldManifestFileIssueCode.MANIFEST_BOM_NOT_ALLOWED]


def test_empty_file_preserves_parser_manifest_issue(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_bytes(b"")

    result = read_class_world_manifest_file(path, _plan())

    assert result.issues == ()
    assert [issue.code for issue in result.manifest_issues] == [
        ClassWorldManifestIssueCode.MANIFEST_TEXT_REQUIRED
    ]


def test_exact_size_is_read_but_one_byte_over_is_rejected_before_parsing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exact = tmp_path / "exact.json"
    exact.write_bytes(b" " * MAX_CLASS_WORLD_MANIFEST_BYTES)
    exact_result = read_class_world_manifest_file(exact, _plan())
    assert exact_result.issues == ()
    assert [issue.code for issue in exact_result.manifest_issues] == [
        ClassWorldManifestIssueCode.MANIFEST_TEXT_REQUIRED
    ]

    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b" " * (MAX_CLASS_WORLD_MANIFEST_BYTES + 1))

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("oversized content reached JSON parsing")

    monkeypatch.setattr(transport, "parse_class_world_manifest", fail)
    oversized_result = read_class_world_manifest_file(oversized, _plan())

    assert _codes(oversized_result) == [ClassWorldManifestFileIssueCode.FILE_TOO_LARGE]


def test_read_requests_only_limit_plus_one_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "manifest.json"
    path.write_bytes(b"{}")
    sizes: list[int] = []

    class ReadContext(io.BytesIO):
        def read(self, size: int = -1) -> bytes:
            sizes.append(size)
            return b" " * size

        def __enter__(self) -> ReadContext:
            return self

        def __exit__(self, *args: object) -> None:
            self.close()

    monkeypatch.setattr(Path, "open", lambda *args, **kwargs: ReadContext())

    result = read_class_world_manifest_file(path, _plan())

    assert sizes == [MAX_CLASS_WORLD_MANIFEST_BYTES + 1]
    assert _codes(result) == [ClassWorldManifestFileIssueCode.FILE_TOO_LARGE]


def test_multibyte_unicode_boundary_is_measured_in_bytes(tmp_path: Path) -> None:
    configuration = _configuration(display_name="Expedition Ω")
    canonical = serialize_class_world_manifest(configuration).encode("utf-8")
    exact = tmp_path / "exact.json"
    exact.write_bytes(b" " * (MAX_CLASS_WORLD_MANIFEST_BYTES - len(canonical)) + canonical)

    exact_result = read_class_world_manifest_file(exact, configuration.package_set_plan)
    assert exact_result.configuration == configuration

    over = tmp_path / "over.json"
    over.write_bytes(b" " + exact.read_bytes())
    assert _codes(read_class_world_manifest_file(over, configuration.package_set_plan)) == [
        ClassWorldManifestFileIssueCode.FILE_TOO_LARGE
    ]


def test_writer_accepts_exact_multibyte_byte_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "manifest.json"
    monkeypatch.setattr(
        transport,
        "serialize_class_world_manifest",
        lambda value: "é" * (MAX_CLASS_WORLD_MANIFEST_BYTES // 2),
    )

    result = write_class_world_manifest_file(_configuration(), destination)

    assert result == ClassWorldManifestFileWriteResult(MAX_CLASS_WORLD_MANIFEST_BYTES, ())
    assert destination.stat().st_size == MAX_CLASS_WORLD_MANIFEST_BYTES


def test_reader_does_not_serialize_and_writer_does_not_parse_or_read_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _configuration()
    source = tmp_path / "source.json"
    source.write_bytes(serialize_class_world_manifest(configuration).encode("utf-8"))

    monkeypatch.setattr(
        transport,
        "serialize_class_world_manifest",
        lambda value: (_ for _ in ()).throw(AssertionError("reader serialized")),
    )
    assert read_class_world_manifest_file(source, configuration.package_set_plan).is_read

    monkeypatch.undo()
    destination = tmp_path / "destination.json"
    monkeypatch.setattr(
        transport,
        "parse_class_world_manifest",
        lambda *args: (_ for _ in ()).throw(AssertionError("writer parsed")),
    )
    monkeypatch.setattr(
        Path,
        "open",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("writer read back")),
    )

    result = write_class_world_manifest_file(configuration, destination)

    assert result.is_written
    assert destination.stat().st_size == result.bytes_written


def test_read_open_failure_is_structured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "manifest.json"
    path.write_bytes(b"{}")
    monkeypatch.setattr(
        Path,
        "open",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("injected read failure")),
    )

    result = read_class_world_manifest_file(path, _plan())

    assert _codes(result) == [ClassWorldManifestFileIssueCode.FILE_READ_FAILED]


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (lambda text: "{", ClassWorldManifestIssueCode.MANIFEST_INVALID_JSON),
        (
            lambda text: text.replace(
                '"schema_version": "0.1"',
                '"schema_version": "0.1", "schema_version": "0.1"',
            ),
            ClassWorldManifestIssueCode.MANIFEST_DUPLICATE_KEY,
        ),
        (
            lambda text: text.replace(
                '"schema_version": "0.1"',
                '"schema_version": "0.1", "unknown": true',
            ),
            ClassWorldManifestIssueCode.MANIFEST_FIELD_UNKNOWN,
        ),
        (
            _reverse_manifest_packages,
            ClassWorldManifestIssueCode.MANIFEST_PACKAGE_ORDER_MISMATCH,
        ),
    ],
)
def test_manifest_parser_issues_are_preserved_without_transport_issue(
    tmp_path: Path,
    mutation: object,
    expected_code: ClassWorldManifestIssueCode,
) -> None:
    configuration = _configuration()
    text = mutation(serialize_class_world_manifest(configuration))  # type: ignore[operator]
    path = tmp_path / "manifest.json"
    path.write_text(text, encoding="utf-8")
    direct = parse_class_world_manifest(text, configuration.package_set_plan)

    result = read_class_world_manifest_file(path, configuration.package_set_plan)

    assert result.issues == ()
    assert result.manifest_issues == direct.issues
    assert expected_code in [issue.code for issue in result.manifest_issues]
    assert result.configuration is None


def test_invalid_configuration_and_encoding_failure_preserve_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "manifest.json"
    destination.write_bytes(b"original")
    invalid = replace(_configuration(), class_world_id="Bad World")

    invalid_result = write_class_world_manifest_file(invalid, destination)
    assert _codes(invalid_result) == [ClassWorldManifestFileIssueCode.MANIFEST_INVALID]
    assert destination.read_bytes() == b"original"
    assert _private_temps(tmp_path, destination) == []

    monkeypatch.setattr(transport, "serialize_class_world_manifest", lambda value: "\ud800")
    encoding_result = write_class_world_manifest_file(_configuration(), destination)
    assert _codes(encoding_result) == [ClassWorldManifestFileIssueCode.FILE_INVALID_UTF8]
    assert destination.read_bytes() == b"original"
    assert _private_temps(tmp_path, destination) == []


def test_oversized_write_preserves_destination_and_creates_no_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "manifest.json"
    destination.write_bytes(b"original")
    monkeypatch.setattr(
        transport,
        "serialize_class_world_manifest",
        lambda value: "é" * ((MAX_CLASS_WORLD_MANIFEST_BYTES // 2) + 1),
    )

    result = write_class_world_manifest_file(_configuration(), destination)

    assert _codes(result) == [ClassWorldManifestFileIssueCode.FILE_TOO_LARGE]
    assert destination.read_bytes() == b"original"
    assert _private_temps(tmp_path, destination) == []


def test_temporary_creation_failure_preserves_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "manifest.json"
    destination.write_bytes(b"original")

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("injected create failure")

    monkeypatch.setattr(transport.tempfile, "mkstemp", fail)

    result = write_class_world_manifest_file(_configuration(), destination)

    assert _codes(result) == [ClassWorldManifestFileIssueCode.TEMP_FILE_CREATE_FAILED]
    assert destination.read_bytes() == b"original"


class _FailureStream:
    def __init__(self, stream: object, phase: str) -> None:
        self._stream = stream
        self._phase = phase

    def write(self, content: object) -> int:
        if self._phase == "write":
            raise OSError("injected write failure")
        return self._stream.write(content)  # type: ignore[no-any-return, union-attr]

    def flush(self) -> None:
        if self._phase == "flush":
            raise OSError("injected flush failure")
        self._stream.flush()  # type: ignore[union-attr]

    def fileno(self) -> int:
        return self._stream.fileno()  # type: ignore[no-any-return, union-attr]

    def close(self) -> None:
        self._stream.close()  # type: ignore[union-attr]


@pytest.mark.parametrize(
    ("phase", "code"),
    [
        ("write", ClassWorldManifestFileIssueCode.FILE_WRITE_FAILED),
        ("flush", ClassWorldManifestFileIssueCode.FILE_FLUSH_FAILED),
        ("fsync", ClassWorldManifestFileIssueCode.FILE_SYNC_FAILED),
        ("replace", ClassWorldManifestFileIssueCode.ATOMIC_REPLACE_FAILED),
    ],
)
def test_atomic_failures_preserve_old_destination_and_clean_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
    code: ClassWorldManifestFileIssueCode,
) -> None:
    destination = tmp_path / "manifest.json"
    destination.write_bytes(b"original")
    real_fdopen = transport.os.fdopen

    if phase in {"write", "flush"}:
        monkeypatch.setattr(
            transport.os,
            "fdopen",
            lambda *args, **kwargs: _FailureStream(real_fdopen(*args, **kwargs), phase),
        )
    elif phase == "fsync":
        monkeypatch.setattr(
            transport.os,
            "fsync",
            lambda descriptor: (_ for _ in ()).throw(OSError("injected sync failure")),
        )
    else:
        monkeypatch.setattr(
            transport.os,
            "replace",
            lambda source, target: (_ for _ in ()).throw(OSError("injected replace failure")),
        )

    result = write_class_world_manifest_file(_configuration(), destination)

    assert _codes(result) == [code]
    assert destination.read_bytes() == b"original"
    assert _private_temps(tmp_path, destination) == []


def test_cleanup_failure_reports_original_then_cleanup_without_temp_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "manifest.json"
    destination.write_bytes(b"original")

    monkeypatch.setattr(
        transport.os,
        "replace",
        lambda source, target: (_ for _ in ()).throw(OSError("injected replace failure")),
    )
    monkeypatch.setattr(
        transport.Path,
        "unlink",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("injected cleanup failure")),
    )

    result = write_class_world_manifest_file(_configuration(), destination)

    assert _codes(result) == [
        ClassWorldManifestFileIssueCode.ATOMIC_REPLACE_FAILED,
        ClassWorldManifestFileIssueCode.TEMP_FILE_CLEANUP_FAILED,
    ]
    assert destination.read_bytes() == b"original"
    assert all(destination.name not in issue.message for issue in result.issues)
    assert all("0x" not in issue.message for issue in result.issues)


def test_writer_wrong_type_retains_serializer_type_error(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="ClassWorldConfiguration"):
        write_class_world_manifest_file(object(), tmp_path / "manifest.json")  # type: ignore[arg-type]


def test_transport_models_are_deeply_immutable_and_use_tuples() -> None:
    issue = ClassWorldManifestFileIssue(
        ClassWorldManifestFileIssueCode.FILE_NOT_FOUND,
        "missing",
        "path",
    )
    read_result = ClassWorldManifestFileReadResult(None, (issue,), ())
    write_result = ClassWorldManifestFileWriteResult(0, (issue,))

    assert isinstance(read_result.issues, tuple)
    assert isinstance(read_result.manifest_issues, tuple)
    assert isinstance(write_result.issues, tuple)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        issue.location = "changed"  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        read_result.configuration = _configuration()  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        write_result.bytes_written = 10  # type: ignore[misc]


def test_transport_public_exports_preserve_earlier_pipeline() -> None:
    import explore.packages as packages

    expected = {
        "read_class_world_manifest_file",
        "write_class_world_manifest_file",
        "ClassWorldManifestFileReadResult",
        "ClassWorldManifestFileWriteResult",
        "ClassWorldManifestFileIssue",
        "ClassWorldManifestFileIssueCode",
        "MAX_CLASS_WORLD_MANIFEST_BYTES",
        "serialize_class_world_manifest",
        "parse_class_world_manifest",
        "build_class_world_configuration",
        "build_package_set_plan",
        "apply_package_set_plan",
        "load_explorer_package",
        "validate_explorer_package",
    }

    assert MAX_CLASS_WORLD_MANIFEST_BYTES == 1 * 1024 * 1024
    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)


def test_transport_source_stays_inside_local_file_boundary() -> None:
    source = Path(transport.__file__).read_text(encoding="utf-8")
    forbidden = (
        "import hashlib",
        "import hmac",
        "import yaml",
        "import pygame",
        "from engine",
        "load_explorer_package",
        "validate_explorer_package",
        "build_package_set_plan",
        "apply_package_set_plan",
        "StudentAPIWorldRegistrationTarget",
        "requests",
        "httpx",
    )

    assert all(term not in source for term in forbidden)
