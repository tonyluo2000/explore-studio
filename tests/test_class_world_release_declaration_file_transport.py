"""Behavior tests for release-declaration file transport v0.1."""

from __future__ import annotations

import io
import json
import os
import stat
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Any

import pytest

from explore.packages import (
    MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES,
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_TRANSPORT_CONTRACT_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldCohort,
    ClassWorldConfiguration,
    ClassWorldConfigurationSpec,
    ClassWorldPackagePin,
    ClassWorldReleaseDeclaration,
    ClassWorldReleaseDeclarationFileIssue,
    ClassWorldReleaseDeclarationFileIssueCode,
    ClassWorldReleaseDeclarationFileReadResult,
    ClassWorldReleaseDeclarationFileWriteResult,
    ClassWorldReleaseDeclarationIssueCode,
    ClassWorldReleaseDeclarationSerializationIssueCode,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    build_class_world_configuration,
    build_class_world_release_declaration,
    parse_class_world_release_declaration,
    read_class_world_release_declaration_file,
    serialize_class_world_release_declaration,
    write_class_world_release_declaration_file,
)
from explore.packages import class_world_release_declaration_file_transport as transport


def _provenance(package_id: str, package_version: str) -> PackageProvenance:
    return PackageProvenance(package_id, package_version, "0.1")


def _selected(
    package_id: str,
    package_version: str,
    entry: CharacterRegistration | WorldObjectRegistration,
) -> SelectedPackagePlan:
    provenance = _provenance(package_id, package_version)
    adjusted = replace(entry, provenance=provenance)
    return SelectedPackagePlan(
        package_id,
        package_version,
        provenance,
        StudentAPIRegistrationPlan(provenance, (adjusted,)),
    )


def _configuration() -> ClassWorldConfiguration:
    first_id = "zeta-character"
    second_id = "alpha-lantern"
    packages = (
        _selected(
            first_id,
            "2.1.0-beta.1+class",
            CharacterRegistration(
                f"{first_id}:hero",
                "hero",
                _provenance(first_id, "2.1.0-beta.1+class"),
                CharacterRegistrationSpec("Exploratrice", 10, 20, "gold"),
                None,
            ),
        ),
        _selected(
            second_id,
            "1.0.0",
            WorldObjectRegistration(
                f"{second_id}:lantern",
                "lantern",
                _provenance(second_id, "1.0.0"),
                WorldObjectRegistrationSpec("Lanterne", 30, 40, "green", "Regardez.", "Trouvée!"),
                None,
            ),
        ),
    )
    plan = PackageSetPlan(
        "0.1",
        packages,
        tuple(entry for package in packages for entry in package.registration_plan.entries),
    )
    result = build_class_world_configuration(
        ClassWorldConfigurationSpec(
            "0.1",
            "expedition-orion-fall-2026",
            "Expédition Orion — Automne 2026 🚀",
            "3.2.1",
            "1.4.0",
            "0.1",
            ClassWorldCohort("expedition-orion", "Expédition Orion 🚀"),
            tuple(
                ClassWorldPackagePin(package.package_id, package.package_version)
                for package in packages
            ),
        ),
        plan,
    )
    assert result.configuration is not None
    return result.configuration


def _declaration(
    configuration: ClassWorldConfiguration | None = None,
) -> ClassWorldReleaseDeclaration:
    result = build_class_world_release_declaration(
        configuration or _configuration(),
        release_id="spring-showcase",
        release_version="1.2.3-rc.1+school",
    )
    assert result.declaration is not None
    return result.declaration


def _codes(
    result: (
        ClassWorldReleaseDeclarationFileReadResult | ClassWorldReleaseDeclarationFileWriteResult
    ),
) -> list[ClassWorldReleaseDeclarationFileIssueCode]:
    return [issue.code for issue in result.issues]


def _private_temps(parent: Path, destination: Path) -> list[Path]:
    return list(parent.glob(f".{destination.name}.*.tmp"))


