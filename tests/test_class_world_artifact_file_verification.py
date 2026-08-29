"""Behavior tests for bounded class-world artifact-file verification v0.1."""

from __future__ import annotations

import hashlib
import os
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

from explore.packages import (
    MAX_CLASS_WORLD_ARTIFACT_SET_BYTES,
    MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES,
    SUPPORTED_CLASS_WORLD_ARTIFACT_FILE_VERIFICATION_CONTRACT_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldArtifactFileVerificationIssueCode,
    ClassWorldArtifactInventory,
    ClassWorldArtifactInventoryResult,
    ClassWorldAssemblyPlanIssue,
    ClassWorldAssemblyPlanIssueCode,
    ClassWorldAssemblyPlanResult,
    ClassWorldCohort,
    ClassWorldConfigurationSpec,
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
    build_class_world_release_declaration,
    compute_class_world_release_declaration_digest,
    verify_class_world_artifact_contents,
    verify_class_world_artifact_files,
)
from explore.packages import class_world_artifact_file_verification as verification_module

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


def _bindings() -> tuple[ClassWorldPackageArtifactFileBinding, ...]:
    return (
        ClassWorldPackageArtifactFileBinding("zeta-character", "2.1.0", "zeta.pkg"),
        ClassWorldPackageArtifactFileBinding("alpha-object", "1.4.2", "nested/alpha.pkg"),
    )


def _write_files(root: Path, contents: tuple[bytes, bytes] = _CONTENTS) -> None:
    (root / "nested").mkdir(parents=True, exist_ok=True)
    (root / "zeta.pkg").write_bytes(contents[0])
    (root / "nested" / "alpha.pkg").write_bytes(contents[1])


def _codes(result) -> list[ClassWorldArtifactFileVerificationIssueCode]:
    return [issue.code for issue in result.issues]


def test_reads_in_plan_order_and_delegates_bytes_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan_result = _plan_result()
    _write_files(tmp_path)
    supplied = tuple(reversed(_bindings()))
    delegated: list[tuple[object, tuple[bytes, ...]]] = []

    def spy(plan: object, contents: tuple[bytes, ...]):
        delegated.append((plan, contents))
        return verify_class_world_artifact_contents(plan, contents)  # type: ignore[arg-type]

    monkeypatch.setattr(verification_module, "verify_class_world_artifact_contents", spy)

    result = verify_class_world_artifact_files(plan_result, tmp_path, supplied)

    assert result.is_complete
    assert result.issues == ()
    assert result.content_verification is not None
    assert result.content_verification.verification is not None
    assert result.content_verification.verification.all_match is True
    assert delegated == [(plan_result, _CONTENTS)]
    assert [file.binding.package_id for file in result.files] == [
        "zeta-character",
        "alpha-object",
    ]
    assert result.files[0].binding is supplied[1]
    assert result.files[1].binding is supplied[0]
    assert [file.bytes_read for file in result.files] == [len(value) for value in _CONTENTS]
    assert [field.name for field in fields(result)] == [
        "contract_version",
        "files",
        "content_verification",
        "issues",
    ]
    assert SUPPORTED_CLASS_WORLD_ARTIFACT_FILE_VERIFICATION_CONTRACT_VERSION == "0.1"
    assert MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES == 64 * 1024 * 1024
    assert MAX_CLASS_WORLD_ARTIFACT_SET_BYTES == 256 * 1024 * 1024
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.files = ()  # type: ignore[misc]


def test_digest_mismatch_remains_delegated_completed_state(tmp_path: Path) -> None:
    _write_files(tmp_path, (_CONTENTS[0], b"changed"))

    result = verify_class_world_artifact_files(_plan_result(), tmp_path, _bindings())

    assert result.is_complete
    assert result.issues == ()
    assert result.content_verification is not None
    assert result.content_verification.verification is not None
    assert [package.matches for package in result.content_verification.verification.packages] == [
        True,
        False,
    ]


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        (None, ClassWorldArtifactFileVerificationIssueCode.PLAN_RESULT_REQUIRED),
        (object(), ClassWorldArtifactFileVerificationIssueCode.PLAN_RESULT_INVALID),
        ((), ClassWorldArtifactFileVerificationIssueCode.PLAN_RESULT_INVALID),
    ],
)
def test_invalid_plan_result_precedes_root_or_binding_inspection(
    candidate: object,
    expected: ClassWorldArtifactFileVerificationIssueCode,
) -> None:
    result = verify_class_world_artifact_files(  # type: ignore[arg-type]
        candidate,
        object(),
        object(),
    )

    assert result.files == ()
    assert result.content_verification is None
    assert _codes(result) == [expected]


