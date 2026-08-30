"""Tests for bounded assembled-output manifest readback and digest verification."""

from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

from explore.packages import (
    MAX_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_BYTES,
    SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_FILE_DIGEST_VERIFICATION_CONTRACT_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldArtifactInventory,
    ClassWorldArtifactInventoryResult,
    ClassWorldAssembledOutputManifestDigest,
    ClassWorldAssembledOutputManifestFileIssueCode,
    ClassWorldCohort,
    ClassWorldConfigurationSpec,
    ClassWorldPackageArtifactDeclaration,
    ClassWorldPackageArtifactFileBinding,
    ClassWorldPackagePin,
    ClassWorldVerifiedMaterializationResult,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    build_class_world_assembled_output_manifest,
    build_class_world_assembly_plan,
    build_class_world_configuration,
    build_class_world_materialization_plan,
    build_class_world_release_declaration,
    compute_class_world_release_declaration_digest,
    materialize_verified_class_world_artifacts,
    serialize_class_world_assembled_output_manifest,
    verify_class_world_artifact_files,
    verify_class_world_assembled_output_manifest_file_digest,
)
from explore.packages import (
    class_world_assembled_output_manifest_file_digest_verification as verification_module,
)

_CONTENTS = (b"zeta package artifact\x00", b"alpha package artifact\xff")


def _assembly_plan_result():
    selected_packages = []
    entries = []
    pins = []
    artifacts = []
    for index, (package_id, version, content) in enumerate(
        (
            ("zeta-character", "2.1.0", _CONTENTS[0]),
            ("alpha-object", "1.4.2", _CONTENTS[1]),
        )
    ):
        provenance = PackageProvenance(package_id, version, "0.1")
        entry = (
            CharacterRegistration(
                f"{package_id}:hero",
                "hero",
                provenance,
                CharacterRegistrationSpec("Explorer", index, index, "gold"),
                None,
            )
            if index == 0
            else WorldObjectRegistration(
                f"{package_id}:beacon",
                "beacon",
                provenance,
                WorldObjectRegistrationSpec("Beacon", index, index, "blue", None, None),
                None,
            )
        )
        selected_packages.append(
            SelectedPackagePlan(
                package_id,
                version,
                provenance,
                StudentAPIRegistrationPlan(provenance, (entry,)),
            )
        )
        entries.append(entry)
        pins.append(ClassWorldPackagePin(package_id, version))
        artifacts.append(
            ClassWorldPackageArtifactDeclaration(
                package_id,
                version,
                "sha256",
                hashlib.sha256(content).hexdigest(),
            )
        )

    configuration_result = build_class_world_configuration(
        ClassWorldConfigurationSpec(
            "0.1",
            "expedition-orion-fall-2026",
            "Expedition Orion",
            "3.2.1",
            "1.4.0",
            "0.1",
            ClassWorldCohort("expedition-orion", "Expedition Orion"),
            tuple(pins),
        ),
        PackageSetPlan("0.1", tuple(selected_packages), tuple(entries)),
    )
    assert configuration_result.configuration is not None
    declaration_result = build_class_world_release_declaration(
        configuration_result.configuration,
        release_id="spring-showcase",
        release_version="1.2.3",
    )
    assert declaration_result.declaration is not None
    declaration = declaration_result.declaration
    return build_class_world_assembly_plan(
        ClassWorldArtifactInventoryResult(
            inventory=ClassWorldArtifactInventory(
                contract_version="0.1",
                declaration=declaration,
                declaration_digest=compute_class_world_release_declaration_digest(declaration),
                artifacts=tuple(artifacts),
            ),
            issues=(),
        )
    )


def _materialization_result(tmp_path: Path) -> ClassWorldVerifiedMaterializationResult:
    source = tmp_path / "source"
    (source / "nested").mkdir(parents=True)
    (source / "zeta.pkg").write_bytes(_CONTENTS[0])
    (source / "nested" / "alpha.pkg").write_bytes(_CONTENTS[1])
    bindings = (
        ClassWorldPackageArtifactFileBinding("zeta-character", "2.1.0", "zeta.pkg"),
        ClassWorldPackageArtifactFileBinding("alpha-object", "1.4.2", "nested/alpha.pkg"),
    )
    file_result = verify_class_world_artifact_files(_assembly_plan_result(), source, bindings)
    plan_result = build_class_world_materialization_plan(file_result)
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    result = materialize_verified_class_world_artifacts(
        plan_result, source, output_parent / "release"
    )
    assert result.materialization is not None
    return result