@pytest.mark.parametrize("use_string", [False, True], ids=["path", "str"])
def test_write_creates_exact_canonical_utf8_without_bom_or_temp(
    tmp_path: Path,
    use_string: bool,
) -> None:
    declaration = _declaration()
    destination = tmp_path / "class-world.release.json"

    result = write_class_world_release_declaration_file(
        declaration,
        str(destination) if use_string else destination,
    )

    expected = serialize_class_world_release_declaration(declaration).encode("utf-8")
    assert result == ClassWorldReleaseDeclarationFileWriteResult(len(expected), ())
    assert result.is_written
    assert destination.read_bytes() == expected
    assert "Expédition" not in destination.read_text(encoding="utf-8")
    assert not expected.startswith(b"\xef\xbb\xbf")
    assert expected.endswith(b"\n") and not expected.endswith(b"\n\n")
    assert _private_temps(tmp_path, destination) == []


def test_write_atomically_replaces_regular_file_without_backup(tmp_path: Path) -> None:
    destination = tmp_path / "chosen.json"
    destination.write_bytes(b"old content")
    declaration = _declaration()

    result = write_class_world_release_declaration_file(declaration, destination)

    assert result.is_written
    assert destination.read_bytes() == serialize_class_world_release_declaration(
        declaration
    ).encode("utf-8")
    assert sorted(path.name for path in tmp_path.iterdir()) == [destination.name]


@pytest.mark.parametrize("use_string", [False, True], ids=["path", "str"])
def test_read_canonical_preserves_exact_configuration_and_package_order(
    tmp_path: Path,
    use_string: bool,
) -> None:
    declaration = _declaration()
    path = tmp_path / "class-world.release.json"
    path.write_bytes(serialize_class_world_release_declaration(declaration).encode("utf-8"))

    first = read_class_world_release_declaration_file(
        str(path) if use_string else path,
        declaration.configuration,
    )
    second = read_class_world_release_declaration_file(path, declaration.configuration)

    assert first.is_read
    assert first.declaration == declaration
    assert first.declaration is not None
    assert first.declaration.configuration is declaration.configuration
    assert [pin.package_id for pin in first.declaration.provenance.package_pins] == [
        "zeta-character",
        "alpha-lantern",
    ]
    assert first == second


@pytest.mark.parametrize(
    "transform",
    [
        lambda value: json.dumps(value, separators=(",", ":"), ensure_ascii=False),
        lambda value: json.dumps(
            {
                "provenance": value["provenance"],
                "identity": value["identity"],
                "schema_version": value["schema_version"],
            },
            ensure_ascii=False,
        ),
        lambda value: json.dumps(value, ensure_ascii=True),
        lambda value: " \n" + json.dumps(value, ensure_ascii=False) + "\t",
    ],
    ids=["compact", "reordered", "escaped-unicode", "whitespace"],
)
def test_read_accepts_valid_noncanonical_json_and_canonicalizes(
    tmp_path: Path,
    transform: Any,
) -> None:
    declaration = _declaration()
    value = json.loads(serialize_class_world_release_declaration(declaration))
    path = tmp_path / "declaration.json"
    path.write_text(transform(value), encoding="utf-8")

    result = read_class_world_release_declaration_file(path, declaration.configuration)

    assert result.declaration == declaration
    assert result.declaration is not None
    assert serialize_class_world_release_declaration(result.declaration) == (
        serialize_class_world_release_declaration(declaration)
    )


def test_declaration_file_round_trip_and_canonical_stability(tmp_path: Path) -> None:
    declaration = _declaration()
    path = tmp_path / "class-world.release.json"

    written = write_class_world_release_declaration_file(declaration, path)
    read = read_class_world_release_declaration_file(path, declaration.configuration)

    assert written.is_written and read.is_read
    assert read.declaration == declaration
    assert read.declaration is not None
    assert read.declaration.configuration is declaration.configuration
    assert serialize_class_world_release_declaration(read.declaration).encode("utf-8") == (
        path.read_bytes()
    )


