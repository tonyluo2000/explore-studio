"""Behavior tests for atomic verified class-world materialization v0.1."""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

from explore.packages import (
    SUPPORTED_CLASS_WORLD_VERIFIED_MATERIALIZATION_CONTRACT_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldArtifactInventory,
    ClassWorldArtifactInventoryResult,
    ClassWorldAssemblyPlanResult,
    ClassWorldCohort,
    ClassWorldConfigurationSpec,
    ClassWorldMaterializationPlanIssue,
    ClassWorldMaterializationPlanIssueCode,
    ClassWorldMaterializationPlanResult,
    ClassWorldPackageArtifactDeclaration,
    ClassWorldPackageArtifactFileBinding,
    ClassWorldPackagePin,
    ClassWorldVerifiedMaterializationIssueCode,
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
    materialize_verified_class_world_artifacts,
    verify_class_world_artifact_contents,
    verify_class_world_artifact_files,
)
from explore.packages import (
    class_world_artifact_file_verification as file_verification_module,
)
from explore.packages import (
    class_world_verified_materialization as materialization_module,
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


def _write_sources(root: Path, contents: tuple[bytes, bytes] = _CONTENTS) -> None:
    (root / "nested").mkdir(parents=True, exist_ok=True)
    (root / "zeta.pkg").write_bytes(contents[0])
    (root / "nested" / "alpha.pkg").write_bytes(contents[1])


def _plan_result(source_root: Path) -> ClassWorldMaterializationPlanResult:
    _write_sources(source_root)
    file_result = verify_class_world_artifact_files(
        _assembly_plan_result(),
        source_root,
        _bindings(),
    )
    result = build_class_world_materialization_plan(file_result)
    assert result.plan is not None
    return result


def _codes(result) -> list[ClassWorldVerifiedMaterializationIssueCode]:
    return [issue.code for issue in result.issues]


def _stage_names(parent: Path) -> list[str]:
    return sorted(
        path.name for path in parent.iterdir() if path.name.startswith(".class-world-stage-")
    )


def test_reverifies_and_atomically_materializes_only_authorized_paths(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    plan_result = _plan_result(source)
    output = output_parent / "release"

    result = materialize_verified_class_world_artifacts(plan_result, source, output)

    assert result.is_materialized
    assert result.issues == ()
    assert result.materialization is not None
    assert result.source_verification is result.materialization.source_verification
    assert result.source_verification is not plan_result.plan.file_verification
    assert result.source_verification == plan_result.plan.file_verification
    assert result.materialization.plan is plan_result.plan
    assert result.materialization.contract_version == "0.1"
    assert result.materialization.total_bytes == sum(len(content) for content in _CONTENTS)
    assert [package.bytes_written for package in result.materialization.packages] == [
        len(content) for content in _CONTENTS
    ]
    expected = {
        "packages/zeta-character/2.1.0/artifact": _CONTENTS[0],
        "packages/alpha-object/1.4.2/artifact": _CONTENTS[1],
    }
    actual = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    assert actual == expected
    assert _stage_names(output_parent) == []
    assert stat.S_IMODE(output.stat().st_mode) == 0o755
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o644 for path in output.rglob("artifact"))
    assert [field.name for field in fields(result.materialization)] == [
        "contract_version",
        "plan",
        "source_verification",
        "packages",
        "total_bytes",
    ]
    assert SUPPORTED_CLASS_WORLD_VERIFIED_MATERIALIZATION_CONTRACT_VERSION == "0.1"
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.materialization.total_bytes = 0  # type: ignore[misc]


def test_exact_bytes_delegated_to_existing_verifier_are_written(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    plan_result = _plan_result(source)
    delegated: list[tuple[object, tuple[bytes, ...]]] = []

    def spy(plan: object, contents: tuple[bytes, ...]):
        delegated.append((plan, contents))
        return verify_class_world_artifact_contents(plan, contents)  # type: ignore[arg-type]

    monkeypatch.setattr(file_verification_module, "verify_class_world_artifact_contents", spy)

    result = materialize_verified_class_world_artifacts(
        plan_result,
        source,
        output_parent / "release",
    )

    assert result.is_materialized
    assert len(delegated) == 1
    assert delegated[0][1] == _CONTENTS
    assert [
        (output_parent / "release" / package.relative_path).read_bytes()
        for package in plan_result.plan.packages
    ] == list(delegated[0][1])


def test_changed_source_fails_before_any_destination_write(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    plan_result = _plan_result(source)
    (source / "nested" / "alpha.pkg").write_bytes(b"changed after planning")
    output = output_parent / "release"

    result = materialize_verified_class_world_artifacts(plan_result, source, output)

    assert result.materialization is None
    assert _codes(result) == [ClassWorldVerifiedMaterializationIssueCode.SOURCE_CONTENT_MISMATCH]
    assert result.source_verification is not None
    assert result.source_verification.content_verification is not None
    assert result.source_verification.content_verification.verification is not None
    assert result.source_verification.content_verification.verification.all_match is False
    assert not output.exists()
    assert _stage_names(output_parent) == []


def test_source_change_after_verification_cannot_change_staged_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    plan_result = _plan_result(source)
    original = materialization_module._write_package
    changed = False

    def change_source_then_write(*args: object) -> None:
        nonlocal changed
        if not changed:
            changed = True
            (source / "zeta.pkg").write_bytes(b"changed after fresh verification")
        original(*args)  # type: ignore[arg-type]

    monkeypatch.setattr(materialization_module, "_write_package", change_source_then_write)
    output = output_parent / "release"

    result = materialize_verified_class_world_artifacts(plan_result, source, output)

    assert result.is_materialized
    assert changed
    assert (output / "packages/zeta-character/2.1.0/artifact").read_bytes() == _CONTENTS[0]
    assert (source / "zeta.pkg").read_bytes() != _CONTENTS[0]


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (None, ClassWorldVerifiedMaterializationIssueCode.PLAN_RESULT_REQUIRED),
        (object(), ClassWorldVerifiedMaterializationIssueCode.PLAN_RESULT_INVALID),
        ((), ClassWorldVerifiedMaterializationIssueCode.PLAN_RESULT_INVALID),
    ],
)
def test_invalid_plan_precedes_root_inspection(candidate: object, expected) -> None:
    result = materialize_verified_class_world_artifacts(  # type: ignore[arg-type]
        candidate,
        object(),
        object(),
    )

    assert result.materialization is None
    assert result.source_verification is None
    assert _codes(result) == [expected]


def test_failed_and_forged_plans_fail_before_root_inspection(tmp_path: Path) -> None:
    source = tmp_path / "source"
    valid = _plan_result(source)
    failed = ClassWorldMaterializationPlanResult(
        plan=None,
        issues=(
            ClassWorldMaterializationPlanIssue(
                ClassWorldMaterializationPlanIssueCode.FILE_VERIFICATION_NOT_COMPLETE,
                "failed",
                "file_verification_result",
            ),
        ),
    )
    assert valid.plan is not None
    forged = replace(valid, plan=replace(valid.plan, total_bytes=valid.plan.total_bytes + 1))

    failed_result = materialize_verified_class_world_artifacts(failed, object(), object())
    forged_result = materialize_verified_class_world_artifacts(forged, object(), object())

    assert _codes(failed_result) == [ClassWorldVerifiedMaterializationIssueCode.PLAN_NOT_BUILT]
    assert _codes(forged_result) == [ClassWorldVerifiedMaterializationIssueCode.PLAN_INCONSISTENT]


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        (None, ClassWorldVerifiedMaterializationIssueCode.OUTPUT_ROOT_REQUIRED),
        (" ", ClassWorldVerifiedMaterializationIssueCode.OUTPUT_ROOT_REQUIRED),
        (object(), ClassWorldVerifiedMaterializationIssueCode.OUTPUT_ROOT_INVALID_TYPE),
        ("relative", ClassWorldVerifiedMaterializationIssueCode.OUTPUT_ROOT_NOT_ABSOLUTE),
    ],
)
def test_output_root_value_fails_before_source_reverification(
    tmp_path: Path,
    output: object,
    expected: ClassWorldVerifiedMaterializationIssueCode,
) -> None:
    source = tmp_path / "source"
    plan_result = _plan_result(source)
    (source / "zeta.pkg").write_bytes(b"changed")

    result = materialize_verified_class_world_artifacts(  # type: ignore[arg-type]
        plan_result,
        source,
        output,
    )

    assert _codes(result) == [expected]
    assert result.source_verification is None


