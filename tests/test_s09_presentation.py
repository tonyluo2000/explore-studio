"""S09 charge art observes authored counters without changing M09 gameplay."""

import shutil
from pathlib import Path

import pytest
import yaml

from engine.rendering._classroom_sprites import STORM_ENGINE_PRESENTATION_ID
from engine.rendering._mission_presentation import mission_presentation
from explore._colors import resolve_color
from scripts.trail_driver import Trail

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "lessons/sessions/s09/student/explorer-package"
DEVICE = "storm-engine:storm-engine"
MISSION = "count-object-interactions"


def test_only_s09_package_opts_into_the_reused_mission():
    assert mission_presentation(MISSION) is None
    policy = mission_presentation(MISSION, package_ids=("storm-engine",))
    assert policy and policy.celebration and policy.meadow_audio and policy.object_feedback_focus
    assert policy.sprite_aliases == {DEVICE: STORM_ENGINE_PRESENTATION_ID}
    assert not policy.talk_cue and not policy.dialogue_focus
    for sid in ("s10", "s13", "s18"):
        root = ROOT / f"lessons/sessions/{sid}/student/explorer-package"
        identity = yaml.safe_load((root / "manifest.yaml").read_text())["package"]["id"]
        assert mission_presentation(MISSION, package_ids=(identity,)) is None


@pytest.mark.parametrize("goal,color", [(2, "green"), (3, "purple"), (4, "pink"), (5, "gold")])
def test_authored_goal_text_color_and_position_drive_each_charge(tmp_path, goal, color):
    import pygame

    package = tmp_path / "package"
    shutil.copytree(PACKAGE, package)
    path = package / "objects/storm-engine.yaml"
    data = yaml.safe_load(path.read_text())
    data.update(
        color=color,
        x=430,
        y=305,
        when_near="Listen for my authored hum.",
        when_interacted="My own spark message.",
    )
    data["counter"].update(goal=goal, when_goal_reached="My own fully powered message!")
    path.write_text(yaml.safe_dump(data))
    trail = Trail((ROOT / "examples/explorer-packages/nova-character", package), mission_id=MISSION)
    try:
        trail.walk_to(360, 305)
        trail.hold(0.4)
        scene = trail.scene
        assert scene._presentation.active and not scene.npcs
        item = scene.objects[0]
        assert (item.world_object.x, item.world_object.y) == (430, 305)
        assert item.world_object.color == resolve_color(color)
        assert item.counter.goal == goal
        assert item.when_near in trail.renderer.texts
        assert dict(scene.counter_counts) == {DEVICE: 0}
        frames = []
        celebration = None
        for count in range(goal + 2):
            if count:
                trail.press()
                trail.hold(0.35)
            assert scene.counter_counts[DEVICE] == count
            assert scene.mission_is_complete is (count >= goal)
            pose = scene._presentation.pose_for(DEVICE)
            assert (pose.row, pose.column) == (f"cells-{goal}", f"lit-{min(count, goal)}")
            frames.append(
                pygame.image.tobytes(trail.surface().subsurface((430, 305, 80, 80)), "RGB")
            )
            if count:
                assert item.when_interacted in scene.feedback_message
                assert (item.counter.when_goal_reached in scene.feedback_message) is (count >= goal)
            if count == goal:
                celebration = scene._presentation.celebration_start
                assert celebration is not None
            if count > goal:
                assert scene._presentation.celebration_start == celebration
            assert scene.displayed_counter_comparison_branches == frozenset()
        assert len(set(frames[: goal + 1])) == goal + 1
        assert item.world_object.color == resolve_color(color)
        assert (item.world_object.x, item.world_object.y) == (430, 305)
    finally:
        trail.close()
