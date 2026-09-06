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
    MISSION_05,
    MISSION_05_ID,
    MISSION_06,
    MISSION_06_ID,
    MISSION_07,
    MISSION_07_ID,
    MISSION_08,
    MISSION_08_ID,
    get_course_mission,
)


def test_catalog_contains_exactly_missions_01_through_08_by_deterministic_identity() -> None:
    assert MISSION_01_ID == "visit-all-classroom-objects"
    assert MISSION_02_ID == "create-a-classroom-object"
    assert MISSION_03_ID == "make-your-object-respond"
    assert MISSION_04_ID == "introduce-your-character"
    assert MISSION_05_ID == "write-a-short-conversation"
    assert MISSION_06_ID == "build-an-object-collection"
    assert MISSION_07_ID == "toggle-an-object-state"
    assert MISSION_08_ID == "respond-to-object-state"
    assert CANONICAL_COURSE_MISSION_IDS == (
        MISSION_06_ID,
        MISSION_02_ID,
        MISSION_04_ID,
        MISSION_03_ID,
        MISSION_08_ID,
        MISSION_07_ID,
        MISSION_01_ID,
        MISSION_05_ID,
    )
    assert tuple(COURSE_MISSION_CATALOG) == CANONICAL_COURSE_MISSION_IDS
    assert tuple(COURSE_MISSION_CATALOG.values()) == (
        MISSION_06,
        MISSION_02,
        MISSION_04,
        MISSION_03,
        MISSION_08,
        MISSION_07,
        MISSION_01,
        MISSION_05,
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


def test_mission_05_requires_an_authored_short_conversation_and_final_lines() -> None:
    mission = get_course_mission(MISSION_05_ID)

    assert mission is MISSION_05
    assert mission.title == "Write a Conversation"
    assert mission.instructions == (
        "Author a 2–3-line conversation for one character, then speak through every "
        "conversation NPC's final line."
    )
    assert "2–3-line conversation" in mission.instructions
    assert "every conversation NPC's final line" in mission.instructions
    assert (
        mission.completion_rule
        is ClassroomTrailMissionCompletionRule.ALL_CONVERSATION_NPCS_COMPLETED
    )
    with pytest.raises(FrozenInstanceError):
        mission.instructions = "Changed"  # type: ignore[misc]


def test_mission_06_requires_three_distinct_related_objects_and_existing_completion() -> None:
    mission = get_course_mission(MISSION_06_ID)

    assert mission is MISSION_06
    assert mission.title == "Build a Curious Collection"
    assert mission.instructions == (
        "Create three related objects with distinct names, positions, colors, and responses, "
        "then interact with every classroom object."
    )
    for requirement in ("three related objects", "names", "positions", "colors", "responses"):
        assert requirement in mission.instructions
    assert mission.completion_rule is ClassroomTrailMissionCompletionRule.ALL_OBJECTS_VISITED
    with pytest.raises(FrozenInstanceError):
        mission.instructions = "Changed"  # type: ignore[misc]


def test_mission_07_requires_toggling_every_toggle_object() -> None:
    mission = get_course_mission(MISSION_07_ID)

    assert mission is MISSION_07
    assert mission.title == "Flip a Magic Switch"
    assert mission.instructions == (
        "Give one object distinct off and on colors, then interact with every toggle object "
        "at least once."
    )
    assert mission.completion_rule is ClassroomTrailMissionCompletionRule.ALL_TOGGLE_OBJECTS_CHANGED
    with pytest.raises(FrozenInstanceError):
        mission.instructions = "Changed"  # type: ignore[misc]


def test_mission_08_requires_displaying_both_conditional_branches() -> None:
    mission = get_course_mission(MISSION_08_ID)

    assert mission is MISSION_08
    assert mission.title == "Make an If/Else Character"
    assert mission.instructions == (
        "Link one NPC to a toggle object, write a response for OFF and ON, then talk to the NPC "
        "in both states."
    )
    assert (
        mission.completion_rule
        is ClassroomTrailMissionCompletionRule.ALL_CONDITIONAL_BRANCHES_DISPLAYED
    )
    with pytest.raises(FrozenInstanceError):
        mission.instructions = "Changed"  # type: ignore[misc]


@pytest.mark.parametrize("mission_id", ["mission-09", "write-conversation", "", None, 1])
def test_unknown_mission_id_fails_closed(mission_id: object) -> None:
    with pytest.raises(KeyError, match="unknown canonical course mission ID"):
        get_course_mission(mission_id)  # type: ignore[arg-type]