@pytest.mark.parametrize(
    ("path", "code"),
    [
        (None, ClassWorldReleaseDeclarationFileIssueCode.PATH_REQUIRED),
        ("", ClassWorldReleaseDeclarationFileIssueCode.PATH_REQUIRED),
        (" \n\t", ClassWorldReleaseDeclarationFileIssueCode.PATH_REQUIRED),
        (b"release.json", ClassWorldReleaseDeclarationFileIssueCode.PATH_INVALID_TYPE),
        (1, ClassWorldReleaseDeclarationFileIssueCode.PATH_INVALID_TYPE),
        (True, ClassWorldReleaseDeclarationFileIssueCode.PATH_INVALID_TYPE),
        (object(), ClassWorldReleaseDeclarationFileIssueCode.PATH_INVALID_TYPE),
    ],
)
def test_invalid_path_inputs_return_structured_issues(path: object, code: object) -> None:
    read = read_class_world_release_declaration_file(  # type: ignore[arg-type]
        path, _configuration()
    )
    write = write_class_world_release_declaration_file(  # type: ignore[arg-type]
        _declaration(), path
    )

    assert _codes(read) == [code]
    assert _codes(write) == [code]


def test_write_requires_existing_directory_parent(tmp_path: Path) -> None:
    missing = tmp_path / "missing" / "release.json"
    file_parent = tmp_path / "file-parent"
    file_parent.write_text("file", encoding="utf-8")

    missing_result = write_class_world_release_declaration_file(_declaration(), missing)
    file_result = write_class_world_release_declaration_file(
        _declaration(), file_parent / "release.json"
    )

    assert _codes(missing_result) == [ClassWorldReleaseDeclarationFileIssueCode.PARENT_NOT_FOUND]
    assert _codes(file_result) == [ClassWorldReleaseDeclarationFileIssueCode.PARENT_NOT_DIRECTORY]
    assert not missing.parent.exists()


def test_missing_directory_and_device_paths_are_rejected(tmp_path: Path) -> None:
    missing = read_class_world_release_declaration_file(tmp_path / "missing.json", _configuration())
    directory_read = read_class_world_release_declaration_file(tmp_path, _configuration())
    directory_write = write_class_world_release_declaration_file(_declaration(), tmp_path)

    assert _codes(missing) == [ClassWorldReleaseDeclarationFileIssueCode.FILE_NOT_FOUND]
    assert _codes(directory_read) == [ClassWorldReleaseDeclarationFileIssueCode.FILE_NOT_REGULAR]
    assert _codes(directory_write) == [
        ClassWorldReleaseDeclarationFileIssueCode.DESTINATION_IS_DIRECTORY
    ]
    if Path("/dev/null").exists():
        assert _codes(read_class_world_release_declaration_file("/dev/null", _configuration())) == [
            ClassWorldReleaseDeclarationFileIssueCode.FILE_NOT_REGULAR
        ]
        assert _codes(write_class_world_release_declaration_file(_declaration(), "/dev/null")) == [
            ClassWorldReleaseDeclarationFileIssueCode.DESTINATION_NOT_REGULAR
        ]


@pytest.mark.parametrize(
    ("target_kind", "target_exists"),
    [("file", True), ("file", False), ("directory", True)],
    ids=["file", "broken", "directory"],
)
def test_final_path_symlinks_are_rejected_for_read_and_write(
    tmp_path: Path,
    target_kind: str,
    target_exists: bool,
) -> None:
    target = tmp_path / "target"
    if target_exists:
        if target_kind == "directory":
            target.mkdir()
        else:
            target.write_text("{}", encoding="utf-8")
    link = tmp_path / "release.json"
    try:
        link.symlink_to(target, target_is_directory=target_kind == "directory")
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Symlinks unavailable: {error}")

    read = read_class_world_release_declaration_file(link, _configuration())
    write = write_class_world_release_declaration_file(_declaration(), link)

    assert _codes(read) == [ClassWorldReleaseDeclarationFileIssueCode.FILE_SYMLINK_NOT_ALLOWED]
    assert _codes(write) == [ClassWorldReleaseDeclarationFileIssueCode.FILE_SYMLINK_NOT_ALLOWED]
    assert link.is_symlink()


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs unavailable")
def test_fifo_is_rejected_without_opening(tmp_path: Path) -> None:
    fifo = tmp_path / "release.pipe"
    os.mkfifo(fifo)

    read = read_class_world_release_declaration_file(fifo, _configuration())
    write = write_class_world_release_declaration_file(_declaration(), fifo)

    assert _codes(read) == [ClassWorldReleaseDeclarationFileIssueCode.FILE_NOT_REGULAR]
    assert _codes(write) == [ClassWorldReleaseDeclarationFileIssueCode.DESTINATION_NOT_REGULAR]


