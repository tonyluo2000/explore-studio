"""Behavior tests for release-declaration digest verification v0.1."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path
from typing import Literal

import pytest

from explore.packages import (
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_VERIFICATION_CONTRACT_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldCohort,
    ClassWorldConfiguration,
    ClassWorldConfigurationSpec,
    ClassWorldPackagePin,
    ClassWorldReleaseDeclaration,
    ClassWorldReleaseDeclarationDigest,
    ClassWorldReleaseDeclarationDigestVerificationResult,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    build_class_world_configuration,
    build_class_world_release_declaration,
    compute_class_world_release_declaration_digest,
    verify_class_world_release_declaration_digest,
)
from explore.packages import (
    class_world_release_declaration_digest_verification as verification_module,
)

_PackageSpec = tuple[str, str, Literal["character", "object"]]
_CHARACTER_PACKAGE: _PackageSpec = (
    "zeta-character",
    "2.1.0-beta.1+class",
    "character",
)
_OBJECT_PACKAGE: _PackageSpec = ("alpha-lantern", "1.0.0", "object")


def _selected(specification: _PackageSpec) -> SelectedPackagePlan:
    package_id, package_version, contribution_type = specification
    provenance = PackageProvenance(package_id, package_version, "0.1")
    if contribution_type == "character":
        entry: CharacterRegistration | WorldObjectRegistration = CharacterRegistration(
            f"{package_id}:hero",
            "hero",
            provenance,
            CharacterRegistrationSpec("Exploratrice", 10, 20, "gold"),
            None,
        )
    else:
        entry = WorldObjectRegistration(
            f"{package_id}:lantern",
            "lantern",
            provenance,
            WorldObjectRegistrationSpec(
                "Lanterne",
                30,
                40,
                "green",
                "Regardez.",
                "Trouvée!",
            ),
            None,
        )
    return SelectedPackagePlan(
        package_id,
        package_version,
        provenance,
        StudentAPIRegistrationPlan(provenance, (entry,)),
    )


def _configuration(
    *,
    packages: tuple[_PackageSpec, ...] = (_CHARACTER_PACKAGE, _OBJECT_PACKAGE),
) -> ClassWorldConfiguration:
    selected = tuple(_selected(package) for package in packages)
    plan = PackageSetPlan(
        "0.1",
        selected,
        tuple(entry for package in selected for entry in package.registration_plan.entries),
    )
    result = build_class_world_configuration(
        ClassWorldConfigurationSpec(
            "0.1",
            "expedition-orion-fall-2026",
            "Expédition Orion — Automne 2026 🚀",
            "3.2.1",
            "1.4.0",
            "0.1",
            ClassWorldCohort("expedition-orion", "Expédition Orion 🚀"),
            tuple(
                ClassWorldPackagePin(package.package_id, package.package_version)
                for package in selected
            ),
        ),
        plan,
    )
    assert result.configuration is not None
    return result.configuration


def _declaration(
    configuration: ClassWorldConfiguration | None = None,
    *,
    release_id: str = "spring-showcase",
    release_version: str = "1.2.3-rc.1+school",
) -> ClassWorldReleaseDeclaration:
    result = build_class_world_release_declaration(
        configuration or _configuration(),
        release_id=release_id,
        release_version=release_version,
    )
    assert result.declaration is not None
    return result.declaration


def test_match_retains_expected_identity_and_returns_deterministic_frozen_result() -> None:
    declaration = _declaration()
    expected = compute_class_world_release_declaration_digest(declaration)

    first = verify_class_world_release_declaration_digest(declaration, expected)
    second = verify_class_world_release_declaration_digest(declaration, expected)

    assert first == second
    assert first.matches is True
    assert first.expected_digest is expected
    assert first.actual_digest == expected
    assert first.actual_digest is not expected
    assert [field.name for field in fields(first)] == [
        "expected_digest",
        "actual_digest",
        "matches",
    ]
    assert SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_VERIFICATION_CONTRACT_VERSION == "0.1"
    with pytest.raises((FrozenInstanceError, AttributeError)):
        first.matches = False  # type: ignore[misc]


@pytest.mark.parametrize(
    "other_declaration",
    [
        pytest.param(_declaration(release_id="autumn-showcase"), id="release-id"),
        pytest.param(_declaration(release_version="1.2.4"), id="release-version"),
        pytest.param(
            _declaration(_configuration(packages=(_CHARACTER_PACKAGE,))),
            id="package-configuration",
        ),
    ],
)
def test_valid_different_digest_is_normal_mismatch_result(
    other_declaration: ClassWorldReleaseDeclaration,
) -> None:
    declaration = _declaration()
    expected = compute_class_world_release_declaration_digest(other_declaration)

    result = verify_class_world_release_declaration_digest(declaration, expected)

    assert result.matches is False
    assert result.expected_digest is expected
    assert result.actual_digest == compute_class_world_release_declaration_digest(declaration)
    assert result.actual_digest != result.expected_digest


@pytest.mark.parametrize("invalid", [None, object(), "0" * 64, {"algorithm": "sha256"}])
def test_wrong_expected_digest_object_raises_type_error(invalid: object) -> None:
    with pytest.raises(TypeError, match="ClassWorldReleaseDeclarationDigest"):
        verify_class_world_release_declaration_digest(
            _declaration(),
            invalid,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("algorithm", "hex_digest"),
    [
        ("SHA256", "a" * 64),
        ("sha-256", "a" * 64),
        ("sha512", "a" * 64),
        (7, "a" * 64),
        ("sha256", "A" * 64),
        ("sha256", "a" * 63),
        ("sha256", "a" * 65),
        ("sha256", "g" * 64),
        ("sha256", " " + "a" * 63),
        ("sha256", "a" * 63 + " "),
        ("sha256", ""),
        ("sha256", 7),
    ],
)
def test_malformed_expected_digest_raises_value_error(
    algorithm: object,
    hex_digest: object,
) -> None:
    malformed = ClassWorldReleaseDeclarationDigest(
        algorithm=algorithm,  # type: ignore[arg-type]
        hex_digest=hex_digest,  # type: ignore[arg-type]
    )

    with pytest.raises(ValueError, match="expected_digest"):
        verify_class_world_release_declaration_digest(_declaration(), malformed)


@pytest.mark.parametrize("invalid", [None, object(), True, b"declaration"])
def test_wrong_declaration_preserves_digest_type_error(invalid: object) -> None:
    expected = ClassWorldReleaseDeclarationDigest("sha256", "a" * 64)

    with pytest.raises(TypeError, match="ClassWorldReleaseDeclaration"):
        verify_class_world_release_declaration_digest(
            invalid,  # type: ignore[arg-type]
            expected,
        )


def test_inconsistent_declaration_preserves_value_error_without_mutation() -> None:
    declaration = _declaration()
    inconsistent = replace(
        declaration,
        identity=replace(declaration.identity, release_id="Bad/Release"),
    )
    expected = compute_class_world_release_declaration_digest(declaration)
    before_expected = expected
    before_inconsistent = inconsistent

    with pytest.raises(ValueError):
        verify_class_world_release_declaration_digest(inconsistent, expected)

    assert expected == before_expected
    assert inconsistent == before_inconsistent


def test_malformed_expected_digest_fails_before_digest_computation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def compute(value: object) -> ClassWorldReleaseDeclarationDigest:
        calls.append(value)
        raise AssertionError("digest computation must not run")

    monkeypatch.setattr(
        verification_module,
        "compute_class_world_release_declaration_digest",
        compute,
    )
    malformed = ClassWorldReleaseDeclarationDigest("SHA256", "a" * 64)

    with pytest.raises(ValueError):
        verify_class_world_release_declaration_digest(_declaration(), malformed)

    assert calls == []


def test_valid_expected_digest_delegates_exactly_once_and_compares_complete_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declaration = _declaration()
    expected = ClassWorldReleaseDeclarationDigest("sha256", "a" * 64)
    actual = ClassWorldReleaseDeclarationDigest("sha256", "b" * 64)
    calls: list[object] = []

    def compute(value: object) -> ClassWorldReleaseDeclarationDigest:
        calls.append(value)
        return actual

    monkeypatch.setattr(
        verification_module,
        "compute_class_world_release_declaration_digest",
        compute,
    )

    result = verify_class_world_release_declaration_digest(declaration, expected)

    assert calls == [declaration]
    assert result == ClassWorldReleaseDeclarationDigestVerificationResult(
        expected_digest=expected,
        actual_digest=actual,
        matches=False,
    )


def test_complete_model_comparison_includes_algorithm_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declaration = _declaration()
    expected = ClassWorldReleaseDeclarationDigest("sha256", "a" * 64)
    actual = ClassWorldReleaseDeclarationDigest("sha512", "a" * 64)
    monkeypatch.setattr(
        verification_module,
        "compute_class_world_release_declaration_digest",
        lambda value: actual,
    )

    result = verify_class_world_release_declaration_digest(declaration, expected)

    assert result.expected_digest.hex_digest == result.actual_digest.hex_digest
    assert result.matches is False


def test_verification_source_stays_inside_pure_digest_comparison_boundary() -> None:
    source = Path(verification_module.__file__).read_text(encoding="utf-8")
    forbidden = (
        "hashlib",
        "serialize_class_world_release_declaration",
        "compare_digest",
        "import hmac",
        "import os",
        "import random",
        "import secrets",
        "import subprocess",
        "import time",
        "import uuid",
        "from pathlib",
        "open(",
        "read_class_world_release_declaration_file",
        "write_class_world_release_declaration_file",
        "load_explorer_package",
        "validate_explorer_package",
        "build_package_set_plan",
        "apply_package_set_plan",
        "pygame",
        "requests",
        "httpx",
        "sqlite",
        "certificate",
        "signature",
        "archive",
        "inventory",
        "deploy",
    )

    assert "compute_class_world_release_declaration_digest(declaration)" in source
    assert "matches=expected_digest == actual_digest" in source
    assert all(term not in source.lower() for term in forbidden)


def test_public_exports_preserve_all_prior_boundaries() -> None:
    import explore.packages as packages

    expected = {
        "verify_class_world_release_declaration_digest",
        "ClassWorldReleaseDeclarationDigestVerificationResult",
        "SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_VERIFICATION_CONTRACT_VERSION",
        "compute_class_world_release_declaration_digest",
        "ClassWorldReleaseDeclarationDigest",
        "SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM",
        "SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_CONTRACT_VERSION",
        "serialize_class_world_release_declaration",
        "parse_class_world_release_declaration",
        "read_class_world_release_declaration_file",
        "write_class_world_release_declaration_file",
        "build_class_world_release_declaration",
        "ClassWorldReleaseDeclaration",
        "ClassWorldReleaseIdentity",
        "ClassWorldReleaseProvenance",
        "build_class_world_configuration",
        "serialize_class_world_manifest",
        "parse_class_world_manifest",
        "read_class_world_manifest_file",
        "write_class_world_manifest_file",
        "build_package_set_plan",
        "apply_package_set_plan",
        "build_student_api_registration_plan",
        "apply_student_api_registration_plan",
        "load_explorer_package",
        "validate_explorer_package",
    }

    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)
    assert not any(name.startswith("_") for name in packages.__all__)
    assert not hasattr(packages, "_validate_expected_digest")