def test_rejects_missing_nondirectory_existing_and_symlink_destinations(tmp_path: Path) -> None:
    source = tmp_path / "source"
    plan_result = _plan_result(source)
    missing = tmp_path / "missing" / "release"
    parent_file = tmp_path / "parent-file"
    parent_file.write_text("not a directory", encoding="utf-8")
    existing_file = tmp_path / "existing-file"
    existing_file.write_text("keep", encoding="utf-8")
    existing_directory = tmp_path / "existing-directory"
    existing_directory.mkdir()
    symlink = tmp_path / "destination-link"
    try:
        symlink.symlink_to(existing_directory, target_is_directory=True)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Symlinks unavailable: {error}")

    outputs = (missing, parent_file / "release", existing_file, existing_directory, symlink)
    results = [
        materialize_verified_class_world_artifacts(plan_result, source, path) for path in outputs
    ]

    assert [_codes(result)[0] for result in results] == [
        ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_NOT_FOUND,
        ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_NOT_DIRECTORY,
        ClassWorldVerifiedMaterializationIssueCode.OUTPUT_DESTINATION_EXISTS,
        ClassWorldVerifiedMaterializationIssueCode.OUTPUT_DESTINATION_EXISTS,
        ClassWorldVerifiedMaterializationIssueCode.OUTPUT_DESTINATION_EXISTS,
    ]
    assert existing_file.read_text(encoding="utf-8") == "keep"