def _state(tmp_path: Path):
    materialization = _materialization_result(tmp_path / "state")
    built = build_class_world_assembled_output_manifest(materialization)
    assert built.manifest is not None
    assert built.digest is not None
    return materialization, built


def _write(path: Path, built) -> bytes:
    assert built.manifest is not None
    content = serialize_class_world_assembled_output_manifest(built.manifest).encode("utf-8")
    path.write_bytes(content)
    return content


def _codes(result) -> list[ClassWorldAssembledOutputManifestFileIssueCode]:
    return [issue.code for issue in result.issues]


@pytest.mark.parametrize("use_string", [False, True], ids=["path", "str"])
def test_reads_only_explicit_manifest_and_verifies_canonical_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    use_string: bool,
) -> None:
    materialization, built = _state(tmp_path)
    path = tmp_path / "assembled-output.json"
    content = _write(path, built)
    opened: list[Path] = []
    inspected: list[Path] = []
    original_open = Path.open
    original_lstat = Path.lstat

    def spy_open(candidate: Path, *args: object, **kwargs: object):
        opened.append(candidate)
        return original_open(candidate, *args, **kwargs)

    def spy_lstat(candidate: Path, *args: object, **kwargs: object):
        inspected.append(candidate)
        return original_lstat(candidate, *args, **kwargs)

    monkeypatch.setattr(Path, "open", spy_open)
    monkeypatch.setattr(Path, "lstat", spy_lstat)

    result = verify_class_world_assembled_output_manifest_file_digest(
        str(path) if use_string else path,
        materialization,
        built.digest,
    )

    assert result.is_verified
    assert result.manifest == built.manifest
    assert result.manifest is not built.manifest
    assert result.manifest is not None
    assert result.manifest.materialization is built.manifest.materialization
    assert result.expected_digest is built.digest
    assert result.actual_digest == built.digest
    assert result.actual_digest is not built.digest
    assert result.matches is True
    assert result.bytes_read == len(content)
    assert result.issues == ()
    assert opened == [path]
    assert inspected == [path]


def test_well_formed_unequal_digest_is_explicit_nonmatching_state(tmp_path: Path) -> None:
    materialization, built = _state(tmp_path)
    path = tmp_path / "assembled-output.json"
    _write(path, built)
    expected = ClassWorldAssembledOutputManifestDigest("sha256", "0" * 64)
    assert expected != built.digest

    result = verify_class_world_assembled_output_manifest_file_digest(
        path, materialization, expected
    )

    assert not result.is_verified
    assert result.manifest == built.manifest
    assert result.manifest is not built.manifest
    assert result.expected_digest is expected
    assert result.actual_digest == built.digest
    assert result.matches is False
    assert result.issues == ()


def test_noncanonical_json_verifies_canonical_manifest_not_raw_file_bytes(tmp_path: Path) -> None:
    materialization, built = _state(tmp_path)
    assert built.manifest is not None
    canonical = serialize_class_world_assembled_output_manifest(built.manifest).encode("utf-8")
    body = json.loads(canonical)
    noncanonical = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
    assert noncanonical != canonical
    path = tmp_path / "assembled-output.json"
    path.write_bytes(noncanonical)

    result = verify_class_world_assembled_output_manifest_file_digest(
        path, materialization, built.digest
    )

    assert result.is_verified
    assert result.actual_digest == built.digest
    assert result.bytes_read == len(noncanonical)


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (None, ClassWorldAssembledOutputManifestFileIssueCode.PATH_REQUIRED),
        ("", ClassWorldAssembledOutputManifestFileIssueCode.PATH_REQUIRED),
        ("   ", ClassWorldAssembledOutputManifestFileIssueCode.PATH_REQUIRED),
        (object(), ClassWorldAssembledOutputManifestFileIssueCode.PATH_INVALID_TYPE),
    ],
)
def test_rejects_missing_or_invalid_explicit_path(
    tmp_path: Path,
    candidate: object,
    expected: ClassWorldAssembledOutputManifestFileIssueCode,
) -> None:
    materialization, built = _state(tmp_path)

    result = verify_class_world_assembled_output_manifest_file_digest(
        candidate,
        materialization,
        built.digest,  # type: ignore[arg-type]
    )

    assert _codes(result) == [expected]
    assert result.manifest is result.actual_digest is result.expected_digest is None
    assert result.matches is None
    assert result.bytes_read == 0


