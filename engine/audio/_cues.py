"""Semantic Trail audio cues and the one mix table that voices them.

Presentation code asks for a *cue* ("the Compass was used", "Nova took a
step"); only this table knows which trusted sound plays, how loud, and how
often it may repeat. Change the mix here, never at a call site.

Loudness is set for a classroom: the ambience and footsteps sit far below a
teacher's voice, interaction accents are soft, and only the mission-complete
motif is medium. Every file is normalized at build time (peaks at or under
-2.5 dBFS, the ambience at -20 dBFS RMS), so these volumes are the final
level: even every channel sounding at once stays under full scale.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final


class AudioCue(StrEnum):
    """What happened, never which file plays."""

    AMBIENT_MOON_MEADOW = "ambient_moon_meadow"
    FOOTSTEP_GRASS = "footstep_grass"
    OBJECT_NEAR = "object_near"
    OBJECT_INTERACT = "object_interact"
    COMPASS_MAGIC = "compass_magic"
    PIXEL_GREETING = "pixel_greeting"
    NPC_TALK = "npc_talk"
    LANTERN_CHIME = "lantern_chime"
    MISSION_COMPLETE = "mission_complete"
    UI_MUTE_TOGGLE = "ui_mute_toggle"


class CueBus(StrEnum):
    """Which fixed mixer channel(s) a cue may use."""

    AMBIENCE = "ambience"
    FOOTSTEPS = "footsteps"
    EFFECTS = "effects"


@dataclass(frozen=True)
class CueSpec:
    """How one cue sounds: its trusted sound(s), volume, and repeat limit."""

    #: Trusted audio ids; more than one rotates in order (footstep variety).
    assets: tuple[str, ...]
    #: 0..1 sound volume, applied once at load.
    volume: float
    bus: CueBus = CueBus.EFFECTS
    #: Minimum seconds between two plays of this cue; extra requests are dropped.
    cooldown: float = 0.0


#: Relative mix, quietest first.
AMBIENCE_VOLUME: Final = 0.12
FOOTSTEP_VOLUME: Final = 0.06
NEAR_VOLUME: Final = 0.10
UI_VOLUME: Final = 0.12
PIXEL_VOLUME: Final = 0.18
OBJECT_VOLUME: Final = 0.22
NPC_VOLUME: Final = 0.24
COMPLETE_VOLUME: Final = 0.28

#: Footsteps follow Nova's real foot contacts at a very low level. Set this
#: to False to drop them if a class finds them distracting; nothing else changes.
FOOTSTEPS: Final = True

#: The ambience rises over this long when it starts, and fades over
#: ``AMBIENCE_FADE_OUT_MS`` when the Moon Meadow closes.
AMBIENCE_FADE_IN: Final = 1.5
AMBIENCE_FADE_OUT_MS: Final = 600

CUES: Final[Mapping[AudioCue, CueSpec]] = MappingProxyType(
    {
        AudioCue.AMBIENT_MOON_MEADOW: CueSpec(
            ("ambient/moon-meadow",), AMBIENCE_VOLUME, CueBus.AMBIENCE
        ),
        AudioCue.FOOTSTEP_GRASS: CueSpec(
            ("sfx/footstep-grass-a", "sfx/footstep-grass-b"),
            FOOTSTEP_VOLUME,
            CueBus.FOOTSTEPS,
            cooldown=0.12,
        ),
        AudioCue.OBJECT_NEAR: CueSpec(("sfx/object-near",), NEAR_VOLUME, cooldown=1.5),
        AudioCue.OBJECT_INTERACT: CueSpec(("sfx/object-interact",), OBJECT_VOLUME, cooldown=0.25),
        AudioCue.COMPASS_MAGIC: CueSpec(("sfx/compass-magic",), OBJECT_VOLUME, cooldown=0.6),
        AudioCue.PIXEL_GREETING: CueSpec(("sfx/pixel-greeting",), PIXEL_VOLUME, cooldown=0.6),
        AudioCue.NPC_TALK: CueSpec(("sfx/npc-talk",), NPC_VOLUME, cooldown=0.6),
        AudioCue.LANTERN_CHIME: CueSpec(("sfx/lantern-chime",), OBJECT_VOLUME, cooldown=0.6),
        AudioCue.MISSION_COMPLETE: CueSpec(
            ("sfx/mission-complete",), COMPLETE_VOLUME, cooldown=2.0
        ),
        AudioCue.UI_MUTE_TOGGLE: CueSpec(("sfx/ui-mute-toggle",), UI_VOLUME, cooldown=0.1),
    }
)
