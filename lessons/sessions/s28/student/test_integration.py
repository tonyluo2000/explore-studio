"""Focused S28 learner tests for safe deterministic package integration."""

from __future__ import annotations

import shutil

import pytest
import yaml

from explore.packages.loader import load_explorer_package
from lessons.sessions.s28.student import integration
from lessons.sessions.s28.student.fixtures import (
    CORRUPT_SOURCE,
    EXPECTED_ROUTE_IDS,
    EXPECTED_STYLE_ID,
    EXPECTED_STYLED_IDS,
    GOLDEN_FILE_LIST,
    INVALID_SOURCE,
    UNSAFE_ID_SOURCE,
    VALID_SOURCE,
)


def prepare_case(tmp_path, monkeypatch, source=VALID_SOURCE):
    student_root = tmp_path / "student"
    student_root.mkdir()
    copied_source = student_root / "source-plan.yaml"
    shutil.copyfile(source, copied_source)
    monkeypatch.setattr(integration, "STUDENT_ROOT", student_root)
    monkeypatch.setattr(integration, "PACKAGE_ROOT", student_root / "explorer-package")
    return copied_source


def generated_bytes():
    return {
        relative: (integration.PACKAGE_ROOT / relative).read_bytes()
        for relative in GOLDEN_FILE_LIST
    }


def test_missing_source_file_has_named_clear_error(tmp_path, monkeypatch):
    student_root = tmp_path / "student"
    student_root.mkdir()
    monkeypatch.setattr(integration, "STUDENT_ROOT", student_root)

    with pytest.raises(integration.InputPlanError, match="missing input file: missing.yaml"):
        integration.load_plan(student_root / "missing.yaml")


def test_corrupt_yaml_has_named_clear_error(tmp_path, monkeypatch):
    source = prepare_case(tmp_path, monkeypatch, CORRUPT_SOURCE)

    with pytest.raises(integration.CorruptPlanError, match="corrupt YAML data: source-plan.yaml"):
        integration.load_plan(source)


def test_semantically_invalid_plan_preserves_diagnostics(tmp_path, monkeypatch):
    source = prepare_case(tmp_path, monkeypatch, INVALID_SOURCE)
    plan = integration.load_plan(source)

    with pytest.raises(
        integration.InvalidPlanError, match="route_order must be a positive integer"
    ):
        integration.build_package(plan)


def test_valid_source_generates_golden_file_list(tmp_path, monkeypatch):
    source = prepare_case(tmp_path, monkeypatch)
    plan = integration.load_plan(source)
    result = integration.build_package(plan)

    assert result["generated_files"] == GOLDEN_FILE_LIST
    assert result["output_root"] == str(integration.PACKAGE_ROOT)
    assert result["validation_issues"] == ()
    assert all((integration.PACKAGE_ROOT / relative).is_file() for relative in GOLDEN_FILE_LIST)


def test_repeated_generation_is_byte_identical(tmp_path, monkeypatch):
    source = prepare_case(tmp_path, monkeypatch)
    plan = integration.load_plan(source)

    integration.build_package(plan)
    first = generated_bytes()
    integration.build_package(plan)
    second = generated_bytes()

    assert first == second


def test_unsafe_identifier_rejected_before_path_construction(tmp_path, monkeypatch):
    source = prepare_case(tmp_path, monkeypatch, UNSAFE_ID_SOURCE)
    plan = integration.load_plan(source)

    with pytest.raises(integration.UnsafeIdentifierError, match=r"\.\./escape"):
        integration.build_package(plan)
    assert not integration.PACKAGE_ROOT.exists()


def test_generated_package_validates(tmp_path, monkeypatch):
    source = prepare_case(tmp_path, monkeypatch)
    plan = integration.load_plan(source)
    result = integration.build_package(plan)
    loaded = load_explorer_package(integration.PACKAGE_ROOT)

    assert loaded.is_loaded, loaded.all_issues
    assert result["validation_issues"] == ()


def test_generated_package_has_expected_m14_m15_structure(tmp_path, monkeypatch):
    source = prepare_case(tmp_path, monkeypatch)
    integration.build_package(integration.load_plan(source))
    manifest = yaml.safe_load((integration.PACKAGE_ROOT / "manifest.yaml").read_text())
    object_documents = {
        item["id"]: yaml.safe_load((integration.PACKAGE_ROOT / item["path"]).read_text())
        for item in manifest["contributions"]
        if item["type"] == "world_object"
    }
    guide = yaml.safe_load((integration.PACKAGE_ROOT / "character" / "sky-guide.yaml").read_text())

    assert len(manifest["toggle_styles"]) == 1
    assert manifest["toggle_styles"][0]["id"] == EXPECTED_STYLE_ID
    assert (
        tuple(
            object_id
            for object_id, document in object_documents.items()
            if document.get("toggle_style_id") == EXPECTED_STYLE_ID
        )
        == EXPECTED_STYLED_IDS
    )
    assert tuple(guide["respond_to_sequence"]["object_ids"]) == EXPECTED_ROUTE_IDS
