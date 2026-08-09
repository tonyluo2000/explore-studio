"""Behavior tests for deterministic release-declaration digest v0.1."""

from __future__ import annotations

import hashlib
import re
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import Literal

import pytest

from explore.packages import (
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM,
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_TRANSPORT_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldCohort,
    ClassWorldConfiguration,
    ClassWorldConfigurationSpec,
    ClassWorldPackagePin,
    ClassWorldReleaseDeclaration,
    ClassWorldReleaseDeclarationDigest,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    build_class_world_configuration,
    build_class_world_release_declaration,
    compute_class_world_release_declaration_digest,
    serialize_class_world_release_declaration,
)
from explore.packages import class_world_release_declaration_digest as digest_module

_PackageSpec = tuple[str, str, Literal["character", "object"]]
_CHARACTER_PACKAGE: _PackageSpec = (
    "zeta-character",
    "2.1.0-beta.1+class",
    "character",
)
_OBJECT_PACKAGE: _PackageSpec = ("alpha-lantern", "1.0.0", "object")


def _provenance(package_id: str, package_version: str) -> PackageProvenance:
    return PackageProvenance(package_id, package_version, "0.1")


def _selected(specification: _PackageSpec) -> SelectedPackagePlan:
    package_id, package_version, contribution_type = specification
    provenance = _provenance(package_id, package_version)
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
    class_world_id: str = "expedition-orion-fall-2026",
    class_world_version: str = "3.2.1",
    engine_version: str = "1.4.0",
    cohort_id: str = "expedition-orion",
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
            class_world_id,
            "Expédition Orion — Automne 2026 🚀",
            class_world_version,
            engine_version,
            "0.1",
            ClassWorldCohort(cohort_id, "Expédition Orion 🚀"),
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


def test_digest_matches_known_canonical_sha256_vector() -> None:
    declaration = _declaration()
    canonical = """{
  "schema_version": "0.1",
  "identity": {
    "release_id": "spring-showcase",
    "release_version": "1.2.3-rc.1+school",
    "class_world_id": "expedition-orion-fall-2026",
    "class_world_version": "3.2.1"
  },
  "provenance": {
    "engine_version": "1.4.0",
    "student_api_version": "0.1",
    "class_world_manifest_schema_version": "0.1",
    "manifest_transport_contract_version": "0.1",
    "cohort_id": "expedition-orion",
    "packages": [
      {
        "id": "zeta-character",
        "version": "2.1.0-beta.1+class"
      },
      {
        "id": "alpha-lantern",
        "version": "1.0.0"
      }
    ]
  }
}
"""

    assert serialize_class_world_release_declaration(declaration) == canonical
    assert compute_class_world_release_declaration_digest(declaration) == (
        ClassWorldReleaseDeclarationDigest(
            algorithm="sha256",
            hex_digest="c2511d501f04655935886a8336c72bf6c88f1eca07010465e8e1719546af78ff",
        )
    )


def test_digest_shape_constants_immutability_and_repeated_equality() -> None:
    declaration = _declaration()

    first = compute_class_world_release_declaration_digest(declaration)
    second = compute_class_world_release_declaration_digest(declaration)

    assert first == second
    assert first.algorithm == "sha256"
    assert len(first.hex_digest) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", first.hex_digest)
    assert SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM == "sha256"
    assert SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_CONTRACT_VERSION == "0.1"
    assert SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION == "0.1"
    assert SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_TRANSPORT_CONTRACT_VERSION == "0.1"
    with pytest.raises((FrozenInstanceError, AttributeError)):
        first.hex_digest = "0" * 64  # type: ignore[misc]


def test_exact_serializer_utf8_bytes_and_final_newline_are_hashed() -> None:
    declaration = _declaration()
    canonical = serialize_class_world_release_declaration(declaration)

    digest = compute_class_world_release_declaration_digest(declaration)

    assert canonical.endswith("\n") and not canonical.endswith("\n\n")
    assert digest.hex_digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert digest.hex_digest != hashlib.sha256(canonical.rstrip("\n").encode("utf-8")).hexdigest()


def test_serializer_is_the_sole_byte_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declaration = _declaration()
    calls: list[object] = []
    canonical = '{"label":"Expédition 🚀"}\n'

    def serialize(value: object) -> str:
        calls.append(value)
        return canonical

    monkeypatch.setattr(digest_module, "serialize_class_world_release_declaration", serialize)

    result = compute_class_world_release_declaration_digest(declaration)

    assert calls == [declaration]
    assert result.hex_digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_equivalent_separately_built_declarations_have_equal_digests() -> None:
    first = _declaration(_configuration())
    second = _declaration(_configuration())

    assert first == second
    assert compute_class_world_release_declaration_digest(first) == (
        compute_class_world_release_declaration_digest(second)
    )


