"""Behavior tests for class-world artifact content verification v0.1."""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

from explore.packages import (
    SUPPORTED_CLASS_WORLD_ARTIFACT_CONTENT_VERIFICATION_CONTRACT_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldArtifactContentVerificationIssueCode,
    ClassWorldArtifactInventory,
    ClassWorldArtifactInventoryResult,
    ClassWorldAssemblyPlanIssue,
    ClassWorldAssemblyPlanIssueCode,
    ClassWorldAssemblyPlanResult,
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
    verify_class_world_artifact_contents,
)
from explore.packages import class_world_artifact_content_verification as verification_module

_CONTENTS = (b"zeta package artifact\x00", b"alpha package artifact\xff")


def _plan_result() -> ClassWorldAssemblyPlanResult:
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
    inventory_result = ClassWorldArtifactInventoryResult(
        inventory=ClassWorldArtifactInventory(
            contract_version="0.1",
            declaration=declaration,
            declaration_digest=compute_class_world_release_declaration_digest(declaration),
            artifacts=tuple(artifacts),
        ),
        issues=(),
    )
    result = build_class_world_assembly_plan(inventory_result)
    assert result.plan is not None
    return result


def _codes(result) -> list[ClassWorldArtifactContentVerificationIssueCode]:
    return [issue.code for issue in result.issues]


def test_matching_contents_return_frozen_canonical_verification() -> None:
    plan_result = _plan_result()

    result = verify_class_world_artifact_contents(plan_result, _CONTENTS)

    assert result.is_complete
    assert result.issues == ()
    assert result.verification is not None
    assert result.verification.contract_version == "0.1"
    assert result.verification.plan is plan_result.plan
    assert result.verification.all_match is True
    assert [package.artifact.package_id for package in result.verification.packages] == [
        "zeta-character",
        "alpha-object",
    ]
    assert [package.actual_digest.hex_digest for package in result.verification.packages] == [
        "695db89cb9aae70880686aeed4be835285ccb730bfdba39b12bb899b8c4a11d2",
        "d75603c49e1a6ffed6bc3d044df1ed0f5d1039419e61c81c624a61200f0d1fab",
    ]
    assert all(
        package.actual_digest.algorithm == "sha256" for package in result.verification.packages
    )
    assert all(package.matches for package in result.verification.packages)
    assert [field.name for field in fields(result.verification)] == [
        "contract_version",
        "plan",
        "packages",
    ]
    assert SUPPORTED_CLASS_WORLD_ARTIFACT_CONTENT_VERIFICATION_CONTRACT_VERSION == "0.1"
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.verification.packages = ()  # type: ignore[misc]


def test_mismatch_is_complete_deterministic_state_without_issues() -> None:
    first = verify_class_world_artifact_contents(_plan_result(), (_CONTENTS[0], b"changed"))
    second = verify_class_world_artifact_contents(_plan_result(), (_CONTENTS[0], b"changed"))

    assert first == second
    assert first.is_complete
    assert first.issues == ()
    assert first.verification is not None
    assert [package.matches for package in first.verification.packages] == [True, False]
    assert first.verification.all_match is False


def test_payload_order_is_authoritative_and_not_rejoined() -> None:
    result = verify_class_world_artifact_contents(_plan_result(), tuple(reversed(_CONTENTS)))

    assert result.verification is not None
    assert [package.matches for package in result.verification.packages] == [False, False]


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (None, ClassWorldArtifactContentVerificationIssueCode.PLAN_RESULT_REQUIRED),
        (object(), ClassWorldArtifactContentVerificationIssueCode.PLAN_RESULT_INVALID),
        ((), ClassWorldArtifactContentVerificationIssueCode.PLAN_RESULT_INVALID),
    ],
)
def test_missing_or_wrong_plan_result_fails_before_content(
    candidate: object,
    expected: ClassWorldArtifactContentVerificationIssueCode,
) -> None:
    result = verify_class_world_artifact_contents(candidate, object())  # type: ignore[arg-type]

    assert result.verification is None
    assert _codes(result) == [expected]


def test_failed_plan_result_is_not_reinterpreted() -> None:
    failed = ClassWorldAssemblyPlanResult(
        plan=None,
        issues=(
            ClassWorldAssemblyPlanIssue(
                ClassWorldAssemblyPlanIssueCode.INVENTORY_NOT_BUILT,
                "not built",
                "inventory_result",
            ),
        ),
    )

    result = verify_class_world_artifact_contents(failed, _CONTENTS)

    assert result.verification is None
    assert _codes(result) == [ClassWorldArtifactContentVerificationIssueCode.PLAN_NOT_BUILT]


