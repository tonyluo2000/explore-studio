"""S01 (M01) arrives in the frozen Moon Meadow, without gameplay change.

These tests pin M01's explicit presentation policy (shared layers only: no
Lantern waypoint, M02 label or celebration, talk cue, dialogue focus, or
audio), the canonical S01 cast (Nova, a non-counting Pixel, and the Crystal
Lantern), that Moon Meadow is never implied by omitting ``--mission-id``, and
that a scripted M01 run is identical with and without presentation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import engine.rendering._classroom_environment as environment_module
import engine.rendering._trail_presentation as presentation_module
from engine.input import DirectionalInput, InteractionInput
from engine.rendering._classroom_environment import MEADOW_BACKDROP, draw_classroom_backdrop
from engine.rendering._classroom_sprites import (
    COMPASS_HALO_SHEET_ID,
    COMPASS_SHEET_ID,
    CRYSTAL_LANTERN_QUALIFIED_ID,
    MOON_COMPASS_QUALIFIED_ID,
    MOONLIT_GUIDE_QUALIFIED_ID,
    NOVA_QUALIFIED_ID,
    PIXEL_QUALIFIED_ID,
    SPRITE_SHEET_IDS,
)
from engine.rendering._mission_presentation import (
    MISSION_PRESENTATIONS,
    S01_MISSION_ID,
    MissionPresentation,
    mission_presentation,
)
from engine.rendering._trail_presentation import _WAYPOINT, TrailPresentation
from explore.curriculum import MISSION_01_ID, MISSION_06_ID
from explore.packages import cli
from explore.packages.classroom_trail import (
    DEFAULT_CLASSROOM_TRAIL_MISSION_ID,
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from tests.test_mission_presentation_contract import CANONICAL, AccentCheckingRenderer
from tests.test_s02_art_pass import ArtRenderer
from tests.test_trail_audio import FakeBackend, _manager

REPO = Path(__file__).resolve().parents[1]
EXAMPLES = REPO / "examples/explorer-packages"
#: Exactly the packages of the canonical S01 ``explore-package trail`` command.
S01_PACKAGES = (
    EXAMPLES / "nova-character",
    EXAMPLES / "pixel-companion",
    EXAMPLES / "crystal-lantern",
)
#: The retired S01 cast, still shipped as reusable free-play examples.
FREE_PLAY_PACKAGES = (
    EXAMPLES / "nova-character",
    EXAMPLES / "forest-guide",
    EXAMPLES / "crystal-lantern",
    EXAMPLES / "river-fountain",
)
STEP = 1 / 60
STILL = DirectionalInput()
NO_E = InteractionInput()
PRESS_E = InteractionInput(interact_pressed=True)
#: Beside the Lantern shrine and in interaction range.
LANTERN_APPROACH = (130.0, 400.0)


def _scene(  # type: ignore[no-untyped-def]
    renderer: object,
    *,
    mission_id: str | None = MISSION_01_ID,
    package_roots=S01_PACKAGES,
    audio: object = None,
):
    planned = plan_local_classroom_trail(package_roots, player_qualified_id=NOVA_QUALIFIED_ID)
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=mission_id, audio=audio)
    scene.enter()
    return scene


def _frame(scene, renderer: ArtRenderer, directions=STILL, interact=NO_E) -> None:  # type: ignore[no-untyped-def]
    scene.update(directions, interact, STEP)
    renderer.operations.clear()
    scene.render()


def _walk_to(scene, renderer: ArtRenderer, x: float, y: float) -> None:  # type: ignore[no-untyped-def]
    player = scene.player
    for _ in range(900):
        dx, dy = x - player.x_float, y - player.y_float
        if abs(dx) < 3 and abs(dy) < 3:
            return
        _frame(
            scene,
            renderer,
            DirectionalInput(left=dx < -2, right=dx > 2, up=dy < -2, down=dy > 2),
        )
    raise AssertionError(f"Nova never reached {(x, y)}")


def _texts(renderer: ArtRenderer) -> list[object]:
    return [values[0] for kind, values in renderer.operations if kind == "text"]


def _waypoint_kites(renderer: ArtRenderer) -> list[tuple[object, ...]]:
    return [
        values
        for kind, values in renderer.operations
        if kind == "polygon" and values[1] == _WAYPOINT
    ]


# ---------------------------------------------------------------------------
# Policy: explicit, shared layers only, silent
# ---------------------------------------------------------------------------


def test_m01_policy_is_explicit_and_withholds_every_later_story_beat() -> None:
    assert S01_MISSION_ID == MISSION_01_ID == DEFAULT_CLASSROOM_TRAIL_MISSION_ID
    policy = mission_presentation(MISSION_01_ID)
    assert policy is MISSION_PRESENTATIONS[MISSION_01_ID]
    assert policy == MissionPresentation()
    assert not policy.discovery_label and not policy.celebration
    assert not policy.lantern_waypoint and not policy.talk_cue and not policy.dialogue_focus
    assert not policy.meadow_audio
    assert policy.sprite_aliases == {}
    assert TrailPresentation(MISSION_01_ID).active


# ---------------------------------------------------------------------------
# The canonical S01 cast
# ---------------------------------------------------------------------------


def test_canonical_s01_command_is_nova_pixel_and_the_lantern() -> None:
    packages, options = CANONICAL["s01"]
    assert packages == (
        "examples/explorer-packages/nova-character",
        "examples/explorer-packages/pixel-companion",
        "examples/explorer-packages/crystal-lantern",
    )
    assert options["--player"] == NOVA_QUALIFIED_ID
    assert options["--mission-id"] == MISSION_01_ID
    assert tuple(REPO / package for package in packages) == S01_PACKAGES


def test_s01_scene_has_no_fern_fountain_compass_or_guide() -> None:
    scene = _scene(ArtRenderer())
    npcs = {npc.qualified_id for npc in scene.npcs}
    objects = {item.qualified_id for item in scene.objects}
    assert npcs == {PIXEL_QUALIFIED_ID}
    assert objects == {CRYSTAL_LANTERN_QUALIFIED_ID}
    retired = {"forest-guide:guide", "river-fountain:fountain"}
    assert not (npcs | objects) & (retired | {MOON_COMPASS_QUALIFIED_ID})
    assert MOONLIT_GUIDE_QUALIFIED_ID not in npcs
    names = {npc.character.name for npc in scene.npcs} | {
        item.world_object.name for item in scene.objects
    }
    assert names == {"Pixel", "Crystal Lantern"}


def test_retired_s01_examples_still_ship_and_validate() -> None:
    planned = plan_local_classroom_trail(FREE_PLAY_PACKAGES, player_qualified_id=NOVA_QUALIFIED_ID)
    assert planned.is_planned, planned.issues


def test_explicit_m01_draws_the_meadow_and_trusted_cast_in_their_boxes() -> None:
    renderer = AccentCheckingRenderer()
    scene = _scene(renderer)
    _frame(scene, renderer)
    sprites = [values for kind, values in renderer.operations if kind == "sprite"]
    assert sprites[0][:3] == MEADOW_BACKDROP
    entities = {NOVA_QUALIFIED_ID: scene.player}
    entities.update((npc.qualified_id, npc.character) for npc in scene.npcs)
    entities.update((item.qualified_id, item.world_object) for item in scene.objects)
    for qualified_id, entity in entities.items():
        sheet = SPRITE_SHEET_IDS[qualified_id]
        drawn = [values for values in sprites if values[0] == sheet]
        assert drawn, f"{qualified_id} fell back instead of drawing {sheet}"
        assert all(
            values[3:7] == (entity.x, entity.y, entity.width, entity.height) for values in drawn
        )
        box = (entity.x, entity.y, entity.width, entity.height, entity.color)
        assert ("rect", box) not in renderer.operations, f"{qualified_id} rectangle"
    assert not renderer.sprite_ops(COMPASS_SHEET_ID)
    assert not renderer.sprite_ops(COMPASS_HALO_SHEET_ID)
    assert not renderer.sprite_ops("characters/moonlit-guide")


# ---------------------------------------------------------------------------
# Completion: only the Lantern counts; Pixel is narrative only
# ---------------------------------------------------------------------------


def test_only_the_lantern_counts_and_pixel_is_never_required() -> None:
    renderer = ArtRenderer()
    scene = _scene(renderer)
    _frame(scene, renderer)
    assert scene.total_objects == 1
    assert "Visited 0 / 1" in _texts(renderer)
    _walk_to(scene, renderer, *LANTERN_APPROACH)
    assert scene.target_qualified_id == CRYSTAL_LANTERN_QUALIFIED_ID
    _frame(scene, renderer, interact=PRESS_E)
    assert scene.visited_qualified_ids == {CRYSTAL_LANTERN_QUALIFIED_ID}
    assert scene.spoken_npc_ids == frozenset(), "Pixel was never spoken to"
    assert scene.mission_is_complete and scene.is_complete
    texts = _texts(renderer)
    assert "Visited 1 / 1" in texts and "Trail complete!" in texts
    assert "Mission state: Complete" in texts


def test_talking_to_pixel_never_counts_toward_m01() -> None:
    renderer = ArtRenderer()
    scene = _scene(renderer)
    _frame(scene, renderer)
    assert scene.target_qualified_id == PIXEL_QUALIFIED_ID
    _frame(scene, renderer, interact=PRESS_E)
    assert scene.spoken_npc_ids == {PIXEL_QUALIFIED_ID}
    assert scene.feedback_message == (
        "Pixel: Beep! I'm Pixel. I can't do much yet, but I'm very curious."
    )
    assert scene.visited_count == 0 and not scene.mission_is_complete
    assert "Visited 0 / 1" in _texts(renderer)


# ---------------------------------------------------------------------------
# No later-session beat leaks into the arrival
# ---------------------------------------------------------------------------


def test_no_m02_m03_or_m04_story_beat_leaks_into_m01() -> None:
    renderer = ArtRenderer()
    scene = _scene(renderer)
    seen: set[object] = set()
    _frame(scene, renderer, interact=PRESS_E)  # Pixel greets
    _walk_to(scene, renderer, *LANTERN_APPROACH)
    _frame(scene, renderer, interact=PRESS_E)
    for _ in range(round(3.5 / STEP)):
        _frame(scene, renderer)
        seen.update(_texts(renderer))
        assert not _waypoint_kites(renderer), "no Lantern destination marker in S01"
        assert not renderer.sprite_ops(COMPASS_HALO_SHEET_ID)
    assert scene.is_complete
    assert not any("discovered!" in str(text) for text in seen)
    assert "Mission complete!" not in seen
    assert not any("Compass" in str(text) or "Guide" in str(text) for text in seen)
    presentation = scene._presentation
    assert presentation.celebration_start is None and presentation.label is None
    assert presentation.talk_cue_ids(scene) == ()


def test_lantern_has_no_waypoint_before_it_is_visited() -> None:
    renderer = ArtRenderer()
    scene = _scene(renderer)
    for _ in range(30):
        _frame(scene, renderer)
        assert not _waypoint_kites(renderer)
    assert renderer.sprite_ops(SPRITE_SHEET_IDS[CRYSTAL_LANTERN_QUALIFIED_ID])


# ---------------------------------------------------------------------------
# Omitting --mission-id never implies the S01 story presentation
# ---------------------------------------------------------------------------


def test_no_mission_id_runs_m01_rules_on_the_plain_trail() -> None:
    renderer = ArtRenderer()
    scene = _scene(renderer, mission_id=None)
    assert scene.mission.mission_id == MISSION_01_ID
    assert not scene._presentation.active
    assert not scene._audio.active
    _frame(scene, renderer)
    assert not renderer.sprite_ops(MEADOW_BACKDROP[0])
    assert not {"translucent", "glow", "shadow"} & set(renderer.kinds())
    assert not draw_classroom_backdrop(ArtRenderer(), None)  # type: ignore[arg-type]


def _plain_m01_operations(monkeypatch: pytest.MonkeyPatch, *, mission_id: str | None) -> list:  # type: ignore[type-arg]
    renderer = ArtRenderer()
    scene = _scene(renderer, mission_id=mission_id, package_roots=FREE_PLAY_PACKAGES)
    frames = []
    for directions in [DirectionalInput(left=True)] * 30 + [STILL] * 10:
        _frame(scene, renderer, directions)
        frames.append(list(renderer.operations))
    monkeypatch.undo()
    return frames


def test_no_mission_free_play_renders_exactly_like_the_pre_s01_plain_trail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A free-play Trail without --mission-id draws what M01 drew before S01 opted in."""
    omitted = _plain_m01_operations(monkeypatch, mission_id=None)
    # Before the opt-in, M01 had no policy anywhere.
    monkeypatch.setattr(presentation_module, "mission_presentation", lambda _id: None)
    monkeypatch.setattr(environment_module, "mission_presentation", lambda _id: None)
    before = _plain_m01_operations(monkeypatch, mission_id=MISSION_01_ID)
    assert omitted == before