def _variant(case: str) -> ClassWorldReleaseDeclaration:
    if case == "release-id":
        return _declaration(release_id="autumn-showcase")
    if case == "release-version":
        return _declaration(release_version="1.2.4")
    if case == "class-world-id":
        return _declaration(_configuration(class_world_id="expedition-lyra-fall-2026"))
    if case == "class-world-version":
        return _declaration(_configuration(class_world_version="3.2.2"))
    if case == "engine-version":
        return _declaration(_configuration(engine_version="1.4.1"))
    if case == "cohort-id":
        return _declaration(_configuration(cohort_id="expedition-lyra"))
    if case == "package-id":
        return _declaration(
            _configuration(
                packages=(("omega-character", _CHARACTER_PACKAGE[1], "character"), _OBJECT_PACKAGE)
            )
        )
    if case == "package-version":
        return _declaration(
            _configuration(
                packages=((_CHARACTER_PACKAGE[0], "2.1.1", "character"), _OBJECT_PACKAGE)
            )
        )
    if case == "package-order":
        return _declaration(_configuration(packages=(_OBJECT_PACKAGE, _CHARACTER_PACKAGE)))
    if case == "package-count":
        return _declaration(_configuration(packages=(_CHARACTER_PACKAGE,)))
    raise AssertionError(f"unknown sensitivity case: {case}")


@pytest.mark.parametrize(
    "case",
    [
        "release-id",
        "release-version",
        "class-world-id",
        "class-world-version",
        "engine-version",
        "cohort-id",
        "package-id",
        "package-version",
        "package-order",
        "package-count",
    ],
)
def test_meaningful_valid_declaration_changes_change_digest(case: str) -> None:
    baseline = compute_class_world_release_declaration_digest(_declaration())

    changed = compute_class_world_release_declaration_digest(_variant(case))

    assert changed != baseline


def test_unsupported_student_api_change_is_not_partially_hashed() -> None:
    declaration = _declaration()
    inconsistent = replace(
        declaration,
        provenance=replace(declaration.provenance, student_api_version="0.2"),
    )

    with pytest.raises(ValueError, match="inconsistent"):
        compute_class_world_release_declaration_digest(inconsistent)


@pytest.mark.parametrize("invalid", [None, object(), True, b"declaration"])
def test_wrong_input_preserves_serializer_type_error(invalid: object) -> None:
    with pytest.raises(TypeError, match="ClassWorldReleaseDeclaration"):
        compute_class_world_release_declaration_digest(invalid)  # type: ignore[arg-type]


def test_inconsistent_declaration_preserves_value_error_without_mutation() -> None:
    declaration = _declaration()
    inconsistent = replace(
        declaration,
        identity=replace(declaration.identity, release_id="Bad/Release"),
    )
    before = declaration

    with pytest.raises(ValueError):
        compute_class_world_release_declaration_digest(inconsistent)

    assert declaration == before


def test_literal_unicode_is_not_escaped_or_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    declaration = _declaration()
    composed_text = '{"value":"é"}\n'
    decomposed_text = '{"value":"é"}\n'
    canonical_values = iter((composed_text, decomposed_text))
    monkeypatch.setattr(
        digest_module,
        "serialize_class_world_release_declaration",
        lambda value: next(canonical_values),
    )

    composed = compute_class_world_release_declaration_digest(declaration)
    decomposed = compute_class_world_release_declaration_digest(declaration)

    assert composed.hex_digest == hashlib.sha256(composed_text.encode("utf-8")).hexdigest()
    assert decomposed.hex_digest == hashlib.sha256(decomposed_text.encode("utf-8")).hexdigest()
    assert composed != decomposed


def test_digest_source_stays_inside_pure_canonical_byte_boundary() -> None:
    source = Path(digest_module.__file__).read_text(encoding="utf-8")
    forbidden = (
        "import json",
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
        "signature",
        "hmac",
        "archive",
        "inventory",
        "deploy",
    )

    assert "serialize_class_world_release_declaration(declaration)" in source
    assert 'canonical_text.encode("utf-8")' in source
    assert "hashlib.sha256(canonical_bytes).hexdigest()" in source
    assert all(term not in source.lower() for term in forbidden)


def test_public_exports_preserve_prior_package_boundaries() -> None:
    import explore.packages as packages

    expected = {
        "compute_class_world_release_declaration_digest",
        "ClassWorldReleaseDeclarationDigest",
        "SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_ALGORITHM",
        "SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_DIGEST_CONTRACT_VERSION",
        "serialize_class_world_release_declaration",
        "parse_class_world_release_declaration",
        "build_class_world_release_declaration",
        "read_class_world_release_declaration_file",
        "write_class_world_release_declaration_file",
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
    assert not hasattr(packages, "_compute_digest")
