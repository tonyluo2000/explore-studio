"""Which Trail missions receive the Moon Meadow presentation, and how much of it.

This is the single, explicit mission boundary for every cosmetic layer: the
illustrated backdrop and foreground, ambient life, trusted sprites and their
poses, entity effects, the HUD panel, and proximity prompts. A mission absent
from :data:`MISSION_PRESENTATIONS` keeps the plain cleared frame and the static
procedural sprites, exactly as before.

Presentation never changes gameplay. Per-mission options only *withhold*
story beats that belong to one session, and alias a mission's canonical
package identity onto the trusted art it should wear.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from engine.rendering._classroom_sprites import MOON_COMPASS_QUALIFIED_ID

#: Match ``explore.curriculum.MISSION_02_ID`` / ``MISSION_03_ID`` without
#: importing the course layer into the engine (a test keeps them equal).
S02_MISSION_ID: Final = "create-a-classroom-object"
S03_MISSION_ID: Final = "make-your-object-respond"

#: The canonical S03 package (``lessons/sessions/s03/student/explorer-package``)
#: ships the same Moon Compass under its own package id.
S03_MOON_COMPASS_QUALIFIED_ID: Final = "moon-compass-response:compass"


@dataclass(frozen=True)
class MissionPresentation:
    """The Moon Meadow presentation one mission receives.

    Every listed mission gets the shared layers. The flags below are the
    session-specific extras, off unless a mission opts in.
    """

    #: M02's "<name> discovered!" label on the first Compass inspection.
    discovery_label: bool = False
    #: M02's confetti and "Mission complete!" banner.
    celebration: bool = False
    #: Package qualified id -> the trusted-art identity it is drawn and posed as.
    sprite_aliases: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))


MISSION_PRESENTATIONS: Final[Mapping[str, MissionPresentation]] = MappingProxyType(
    {
        S02_MISSION_ID: MissionPresentation(discovery_label=True, celebration=True),
        # S03's own clue and reveal text are the story, so M02's discovery
        # label and celebration stay out of it.
        S03_MISSION_ID: MissionPresentation(
            sprite_aliases=MappingProxyType(
                {S03_MOON_COMPASS_QUALIFIED_ID: MOON_COMPASS_QUALIFIED_ID}
            ),
        ),
    }
)


def mission_presentation(mission_id: str) -> MissionPresentation | None:
    """Return the mission's presentation, or ``None`` for the plain Trail."""
    return MISSION_PRESENTATIONS.get(mission_id) if isinstance(mission_id, str) else None