def test_failed_and_forged_plan_results_fail_closed(tmp_path: Path) -> None:
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
    valid = _plan_result()
    assert valid.plan is not None
    forged = replace(valid, plan=replace(valid.plan, input_digest=object()))

    failed_result = verify_class_world_artifact_files(failed, tmp_path, _bindings())
    forged_result = verify_class_world_artifact_files(forged, tmp_path, _bindings())

    assert _codes(failed_result) == [ClassWorldArtifactFileVerificationIssueCode.PLAN_NOT_BUILT]
    assert _codes(forged_result) == [ClassWorldArtifactFileVerificationIssueCode.PLAN_INVALID]


@pytest.mark.parametrize(
    ("root", "expected"),
    [
        (None, ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_REQUIRED),
        (" ", ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_REQUIRED),
        (object(), ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_INVALID_TYPE),
        ("relative", ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_NOT_ABSOLUTE),
    ],
)
def test_root_value_must_be_explicit_absolute_path(root: object, expected) -> None:
    result = verify_class_world_artifact_files(  # type: ignore[arg-type]
        _plan_result(),
        root,
        _bindings(),
    )

    assert _codes(result) == [expected]


def test_root_must_exist_be_directory_and_not_symlink(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    regular = tmp_path / "regular"
    regular.write_bytes(b"file")
    symlink = tmp_path / "root-link"
    try:
        symlink.symlink_to(tmp_path, target_is_directory=True)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Symlinks unavailable: {error}")

    results = [
        verify_class_world_artifact_files(_plan_result(), root, _bindings())
        for root in (missing, regular, symlink)
    ]

    assert [_codes(result)[0] for result in results] == [
        ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_NOT_FOUND,
        ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_NOT_DIRECTORY,
        ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_ROOT_SYMLINK_NOT_ALLOWED,
    ]


def test_bindings_must_be_immutable_and_exactly_typed(tmp_path: Path) -> None:
    tuple_result = verify_class_world_artifact_files(_plan_result(), tmp_path, [])  # type: ignore[arg-type]
    type_result = verify_class_world_artifact_files(_plan_result(), tmp_path, (object(),))  # type: ignore[arg-type]

    assert _codes(tuple_result) == [ClassWorldArtifactFileVerificationIssueCode.BINDINGS_REQUIRED]
    assert ClassWorldArtifactFileVerificationIssueCode.BINDING_INVALID_TYPE in _codes(type_result)
    assert ClassWorldArtifactFileVerificationIssueCode.BINDING_PACKAGE_MISSING in _codes(
        type_result
    )


def test_package_bindings_are_one_to_one_and_version_exact(tmp_path: Path) -> None:
    zeta, alpha = _bindings()
    cases = (
        (
            (zeta, replace(alpha, package_id="zeta-character")),
            ClassWorldArtifactFileVerificationIssueCode.BINDING_PACKAGE_DUPLICATE,
        ),
        (
            (zeta, replace(alpha, package_id="extra-package")),
            ClassWorldArtifactFileVerificationIssueCode.BINDING_PACKAGE_UNEXPECTED,
        ),
        (
            (zeta, replace(alpha, package_version="1.4.3")),
            ClassWorldArtifactFileVerificationIssueCode.BINDING_PACKAGE_VERSION_MISMATCH,
        ),
        ((zeta,), ClassWorldArtifactFileVerificationIssueCode.BINDING_PACKAGE_MISSING),
        (
            (zeta, replace(alpha, relative_path=zeta.relative_path)),
            ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_DUPLICATE,
        ),
    )

    results = [
        verify_class_world_artifact_files(_plan_result(), tmp_path, bindings)
        for bindings, _ in cases
    ]

    assert all(
        expected in _codes(result) for result, (_, expected) in zip(results, cases, strict=True)
    )
    assert all(result.files == () and result.content_verification is None for result in results)


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("", ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_REQUIRED),
        (Path("zeta.pkg"), ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_INVALID_TYPE),
        ("/zeta.pkg", ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_ABSOLUTE),
        ("C:/zeta.pkg", ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_ABSOLUTE),
        ("../zeta.pkg", ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_TRAVERSAL),
        ("nested/../zeta.pkg", ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_TRAVERSAL),
        ("./zeta.pkg", ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_INVALID),
        ("nested//zeta.pkg", ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_INVALID),
        ("nested\\zeta.pkg", ClassWorldArtifactFileVerificationIssueCode.BINDING_PATH_INVALID),
    ],
)
def test_binding_paths_must_be_canonical_safe_relative_strings(
    tmp_path: Path,
    path: object,
    expected: ClassWorldArtifactFileVerificationIssueCode,
) -> None:
    bindings = (replace(_bindings()[0], relative_path=path), _bindings()[1])  # type: ignore[arg-type]

    result = verify_class_world_artifact_files(_plan_result(), tmp_path, bindings)

    assert expected in _codes(result)
    assert result.files == ()


