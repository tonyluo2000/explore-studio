"""Behavior tests for deterministic class-world materialization planning v0.1."""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

from explore.packages import (
    SUPPORTED_CLASS_WORLD_MATERIALIZATION_PLAN_CONTRACT_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldArtifactFileVerificationIssue,
    ClassWorldArtifactFileVerificationIssueCode,
    ClassWorldArtifactInventory,
    ClassWorldArtifactInventoryResult,
    ClassWorldAssemblyPlanResult,
    ClassWorldCohort,
    ClassWorldConfigurationSpec,
    ClassWorldMaterializationPlanIssueCode,
    ClassWorldPackageArtifactDeclaration,
    ClassWorldPackageArtifactFileBinding,
    ClassWorldPackagePin,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    build_class_world_assembly_plan,
    build_class_world_configuration,
    build_class_world_materialization_plan,
    build_class_world_release_declaration,
    compute_class_world_release_declaration_digest,
    verify_class_world_artifact_files,
)
from explore.packages import class_world_materialization_plan as plan_module
from explore.packages.class_world_artifact_file_verification_models import (
    ClassWorldArtifactFileVerificationResult,
)

_CONTENTS = (b"zeta package artifact\x00", b"alpha package artifact\xff")


def _assembly_plan_result() -> ClassWorldAssemblyPlanResult:
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


def _bindings() -> tuple[ClassWorldPackageArtifactFileBinding, ...]:
    return (
        ClassWorldPackageArtifactFileBinding("zeta-character", "2.1.0", "zeta.pkg"),
        ClassWorldPackageArtifactFileBinding("alpha-object", "1.4.2", "nested/alpha.pkg"),
    )


def _file_result(
    tmp_path: Path,
    contents: tuple[bytes, bytes] = _CONTENTS,
) -> ClassWorldArtifactFileVerificationResult:
    (tmp_path / "nested").mkdir(parents=True, exist_ok=True)
    (tmp_path / "zeta.pkg").write_bytes(contents[0])
    (tmp_path / "nested" / "alpha.pkg").write_bytes(contents[1])
    return verify_class_world_artifact_files(_assembly_plan_result(), tmp_path, _bindings())


def _codes(result) -> list[ClassWorldMaterializationPlanIssueCode]:
    return [issue.code for issue in result.issues]


def test_builds_canonical_package_separated_layout_from_matching_files(tmp_path: Path) -> None:
    verified = _file_result(tmp_path)

    result = build_class_world_materialization_plan(verified)

    assert result.is_planned
    assert result.issues == ()
    assert result.plan is not None
    assert result.plan.contract_version == "0.1"
    assert result.plan.file_verification is verified
    assert [package.relative_path for package in result.plan.packages] == [
        "packages/zeta-character/2.1.0/artifact",
        "packages/alpha-object/1.4.2/artifact",
    ]
    assert [package.source for package in result.plan.packages] == list(verified.files)
    assert all(
        package.source is source
        for package, source in zip(result.plan.packages, verified.files, strict=True)
    )
    assert result.plan.total_bytes == sum(len(content) for content in _CONTENTS)
    assert [field.name for field in fields(result.plan)] == [
        "contract_version",
        "file_verification",
        "packages",
        "total_bytes",
    ]
    assert SUPPORTED_CLASS_WORLD_MATERIALIZATION_PLAN_CONTRACT_VERSION == "0.1"
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.plan.packages = ()  # type: ignore[misc]


def test_same_verified_input_produces_equal_plan_without_mutating_files(tmp_path: Path) -> None:
    verified = _file_result(tmp_path)
    before = {
        path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*.pkg")
    }

    first = build_class_world_materialization_plan(verified)
    second = build_class_world_materialization_plan(verified)

    after = {
        path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*.pkg")
    }
    assert first == second
    assert before == after
    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*")) == [
        "nested",
        "nested/alpha.pkg",
        "zeta.pkg",
    ]


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (None, ClassWorldMaterializationPlanIssueCode.FILE_VERIFICATION_RESULT_REQUIRED),
        (object(), ClassWorldMaterializationPlanIssueCode.FILE_VERIFICATION_RESULT_INVALID),
        ((), ClassWorldMaterializationPlanIssueCode.FILE_VERIFICATION_RESULT_INVALID),
    ],
)
def test_rejects_missing_or_wrong_upstream_result_before_planning(
    candidate: object,
    expected: ClassWorldMaterializationPlanIssueCode,
) -> None:
    result = build_class_world_materialization_plan(candidate)  # type: ignore[arg-type]

    assert result.plan is None
    assert _codes(result) == [expected]


