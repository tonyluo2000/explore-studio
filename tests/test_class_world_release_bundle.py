"""Behavior tests for deterministic Class-World release bundles v0.1."""

from __future__ import annotations

import hashlib
import io
import stat
import zipfile
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

from explore.packages import (
    CLASS_WORLD_RELEASE_BUNDLE_DECLARATION_PATH,
    CLASS_WORLD_RELEASE_BUNDLE_FILE_MODE,
    CLASS_WORLD_RELEASE_BUNDLE_OUTPUT_MANIFEST_PATH,
    SUPPORTED_CLASS_WORLD_RELEASE_BUNDLE_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_RELEASE_BUNDLE_DIGEST_ALGORITHM,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldArtifactInventory,
    ClassWorldArtifactInventoryResult,
    ClassWorldAssembledOutputManifestDigest,
    ClassWorldCohort,
    ClassWorldConfigurationSpec,
    ClassWorldPackageArtifactDeclaration,
    ClassWorldPackageArtifactFileBinding,
    ClassWorldPackagePin,
    ClassWorldReleaseBundleDigest,
    ClassWorldReleaseBundleIssueCode,
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
    serialize_class_world_release_declaration,
    verify_class_world_artifact_files,
    verify_class_world_assembled_output_manifest_file_digest,
    verify_class_world_output_tree,
    verify_class_world_release_bundle_file,
    write_class_world_release_bundle,
)

_CONTENTS = (b"zeta package artifact\x00", b"alpha package artifact\xff")
_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


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
    configuration = build_class_world_configuration(
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
    ).configuration
    assert configuration is not None
    declaration = build_class_world_release_declaration(
        configuration,
        release_id="spring-showcase",
        release_version="1.2.3",
    ).declaration
    assert declaration is not None
    return build_class_world_assembly_plan(
        ClassWorldArtifactInventoryResult(
            ClassWorldArtifactInventory(
                "0.1",
                declaration,
                compute_class_world_release_declaration_digest(declaration),
                tuple(artifacts),
            ),
            (),
        )
    )


def _verified_tree(tmp_path: Path):
    source = tmp_path / "source"
    (source / "nested").mkdir(parents=True)
    (source / "zeta.pkg").write_bytes(_CONTENTS[0])
    (source / "nested" / "alpha.pkg").write_bytes(_CONTENTS[1])
    bindings = (
        ClassWorldPackageArtifactFileBinding("zeta-character", "2.1.0", "zeta.pkg"),
        ClassWorldPackageArtifactFileBinding("alpha-object", "1.4.2", "nested/alpha.pkg"),
    )
    files = verify_class_world_artifact_files(_assembly_plan_result(), source, bindings)
    plan = build_class_world_materialization_plan(files)
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    output_root = output_parent / "release"
    materialization = materialize_verified_class_world_artifacts(plan, source, output_root)
    built = build_class_world_assembled_output_manifest(materialization)
    assert built.manifest is not None and built.digest is not None
    manifest_path = tmp_path / "assembled-output.json"
    manifest_path.write_text(
        serialize_class_world_assembled_output_manifest(built.manifest), encoding="utf-8"
    )
    verified_manifest = verify_class_world_assembled_output_manifest_file_digest(
        manifest_path, materialization, built.digest
    )
    tree = verify_class_world_output_tree(verified_manifest, output_root)
    assert tree.is_verified
    return tree, output_root, built


def _write(tmp_path: Path):
    tree, output_root, built = _verified_tree(tmp_path)
    destination = tmp_path / "class-world-release.zip"
    result = write_class_world_release_bundle(tree, output_root, destination)
    assert result.is_written
    return result, destination, tree, built


def _codes(result) -> list[ClassWorldReleaseBundleIssueCode]:
    return [issue.code for issue in result.issues]


def _rewrite_zip(
    path: Path,
    *,
    reverse: bool = False,
    timestamp: tuple[int, int, int, int, int, int] | None = None,
    mutate_package: bool = False,
) -> None:
    with zipfile.ZipFile(path, "r") as source:
        members = [(item, source.read(item)) for item in source.infolist()]
    if reverse:
        members.reverse()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as target:
        for original, content in members:
            info = zipfile.ZipInfo(original.filename, timestamp or original.date_time)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            if mutate_package and original.filename.startswith("packages/"):
                content = bytes([content[0] ^ 1]) + content[1:]
                mutate_package = False
            target.writestr(info, content)
    path.write_bytes(buffer.getvalue())