def test_rejects_missing_directory_and_final_symlink_paths(tmp_path: Path) -> None:
    materialization, built = _state(tmp_path)
    missing = tmp_path / "missing.json"
    directory = tmp_path / "directory"
    directory.mkdir()
    target = tmp_path / "target.json"
    _write(target, built)
    symlink = tmp_path / "link.json"
    symlink.symlink_to(target)

    results = (
        verify_class_world_assembled_output_manifest_file_digest(
            missing, materialization, built.digest
        ),
        verify_class_world_assembled_output_manifest_file_digest(
            directory, materialization, built.digest
        ),
        verify_class_world_assembled_output_manifest_file_digest(
            symlink, materialization, built.digest
        ),
    )

    assert [_codes(result) for result in results] == [
        [ClassWorldAssembledOutputManifestFileIssueCode.FILE_NOT_FOUND],
        [ClassWorldAssembledOutputManifestFileIssueCode.FILE_NOT_REGULAR],
        [ClassWorldAssembledOutputManifestFileIssueCode.FILE_SYMLINK_NOT_ALLOWED],
    ]


@pytest.mark.parametrize(
    "candidate",
    [
        None,
        object(),
        ClassWorldAssembledOutputManifestDigest("sha-256", "0" * 64),
        ClassWorldAssembledOutputManifestDigest("sha256", "A" * 64),
        ClassWorldAssembledOutputManifestDigest("sha256", "0" * 63),
    ],
)
def test_malformed_expected_digest_fails_before_file_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    candidate: object,
) -> None:
    materialization, _built = _state(tmp_path)

    def fail_lstat(*args: object, **kwargs: object) -> None:
        raise AssertionError("manifest file must not be inspected")

    monkeypatch.setattr(Path, "lstat", fail_lstat)
    result = verify_class_world_assembled_output_manifest_file_digest(
        tmp_path / "unused.json",
        materialization,
        candidate,  # type: ignore[arg-type]
    )

    assert _codes(result) == [
        ClassWorldAssembledOutputManifestFileIssueCode.EXPECTED_DIGEST_INVALID
    ]


def test_incomplete_materialization_fails_before_file_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _materialization, built = _state(tmp_path)
    invalid = ClassWorldVerifiedMaterializationResult(None, None, ())

    def fail_lstat(*args: object, **kwargs: object) -> None:
        raise AssertionError("manifest file must not be inspected")

    monkeypatch.setattr(Path, "lstat", fail_lstat)
    result = verify_class_world_assembled_output_manifest_file_digest(
        tmp_path / "unused.json", invalid, built.digest
    )

    assert _codes(result) == [
        ClassWorldAssembledOutputManifestFileIssueCode.MATERIALIZATION_INVALID
    ]


