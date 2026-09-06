"""Focused tests for the immutable canonical course mission catalog."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from engine.scenes import ClassroomTrailMissionCompletionRule
from explore.curriculum import (
    CANONICAL_COURSE_MISSION_IDS,
    COURSE_MISSION_CATALOG,
    MISSION_01,
    MISSION_01_ID,
    get_course_mission,
)


def test_catalog_contains_exactly_mission_01_by_deterministic_identity() -> None:
    assert MISSION_01_ID == "visit-all-classroom-objects"
    assert CANONICAL_COURSE_MISSION_IDS == (MISSION_01_ID,)
    assert tuple(COURSE_MISSION_CATALOG) == CANONICAL_COURSE_MISSION_IDS
    assert tuple(COURSE_MISSION_CATALOG.values()) == (MISSION_01,)


def test_mission_01_lookup_returns_exact_immutable_definition() -> None:
    mission = get_course_mission(MISSION_01_ID)

    assert mission is MISSION_01
    assert mission.title == "Explore Every Object"
    assert mission.instructions == "Interact with every classroom object."
    assert mission.completion_rule is ClassroomTrailMissionCompletionRule.ALL_OBJECTS_VISITED
    with pytest.raises(FrozenInstanceError):
        mission.title = "Changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        COURSE_MISSION_CATALOG[MISSION_01_ID] = mission  # type: ignore[index]


@pytest.mark.parametrize("mission_id", ["mission-02", "", None, 1])
def test_unknown_mission_id_fails_closed(mission_id: object) -> None:
    with pytest.raises(KeyError, match="unknown canonical course mission ID"):
        get_course_mission(mission_id)  # type: ignore[arg-type]
