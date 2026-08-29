"""Behavior tests for deterministic assembled-output manifests v0.1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

from explore.packages import (
    SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_DIGEST_ALGORITHM,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldArtifactInventory,
    ClassWorldArtifactInventoryResult,
    ClassWorldAssembledOutputManifestIssueCode,
    ClassWorldAssembledOutputPackage,
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
)
from explore.packages import class_world_assembled_output_manifest as manifest_module

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


def _code(result) -> ClassWorldAssembledOutputManifestIssueCode:
    assert len(result.issues) == 1
    return result.issues[0].code


def test_projects_exact_authorized_packages_in_canonical_plan_order(tmp_path: Path) -> None:
    materialization_result = _materialization_result(tmp_path)

    result = build_class_world_assembled_output_manifest(materialization_result)

    assert result.is_built
    assert result.issues == ()
    assert result.manifest is not None
    assert result.digest is not None
    assert result.manifest.materialization is materialization_result.materialization
    assert result.manifest.contract_version == "0.1"
    assert result.manifest.total_bytes == sum(map(len, _CONTENTS))
    assert [package.package_id for package in result.manifest.packages] == [
        "zeta-character",
        "alpha-object",
    ]
    assert [package.relative_path for package in result.manifest.packages] == [
        "packages/zeta-character/2.1.0/artifact",
        "packages/alpha-object/1.4.2/artifact",
    ]
    assert [package.bytes_written for package in result.manifest.packages] == list(
        map(len, _CONTENTS)
    )
    assert [package.digest_hex for package in result.manifest.packages] == [
        hashlib.sha256(content).hexdigest() for content in _CONTENTS
    ]


def test_canonical_serialization_and_digest_match_exact_known_projection(tmp_path: Path) -> None:
    result = build_class_world_assembled_output_manifest(_materialization_result(tmp_path))
    assert result.manifest is not None
    assert result.digest is not None

    canonical = serialize_class_world_assembled_output_manifest(result.manifest)
    expected_payload = {
        "contract_version": "0.1",
        "packages": [
            {
                "package_id": "zeta-character",
                "package_version": "2.1.0",
                "digest_algorithm": "sha256",
                "digest_hex": hashlib.sha256(_CONTENTS[0]).hexdigest(),
                "relative_path": "packages/zeta-character/2.1.0/artifact",
                "bytes_written": len(_CONTENTS[0]),
            },
            {
                "package_id": "alpha-object",
                "package_version": "1.4.2",
                "digest_algorithm": "sha256",
                "digest_hex": hashlib.sha256(_CONTENTS[1]).hexdigest(),
                "relative_path": "packages/alpha-object/1.4.2/artifact",
                "bytes_written": len(_CONTENTS[1]),
            },
        ],
        "total_bytes": sum(map(len, _CONTENTS)),
    }
    expected = json.dumps(expected_payload, ensure_ascii=False, separators=(",", ":")) + "\n"

    assert canonical == expected
    assert result.digest.algorithm == "sha256"
    assert result.digest.hex_digest == hashlib.sha256(expected.encode("utf-8")).hexdigest()
    assert canonical.endswith("\n")
    assert " " not in canonical


def test_output_is_deterministic_across_equivalent_materializations(tmp_path: Path) -> None:
    first = build_class_world_assembled_output_manifest(_materialization_result(tmp_path / "first"))
    second = build_class_world_assembled_output_manifest(
        _materialization_result(tmp_path / "second")
    )

    assert first.manifest == second.manifest
    assert first.digest == second.digest
    assert first.manifest is not None
    assert second.manifest is not None
    assert serialize_class_world_assembled_output_manifest(
        first.manifest
    ) == serialize_class_world_assembled_output_manifest(second.manifest)


@pytest.mark.parametrize("candidate", [None, object(), "materialized"])
def test_rejects_missing_or_wrong_result_type(candidate: object) -> None:
    result = build_class_world_assembled_output_manifest(candidate)  # type: ignore[arg-type]

    expected = (
        ClassWorldAssembledOutputManifestIssueCode.MATERIALIZATION_RESULT_REQUIRED
        if candidate is None
        else ClassWorldAssembledOutputManifestIssueCode.MATERIALIZATION_RESULT_INVALID
    )
    assert not result.is_built
    assert result.manifest is None
    assert result.digest is None
    assert _code(result) == expected


def test_rejects_incomplete_or_forged_success_envelope(tmp_path: Path) -> None:
    valid = _materialization_result(tmp_path)
    assert valid.materialization is not None
    candidates = (
        replace(valid, materialization=None),
        replace(valid, issues=[]),  # type: ignore[arg-type]
        replace(valid, issues=(object(),)),  # type: ignore[arg-type]
        replace(valid, source_verification=valid.materialization.plan.file_verification),
    )

    for candidate in candidates:
        result = build_class_world_assembled_output_manifest(candidate)
        assert (
            _code(result) == ClassWorldAssembledOutputManifestIssueCode.MATERIALIZATION_NOT_COMPLETE
        )
        assert result.manifest is result.digest is None


def test_rejects_incomplete_forged_or_nonmatching_materialization_state(tmp_path: Path) -> None:
    valid = _materialization_result(tmp_path)
    assert valid.materialization is not None
    materialization = valid.materialization
    first = materialization.packages[0]
    detached_first = replace(first, package=replace(first.package))
    forged_materializations = (
        replace(materialization, contract_version="9.9"),
        replace(materialization, packages=materialization.packages[:-1]),
        replace(materialization, packages=tuple(reversed(materialization.packages))),
        replace(materialization, packages=(detached_first, *materialization.packages[1:])),
        replace(
            materialization,
            packages=(
                replace(first, bytes_written=first.bytes_written + 1),
                *materialization.packages[1:],
            ),
        ),
        replace(materialization, total_bytes=materialization.total_bytes + 1),
        replace(materialization, total_bytes=True),
        replace(materialization, plan=replace(materialization.plan, total_bytes=0)),
        replace(materialization, source_verification=object()),  # type: ignore[arg-type]
    )

    for forged in forged_materializations:
        candidate = replace(
            valid, materialization=forged, source_verification=forged.source_verification
        )
        result = build_class_world_assembled_output_manifest(candidate)
        assert (
            _code(result) == ClassWorldAssembledOutputManifestIssueCode.MATERIALIZATION_INCONSISTENT
        )
        assert result.manifest is result.digest is None


def test_serializer_fails_closed_on_forged_manifest(tmp_path: Path) -> None:
    result = build_class_world_assembled_output_manifest(_materialization_result(tmp_path))
    assert result.manifest is not None
    manifest = result.manifest
    first = manifest.packages[0]
    candidates = (
        object(),
        replace(manifest, contract_version="9.9"),
        replace(manifest, packages=manifest.packages[:-1]),
        replace(manifest, packages=tuple(reversed(manifest.packages))),
        replace(
            manifest,
            packages=(replace(first, relative_path="packages/forged"), *manifest.packages[1:]),
        ),
        replace(manifest, packages=(replace(first, digest_hex="0" * 64), *manifest.packages[1:])),
        replace(manifest, total_bytes=manifest.total_bytes + 1),
    )

    for candidate in candidates:
        with pytest.raises(ValueError, match="coherent verified materialization"):
            serialize_class_world_assembled_output_manifest(candidate)  # type: ignore[arg-type]


def test_models_are_frozen_and_have_stable_field_order(tmp_path: Path) -> None:
    result = build_class_world_assembled_output_manifest(_materialization_result(tmp_path))
    assert result.manifest is not None
    assert result.digest is not None
    assert [field.name for field in fields(result.manifest)] == [
        "contract_version",
        "materialization",
        "packages",
        "total_bytes",
    ]
    assert [field.name for field in fields(result.digest)] == ["algorithm", "hex_digest"]
    assert [field.name for field in fields(result.manifest.packages[0])] == [
        "package_id",
        "package_version",
        "digest_algorithm",
        "digest_hex",
        "relative_path",
        "bytes_written",
    ]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.manifest.total_bytes = 0  # type: ignore[misc]


def test_composer_does_not_reread_files_or_cross_forbidden_boundaries() -> None:
    source = Path(manifest_module.__file__).read_text(encoding="utf-8").lower()
    forbidden = (
        "pathlib",
        "open(",
        "read_bytes",
        "verify_class_world_artifact",
        "materialize_verified_class_world_artifacts",
        "archive",
        "extract",
        "load_explorer_package",
        "subprocess",
        "pygame",
        "requests",
        "auth",
        "sign",
        "approve",
        "publication",
        "deploy",
    )

    assert source.count("build_class_world_materialization_plan(") == 1
    assert all(term not in source for term in forbidden)


def test_public_exports_preserve_manifest_and_prior_contracts() -> None:
    import explore.packages as packages

    expected = {
        "build_class_world_assembled_output_manifest",
        "serialize_class_world_assembled_output_manifest",
        "ClassWorldAssembledOutputManifest",
        "ClassWorldAssembledOutputManifestDigest",
        "ClassWorldAssembledOutputManifestIssue",
        "ClassWorldAssembledOutputManifestIssueCode",
        "ClassWorldAssembledOutputManifestResult",
        "ClassWorldAssembledOutputPackage",
        "SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_CONTRACT_VERSION",
        "SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_DIGEST_ALGORITHM",
        "materialize_verified_class_world_artifacts",
        "build_class_world_materialization_plan",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
    assert SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_CONTRACT_VERSION == "0.1"
    assert SUPPORTED_CLASS_WORLD_ASSEMBLED_OUTPUT_MANIFEST_DIGEST_ALGORITHM == "sha256"


def test_package_projection_constructor_does_not_hide_extra_state() -> None:
    package = ClassWorldAssembledOutputPackage("pkg", "1.0.0", "sha256", "0" * 64, "path", 1)

    assert package.package_id == "pkg"