def test_cli_omitted_mission_id_reaches_the_runner_as_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(cli, "run_classroom_trail", lambda plan, **kwargs: calls.append(kwargs))
    roots = [str(root) for root in FREE_PLAY_PACKAGES]
    assert cli.main(["trail", *roots, "--player", NOVA_QUALIFIED_ID]) == 0
    assert calls == [{"name": "Classroom Trail", "mission_id": None}]
    assert (
        cli.main(["trail", *roots, "--player", NOVA_QUALIFIED_ID, "--mission-id", MISSION_01_ID])
        == 0
    )
    assert calls[-1] == {"name": "Classroom Trail", "mission_id": MISSION_01_ID}


def test_runner_without_mission_builds_a_plain_trail(monkeypatch: pytest.MonkeyPatch) -> None:
    """``run_classroom_trail`` passes the omission through, so no story presentation."""
    import explore.packages.classroom_trail as trail_module

    seen: list[object] = []

    def capture(renderer, plan, *, mission_id=None, audio=None):  # type: ignore[no-untyped-def]
        seen.append(mission_id)
        raise _StopError

    class _StopError(Exception):
        pass

    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("EXPLORE_STUDIO_AUDIO", "off")
    monkeypatch.setattr(trail_module, "create_classroom_trail_scene", capture)
    planned = plan_local_classroom_trail(FREE_PLAY_PACKAGES, player_qualified_id=NOVA_QUALIFIED_ID)
    with pytest.raises(_StopError):
        trail_module.run_classroom_trail(planned.plan)
    with pytest.raises(_StopError):
        trail_module.run_classroom_trail(planned.plan, mission_id=MISSION_01_ID)
    assert seen == [None, MISSION_01_ID]