def test_missing_directory_and_nonregular_files_fail_atomically(tmp_path: Path) -> None:
    (tmp_path / "nested").mkdir()
    (tmp_path / "zeta.pkg").mkdir()

    result = verify_class_world_artifact_files(_plan_result(), tmp_path, _bindings())

    assert result.files == ()
    assert result.content_verification is None
    assert _codes(result) == [
        ClassWorldArtifactFileVerificationIssueCode.FILE_NOT_REGULAR,
        ClassWorldArtifactFileVerificationIssueCode.FILE_NOT_FOUND,
    ]


def test_symlink_at_any_binding_component_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (outside / "artifact.pkg").write_bytes(_CONTENTS[1])
    (tmp_path / "zeta.pkg").write_bytes(_CONTENTS[0])
    try:
        (tmp_path / "nested").symlink_to(outside, target_is_directory=True)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"Symlinks unavailable: {error}")

    result = verify_class_world_artifact_files(_plan_result(), tmp_path, _bindings())

    assert result.files == ()
    assert _codes(result) == [ClassWorldArtifactFileVerificationIssueCode.FILE_SYMLINK_NOT_ALLOWED]


def test_distinct_paths_to_same_file_identity_are_ambiguous(tmp_path: Path) -> None:
    _write_files(tmp_path)
    alias = tmp_path / "nested" / "alpha.pkg"
    alias.unlink()
    try:
        os.link(tmp_path / "zeta.pkg", alias)
    except OSError as error:
        pytest.skip(f"Hard links unavailable: {error}")

    result = verify_class_world_artifact_files(_plan_result(), tmp_path, _bindings())

    assert result.files == ()
    assert _codes(result) == [ClassWorldArtifactFileVerificationIssueCode.FILE_IDENTITY_DUPLICATE]


def test_per_file_and_aggregate_bounds_are_checked_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_files(tmp_path)
    monkeypatch.setattr(verification_module, "MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES", 4)

    per_file = verify_class_world_artifact_files(_plan_result(), tmp_path, _bindings())

    assert ClassWorldArtifactFileVerificationIssueCode.FILE_TOO_LARGE in _codes(per_file)

    monkeypatch.setattr(verification_module, "MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES", 1024)
    monkeypatch.setattr(verification_module, "MAX_CLASS_WORLD_ARTIFACT_SET_BYTES", 8)
    aggregate = verify_class_world_artifact_files(_plan_result(), tmp_path, _bindings())

    assert _codes(aggregate) == [ClassWorldArtifactFileVerificationIssueCode.ARTIFACT_SET_TOO_LARGE]


def test_read_failure_skips_content_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_files(tmp_path)

    def fail_open(*args: object, **kwargs: object) -> None:
        raise OSError("simulated")

    def fail_verifier(*args: object, **kwargs: object) -> None:
        raise AssertionError("content verifier must not run after read failure")

    monkeypatch.setattr(verification_module.os, "open", fail_open)
    monkeypatch.setattr(
        verification_module,
        "verify_class_world_artifact_contents",
        fail_verifier,
    )

    result = verify_class_world_artifact_files(_plan_result(), tmp_path, _bindings())

    assert result.files == ()
    assert result.content_verification is None
    assert _codes(result) == [ClassWorldArtifactFileVerificationIssueCode.FILE_READ_FAILED]


def test_layer_delegates_hashing_and_performs_no_package_or_trust_operations() -> None:
    source = Path(verification_module.__file__).read_text(encoding="utf-8").lower()
    forbidden = (
        "hashlib",
        "sha256(",
        "build_class_world_artifact_inventory",
        "build_class_world_assembly_plan",
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

    assert "verify_class_world_artifact_contents" in source
    assert all(term not in source for term in forbidden)


def test_public_exports_are_explicit() -> None:
    import explore.packages as packages

    expected = {
        "verify_class_world_artifact_files",
        "ClassWorldPackageArtifactFileBinding",
        "ClassWorldPackageArtifactFileRead",
        "ClassWorldArtifactFileVerificationIssue",
        "ClassWorldArtifactFileVerificationIssueCode",
        "ClassWorldArtifactFileVerificationResult",
        "MAX_CLASS_WORLD_PACKAGE_ARTIFACT_BYTES",
        "MAX_CLASS_WORLD_ARTIFACT_SET_BYTES",
        "SUPPORTED_CLASS_WORLD_ARTIFACT_FILE_VERIFICATION_CONTRACT_VERSION",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
    assert not hasattr(packages, "_validated_bindings")