def test_socket_metadata_is_rejected_without_opening(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "release.sock"
    monkeypatch.setattr(
        Path,
        "lstat",
        lambda self: os.stat_result((stat.S_IFSOCK, 0, 0, 0, 0, 0, 0, 0, 0, 0)),
    )

    assert _codes(read_class_world_release_declaration_file(path, _configuration())) == [
        ClassWorldReleaseDeclarationFileIssueCode.FILE_NOT_REGULAR
    ]
    assert _codes(write_class_world_release_declaration_file(_declaration(), path)) == [
        ClassWorldReleaseDeclarationFileIssueCode.DESTINATION_NOT_REGULAR
    ]


@pytest.mark.parametrize(
    "content",
    [
        b"\xff{}",
        b'{"identity":"\xe2\x82"}',
        "{}".encode("utf-16"),
        "{}".encode("utf-32"),
    ],
    ids=["invalid", "truncated", "utf16", "utf32"],
)
def test_invalid_or_non_utf8_content_is_rejected(tmp_path: Path, content: bytes) -> None:
    path = tmp_path / "release.json"
    path.write_bytes(content)

    result = read_class_world_release_declaration_file(path, _configuration())

    assert _codes(result) == [ClassWorldReleaseDeclarationFileIssueCode.FILE_INVALID_UTF8]


@pytest.mark.parametrize("suffix", [b"", b"{}"], ids=["bom-only", "bom-json"])
def test_utf8_bom_is_rejected_separately(tmp_path: Path, suffix: bytes) -> None:
    path = tmp_path / "release.json"
    path.write_bytes(b"\xef\xbb\xbf" + suffix)

    result = read_class_world_release_declaration_file(path, _configuration())

    assert _codes(result) == [ClassWorldReleaseDeclarationFileIssueCode.DECLARATION_BOM_NOT_ALLOWED]


def test_valid_multibyte_unicode_reads_successfully(tmp_path: Path) -> None:
    declaration = _declaration()
    path = tmp_path / "release.json"
    text = serialize_class_world_release_declaration(declaration).replace(
        '"spring-showcase"', '"spring-\\u0073howcase"'
    )
    path.write_text(text, encoding="utf-8")

    result = read_class_world_release_declaration_file(path, declaration.configuration)

    assert result.declaration == declaration


def test_exact_limit_is_parsed_but_limit_plus_one_bypasses_parser(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declaration = _declaration()
    canonical = serialize_class_world_release_declaration(declaration).encode("utf-8")
    exact = tmp_path / "exact.json"
    exact.write_bytes(
        b" " * (MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES - len(canonical)) + canonical
    )

    exact_result = read_class_world_release_declaration_file(exact, declaration.configuration)
    assert exact_result.declaration == declaration

    over = tmp_path / "over.json"
    over.write_bytes(b" " + exact.read_bytes())

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("oversized content reached parser")

    monkeypatch.setattr(transport, "parse_class_world_release_declaration", fail)
    over_result = read_class_world_release_declaration_file(over, declaration.configuration)
    assert _codes(over_result) == [ClassWorldReleaseDeclarationFileIssueCode.FILE_TOO_LARGE]


def test_much_larger_file_is_bounded_to_limit_plus_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "release.json"
    path.write_bytes(b"{}")
    requested: list[int] = []

    class ReadContext(io.BytesIO):
        def read(self, size: int = -1) -> bytes:
            requested.append(size)
            return b" " * size

        def __enter__(self) -> ReadContext:
            return self

        def __exit__(self, *args: object) -> None:
            self.close()

    monkeypatch.setattr(Path, "open", lambda *args, **kwargs: ReadContext())

    result = read_class_world_release_declaration_file(path, _configuration())

    assert requested == [MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES + 1]
    assert _codes(result) == [ClassWorldReleaseDeclarationFileIssueCode.FILE_TOO_LARGE]


def test_writer_size_limit_uses_multibyte_utf8_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exact = tmp_path / "exact.json"
    monkeypatch.setattr(
        transport,
        "serialize_class_world_release_declaration",
        lambda value: "é" * (MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES // 2),
    )
    exact_result = write_class_world_release_declaration_file(_declaration(), exact)
    assert exact_result.bytes_written == MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES
    assert exact.stat().st_size == MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES

    over = tmp_path / "over.json"
    monkeypatch.setattr(
        transport,
        "serialize_class_world_release_declaration",
        lambda value: "é" * ((MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES // 2) + 1),
    )
    over.write_bytes(b"original")
    over_result = write_class_world_release_declaration_file(_declaration(), over)
    assert _codes(over_result) == [ClassWorldReleaseDeclarationFileIssueCode.FILE_TOO_LARGE]
    assert over.read_bytes() == b"original"
    assert _private_temps(tmp_path, over) == []


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda text: "{", ClassWorldReleaseDeclarationSerializationIssueCode.JSON_INVALID),
        (
            lambda text: text.replace(
                '"schema_version": "0.1"',
                '"schema_version": "0.1", "schema_version": "0.1"',
            ),
            ClassWorldReleaseDeclarationSerializationIssueCode.JSON_DUPLICATE_KEY,
        ),
        (
            lambda text: text.replace(
                '"schema_version": "0.1"',
                '"schema_version": "0.1", "unknown": "field"',
            ),
            ClassWorldReleaseDeclarationSerializationIssueCode.FIELD_UNKNOWN,
        ),
        (
            lambda text: json.dumps(
                {
                    **json.loads(text),
                    "provenance": {
                        **json.loads(text)["provenance"],
                        "packages": list(reversed(json.loads(text)["provenance"]["packages"])),
                    },
                }
            ),
            ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_ID_MISMATCH,
        ),
        (
            lambda text: text.replace('"version": "1.0.0"', '"version": "9.9.9"'),
            ClassWorldReleaseDeclarationSerializationIssueCode.PACKAGE_VERSION_MISMATCH,
        ),
    ],
    ids=["malformed", "duplicate", "unknown", "package-order", "package-version"],
)
def test_serialization_issues_are_preserved_exactly(
    tmp_path: Path,
    mutation: Any,
    expected: ClassWorldReleaseDeclarationSerializationIssueCode,
) -> None:
    declaration = _declaration()
    text = mutation(serialize_class_world_release_declaration(declaration))
    path = tmp_path / "release.json"
    path.write_text(text, encoding="utf-8")
    direct = parse_class_world_release_declaration(text, declaration.configuration)

    result = read_class_world_release_declaration_file(path, declaration.configuration)

    assert result.declaration is None
    assert result.issues == ()
    assert result.serialization_issues == direct.issues
    assert expected in [issue.code for issue in result.serialization_issues]
    assert result.declaration_issues == ()


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("release_id", "Bad/ID", ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID),
        (
            "release_version",
            "01.0",
            ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID,
        ),
    ],
)
def test_builder_issues_are_preserved_exactly(
    tmp_path: Path,
    field: str,
    value: str,
    expected: ClassWorldReleaseDeclarationIssueCode,
) -> None:
    declaration = _declaration()
    body = json.loads(serialize_class_world_release_declaration(declaration))
    body["identity"][field] = value
    text = json.dumps(body)
    path = tmp_path / "release.json"
    path.write_text(text, encoding="utf-8")
    direct = parse_class_world_release_declaration(text, declaration.configuration)

    result = read_class_world_release_declaration_file(path, declaration.configuration)

    assert result.declaration is None
    assert result.issues == ()
    assert result.serialization_issues == ()
    assert result.declaration_issues == direct.declaration_issues
    assert [issue.code for issue in result.declaration_issues] == [expected]