def test_writes_self_contained_archive_with_canonical_members_and_metadata(
    tmp_path: Path,
) -> None:
    result, destination, tree, _built = _write(tmp_path)

    assert result.issues == ()
    assert result.bundle is not None and result.digest is not None
    assert result.bundle.contract_version == SUPPORTED_CLASS_WORLD_RELEASE_BUNDLE_CONTRACT_VERSION
    assert result.digest.algorithm == SUPPORTED_CLASS_WORLD_RELEASE_BUNDLE_DIGEST_ALGORITHM
    assert result.digest.hex_digest == hashlib.sha256(destination.read_bytes()).hexdigest()
    assert result.bytes_written == destination.stat().st_size
    assert stat.S_IMODE(destination.stat().st_mode) == CLASS_WORLD_RELEASE_BUNDLE_FILE_MODE

    with zipfile.ZipFile(destination) as archive:
        members = archive.infolist()
        assert [member.filename for member in members] == [
            CLASS_WORLD_RELEASE_BUNDLE_DECLARATION_PATH,
            CLASS_WORLD_RELEASE_BUNDLE_OUTPUT_MANIFEST_PATH,
            *(artifact.relative_path for artifact in tree.artifacts),
        ]
        assert archive.comment == b""
        assert all(member.date_time == _TIMESTAMP for member in members)
        assert all(member.create_system == 3 for member in members)
        assert all(member.compress_type == zipfile.ZIP_STORED for member in members)
        assert all(member.extra == b"" and member.comment == b"" for member in members)
        assert all((member.external_attr >> 16) == stat.S_IFREG | 0o644 for member in members)
        assert archive.read(members[0]) == serialize_class_world_release_declaration(
            result.bundle.declaration
        ).encode("utf-8")
        assert archive.read(members[1]) == serialize_class_world_assembled_output_manifest(
            result.bundle.output_manifest
        ).encode("utf-8")
        assert [archive.read(member) for member in members[2:]] == list(_CONTENTS)


def test_readback_verifies_structure_contents_metadata_and_whole_digest(tmp_path: Path) -> None:
    written, destination, tree, _built = _write(tmp_path)
    assert written.digest is not None

    result = verify_class_world_release_bundle_file(destination, tree, written.digest)

    assert result.is_verified
    assert result.bundle == written.bundle
    assert result.expected_digest is written.digest
    assert result.actual_digest == written.digest
    assert result.matches is True
    assert result.bytes_read == written.bytes_written
    assert result.issues == ()


def test_equivalent_pipelines_produce_byte_identical_archives(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()

    first, first_path, _first_tree, _first_built = _write(first_root)
    second, second_path, _second_tree, _second_built = _write(second_root)

    assert first_path.read_bytes() == second_path.read_bytes()
    assert first.digest == second.digest
    assert first.bundle == second.bundle


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (None, ClassWorldReleaseBundleIssueCode.OUTPUT_TREE_RESULT_REQUIRED),
        (object(), ClassWorldReleaseBundleIssueCode.OUTPUT_TREE_RESULT_INVALID),
    ],
)
def test_rejects_missing_or_wrong_output_tree_before_filesystem_access(
    tmp_path: Path, candidate: object, expected: ClassWorldReleaseBundleIssueCode
) -> None:
    result = write_class_world_release_bundle(
        candidate, tmp_path / "missing", tmp_path / "bundle.zip"  # type: ignore[arg-type]
    )

    assert _codes(result) == [expected]
    assert result.bundle is None
    assert not (tmp_path / "bundle.zip").exists()