def test_rejects_symlinked_output_parent_and_ancestor(tmp_path: Path) -> None:
    source = tmp_path / "source"
    plan_result = _plan_result(source)
    real = tmp_path / "real"
    real.mkdir()
    nested = real / "nested"
    nested.mkdir()
    parent_link = tmp_path / "parent-link"
    ancestor_link = tmp_path / "ancestor-link"
    try:
        parent_link.symlink_to(real, target_is_directory=True)
        ancestor_link.symlink_to(real, target_is_directory=True)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Symlinks unavailable: {error}")

    direct = materialize_verified_class_world_artifacts(
        plan_result,
        source,
        parent_link / "release",
    )
    ancestor = materialize_verified_class_world_artifacts(
        plan_result,
        source,
        ancestor_link / "nested" / "release",
    )

    assert _codes(direct) == [
        ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_SYMLINK_NOT_ALLOWED
    ]
    assert _codes(ancestor) == [
        ClassWorldVerifiedMaterializationIssueCode.OUTPUT_PARENT_SYMLINK_NOT_ALLOWED
    ]
    assert not (real / "release").exists()
    assert not (nested / "release").exists()


def test_source_failure_and_intermediate_symlink_are_delegated_without_writes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    plan_result = _plan_result(source)
    original_nested = source / "nested"
    moved_nested = source / "moved-nested"
    original_nested.rename(moved_nested)
    try:
        original_nested.symlink_to(moved_nested, target_is_directory=True)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Symlinks unavailable: {error}")
    output = output_parent / "release"

    result = materialize_verified_class_world_artifacts(plan_result, source, output)

    assert _codes(result) == [ClassWorldVerifiedMaterializationIssueCode.SOURCE_VERIFICATION_FAILED]
    assert result.source_verification is not None
    assert result.source_verification.issues
    assert not output.exists()
    assert _stage_names(output_parent) == []


def test_intermediate_directory_swap_after_inspection_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    plan_result = _plan_result(source)
    original_inspect = file_verification_module._inspect_files
    swapped = False

    def inspect_then_swap(*args: object, **kwargs: object):
        nonlocal swapped
        result = original_inspect(*args, **kwargs)  # type: ignore[arg-type]
        if not result[1] and not swapped:
            swapped = True
            nested = source / "nested"
            moved = source / "moved-nested"
            nested.rename(moved)
            nested.symlink_to(moved, target_is_directory=True)
        return result

    monkeypatch.setattr(file_verification_module, "_inspect_files", inspect_then_swap)
    output = output_parent / "release"

    result = materialize_verified_class_world_artifacts(plan_result, source, output)

    assert swapped
    assert _codes(result) == [ClassWorldVerifiedMaterializationIssueCode.SOURCE_VERIFICATION_FAILED]
    assert result.source_verification is not None
    assert result.source_verification.issues
    assert not output.exists()
    assert _stage_names(output_parent) == []


def test_source_file_alias_is_rejected_without_writes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    plan_result = _plan_result(source)
    alpha = source / "nested" / "alpha.pkg"
    alpha.unlink()
    try:
        os.link(source / "zeta.pkg", alpha)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Hard links unavailable: {error}")
    output = output_parent / "release"

    result = materialize_verified_class_world_artifacts(plan_result, source, output)

    assert _codes(result) == [ClassWorldVerifiedMaterializationIssueCode.SOURCE_VERIFICATION_FAILED]
    assert result.source_verification is not None
    assert result.source_verification.issues
    assert not output.exists()
    assert _stage_names(output_parent) == []


