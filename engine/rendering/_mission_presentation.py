"""Which Trail missions receive the Moon Meadow presentation, and how much of it.

This is the single, explicit mission boundary for every cosmetic layer: the
illustrated backdrop and foreground, ambient life, trusted sprites and their
poses, entity effects, the HUD panel, proximity prompts, and the Moon Meadow
audio. A mission absent
from :data:`MISSION_PRESENTATIONS` keeps the plain cleared frame and the static
procedural sprites, exactly as before.

A mission id must be chosen explicitly to receive its presentation: a Trail
launched without ``--mission-id`` keeps M01's completion rule on the plain
Trail (see ``explore.packages.classroom_trail``), so M01's entry here never
leaks into free-play runs.

Most presentations are mission-wide. Reused missions can instead opt in one
exact package identity through :data:`PACKAGE_SCOPED_PRESENTATIONS`. That is
the session boundary for S06: later sessions reuse M06 with different packages
and receive their own course profiles when migrated deliberately.
S10–S30 profiles preserve the same boundary. An explicit presentation session
lets student-owned packages change identity without adding YAML fields or
changing their selected mission. S26 is planning-only and has no profile.

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

from engine.rendering._classroom_sprites import (
    MOON_COMPASS_QUALIFIED_ID,
    MOONLIT_GUIDE_QUALIFIED_ID,
    RAIN_BELL_PRESENTATION_ID,
    SKY_LANTERN_PRESENTATION_ID,
    STORM_ENGINE_PRESENTATION_ID,
    SUN_SEED_PRESENTATION_ID,
    WIND_FLOWER_PRESENTATION_ID,
)

#: Match ``explore.curriculum.MISSION_01_ID`` .. ``MISSION_05_ID`` without
#: importing the course layer into the engine (a test keeps them equal).
S01_MISSION_ID: Final = "visit-all-classroom-objects"
S02_MISSION_ID: Final = "create-a-classroom-object"
S03_MISSION_ID: Final = "make-your-object-respond"
S04_MISSION_ID: Final = "introduce-your-character"
S05_MISSION_ID: Final = "write-a-short-conversation"
S06_MISSION_ID: Final = "build-an-object-collection"
S07_MISSION_ID: Final = "toggle-an-object-state"
S07_PACKAGE_ID: Final = "sky-lantern-switch"
S07_SKY_LANTERN_QUALIFIED_ID: Final = f"{S07_PACKAGE_ID}:sky-lantern"
S09_MISSION_ID: Final = "count-object-interactions"
S09_PACKAGE_ID: Final = "storm-engine"
S09_DEVICE_QUALIFIED_ID: Final = "storm-engine:storm-engine"
S08_MISSION_ID: Final = "respond-to-object-state"
S08_PACKAGE_ID: Final = "cloud-gate"
S08_SKY_SWITCH_QUALIFIED_ID: Final = f"{S08_PACKAGE_ID}:sky-switch"
S08_GATE_GUARDIAN_QUALIFIED_ID: Final = f"{S08_PACKAGE_ID}:gate-guardian"

#: The canonical S03 package (``lessons/sessions/s03/student/explorer-package``)
#: ships the same Moon Compass under its own package id.
S03_MOON_COMPASS_QUALIFIED_ID: Final = "moon-compass-response:compass"
#: The canonical S05 package (``lessons/sessions/s05/student/explorer-package``)
#: ships the same Moonlit Guide under its own package id.
S05_MOONLIT_GUIDE_QUALIFIED_ID: Final = "moonlit-conversation:guide"

#: The canonical S06 package and its three authored objects. The presentation
#: aliases are private visual roles; package names and response text still come
#: from the validated YAML registrations.
S06_PACKAGE_ID: Final = "starlight-garden"
S06_SUN_SEED_QUALIFIED_ID: Final = f"{S06_PACKAGE_ID}:sun-seed"
S06_RAIN_BELL_QUALIFIED_ID: Final = f"{S06_PACKAGE_ID}:rain-bell"
S06_WIND_FLOWER_QUALIFIED_ID: Final = f"{S06_PACKAGE_ID}:wind-flower"


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
    #: The floating gem that marks the Crystal Lantern until it is inspected.
    #: Only missions whose completion includes visiting the Lantern show it.
    lantern_waypoint: bool = False
    #: A small speech cue over each interactable NPC the mission still needs,
    #: for missions completed by talking: until it is spoken to (M04's
    #: ``ALL_INTERACTABLE_NPCS_SPOKEN_TO``), or, for an NPC with a 2-3-line
    #: conversation, until its final line is shown (M05's
    #: ``ALL_CONVERSATION_NPCS_COMPLETED``).
    talk_cue: bool = False
    #: Dialogue is the lesson: a larger, longer-lived speech bubble sized to the
    #: whole line, placed clear of the HUD, and an on-screen HUD echo. Each line
    #: of a 2-3-line conversation gets the same bubble as it is spoken.
    dialogue_focus: bool = False
    #: The Moon Meadow ambience and its interaction, step, and completion cues
    #: (``engine.audio``). Off unless a mission opts in; never gameplay.
    meadow_audio: bool = False
    #: Give long object near/interacted responses a wrapped lower-screen card.
    #: The response still comes directly from the package-backed scene state.
    object_feedback_focus: bool = False
    #: Optional presentation-only player spawn. This is package-scoped when a
    #: reused mission needs a coherent visual route without moving authored objects.
    player_start: tuple[int, int] | None = None
    #: Later course profiles infer cosmetic roles from validated entity types.
    authored_roles: bool = False
    #: Package qualified id -> the trusted-art identity it is drawn and posed as.
    sprite_aliases: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))


MISSION_PRESENTATIONS: Final[Mapping[str, MissionPresentation]] = MappingProxyType(
    {
        # S01 is the arrival: the frozen meadow, Nova, Pixel, and the Lantern
        # with the shared layers only. No waypoint (students predict what
        # counts), no M02 label or celebration, no talk cue, and no audio.
        S01_MISSION_ID: MissionPresentation(),
        S02_MISSION_ID: MissionPresentation(
            discovery_label=True, celebration=True, lantern_waypoint=True, meadow_audio=True
        ),
        # S03's own clue and reveal text are the story, so M02's discovery
        # label and celebration stay out of it.
        S03_MISSION_ID: MissionPresentation(
            lantern_waypoint=True,
            meadow_audio=True,
            sprite_aliases=MappingProxyType(
                {S03_MOON_COMPASS_QUALIFIED_ID: MOON_COMPASS_QUALIFIED_ID}
            ),
        ),
        # S04 completes by talking to the Moonlit Guide, so the Guide carries
        # the cue and the dialogue is the focus. The Lantern stays a lit world
        # object without a destination marker, and M02's discovery label and
        # celebration stay out of it.
        S04_MISSION_ID: MissionPresentation(talk_cue=True, dialogue_focus=True, meadow_audio=True),
        # S05 continues the same conversation at the same spot: S04's Guide
        # treatment, worn by the S05 package's Guide, one bubble per line.
        S05_MISSION_ID: MissionPresentation(
            talk_cue=True,
            dialogue_focus=True,
            meadow_audio=True,
            sprite_aliases=MappingProxyType(
                {S05_MOONLIT_GUIDE_QUALIFIED_ID: MOONLIT_GUIDE_QUALIFIED_ID}
            ),
        ),
    }
)


PACKAGE_SCOPED_PRESENTATIONS: Final[Mapping[tuple[str, str], MissionPresentation]] = (
    MappingProxyType(
        {
            # S06 alone continues the Moonlit expedition. M06 is reused by
            # S16/S17/S21/S27, whose package ids intentionally do not match.
            (S06_MISSION_ID, S06_PACKAGE_ID): MissionPresentation(
                celebration=True,
                meadow_audio=True,
                object_feedback_focus=True,
                player_start=(80, 180),
                sprite_aliases=MappingProxyType(
                    {
                        S06_SUN_SEED_QUALIFIED_ID: SUN_SEED_PRESENTATION_ID,
                        S06_RAIN_BELL_QUALIFIED_ID: RAIN_BELL_PRESENTATION_ID,
                        S06_WIND_FLOWER_QUALIFIED_ID: WIND_FLOWER_PRESENTATION_ID,
                    }
                ),
            ),
            # Only S07: later toggle/style sessions retain their own presentation.
            (S07_MISSION_ID, S07_PACKAGE_ID): MissionPresentation(
                celebration=True,
                meadow_audio=True,
                object_feedback_focus=True,
                player_start=(240, 300),
                sprite_aliases=MappingProxyType(
                    {S07_SKY_LANTERN_QUALIFIED_ID: SKY_LANTERN_PRESENTATION_ID}
                ),
            ),
            # M09 is reused later: only the authored S09 package opts in.
            (S09_MISSION_ID, S09_PACKAGE_ID): MissionPresentation(
                celebration=True,
                meadow_audio=True,
                object_feedback_focus=True,
                player_start=(280, 300),
                sprite_aliases=MappingProxyType(
                    {S09_DEVICE_QUALIFIED_ID: STORM_ENGINE_PRESENTATION_ID}
                ),
            ),
            (S08_MISSION_ID, S08_PACKAGE_ID): MissionPresentation(
                celebration=True,
                talk_cue=True,
                dialogue_focus=True,
                meadow_audio=True,
                object_feedback_focus=True,
                player_start=(710, 290),
                sprite_aliases=MappingProxyType(
                    {
                        S08_SKY_SWITCH_QUALIFIED_ID: SKY_LANTERN_PRESENTATION_ID,
                        S08_GATE_GUARDIAN_QUALIFIED_ID: MOONLIT_GUIDE_QUALIFIED_ID,
                    }
                ),
            ),
        }
    )
)


# Explicit session boundaries. S26 is planning-only and has no Trail profile.
# The extra package ids are the authored generator/recovery identities, not wildcards.
COURSE_TRAIL_PROFILES: Final = MappingProxyType(
    {
        "S10": (("storm-observatory",), ("compare-a-counter-to-its-goal",), (680, 260)),
        "S11": (("twin-star-vault",), ("require-all-switches-on",), (700, 260)),
        "S12": (("storm-rescue-signals",), ("open-with-either-switch",), (710, 330)),
        "S13": (("moonflower-garden",), ("invert-a-switch-condition",), (650, 300)),
        "S14": (("twin-beacon-style",), ("reuse-a-named-toggle-style",), (140, 220)),
        "S15": (("star-song-sequence",), ("complete-actions-in-order",), (740, 230)),
        "S16": (("curators-atlas",), ("build-an-object-collection",), (100, 190)),
        "S17": (("clue-finder",), ("build-an-object-collection",), (110, 390)),
        "S18": (
            ("power-scoreboard",),
            ("compare-a-counter-to-its-goal", "count-object-interactions"),
            (670, 310),
        ),
        "S19": (("priority-route",), ("complete-actions-in-order",), (750, 390)),
        "S20": (("data-built-mystery",), ("complete-actions-in-order",), (750, 220)),
        "S21": (("ranger-gatekeeper-kit",), ("build-an-object-collection",), (100, 190)),
        "S22": (("prism-guardian-repair",), ("respond-to-object-state",), (660, 260)),
        "S23": (
            ("builders-workshop-twins", "workshop-twins", "my-workshop-system"),
            ("reuse-a-named-toggle-style", "respond-to-object-state"),
            (700, 220),
        ),
        "S24": (("fast-ranger-route",), ("complete-actions-in-order",), (740, 220)),
        "S25": (
            ("my-playable-prototype", "stormlight-rescue-trail"),
            (
                "complete-actions-in-order",
                "count-object-interactions",
                "respond-to-object-state",
                "require-all-switches-on",
                "open-with-either-switch",
                "compare-a-counter-to-its-goal",
            ),
            (760, 210),
        ),
        "S27": (
            ("skyglass-core",),
            ("build-an-object-collection", "reuse-a-named-toggle-style"),
            (140, 300),
        ),
        "S28": (
            ("skyglass-integration",),
            ("reuse-a-named-toggle-style", "complete-actions-in-order"),
            (140, 300),
        ),
        "S29": (
            ("skyglass-review",),
            ("reuse-a-named-toggle-style", "complete-actions-in-order"),
            (140, 300),
        ),
        "S30": (
            ("skyglass-premiere",),
            (
                "present-your-capstone-expedition",
                "reuse-a-named-toggle-style",
                "complete-actions-in-order",
            ),
            (140, 300),
        ),
    }
)


def _course_profile(session: str) -> MissionPresentation:
    return MissionPresentation(
        celebration=True,
        talk_cue=True,
        dialogue_focus=True,
        meadow_audio=True,
        object_feedback_focus=True,
        authored_roles=True,
        player_start=COURSE_TRAIL_PROFILES[session][2],
    )


def mission_presentation(
    mission_id: str | None,
    *,
    package_ids: tuple[str, ...] = (),
    presentation_session: str | None = None,
) -> MissionPresentation | None:
    """Return this exact Trail's presentation, or ``None`` for the plain Trail.

    Mission-wide entries remain the normal policy. A package-scoped entry is
    selected only when the canonical package is actually loaded, preventing a
    reused mission id from silently changing later curriculum sessions.
    """
    if presentation_session is not None:
        if presentation_session not in COURSE_TRAIL_PROFILES:
            raise ValueError("unknown Trail presentation session")
        if mission_id not in COURSE_TRAIL_PROFILES[presentation_session][1]:
            raise ValueError("presentation session does not support this mission")
        return _course_profile(presentation_session)
    if not isinstance(mission_id, str):
        return None
    policy = MISSION_PRESENTATIONS.get(mission_id)
    if policy is not None:
        return policy
    if not isinstance(package_ids, tuple) or any(
        not isinstance(package_id, str) for package_id in package_ids
    ):
        return None
    matches = [
        policy
        for (scoped_mission, package_id), policy in PACKAGE_SCOPED_PRESENTATIONS.items()
        if scoped_mission == mission_id and package_id in package_ids
    ]
    if matches:
        return matches[0] if len(matches) == 1 else None
    course_matches = [
        session
        for session, (identities, missions, _) in COURSE_TRAIL_PROFILES.items()
        if mission_id in missions and any(identity in package_ids for identity in identities)
    ]
    return _course_profile(course_matches[0]) if len(course_matches) == 1 else None
