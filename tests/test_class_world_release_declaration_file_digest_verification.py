"""Behavior tests for release-declaration file digest verification v0.1."""

from __future__ import annotations

import json
import os
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

from explore.packages import (
    MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES,
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_FILE_DIGEST_VERIFICATION_CONTRACT_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldCohort,
    ClassWorldConfiguration,
    ClassWorldConfigurationSpec,
    ClassWorldPackagePin,
    ClassWorldReleaseDeclaration,
    ClassWorldReleaseDeclarationDigest,
    ClassWorldReleaseDeclarationFileIssue,
    ClassWorldReleaseDeclarationFileIssueCode,
    ClassWorldReleaseDeclarationFileReadResult,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    build_class_world_configuration,
    build_class_world_release_declaration,
    compute_class_world_release_declaration_digest,
    read_class_world_release_declaration_file,
    serialize_class_world_release_declaration,
    verify_class_world_release_declaration_digest,
    verify_class_world_release_declaration_file_digest,
)
from explore.packages import (
    class_world_release_declaration_file_digest_verification as verification_module,
)


def _configuration() -> ClassWorldConfiguration:
    package_id = "zeta-character"
    package_version = "2.1.0-beta.1+class"
    provenance = PackageProvenance(package_id, package_version, "0.1")
    entry = CharacterRegistration(
        f"{package_id}:hero",
        "hero",
        provenance,
        CharacterRegistrationSpec("Exploratrice", 10, 20, "gold"),
        None,
    )
    selected = SelectedPackagePlan(
        package_id,
        package_version,
        provenance,
        StudentAPIRegistrationPlan(provenance, (entry,)),
    )
    plan = PackageSetPlan("0.1", (selected,), (entry,))
    result = build_class_world_configuration(
        ClassWorldConfigurationSpec(
            "0.1",
            "expedition-orion-fall-2026",
            "Expédition Orion — Automne 2026 🚀",
            "3.2.1",
            "1.4.0",
            "0.1",
            ClassWorldCohort("expedition-orion", "Expédition Orion 🚀"),
            (ClassWorldPackagePin(package_id, package_version),),
        ),
        plan,
    )
    assert result.configuration is not None
    return result.configuration


def _declaration(
    configuration: ClassWorldConfiguration | None = None,
    *,
    release_id: str = "spring-showcase",
) -> ClassWorldReleaseDeclaration:
    result = build_class_world_release_declaration(
        configuration or _configuration(),
        release_id=release_id,
        release_version="1.2.3-rc.1+school",
    )
    assert result.declaration is not None
    return result.declaration


def _write_canonical(path: Path, declaration: ClassWorldReleaseDeclaration) -> bytes:
    content = serialize_class_world_release_declaration(declaration).encode("utf-8")
    path.write_bytes(content)
    return content


def _fail_verifier(*args: object, **kwargs: object) -> None:
    raise AssertionError("digest verifier must not be called after reader failure")


@pytest.mark.parametrize("use_string", [False, True], ids=["path", "str"])
def test_matching_file_returns_frozen_identity_preserving_result(
    tmp_path: Path,
    use_string: bool,
) -> None:
    declaration = _declaration()
    path = tmp_path / "release.json"
    _write_canonical(path, declaration)
    expected = compute_class_world_release_declaration_digest(declaration)

    result = verify_class_world_release_declaration_file_digest(
        str(path) if use_string else path,
        declaration.configuration,
        expected,
    )

    assert result.declaration == declaration
    assert result.declaration is not None
    assert result.declaration.configuration is declaration.configuration
    assert result.verification is not None
    assert result.verification.matches is True
    assert result.verification.expected_digest is expected
    assert result.verification.actual_digest == expected
    assert result.verification.actual_digest is not expected
    assert result.issues == result.serialization_issues == result.declaration_issues == ()
    assert [field.name for field in fields(result)] == [
        "declaration",
        "verification",
        "issues",
        "serialization_issues",
        "declaration_issues",
    ]
    assert isinstance(result.issues, tuple)
    assert SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_FILE_DIGEST_VERIFICATION_CONTRACT_VERSION == (
        "0.1"
    )
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.verification = None  # type: ignore[misc]


