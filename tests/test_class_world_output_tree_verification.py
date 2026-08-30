"""Tests for materialized output-tree verification against a verified manifest."""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

from explore.packages import (
    SUPPORTED_CLASS_WORLD_OUTPUT_TREE_VERIFICATION_CONTRACT_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldArtifactInventory,
    ClassWorldArtifactInventoryResult,
    ClassWorldAssembledOutputManifestDigest,
    ClassWorldAssembledOutputManifestFileDigestVerificationResult,
    ClassWorldCohort,
    ClassWorldConfigurationSpec,
    ClassWorldOutputTreeVerificationIssueCode,
    ClassWorldPackageArtifactDeclaration,
    ClassWorldPackageArtifactFileBinding,
    ClassWorldPackagePin,
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
    verify_class_world_artifact_files,
    verify_class_world_assembled_output_manifest_file_digest,
    verify_class_world_output_tree,
)
from explore.packages import class_world_output_tree_verification as tree_module

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


def _materialize(tmp_path: Path):
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
    output_root = output_parent / "release"
    result = materialize_verified_class_world_artifacts(plan_result, source, output_root)
    assert result.materialization is not None
    return result, output_root


def _verified_manifest(tmp_path: Path):
    materialization, output_root = _materialize(tmp_path)
    built = build_class_world_assembled_output_manifest(materialization)
    assert built.manifest is not None and built.digest is not None
    verified = verify_class_world_assembled_output_manifest_file_digest(
        _serialized_manifest_path(tmp_path, built), materialization, built.digest
    )
    assert verified.is_verified
    return verified, output_root, built


def _serialized_manifest_path(tmp_path: Path, built) -> Path:
    from explore.packages import serialize_class_world_assembled_output_manifest

    path = tmp_path / "assembled-output.json"
    path.write_bytes(
        serialize_class_world_assembled_output_manifest(built.manifest).encode("utf-8")
    )
    return path


def _codes(result) -> list[ClassWorldOutputTreeVerificationIssueCode]:
    return [issue.code for issue in result.issues]


def _snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    snapshot: dict[str, tuple[bytes, int]] = {}
    for item in sorted(root.rglob("*")):
        if item.is_file():
            stat_result = item.stat()
            snapshot[str(item.relative_to(root))] = (item.read_bytes(), stat_result.st_mtime_ns)
    return snapshot


def test_verifies_materialized_tree_in_canonical_manifest_order(tmp_path: Path) -> None:
    verified, output_root, built = _verified_manifest(tmp_path)
    before = _snapshot(output_root)

    result = verify_class_world_output_tree(verified, output_root)

    assert result.is_verified
    assert result.issues == ()
    assert result.manifest is verified.manifest
    assert (
        result.contract_version == SUPPORTED_CLASS_WORLD_OUTPUT_TREE_VERIFICATION_CONTRACT_VERSION
    )
    assert [artifact.relative_path for artifact in result.artifacts] == [
        package.relative_path for package in built.manifest.packages
    ]
    assert [artifact.package_id for artifact in result.artifacts] == [
        "zeta-character",
        "alpha-object",
    ]
    assert result.total_bytes == built.manifest.total_bytes
    assert sum(artifact.bytes_verified for artifact in result.artifacts) == result.total_bytes
    for artifact, content in zip(result.artifacts, _CONTENTS, strict=True):
        assert artifact.bytes_verified == len(content)
        assert artifact.digest_hex == hashlib.sha256(content).hexdigest()
    assert _snapshot(output_root) == before


