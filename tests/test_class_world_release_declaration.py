"""Behavior-focused tests for class-world release declarations v0.1."""

from __future__ import annotations

import importlib
import socket
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from explore.packages import (
    SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION,
    SUPPORTED_CLASS_WORLD_MANIFEST_TRANSPORT_CONTRACT_VERSION,
    SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION,
    CharacterRegistration,
    CharacterRegistrationSpec,
    ClassWorldCohort,
    ClassWorldConfiguration,
    ClassWorldConfigurationSpec,
    ClassWorldPackagePin,
    ClassWorldReleaseDeclarationIssueCode,
    ClassWorldReleaseDeclarationResult,
    PackageProvenance,
    PackageSetPlan,
    SelectedPackagePlan,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
    build_class_world_configuration,
    build_class_world_release_declaration,
)


def _provenance(package_id: str, package_version: str) -> PackageProvenance:
    return PackageProvenance(package_id, package_version, "0.1")


def _selected(
    package_id: str,
    package_version: str,
    entry: CharacterRegistration | WorldObjectRegistration,
) -> SelectedPackagePlan:
    provenance = _provenance(package_id, package_version)
    adjusted = replace(entry, provenance=provenance)
    registration_plan = StudentAPIRegistrationPlan(provenance, (adjusted,))
    return SelectedPackagePlan(
        package_id,
        package_version,
        provenance,
        registration_plan,
    )


def _plan() -> PackageSetPlan:
    zeta_id = "zeta-character"
    alpha_id = "alpha-lantern"
    packages = (
        _selected(
            zeta_id,
            "2.1.0-beta.1+class",
            CharacterRegistration(
                f"{zeta_id}:hero",
                "hero",
                _provenance(zeta_id, "2.1.0-beta.1+class"),
                CharacterRegistrationSpec("Explorer", 10, 20, "gold"),
                None,
            ),
        ),
        _selected(
            alpha_id,
            "1.0.0",
            WorldObjectRegistration(
                f"{alpha_id}:lantern",
                "lantern",
                _provenance(alpha_id, "1.0.0"),
                WorldObjectRegistrationSpec(
                    "Lantern",
                    30,
                    40,
                    "green",
                    "Look closer.",
                    "You found it!",
                ),
                None,
            ),
        ),
    )
    return PackageSetPlan(
        student_api_version="0.1",
        packages=packages,
        entries=tuple(entry for package in packages for entry in package.registration_plan.entries),
    )


def _configuration(plan: PackageSetPlan | None = None) -> ClassWorldConfiguration:
    selected_plan = plan or _plan()
    result = build_class_world_configuration(
        ClassWorldConfigurationSpec(
            schema_version="0.1",
            class_world_id="expedition-orion-fall-2026",
            display_name="Expedition Orion — Fall 2026",
            class_world_version="3.2.1",
            engine_version="1.4.0",
            student_api_version="0.1",
            cohort=ClassWorldCohort("expedition-orion", "Expedition Orion"),
            packages=tuple(
                ClassWorldPackagePin(package.package_id, package.package_version)
                for package in selected_plan.packages
            ),
        ),
        selected_plan,
    )
    assert result.configuration is not None
    return result.configuration


def _codes(
    result: ClassWorldReleaseDeclarationResult,
) -> list[ClassWorldReleaseDeclarationIssueCode]:
    return [issue.code for issue in result.issues]