def test_valid_digest_mismatch_is_normal_result_without_reader_issues(tmp_path: Path) -> None:
    declaration = _declaration()
    path = tmp_path / "release.json"
    _write_canonical(path, declaration)
    expected = compute_class_world_release_declaration_digest(
        _declaration(release_id="autumn-showcase")
    )

    result = verify_class_world_release_declaration_file_digest(
        path, declaration.configuration, expected
    )

    assert result.declaration == declaration
    assert result.verification is not None
    assert result.verification.matches is False
    assert result.verification.expected_digest is expected
    assert result.verification.actual_digest == compute_class_world_release_declaration_digest(
        declaration
    )
    assert result.verification.actual_digest != expected
    assert result.issues == result.serialization_issues == result.declaration_issues == ()


def test_noncanonical_json_verifies_canonical_declaration_not_raw_bytes(
    tmp_path: Path,
) -> None:
    declaration = _declaration()
    canonical = serialize_class_world_release_declaration(declaration).encode("utf-8")
    body = json.loads(canonical)
    noncanonical = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert noncanonical != canonical
    path = tmp_path / "release.json"
    path.write_bytes(noncanonical)
    expected = compute_class_world_release_declaration_digest(declaration)

    result = verify_class_world_release_declaration_file_digest(
        path, declaration.configuration, expected
    )

    assert path.read_bytes() != canonical
    assert result.declaration == declaration
    assert result.verification is not None and result.verification.matches is True


@pytest.mark.parametrize("invalid_path", [None, "", " \n\t", b"release.json", object()])
def test_invalid_path_preserves_transport_failure_and_skips_verifier(
    invalid_path: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        verification_module,
        "verify_class_world_release_declaration_digest",
        _fail_verifier,
    )

    result = verify_class_world_release_declaration_file_digest(  # type: ignore[arg-type]
        invalid_path,
        _configuration(),
        object(),  # type: ignore[arg-type]
    )

    assert result.declaration is None and result.verification is None
    assert len(result.issues) == 1
    assert result.serialization_issues == result.declaration_issues == ()


def test_filesystem_transport_failures_skip_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = tmp_path / "missing.json"
    directory = tmp_path / "directory"
    directory.mkdir()
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    symlink = tmp_path / "symlink.json"
    broken = tmp_path / "broken.json"
    try:
        symlink.symlink_to(target)
        broken.symlink_to(tmp_path / "absent.json")
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Symlinks unavailable: {error}")
    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b" " * (MAX_CLASS_WORLD_RELEASE_DECLARATION_BYTES + 1))
    paths = [missing, directory, symlink, broken, oversized]
    if Path("/dev/null").exists():
        paths.append(Path("/dev/null"))
    monkeypatch.setattr(
        verification_module,
        "verify_class_world_release_declaration_digest",
        _fail_verifier,
    )

    results = [
        verify_class_world_release_declaration_file_digest(
            path,
            _configuration(),
            object(),  # type: ignore[arg-type]
        )
        for path in paths
    ]

    assert all(result.declaration is None and result.verification is None for result in results)
    assert all(len(result.issues) == 1 for result in results)
    assert all(not result.serialization_issues for result in results)
    assert all(not result.declaration_issues for result in results)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs unavailable")
def test_nonregular_fifo_skips_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fifo = tmp_path / "release.pipe"
    os.mkfifo(fifo)
    monkeypatch.setattr(
        verification_module,
        "verify_class_world_release_declaration_digest",
        _fail_verifier,
    )

    result = verify_class_world_release_declaration_file_digest(
        fifo,
        _configuration(),
        object(),  # type: ignore[arg-type]
    )

    assert [issue.code for issue in result.issues] == [
        ClassWorldReleaseDeclarationFileIssueCode.FILE_NOT_REGULAR
    ]
    assert result.verification is None