def test_rejects_forged_or_incomplete_verified_tree(tmp_path: Path) -> None:
    tree, output_root, _built = _verified_tree(tmp_path)
    malformed = replace(tree, artifacts=tree.artifacts[:-1])

    result = write_class_world_release_bundle(malformed, output_root, tmp_path / "bundle.zip")

    assert _codes(result) == [ClassWorldReleaseBundleIssueCode.OUTPUT_TREE_INCONSISTENT]


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (None, ClassWorldReleaseBundleIssueCode.OUTPUT_ROOT_REQUIRED),
        (object(), ClassWorldReleaseBundleIssueCode.OUTPUT_ROOT_INVALID_TYPE),
        ("relative", ClassWorldReleaseBundleIssueCode.OUTPUT_ROOT_NOT_ABSOLUTE),
    ],
)
def test_validates_explicit_absolute_output_root(
    tmp_path: Path, candidate: object, expected: ClassWorldReleaseBundleIssueCode
) -> None:
    tree, _output_root, _built = _verified_tree(tmp_path)

    result = write_class_world_release_bundle(
        tree, candidate, tmp_path / "bundle.zip"  # type: ignore[arg-type]
    )

    assert _codes(result) == [expected]


def test_rereads_and_rejects_payload_changed_after_tree_verification(tmp_path: Path) -> None:
    tree, output_root, _built = _verified_tree(tmp_path)
    target = output_root / tree.artifacts[0].relative_path
    target.write_bytes(b"x" * tree.artifacts[0].bytes_verified)

    result = write_class_world_release_bundle(tree, output_root, tmp_path / "bundle.zip")

    assert _codes(result) == [ClassWorldReleaseBundleIssueCode.PAYLOAD_MISMATCH]
    assert not (tmp_path / "bundle.zip").exists()


def test_destination_must_be_absent_and_existing_bytes_are_unchanged(tmp_path: Path) -> None:
    tree, output_root, _built = _verified_tree(tmp_path)
    destination = tmp_path / "bundle.zip"
    destination.write_bytes(b"existing")

    result = write_class_world_release_bundle(tree, output_root, destination)

    assert _codes(result) == [ClassWorldReleaseBundleIssueCode.DESTINATION_EXISTS]
    assert destination.read_bytes() == b"existing"


def test_wrong_whole_bundle_digest_retains_comparison_state(tmp_path: Path) -> None:
    written, destination, tree, _built = _write(tmp_path)
    wrong = ClassWorldReleaseBundleDigest("sha256", "0" * 64)

    result = verify_class_world_release_bundle_file(destination, tree, wrong)

    assert result.bundle == written.bundle
    assert result.expected_digest is wrong
    assert result.actual_digest == written.digest
    assert result.matches is False
    assert result.issues == ()
    assert not result.is_verified


def test_readback_rejects_member_reordering(tmp_path: Path) -> None:
    written, destination, tree, _built = _write(tmp_path)
    _rewrite_zip(destination, reverse=True)
    assert written.digest is not None

    result = verify_class_world_release_bundle_file(destination, tree, written.digest)

    assert _codes(result) == [ClassWorldReleaseBundleIssueCode.ARCHIVE_MEMBER_MISMATCH]


def test_readback_rejects_noncanonical_timestamp(tmp_path: Path) -> None:
    written, destination, tree, _built = _write(tmp_path)
    _rewrite_zip(destination, timestamp=(2026, 1, 2, 3, 4, 6))
    assert written.digest is not None

    result = verify_class_world_release_bundle_file(destination, tree, written.digest)

    assert _codes(result) == [ClassWorldReleaseBundleIssueCode.ARCHIVE_METADATA_MISMATCH]


def test_readback_rejects_payload_content_tampering(tmp_path: Path) -> None:
    written, destination, tree, _built = _write(tmp_path)
    _rewrite_zip(destination, mutate_package=True)
    assert written.digest is not None

    result = verify_class_world_release_bundle_file(destination, tree, written.digest)

    assert _codes(result) == [ClassWorldReleaseBundleIssueCode.ARCHIVE_CONTENT_MISMATCH]