def test_rejects_output_inside_source_root(tmp_path: Path) -> None:
    source = tmp_path / "source"
    plan_result = _plan_result(source)

    result = materialize_verified_class_world_artifacts(
        plan_result,
        source,
        source / "release",
    )

    assert _codes(result) == [ClassWorldVerifiedMaterializationIssueCode.OUTPUT_OVERLAPS_SOURCE]
    assert result.source_verification is not None
    assert not (source / "release").exists()


def test_write_failure_cleans_staging_and_publishes_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    plan_result = _plan_result(source)
    original = materialization_module._write_package
    calls = 0

    def fail_second(*args: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated write failure")
        original(*args)  # type: ignore[arg-type]

    monkeypatch.setattr(materialization_module, "_write_package", fail_second)
    output = output_parent / "release"

    result = materialize_verified_class_world_artifacts(plan_result, source, output)

    assert _codes(result) == [ClassWorldVerifiedMaterializationIssueCode.DESTINATION_WRITE_FAILED]
    assert not output.exists()
    assert _stage_names(output_parent) == []


def test_atomic_publish_failure_cleans_complete_staging_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    plan_result = _plan_result(source)

    def fail_replace(*args: object, **kwargs: object) -> None:
        raise OSError("simulated atomic publish failure")

    monkeypatch.setattr(materialization_module.os, "replace", fail_replace)
    output = output_parent / "release"

    result = materialize_verified_class_world_artifacts(plan_result, source, output)

    assert _codes(result) == [ClassWorldVerifiedMaterializationIssueCode.ATOMIC_PUBLISH_FAILED]
    assert not output.exists()
    assert _stage_names(output_parent) == []


def test_writes_are_chunk_bounded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    plan_result = _plan_result(source)
    original = materialization_module.os.write
    sizes: list[int] = []

    def spy(descriptor: int, content: object) -> int:
        sizes.append(len(content))  # type: ignore[arg-type]
        return original(descriptor, content)  # type: ignore[arg-type]

    monkeypatch.setattr(materialization_module.os, "write", spy)

    result = materialize_verified_class_world_artifacts(
        plan_result,
        source,
        output_parent / "release",
    )

    assert result.is_materialized
    assert sizes
    assert max(sizes) <= materialization_module._WRITE_CHUNK_BYTES
    assert sum(sizes) == sum(len(content) for content in _CONTENTS)


def test_equivalent_runs_publish_equal_authorized_trees(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output_parent = tmp_path / "outputs"
    output_parent.mkdir()
    plan_result = _plan_result(source)
    first = output_parent / "first"
    second = output_parent / "second"

    first_result = materialize_verified_class_world_artifacts(plan_result, source, first)
    second_result = materialize_verified_class_world_artifacts(plan_result, source, second)

    assert first_result.materialization == second_result.materialization
    first_tree = {
        path.relative_to(first).as_posix(): path.read_bytes()
        for path in first.rglob("*")
        if path.is_file()
    }
    second_tree = {
        path.relative_to(second).as_posix(): path.read_bytes()
        for path in second.rglob("*")
        if path.is_file()
    }
    assert first_tree == second_tree


def test_materializer_does_not_duplicate_hashing_or_cross_forbidden_boundaries() -> None:
    source = Path(materialization_module.__file__).read_text(encoding="utf-8").lower()
    forbidden = (
        "hashlib",
        "verify_class_world_artifact_contents",
        "archive",
        "extract",
        "load_explorer_package",
        "apply_package_set_plan",
        "subprocess",
        "pygame",
        "requests",
        "auth",
        "sign",
        "approve",
        "publication",
        "deploy",
    )

    assert source.count("_verify_class_world_artifact_files_with_contents(") == 1
    assert all(term not in source for term in forbidden)


def test_public_exports_preserve_prior_contracts() -> None:
    import explore.packages as packages

    expected = {
        "materialize_verified_class_world_artifacts",
        "ClassWorldMaterializedPackage",
        "ClassWorldVerifiedMaterialization",
        "ClassWorldVerifiedMaterializationIssue",
        "ClassWorldVerifiedMaterializationIssueCode",
        "ClassWorldVerifiedMaterializationResult",
        "SUPPORTED_CLASS_WORLD_VERIFIED_MATERIALIZATION_CONTRACT_VERSION",
        "build_class_world_materialization_plan",
        "verify_class_world_artifact_files",
        "verify_class_world_artifact_contents",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
    assert not hasattr(packages, "_verify_class_world_artifact_files_with_contents")
