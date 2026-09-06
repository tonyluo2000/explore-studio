"""Immutable canonical course mission catalog."""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

from engine.scenes import ClassroomTrailMission

MISSION_01_ID: Final = "visit-all-classroom-objects"
MISSION_02_ID: Final = "create-a-classroom-object"

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

_MISSIONS = (MISSION_01, MISSION_02)
COURSE_MISSION_CATALOG = MappingProxyType(
    {mission.mission_id: mission for mission in sorted(_MISSIONS, key=lambda item: item.mission_id)}
)
CANONICAL_COURSE_MISSION_IDS: Final = tuple(COURSE_MISSION_CATALOG)


def get_course_mission(mission_id: str) -> ClassroomTrailMission:
    """Return one exact canonical mission or fail closed without a fallback."""
    if not isinstance(mission_id, str) or mission_id not in COURSE_MISSION_CATALOG:
        raise KeyError("unknown canonical course mission ID")
    return COURSE_MISSION_CATALOG[mission_id]
