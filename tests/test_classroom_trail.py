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
    ClassroomTrailObject,
    ClassroomTrailScene,
)
from explore.curriculum import MISSION_01, MISSION_02, MISSION_02_ID
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
    near: str | None = None,
    interacted: str | None = None,
) -> ClassroomTrailObject:
    return ClassroomTrailObject(
        qualified_id,
        WorldObject(
            name=qualified_id,
            x=x,
            y=0,
            width=20,
            height=20,
            color=(0, 255, 0),
        ),
        near,
        interacted,
    )


def _trail_npc(
    qualified_id: str,
    x: int,
    *,
    name: str | None = None,
    greeting: str | None = None,
    conversation: tuple[str, ...] | None = None,
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


def test_local_mission_is_immutable_and_supports_exactly_one_rule() -> None:
    mission = ClassroomTrailMission(
        "visit-all-classroom-objects",
        "Explore Every Object",
        "Interact with every classroom object.",
    )

    assert tuple(ClassroomTrailMissionCompletionRule) == (
        ClassroomTrailMissionCompletionRule.ALL_OBJECTS_VISITED,
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
    assert scene.mission_is_complete is False

    scene.update(DirectionalInput(right=True), _NO_INTERACTION, 1.25)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    assert scene.mission_is_complete is True

    scene.update(DirectionalInput(left=True), _NO_INTERACTION, 1.25)
    scene.update(_NO_MOVEMENT, _INTERACT, 0.0)
    scene.render()
    assert renderer.text[-1] == "Guide: Second"
    assert scene.mission_is_complete is True


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


def test_v01_rejects_but_v04_trail_accepts_multiple_package_objects(tmp_path: Path) -> None:
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
    assert trail.plan.contract_version == "0.4"
    assert [item.qualified_id for item in trail.plan.world_objects] == [
        "alpha-package:lantern",
        "beta-package:fountain",
    ]


def test_v04_accepts_multiple_objects_from_one_package(tmp_path: Path) -> None:
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
            'name: "Lantern"\nx: 30\ny: 0\ncolor: "yellow"\n',
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


def test_cli_runs_planned_local_trail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
                MISSION_02_ID,
            ]
        )
        == 0
    )
    assert calls == [("Room 12 Trail", MISSION_02_ID, 1)]


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