@pytest.mark.parametrize("use_string", [False, True], ids=["path", "str"])
def test_accepts_str_or_path_output_root(tmp_path: Path, use_string: bool) -> None:
    verified, output_root, _built = _verified_manifest(tmp_path)

    result = verify_class_world_output_tree(
        verified, str(output_root) if use_string else output_root
    )

    assert result.is_verified


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (None, ClassWorldOutputTreeVerificationIssueCode.VERIFIED_MANIFEST_REQUIRED),
        (object(), ClassWorldOutputTreeVerificationIssueCode.VERIFIED_MANIFEST_INVALID),
        (
            ClassWorldAssembledOutputManifestFileDigestVerificationResult(
                None, None, None, None, 0, ()
            ),
            ClassWorldOutputTreeVerificationIssueCode.VERIFIED_MANIFEST_NOT_VERIFIED,
        ),
    ],
)
def test_rejects_manifest_result_that_is_not_successfully_verified(
    tmp_path: Path,
    candidate: object,
    expected: ClassWorldOutputTreeVerificationIssueCode,
) -> None:
    _verified, output_root, _built = _verified_manifest(tmp_path)

    result = verify_class_world_output_tree(candidate, output_root)  # type: ignore[arg-type]

    assert _codes(result) == [expected]
    assert result.manifest is None
    assert result.artifacts == ()
    assert result.total_bytes is None


def test_nonmatching_digest_verification_result_is_rejected(tmp_path: Path) -> None:
    verified, output_root, _built = _verified_manifest(tmp_path)
    nonmatching = replace(
        verified,
        matches=False,
        expected_digest=ClassWorldAssembledOutputManifestDigest("sha256", "0" * 64),
    )
    assert not nonmatching.is_verified

    result = verify_class_world_output_tree(nonmatching, output_root)

    assert _codes(result) == [
        ClassWorldOutputTreeVerificationIssueCode.VERIFIED_MANIFEST_NOT_VERIFIED
    ]


@pytest.mark.parametrize(
    ("factory", "expected"),
    [
        (lambda tmp_path: None, ClassWorldOutputTreeVerificationIssueCode.OUTPUT_ROOT_REQUIRED),
        (lambda tmp_path: "   ", ClassWorldOutputTreeVerificationIssueCode.OUTPUT_ROOT_REQUIRED),
        (
            lambda tmp_path: object(),
            ClassWorldOutputTreeVerificationIssueCode.OUTPUT_ROOT_INVALID_TYPE,
        ),
        (
            lambda tmp_path: "relative/output",
            ClassWorldOutputTreeVerificationIssueCode.OUTPUT_ROOT_NOT_ABSOLUTE,
        ),
        (
            lambda tmp_path: tmp_path / "missing",
            ClassWorldOutputTreeVerificationIssueCode.OUTPUT_ROOT_NOT_FOUND,
        ),
    ],
)
def test_rejects_invalid_output_root_values(
    tmp_path: Path,
    factory,
    expected: ClassWorldOutputTreeVerificationIssueCode,
) -> None:
    verified, _output_root, _built = _verified_manifest(tmp_path)

    result = verify_class_world_output_tree(verified, factory(tmp_path))

    assert _codes(result) == [expected]


def test_rejects_output_root_that_is_a_regular_file(tmp_path: Path) -> None:
    verified, _output_root, _built = _verified_manifest(tmp_path)
    plain = tmp_path / "plain-file"
    plain.write_text("not a directory", encoding="utf-8")

    result = verify_class_world_output_tree(verified, plain)

    assert _codes(result) == [ClassWorldOutputTreeVerificationIssueCode.OUTPUT_ROOT_NOT_DIRECTORY]


def test_rejects_symlinked_output_root(tmp_path: Path) -> None:
    verified, output_root, _built = _verified_manifest(tmp_path)
    link = tmp_path / "linked-release"
    link.symlink_to(output_root)

    result = verify_class_world_output_tree(verified, link)

    assert _codes(result) == [
        ClassWorldOutputTreeVerificationIssueCode.OUTPUT_ROOT_SYMLINK_NOT_ALLOWED
    ]