def test_read_is_bounded_to_limit_plus_one_byte(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization, built = _state(tmp_path)
    path = tmp_path / "assembled-output.json"
    _write(path, built)
    sizes: list[int] = []
    original_open = Path.open

    class _Reader:
        def __init__(self, stream):
            self._stream = stream

        def __enter__(self):
            self._stream.__enter__()
            return self

        def __exit__(self, *args: object):
            return self._stream.__exit__(*args)

        def read(self, size: int) -> bytes:
            sizes.append(size)
            return self._stream.read(size)

    def spy_open(candidate: Path, *args: object, **kwargs: object):
        return _Reader(original_open(candidate, *args, **kwargs))

    monkeypatch.setattr(Path, "open", spy_open)
    result = verify_class_world_assembled_output_manifest_file_digest(
        path, materialization, built.digest
    )

    assert result.is_verified
    assert sizes == [MAX_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_BYTES + 1]


def test_rejects_oversized_file_without_parsing(tmp_path: Path) -> None:
    materialization, built = _state(tmp_path)
    path = tmp_path / "oversized.json"
    path.write_bytes(b" " * (MAX_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_BYTES + 1))

    result = verify_class_world_assembled_output_manifest_file_digest(
        path, materialization, built.digest
    )

    assert _codes(result) == [ClassWorldAssembledOutputManifestFileIssueCode.FILE_TOO_LARGE]
    assert result.bytes_read == MAX_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_BYTES + 1


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (b"\xef\xbb\xbf{}", ClassWorldAssembledOutputManifestFileIssueCode.FILE_BOM_NOT_ALLOWED),
        (b"\xff", ClassWorldAssembledOutputManifestFileIssueCode.FILE_INVALID_UTF8),
        (b"{", ClassWorldAssembledOutputManifestFileIssueCode.JSON_INVALID),
        (b'{"total_bytes":NaN}', ClassWorldAssembledOutputManifestFileIssueCode.JSON_INVALID),
        (
            b'{"total_bytes":' + b"9" * 5000 + b"}",
            ClassWorldAssembledOutputManifestFileIssueCode.JSON_INVALID,
        ),
        (b"[]", ClassWorldAssembledOutputManifestFileIssueCode.FIELD_INVALID_TYPE),
        (
            b'{"contract_version":"0.1","contract_version":"0.1","packages":[],"total_bytes":0}',
            ClassWorldAssembledOutputManifestFileIssueCode.JSON_DUPLICATE_KEY,
        ),
    ],
)
def test_rejects_invalid_utf8_or_json_forms(
    tmp_path: Path,
    content: bytes,
    expected: ClassWorldAssembledOutputManifestFileIssueCode,
) -> None:
    materialization, built = _state(tmp_path)
    path = tmp_path / "invalid.json"
    path.write_bytes(content)

    result = verify_class_world_assembled_output_manifest_file_digest(
        path, materialization, built.digest
    )

    assert _codes(result) == [expected]
    assert result.manifest is None
    assert result.matches is None


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (
            lambda body: body.pop("total_bytes"),
            ClassWorldAssembledOutputManifestFileIssueCode.FIELD_REQUIRED,
        ),
        (
            lambda body: body.update({"extra": True}),
            ClassWorldAssembledOutputManifestFileIssueCode.FIELD_UNKNOWN,
        ),
        (
            lambda body: body.update({"total_bytes": True}),
            ClassWorldAssembledOutputManifestFileIssueCode.FIELD_INVALID_TYPE,
        ),
        (
            lambda body: body.update({"contract_version": "9.9"}),
            ClassWorldAssembledOutputManifestFileIssueCode.FIELD_INVALID_VALUE,
        ),
        (
            lambda body: body["packages"][0].update({"digest_hex": "A" * 64}),
            ClassWorldAssembledOutputManifestFileIssueCode.FIELD_INVALID_VALUE,
        ),
    ],
)
def test_rejects_malformed_manifest_structure(
    tmp_path: Path,
    mutate,
    expected: ClassWorldAssembledOutputManifestFileIssueCode,
) -> None:
    materialization, built = _state(tmp_path)
    assert built.manifest is not None
    body = json.loads(serialize_class_world_assembled_output_manifest(built.manifest))
    mutate(body)
    path = tmp_path / "malformed.json"
    path.write_text(json.dumps(body), encoding="utf-8")

    result = verify_class_world_assembled_output_manifest_file_digest(
        path, materialization, built.digest
    )

    assert expected in _codes(result)
    assert result.manifest is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda body: body["packages"].reverse(),
        lambda body: body["packages"].pop(),
        lambda body: body["packages"][0].update({"package_id": "forged-package"}),
        lambda body: body["packages"][0].update({"relative_path": "packages/forged"}),
        lambda body: body["packages"][0].update({"bytes_written": 0}),
        lambda body: body.update({"total_bytes": 0}),
    ],
)
def test_rejects_well_formed_nonmatching_or_reordered_manifest(
    tmp_path: Path,
    mutate,
) -> None:
    materialization, built = _state(tmp_path)
    assert built.manifest is not None
    body = json.loads(serialize_class_world_assembled_output_manifest(built.manifest))
    mutate(body)
    path = tmp_path / "forged.json"
    path.write_text(json.dumps(body), encoding="utf-8")

    result = verify_class_world_assembled_output_manifest_file_digest(
        path, materialization, built.digest
    )

    assert _codes(result) == [ClassWorldAssembledOutputManifestFileIssueCode.MANIFEST_MISMATCH]
    assert result.manifest is result.actual_digest is None
    assert result.matches is None


