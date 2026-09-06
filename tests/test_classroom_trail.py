"""Focused tests for the additive local Classroom Trail contract."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from engine.entities import Character, WorldObject
from engine.input import DirectionalInput, InteractionInput
from engine.scenes import (
    ClassroomTrailMission,
    ClassroomTrailMissionCompletionRule,
    ClassroomTrailNPC,
    ClassroomTrailNPCConditionalResponse,
    ClassroomTrailNPCEitherToggleResponse,
    ClassroomTrailNPCTwoToggleResponse,
    ClassroomTrailObject,
    ClassroomTrailObjectCounter,
    ClassroomTrailObjectToggle,
    ClassroomTrailScene,
)
from explore.curriculum import (
    MISSION_01,
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
    MISSION_09,
    MISSION_09_ID,
    MISSION_10,
    MISSION_10_ID,
    MISSION_11,
    MISSION_11_ID,
    MISSION_12,
    MISSION_12_ID,
)
from explore.packages import (
    ClassroomTrailPlan,
    ClassroomTrailPlanIssueCode,
    PackageSelection,
    build_classroom_trail_plan,
    build_package_set_plan,
    create_classroom_trail_scene,
    export_explorer_package,
    load_explorer_package,
    plan_loaded_explorer_package,
    plan_local_classroom_trail,
)

_NO_MOVEMENT = DirectionalInput()
_NO_INTERACTION = InteractionInput()
_INTERACT = InteractionInput(interact_pressed=True)


class _RecordingRenderer:
    def __init__(self) -> None:
        self.rectangles: list[tuple[object, ...]] = []
        self.text: list[str] = []

    def draw_rect(self, *values: object) -> None:
        self.rectangles.append(values)

    def draw_text(self, text: str, *values: object) -> None:
        self.text.append(text)


def _trail_object(
    qualified_id: str,
    x: int,
    *,
    name: str | None = None,
    color: tuple[int, int, int] = (0, 255, 0),
    near: str | None = None,
    interacted: str | None = None,
    toggle: ClassroomTrailObjectToggle | None = None,
    counter: ClassroomTrailObjectCounter | None = None,
) -> ClassroomTrailObject:
    return ClassroomTrailObject(
        qualified_id,
        WorldObject(
            name=name or qualified_id,
            x=x,
            y=0,
            width=20,
            height=20,
            color=color,
        ),
        near,
        interacted,
        toggle,
        counter,
    )


def _trail_npc(
    qualified_id: str,
    x: int,
    *,
    name: str | None = None,
    greeting: str | None = None,
    conversation: tuple[str, ...] | None = None,
    respond_to_toggle: ClassroomTrailNPCConditionalResponse | None = None,
    respond_to_two_toggles: ClassroomTrailNPCTwoToggleResponse | None = None,
    respond_to_either_toggle: ClassroomTrailNPCEitherToggleResponse | None = None,
) -> ClassroomTrailNPC:
    return ClassroomTrailNPC(
        qualified_id,
        Character(
            name=name or qualified_id,
            x=x,
            y=0,
            width=20,
            height=20,
            color=(100, 150, 255),
        ),
        greeting,
        conversation,
        respond_to_toggle,
        respond_to_two_toggles,
        respond_to_either_toggle,
    )


def _scene(
    *objects: ClassroomTrailObject,
    npcs: tuple[ClassroomTrailNPC, ...] = (),
    interaction_range: int = 120,
) -> ClassroomTrailScene:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(
            name="Player",
            x=0,
            y=0,
            width=20,
            height=20,
            color=(255, 200, 50),
        ),
        tuple(objects),
        npcs,
        mission=MISSION_01,
        interaction_range=interaction_range,
    )
    scene.enter()
    return scene


def _write_package(
    root: Path,
    package_id: str,
    contribution_id: str,
    contribution_type: str,
    body: str,
) -> Path:
    contribution_dir = "character" if contribution_type == "character" else "objects"
    contribution_path = f"{contribution_dir}/{contribution_id}.yaml"
    root.mkdir()
    (root / contribution_dir).mkdir()
    (root / "manifest.yaml").write_text(
        (
            'schema_version: "0.1"\n'
            "package:\n"
            f'  id: "{package_id}"\n'
            f'  display_name: "{package_id}"\n'
            '  version: "1.0.0"\n'
            "compatibility:\n"
            '  student_api: "0.1"\n'
            "contributions:\n"
            f'  - id: "{contribution_id}"\n'
            f'    type: "{contribution_type}"\n'
            f'    path: "{contribution_path}"\n'
        ),
        encoding="utf-8",
    )
    (root / contribution_path).write_text(body, encoding="utf-8")
    return root


def _selection(root: Path) -> PackageSelection:
    registration = plan_loaded_explorer_package(load_explorer_package(root))
    assert registration.plan is not None
    provenance = registration.plan.provenance
    return PackageSelection(
        provenance.package_id,
        provenance.package_version,
        registration.plan,
    )


@pytest.mark.parametrize("field", ["mission_id", "title", "instructions"])
@pytest.mark.parametrize("invalid", ["", "   ", 42])
def test_local_mission_requires_nonblank_text_fields(field: str, invalid: object) -> None:
    values: dict[str, object] = {
        "mission_id": "visit-all-classroom-objects",
        "title": "Explore Every Object",
        "instructions": "Interact with every classroom object.",
    }
    values[field] = invalid

    with pytest.raises(ValueError, match=field):
        ClassroomTrailMission(**values)  # type: ignore[arg-type]


def test_local_mission_is_immutable_and_supports_exactly_eight_rules() -> None:
    mission = ClassroomTrailMission(
        "visit-all-classroom-objects",
        "Explore Every Object",
        "Interact with every classroom object.",
    )

    assert tuple(ClassroomTrailMissionCompletionRule) == (
        ClassroomTrailMissionCompletionRule.ALL_OBJECTS_VISITED,
        ClassroomTrailMissionCompletionRule.ALL_INTERACTABLE_NPCS_SPOKEN_TO,
        ClassroomTrailMissionCompletionRule.ALL_CONVERSATION_NPCS_COMPLETED,
        ClassroomTrailMissionCompletionRule.ALL_TOGGLE_OBJECTS_CHANGED,
        ClassroomTrailMissionCompletionRule.ALL_CONDITIONAL_BRANCHES_DISPLAYED,
        ClassroomTrailMissionCompletionRule.ALL_COUNTER_GOALS_REACHED,
        ClassroomTrailMissionCompletionRule.ALL_TWO_TOGGLE_BRANCHES_DISPLAYED,
        ClassroomTrailMissionCompletionRule.ALL_EITHER_TOGGLE_CASES_DISPLAYED,
    )
    assert mission.completion_rule is ClassroomTrailMissionCompletionRule.ALL_OBJECTS_VISITED
    with pytest.raises(FrozenInstanceError):
        mission.title = "Changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="ALL_OBJECTS_VISITED"):
        ClassroomTrailMission(
            "invalid-rule",
            "Invalid",
            "Invalid",
            "SOMETHING_ELSE",  # type: ignore[arg-type]
        )


def test_toggle_runtime_model_is_strict_and_immutable() -> None:
    toggle = ClassroomTrailObjectToggle((220, 50, 50), (50, 180, 50))

    with pytest.raises(FrozenInstanceError):
        toggle.on_color = (50, 80, 220)  # type: ignore[misc]
    with pytest.raises(ValueError, match="distinct"):
        ClassroomTrailObjectToggle((220, 50, 50), (220, 50, 50))
    with pytest.raises(ValueError, match="RGB"):
        ClassroomTrailObjectToggle((220, 50), (50, 180, 50))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must equal"):
        _trail_object("switch:bad", 30, color=(50, 80, 220), toggle=toggle)


def test_mission_ui_starts_incomplete_from_existing_trail_state() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("object:lantern", 30),),
        mission=MISSION_01,
    )
    scene.enter()

    scene.render()

    assert scene.mission is MISSION_01
    assert scene.mission_is_complete is False
    assert scene.mission_is_complete == scene.is_complete
    assert "Mission: Explore Every Object" in renderer.text
    assert "Interact with every classroom object." in renderer.text
    assert "Mission state: Incomplete" in renderer.text
    assert "_mission_complete" not in vars(scene)


def test_mission_completion_is_derived_idempotent_and_monotonic() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("object:lantern", 30),),
        mission=MISSION_01,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    scene.render()

    assert scene.visited_qualified_ids == frozenset({"object:lantern"})
    assert scene.mission_is_complete is True
    assert scene.mission_is_complete == scene.is_complete
    assert "Mission state: Complete" in renderer.text
    assert "_mission_complete" not in vars(scene)


def test_mission_06_ui_and_completion_reuse_existing_three_object_trail_behavior() -> None:
    renderer = _RecordingRenderer()
    objects = (
        _trail_object(
            "collection:feather",
            30,
            name="Moon Feather",
            color=(220, 50, 50),
            interacted="The feather hums.",
        ),
        _trail_object(
            "collection:shell",
            190,
            name="Star Shell",
            color=(50, 80, 220),
            interacted="The shell whispers.",
        ),
        _trail_object(
            "collection:stone",
            350,
            name="Sun Stone",
            color=(255, 200, 50),
            interacted="The stone glows.",
        ),
    )
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        objects,
        mission=MISSION_06,
        interaction_range=60,
    )
    scene.enter()

    scene.render()
    assert "Mission: Build a Curious Collection" in renderer.text
    assert MISSION_06.instructions in renderer.text
    assert scene.mission_is_complete is False

    for index, expected_response in enumerate(
        ("The feather hums.", "The shell whispers.", "The stone glows.")
    ):
        if index:
            scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
        scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
        scene.render()
        assert expected_response in renderer.text

    assert [item.world_object.name for item in scene.objects] == [
        "Moon Feather",
        "Star Shell",
        "Sun Stone",
    ]
    assert len({item.world_object.x for item in scene.objects}) == 3
    assert len({item.world_object.color for item in scene.objects}) == 3
    assert scene.visited_qualified_ids == frozenset(item.qualified_id for item in objects)
    assert scene.mission_is_complete is True
    assert scene.mission_is_complete == scene.is_complete
    assert "Mission state: Complete" in renderer.text


def test_toggle_starts_off_and_each_successful_interaction_flips_once() -> None:
    renderer = _RecordingRenderer()
    toggle = ClassroomTrailObjectToggle(
        off_color=(220, 50, 50),
        on_color=(50, 180, 50),
    )
    world_object = _trail_object(
        "switch:magic",
        30,
        color=toggle.off_color,
        interacted="Click!",
        toggle=toggle,
    )
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (world_object,),
        mission=MISSION_07,
        interaction_range=60,
    )
    scene.enter()

    scene.render()
    immutable_color = world_object.world_object.color
    assert renderer.rectangles[0][-1] == toggle.off_color
    assert scene.toggle_on_qualified_ids == frozenset()
    assert scene.changed_toggle_qualified_ids == frozenset()
    assert scene.mission_is_complete is False

    renderer.rectangles.clear()
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert renderer.rectangles[0][-1] == toggle.on_color
    assert scene.toggle_on_qualified_ids == frozenset({"switch:magic"})
    assert scene.changed_toggle_qualified_ids == frozenset({"switch:magic"})
    assert scene.visited_qualified_ids == frozenset({"switch:magic"})
    assert scene.mission_is_complete is True

    renderer.rectangles.clear()
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert renderer.rectangles[0][-1] == toggle.off_color
    assert scene.toggle_on_qualified_ids == frozenset()
    assert scene.changed_toggle_qualified_ids == frozenset({"switch:magic"})
    assert scene.visited_qualified_ids == frozenset({"switch:magic"})
    assert world_object.world_object.color == immutable_color
    assert scene.mission_is_complete is True


def test_toggle_completion_excludes_ordinary_objects_and_visit_progress_is_independent() -> None:
    toggle = ClassroomTrailObjectToggle(
        off_color=(220, 50, 50),
        on_color=(50, 180, 50),
    )
    scene = ClassroomTrailScene(
        _RecordingRenderer(),  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (
            _trail_object("alpha:ordinary", 30),
            _trail_object("beta:toggle", 190, color=toggle.off_color, toggle=toggle),
            _trail_object("gamma:ordinary", 350),
        ),
        mission=MISSION_07,
        interaction_range=60,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.mission_is_complete is False
    assert scene.is_complete is False

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.changed_toggle_qualified_ids == frozenset({"beta:toggle"})
    assert scene.mission_is_complete is True
    assert scene.is_complete is False
    assert scene.visited_qualified_ids == frozenset({"alpha:ordinary", "beta:toggle"})


def test_all_toggle_objects_must_change_and_evidence_survives_return_to_off() -> None:
    toggle = ClassroomTrailObjectToggle(
        off_color=(220, 50, 50),
        on_color=(50, 180, 50),
    )
    scene = ClassroomTrailScene(
        _RecordingRenderer(),  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (
            _trail_object("alpha:toggle", 30, color=toggle.off_color, toggle=toggle),
            _trail_object("beta:toggle", 190, color=toggle.off_color, toggle=toggle),
        ),
        mission=MISSION_07,
        interaction_range=60,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.changed_toggle_qualified_ids == frozenset({"alpha:toggle"})
    assert scene.mission_is_complete is False

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.changed_toggle_qualified_ids == frozenset({"alpha:toggle", "beta:toggle"})
    assert scene.toggle_on_qualified_ids == frozenset({"alpha:toggle", "beta:toggle"})
    assert scene.mission_is_complete is True

    scene.update(DirectionalInput(left=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.toggle_on_qualified_ids == frozenset({"beta:toggle"})
    assert scene.changed_toggle_qualified_ids == frozenset({"alpha:toggle", "beta:toggle"})
    assert scene.mission_is_complete is True


def test_toggle_completion_is_incomplete_when_trail_has_no_toggle_objects() -> None:
    scene = ClassroomTrailScene(
        _RecordingRenderer(),  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("ordinary:object", 30),),
        mission=MISSION_07,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)

    assert scene.is_complete is True
    assert scene.mission_is_complete is False
    assert scene.changed_toggle_qualified_ids == frozenset()


def test_conditional_runtime_model_is_strict_and_immutable() -> None:
    conditional = ClassroomTrailNPCConditionalResponse(
        "magic:switch", "The lamp is dark.", "The lamp is glowing!"
    )

    with pytest.raises(FrozenInstanceError):
        conditional.when_on = "Changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="when_off"):
        ClassroomTrailNPCConditionalResponse("magic:switch", " ", "On")
    with pytest.raises(ValueError, match="respond_to_toggle cannot be combined"):
        _trail_npc(
            "magic:guide",
            30,
            greeting="Hello",
            respond_to_toggle=conditional,
        )


def test_conditional_reference_must_resolve_to_same_package_toggle() -> None:
    toggle = ClassroomTrailObjectToggle((220, 50, 50), (50, 180, 50))
    conditional = ClassroomTrailNPCConditionalResponse(
        "other:switch", "The lamp is dark.", "The lamp is glowing!"
    )

    with pytest.raises(ValueError, match="same-package toggle object"):
        ClassroomTrailScene(
            _RecordingRenderer(),  # type: ignore[arg-type]
            Character(name="Player", x=0, y=0, width=20, height=20, color=(1, 2, 3)),
            (_trail_object("magic:switch", 190, color=toggle.off_color, toggle=toggle),),
            (_trail_npc("magic:guide", 30, respond_to_toggle=conditional),),
            mission=MISSION_08,
        )


def test_conditional_npc_displays_current_branch_and_records_monotonic_evidence() -> None:
    renderer = _RecordingRenderer()
    toggle = ClassroomTrailObjectToggle((220, 50, 50), (50, 180, 50))
    conditional = ClassroomTrailNPCConditionalResponse(
        "magic:switch", "The lamp is dark.", "The lamp is glowing!"
    )
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("magic:switch", 190, color=toggle.off_color, toggle=toggle),),
        (_trail_npc("magic:guide", 30, name="Guide", respond_to_toggle=conditional),),
        mission=MISSION_08,
        interaction_range=60,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert "Guide: The lamp is dark." in renderer.text
    assert scene.displayed_conditional_branches == frozenset({("magic:guide", False)})
    assert scene.toggle_on_qualified_ids == frozenset()
    assert scene.visited_qualified_ids == frozenset()
    assert scene.mission_is_complete is False

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.displayed_conditional_branches == frozenset({("magic:guide", False)})

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.toggle_on_qualified_ids == frozenset({"magic:switch"})
    assert scene.visited_qualified_ids == frozenset({"magic:switch"})
    assert scene.displayed_conditional_branches == frozenset({("magic:guide", False)})

    scene.update(DirectionalInput(left=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert "Guide: The lamp is glowing!" in renderer.text
    assert scene.displayed_conditional_branches == frozenset(
        {("magic:guide", False), ("magic:guide", True)}
    )
    assert scene.toggle_on_qualified_ids == frozenset({"magic:switch"})
    assert scene.mission_is_complete is True


def test_conditional_completion_excludes_ordinary_npcs_and_zero_is_incomplete() -> None:
    ordinary_scene = ClassroomTrailScene(
        _RecordingRenderer(),  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(1, 2, 3)),
        (_trail_object("magic:object", 200),),
        (_trail_npc("magic:greeter", 30, greeting="Hello"),),
        mission=MISSION_08,
    )
    ordinary_scene.enter()
    ordinary_scene.update(_NO_MOVEMENT, _INTERACT, 0.0)

    assert ordinary_scene.spoken_npc_ids == frozenset({"magic:greeter"})
    assert ordinary_scene.displayed_conditional_branches == frozenset()
    assert ordinary_scene.mission_is_complete is False


def test_two_toggle_runtime_model_is_strict_and_immutable() -> None:
    conditional = ClassroomTrailNPCTwoToggleResponse(
        ("magic:first", "magic:second"), "Still locked.", "Unlocked!"
    )

    with pytest.raises(FrozenInstanceError):
        conditional.when_all_on = "Changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="exactly two distinct"):
        ClassroomTrailNPCTwoToggleResponse(
            ("magic:first", "magic:first"), "Still locked.", "Unlocked!"
        )
    with pytest.raises(ValueError, match="respond_to_two_toggles cannot be combined"):
        _trail_npc(
            "magic:guide",
            30,
            greeting="Hello",
            respond_to_two_toggles=conditional,
        )


def test_two_toggle_reference_must_resolve_to_same_package_toggles() -> None:
    toggle = ClassroomTrailObjectToggle((220, 50, 50), (50, 180, 50))
    conditional = ClassroomTrailNPCTwoToggleResponse(
        ("magic:first", "other:second"), "Still locked.", "Unlocked!"
    )

    with pytest.raises(ValueError, match="exactly two same-package toggle objects"):
        ClassroomTrailScene(
            _RecordingRenderer(),  # type: ignore[arg-type]
            Character(name="Player", x=0, y=0, width=20, height=20, color=(1, 2, 3)),
            (
                _trail_object("magic:first", 190, color=toggle.off_color, toggle=toggle),
                _trail_object("magic:second", 350, color=toggle.off_color, toggle=toggle),
            ),
            (_trail_npc("magic:guide", 30, respond_to_two_toggles=conditional),),
            mission=MISSION_10,
        )


def test_two_toggle_npc_uses_boolean_and_and_records_separate_monotonic_evidence() -> None:
    renderer = _RecordingRenderer()
    toggle = ClassroomTrailObjectToggle((220, 50, 50), (50, 180, 50))
    conditional = ClassroomTrailNPCTwoToggleResponse(
        ("magic:first", "magic:second"), "Still locked.", "Unlocked!"
    )
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (
            _trail_object(
                "magic:first",
                190,
                color=toggle.off_color,
                toggle=toggle,
                counter=ClassroomTrailObjectCounter(2, "Powered!"),
            ),
            _trail_object("magic:second", 350, color=toggle.off_color, toggle=toggle),
        ),
        (
            _trail_npc(
                "magic:guide",
                30,
                name="Guide",
                respond_to_two_toggles=conditional,
            ),
        ),
        mission=MISSION_10,
        interaction_range=60,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert "Guide: Still locked." in renderer.text
    assert scene.spoken_npc_ids == frozenset({"magic:guide"})
    assert scene.displayed_two_toggle_branches == frozenset({("magic:guide", False)})
    assert scene.displayed_conditional_branches == frozenset()
    assert scene.mission_is_complete is False

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.displayed_two_toggle_branches == frozenset({("magic:guide", False)})

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.update(DirectionalInput(left=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.toggle_on_qualified_ids == frozenset({"magic:first"})
    assert scene.displayed_two_toggle_branches == frozenset({("magic:guide", False)})

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 2.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.toggle_on_qualified_ids == frozenset({"magic:first", "magic:second"})
    visits_before_npc = scene.visited_qualified_ids
    counts_before_npc = dict(scene.counter_counts)
    assert counts_before_npc == {"magic:first": 1}

    scene.update(DirectionalInput(left=True), _NO_INTERACTION, 2.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert "Guide: Unlocked!" in renderer.text
    assert scene.displayed_two_toggle_branches == frozenset(
        {("magic:guide", False), ("magic:guide", True)}
    )
    assert scene.displayed_conditional_branches == frozenset()
    assert scene.toggle_on_qualified_ids == frozenset({"magic:first", "magic:second"})
    assert scene.visited_qualified_ids == visits_before_npc
    assert dict(scene.counter_counts) == counts_before_npc
    assert scene.mission_is_complete is True


def test_two_toggle_completion_excludes_ordinary_npcs_and_zero_is_incomplete() -> None:
    scene = ClassroomTrailScene(
        _RecordingRenderer(),  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(1, 2, 3)),
        (_trail_object("magic:object", 200),),
        (_trail_npc("magic:greeter", 30, greeting="Hello"),),
        mission=MISSION_10,
    )
    scene.enter()
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)

    assert scene.spoken_npc_ids == frozenset({"magic:greeter"})
    assert scene.displayed_two_toggle_branches == frozenset()
    assert scene.mission_is_complete is False


def test_either_toggle_model_is_strict_mutually_exclusive_and_same_package() -> None:
    toggle = ClassroomTrailObjectToggle((220, 50, 50), (50, 180, 50))
    conditional = ClassroomTrailNPCEitherToggleResponse(
        ("magic:first", "magic:second"), "Locked.", "Open!"
    )
    with pytest.raises(FrozenInstanceError):
        conditional.when_either_on = "Changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="exactly two distinct"):
        ClassroomTrailNPCEitherToggleResponse(("magic:first", "magic:first"), "Locked.", "Open!")
    with pytest.raises(ValueError, match="respond_to_either_toggle cannot be combined"):
        _trail_npc("magic:guide", 30, greeting="Hello", respond_to_either_toggle=conditional)
    with pytest.raises(ValueError, match="exactly two same-package toggle objects"):
        ClassroomTrailScene(
            _RecordingRenderer(),  # type: ignore[arg-type]
            Character(name="Player", x=0, y=0, width=20, height=20, color=(1, 2, 3)),
            (
                _trail_object("magic:first", 190, color=toggle.off_color, toggle=toggle),
                _trail_object("magic:second", 350, color=toggle.off_color, toggle=toggle),
            ),
            (
                _trail_npc(
                    "magic:guide",
                    30,
                    respond_to_either_toggle=ClassroomTrailNPCEitherToggleResponse(
                        ("magic:first", "other:second"), "Locked.", "Open!"
                    ),
                ),
            ),
            mission=MISSION_11,
        )


def test_either_toggle_or_truth_cases_are_monotonic_and_complete_mission_11() -> None:
    renderer = _RecordingRenderer()
    toggle = ClassroomTrailObjectToggle((220, 50, 50), (50, 180, 50))
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (
            _trail_object(
                "magic:first",
                190,
                color=toggle.off_color,
                toggle=toggle,
                counter=ClassroomTrailObjectCounter(2, "Powered!"),
            ),
            _trail_object("magic:second", 350, color=toggle.off_color, toggle=toggle),
        ),
        (
            _trail_npc(
                "magic:guide",
                30,
                name="Guide",
                respond_to_either_toggle=ClassroomTrailNPCEitherToggleResponse(
                    ("magic:first", "magic:second"), "Locked.", "Open!"
                ),
            ),
        ),
        mission=MISSION_11,
        interaction_range=60,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)  # both off
    scene.render()
    assert "Guide: Locked." in renderer.text
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)  # idempotent
    assert scene.displayed_either_toggle_cases == frozenset({("magic:guide", False, False)})
    assert not scene.mission_is_complete

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)  # first on
    scene.update(DirectionalInput(left=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)  # first only
    assert ("magic:guide", True, False) in scene.displayed_either_toggle_cases
    assert not scene.mission_is_complete

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)  # first off
    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)  # second on
    visits_before = scene.visited_qualified_ids
    counts_before = dict(scene.counter_counts)
    prior_evidence = scene.displayed_two_toggle_branches
    scene.update(DirectionalInput(left=True), _NO_INTERACTION, 2.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)  # second only
    scene.render()
    assert "Guide: Open!" in renderer.text
    assert ("magic:guide", False, True) in scene.displayed_either_toggle_cases
    assert scene.mission_is_complete
    assert scene.visited_qualified_ids == visits_before
    assert dict(scene.counter_counts) == counts_before
    assert scene.displayed_two_toggle_branches == prior_evidence
    assert scene.displayed_conditional_branches == frozenset()

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)  # both on
    scene.update(DirectionalInput(left=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert ("magic:guide", True, True) in scene.displayed_either_toggle_cases
    assert scene.mission_is_complete


def test_either_toggle_completion_with_zero_qualifying_npcs_is_incomplete() -> None:
    scene = ClassroomTrailScene(
        _RecordingRenderer(),  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(1, 2, 3)),
        (_trail_object("magic:object", 200),),
        (_trail_npc("magic:greeter", 30, greeting="Hello"),),
        mission=MISSION_11,
    )
    scene.enter()
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.displayed_either_toggle_cases == frozenset()
    assert not scene.mission_is_complete


def test_counter_runtime_model_is_bounded_and_immutable() -> None:
    counter = ClassroomTrailObjectCounter(3, "Fully powered!")

    with pytest.raises(FrozenInstanceError):
        counter.goal = 4  # type: ignore[misc]
    for invalid in (True, 1, 6, 2.0):
        with pytest.raises(ValueError, match="goal"):
            ClassroomTrailObjectCounter(invalid, "Ready")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="when_goal_reached"):
        ClassroomTrailObjectCounter(2, " ")


def test_counter_interaction_increments_once_and_combines_with_toggle() -> None:
    renderer = _RecordingRenderer()
    toggle = ClassroomTrailObjectToggle((220, 50, 50), (50, 180, 50))
    counter = ClassroomTrailObjectCounter(2, "Fully powered!")
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (
            _trail_object(
                "power:core",
                30,
                color=toggle.off_color,
                interacted="Pressed.",
                toggle=toggle,
                counter=counter,
            ),
        ),
        mission=MISSION_09,
        interaction_range=60,
    )
    scene.enter()

    assert dict(scene.counter_counts) == {"power:core": 0}
    with pytest.raises(TypeError):
        scene.counter_counts["power:core"] = 9  # type: ignore[index]

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert dict(scene.counter_counts) == {"power:core": 1}
    assert scene.toggle_on_qualified_ids == frozenset({"power:core"})
    assert scene.changed_toggle_qualified_ids == frozenset({"power:core"})
    assert scene.visited_qualified_ids == frozenset({"power:core"})
    assert "Pressed. Count: 1 / 2." in renderer.text
    assert "Fully powered!" not in renderer.text
    assert scene.mission_is_complete is False

    renderer.text.clear()
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert dict(scene.counter_counts) == {"power:core": 2}
    assert scene.toggle_on_qualified_ids == frozenset()
    assert scene.visited_qualified_ids == frozenset({"power:core"})
    assert "Pressed. Count: 2 / 2. Fully powered!" in renderer.text
    assert scene.mission_is_complete is True

    renderer.text.clear()
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert dict(scene.counter_counts) == {"power:core": 3}
    assert scene.toggle_on_qualified_ids == frozenset({"power:core"})
    assert "Pressed. Count: 3 / 2. Fully powered!" in renderer.text
    assert scene.mission_is_complete is True


def test_all_counter_goals_are_required_and_ordinary_objects_are_excluded() -> None:
    scene = ClassroomTrailScene(
        _RecordingRenderer(),  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(1, 2, 3)),
        (
            _trail_object(
                "alpha:counter",
                30,
                counter=ClassroomTrailObjectCounter(2, "Alpha ready"),
            ),
            _trail_object("beta:ordinary", 190),
            _trail_object(
                "gamma:counter",
                350,
                counter=ClassroomTrailObjectCounter(2, "Gamma ready"),
            ),
        ),
        mission=MISSION_09,
        interaction_range=60,
    )
    scene.enter()

    for _ in range(2):
        scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.mission_is_complete is False
    assert scene.is_complete is False

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 2.0)
    for _ in range(2):
        scene.update(_NO_MOVEMENT, _INTERACT, 0.0)

    assert dict(scene.counter_counts) == {"alpha:counter": 2, "gamma:counter": 2}
    assert scene.mission_is_complete is True
    assert scene.is_complete is False
    assert scene.visited_qualified_ids == frozenset({"alpha:counter", "gamma:counter"})


def test_counter_completion_with_zero_counter_objects_is_incomplete() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(1, 2, 3)),
        (_trail_object("plain:object", 30, interacted="Original response"),),
        mission=MISSION_09,
    )
    scene.enter()
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()

    assert scene.counter_counts == {}
    assert "Original response" in renderer.text
    assert scene.is_complete is True
    assert scene.mission_is_complete is False


def test_mission_preserves_npc_conversation_and_counts_only_objects() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("object:lantern", 220),),
        (_trail_npc("guide:npc", 20, name="Guide", conversation=("First", "Second")),),
        interaction_range=60,
        mission=MISSION_01,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert renderer.text[-1] == "Guide: First"
    assert scene.spoken_npc_ids == frozenset({"guide:npc"})
    assert scene.mission_is_complete is False

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.25)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.mission_is_complete is True

    scene.update(DirectionalInput(left=True), _NO_INTERACTION, 1.25)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert renderer.text[-1] == "Guide: Second"
    assert scene.mission_is_complete is True


def test_npc_rule_tracks_greeting_and_first_conversation_response_idempotently() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("object:lantern", 500),),
        (
            _trail_npc("silent:npc", 10, name="Silent"),
            _trail_npc("alpha:npc", 30, name="Alpha", greeting="Hello!"),
            _trail_npc("beta:npc", 220, name="Beta", conversation=("First", "Second")),
        ),
        mission=MISSION_04,
        interaction_range=80,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert scene.target_qualified_id == "alpha:npc"
    assert renderer.text[-1] == "Alpha: Hello!"
    assert scene.spoken_npc_ids == frozenset({"alpha:npc"})
    assert scene.mission_is_complete is False
    assert scene.visited_qualified_ids == frozenset()
    assert scene.is_complete is False

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.spoken_npc_ids == frozenset({"alpha:npc"})

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.1875)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert scene.target_qualified_id == "beta:npc"
    assert renderer.text[-1] == "Beta: First"
    assert scene.spoken_npc_ids == frozenset({"alpha:npc", "beta:npc"})
    assert scene.completed_conversation_npc_ids == frozenset()
    assert scene.mission_is_complete is True
    assert scene.visited_qualified_ids == frozenset()
    assert scene.is_complete is False
    assert "Mission state: Complete" in renderer.text
    assert "Trail complete!" not in renderer.text

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert renderer.text[-1] == "Beta: Second"
    assert scene.spoken_npc_ids == frozenset({"alpha:npc", "beta:npc"})
    assert scene.completed_conversation_npc_ids == frozenset({"beta:npc"})

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert renderer.text[-1] == "Beta: First"
    assert scene.spoken_npc_ids == frozenset({"alpha:npc", "beta:npc"})
    assert scene.completed_conversation_npc_ids == frozenset({"beta:npc"})


def test_npc_rule_is_incomplete_without_interactable_npcs_and_isolated_from_objects() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("object:lantern", 30),),
        (_trail_npc("silent:npc", 10, name="Silent"),),
        mission=MISSION_04,
    )
    scene.enter()

    assert scene.mission_is_complete is False
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()

    assert scene.spoken_npc_ids == frozenset()
    assert scene.visited_qualified_ids == frozenset({"object:lantern"})
    assert scene.is_complete is True
    assert scene.mission_is_complete is False
    assert "Trail complete!" in renderer.text
    assert "Mission state: Incomplete" in renderer.text


@pytest.mark.parametrize(
    "conversation",
    [("First", "Final"), ("First", "Second", "Final")],
)
def test_conversation_rule_completes_on_final_line_and_survives_wrap(
    conversation: tuple[str, ...],
) -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("object:lantern", 500),),
        (
            _trail_npc("silent:npc", 10, name="Silent"),
            _trail_npc("conversation:npc", 30, name="Guide", conversation=conversation),
            _trail_npc("greeting:npc", 500, name="Greeter", greeting="Hello!"),
        ),
        mission=MISSION_05,
        interaction_range=80,
    )
    scene.enter()

    for index, line in enumerate(conversation):
        scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
        scene.render()
        assert renderer.text[-1] == f"Guide: {line}"
        if index < len(conversation) - 1:
            assert scene.completed_conversation_npc_ids == frozenset()
            assert scene.mission_is_complete is False

    completed = frozenset({"conversation:npc"})
    assert scene.completed_conversation_npc_ids == completed
    assert scene.spoken_npc_ids == completed
    assert scene.mission_is_complete is True
    assert scene.visited_qualified_ids == frozenset()
    assert scene.is_complete is False
    assert "Mission state: Complete" in renderer.text
    assert "Trail complete!" not in renderer.text

    restarted_lines: list[str] = []
    for _ in conversation:
        scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
        scene.render()
        restarted_lines.append(renderer.text[-1])
        assert scene.completed_conversation_npc_ids == completed
        assert scene.mission_is_complete is True

    assert restarted_lines == [f"Guide: {line}" for line in conversation]


def test_conversation_rule_excludes_greeting_and_silent_npcs_and_rejects_empty_set() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("object:lantern", 220),),
        (
            _trail_npc("silent:npc", 10, name="Silent"),
            _trail_npc("greeting:npc", 30, name="Greeter", greeting="Hello!"),
        ),
        mission=MISSION_05,
        interaction_range=80,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert scene.target_qualified_id == "greeting:npc"
    assert renderer.text[-1] == "Greeter: Hello!"
    assert scene.spoken_npc_ids == frozenset({"greeting:npc"})
    assert scene.completed_conversation_npc_ids == frozenset()
    assert scene.mission_is_complete is False

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.1875)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.visited_qualified_ids == frozenset({"object:lantern"})
    assert scene.is_complete is True
    assert scene.mission_is_complete is False


def test_nearest_in_range_object_is_targeted() -> None:
    scene = _scene(
        _trail_object("far:object", 80),
        _trail_object("near:object", 30),
    )

    scene.update(_NO_MOVEMENT, _NO_INTERACTION, 0.0)

    assert scene.target_qualified_id == "near:object"


def test_equal_distance_tie_uses_qualified_id() -> None:
    scene = _scene(
        _trail_object("zebra:object", 40),
        _trail_object("alpha:object", 40),
    )

    scene.update(_NO_MOVEMENT, _NO_INTERACTION, 0.0)

    assert scene.target_qualified_id == "alpha:object"


def test_toggle_metadata_does_not_change_target_tie_order() -> None:
    toggle = ClassroomTrailObjectToggle((220, 50, 50), (50, 180, 50))
    scene = _scene(
        _trail_object("zebra:toggle", 40, color=toggle.off_color, toggle=toggle),
        _trail_object("alpha:ordinary", 40),
    )

    scene.update(_NO_MOVEMENT, _NO_INTERACTION, 0.0)

    assert scene.target_qualified_id == "alpha:ordinary"


def test_npcs_are_canonical_and_nearest_greeting_is_displayed() -> None:
    renderer = _RecordingRenderer()
    far = _trail_npc("zebra:npc", 70, name="Zara", greeting="Welcome!")
    near = _trail_npc("alpha:npc", 30, name="Ari", greeting="Hello there!")
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("object:lantern", 250),),
        (far, near),
        mission=MISSION_01,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()

    assert [npc.qualified_id for npc in scene.npcs] == ["alpha:npc", "zebra:npc"]
    assert scene.target_qualified_id == "alpha:npc"
    assert "Ari: Hello there!" in renderer.text
    assert scene.visited_qualified_ids == frozenset()
    assert scene.is_complete is False

    npc_positions = tuple((npc.character.x, npc.character.y) for npc in scene.npcs)
    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 0.25)
    assert tuple((npc.character.x, npc.character.y) for npc in scene.npcs) == npc_positions


def test_conversation_advances_in_authored_order_and_restarts() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("object:lantern", 250),),
        (
            _trail_npc(
                "guide:npc",
                30,
                name="Guide",
                conversation=("First line.", "Second line.", "Third line."),
            ),
        ),
        mission=MISSION_01,
    )
    scene.enter()

    messages: list[str] = []
    for _ in range(4):
        scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
        scene.render()
        messages.append(renderer.text[-1])

    assert messages == [
        "Guide: First line.",
        "Guide: Second line.",
        "Guide: Third line.",
        "Guide: First line.",
    ]
    assert scene.visited_qualified_ids == frozenset()


def test_conversation_position_is_independent_per_npc() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("object:lantern", 500),),
        (
            _trail_npc("alpha:npc", 20, name="Alpha", conversation=("A1", "A2", "A3")),
            _trail_npc("beta:npc", 220, name="Beta", conversation=("B1", "B2")),
        ),
        mission=MISSION_01,
        interaction_range=60,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.25)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert renderer.text[-1] == "Beta: B1"

    scene.update(DirectionalInput(left=True), _NO_INTERACTION, 1.25)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert renderer.text[-1] == "Alpha: A3"


def test_greeting_remains_a_one_line_conversation() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("object:lantern", 250),),
        (_trail_npc("guide:npc", 30, name="Guide", greeting="Welcome!"),),
        mission=MISSION_01,
    )
    scene.enter()

    for _ in range(2):
        scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
        scene.render()
        assert renderer.text[-1] == "Guide: Welcome!"


def test_conversation_npc_and_object_share_existing_targeting_and_state() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("zebra:object", 40, interacted="Object found"),),
        (_trail_npc("alpha:npc", 40, name="Ari", conversation=("Hi", "Again")),),
        mission=MISSION_01,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()

    assert scene.target_qualified_id == "alpha:npc"
    assert renderer.text[-1] == "Ari: Hi"
    assert scene.visited_count == 0
    assert scene.is_complete is False


def test_equal_distance_npc_object_tie_uses_qualified_id() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("zebra:object", 40),),
        (_trail_npc("alpha:npc", 40, name="Ari", greeting="Hi!"),),
        mission=MISSION_01,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()

    assert scene.target_qualified_id == "alpha:npc"
    assert "Ari: Hi!" in renderer.text
    assert scene.visited_count == 0


def test_npc_without_greeting_renders_but_does_not_mask_object_interaction() -> None:
    renderer = _RecordingRenderer()
    silent = _trail_npc("alpha:silent", 10, name="Silent")
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(name="Player", x=0, y=0, width=20, height=20, color=(255, 200, 50)),
        (_trail_object("beta:object", 40, interacted="Object found"),),
        (silent,),
        mission=MISSION_01,
    )
    scene.enter()

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()

    assert scene.target_qualified_id == "beta:object"
    assert scene.visited_qualified_ids == frozenset({"beta:object"})
    assert "Object found" in renderer.text
    assert any(rectangle[0] == silent.character.x for rectangle in renderer.rectangles)


def test_only_in_range_interactions_change_session_state() -> None:
    scene = _scene(_trail_object("far:object", 300), interaction_range=50)

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)

    assert scene.did_interact_this_frame is False
    assert scene.visited_qualified_ids == frozenset()
    assert scene.is_complete is False


def test_visited_identity_is_idempotent_and_all_objects_complete_trail() -> None:
    scene = _scene(
        _trail_object("alpha:object", 30),
        _trail_object("beta:object", 260),
        interaction_range=80,
    )

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.visited_qualified_ids == frozenset({"alpha:object"})
    assert scene.is_complete is False

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.5)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)

    assert scene.visited_qualified_ids == frozenset({"alpha:object", "beta:object"})
    assert scene.is_complete is True


def test_ui_shows_authored_messages_progress_and_completion() -> None:
    renderer = _RecordingRenderer()
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        Character(
            name="Player",
            x=0,
            y=0,
            width=20,
            height=20,
            color=(255, 200, 50),
        ),
        (
            _trail_object(
                "student:lantern",
                30,
                near="The lantern glows.",
                interacted="A crystal spark appears!",
            ),
        ),
        mission=MISSION_01,
    )
    scene.enter()
    scene.update(_NO_MOVEMENT, _NO_INTERACTION, 0.0)
    scene.render()
    assert "Visited 0 / 1" in renderer.text
    assert "The lantern glows." in renderer.text

    renderer.text.clear()
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert "Visited 1 / 1" in renderer.text
    assert "Trail complete!" in renderer.text
    assert "A crystal spark appears!" in renderer.text


def test_v01_rejects_but_v07_trail_accepts_multiple_package_objects(tmp_path: Path) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\nx: 0\ny: 0\ncolor: "gold"\n',
    )
    alpha_root = _write_package(
        tmp_path / "alpha",
        "alpha-package",
        "lantern",
        "world_object",
        (
            'name: "Lantern"\nx: 30\ny: 0\ncolor: "yellow"\n'
            'when_near: "The lantern glows."\n'
            'when_interacted: "A spark appears!"\n'
        ),
    )
    beta_root = _write_package(
        tmp_path / "beta",
        "beta-package",
        "fountain",
        "world_object",
        (
            'name: "Fountain"\nx: 260\ny: 0\ncolor: "blue"\n'
            'when_near: "Water hums."\n'
            'when_interacted: "You found a ripple!"\n'
        ),
    )
    selections = tuple(_selection(root) for root in (player_root, alpha_root, beta_root))

    assert build_package_set_plan(selections).is_planned is False
    trail = build_classroom_trail_plan(
        selections,
        player_qualified_id="player-package:player",
    )

    assert trail.is_planned
    assert trail.plan is not None
    assert trail.plan.contract_version == "0.9"
    assert [item.qualified_id for item in trail.plan.world_objects] == [
        "alpha-package:lantern",
        "beta-package:fountain",
    ]


def test_v07_accepts_multiple_objects_from_one_package(tmp_path: Path) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\n',
    )
    object_root = _write_package(
        tmp_path / "objects",
        "shared-package",
        "lantern",
        "world_object",
        'name: "Lantern"\nx: 30\ny: 0\n',
    )
    manifest = object_root / "manifest.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8")
        + (
            '  - id: "fountain"\n'
            '    type: "world_object"\n'
            '    path: "objects/fountain.yaml"\n'
        ),
        encoding="utf-8",
    )
    (object_root / "objects" / "fountain.yaml").write_text(
        'name: "Fountain"\nx: 260\ny: 0\n',
        encoding="utf-8",
    )
    selections = (_selection(player_root), _selection(object_root))

    assert build_package_set_plan(selections).is_planned is False
    result = build_classroom_trail_plan(
        selections,
        player_qualified_id="player-package:player",
    )

    assert result.plan is not None
    assert [item.qualified_id for item in result.plan.world_objects] == [
        "shared-package:fountain",
        "shared-package:lantern",
    ]


def test_v07_projects_toggle_metadata_losslessly_into_runnable_trail(tmp_path: Path) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\nx: 0\ny: 0\ncolor: "gold"\n',
    )
    switch_root = _write_package(
        tmp_path / "switch",
        "switch-package",
        "magic-switch",
        "world_object",
        (
            'name: "Magic Switch"\nx: 30\ny: 0\n'
            'when_near: "The switch is quiet."\n'
            'when_interacted: "Click!"\n'
            "toggle:\n"
            '  off_color: "red"\n'
            '  on_color: "green"\n'
        ),
    )

    planned = plan_local_classroom_trail(
        (player_root, switch_root),
        player_qualified_id="player-package:player",
    )

    assert planned.is_planned
    assert planned.plan is not None
    assert planned.plan.contract_version == "0.9"
    registration = planned.plan.world_objects[0]
    assert registration.world_object.toggle is not None
    assert registration.world_object.toggle.off_color == "red"
    assert registration.world_object.toggle.on_color == "green"

    renderer = _RecordingRenderer()
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=MISSION_07_ID)
    scene.enter()
    scene.render()
    assert scene.objects[0].toggle == ClassroomTrailObjectToggle(
        off_color=(220, 50, 50),
        on_color=(50, 180, 50),
    )
    assert renderer.rectangles[0][-1] == (220, 50, 50)
    assert "Mission: Flip a Magic Switch" in renderer.text
    assert MISSION_07.instructions in renderer.text

    renderer.rectangles.clear()
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert renderer.rectangles[0][-1] == (50, 180, 50)
    assert "Click!" in renderer.text
    assert scene.visited_qualified_ids == frozenset({"switch-package:magic-switch"})
    assert scene.changed_toggle_qualified_ids == frozenset({"switch-package:magic-switch"})
    assert scene.mission_is_complete is True


def test_v07_projects_conditional_metadata_into_mission_08_runtime(tmp_path: Path) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\nx: 0\ny: 0\ncolor: "gold"\n',
    )
    conditional_root = _write_package(
        tmp_path / "conditional",
        "magic-package",
        "guide",
        "character",
        (
            'name: "Guide"\nx: 30\ny: 0\n'
            "respond_to_toggle:\n"
            '  object_id: "magic-switch"\n'
            '  when_off: "The portal is sleeping."\n'
            '  when_on: "The portal is glowing!"\n'
        ),
    )
    manifest = conditional_root / "manifest.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8")
        + (
            '  - id: "magic-switch"\n'
            '    type: "world_object"\n'
            '    path: "objects/switch.yaml"\n'
        ),
        encoding="utf-8",
    )
    (conditional_root / "objects").mkdir()
    (conditional_root / "objects" / "switch.yaml").write_text(
        (
            'name: "Magic Switch"\nx: 190\ny: 0\n'
            "toggle:\n"
            '  off_color: "red"\n'
            '  on_color: "green"\n'
        ),
        encoding="utf-8",
    )

    planned = plan_local_classroom_trail(
        (player_root, conditional_root),
        player_qualified_id="player-package:player",
    )

    assert planned.is_planned
    assert planned.plan is not None
    assert planned.plan.contract_version == "0.9"
    conditional = planned.plan.npcs[0].character.respond_to_toggle
    assert conditional is not None
    assert conditional.object_id == "magic-switch"
    renderer = _RecordingRenderer()
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=MISSION_08_ID)
    scene.enter()
    scene.render()
    assert scene.mission is MISSION_08
    assert "Mission: Make an If/Else Character" in renderer.text
    assert MISSION_08.instructions in renderer.text

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert "Guide: The portal is sleeping." in renderer.text
    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.update(DirectionalInput(left=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)

    scene.render()
    assert "Guide: The portal is glowing!" in renderer.text
    assert scene.displayed_conditional_branches == frozenset(
        {("magic-package:guide", False), ("magic-package:guide", True)}
    )
    assert scene.toggle_on_qualified_ids == frozenset({"magic-package:magic-switch"})
    assert scene.mission_is_complete is True

    mission_12_renderer = _RecordingRenderer()
    mission_12_scene = create_classroom_trail_scene(
        mission_12_renderer, planned.plan, mission_id=MISSION_12_ID
    )
    mission_12_scene.enter()
    mission_12_scene.render()
    assert mission_12_scene.mission is MISSION_12
    assert "Mission: Turn the Rule Around" in mission_12_renderer.text
    assert MISSION_12.instructions in mission_12_renderer.text

    mission_12_scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    mission_12_scene.render()
    assert "Guide: The portal is sleeping." in mission_12_renderer.text
    mission_12_scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    mission_12_scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    mission_12_scene.update(DirectionalInput(left=True), _NO_INTERACTION, 1.0)
    mission_12_scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    mission_12_scene.render()
    assert "Guide: The portal is glowing!" in mission_12_renderer.text
    assert mission_12_scene.displayed_conditional_branches == frozenset(
        {("magic-package:guide", False), ("magic-package:guide", True)}
    )
    assert mission_12_scene.mission_is_complete is True


def test_v07_projects_counter_metadata_into_mission_09_runtime(tmp_path: Path) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\nx: 0\ny: 0\ncolor: "gold"\n',
    )
    counter_root = _write_package(
        tmp_path / "counter",
        "power-package",
        "core",
        "world_object",
        (
            'name: "Power Core"\nx: 30\ny: 0\nwhen_interacted: "Pressed."\n'
            "toggle:\n"
            '  off_color: "red"\n'
            '  on_color: "green"\n'
            "counter:\n"
            "  goal: 2\n"
            '  when_goal_reached: "Fully powered!"\n'
        ),
    )

    planned = plan_local_classroom_trail(
        (player_root, counter_root),
        player_qualified_id="player-package:player",
    )

    assert planned.is_planned
    assert planned.plan is not None
    assert planned.plan.contract_version == "0.9"
    registration = planned.plan.world_objects[0]
    assert registration.world_object.counter is not None
    assert registration.world_object.counter.goal == 2
    assert registration.world_object.counter.when_goal_reached == "Fully powered!"

    renderer = _RecordingRenderer()
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=MISSION_09_ID)
    scene.enter()
    scene.render()
    assert scene.mission is MISSION_09
    assert "Mission: Power It Up" in renderer.text
    assert MISSION_09.instructions in renderer.text
    assert dict(scene.counter_counts) == {"power-package:core": 0}

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()

    assert dict(scene.counter_counts) == {"power-package:core": 2}
    assert scene.visited_qualified_ids == frozenset({"power-package:core"})
    assert scene.changed_toggle_qualified_ids == frozenset({"power-package:core"})
    assert scene.toggle_on_qualified_ids == frozenset()
    assert "Pressed. Count: 2 / 2. Fully powered!" in renderer.text
    assert scene.mission_is_complete is True


def test_v08_projects_two_toggle_metadata_into_mission_10_runtime(tmp_path: Path) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\nx: 0\ny: 0\ncolor: "gold"\n',
    )
    conditional_root = _write_package(
        tmp_path / "conditional",
        "secret-package",
        "guide",
        "character",
        (
            'name: "Guide"\nx: 30\ny: 0\n'
            "respond_to_two_toggles:\n"
            '  object_ids: ["first", "second"]\n'
            '  when_not_all_on: "The secret is locked."\n'
            '  when_all_on: "The secret is revealed!"\n'
        ),
    )
    manifest = conditional_root / "manifest.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8")
        + (
            '  - id: "first"\n'
            '    type: "world_object"\n'
            '    path: "objects/first.yaml"\n'
            '  - id: "second"\n'
            '    type: "world_object"\n'
            '    path: "objects/second.yaml"\n'
        ),
        encoding="utf-8",
    )
    (conditional_root / "objects").mkdir()
    for object_id, x, off_color, on_color in (
        ("first", 190, "red", "green"),
        ("second", 350, "blue", "yellow"),
    ):
        (conditional_root / "objects" / f"{object_id}.yaml").write_text(
            (
                f'name: "{object_id.title()}"\nx: {x}\ny: 0\n'
                "toggle:\n"
                f'  off_color: "{off_color}"\n'
                f'  on_color: "{on_color}"\n'
            ),
            encoding="utf-8",
        )

    planned = plan_local_classroom_trail(
        (player_root, conditional_root),
        player_qualified_id="player-package:player",
    )

    assert planned.is_planned
    assert planned.plan is not None
    assert planned.plan.contract_version == "0.9"
    conditional = planned.plan.npcs[0].character.respond_to_two_toggles
    assert conditional is not None
    assert conditional.object_ids == ("first", "second")
    assert conditional.when_not_all_on == "The secret is locked."
    assert conditional.when_all_on == "The secret is revealed!"

    renderer = _RecordingRenderer()
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=MISSION_10_ID)
    scene.enter()
    scene.render()
    assert scene.mission is MISSION_10
    assert "Mission: Unlock the Secret" in renderer.text
    assert MISSION_10.instructions in renderer.text

    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.update(DirectionalInput(left=True), _NO_INTERACTION, 2.0)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()

    assert "Guide: The secret is revealed!" in renderer.text
    assert scene.displayed_two_toggle_branches == frozenset(
        {("secret-package:guide", False), ("secret-package:guide", True)}
    )
    assert scene.displayed_conditional_branches == frozenset()
    assert scene.mission_is_complete is True


def test_v09_projects_either_toggle_metadata_into_mission_11_ui(tmp_path: Path) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\nx: 0\ny: 0\ncolor: "gold"\n',
    )
    root = _write_package(
        tmp_path / "either",
        "either-package",
        "guide",
        "character",
        (
            'name: "Guide"\nx: 30\ny: 0\nrespond_to_either_toggle:\n'
            '  object_ids: ["first", "second"]\n'
            '  when_both_off: "Locked."\n  when_either_on: "Open!"\n'
        ),
    )
    manifest = root / "manifest.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8")
        + '  - id: "first"\n    type: "world_object"\n'
        + '    path: "objects/first.yaml"\n  - id: "second"\n'
        + '    type: "world_object"\n    path: "objects/second.yaml"\n',
        encoding="utf-8",
    )
    (root / "objects").mkdir()
    (root / "objects/first.yaml").write_text(
        'name: "First"\nx: 190\ny: 0\ntoggle: {off_color: red, on_color: green}\n', encoding="utf-8"
    )
    (root / "objects/second.yaml").write_text(
        'name: "Second"\nx: 350\ny: 0\ntoggle: {off_color: blue, on_color: yellow}\n',
        encoding="utf-8",
    )

    planned = plan_local_classroom_trail(
        (player_root, root), player_qualified_id="player-package:player"
    )
    assert planned.is_planned and planned.plan is not None
    assert planned.plan.contract_version == "0.9"
    retained = planned.plan.npcs[0].character.respond_to_either_toggle
    assert retained is not None and retained.object_ids == ("first", "second")

    renderer = _RecordingRenderer()
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=MISSION_11_ID)
    scene.enter()
    scene.render()
    assert scene.mission is MISSION_11
    assert "Mission: Either Switch Opens It" in renderer.text
    assert MISSION_11.instructions in renderer.text
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert "Guide: Locked." in renderer.text
    assert scene.displayed_either_toggle_cases == frozenset(
        {("either-package:guide", False, False)}
    )
    assert scene.mission_is_complete is False


def test_multiple_local_exports_feed_one_runnable_trail_plan(tmp_path: Path) -> None:
    roots = (
        _write_package(
            tmp_path / "player",
            "player-package",
            "player",
            "character",
            'name: "Player"\nx: 0\ny: 0\ncolor: "gold"\n',
        ),
        _write_package(
            tmp_path / "alpha",
            "alpha-package",
            "lantern",
            "world_object",
            (
                'name: "Lantern"\nx: 30\ny: 0\ncolor: "yellow"\n'
                'when_near: "The lantern glows."\n'
                'when_interacted: "A spark appears!"\n'
            ),
        ),
        _write_package(
            tmp_path / "beta",
            "beta-package",
            "fountain",
            "world_object",
            'name: "Fountain"\nx: 260\ny: 0\ncolor: "blue"\n',
        ),
    )
    export_root = tmp_path / "exports"
    export_root.mkdir()
    for root in roots:
        loaded = load_explorer_package(root)
        assert loaded.package is not None
        destination = export_root / (f"{loaded.package.metadata.id}-1.0.0.explorer-package.zip")
        assert export_explorer_package(root, destination).is_exported

    planned = plan_local_classroom_trail(
        reversed(roots),
        player_qualified_id="player-package:player",
    )
    assert planned.is_planned
    assert planned.plan is not None
    assert [package.package_id for package in planned.plan.packages] == [
        "alpha-package",
        "beta-package",
        "player-package",
    ]

    scene = create_classroom_trail_scene(_RecordingRenderer(), planned.plan)
    assert scene.player.name == "Player"
    assert scene.mission is MISSION_01
    assert [item.qualified_id for item in scene.objects] == [
        "alpha-package:lantern",
        "beta-package:fountain",
    ]

    mission_02_renderer = _RecordingRenderer()
    mission_02_scene = create_classroom_trail_scene(
        mission_02_renderer,
        planned.plan,
        mission_id=MISSION_02_ID,
    )
    mission_02_scene.enter()
    mission_02_scene.render()

    assert mission_02_scene.mission is MISSION_02
    assert "Mission: Create Your First Object" in mission_02_renderer.text
    assert MISSION_02.instructions in mission_02_renderer.text
    assert [item.qualified_id for item in mission_02_scene.objects] == [
        "alpha-package:lantern",
        "beta-package:fountain",
    ]

    mission_03_renderer = _RecordingRenderer()
    mission_03_scene = create_classroom_trail_scene(
        mission_03_renderer,
        planned.plan,
        mission_id=MISSION_03_ID,
    )
    mission_03_scene.enter()
    mission_03_scene.update(_NO_MOVEMENT, _NO_INTERACTION, 0.0)
    mission_03_scene.render()

    assert mission_03_scene.mission is MISSION_03
    assert "Mission: Make It Respond" in mission_03_renderer.text
    assert MISSION_03.instructions in mission_03_renderer.text
    assert "The lantern glows." in mission_03_renderer.text

    mission_03_renderer.text.clear()
    mission_03_scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    mission_03_scene.render()

    assert "A spark appears!" in mission_03_renderer.text
    assert mission_03_scene.visited_qualified_ids == frozenset({"alpha-package:lantern"})
    assert mission_03_scene.mission_is_complete is False

    mission_04_renderer = _RecordingRenderer()
    mission_04_scene = create_classroom_trail_scene(
        mission_04_renderer,
        planned.plan,
        mission_id=MISSION_04_ID,
    )
    mission_04_scene.enter()
    mission_04_scene.render()

    assert mission_04_scene.mission is MISSION_04
    assert "Mission: Give Your Character a Voice" in mission_04_renderer.text
    assert MISSION_04.instructions in mission_04_renderer.text
    assert "Mission state: Incomplete" in mission_04_renderer.text
    assert mission_04_scene.spoken_npc_ids == frozenset()

    mission_05_renderer = _RecordingRenderer()
    mission_05_scene = create_classroom_trail_scene(
        mission_05_renderer,
        planned.plan,
        mission_id=MISSION_05_ID,
    )
    mission_05_scene.enter()
    mission_05_scene.render()

    assert mission_05_scene.mission is MISSION_05
    assert "Mission: Write a Conversation" in mission_05_renderer.text
    assert MISSION_05.instructions in mission_05_renderer.text
    assert "Mission state: Incomplete" in mission_05_renderer.text
    assert mission_05_scene.completed_conversation_npc_ids == frozenset()

    mission_06_renderer = _RecordingRenderer()
    mission_06_scene = create_classroom_trail_scene(
        mission_06_renderer,
        planned.plan,
        mission_id=MISSION_06_ID,
    )
    mission_06_scene.enter()
    mission_06_scene.render()

    assert mission_06_scene.mission is MISSION_06
    assert "Mission: Build a Curious Collection" in mission_06_renderer.text
    assert MISSION_06.instructions in mission_06_renderer.text
    assert mission_06_scene.mission_is_complete == mission_06_scene.is_complete
    assert [item.qualified_id for item in mission_06_scene.objects] == [
        "alpha-package:lantern",
        "beta-package:fountain",
    ]

    mission_07_renderer = _RecordingRenderer()
    mission_07_scene = create_classroom_trail_scene(
        mission_07_renderer,
        planned.plan,
        mission_id=MISSION_07_ID,
    )
    mission_07_scene.enter()
    mission_07_scene.render()

    assert mission_07_scene.mission is MISSION_07
    assert "Mission: Flip a Magic Switch" in mission_07_renderer.text
    assert MISSION_07.instructions in mission_07_renderer.text
    assert mission_07_scene.mission_is_complete is False
    assert mission_07_scene.changed_toggle_qualified_ids == frozenset()

    with pytest.raises(KeyError, match="unknown canonical course mission ID"):
        create_classroom_trail_scene(
            _RecordingRenderer(),
            planned.plan,
            mission_id="unknown-mission",
        )


def test_trail_requires_explicit_player_selection(tmp_path: Path) -> None:
    first = _write_package(
        tmp_path / "first",
        "first-player",
        "player",
        "character",
        'name: "First"\ngreeting: "  Welcome, explorer!  "\n',
    )
    second = _write_package(
        tmp_path / "second",
        "second-player",
        "player",
        "character",
        'name: "Second"\n',
    )
    third = _write_package(
        tmp_path / "third",
        "alpha-player",
        "player",
        "character",
        'name: "Third"\nconversation: ["Hello!", "Welcome back!"]\n',
    )
    object_root = _write_package(
        tmp_path / "object",
        "object-package",
        "object",
        "world_object",
        'name: "Object"\nx: 10\ny: 10\n',
    )

    selections = (
        _selection(first),
        _selection(second),
        _selection(third),
        _selection(object_root),
    )
    missing = build_classroom_trail_plan(selections)
    unknown = build_classroom_trail_plan(
        selections,
        player_qualified_id="missing:player",
    )
    object_selected = build_classroom_trail_plan(
        selections,
        player_qualified_id="object-package:object",
    )
    selected = build_classroom_trail_plan(
        selections,
        player_qualified_id="second-player:player",
    )

    assert missing.plan is None
    assert [issue.code for issue in missing.issues] == [
        ClassroomTrailPlanIssueCode.PLAYER_SELECTION_REQUIRED
    ]
    assert unknown.plan is None
    assert unknown.issues[0].code is ClassroomTrailPlanIssueCode.PLAYER_SELECTION_NOT_FOUND
    assert object_selected.plan is None
    assert object_selected.issues[0].code is ClassroomTrailPlanIssueCode.PLAYER_SELECTION_NOT_FOUND
    assert selected.plan is not None
    assert selected.plan.player.qualified_id == "second-player:player"
    assert [npc.qualified_id for npc in selected.plan.npcs] == [
        "alpha-player:player",
        "first-player:player",
    ]
    assert [npc.character.greeting for npc in selected.plan.npcs] == [
        None,
        "Welcome, explorer!",
    ]
    assert [npc.character.conversation for npc in selected.plan.npcs] == [
        ("Hello!", "Welcome back!"),
        None,
    ]
    scene = create_classroom_trail_scene(_RecordingRenderer(), selected.plan)
    assert scene.player.name == "Second"
    assert [npc.character.name for npc in scene.npcs] == ["Third", "First"]
    assert [npc.conversation_lines for npc in scene.npcs] == [
        ("Hello!", "Welcome back!"),
        ("Welcome, explorer!",),
    ]


@pytest.mark.parametrize(
    "mission_id",
    [
        MISSION_02_ID,
        MISSION_03_ID,
        MISSION_04_ID,
        MISSION_05_ID,
        MISSION_06_ID,
        MISSION_07_ID,
        MISSION_08_ID,
        MISSION_09_ID,
        MISSION_10_ID,
        MISSION_11_ID,
        MISSION_12_ID,
    ],
)
def test_cli_runs_planned_local_trail_with_explicit_mission_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mission_id: str,
) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\n',
    )
    object_root = _write_package(
        tmp_path / "object",
        "object-package",
        "object",
        "world_object",
        'name: "Object"\nx: 10\ny: 10\n',
    )
    calls: list[tuple[str, str, int]] = []

    from explore.packages import cli

    def record_run(plan: ClassroomTrailPlan, *, name: str, mission_id: str) -> None:
        calls.append((name, mission_id, len(plan.world_objects)))

    monkeypatch.setattr(cli, "run_classroom_trail", record_run)

    assert (
        cli.main(
            [
                "trail",
                str(object_root),
                str(player_root),
                "--player",
                "player-package:player",
                "--name",
                "Room 12 Trail",
                "--mission-id",
                mission_id,
            ]
        )
        == 0
    )
    assert calls == [("Room 12 Trail", mission_id, 1)]


def test_runtime_rejects_changed_contract_version(tmp_path: Path) -> None:
    player_root = _write_package(
        tmp_path / "player",
        "player-package",
        "player",
        "character",
        'name: "Player"\n',
    )
    object_root = _write_package(
        tmp_path / "object",
        "object-package",
        "object",
        "world_object",
        'name: "Object"\nx: 10\ny: 10\n',
    )
    result = plan_local_classroom_trail(
        (player_root, object_root),
        player_qualified_id="player-package:player",
    )
    assert result.plan is not None

    changed = replace(result.plan, contract_version="9.9")

    with pytest.raises(ValueError, match="contract_version"):
        create_classroom_trail_scene(_RecordingRenderer(), changed)