def test_rejects_output_root_reached_through_symlinked_parent(tmp_path: Path) -> None:
    verified, output_root, _built = _verified_manifest(tmp_path)
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(output_root.parent)

    result = verify_class_world_output_tree(verified, linked_parent / output_root.name)

    assert _codes(result) == [
        ClassWorldOutputTreeVerificationIssueCode.OUTPUT_ROOT_SYMLINK_NOT_ALLOWED
    ]


def test_rejects_missing_authorized_artifact(tmp_path: Path) -> None:
    verified, output_root, built = _verified_manifest(tmp_path)
    (output_root / built.manifest.packages[0].relative_path).unlink()

    result = verify_class_world_output_tree(verified, output_root)

    assert _codes(result) == [ClassWorldOutputTreeVerificationIssueCode.ARTIFACT_NOT_FOUND]
    assert result.artifacts == ()


def test_rejects_symlinked_authorized_artifact(tmp_path: Path) -> None:
    verified, output_root, built = _verified_manifest(tmp_path)
    target = output_root / built.manifest.packages[0].relative_path
    stashed = tmp_path / "stashed.pkg"
    target.rename(stashed)
    target.symlink_to(stashed)

    result = verify_class_world_output_tree(verified, output_root)

    assert _codes(result) == [
        ClassWorldOutputTreeVerificationIssueCode.ARTIFACT_SYMLINK_NOT_ALLOWED
    ]


def test_rejects_authorized_artifact_reached_through_symlinked_directory(tmp_path: Path) -> None:
    verified, output_root, built = _verified_manifest(tmp_path)
    nested = Path(built.manifest.packages[1].relative_path).parent
    real_dir = output_root / nested
    moved = tmp_path / "moved-nested"
    real_dir.rename(moved)
    (output_root / nested).symlink_to(moved)

    result = verify_class_world_output_tree(verified, output_root)

    assert _codes(result) == [
        ClassWorldOutputTreeVerificationIssueCode.ARTIFACT_SYMLINK_NOT_ALLOWED
    ]


def test_rejects_byte_count_that_disagrees_with_manifest(tmp_path: Path) -> None:
    verified, output_root, built = _verified_manifest(tmp_path)
    target = output_root / built.manifest.packages[0].relative_path
    target.write_bytes(_CONTENTS[0] + b"trailing")

    result = verify_class_world_output_tree(verified, output_root)

    assert _codes(result) == [ClassWorldOutputTreeVerificationIssueCode.BYTE_COUNT_MISMATCH]


def test_rejects_same_byte_count_but_different_bytes(tmp_path: Path) -> None:
    verified, output_root, built = _verified_manifest(tmp_path)
    target = output_root / built.manifest.packages[0].relative_path
    corrupted = bytearray(_CONTENTS[0])
    corrupted[0] ^= 0xFF
    target.write_bytes(bytes(corrupted))

    result = verify_class_world_output_tree(verified, output_root)

    assert _codes(result) == [ClassWorldOutputTreeVerificationIssueCode.DIGEST_MISMATCH]
    assert result.artifacts == ()


def test_rejects_manifest_whose_total_bytes_is_internally_inconsistent(tmp_path: Path) -> None:
    verified, output_root, built = _verified_manifest(tmp_path)
    forged = replace(
        verified,
        manifest=replace(built.manifest, total_bytes=built.manifest.total_bytes + 1),
    )

    result = verify_class_world_output_tree(forged, output_root)

    assert _codes(result) == [
        ClassWorldOutputTreeVerificationIssueCode.VERIFIED_MANIFEST_INCONSISTENT
    ]