@pytest.mark.parametrize("package_roots", (S01_PACKAGES, FREE_PLAY_PACKAGES))
def test_student_free_play_without_mission_never_inherits_s01(package_roots) -> None:  # type: ignore[no-untyped-def]
    renderer = ArtRenderer()
    scene = _scene(renderer, mission_id=None, package_roots=package_roots)
    for _ in range(20):
        _frame(scene, renderer, DirectionalInput(right=True))
        sprites = {values[0] for kind, values in renderer.operations if kind == "sprite"}
        assert MEADOW_BACKDROP[0] not in sprites
        assert "scenery/moon-meadow-foreground" not in sprites
        assert not _waypoint_kites(renderer)
    assert scene._presentation.pose_for(NOVA_QUALIFIED_ID) is None


# ---------------------------------------------------------------------------
# Audio: S01 stays silent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mission_id", (MISSION_01_ID, None))
def test_canonical_s01_never_opens_the_mixer(mission_id: str | None) -> None:
    backend = FakeBackend()
    manager = _manager(backend)
    renderer = ArtRenderer()
    scene = _scene(renderer, mission_id=mission_id, audio=manager)
    _frame(scene, renderer, interact=PRESS_E)
    _walk_to(scene, renderer, *LANTERN_APPROACH)
    _frame(scene, renderer, interact=PRESS_E)
    for _ in range(60):
        _frame(scene, renderer)
    assert scene.is_complete
    assert scene.toggle_audio_mute() is None
    scene.exit()
    assert backend.calls == [] and backend.open_count == 0
    assert not any(str(text).startswith("Audio:") for text in _texts(renderer))


