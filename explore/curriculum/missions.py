"""Immutable canonical course mission catalog."""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

from engine.scenes import ClassroomTrailMission, ClassroomTrailMissionCompletionRule

MISSION_01_ID: Final = "visit-all-classroom-objects"
MISSION_02_ID: Final = "create-a-classroom-object"
MISSION_03_ID: Final = "make-your-object-respond"
MISSION_04_ID: Final = "introduce-your-character"
MISSION_05_ID: Final = "write-a-short-conversation"
MISSION_06_ID: Final = "build-an-object-collection"
MISSION_07_ID: Final = "toggle-an-object-state"
MISSION_08_ID: Final = "respond-to-object-state"
MISSION_09_ID: Final = "count-object-interactions"
MISSION_10_ID: Final = "require-all-switches-on"

MISSION_01: Final = ClassroomTrailMission(
    mission_id=MISSION_01_ID,
    title="Explore Every Object",
    instructions="Interact with every classroom object.",
)

MISSION_02: Final = ClassroomTrailMission(
    mission_id=MISSION_02_ID,
    title="Create Your First Object",
    instructions=(
        "Create a named world object, choose its x and y position and color, "
        "then interact with every classroom object."
    ),
)

MISSION_03: Final = ClassroomTrailMission(
    mission_id=MISSION_03_ID,
    title="Make It Respond",
    instructions=(
        "Author when_near and when_interacted text for your world object, "
        "then interact with every classroom object."
    ),
)

MISSION_04: Final = ClassroomTrailMission(
    mission_id=MISSION_04_ID,
    title="Give Your Character a Voice",
    instructions=("Author a greeting for one character, then speak to every interactable NPC."),
    completion_rule=ClassroomTrailMissionCompletionRule.ALL_INTERACTABLE_NPCS_SPOKEN_TO,
)

MISSION_05: Final = ClassroomTrailMission(
    mission_id=MISSION_05_ID,
    title="Write a Conversation",
    instructions=(
        "Author a 2–3-line conversation for one character, then speak through every "
        "conversation NPC's final line."
    ),
    completion_rule=ClassroomTrailMissionCompletionRule.ALL_CONVERSATION_NPCS_COMPLETED,
)

MISSION_06: Final = ClassroomTrailMission(
    mission_id=MISSION_06_ID,
    title="Build a Curious Collection",
    instructions=(
        "Create three related objects with distinct names, positions, colors, and responses, "
        "then interact with every classroom object."
    ),
)

MISSION_07: Final = ClassroomTrailMission(
    mission_id=MISSION_07_ID,
    title="Flip a Magic Switch",
    instructions=(
        "Give one object distinct off and on colors, then interact with every toggle object "
        "at least once."
    ),
    completion_rule=ClassroomTrailMissionCompletionRule.ALL_TOGGLE_OBJECTS_CHANGED,
)

MISSION_08: Final = ClassroomTrailMission(
    mission_id=MISSION_08_ID,
    title="Make an If/Else Character",
    instructions=(
        "Link one NPC to a toggle object, write a response for OFF and ON, then talk to the NPC "
        "in both states."
    ),
    completion_rule=ClassroomTrailMissionCompletionRule.ALL_CONDITIONAL_BRANCHES_DISPLAYED,
)

MISSION_09: Final = ClassroomTrailMission(
    mission_id=MISSION_09_ID,
    title="Power It Up",
    instructions=(
        "Give an object a goal from 2 to 5 and a goal-reached message, then interact until every "
        "counter object reaches its goal."
    ),
    completion_rule=ClassroomTrailMissionCompletionRule.ALL_COUNTER_GOALS_REACHED,
)

MISSION_10: Final = ClassroomTrailMission(
    mission_id=MISSION_10_ID,
    title="Unlock the Secret",
    instructions=(
        "Connect one NPC to two toggle objects, write a fallback and success response, then "
        "talk to the NPC both before and after both switches are on."
    ),
    completion_rule=ClassroomTrailMissionCompletionRule.ALL_TWO_TOGGLE_BRANCHES_DISPLAYED,
)

_MISSIONS = (
    MISSION_01,
    MISSION_02,
    MISSION_03,
    MISSION_04,
    MISSION_05,
    MISSION_06,
    MISSION_07,
    MISSION_08,
    MISSION_09,
    MISSION_10,
)
COURSE_MISSION_CATALOG = MappingProxyType(
    {mission.mission_id: mission for mission in sorted(_MISSIONS, key=lambda item: item.mission_id)}
)
CANONICAL_COURSE_MISSION_IDS: Final = tuple(COURSE_MISSION_CATALOG)


def get_course_mission(mission_id: str) -> ClassroomTrailMission:
    """Return one exact canonical mission or fail closed without a fallback."""
    if not isinstance(mission_id, str) or mission_id not in COURSE_MISSION_CATALOG:
        raise KeyError("unknown canonical course mission ID")
    return COURSE_MISSION_CATALOG[mission_id]