def test_reader_delegates_wrong_configuration_to_parser(tmp_path: Path) -> None:
    declaration = _declaration()
    path = tmp_path / "release.json"
    path.write_text(serialize_class_world_release_declaration(declaration), encoding="utf-8")

    result = read_class_world_release_declaration_file(path, object())  # type: ignore[arg-type]

    assert result.issues == ()
    assert result.serialization_issues == ()
    assert [issue.code for issue in result.declaration_issues] == [
        ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID_TYPE
    ]


def test_reader_does_not_serialize_and_writer_does_not_parse_or_read_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declaration = _declaration()
    source = tmp_path / "source.json"
    source.write_text(serialize_class_world_release_declaration(declaration), encoding="utf-8")
    monkeypatch.setattr(
        transport,
        "serialize_class_world_release_declaration",
        lambda value: (_ for _ in ()).throw(AssertionError("reader serialized")),
    )
    assert read_class_world_release_declaration_file(source, declaration.configuration).is_read

    monkeypatch.undo()
    destination = tmp_path / "destination.json"
    monkeypatch.setattr(
        transport,
        "parse_class_world_release_declaration",
        lambda *args: (_ for _ in ()).throw(AssertionError("writer parsed")),
    )
    monkeypatch.setattr(
        Path,
        "open",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("writer read back")),
    )
    result = write_class_world_release_declaration_file(declaration, destination)
    assert result.is_written