def test_success_derives_identity_and_exact_provenance_from_configuration() -> None:
    configuration = _configuration()

    result = build_class_world_release_declaration(
        configuration,
        release_id="spring-showcase",
        release_version="1.2.3-rc.1+school",
    )

    assert result.is_built
    assert result.issues == ()
    assert result.declaration is not None
    declaration = result.declaration
    assert declaration.declaration_version == "0.1"
    assert declaration.configuration is configuration
    assert declaration.configuration.package_set_plan is configuration.package_set_plan
    assert declaration.identity.release_id == "spring-showcase"
    assert declaration.identity.release_version == "1.2.3-rc.1+school"
    assert declaration.identity.class_world_id == configuration.class_world_id
    assert declaration.identity.class_world_version == configuration.class_world_version
    assert declaration.provenance.engine_version == configuration.engine_version
    assert declaration.provenance.student_api_version == configuration.student_api_version
    assert declaration.provenance.cohort_id == configuration.cohort.cohort_id
    assert declaration.provenance.class_world_manifest_schema_version == "0.1"
    assert declaration.provenance.manifest_transport_contract_version == "0.1"
    assert declaration.provenance.package_pins == configuration.packages
    assert [pin.package_id for pin in declaration.provenance.package_pins] == [
        "zeta-character",
        "alpha-lantern",
    ]
    assert [pin.package_version for pin in declaration.provenance.package_pins] == [
        "2.1.0-beta.1+class",
        "1.0.0",
    ]


def test_equivalent_inputs_are_equal_and_order_remains_significant() -> None:
    configuration = _configuration()
    equivalent = _configuration()

    first = build_class_world_release_declaration(
        configuration,
        release_id="spring-showcase",
        release_version="1.0.0",
    )
    second = build_class_world_release_declaration(
        equivalent,
        release_id="spring-showcase",
        release_version="1.0.0",
    )

    assert first == second
    assert first == build_class_world_release_declaration(
        configuration,
        release_id="spring-showcase",
        release_version="1.0.0",
    )


@pytest.mark.parametrize(
    ("release_id", "expected"),
    [
        (None, ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_REQUIRED),
        ("", ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_REQUIRED),
        (" \n\t", ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_REQUIRED),
        (" spring-showcase", ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID),
        ("spring-showcase ", ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID),
        ("Spring-Showcase", ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID),
        ("spring_showcase", ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID),
        ("spring/showcase", ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID),
        ("..", ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID),
        ("a" * 65, ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID),
        ("spring\u200bshowcase", ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID),
        (True, ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID),
        (42, ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID),
        (b"spring-showcase", ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID),
    ],
)
def test_release_id_uses_existing_identifier_policy_without_coercion(
    release_id: object,
    expected: ClassWorldReleaseDeclarationIssueCode,
) -> None:
    result = build_class_world_release_declaration(
        _configuration(),
        release_id=release_id,  # type: ignore[arg-type]
        release_version="1.0.0",
    )

    assert result.declaration is None
    assert _codes(result) == [expected]
    assert result.issues[0].location == "release_id"


@pytest.mark.parametrize(
    ("release_version", "expected"),
    [
        (None, ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_REQUIRED),
        ("", ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_REQUIRED),
        (" \n\t", ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_REQUIRED),
        (" 1.0.0", ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID),
        ("1.0.0 ", ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID),
        ("1.0", ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID),
        ("01.0.0", ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID),
        ("latest", ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID),
        ("1.0.0\u200b", ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID),
        (1, ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID),
        (True, ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID),
        (b"1.0.0", ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID),
    ],
)
def test_release_version_uses_existing_semver_policy_without_coercion(
    release_version: object,
    expected: ClassWorldReleaseDeclarationIssueCode,
) -> None:
    result = build_class_world_release_declaration(
        _configuration(),
        release_id="spring-showcase",
        release_version=release_version,  # type: ignore[arg-type]
    )

    assert result.declaration is None
    assert _codes(result) == [expected]
    assert result.issues[0].location == "release_version"


@pytest.mark.parametrize(
    ("configuration", "expected"),
    [
        (None, ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_REQUIRED),
        (object(), ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID_TYPE),
        ("configuration", ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID_TYPE),
        (b"configuration", ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID_TYPE),
    ],
)
def test_configuration_input_contract_is_structured_and_atomic(
    configuration: object,
    expected: ClassWorldReleaseDeclarationIssueCode,
) -> None:
    result = build_class_world_release_declaration(
        configuration,  # type: ignore[arg-type]
        release_id="spring-showcase",
        release_version="1.0.0",
    )

    assert result.declaration is None
    assert _codes(result) == [expected]
    assert result.issues[0].location == "configuration"


