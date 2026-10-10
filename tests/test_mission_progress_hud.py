"""The Trail HUD's progress row and completion banner follow the active mission.

Regression for the S04 classroom report: M04 ("Give Your Character a Voice")
completes from the Moonlit Guide's greeting, yet the HUD still read
``Visited 0 / 1`` and ``Trail complete!`` waited for the Crystal Lantern.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.entities import Character, WorldObject
from engine.input import DirectionalInput, InteractionInput
from engine.rendering._trail_presentation import COMPLETE_TEXT_Y, HUD_FONT
from engine.scenes import (
    ClassroomTrailMissionCompletionRule,
    ClassroomTrailNPC,
    ClassroomTrailNPCConditionalResponse,
    ClassroomTrailNPCCounterResponse,
    ClassroomTrailNPCEitherToggleResponse,
    ClassroomTrailNPCSequenceResponse,
    ClassroomTrailNPCTwoToggleResponse,
    ClassroomTrailObject,
    ClassroomTrailObjectCounter,
    ClassroomTrailObjectToggle,
    ClassroomTrailScene,
)
from engine.scenes._classroom_trail_scene import _PROGRESS_LABELS
from explore.curriculum import (
    COURSE_MISSION_CATALOG,
    MISSION_01_ID,
    MISSION_02_ID,
    MISSION_03_ID,
    MISSION_04_ID,
)
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from tests.test_s02_art_pass import ArtRenderer

REPO = Path(__file__).resolve().parents[1]
EXAMPLES = REPO / "examples/explorer-packages"
SESSIONS = REPO / "lessons/sessions"
#: Exactly the packages of each canonical S01-S04 ``explore-package trail`` command.
CANONICAL = {
    "S01": (
        MISSION_01_ID,
        (EXAMPLES / "nova-character", EXAMPLES / "pixel-companion", EXAMPLES / "crystal-lantern"),
    ),
    "S02": (
        MISSION_02_ID,
        (
            EXAMPLES / "nova-character",
            EXAMPLES / "pixel-companion",
            EXAMPLES / "crystal-lantern",
            SESSIONS / "s02/student/explorer-package",
        ),
    ),
    "S03": (
        MISSION_03_ID,
        (EXAMPLES / "nova-character", SESSIONS / "s03/student/explorer-package"),
    ),
    "S04": (
        MISSION_04_ID,
        (
            EXAMPLES / "nova-character",
            EXAMPLES / "crystal-lantern",
            SESSIONS / "s04/student/explorer-package",
        ),
    ),
}
NOVA = "nova-character:nova"
GUIDE = "moonlit-guide:guide"
LANTERN = "crystal-lantern:lantern"
STEP = 1 / 60
STILL = DirectionalInput()
NO_E = InteractionInput()
PRESS_E = InteractionInput(interact_pressed=True)
BANNER = "Trail complete!"


def _scene(session: str, *, mission_id: str | None = "canonical"):  # type: ignore[no-untyped-def]
    canonical_mission, packages = CANONICAL[session]
    renderer = ArtRenderer()
    planned = plan_local_classroom_trail(packages, player_qualified_id=NOVA)
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(
        renderer,
        planned.plan,
        mission_id=canonical_mission if mission_id == "canonical" else mission_id,
    )
    scene.enter()
    return scene, renderer


def _frame(scene, renderer: ArtRenderer, directions=STILL, interact=NO_E) -> None:  # type: ignore[no-untyped-def]
    scene.update(directions, interact, STEP)
    renderer.operations.clear()
    scene.render()


def _interact_with(scene, renderer: ArtRenderer, qualified_id: str) -> None:  # type: ignore[no-untyped-def]
    """Walk with real input until *qualified_id* is the target, then press E once."""
    target = next(
        item.world_object if isinstance(item, ClassroomTrailObject) else item.character
        for item in (*scene.objects, *scene.npcs)
        if item.qualified_id == qualified_id
    )
    player = scene.player
    for _ in range(900):
        if scene.target_qualified_id == qualified_id:
            _frame(scene, renderer, interact=PRESS_E)
            return
        dx = target.x + target.width / 2 - (player.x_float + player.width / 2)
        dy = target.y + target.height / 2 - (player.y_float + player.height / 2)
        _frame(
            scene,
            renderer,
            DirectionalInput(left=dx < -2, right=dx > 2, up=dy < -2, down=dy > 2),
        )
    raise AssertionError(f"Nova never reached {qualified_id}")


def _hud(renderer: ArtRenderer) -> list[str]:
    return [str(values[0]) for kind, values in renderer.operations if kind == "text"]


# ---------------------------------------------------------------------------
# S04: the Guide alone completes M04, visibly
# ---------------------------------------------------------------------------


def test_s04_before_greeting_counts_the_guide_not_the_lantern() -> None:
    scene, renderer = _scene("S04")
    _frame(scene, renderer)
    texts = _hud(renderer)
    assert scene.mission.completion_rule.value == "ALL_INTERACTABLE_NPCS_SPOKEN_TO"
    assert scene.mission_progress_label == "Spoken to 0 / 1"
    assert texts[0] == "Spoken to 0 / 1"
    assert not any(text.startswith("Visited") for text in texts)
    assert "Mission state: Incomplete" in texts
    assert BANNER not in texts
    scene.exit()


def test_s04_guide_greeting_completes_and_shows_the_banner_with_nothing_visited() -> None:
    scene, renderer = _scene("S04")
    _frame(scene, renderer)
    _interact_with(scene, renderer, GUIDE)
    texts = _hud(renderer)
    assert scene.spoken_npc_ids == frozenset({GUIDE})
    assert scene.mission_is_complete
    assert scene.visited_count == 0
    assert scene.is_complete is False  # object visitation alone is still 0 / 1
    assert texts[0] == "Spoken to 1 / 1"
    assert "Mission state: Complete" in texts
    assert BANNER in texts
    # The Lantern is still in the world, still unvisited, and not needed.
    assert LANTERN in {item.qualified_id for item in scene.objects}
    assert LANTERN not in scene.visited_qualified_ids
    # The banner's soft card is drawn for it, too.
    rect = scene._presentation.feedback_panel_rect(renderer, scene)
    assert rect is not None and rect[1] < COMPLETE_TEXT_Y < rect[1] + rect[3]
    scene.exit()


def test_s04_lantern_is_optional_and_never_completes_m04_a_second_time() -> None:
    scene, renderer = _scene("S04")
    completions: list[bool] = []
    _frame(scene, renderer)
    _interact_with(scene, renderer, GUIDE)
    completions.append(scene.mission_is_complete)
    for _ in range(30):
        _frame(scene, renderer)
        completions.append(scene.mission_is_complete)
    celebration = scene._presentation.celebration_start
    _interact_with(scene, renderer, LANTERN)
    for _ in range(30):
        _frame(scene, renderer)
        completions.append(scene.mission_is_complete)
        texts = _hud(renderer)
        assert texts[0] == "Spoken to 1 / 1"
        assert BANNER in texts
    assert scene.visited_count == 1
    assert all(completions)
    assert scene._presentation.celebration_start == celebration
    scene.exit()


def test_s04_lantern_alone_does_not_complete_m04() -> None:
    scene, renderer = _scene("S04")
    _frame(scene, renderer)
    _interact_with(scene, renderer, LANTERN)
    texts = _hud(renderer)
    assert scene.is_complete and not scene.mission_is_complete
    assert texts[0] == "Spoken to 0 / 1"
    assert "Mission state: Incomplete" in texts
    assert BANNER not in texts
    scene.exit()


def test_hud_panel_is_sized_for_the_mission_progress_row() -> None:
    scene, renderer = _scene("S04")
    _frame(scene, renderer)
    panel = scene._presentation.hud_panel_rects(renderer, scene)[0]
    label_width = renderer.measure_text("Spoken to 0 / 1", HUD_FONT)[0]
    title_width = renderer.measure_text(f"Mission: {scene.mission.title}", HUD_FONT)[0]
    assert panel[2] == max(label_width, title_width) + 20
    scene.exit()


# ---------------------------------------------------------------------------
# S01-S03 and the plain Trail keep object visitation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("session", ("S01", "S02", "S03"))
def test_s01_to_s03_keep_the_visited_row_and_object_banner(session: str) -> None:
    scene, renderer = _scene(session)
    _frame(scene, renderer)
    total = len(scene.objects)
    assert scene.mission.completion_rule.value == "ALL_OBJECTS_VISITED"
    assert _hud(renderer)[0] == f"Visited 0 / {total}"
    assert BANNER not in _hud(renderer)
    for index, item in enumerate(scene.objects, start=1):
        _interact_with(scene, renderer, item.qualified_id)
        texts = _hud(renderer)
        assert texts[0] == f"Visited {index} / {total}"
        assert scene.mission_progress == (scene.visited_count, scene.total_objects)
        assert (BANNER in texts) is (index == total)
        assert scene.mission_is_complete is scene.is_complete is (index == total)
    scene.exit()


def test_s01_pixel_greeting_still_counts_nothing() -> None:
    scene, renderer = _scene("S01")
    _frame(scene, renderer)
    _interact_with(scene, renderer, "pixel-companion:pixel")
    texts = _hud(renderer)
    assert texts[0] == "Visited 0 / 1"
    assert BANNER not in texts and "Mission state: Incomplete" in texts
    scene.exit()


def test_plain_trail_without_a_mission_keeps_object_visitation() -> None:
    # The S04 cast without --mission-id: the default M01 rule on the plain Trail.
    scene, renderer = _scene("S04", mission_id=None)
    _frame(scene, renderer)
    assert scene.mission.completion_rule.value == "ALL_OBJECTS_VISITED"
    assert _hud(renderer)[0] == "Visited 0 / 1"
    _interact_with(scene, renderer, GUIDE)
    texts = _hud(renderer)
    assert texts[0] == "Visited 0 / 1"
    assert BANNER not in texts and "Mission state: Incomplete" in texts
    _interact_with(scene, renderer, LANTERN)
    texts = _hud(renderer)
    assert texts[0] == "Visited 1 / 1"
    assert BANNER in texts and "Mission state: Complete" in texts
    scene.exit()


# ---------------------------------------------------------------------------
# Every rule: a truthful label that agrees with mission completion
# ---------------------------------------------------------------------------


def test_every_rule_has_a_progress_label_and_only_object_rules_say_visited() -> None:
    assert set(_PROGRESS_LABELS) == set(ClassroomTrailMissionCompletionRule)
    for rule, label in _PROGRESS_LABELS.items():
        is_objects = rule is ClassroomTrailMissionCompletionRule.ALL_OBJECTS_VISITED
        assert (label == "Visited") is is_objects


def _mixed_cast_scene(mission):  # type: ignore[no-untyped-def]
    """One cast with every kind of evidence; only kit:switch starts in range."""

    def thing(name: str, x: int, **options: object) -> ClassroomTrailObject:
        return ClassroomTrailObject(
            f"kit:{name}",
            WorldObject(name=name, x=x, y=0, width=20, height=20, color=(0, 200, 0)),
            **options,
        )

    def npc(name: str, x: int, **options: object) -> ClassroomTrailNPC:
        return ClassroomTrailNPC(
            f"kit:{name}",
            Character(name=name, x=x, y=0, width=20, height=20, color=(0, 0, 200)),
            **options,
        )

    toggle = ClassroomTrailObjectToggle(off_color=(0, 200, 0), on_color=(255, 255, 255))
    objects = (
        thing("switch", 30, toggle=toggle),
        thing("switch2", 600, toggle=toggle),
        thing(
            "battery", 700, counter=ClassroomTrailObjectCounter(goal=2, when_goal_reached="Full!")
        ),
        thing("rock", 800),
    )
    npcs = (
        npc("greeter", 900, greeting="Hi!"),
        npc("talker", 1000, conversation=("One", "Two")),
        npc(
            "oracle",
            1100,
            respond_to_toggle=ClassroomTrailNPCConditionalResponse("kit:switch", "Off", "On"),
        ),
        npc(
            "twin",
            1200,
            respond_to_two_toggles=ClassroomTrailNPCTwoToggleResponse(
                ("kit:switch", "kit:switch2"), "Not yet", "Open"
            ),
        ),
        npc(
            "either",
            1300,
            respond_to_either_toggle=ClassroomTrailNPCEitherToggleResponse(
                ("kit:switch", "kit:switch2"), "Locked", "Open"
            ),
        ),
        npc(
            "gauge",
            1400,
            respond_to_counter=ClassroomTrailNPCCounterResponse("kit:battery", "Low", "High"),
        ),
        npc(
            "keeper",
            1500,
            respond_to_sequence=ClassroomTrailNPCSequenceResponse(
                ("kit:rock", "kit:switch2", "kit:battery"), "Not yet", "Solved"
            ),
        ),
    )
    return ClassroomTrailScene(
        ArtRenderer(),  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(200, 0, 0)),
        objects,
        npcs,
        mission=mission,
        interaction_range=80,
    )


#: Each rule's required evidence in the mixed cast, before and after switch 1 flips.
_EXPECTED = {
    "ALL_OBJECTS_VISITED": ("Visited", 4, 1),
    "ALL_INTERACTABLE_NPCS_SPOKEN_TO": ("Spoken to", 2, 0),
    "ALL_CONVERSATION_NPCS_COMPLETED": ("Conversations", 1, 0),
    "ALL_TOGGLE_OBJECTS_CHANGED": ("Switches", 2, 1),
    "ALL_CONDITIONAL_BRANCHES_DISPLAYED": ("Responses", 2, 0),
    "ALL_COUNTER_GOALS_REACHED": ("Goals", 1, 0),
    "ALL_TWO_TOGGLE_BRANCHES_DISPLAYED": ("Responses", 2, 0),
    "ALL_EITHER_TOGGLE_CASES_DISPLAYED": ("Responses", 3, 0),
    "ALL_COUNTER_COMPARISON_BRANCHES_DISPLAYED": ("Responses", 2, 0),
    "ALL_THREE_OBJECT_SEQUENCES_COMPLETED": ("Sequences", 1, 0),
}


@pytest.mark.parametrize("mission_id", sorted(COURSE_MISSION_CATALOG))
def test_every_course_mission_counts_its_own_rule(mission_id: str) -> None:
    mission = COURSE_MISSION_CATALOG[mission_id]
    label, required, after_switch = _EXPECTED[mission.completion_rule.value]
    scene = _mixed_cast_scene(mission)
    renderer = scene._renderer
    scene.enter()
    scene.update(STILL, NO_E, STEP)
    renderer.operations.clear()
    scene.render()
    assert _hud(renderer)[0] == f"{label} 0 / {required}"
    assert BANNER not in _hud(renderer)
    scene.update(STILL, PRESS_E, STEP)
    renderer.operations.clear()
    scene.render()
    assert scene.target_qualified_id == "kit:switch"
    assert _hud(renderer)[0] == f"{label} {after_switch} / {required}"
    done, total = scene.mission_progress
    assert scene.mission_is_complete is (total > 0 and done == total)
    assert (BANNER in _hud(renderer)) is scene.mission_is_complete
    scene.exit()
