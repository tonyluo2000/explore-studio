"""Focused S30 learner checks for final presentation evidence."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from lessons.sessions.s30.student import premiere_evidence

EXPECTED_MEMBERS = (
    "manifest.yaml",
    "objects/echo-lens.yaml",
    "objects/wind-dial.yaml",
    "objects/comet-bell.yaml",
    "character/sky-guide.yaml",
)
EXPECTED_OBJECTS = (
    "skyglass-premiere:comet-bell",
    "skyglass-premiere:echo-lens",
    "skyglass-premiere:wind-dial",
)


def test_final_package_validates_plans_and_exports_twice(tmp_path):
    evidence = premiere_evidence.collect_premiere_evidence(tmp_path / "exports")

    assert evidence.package_id == "skyglass-premiere"
    assert evidence.package_version == "1.0.0"
    assert evidence.member_paths == EXPECTED_MEMBERS
    assert evidence.world_object_ids == EXPECTED_OBJECTS
    assert evidence.archive_bytes > 0


def test_two_exports_have_identical_archive_bytes_and_digest(tmp_path):
    evidence = premiere_evidence.collect_premiere_evidence(tmp_path / "exports")

    assert evidence.exports_match
    assert evidence.first_sha256 == evidence.second_sha256
    assert len(evidence.first_sha256) == 64


def test_final_evidence_uses_existing_m16_and_is_immutable(tmp_path):
    evidence = premiere_evidence.collect_premiere_evidence(tmp_path / "exports")

    assert evidence.mission_id == "present-your-capstone-expedition"
    with pytest.raises(FrozenInstanceError):
        evidence.exports_match = False


def test_invalid_package_stops_before_export(tmp_path):
    package_root = tmp_path / "broken-package"
    package_root.mkdir()
    output_root = tmp_path / "exports"

    with pytest.raises(premiere_evidence.PremiereEvidenceError, match="validation failed"):
        premiere_evidence.collect_premiere_evidence(output_root, package_root)

    assert not output_root.exists()