def test_read_open_failure_is_structured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "release.json"
    path.write_bytes(b"{}")
    monkeypatch.setattr(
        Path,
        "open",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("injected")),
    )

    result = read_class_world_release_declaration_file(path, _configuration())

    assert _codes(result) == [ClassWorldReleaseDeclarationFileIssueCode.FILE_READ_FAILED]


def test_invalid_declaration_and_encoding_failure_preserve_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "release.json"
    destination.write_bytes(b"original")
    invalid = replace(_declaration(), identity=replace(_declaration().identity, release_id="Bad"))

    invalid_result = write_class_world_release_declaration_file(invalid, destination)
    assert _codes(invalid_result) == [ClassWorldReleaseDeclarationFileIssueCode.DECLARATION_INVALID]
    assert destination.read_bytes() == b"original"
    assert _private_temps(tmp_path, destination) == []

    monkeypatch.setattr(
        transport, "serialize_class_world_release_declaration", lambda value: "\ud800"
    )
    encoding_result = write_class_world_release_declaration_file(_declaration(), destination)
    assert _codes(encoding_result) == [ClassWorldReleaseDeclarationFileIssueCode.FILE_INVALID_UTF8]
    assert destination.read_bytes() == b"original"
    assert _private_temps(tmp_path, destination) == []


def test_temp_creation_and_fdopen_failures_preserve_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "release.json"
    destination.write_bytes(b"original")
    monkeypatch.setattr(
        transport.tempfile,
        "mkstemp",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("create")),
    )
    create_result = write_class_world_release_declaration_file(_declaration(), destination)
    assert _codes(create_result) == [
        ClassWorldReleaseDeclarationFileIssueCode.TEMP_FILE_CREATE_FAILED
    ]
    assert destination.read_bytes() == b"original"

    monkeypatch.undo()
    monkeypatch.setattr(
        transport.os,
        "fdopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("fdopen")),
    )
    open_result = write_class_world_release_declaration_file(_declaration(), destination)
    assert _codes(open_result) == [
        ClassWorldReleaseDeclarationFileIssueCode.TEMP_FILE_CREATE_FAILED
    ]
    assert destination.read_bytes() == b"original"
    assert _private_temps(tmp_path, destination) == []


