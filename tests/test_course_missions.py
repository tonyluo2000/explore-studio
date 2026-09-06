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
    MISSION_02,
    MISSION_02_ID,
    MISSION_03,
    MISSION_03_ID,
    MISSION_04,
    MISSION_04_ID,
    get_course_mission,
)


def test_catalog_contains_exactly_missions_01_through_04_by_deterministic_identity() -> None:
    assert MISSION_01_ID == "visit-all-classroom-objects"
    assert MISSION_02_ID == "create-a-classroom-object"
    assert MISSION_03_ID == "make-your-object-respond"
    assert MISSION_04_ID == "introduce-your-character"
    assert CANONICAL_COURSE_MISSION_IDS == (
        MISSION_02_ID,
        MISSION_04_ID,
        MISSION_03_ID,
        MISSION_01_ID,
    )
    assert tuple(COURSE_MISSION_CATALOG) == CANONICAL_COURSE_MISSION_IDS
    assert tuple(COURSE_MISSION_CATALOG.values()) == (
        MISSION_02,
        MISSION_04,
        MISSION_03,
        MISSION_01,
    )


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


def test_mission_02_lookup_returns_exact_immutable_definition() -> None:
    mission = get_course_mission(MISSION_02_ID)

    assert mission is MISSION_02
    assert mission.title == "Create Your First Object"
    assert mission.instructions == (
        "Create a named world object, choose its x and y position and color, "
        "then interact with every classroom object."
    )
    assert mission.completion_rule is ClassroomTrailMissionCompletionRule.ALL_OBJECTS_VISITED
    with pytest.raises(FrozenInstanceError):
        mission.instructions = "Changed"  # type: ignore[misc]


def test_mission_03_requires_authored_object_response_text() -> None:
    mission = get_course_mission(MISSION_03_ID)

    assert mission is MISSION_03
    assert mission.title == "Make It Respond"
    assert mission.instructions == (
        "Author when_near and when_interacted text for your world object, "
        "then interact with every classroom object."
    )
    assert "when_near" in mission.instructions
    assert "when_interacted" in mission.instructions
    assert mission.completion_rule is ClassroomTrailMissionCompletionRule.ALL_OBJECTS_VISITED
    with pytest.raises(FrozenInstanceError):
        mission.instructions = "Changed"  # type: ignore[misc]


def test_mission_04_requires_an_authored_greeting_and_npc_interactions() -> None:
    mission = get_course_mission(MISSION_04_ID)

    assert mission is MISSION_04
    assert mission.title == "Give Your Character a Voice"
    assert mission.instructions == (
        "Author a greeting for one character, then speak to every interactable NPC."
    )
    assert "greeting" in mission.instructions
    assert "every interactable NPC" in mission.instructions
    assert (
        mission.completion_rule
        is ClassroomTrailMissionCompletionRule.ALL_INTERACTABLE_NPCS_SPOKEN_TO
    )
    with pytest.raises(FrozenInstanceError):
        mission.instructions = "Changed"  # type: ignore[misc]


@pytest.mark.parametrize("mission_id", ["mission-05", "introduce-character", "", None, 1])
def test_unknown_mission_id_fails_closed(mission_id: object) -> None:
    with pytest.raises(KeyError, match="unknown canonical course mission ID"):
        get_course_mission(mission_id)  # type: ignore[arg-type]
