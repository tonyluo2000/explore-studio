"""Focused S29 learner checks for review and regression evidence."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import yaml

from lessons.sessions.s29.student import review_harness

STUDENT_ROOT = Path(__file__).parent
PACKAGE_ROOT = STUDENT_ROOT / "explorer-package"
FIXTURE_ROOT = STUDENT_ROOT / "review-fixtures"
EXPECTED_PATHS = (
    "character/sky-guide.yaml",
    "manifest.yaml",
    "objects/comet-bell.yaml",
    "objects/echo-lens.yaml",
    "objects/wind-dial.yaml",
)


def load_prepared_example():
    path = FIXTURE_ROOT / "prepared_review_example.py"
    spec = importlib.util.spec_from_file_location("s29_prepared_review_example", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_snapshot_is_stable_and_contains_expected_files():
    first = review_harness.snapshot_package()
    second = review_harness.snapshot_package()

    assert first == second
    assert tuple(entry["path"] for entry in first) == EXPECTED_PATHS
    assert all(len(entry["sha256"]) == 64 for entry in first)


def test_unchanged_before_after_snapshots_have_no_delta():
    before = review_harness.snapshot_package()
    after = review_harness.snapshot_package()

    assert review_harness.compare_snapshots(before, after) == ()


def test_snapshot_comparison_identifies_only_changed_file(tmp_path):
    copied_package = tmp_path / "explorer-package"
    shutil.copytree(PACKAGE_ROOT, copied_package)
    before = review_harness.snapshot_package(copied_package)
    object_path = copied_package / "objects" / "echo-lens.yaml"
    object_path.write_text(object_path.read_text() + "# review evidence\n")
    after = review_harness.snapshot_package(copied_package)

    assert review_harness.compare_snapshots(before, after) == ("objects/echo-lens.yaml",)


def test_student_package_validates_and_plans():
    loaded, planned = review_harness.validate_and_plan()

    assert loaded.is_loaded
    assert planned.is_planned


def test_student_package_retains_m14_and_m15_contracts():
    manifest = yaml.safe_load((PACKAGE_ROOT / "manifest.yaml").read_text())
    objects = {
        contribution["id"]: yaml.safe_load((PACKAGE_ROOT / contribution["path"]).read_text())
        for contribution in manifest["contributions"]
        if contribution["type"] == "world_object"
    }
    guide = yaml.safe_load((PACKAGE_ROOT / "character" / "sky-guide.yaml").read_text())

    assert manifest["toggle_styles"][0]["id"] == "observatory-glow"
    assert tuple(
        object_id
        for object_id, document in objects.items()
        if document.get("toggle_style_id") == "observatory-glow"
    ) == ("echo-lens", "wind-dial")
    assert tuple(guide["respond_to_sequence"]["object_ids"]) == (
        "echo-lens",
        "wind-dial",
        "comet-bell",
    )


def test_prepared_example_preserves_all_records_baseline():
    example = load_prepared_example()
    cases = yaml.safe_load((FIXTURE_ROOT / "cases.yaml").read_text())
    expected = yaml.safe_load((FIXTURE_ROOT / "expected-output.yaml").read_text())

    assert example.run(cases) == expected["all_records"]


def test_prepared_example_preserves_enabled_records_baseline():
    example = load_prepared_example()
    cases = yaml.safe_load((FIXTURE_ROOT / "cases.yaml").read_text())
    expected = yaml.safe_load((FIXTURE_ROOT / "expected-output.yaml").read_text())

    assert example.run(cases, enabled_only=True) == expected["enabled_records"]
    assert example.run(cases, enabled_only=True, include_count=True) == {
        "records": expected["enabled_records"],
        "count": 2,
    }