def test_forged_plan_output_fails_closed_without_recomputing_it() -> None:
    valid = _plan_result()
    assert valid.plan is not None
    candidates = (
        replace(valid.plan, contract_version="0.2"),
        replace(valid.plan, input_digest=object()),
        replace(valid.plan, inventory=object()),
        replace(
            valid.plan,
            inventory=replace(valid.plan.inventory, contract_version="0.2"),
        ),
        replace(
            valid.plan,
            inventory=replace(
                valid.plan.inventory,
                artifacts=(replace(valid.plan.inventory.artifacts[0], digest_hex="A" * 64),),
            ),
        ),
    )

    results = [
        verify_class_world_artifact_contents(replace(valid, plan=plan), _CONTENTS)
        for plan in candidates
    ]

    assert all(result.verification is None for result in results)
    assert all(
        _codes(result) == [ClassWorldArtifactContentVerificationIssueCode.PLAN_INVALID]
        for result in results
    )


@pytest.mark.parametrize("invalid", [None, [], iter(_CONTENTS), object()])
def test_contents_must_be_an_immutable_tuple(invalid: object) -> None:
    result = verify_class_world_artifact_contents(_plan_result(), invalid)  # type: ignore[arg-type]

    assert result.verification is None
    assert _codes(result) == [
        ClassWorldArtifactContentVerificationIssueCode.ARTIFACT_CONTENTS_REQUIRED
    ]


@pytest.mark.parametrize("contents", [(), (_CONTENTS[0],), (*_CONTENTS, b"extra")])
def test_content_count_must_equal_planned_artifact_count(contents: tuple[bytes, ...]) -> None:
    result = verify_class_world_artifact_contents(_plan_result(), contents)

    assert result.verification is None
    assert _codes(result) == [
        ClassWorldArtifactContentVerificationIssueCode.ARTIFACT_CONTENT_COUNT_MISMATCH
    ]


def test_invalid_payload_types_report_all_indexes_before_hashing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan_result = _plan_result()

    def fail_hash(*args: object, **kwargs: object) -> None:
        raise AssertionError("hashing must not start for invalid payload types")

    monkeypatch.setattr(verification_module.hashlib, "sha256", fail_hash)

    result = verify_class_world_artifact_contents(
        plan_result,
        (bytearray(_CONTENTS[0]), memoryview(_CONTENTS[1])),  # type: ignore[arg-type]
    )

    assert result.verification is None
    assert _codes(result) == [
        ClassWorldArtifactContentVerificationIssueCode.ARTIFACT_CONTENT_INVALID_TYPE,
        ClassWorldArtifactContentVerificationIssueCode.ARTIFACT_CONTENT_INVALID_TYPE,
    ]
    assert [issue.artifact_index for issue in result.issues] == [0, 1]


def test_layer_does_not_repeat_upstream_behavior_or_perform_io_or_execution() -> None:
    source = Path(verification_module.__file__).read_text(encoding="utf-8").lower()
    forbidden = (
        "build_class_world_assembly_plan",
        "build_class_world_artifact_inventory",
        "verify_class_world_release_declaration",
        "_canonical_input_bytes",
        "read_bytes",
        "read_text",
        "open(",
        "pathlib",
        "load_explorer_package",
        "apply_package_set_plan",
        "subprocess",
        "pygame",
        "signature",
        "approval",
        "publish",
        "deploy",
        "auth",
    )

    assert all(term not in source for term in forbidden)


def test_public_exports_are_explicit() -> None:
    import explore.packages as packages

    expected = {
        "verify_class_world_artifact_contents",
        "ClassWorldPackageArtifactContentDigest",
        "ClassWorldPackageArtifactContentVerification",
        "ClassWorldArtifactContentVerification",
        "ClassWorldArtifactContentVerificationIssue",
        "ClassWorldArtifactContentVerificationIssueCode",
        "ClassWorldArtifactContentVerificationResult",
        "SUPPORTED_CLASS_WORLD_ARTIFACT_CONTENT_VERIFICATION_CONTRACT_VERSION",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
    assert not hasattr(packages, "_plan_is_usable")