def test_readback_rejects_tampered_canonical_release_declaration(tmp_path: Path) -> None:
    written, destination, tree, _built = _write(tmp_path)
    with zipfile.ZipFile(destination) as source:
        members = [(item, source.read(item)) for item in source.infolist()]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as target:
        for original, content in members:
            if original.filename == CLASS_WORLD_RELEASE_BUNDLE_DECLARATION_PATH:
                content = content.replace(b"spring-showcase", b"winter-showcase")
            info = zipfile.ZipInfo(original.filename, _TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            target.writestr(info, content)
    destination.write_bytes(buffer.getvalue())
    assert written.digest is not None

    result = verify_class_world_release_bundle_file(destination, tree, written.digest)

    assert _codes(result) == [ClassWorldReleaseBundleIssueCode.ARCHIVE_CONTENT_MISMATCH]


def test_readback_rejects_additional_member(tmp_path: Path) -> None:
    written, destination, tree, _built = _write(tmp_path)
    with zipfile.ZipFile(destination, "a", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("unexpected", b"unexpected")
    assert written.digest is not None

    result = verify_class_world_release_bundle_file(destination, tree, written.digest)

    assert _codes(result) == [ClassWorldReleaseBundleIssueCode.ARCHIVE_MEMBER_MISMATCH]


def test_readback_rejects_invalid_zip(tmp_path: Path) -> None:
    written, destination, tree, _built = _write(tmp_path)
    destination.write_bytes(b"not a zip")
    assert written.digest is not None

    result = verify_class_world_release_bundle_file(destination, tree, written.digest)

    assert _codes(result) == [ClassWorldReleaseBundleIssueCode.ARCHIVE_INVALID]


@pytest.mark.parametrize(
    "candidate",
    [
        None,
        object(),
        ClassWorldReleaseBundleDigest("sha512", "0" * 64),
        ClassWorldReleaseBundleDigest("sha256", "A" * 64),
    ],
)
def test_readback_rejects_invalid_expected_digest_before_archive_access(
    tmp_path: Path, candidate: object
) -> None:
    tree, _output_root, _built = _verified_tree(tmp_path)

    result = verify_class_world_release_bundle_file(
        tmp_path / "missing.zip", tree, candidate  # type: ignore[arg-type]
    )

    assert _codes(result) == [ClassWorldReleaseBundleIssueCode.EXPECTED_DIGEST_INVALID]
    assert result.bytes_read == 0


def test_readback_rejects_archive_symlink(tmp_path: Path) -> None:
    written, destination, tree, _built = _write(tmp_path)
    link = tmp_path / "bundle-link.zip"
    link.symlink_to(destination)
    assert written.digest is not None

    result = verify_class_world_release_bundle_file(link, tree, written.digest)

    assert _codes(result) == [ClassWorldReleaseBundleIssueCode.ARCHIVE_SYMLINK_NOT_ALLOWED]


def test_write_rejects_symlinked_destination_parent(tmp_path: Path) -> None:
    tree, output_root, _built = _verified_tree(tmp_path)
    real_parent = tmp_path / "real-releases"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-releases"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    result = write_class_world_release_bundle(tree, output_root, linked_parent / "bundle.zip")

    assert _codes(result) == [
        ClassWorldReleaseBundleIssueCode.DESTINATION_PARENT_SYMLINK_NOT_ALLOWED
    ]
    assert not (real_parent / "bundle.zip").exists()


def test_models_are_frozen_and_have_stable_field_order(tmp_path: Path) -> None:
    written, _destination, _tree, _built = _write(tmp_path)
    assert written.bundle is not None and written.digest is not None

    assert [field.name for field in fields(written.bundle)] == [
        "contract_version",
        "declaration",
        "declaration_digest",
        "output_manifest",
        "output_manifest_digest",
        "entries",
        "total_content_bytes",
    ]
    assert [field.name for field in fields(written.digest)] == ["algorithm", "hex_digest"]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        written.bundle.entries = ()  # type: ignore[misc]


def test_public_api_exports_bundle_contract() -> None:
    import explore.packages as public

    assert public.write_class_world_release_bundle is write_class_world_release_bundle
    assert public.verify_class_world_release_bundle_file is verify_class_world_release_bundle_file
    assert public.SUPPORTED_CLASS_WORLD_RELEASE_BUNDLE_CONTRACT_VERSION == "0.1"
    assert public.SUPPORTED_CLASS_WORLD_RELEASE_BUNDLE_DIGEST_ALGORITHM == "sha256"


def test_contract_does_not_cross_forbidden_boundaries() -> None:
    import inspect

    from explore.packages import class_world_release_bundle as module

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


def test_manifest_digest_type_remains_distinct_from_bundle_digest() -> None:
    manifest_digest = ClassWorldAssembledOutputManifestDigest("sha256", "0" * 64)
    bundle_digest = ClassWorldReleaseBundleDigest("sha256", "0" * 64)

    assert type(manifest_digest) is not type(bundle_digest)