def test_rejects_failed_or_incomplete_file_verification(tmp_path: Path) -> None:
    valid = _file_result(tmp_path)
    issue = ClassWorldArtifactFileVerificationIssue(
        ClassWorldArtifactFileVerificationIssueCode.FILE_READ_FAILED,
        "failed",
        "bindings[0]",
    )
    candidates = (
        replace(valid, issues=(issue,)),
        replace(valid, files=()),
        replace(valid, content_verification=None),
        replace(valid, contract_version="9.9"),
    )

    results = [build_class_world_materialization_plan(candidate) for candidate in candidates]

    assert all(result.plan is None for result in results)
    assert all(
        _codes(result) == [ClassWorldMaterializationPlanIssueCode.FILE_VERIFICATION_NOT_COMPLETE]
        for result in results
    )


def test_digest_mismatch_is_a_fail_closed_planning_issue(tmp_path: Path) -> None:
    verified = _file_result(tmp_path, (_CONTENTS[0], b"changed"))

    result = build_class_world_materialization_plan(verified)

    assert result.plan is None
    assert _codes(result) == [ClassWorldMaterializationPlanIssueCode.ARTIFACT_CONTENT_MISMATCH]
    assert result.issues[0].package_id == "alpha-object"
    assert result.issues[0].package_index == 1


def test_reports_every_digest_mismatch_in_canonical_package_order(tmp_path: Path) -> None:
    verified = _file_result(tmp_path, (b"wrong-zeta", b"wrong-alpha"))

    result = build_class_world_materialization_plan(verified)

    assert result.plan is None
    assert _codes(result) == [
        ClassWorldMaterializationPlanIssueCode.ARTIFACT_CONTENT_MISMATCH,
        ClassWorldMaterializationPlanIssueCode.ARTIFACT_CONTENT_MISMATCH,
    ]
    assert [issue.package_id for issue in result.issues] == [
        "zeta-character",
        "alpha-object",
    ]


def test_forged_upstream_graphs_fail_closed_as_inconsistent(tmp_path: Path) -> None:
    valid = _file_result(tmp_path)
    assert valid.content_verification is not None
    assert valid.content_verification.verification is not None
    verification = valid.content_verification.verification
    first_file = valid.files[0]
    first_package = verification.packages[0]
    candidates = (
        replace(valid, files=(object(), *valid.files[1:])),  # type: ignore[arg-type]
        replace(valid, files=(replace(first_file, bytes_read=-1), *valid.files[1:])),
        replace(
            valid,
            files=(
                replace(
                    first_file,
                    binding=replace(first_file.binding, package_version="9.9.9"),
                ),
                *valid.files[1:],
            ),
        ),
        replace(
            valid,
            content_verification=replace(
                valid.content_verification,
                verification=replace(
                    verification,
                    packages=(replace(first_package, matches=False), *verification.packages[1:]),
                ),
            ),
        ),
        replace(valid, files=tuple(reversed(valid.files))),
    )

    results = [build_class_world_materialization_plan(candidate) for candidate in candidates]

    assert all(result.plan is None for result in results)
    assert all(result.issues for result in results)
    assert all(
        all(
            code is ClassWorldMaterializationPlanIssueCode.FILE_VERIFICATION_INCONSISTENT
            for code in _codes(result)
        )
        for result in results
    )


def test_planner_stays_pure_and_does_not_duplicate_upstream_work() -> None:
    source = Path(plan_module.__file__).read_text(encoding="utf-8").lower()
    forbidden = (
        "hashlib",
        "json",
        "pathlib",
        " os",
        "open(",
        "read_",
        "write_",
        "mkdir",
        "replace(",
        "verify_class_world_artifact",
        "build_class_world_assembly_plan",
        "build_class_world_artifact_inventory",
        "load_explorer_package",
        "apply_package_set_plan",
        "subprocess",
        "pygame",
        "requests",
        "auth",
        "sign",
        "approve",
        "publish",
        "deploy",
    )

    assert all(term not in source for term in forbidden)


def test_public_exports_preserve_prior_boundaries() -> None:
    import explore.packages as packages

    expected = {
        "build_class_world_materialization_plan",
        "ClassWorldPackageMaterialization",
        "ClassWorldMaterializationPlan",
        "ClassWorldMaterializationPlanIssue",
        "ClassWorldMaterializationPlanIssueCode",
        "ClassWorldMaterializationPlanResult",
        "SUPPORTED_CLASS_WORLD_MATERIALIZATION_PLAN_CONTRACT_VERSION",
        "verify_class_world_artifact_files",
        "verify_class_world_artifact_contents",
        "build_class_world_assembly_plan",
        "build_class_world_artifact_inventory",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
    assert not hasattr(packages, "_structural_issues")
