"""S06 continues the Moon Meadow without changing M06 gameplay semantics."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from engine.rendering._classroom_environment import MEADOW_BACKDROP
from engine.rendering._classroom_sprites import (
    PRESENTATION_PRIMITIVE_IDS,
    RAIN_BELL_PRESENTATION_ID,
    SUN_SEED_PRESENTATION_ID,
    WIND_FLOWER_PRESENTATION_ID,
)
from engine.rendering._mission_presentation import (
    S06_MISSION_ID,
    S06_PACKAGE_ID,
    S06_RAIN_BELL_QUALIFIED_ID,
    S06_SUN_SEED_QUALIFIED_ID,
    S06_WIND_FLOWER_QUALIFIED_ID,
    mission_presentation,
)
from engine.rendering._trail_presentation import TrailPresentation
from explore._colors import resolve_color
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from scripts.trail_driver import Trail
from tests.test_mission_presentation_contract import (
    CANONICAL,
    AccentCheckingRenderer,
    _package_root,
)

ROOT = Path(__file__).resolve().parents[1]
NOVA_PACKAGE = ROOT / "examples/explorer-packages/nova-character"
S06_PACKAGE = ROOT / "lessons/sessions/s06/student/explorer-package"
S06_OBJECT_IDS = (
    S06_SUN_SEED_QUALIFIED_ID,
    S06_RAIN_BELL_QUALIFIED_ID,
    S06_WIND_FLOWER_QUALIFIED_ID,
)
LATER_M06_SESSIONS = ("s16", "s17", "s21", "s27")


def _records() -> dict[str, dict[str, object]]:
    records = {}
    for path in sorted((S06_PACKAGE / "objects").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        records[path.stem] = data
    return records


def _planned_s06():  # type: ignore[no-untyped-def]
    planned = plan_local_classroom_trail(
        (NOVA_PACKAGE, S06_PACKAGE), player_qualified_id="nova-character:nova"
    )
    assert planned.is_planned and planned.plan is not None, planned.issues
    return planned.plan


def test_s06_policy_is_exactly_package_scoped() -> None:
    assert mission_presentation(S06_MISSION_ID) is None
    policy = mission_presentation(S06_MISSION_ID, package_ids=("nova-character", S06_PACKAGE_ID))
    assert policy is not None
    assert policy.celebration and policy.meadow_audio
    assert not policy.lantern_waypoint
    assert not policy.talk_cue and not policy.dialogue_focus
    assert policy.player_start == (80, 180)
    assert policy.sprite_aliases == {
        S06_SUN_SEED_QUALIFIED_ID: SUN_SEED_PRESENTATION_ID,
        S06_RAIN_BELL_QUALIFIED_ID: RAIN_BELL_PRESENTATION_ID,
        S06_WIND_FLOWER_QUALIFIED_ID: WIND_FLOWER_PRESENTATION_ID,
    }


@pytest.mark.parametrize("session", LATER_M06_SESSIONS)
def test_later_m06_reuse_stays_standard(session: str) -> None:
    packages, options = CANONICAL[session]
    roots = tuple(_package_root(argument) for argument in packages)
    planned = plan_local_classroom_trail(roots, player_qualified_id=options["--player"])
    assert planned.is_planned and planned.plan is not None
    package_ids = tuple(package.package_id for package in planned.plan.packages)
    assert S06_PACKAGE_ID not in package_ids
    assert mission_presentation(S06_MISSION_ID, package_ids=package_ids) is None
    scene = create_classroom_trail_scene(
        AccentCheckingRenderer(), planned.plan, mission_id=S06_MISSION_ID
    )
    assert not scene._presentation.active


def test_s06_scene_preserves_authored_objects_and_uses_distinct_primitives() -> None:
    plan = _planned_s06()
    renderer = AccentCheckingRenderer()
    scene = create_classroom_trail_scene(renderer, plan, mission_id=S06_MISSION_ID)
    scene.enter()
    scene.render()

    assert scene._presentation.active
    assert (scene.player.x, scene.player.y) == (80, 180)
    assert scene.npcs == ()
    assert len(scene.objects) == 3
    records = _records()
    aliases = []
    for item in scene.objects:
        object_id = item.qualified_id.partition(":")[2]
        record = records[object_id]
        world_object = item.world_object
        assert (world_object.name, world_object.x, world_object.y, world_object.color) == (
            record["name"],
            record["x"],
            record["y"],
            resolve_color(record["color"]),
        )
        assert item.when_near == record["when_near"]
        assert item.when_interacted == record["when_interacted"]
        alias = scene._presentation.sprite_identity(item.qualified_id)
        aliases.append(alias)
        assert alias in PRESENTATION_PRIMITIVE_IDS
        assert scene._presentation.pose_for(item.qualified_id) is not None
        full_box = (
            world_object.x,
            world_object.y,
            world_object.width,
            world_object.height,
            world_object.color,
        )
        assert ("rect", full_box) not in renderer.operations
    assert len(set(aliases)) == 3

    sprites = [values for kind, values in renderer.operations if kind == "sprite"]
    assert sprites and sprites[0][:3] == MEADOW_BACKDROP


def test_s06_truthful_progress_and_package_authored_feedback() -> None:
    records = _records()
    trail = Trail((NOVA_PACKAGE, S06_PACKAGE), mission_id=S06_MISSION_ID)
    try:
        assert trail.scene.npcs == ()
        assert trail.scene.visited_qualified_ids == frozenset()
        assert not trail.scene.mission_is_complete
        trail.step()
        assert trail.scene.target_qualified_id == S06_SUN_SEED_QUALIFIED_ID
        assert "Inspect Sun Seed" in trail.renderer.texts
        assert "Visited 0 / 3" in trail.renderer.texts
        assert "Mission state: Incomplete" in trail.renderer.texts

        route = ("sun-seed", "rain-bell", "wind-flower")
        for index, object_id in enumerate(route, start=1):
            record = records[object_id]
            trail.walk_to(int(record["x"]), int(record["y"]))
            # Let the previous interaction response finish before checking the
            # next package-authored near response.
            trail.hold(3.2 if index > 1 else 0.1)
            assert f"Inspect {record['name']}" in trail.renderer.texts
            assert record["when_near"] in trail.renderer.texts
            trail.press()
            assert trail.scene.feedback_message == record["when_interacted"]
            assert len(trail.scene.visited_qualified_ids) == index
            assert trail.scene.mission_is_complete is (index == 3)
            assert f"Visited {index} / 3" in trail.renderer.texts
            expected_state = "Complete" if index == 3 else "Incomplete"
            assert f"Mission state: {expected_state}" in trail.renderer.texts
            assert ("Trail complete!" in trail.renderer.texts) is (index == 3)

        assert trail.scene.visited_qualified_ids == frozenset(S06_OBJECT_IDS)
        assert (
            trail.scene.feedback_message
            == "The flower whispers a map of the wind — it points toward a gate hidden in the sky."
        )
    finally:
        trail.close()


def test_s06_feedback_falls_back_when_focused_card_cannot_draw() -> None:
    message = "Package-authored feedback stays visible."
    presentation = TrailPresentation(S06_MISSION_ID, package_ids=(S06_PACKAGE_ID,))

    class ReducedRenderer:
        pass

    reduced = ReducedRenderer()
    assert presentation.fit_feedback(reduced, message) == message

    class FailingCardRenderer:
        @staticmethod
        def measure_text(text: str, size: int) -> tuple[int, int]:
            return len(text) * max(1, size // 2), size

        @staticmethod
        def draw_translucent_panel(*_args: object, **_kwargs: object) -> None:
            raise RuntimeError("renderer cannot draw the focused card")

    failing = FailingCardRenderer()
    view = SimpleNamespace(feedback_message=message)
    presentation._guard("object-feedback", presentation._draw_object_feedback, failing, view)
    assert presentation.fit_feedback(failing, message) == message


def test_s06_contains_no_lantern_or_s07_state_mechanic() -> None:
    scene = create_classroom_trail_scene(
        AccentCheckingRenderer(), _planned_s06(), mission_id=S06_MISSION_ID
    )
    assert scene.npcs == ()
    assert {item.qualified_id for item in scene.objects} == set(S06_OBJECT_IDS)
    assert all(item.toggle is None and item.counter is None for item in scene.objects)
    assert all("lantern" not in item.qualified_id for item in scene.objects)
    assert all("gate" not in item.qualified_id for item in scene.objects)
