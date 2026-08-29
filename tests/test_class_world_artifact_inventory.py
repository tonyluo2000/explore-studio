"""Behavior tests for deterministic class-world package artifact inventory v0.1."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

from explore.packages import (
    SUPPORTED_CLASS_WORLD_ARTIFACT_INVENTORY_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldArtifactInventoryIssueCode,
    ClassWorldCohort,
    ClassWorldConfigurationSpec,
    ClassWorldPackageArtifactDeclaration,
    ClassWorldPackagePin,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    build_class_world_artifact_inventory,
    build_class_world_configuration,
    build_class_world_release_declaration,
    compute_class_world_release_declaration_digest,
    serialize_class_world_release_declaration,
    verify_class_world_release_declaration_file_digest,
)
from explore.packages import class_world_artifact_inventory as inventory_module
from explore.packages.class_world_release_declaration_digest_models import (
    ClassWorldReleaseDeclarationDigest,
)
from explore.packages.class_world_release_declaration_file_digest_verification_models import (
    ClassWorldReleaseDeclarationFileDigestVerificationResult,
)


def _configuration():
    selected_packages = []
    entries = []
    pins = []
    for index, (package_id, version) in enumerate(
        (("zeta-character", "2.1.0"), ("alpha-object", "1.4.2"))
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
    plan = PackageSetPlan("0.1", tuple(selected_packages), tuple(entries))
    result = build_class_world_configuration(
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
        plan,
    )
    assert result.configuration is not None
    return result.configuration


def _verified_result(tmp_path: Path) -> ClassWorldReleaseDeclarationFileDigestVerificationResult:
    configuration = _configuration()
    declaration_result = build_class_world_release_declaration(
        configuration,
        release_id="spring-showcase",
        release_version="1.2.3",
    )
    assert declaration_result.declaration is not None
    declaration = declaration_result.declaration
    path = tmp_path / "release.json"
    path.write_text(serialize_class_world_release_declaration(declaration), encoding="utf-8")
    return verify_class_world_release_declaration_file_digest(
        path,
        configuration,
        compute_class_world_release_declaration_digest(declaration),
    )


def _artifacts() -> tuple[ClassWorldPackageArtifactDeclaration, ...]:
    return (
        ClassWorldPackageArtifactDeclaration("zeta-character", "2.1.0", "sha256", "a" * 64),
        ClassWorldPackageArtifactDeclaration("alpha-object", "1.4.2", "sha256", "b" * 64),
    )


def test_builds_frozen_inventory_in_verified_release_pin_order(tmp_path: Path) -> None:
    verified = _verified_result(tmp_path)
    supplied = tuple(reversed(_artifacts()))

    result = build_class_world_artifact_inventory(verified, supplied)

    assert result.is_built
    assert result.issues == ()
    assert result.inventory is not None
    assert result.inventory.contract_version == "0.1"
    assert result.inventory.declaration is verified.declaration
    assert result.inventory.declaration_digest is verified.verification.actual_digest
    assert result.inventory.artifacts == (_artifacts()[0], _artifacts()[1])
    assert result.inventory.artifacts[0] is supplied[1]
    assert result.inventory.artifacts[1] is supplied[0]
    assert [field.name for field in fields(result.inventory)] == [
        "contract_version",
        "declaration",
        "declaration_digest",
        "artifacts",
    ]
    assert SUPPORTED_CLASS_WORLD_ARTIFACT_INVENTORY_CONTRACT_VERSION == "0.1"
    assert SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM == "sha256"
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.inventory.artifacts = ()  # type: ignore[misc]


def test_output_is_repeatable_and_independent_of_input_declaration_order(tmp_path: Path) -> None:
    verified = _verified_result(tmp_path)

    first = build_class_world_artifact_inventory(verified, _artifacts())
    second = build_class_world_artifact_inventory(verified, tuple(reversed(_artifacts())))
    third = build_class_world_artifact_inventory(verified, _artifacts())

    assert first == second == third


@pytest.mark.parametrize(
    "invalid",
    [None, object(), (), []],
    ids=["none", "object", "tuple", "list"],
)
def test_rejects_missing_or_wrong_upstream_result_before_artifacts(invalid: object) -> None:
    result = build_class_world_artifact_inventory(  # type: ignore[arg-type]
        invalid,
        _artifacts(),
    )

    expected = (
        ClassWorldArtifactInventoryIssueCode.VERIFICATION_RESULT_REQUIRED
        if invalid is None
        else ClassWorldArtifactInventoryIssueCode.VERIFICATION_RESULT_INVALID
    )
    assert result.inventory is None
    assert [issue.code for issue in result.issues] == [expected]


def test_requires_successful_matching_upstream_verification(tmp_path: Path) -> None:
    verified = _verified_result(tmp_path)
    assert verified.verification is not None
    mismatch = replace(verified.verification, matches=False)
    inconsistent = replace(
        verified.verification,
        actual_digest=ClassWorldReleaseDeclarationDigest("sha256", "f" * 64),
    )
    candidates = (
        replace(verified, verification=None),
        replace(verified, verification=object()),  # type: ignore[arg-type]
        replace(verified, declaration=None),
        replace(verified, verification=mismatch),
        replace(verified, verification=inconsistent),
    )

    results = [
        build_class_world_artifact_inventory(candidate, _artifacts()) for candidate in candidates
    ]

    assert all(result.inventory is None for result in results)
    assert all(
        [issue.code for issue in result.issues]
        == [ClassWorldArtifactInventoryIssueCode.DECLARATION_NOT_VERIFIED]
        for result in results
    )


def test_requires_immutable_artifact_declaration_tuple(tmp_path: Path) -> None:
    verified = _verified_result(tmp_path)

    for invalid in (None, list(_artifacts()), iter(_artifacts()), object()):
        result = build_class_world_artifact_inventory(  # type: ignore[arg-type]
            verified,
            invalid,
        )
        assert result.inventory is None
        assert [issue.code for issue in result.issues] == [
            ClassWorldArtifactInventoryIssueCode.ARTIFACT_DECLARATIONS_REQUIRED
        ]


@pytest.mark.parametrize(
    ("artifact", "expected_code"),
    [
        (object(), ClassWorldArtifactInventoryIssueCode.ARTIFACT_DECLARATION_INVALID_TYPE),
        (
            ClassWorldPackageArtifactDeclaration("Bad ID", "2.1.0", "sha256", "a" * 64),
            ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_ID_INVALID,
        ),
        (
            ClassWorldPackageArtifactDeclaration("zeta-character", "latest", "sha256", "a" * 64),
            ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_VERSION_INVALID,
        ),
        (
            ClassWorldPackageArtifactDeclaration("zeta-character", "2.1.0", "SHA256", "a" * 64),
            ClassWorldArtifactInventoryIssueCode.ARTIFACT_DIGEST_ALGORITHM_INVALID,
        ),
        (
            ClassWorldPackageArtifactDeclaration("zeta-character", "2.1.0", "sha256", "A" * 64),
            ClassWorldArtifactInventoryIssueCode.ARTIFACT_DIGEST_INVALID,
        ),
    ],
)
def test_malformed_declaration_fails_closed(
    tmp_path: Path,
    artifact: object,
    expected_code: ClassWorldArtifactInventoryIssueCode,
) -> None:
    verified = _verified_result(tmp_path)
    declarations = (artifact, _artifacts()[1])

    result = build_class_world_artifact_inventory(  # type: ignore[arg-type]
        verified,
        declarations,
    )

    assert result.inventory is None
    assert expected_code in [issue.code for issue in result.issues]


def test_missing_duplicate_unexpected_and_inconsistent_pins_fail_atomically(
    tmp_path: Path,
) -> None:
    verified = _verified_result(tmp_path)
    declarations = (
        _artifacts()[0],
        _artifacts()[0],
        ClassWorldPackageArtifactDeclaration("alpha-object", "1.4.3", "sha256", "b" * 64),
        ClassWorldPackageArtifactDeclaration("extra-package", "1.0.0", "sha256", "c" * 64),
    )

    result = build_class_world_artifact_inventory(verified, declarations)

    assert result.inventory is None
    assert [issue.code for issue in result.issues] == [
        ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_DUPLICATE,
        ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_VERSION_MISMATCH,
        ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_UNEXPECTED,
    ]
    assert [(issue.package_id, issue.artifact_index) for issue in result.issues] == [
        ("zeta-character", 1),
        ("alpha-object", 2),
        ("extra-package", 3),
    ]


def test_empty_declarations_report_each_missing_pin_in_release_order(tmp_path: Path) -> None:
    result = build_class_world_artifact_inventory(_verified_result(tmp_path), ())

    assert result.inventory is None
    assert [issue.code for issue in result.issues] == [
        ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_MISSING,
        ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_MISSING,
    ]
    assert [issue.package_id for issue in result.issues] == ["zeta-character", "alpha-object"]


def test_inventory_layer_does_not_repeat_io_digest_or_assembly_behavior() -> None:
    source = Path(inventory_module.__file__).read_text(encoding="utf-8").lower()
    forbidden = (
        "open(",
        "read_bytes",
        "read_text",
        "write_",
        "hashlib",
        "compute_class_world_release_declaration_digest",
        "verify_class_world_release_declaration",
        "serialize_class_world_release_declaration",
        "parse_class_world_release_declaration",
        "load_explorer_package",
        "apply_package_set_plan",
        "subprocess",
        "requests",
        "httpx",
        "pygame",
        "signature",
        "approval",
        "publish",
        "deploy",
    )

    assert all(term not in source for term in forbidden)


def test_public_exports_preserve_prior_boundaries() -> None:
    import explore.packages as packages

    expected = {
        "build_class_world_artifact_inventory",
        "ClassWorldPackageArtifactDeclaration",
        "ClassWorldArtifactInventory",
        "ClassWorldArtifactInventoryIssue",
        "ClassWorldArtifactInventoryIssueCode",
        "ClassWorldArtifactInventoryResult",
        "SUPPORTED_CLASS_WORLD_ARTIFACT_INVENTORY_CONTRACT_VERSION",
        "SUPPORTED_CLASS_WORLD_PACKAGE_ARTIFACT_DIGEST_ALGORITHM",
        "verify_class_world_release_declaration_file_digest",
        "load_explorer_package",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
    assert not hasattr(packages, "_verification_issue")