@pytest.mark.parametrize(
    "content",
    [
        b"\xff{}",
        b"\xef\xbb\xbf{}",
        "{}".encode("utf-16"),
        "{}".encode("utf-32"),
    ],
    ids=["invalid-utf8", "bom", "utf16", "utf32"],
)
def test_encoding_failures_preserve_transport_issues_and_skip_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    content: bytes,
) -> None:
    path = tmp_path / "release.json"
    path.write_bytes(content)
    direct = read_class_world_release_declaration_file(path, _configuration())
    monkeypatch.setattr(
        verification_module,
        "verify_class_world_release_declaration_digest",
        _fail_verifier,
    )

    result = verify_class_world_release_declaration_file_digest(
        path,
        _configuration(),
        object(),  # type: ignore[arg-type]
    )

    assert result.declaration is None and result.verification is None
    assert result.issues == direct.issues
    assert result.serialization_issues == result.declaration_issues == ()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda text: "{",
        lambda text: text.replace(
            '"schema_version": "0.1"',
            '"schema_version": "0.1", "schema_version": "0.1"',
        ),
    ],
    ids=["malformed-json", "duplicate-key"],
)
def test_serialization_failures_are_preserved_and_skip_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: object,
) -> None:
    declaration = _declaration()
    path = tmp_path / "release.json"
    text = mutation(serialize_class_world_release_declaration(declaration))  # type: ignore[operator]
    path.write_text(text, encoding="utf-8")
    direct = read_class_world_release_declaration_file(path, declaration.configuration)
    monkeypatch.setattr(
        verification_module,
        "verify_class_world_release_declaration_digest",
        _fail_verifier,
    )

    result = verify_class_world_release_declaration_file_digest(
        path,
        declaration.configuration,
        object(),  # type: ignore[arg-type]
    )

    assert result.declaration is None and result.verification is None
    assert result.issues == ()
    assert result.serialization_issues == direct.serialization_issues
    assert result.serialization_issues
    assert result.declaration_issues == ()


def test_declaration_failure_is_preserved_and_skips_verifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declaration = _declaration()
    body = json.loads(serialize_class_world_release_declaration(declaration))
    body["identity"]["release_id"] = "Bad/ID"
    path = tmp_path / "release.json"
    path.write_text(json.dumps(body), encoding="utf-8")
    direct = read_class_world_release_declaration_file(path, declaration.configuration)
    monkeypatch.setattr(
        verification_module,
        "verify_class_world_release_declaration_digest",
        _fail_verifier,
    )

    result = verify_class_world_release_declaration_file_digest(
        path,
        declaration.configuration,
        object(),  # type: ignore[arg-type]
    )

    assert result.declaration is None and result.verification is None
    assert result.issues == result.serialization_issues == ()
    assert result.declaration_issues == direct.declaration_issues
    assert result.declaration_issues


@pytest.mark.parametrize(
    "invalid",
    [
        object(),
        ClassWorldReleaseDeclarationDigest("SHA256", "a" * 64),
        ClassWorldReleaseDeclarationDigest("sha256", "A" * 64),
    ],
    ids=["wrong-type", "algorithm", "hex"],
)
def test_expected_digest_errors_are_preserved_after_successful_read(
    tmp_path: Path,
    invalid: object,
) -> None:
    declaration = _declaration()
    path = tmp_path / "release.json"
    _write_canonical(path, declaration)
    expected_error = (
        TypeError if not isinstance(invalid, ClassWorldReleaseDeclarationDigest) else ValueError
    )

    with pytest.raises(expected_error, match="expected_digest"):
        verify_class_world_release_declaration_file_digest(
            path,
            declaration.configuration,
            invalid,  # type: ignore[arg-type]
        )


def test_reader_failure_precedes_malformed_expected_digest(tmp_path: Path) -> None:
    result = verify_class_world_release_declaration_file_digest(
        tmp_path / "missing.json",
        _configuration(),
        object(),  # type: ignore[arg-type]
    )

    assert result.verification is None
    assert [issue.code for issue in result.issues] == [
        ClassWorldReleaseDeclarationFileIssueCode.FILE_NOT_FOUND
    ]


def test_success_delegates_once_and_preserves_returned_objects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declaration = _declaration()
    expected = compute_class_world_release_declaration_digest(declaration)
    read_result = ClassWorldReleaseDeclarationFileReadResult(declaration, (), (), ())
    verification = verify_class_world_release_declaration_digest(declaration, expected)
    read_calls: list[tuple[object, object]] = []
    verification_calls: list[tuple[object, object]] = []

    def read(path: object, configuration: object) -> ClassWorldReleaseDeclarationFileReadResult:
        read_calls.append((path, configuration))
        return read_result

    def verify(value: object, digest: object) -> object:
        verification_calls.append((value, digest))
        return verification

    monkeypatch.setattr(verification_module, "read_class_world_release_declaration_file", read)
    monkeypatch.setattr(
        verification_module, "verify_class_world_release_declaration_digest", verify
    )

    result = verify_class_world_release_declaration_file_digest(
        "chosen.json", declaration.configuration, expected
    )

    assert read_calls == [("chosen.json", declaration.configuration)]
    assert verification_calls == [(declaration, expected)]
    assert result.declaration is declaration
    assert result.verification is verification
    assert result.issues is read_result.issues
    assert result.serialization_issues is read_result.serialization_issues
    assert result.declaration_issues is read_result.declaration_issues


