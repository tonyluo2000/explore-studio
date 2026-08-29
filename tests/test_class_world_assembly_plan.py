"""Behavior tests for deterministic class-world assembly input planning v0.1."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

from explore.packages import (
    SUPPORTED_CLASS_WORLD_ASSEMBLY_INPUT_DIGEST_ALGORITHM,
    SUPPORTED_CLASS_WORLD_ASSEMBLY_PLAN_CONTRACT_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldArtifactInventory,
    ClassWorldArtifactInventoryIssue,
    ClassWorldArtifactInventoryIssueCode,
    ClassWorldArtifactInventoryResult,
    ClassWorldAssemblyPlanIssueCode,
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
    build_class_world_assembly_plan,
    build_class_world_configuration,
    build_class_world_release_declaration,
    compute_class_world_release_declaration_digest,
)
from explore.packages import class_world_assembly_plan as plan_module


def _inventory_result(
    *,
    package_order: tuple[tuple[str, str, str], ...] = (
        ("zeta-character", "2.1.0", "a"),
        ("alpha-object", "1.4.2", "b"),
    ),
) -> ClassWorldArtifactInventoryResult:
    selected_packages = []
    entries = []
    pins = []
    artifacts = []
    for index, (package_id, version, digest_character) in enumerate(package_order):
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
                digest_character * 64,
            )
        )

    package_set_plan = PackageSetPlan("0.1", tuple(selected_packages), tuple(entries))
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
        package_set_plan,
    )
    assert configuration_result.configuration is not None
    declaration_result = build_class_world_release_declaration(
        configuration_result.configuration,
        release_id="spring-showcase",
        release_version="1.2.3",
    )
    assert declaration_result.declaration is not None
    declaration = declaration_result.declaration
    return ClassWorldArtifactInventoryResult(
        inventory=ClassWorldArtifactInventory(
            contract_version="0.1",
            declaration=declaration,
            declaration_digest=compute_class_world_release_declaration_digest(declaration),
            artifacts=tuple(artifacts),
        ),
        issues=(),
    )


def _codes(result) -> list[ClassWorldAssemblyPlanIssueCode]:
    return [issue.code for issue in result.issues]


def test_builds_frozen_content_addressed_plan_and_preserves_inventory_identity() -> None:
    inventory_result = _inventory_result()

    result = build_class_world_assembly_plan(inventory_result)

    assert result.is_planned
    assert result.issues == ()
    assert result.plan is not None
    assert result.plan.inventory is inventory_result.inventory
    assert result.plan.contract_version == "0.1"
    assert result.plan.input_digest.algorithm == "sha256"
    assert result.plan.input_digest.hex_digest == (
        "3d74ba2a6b1a0993ee088f989e458f401878aaa56bf5f740b8b03195e6b36042"
    )
    assert [field.name for field in fields(result.plan)] == [
        "contract_version",
        "inventory",
        "input_digest",
    ]
    assert SUPPORTED_CLASS_WORLD_ASSEMBLY_PLAN_CONTRACT_VERSION == "0.1"
    assert SUPPORTED_CLASS_WORLD_ASSEMBLY_INPUT_DIGEST_ALGORITHM == "sha256"
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.plan.contract_version = "0.2"  # type: ignore[misc]


def test_equivalent_inputs_are_repeatable_and_order_remains_significant() -> None:
    first = build_class_world_assembly_plan(_inventory_result())
    second = build_class_world_assembly_plan(_inventory_result())
    reversed_result = build_class_world_assembly_plan(
        _inventory_result(
            package_order=(
                ("alpha-object", "1.4.2", "b"),
                ("zeta-character", "2.1.0", "a"),
            )
        )
    )

    assert first == second
    assert first.plan is not None
    assert reversed_result.plan is not None
    assert first.plan.input_digest != reversed_result.plan.input_digest


def test_artifact_content_identity_changes_plan_digest() -> None:
    original = _inventory_result()
    assert original.inventory is not None
    changed_artifacts = (
        replace(original.inventory.artifacts[0], digest_hex="c" * 64),
        original.inventory.artifacts[1],
    )
    changed = replace(original, inventory=replace(original.inventory, artifacts=changed_artifacts))

    original_plan = build_class_world_assembly_plan(original)
    changed_plan = build_class_world_assembly_plan(changed)

    assert original_plan.plan is not None
    assert changed_plan.plan is not None
    assert original_plan.plan.input_digest != changed_plan.plan.input_digest


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (None, ClassWorldAssemblyPlanIssueCode.INVENTORY_RESULT_REQUIRED),
        (object(), ClassWorldAssemblyPlanIssueCode.INVENTORY_RESULT_INVALID),
        ((), ClassWorldAssemblyPlanIssueCode.INVENTORY_RESULT_INVALID),
    ],
)
def test_missing_or_wrong_upstream_result_fails_closed(candidate: object, expected) -> None:
    result = build_class_world_assembly_plan(candidate)  # type: ignore[arg-type]

    assert result.plan is None
    assert _codes(result) == [expected]


def test_failed_inventory_result_is_not_reinterpreted() -> None:
    failed = ClassWorldArtifactInventoryResult(
        inventory=None,
        issues=(
            ClassWorldArtifactInventoryIssue(
                ClassWorldArtifactInventoryIssueCode.ARTIFACT_PACKAGE_MISSING,
                "missing",
                "artifact_declarations",
            ),
        ),
    )

    result = build_class_world_assembly_plan(failed)

    assert result.plan is None
    assert _codes(result) == [ClassWorldAssemblyPlanIssueCode.INVENTORY_NOT_BUILT]


def test_malformed_issue_collection_fails_closed() -> None:
    malformed = replace(_inventory_result(), issues=None)  # type: ignore[arg-type]

    result = build_class_world_assembly_plan(malformed)

    assert result.plan is None
    assert _codes(result) == [ClassWorldAssemblyPlanIssueCode.INVENTORY_NOT_BUILT]


def test_incoherent_forged_inventory_outputs_fail_closed() -> None:
    valid = _inventory_result()
    assert valid.inventory is not None
    inventory = valid.inventory
    candidates = (
        replace(inventory, contract_version="0.2"),
        replace(inventory, declaration=replace(inventory.declaration, provenance=object())),
        replace(
            inventory,
            declaration=replace(
                inventory.declaration,
                provenance=replace(
                    inventory.declaration.provenance,
                    package_pins=(object(), *inventory.declaration.provenance.package_pins[1:]),
                ),
            ),
        ),
        replace(
            inventory,
            declaration_digest=replace(inventory.declaration_digest, algorithm="md5"),
        ),
        replace(inventory, artifacts=tuple(reversed(inventory.artifacts))),
        replace(
            inventory,
            artifacts=(
                replace(inventory.artifacts[0], digest_hex="A" * 64),
                *inventory.artifacts[1:],
            ),
        ),
        replace(inventory, artifacts=list(inventory.artifacts)),  # type: ignore[arg-type]
    )

    results = [
        build_class_world_assembly_plan(replace(valid, inventory=item)) for item in candidates
    ]

    assert all(result.plan is None for result in results)
    assert all(
        _codes(result) == [ClassWorldAssemblyPlanIssueCode.INVENTORY_INVALID] for result in results
    )


def test_plan_layer_does_not_repeat_inventory_verification_or_execute_student_code() -> None:
    source = Path(plan_module.__file__).read_text(encoding="utf-8").lower()
    forbidden = (
        "build_class_world_artifact_inventory",
        "verify_class_world_release_declaration",
        "compute_class_world_release_declaration_digest",
        "serialize_class_world_release_declaration",
        "read_bytes",
        "read_text",
        "open(",
        "load_explorer_package",
        "apply_package_set_plan",
        "subprocess",
        "pygame",
        "publish",
        "deploy",
        "auth",
    )

    assert all(term not in source for term in forbidden)


def test_public_exports_are_explicit() -> None:
    import explore.packages as packages

    expected = {
        "build_class_world_assembly_plan",
        "ClassWorldAssemblyInputDigest",
        "ClassWorldAssemblyPlan",
        "ClassWorldAssemblyPlanIssue",
        "ClassWorldAssemblyPlanIssueCode",
        "ClassWorldAssemblyPlanResult",
        "SUPPORTED_CLASS_WORLD_ASSEMBLY_INPUT_DIGEST_ALGORITHM",
        "SUPPORTED_CLASS_WORLD_ASSEMBLY_PLAN_CONTRACT_VERSION",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
    assert not hasattr(packages, "_canonical_input_bytes")
