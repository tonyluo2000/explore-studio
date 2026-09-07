"""Prepared S20 checks for normal, boundary, and malformed local input."""

from copy import deepcopy

import pytest

from explore.packages.loader import load_explorer_package
from lessons.sessions.s20.student.starter import INPUT_PATH, build_package, load_plan


def test_normal_case_builds_valid_priority_order(tmp_path):
    plan = load_plan(INPUT_PATH)
    output_root = tmp_path / "normal-package"

    ordered = build_package(plan, output_root)
    ordered_ids = []
    for record in ordered:
        ordered_ids.append(record["id"])

    assert ordered_ids == ["sun-compass", "whisper-stone", "tide-chime"]
    assert load_explorer_package(output_root).is_loaded


def test_boundary_case_allows_exactly_three_included_records(tmp_path):
    plan = deepcopy(load_plan(INPUT_PATH))
    plan["objects"] = plan["objects"][:3]

    ordered = build_package(plan, tmp_path / "boundary-package")

    assert len(ordered) == 3


def test_malformed_record_fails_before_package_write(tmp_path):
    plan = deepcopy(load_plan(INPUT_PATH))
    del plan["objects"][0]["priority"]
    output_root = tmp_path / "invalid-package"

    with pytest.raises(ValueError, match="valid records"):
        build_package(plan, output_root)

    assert not output_root.exists()


# TODO: after explaining determinism, add one repeat-build byte comparison.