def test_result_models_are_frozen_with_stable_fields(tmp_path: Path) -> None:
    materialization, built = _state(tmp_path)
    path = tmp_path / "assembled-output.json"
    _write(path, built)

    result = verify_class_world_assembled_output_manifest_file_digest(
        path, materialization, built.digest
    )

    assert [field.name for field in fields(result)] == [
        "manifest",
        "expected_digest",
        "actual_digest",
        "matches",
        "bytes_read",
        "issues",
    ]
    assert (
        SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_FILE_DIGEST_VERIFICATION_CONTRACT_VERSION
        == ("0.1")
    )
    assert MAX_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_BYTES == 1024 * 1024
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.matches = False  # type: ignore[misc]


def test_verifier_uses_existing_manifest_contract_without_forbidden_boundaries() -> None:
    source = Path(verification_module.__file__).read_text(encoding="utf-8").lower()
    forbidden = (
        "read_bytes",
        "rglob",
        "walk(",
        "materialize_verified_class_world_artifacts",
        "verify_class_world_artifact",
        "archive",
        "extract",
        "load_explorer_package",
        "subprocess",
        "pygame",
        "requests",
        "authenticate",
        "signing",
        "approval",
        "publication",
        "deploy",
    )

    assert source.count("build_class_world_assembled_output_manifest(") == 1
    assert source.count("serialize_class_world_assembled_output_manifest(") == 1
    assert "hashlib" not in source
    assert all(term not in source for term in forbidden)


def test_public_exports_preserve_readback_and_prior_contracts() -> None:
    import explore.packages as packages

    expected = {
        "verify_class_world_assembled_output_manifest_file_digest",
        "ClassWorldAssembledOutputManifestFileDigestVerificationResult",
        "ClassWorldAssembledOutputManifestFileIssue",
        "ClassWorldAssembledOutputManifestFileIssueCode",
        "MAX_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_BYTES",
        "SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_FILE_DIGEST_VERIFICATION_CONTRACT_VERSION",
        "build_class_world_assembled_output_manifest",
        "serialize_class_world_assembled_output_manifest",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)


def test_expected_digest_value_is_preserved_not_replaced(tmp_path: Path) -> None:
    materialization, built = _state(tmp_path)
    path = tmp_path / "assembled-output.json"
    _write(path, built)
    expected = replace(built.digest)

    result = verify_class_world_assembled_output_manifest_file_digest(
        path, materialization, expected
    )

    assert result.expected_digest is expected


def test_equality_permissive_algorithm_object_cannot_verify(tmp_path: Path) -> None:
    class _AlwaysEqual:
        def __eq__(self, other: object) -> bool:
            return True

        def __ne__(self, other: object) -> bool:
            return False

    materialization, built = _state(tmp_path)
    path = tmp_path / "assembled-output.json"
    _write(path, built)
    crafted = replace(built.digest, algorithm=_AlwaysEqual())

    result = verify_class_world_assembled_output_manifest_file_digest(
        path,
        materialization,
        crafted,  # type: ignore[arg-type]
    )

    assert not result.is_verified
    assert _codes(result) == [
        ClassWorldAssembledOutputManifestFileIssueCode.EXPECTED_DIGEST_INVALID
    ]
