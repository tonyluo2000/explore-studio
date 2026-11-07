"""S07 presentation observes repeated toggles; completion remains first-change only."""

from pathlib import Path

import pytest
import yaml

from engine.rendering._classroom_sprites import SKY_LANTERN_PRESENTATION_ID
from engine.rendering._mission_presentation import (
    S07_MISSION_ID,
    S07_PACKAGE_ID,
    S07_SKY_LANTERN_QUALIFIED_ID,
    mission_presentation,
)
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
PACKAGES = (
    ROOT / "examples/explorer-packages/nova-character",
    ROOT / "lessons/sessions/s07/student/explorer-package",
)
OBJECT = S07_SKY_LANTERN_QUALIFIED_ID


def test_s07_scope_and_alias():
    assert mission_presentation(S07_MISSION_ID) is None
    assert mission_presentation(S07_MISSION_ID, package_ids=("other",)) is None
    policy = mission_presentation(S07_MISSION_ID, package_ids=(S07_PACKAGE_ID,))
    assert policy and policy.celebration and policy.meadow_audio and policy.object_feedback_focus
    assert policy.sprite_aliases == {OBJECT: SKY_LANTERN_PRESENTATION_ID}
    assert not policy.talk_cue and not policy.dialogue_focus and not policy.lantern_waypoint
    # Rendering cannot silently migrate a later toggle-style lesson.
    for session in ("s08", "s14", "s23", "s28"):
        packages, options = CANONICAL[session]
        ids = tuple(
            yaml.safe_load((_package_root(p) / "manifest.yaml").read_text())["package"]["id"]
            for p in packages
        )
        assert mission_presentation(options["--mission-id"], package_ids=ids) is None


def test_authored_identity_messages_and_no_future_mechanic():
    plan = plan_local_classroom_trail(PACKAGES, player_qualified_id="nova-character:nova").plan
    assert plan
    scene = create_classroom_trail_scene(AccentCheckingRenderer(), plan, mission_id=S07_MISSION_ID)
    scene.enter()
    assert scene._presentation.active
    assert (scene.player.x, scene.player.y) == (240, 300)
    assert scene.npcs == () and len(scene.objects) == 1
    item = scene.objects[0]
    assert item.qualified_id == OBJECT and item.counter is None
    assert (item.world_object.name, item.world_object.x, item.world_object.y) == (
        "Sky Lantern",
        360,
        300,
    )
    assert item.toggle.off_color == resolve_color("blue")
    assert item.toggle.on_color == resolve_color("gold")
    assert item.when_near == "The lantern waits for a spark — one flame could reach the gate above."
    assert item.when_interacted == "Click! The lantern changes."
    assert not scene.toggle_on_qualified_ids and not scene.changed_toggle_qualified_ids
    assert scene._presentation.pose_for(OBJECT).row == "off"


def test_repeated_toggle_after_completion_and_distinct_pixels():
    import pygame

    trail = Trail(PACKAGES, mission_id=S07_MISSION_ID)
    try:
        trail.walk_to(290, 300)
        trail.hold(0.4)
        assert trail.scene.target_qualified_id == OBJECT
        assert "Inspect Sky Lantern" in trail.renderer.texts
        assert trail.scene.objects[0].when_near in trail.renderer.texts
        assert not trail.scene.mission_is_complete
        # The lantern crop changes in shape/intensity, as well as hue.
        off = pygame.image.tobytes(trail.surface().subsurface((340, 275, 100, 110)), "RGB")
        for count, on in enumerate((True, False, True), 1):
            trail.press()
            trail.hold(0.35)
            assert (OBJECT in trail.scene.toggle_on_qualified_ids) is on
            assert trail.scene._presentation.pose_for(OBJECT).row == ("on" if on else "off")
            assert trail.scene.changed_toggle_qualified_ids == frozenset({OBJECT})
            assert trail.scene.mission_is_complete
            assert "Mission state: Complete" in trail.renderer.texts
            assert trail.scene.feedback_message == "Click! The lantern changes."
            if count == 1:
                lit = pygame.image.tobytes(trail.surface().subsurface((340, 275, 100, 110)), "RGB")
                assert lit != off
                celebration = trail.scene._presentation.celebration_start
            else:
                assert trail.scene._presentation.celebration_start == celebration
    finally:
        trail.close()


@pytest.mark.parametrize("colors", [("blue", "gold"), ("pink", "green")])
def test_authored_colors_drive_both_visual_states(colors):
    from engine.animation import SpritePose
    from engine.rendering._classroom_sprites import classroom_sprite_pose, draw_classroom_sprite

    # The shared lantern primitive accepts both authored colors without the
    # accent restriction of the fixed-gold Crystal Lantern sprite sheet.
    frames = []
    for state, color in zip(("off", "on"), colors, strict=True):
        renderer = AccentCheckingRenderer()
        with classroom_sprite_pose(SpritePose(row=state)):
            assert draw_classroom_sprite(
                renderer, SKY_LANTERN_PRESENTATION_ID, 360, 300, 64, 64, resolve_color(color)
            )
        assert any(resolve_color(color) in values for _, values in renderer.operations)
        frames.append(renderer.operations)
    assert frames[0] != frames[1]