def test_failure_delegates_reader_once_and_preserves_exact_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    issue = ClassWorldReleaseDeclarationFileIssue(
        ClassWorldReleaseDeclarationFileIssueCode.FILE_NOT_FOUND,
        "missing",
        "path",
    )
    read_result = ClassWorldReleaseDeclarationFileReadResult(None, (issue,), (), ())
    calls: list[tuple[object, object]] = []

    def read(path: object, configuration: object) -> ClassWorldReleaseDeclarationFileReadResult:
        calls.append((path, configuration))
        return read_result

    monkeypatch.setattr(verification_module, "read_class_world_release_declaration_file", read)
    monkeypatch.setattr(
        verification_module,
        "verify_class_world_release_declaration_digest",
        _fail_verifier,
    )
    configuration = _configuration()

    result = verify_class_world_release_declaration_file_digest(
        "missing.json",
        configuration,
        object(),  # type: ignore[arg-type]
    )

    assert calls == [("missing.json", configuration)]
    assert result.declaration is None and result.verification is None
    assert result.issues is read_result.issues
    assert result.serialization_issues is read_result.serialization_issues
    assert result.declaration_issues is read_result.declaration_issues


def test_verification_is_read_only_for_source_file(tmp_path: Path) -> None:
    declaration = _declaration()
    path = tmp_path / "release.json"
    content = _write_canonical(path, declaration)
    before = path.stat()
    names_before = sorted(item.name for item in tmp_path.iterdir())

    result = verify_class_world_release_declaration_file_digest(
        path,
        declaration.configuration,
        compute_class_world_release_declaration_digest(declaration),
    )

    after = path.stat()
    assert result.verification is not None and result.verification.matches
    assert path.read_bytes() == content
    assert after.st_ino == before.st_ino
    assert after.st_size == before.st_size
    assert after.st_mtime_ns == before.st_mtime_ns
    assert sorted(item.name for item in tmp_path.iterdir()) == names_before


def test_composition_source_stays_inside_reader_and_verifier_boundary() -> None:
    source = Path(verification_module.__file__).read_text(encoding="utf-8").lower()
    forbidden = (
        "hashlib",
        "serialize_class_world_release_declaration",
        "_validate_expected_digest",
        "open(",
        "read_bytes",
        "read_text",
        "lstat",
        "write_",
        "tempfile",
        "replace(",
        "load_explorer_package",
        "validate_explorer_package",
        "build_package_set_plan",
        "apply_package_set_plan",
        "pygame",
        "requests",
        "httpx",
        "sqlite",
        "subprocess",
        "environ",
        "random",
        "time",
        "hmac",
        "signature",
        "certificate",
        "archive",
        "inventory",
        "deploy",
    )

    assert source.count("read_class_world_release_declaration_file(path, configuration)") == 1
    assert source.count("verify_class_world_release_declaration_digest(") == 1
    assert all(term not in source for term in forbidden)


def test_public_exports_preserve_prior_package_boundaries() -> None:
    import explore.packages as packages

    expected = {
        "verify_class_world_release_declaration_file_digest",
        "ClassWorldReleaseDeclarationFileDigestVerificationResult",
        "SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_FILE_DIGEST_VERIFICATION_CONTRACT_VERSION",
        "read_class_world_release_declaration_file",
        "write_class_world_release_declaration_file",
        "verify_class_world_release_declaration_digest",
        "compute_class_world_release_declaration_digest",
        "serialize_class_world_release_declaration",
        "build_class_world_release_declaration",
        "build_class_world_configuration",
        "serialize_class_world_manifest",
        "read_class_world_manifest_file",
        "build_package_set_plan",
        "apply_package_set_plan",
        "load_explorer_package",
        "validate_explorer_package",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
    assert not hasattr(packages, "_fail_verifier")
    assert not hasattr(packages, "_validate_expected_digest")