def test_configuration_subclass_is_rejected_when_exact_model_equality_differs() -> None:
    class ConfigurationSubclass(ClassWorldConfiguration):
        pass

    configuration = _configuration()
    subclass = ConfigurationSubclass(
        schema_version=configuration.schema_version,
        class_world_id=configuration.class_world_id,
        display_name=configuration.display_name,
        class_world_version=configuration.class_world_version,
        engine_version=configuration.engine_version,
        student_api_version=configuration.student_api_version,
        cohort=configuration.cohort,
        package_set_plan=configuration.package_set_plan,
    )

    result = build_class_world_release_declaration(
        subclass,
        release_id="spring-showcase",
        release_version="1.0.0",
    )

    assert result.declaration is None
    assert _codes(result) == [ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID]
    assert result.issues[0].location == "configuration"


def test_manually_inconsistent_configuration_is_rejected_without_partial_output() -> None:
    configuration = _configuration()
    invalid_plan = replace(
        configuration.package_set_plan,
        entries=tuple(reversed(configuration.package_set_plan.entries)),
    )
    invalid = replace(configuration, package_set_plan=invalid_plan)

    result = build_class_world_release_declaration(
        invalid,
        release_id="spring-showcase",
        release_version="1.0.0",
    )

    assert result.declaration is None
    assert ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID in _codes(result)
    assert any(
        issue.location == "configuration.package_set_plan.entries" for issue in result.issues
    )
    assert all(
        "0x" not in issue.message and "/Users/" not in issue.message for issue in result.issues
    )


def test_duplicate_package_ids_in_manual_plan_are_not_sorted_or_deduplicated() -> None:
    configuration = _configuration()
    first = configuration.package_set_plan.packages[0]
    duplicate_plan = replace(
        configuration.package_set_plan,
        packages=(first, first),
        entries=(*first.registration_plan.entries, *first.registration_plan.entries),
    )
    invalid = replace(configuration, package_set_plan=duplicate_plan)

    result = build_class_world_release_declaration(
        invalid,
        release_id="spring-showcase",
        release_version="1.0.0",
    )

    assert result.declaration is None
    assert ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_INVALID in _codes(result)


def test_independent_issues_accumulate_in_stable_order() -> None:
    first = build_class_world_release_declaration(
        None,
        release_id="Bad/ID",
        release_version="01.0",
    )
    second = build_class_world_release_declaration(
        None,
        release_id="Bad/ID",
        release_version="01.0",
    )

    assert first == second
    assert first.declaration is None
    assert _codes(first) == [
        ClassWorldReleaseDeclarationIssueCode.CONFIGURATION_REQUIRED,
        ClassWorldReleaseDeclarationIssueCode.RELEASE_ID_INVALID,
        ClassWorldReleaseDeclarationIssueCode.RELEASE_VERSION_INVALID,
    ]
    assert [issue.location for issue in first.issues] == [
        "configuration",
        "release_id",
        "release_version",
    ]


def test_models_and_nested_collections_are_deeply_immutable() -> None:
    result = build_class_world_release_declaration(
        _configuration(),
        release_id="spring-showcase",
        release_version="1.0.0",
    )
    failure = build_class_world_release_declaration(
        None,
        release_id="spring-showcase",
        release_version="1.0.0",
    )
    assert result.declaration is not None

    assert isinstance(result.issues, tuple)
    assert isinstance(result.declaration.provenance.package_pins, tuple)
    for value, field, replacement in (
        (result, "issues", ()),
        (result.declaration, "declaration_version", "changed"),
        (result.declaration.identity, "release_id", "changed"),
        (result.declaration.provenance, "engine_version", "changed"),
        (result.declaration.provenance.package_pins[0], "package_id", "changed"),
        (failure.issues[0], "location", "changed"),
    ):
        with pytest.raises((FrozenInstanceError, AttributeError)):
            setattr(value, field, replacement)