class _FailureStream:
    def __init__(self, stream: Any, phase: str) -> None:
        self._stream = stream
        self._phase = phase
        self.write_calls = 0

    def write(self, content: Any) -> int | None:
        self.write_calls += 1
        if self._phase == "write":
            raise OSError("write")
        if self._phase == "zero":
            return 0
        if self._phase == "none":
            return None
        if self._phase == "partial" and len(content) > 1:
            return self._stream.write(content[: max(1, len(content) // 3)])
        return self._stream.write(content)

    def flush(self) -> None:
        if self._phase == "flush":
            raise OSError("flush")
        self._stream.flush()

    def fileno(self) -> int:
        return self._stream.fileno()

    def close(self) -> None:
        self._stream.close()
        if self._phase == "close":
            raise OSError("close")


@pytest.mark.parametrize("destination_exists", [False, True], ids=["missing", "existing"])
@pytest.mark.parametrize(
    ("phase", "expected"),
    [
        ("write", ClassWorldReleaseDeclarationFileIssueCode.FILE_WRITE_FAILED),
        ("zero", ClassWorldReleaseDeclarationFileIssueCode.FILE_WRITE_FAILED),
        ("none", ClassWorldReleaseDeclarationFileIssueCode.FILE_WRITE_FAILED),
        ("flush", ClassWorldReleaseDeclarationFileIssueCode.FILE_FLUSH_FAILED),
        ("fsync", ClassWorldReleaseDeclarationFileIssueCode.FILE_SYNC_FAILED),
        ("close", ClassWorldReleaseDeclarationFileIssueCode.FILE_WRITE_FAILED),
        ("replace", ClassWorldReleaseDeclarationFileIssueCode.ATOMIC_REPLACE_FAILED),
    ],
)
def test_injected_atomic_failures_preserve_destination_and_clean_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    destination_exists: bool,
    phase: str,
    expected: ClassWorldReleaseDeclarationFileIssueCode,
) -> None:
    destination = tmp_path / "release.json"
    if destination_exists:
        destination.write_bytes(b"original")
    real_fdopen = transport.os.fdopen
    if phase in {"write", "zero", "none", "flush", "close"}:
        monkeypatch.setattr(
            transport.os,
            "fdopen",
            lambda *args, **kwargs: _FailureStream(real_fdopen(*args, **kwargs), phase),
        )
    elif phase == "fsync":
        monkeypatch.setattr(
            transport.os,
            "fsync",
            lambda descriptor: (_ for _ in ()).throw(OSError("fsync")),
        )
    else:
        monkeypatch.setattr(
            transport.os,
            "replace",
            lambda source, target: (_ for _ in ()).throw(OSError("replace")),
        )

    result = write_class_world_release_declaration_file(_declaration(), destination)

    assert result.bytes_written == 0
    assert _codes(result) == [expected]
    if destination_exists:
        assert destination.read_bytes() == b"original"
    else:
        assert not destination.exists()
    assert _private_temps(tmp_path, destination) == []


def test_partial_writes_continue_until_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "release.json"
    real_fdopen = transport.os.fdopen
    wrappers: list[_FailureStream] = []

    def partial(*args: Any, **kwargs: Any) -> _FailureStream:
        wrapper = _FailureStream(real_fdopen(*args, **kwargs), "partial")
        wrappers.append(wrapper)
        return wrapper

    monkeypatch.setattr(transport.os, "fdopen", partial)

    result = write_class_world_release_declaration_file(_declaration(), destination)

    assert result.is_written
    assert wrappers[0].write_calls > 1
    assert destination.stat().st_size == result.bytes_written


def test_successful_write_orders_write_flush_fsync_close_then_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "release.json"
    events: list[str] = []
    real_fdopen = transport.os.fdopen
    real_fsync = transport.os.fsync
    real_replace = transport.os.replace

    class OrderedStream:
        def __init__(self, stream: Any) -> None:
            self._stream = stream

        def write(self, content: Any) -> int:
            events.append("write")
            return self._stream.write(content)

        def flush(self) -> None:
            events.append("flush")
            self._stream.flush()

        def fileno(self) -> int:
            return self._stream.fileno()

        def close(self) -> None:
            events.append("close")
            self._stream.close()

    monkeypatch.setattr(
        transport.os,
        "fdopen",
        lambda *args, **kwargs: OrderedStream(real_fdopen(*args, **kwargs)),
    )

    def ordered_fsync(descriptor: int) -> None:
        events.append("fsync")
        real_fsync(descriptor)

    def ordered_replace(source: Any, target: Any) -> None:
        events.append("replace")
        real_replace(source, target)

    monkeypatch.setattr(transport.os, "fsync", ordered_fsync)
    monkeypatch.setattr(transport.os, "replace", ordered_replace)

    result = write_class_world_release_declaration_file(_declaration(), destination)

    assert result.is_written
    assert events == ["write", "flush", "fsync", "close", "replace"]


def test_cleanup_failure_is_appended_second_without_temp_path_leak(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "release.json"
    destination.write_bytes(b"original")
    monkeypatch.setattr(
        transport.os,
        "replace",
        lambda source, target: (_ for _ in ()).throw(OSError("replace")),
    )
    monkeypatch.setattr(
        transport.Path,
        "unlink",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("cleanup")),
    )

    first = write_class_world_release_declaration_file(_declaration(), destination)
    second = write_class_world_release_declaration_file(_declaration(), destination)

    assert _codes(first) == [
        ClassWorldReleaseDeclarationFileIssueCode.ATOMIC_REPLACE_FAILED,
        ClassWorldReleaseDeclarationFileIssueCode.TEMP_FILE_CLEANUP_FAILED,
    ]
    assert first == second
    assert destination.read_bytes() == b"original"
    assert all(destination.name not in issue.message for issue in first.issues)
    assert all(".tmp" not in issue.message and "0x" not in issue.message for issue in first.issues)


def test_writer_wrong_type_retains_serializer_type_error(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="ClassWorldReleaseDeclaration"):
        write_class_world_release_declaration_file(  # type: ignore[arg-type]
            object(), tmp_path / "release.json"
        )


def test_keyboard_interrupt_and_system_exit_are_not_swallowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for error in (KeyboardInterrupt(), SystemExit()):
        monkeypatch.setattr(
            transport,
            "serialize_class_world_release_declaration",
            lambda value, error=error: (_ for _ in ()).throw(error),
        )
        with pytest.raises(type(error)):
            write_class_world_release_declaration_file(_declaration(), tmp_path / "release.json")


def test_models_are_deeply_immutable_and_use_tuples() -> None:
    issue = ClassWorldReleaseDeclarationFileIssue(
        ClassWorldReleaseDeclarationFileIssueCode.FILE_NOT_FOUND, "missing", "path"
    )
    read = ClassWorldReleaseDeclarationFileReadResult(None, (issue,), (), ())
    write = ClassWorldReleaseDeclarationFileWriteResult(0, (issue,))

    assert isinstance(read.issues, tuple)
    assert isinstance(read.serialization_issues, tuple)
    assert isinstance(read.declaration_issues, tuple)
    assert isinstance(write.issues, tuple)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        issue.location = "changed"  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        read.declaration = _declaration()  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        write.bytes_written = 1  # type: ignore[misc]


def test_public_exports_preserve_all_prior_boundaries() -> None:
    import explore.packages as packages

    expected = {
        "read_class_world_release_declaration_file",
        "write_class_world_release_declaration_file",
        "ClassWorldReleaseDeclarationFileReadResult",
        "ClassWorldReleaseDeclarationFileWriteResult",
        "ClassWorldReleaseDeclarationFileIssue",
        "ClassWorldReleaseDeclarationFileIssueCode",
        "MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES",
        "SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_TRANSPORT_CONTRACT_VERSION",
        "serialize_class_world_release_declaration",
        "parse_class_world_release_declaration",
        "build_class_world_release_declaration",
        "read_class_world_manifest_file",
        "write_class_world_manifest_file",
        "build_package_set_plan",
        "apply_package_set_plan",
        "load_explorer_package",
        "validate_explorer_package",
    }
    assert MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES == 1 * 1024 * 1024
    assert SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_TRANSPORT_CONTRACT_VERSION == "0.1"
    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
    assert not any(name.startswith("_") for name in packages.__all__)


def test_private_helpers_are_not_exported() -> None:
    import explore.packages as packages

    assert "_write_all" not in packages.__all__
    assert "_cleanup_temporary_file" not in packages.__all__
    assert not hasattr(packages, "_write_all")


def test_transport_source_stays_inside_local_file_boundary() -> None:
    source = Path(transport.__file__).read_text(encoding="utf-8")
    forbidden = (
        "import hashlib",
        "import hmac",
        "import cryptography",
        "import yaml",
        "import pygame",
        "from engine",
        "load_explorer_package",
        "validate_explorer_package",
        "build_package_set_plan",
        "apply_package_set_plan",
        "build_student_api_registration_plan",
        "apply_student_api_registration_plan",
        "serialize_class_world_manifest",
        "parse_class_world_manifest",
        "requests",
        "httpx",
        "sqlite",
    )
    assert all(term not in source for term in forbidden)