# ---------------------------------------------------------------------------
# Gameplay parity
# ---------------------------------------------------------------------------


def _gameplay_trace(
    monkeypatch: pytest.MonkeyPatch, *, mission_id: str | None, presented: bool
) -> list[object]:
    if not presented:
        monkeypatch.setattr(presentation_module, "mission_presentation", lambda _id: None)
    renderer = ArtRenderer()
    scene = _scene(renderer, mission_id=mission_id)
    assert scene._presentation.active is presented
    script = (
        [STILL] * 2
        + [DirectionalInput(left=True)] * 112
        + [DirectionalInput(down=True)] * 48
        + [STILL] * 4
    )
    presses = {1, 163, 164}
    trace: list[object] = []
    for index, directions in enumerate(script):
        _frame(scene, renderer, directions, PRESS_E if index in presses else NO_E)
        player = scene.player
        trace.append(
            (
                player.x_float,
                player.y_float,
                scene.target_qualified_id,
                scene.visited_count,
                scene.spoken_npc_ids,
                scene.mission_is_complete,
                scene.is_complete,
                scene.feedback_message,
                tuple(
                    (npc.character.x, npc.character.y, npc.character.width) for npc in scene.npcs
                ),
                tuple(
                    (item.world_object.x, item.world_object.y, item.world_object.width)
                    for item in scene.objects
                ),
            )
        )
    monkeypatch.undo()
    return trace


def test_s01_presentation_never_changes_gameplay(monkeypatch: pytest.MonkeyPatch) -> None:
    presented = _gameplay_trace(monkeypatch, mission_id=MISSION_01_ID, presented=True)
    plain = _gameplay_trace(monkeypatch, mission_id=MISSION_01_ID, presented=False)
    omitted = _gameplay_trace(monkeypatch, mission_id=None, presented=False)
    assert presented == plain == omitted
    assert any(step[5] for step in presented), "the scripted Lantern visit did land"
    assert any(not step[5] for step in presented)
    assert any(step[4] for step in presented), "Pixel's greeting was heard on the way"


def test_m06_and_later_are_unchanged_by_the_s01_opt_in() -> None:
    assert mission_presentation(MISSION_06_ID) is None
    assert not TrailPresentation(MISSION_06_ID).active