def test_builder_performs_no_io_serialization_pipeline_runtime_or_external_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = _configuration()

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("release declaration crossed a forbidden boundary")

    monkeypatch.setattr(Path, "read_text", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    monkeypatch.setattr(Path, "open", fail)
    monkeypatch.setattr(importlib, "import_module", fail)
    monkeypatch.setattr(socket, "socket", fail)

    from explore.packages import (
        class_world_manifest,
        class_world_manifest_transport,
        loader,
        package_set_application,
        package_set_planner,
        registration_adapter,
        registration_application,
        validator,
    )

    monkeypatch.setattr(class_world_manifest, "serialize_class_world_manifest", fail)
    monkeypatch.setattr(class_world_manifest, "parse_class_world_manifest", fail)
    monkeypatch.setattr(class_world_manifest_transport, "read_class_world_manifest_file", fail)
    monkeypatch.setattr(class_world_manifest_transport, "write_class_world_manifest_file", fail)
    monkeypatch.setattr(loader, "load_explorer_package", fail)
    monkeypatch.setattr(validator, "validate_explorer_package", fail)
    monkeypatch.setattr(registration_adapter, "build_student_api_registration_plan", fail)
    monkeypatch.setattr(package_set_planner, "build_package_set_plan", fail)
    monkeypatch.setattr(registration_application, "apply_student_api_registration_plan", fail)
    monkeypatch.setattr(package_set_application, "apply_package_set_plan", fail)

    import pygame

    monkeypatch.setattr(pygame, "init", fail)
    monkeypatch.setattr(pygame.display, "set_mode", fail)

    result = build_class_world_release_declaration(
        configuration,
        release_id="spring-showcase",
        release_version="1.0.0",
    )

    assert result.is_built


def test_public_exports_and_contract_versions_preserve_the_pipeline() -> None:
    import explore.packages as packages

    expected = {
        "build_class_world_release_declaration",
        "ClassWorldReleaseIdentity",
        "ClassWorldReleaseProvenance",
        "ClassWorldReleaseDeclaration",
        "ClassWorldReleaseDeclarationResult",
        "ClassWorldReleaseDeclarationIssue",
        "ClassWorldReleaseDeclarationIssueCode",
        "SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION",
        "SUPPORTED_CLASS_WORLD_MANIFEST_TRANSPORT_CONTRACT_VERSION",
        "serialize_class_world_manifest",
        "parse_class_world_manifest",
        "read_class_world_manifest_file",
        "write_class_world_manifest_file",
        "build_class_world_configuration",
        "build_package_set_plan",
        "apply_package_set_plan",
        "load_explorer_package",
        "validate_explorer_package",
    }

    assert SUPPORTED_CLASS_WORLD_RELEASE_DECLARATION_VERSION == "0.1"
    assert SUPPORTED_CLASS_WORLD_MANIFEST_SCHEMA_VERSION == "0.1"
    assert SUPPORTED_CLASS_WORLD_MANIFEST_TRANSPORT_CONTRACT_VERSION == "0.1"
    assert expected <= set(packages.__all__)
    assert all(hasattr(packages, name) for name in expected)


def test_source_stays_inside_the_pure_declaration_boundary() -> None:
    from explore.packages import class_world_release_declaration

    source = Path(class_world_release_declaration.__file__).read_text(encoding="utf-8")
    forbidden = (
        "import hashlib",
        "import hmac",
        "import cryptography",
        "import os",
        "import pathlib",
        "import subprocess",
        "import uuid",
        "import random",
        "import secrets",
        "import datetime",
        "import time",
        "import pygame",
        "from engine",
        "serialize_class_world_manifest",
        "parse_class_world_manifest",
        "read_class_world_manifest_file",
        "write_class_world_manifest_file",
        "load_explorer_package",
        "validate_explorer_package",
        "build_package_set_plan",
        "apply_package_set_plan",
        "build_student_api_registration_plan",
        "apply_student_api_registration_plan",
        "World(",
        "Character(",
        "Object(",
        "open(",
        "eval(",
        "exec(",
    )

    assert all(term not in source for term in forbidden)
