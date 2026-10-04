"""S03 (M03) gets the polished Moon Meadow without any change to its gameplay.

These tests pin the explicit mission presentation policy, the canonical S03
Compass's routing onto the trusted Moon Compass art, the absence of M02-only
story beats, and that the authored ``when_near``/``when_interacted`` text,
visited count, and completion behave exactly as without presentation.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

import engine.rendering._trail_presentation as presentation_module
from engine.input import DirectionalInput, InteractionInput
from engine.rendering._classroom_environment import (
    MEADOW_BACKDROP,
    MEADOW_FOREGROUND,
    draw_classroom_backdrop,
)
from engine.rendering._classroom_sprites import (
    COMPASS_HALO_SHEET_ID,
    COMPASS_NEEDLE_SHEET_ID,
    COMPASS_SHEET_ID,
    MOON_COMPASS_QUALIFIED_ID,
    NOVA_QUALIFIED_ID,
)
from engine.rendering._mission_presentation import (
    MISSION_PRESENTATIONS,
    S02_MISSION_ID,
    S03_MISSION_ID,
    S03_MOON_COMPASS_QUALIFIED_ID,
    mission_presentation,
)
from engine.rendering._trail_presentation import TrailPresentation
from explore import curriculum
from explore.curriculum import MISSION_02_ID, MISSION_03_ID
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from tests.test_s02_art_pass import ArtRenderer

REPO = Path(__file__).resolve().parents[1]
S03_PACKAGE = REPO / "lessons/sessions/s03/student/explorer-package"
#: Exactly the packages of the canonical S03 ``explore-package trail`` command.
S03_PACKAGES = (REPO / "examples/explorer-packages/nova-character", S03_PACKAGE)
S03_COMPASS = yaml.safe_load((S03_PACKAGE / "objects/compass.yaml").read_text())
STEP = 1 / 60
STILL = DirectionalInput()
NO_E = InteractionInput()
PRESS_E = InteractionInput(interact_pressed=True)
PURPLE = (140, 50, 180)
_FEEDBACK_AT = (360, 560)


def _scene(renderer: object, *, mission_id: str = MISSION_03_ID, package_roots=S03_PACKAGES):  # type: ignore[no-untyped-def]
    planned = plan_local_classroom_trail(package_roots, player_qualified_id=NOVA_QUALIFIED_ID)
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=mission_id)
    scene.enter()
    return scene


def _frame(scene, renderer: ArtRenderer, directions=STILL, interact=NO_E) -> None:  # type: ignore[no-untyped-def]
    scene.update(directions, interact, STEP)
    renderer.operations.clear()
    scene.render()


def _walk_to_compass(scene, renderer: ArtRenderer) -> None:  # type: ignore[no-untyped-def]
    player = scene.player
    for _ in range(600):
        dx, dy = 250 - player.x_float, 230 - player.y_float
        if abs(dx) < 3 and abs(dy) < 3:
            return
        _frame(
            scene,
            renderer,
            DirectionalInput(left=dx < -2, right=dx > 2, up=dy < -2, down=dy > 2),
        )
    raise AssertionError("Nova never reached the Compass")


def _texts(renderer: ArtRenderer) -> list[tuple[object, ...]]:
    return [values for kind, values in renderer.operations if kind == "text"]


def _text_at(renderer: ArtRenderer, position: tuple[int, int]) -> list[object]:
    return [values[0] for values in _texts(renderer) if tuple(values[1:3]) == position]


# ---------------------------------------------------------------------------
# The explicit mission boundary
# ---------------------------------------------------------------------------


def test_presentation_policy_lists_exactly_m02_and_m03() -> None:
    assert S02_MISSION_ID == MISSION_02_ID
    assert S03_MISSION_ID == MISSION_03_ID
    assert set(MISSION_PRESENTATIONS) == {MISSION_02_ID, MISSION_03_ID}
    m02, m03 = mission_presentation(MISSION_02_ID), mission_presentation(MISSION_03_ID)
    assert m02 is not None and m02.discovery_label and m02.celebration
    assert m02.sprite_aliases == {}
    assert m03 is not None and not m03.discovery_label and not m03.celebration
    assert m03.sprite_aliases == {S03_MOON_COMPASS_QUALIFIED_ID: MOON_COMPASS_QUALIFIED_ID}


def test_every_other_course_mission_keeps_the_plain_trail() -> None:
    others = [
        getattr(curriculum, name)
        for name in dir(curriculum)
        if name.startswith("MISSION_") and name.endswith("_ID")
    ]
    others = [mission_id for mission_id in others if mission_id not in MISSION_PRESENTATIONS]
    assert len(others) == 14
    for mission_id in others:
        assert mission_presentation(mission_id) is None
        presentation = TrailPresentation(mission_id)
        assert not presentation.active
        # The S03 alias never leaks outside M03.
        assert presentation.sprite_identity(S03_MOON_COMPASS_QUALIFIED_ID) == (
            S03_MOON_COMPASS_QUALIFIED_ID
        )
        assert presentation.pose_for(S03_MOON_COMPASS_QUALIFIED_ID) is None
        assert not draw_classroom_backdrop(ArtRenderer(), mission_id)  # type: ignore[arg-type]
    assert mission_presentation(None) is None  # type: ignore[arg-type]


def test_the_s03_compass_identity_comes_from_the_canonical_package() -> None:
    planned = plan_local_classroom_trail(S03_PACKAGES, player_qualified_id=NOVA_QUALIFIED_ID)
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(ArtRenderer(), planned.plan, mission_id=MISSION_03_ID)
    assert [item.qualified_id for item in scene.objects] == [S03_MOON_COMPASS_QUALIFIED_ID]
    assert scene.npcs == ()


# ---------------------------------------------------------------------------
# What S03 now draws
# ---------------------------------------------------------------------------


def test_s03_draws_the_moon_meadow_nova_v3_and_the_trusted_compass() -> None:
    renderer = ArtRenderer()
    scene = _scene(renderer)
    _frame(scene, renderer)
    sprites = [values for kind, values in renderer.operations if kind == "sprite"]
    assets = [values[0] for values in sprites]
    assert sprites[0] == (*MEADOW_BACKDROP, 0, 0, 960, 640, {})
    assert "characters/nova" in assets
    assert MEADOW_FOREGROUND[0] in assets
    layers = [(values[0], values[1]) for values in sprites if "compass" in str(values[0])]
    assert layers == [
        (COMPASS_HALO_SHEET_ID, "halo"),
        (COMPASS_SHEET_ID, "ring"),
        (COMPASS_SHEET_ID, "body"),
        (COMPASS_NEEDLE_SHEET_ID, "needle"),
        (COMPASS_SHEET_ID, "glass"),
    ]
    compass = scene.objects[0].world_object
    ring = next(values for values in sprites if values[0] == COMPASS_SHEET_ID)
    assert ring[3] == compass.x == S03_COMPASS["x"]
    assert compass.y <= ring[4] <= compass.y + 2  # the same gentle hover as S02
    assert ring[5:7] == (compass.width, compass.height)
    assert ring[-1] == {"tint": compass.color}
    # No purple-rectangle fallback at the Compass's box.
    box = (compass.x, compass.y, compass.width, compass.height, compass.color)
    assert ("rect", box) not in renderer.operations
    # Shared ambience and the HUD panel; no Pixel or Lantern is injected.
    assert {"glow", "shadow", "translucent"} <= set(renderer.kinds())
    assert not {"characters/pixel", "objects/crystal-lantern"} & set(assets)


def test_s03_compass_art_translates_with_student_coordinates(tmp_path: Path) -> None:
    moved = tmp_path / "explorer-package"
    shutil.copytree(S03_PACKAGE, moved)
    authored = dict(S03_COMPASS, x=600, y=420)
    (moved / "objects/compass.yaml").write_text(yaml.safe_dump(authored, sort_keys=False))
    here, there = ArtRenderer(), ArtRenderer()
    scenes = (_scene(here), _scene(there, package_roots=(S03_PACKAGES[0], moved)))
    for scene, renderer in zip(scenes, (here, there), strict=True):
        _frame(scene, renderer)
    before, after = (
        [
            values
            for kind, values in renderer.operations
            if kind == "sprite" and "compass" in str(values[0])
        ]
        for renderer in (here, there)
    )
    assert len(before) == len(after) == 5  # halo, ring, body, needle, glass
    for first, second in zip(before, after, strict=True):
        assert second[:3] == first[:3]
        assert second[3:5] == (first[3] + 360, first[4] + 240)


def test_s03_compass_keeps_a_procedural_drawing_without_trusted_art() -> None:
    renderer = ArtRenderer(trusted_art=False)
    scene = _scene(renderer)
    _frame(scene, renderer)
    compass = scene.objects[0].world_object
    box = (compass.x, compass.y, compass.width, compass.height, compass.color)
    assert ("rect", box) not in renderer.operations
    assert "sprite" not in renderer.kinds()


# ---------------------------------------------------------------------------
# Authored responses and mission behavior are unchanged
# ---------------------------------------------------------------------------


def test_s03_near_clue_then_reveal_then_completion() -> None:
    renderer = ArtRenderer()
    scene = _scene(renderer)
    _frame(scene, renderer)
    assert "Visited 0 / 1" in [values[0] for values in _texts(renderer)]
    assert _text_at(renderer, _FEEDBACK_AT) == []

    _walk_to_compass(scene, renderer)
    _frame(scene, renderer)
    assert scene.visited_count == 0 and not scene.mission_is_complete
    assert _text_at(renderer, _FEEDBACK_AT) == [S03_COMPASS["when_near"]]
    assert "E" in [values[0] for values in _texts(renderer)]  # the shared prompt
    assert "Inspect Moon Compass" in [values[0] for values in _texts(renderer)]

    _frame(scene, renderer, interact=PRESS_E)
    texts = [values[0] for values in _texts(renderer)]
    assert _text_at(renderer, _FEEDBACK_AT) == [S03_COMPASS["when_interacted"]]
    assert scene.visited_count == 1 and scene.mission_is_complete
    assert "Visited 1 / 1" in texts and "Mission state: Complete" in texts

    # No M02-only story beats: no discovery label, confetti, or banner.
    seen: set[object] = set()
    for _ in range(round(1.5 / STEP)):
        _frame(scene, renderer)
        seen.update(values[0] for values in _texts(renderer))
    assert not any("discovered!" in str(text) for text in seen)
    assert "Mission complete!" not in seen
    assert scene._presentation.celebration_start is None
    assert scene._presentation.label is None


def _gameplay_trace(monkeypatch: pytest.MonkeyPatch, *, presented: bool) -> list[object]:
    if not presented:
        monkeypatch.setattr(presentation_module, "mission_presentation", lambda _id: None)
    renderer = ArtRenderer()
    scene = _scene(renderer)
    assert scene._presentation.active is presented
    script = (
        [DirectionalInput(left=True)] * 40
        + [DirectionalInput(up=True)] * 50
        + [DirectionalInput(left=True, up=True)] * 30
        + [STILL] * 10
    )
    trace: list[object] = []
    for index, directions in enumerate([*script, STILL, STILL]):
        interact = PRESS_E if index in (len(script) - 5, len(script) + 1) else NO_E
        _frame(scene, renderer, directions, interact)
        player = scene.player
        trace.append(
            (
                player.x_float,
                player.y_float,
                scene.target_qualified_id,
                scene.visited_count,
                scene.mission_is_complete,
                _text_at(renderer, _FEEDBACK_AT),
                tuple(
                    (item.world_object.x, item.world_object.y, item.world_object.width)
                    for item in scene.objects
                ),
            )
        )
    monkeypatch.undo()
    return trace


def test_s03_presentation_never_changes_gameplay(monkeypatch: pytest.MonkeyPatch) -> None:
    presented = _gameplay_trace(monkeypatch, presented=True)
    plain = _gameplay_trace(monkeypatch, presented=False)
    assert presented == plain
    assert any(step[3] == 1 for step in presented)  # the scripted E press did land