def test_descriptor_confinement_required(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    verified, output_root, _built = _verified_manifest(tmp_path)
    monkeypatch.setattr(tree_module.os, "supports_dir_fd", set())

    result = verify_class_world_output_tree(verified, output_root)

    assert _codes(result) == [
        ClassWorldOutputTreeVerificationIssueCode.DESCRIPTOR_CONFINEMENT_UNAVAILABLE
    ]


def test_does_not_open_output_tree_for_invalid_manifest_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _verified, output_root, _built = _verified_manifest(tmp_path)

    def fail_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("output tree must not be opened")

    monkeypatch.setattr(tree_module.os, "open", fail_open)
    result = verify_class_world_output_tree(object(), output_root)  # type: ignore[arg-type]

    assert _codes(result) == [ClassWorldOutputTreeVerificationIssueCode.VERIFIED_MANIFEST_INVALID]


def test_verifies_only_authorized_paths_and_ignores_other_tree_content(tmp_path: Path) -> None:
    verified, output_root, built = _verified_manifest(tmp_path)
    # Unrelated content elsewhere in the tree, including an unreadable decoy, must
    # neither be verified nor cause failure: only manifest-authorized paths are read.
    (output_root / "stray.txt").write_bytes(b"not in the manifest")
    decoy_dir = output_root / "decoy"
    decoy_dir.mkdir()
    unreadable = decoy_dir / "decoy.pkg"
    unreadable.write_bytes(b"decoy")
    unreadable.chmod(0o000)
    try:
        result = verify_class_world_output_tree(verified, output_root)
    finally:
        unreadable.chmod(0o644)

    assert result.is_verified
    assert [artifact.relative_path for artifact in result.artifacts] == [
        package.relative_path for package in built.manifest.packages
    ]


def test_read_is_bounded_to_expected_bytes_plus_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    verified, output_root, built = _verified_manifest(tmp_path)
    sizes: list[int] = []
    original_fdopen = tree_module.os.fdopen

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

    def spy_fdopen(*args: object, **kwargs: object):
        return _Reader(original_fdopen(*args, **kwargs))

    monkeypatch.setattr(tree_module.os, "fdopen", spy_fdopen)
    result = verify_class_world_output_tree(verified, output_root)

    assert result.is_verified
    assert sizes == [len(content) + 1 for content in _CONTENTS]


def test_result_models_are_frozen_with_stable_fields(tmp_path: Path) -> None:
    verified, output_root, _built = _verified_manifest(tmp_path)

    result = verify_class_world_output_tree(verified, output_root)

    assert [field.name for field in fields(result)] == [
        "contract_version",
        "manifest",
        "artifacts",
        "total_bytes",
        "issues",
    ]
    assert [field.name for field in fields(result.artifacts[0])] == [
        "package_id",
        "package_version",
        "relative_path",
        "digest_algorithm",
        "digest_hex",
        "bytes_verified",
    ]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.total_bytes = 0  # type: ignore[misc]


def test_module_stays_within_the_output_tree_verification_boundary() -> None:
    source = Path(tree_module.__file__).read_text(encoding="utf-8").lower()
    forbidden = (
        "import json",
        "build_class_world_assembled_output_manifest",
        "serialize_class_world_assembled_output_manifest",
        "verify_class_world_assembled_output_manifest_file_digest",
        "materialize_verified_class_world_artifacts",
        "o_creat",
        "o_wronly",
        "o_trunc",
        "os.mkdir",
        "os.write(",
        "os.remove",
        "os.unlink",
        "os.rmdir",
        "shutil",
        "zipfile",
        "tarfile",
        "archive",
        "extract",
        "subprocess",
        "pygame",
        "importlib",
        "exec(",
        "authenticate",
        "signing",
        "approval",
        "publish",
        "deploy",
    )
    assert all(term not in source for term in forbidden)
    assert "hashlib.sha256(" in source


def test_public_exports_are_available() -> None:
    import explore.packages as packages

    expected = {
        "verify_class_world_output_tree",
        "ClassWorldOutputTreeVerificationResult",
        "ClassWorldOutputTreeVerificationIssue",
        "ClassWorldOutputTreeVerificationIssueCode",
        "ClassWorldVerifiedOutputArtifact",
        "SUPPORTED_CLASS_WORLD_OUTPUT_TREE_VERIFICATION_CONTRACT_VERSION",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
