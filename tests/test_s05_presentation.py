"""S05 (M05) continues the S04 conversation in the frozen Moon Meadow, without gameplay change.

These tests pin M05's explicit presentation policy: the canonical S05 package's
Guide wears the existing trusted Moonlit Guide art, each line of its 2-3-line
conversation is shown whole in the existing dialogue bubble as the scene
speaks it, the existing talk cue stays until the final line has been shown, the
existing audio cues are reused (the moon bell on line one, the completion motif
once), no M02/M03 story beat leaks in, and a scripted M05 run is identical with
and without presentation.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

import engine.rendering._trail_presentation as presentation_module
from engine.audio import AudioCue
from engine.input import DirectionalInput
from engine.rendering._classroom_environment import MEADOW_BACKDROP
from engine.rendering._classroom_sprites import (
    COMPASS_HALO_SHEET_ID,
    CRYSTAL_LANTERN_QUALIFIED_ID,
    MOONLIT_GUIDE_QUALIFIED_ID,
)
from engine.rendering._mission_presentation import (
    MISSION_PRESENTATIONS,
    S05_MISSION_ID,
    S05_MOONLIT_GUIDE_QUALIFIED_ID,
    mission_presentation,
)
from engine.rendering._trail_presentation import (
    _BUBBLE_TEXT,
    ELLIPSIS,
    FEEDBACK_TEXT_X,
    GUIDE_TALK,
    HUD_BOTTOM,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TrailPresentation,
)
from engine.scenes import ClassroomTrailMissionCompletionRule
from explore import curriculum
from explore.curriculum import MISSION_04_ID, MISSION_05, MISSION_05_ID
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from tests.test_s04_presentation import (
    GUIDE_SHEET,
    NO_E,
    PRESS_E,
    STEP,
    AccentRenderer,
    _bubble_texts,
    _frame,
    _scene,
    _texts,
    _walk_to,
    _waypoint_kites,
    platform,  # noqa: F401  (pytest fixture)
)
from tests.test_trail_audio import RecordingSink, _effects, _frames, _visit

REPO = Path(__file__).resolve().parents[1]
S05_PACKAGE = REPO / "lessons/sessions/s05/student/explorer-package"
#: Exactly the packages of the canonical S05 ``explore-package trail`` command.
S05_PACKAGES = (
    REPO / "examples/explorer-packages/nova-character",
    REPO / "examples/explorer-packages/crystal-lantern",
    S05_PACKAGE,
)
GUIDE_YAML = yaml.safe_load((S05_PACKAGE / "character/guide.yaml").read_text())
LINES: tuple[str, ...] = tuple(GUIDE_YAML["conversation"])
GUIDE = S05_MOONLIT_GUIDE_QUALIFIED_ID
#: Beside the Guide and in interaction range, as in S04.
APPROACH = (455.0, 262.0)


def _s05(renderer: object, package_roots=S05_PACKAGES, **options: object):  # type: ignore[no-untyped-def]
    return _scene(renderer, mission_id=MISSION_05_ID, package_roots=package_roots, **options)


def _guide(scene):  # type: ignore[no-untyped-def]
    return next(npc for npc in scene.npcs if npc.qualified_id == GUIDE)


def _talk(scene, renderer) -> None:  # type: ignore[no-untyped-def]
    """Stand beside the Guide (once) and press E for the next line."""
    if scene.target_qualified_id != GUIDE:
        _walk_to(scene, renderer, *APPROACH)
    assert scene.target_qualified_id == GUIDE
    _frame(scene, renderer, interact=PRESS_E)


def _hold(scene, renderer, seconds: float) -> None:  # type: ignore[no-untyped-def]
    for _ in range(round(seconds / STEP)):
        _frame(scene, renderer)


def _talk_cue_panels(renderer) -> list[tuple[object, ...]]:  # type: ignore[no-untyped-def]
    return [
        values
        for kind, values in renderer.operations
        if kind == "panel" and values[2:4] == (30, 20)
    ]


def _package_with_conversation(tmp_path: Path, lines: list[str]) -> Path:
    copy = tmp_path / "moonlit-conversation"
    shutil.copytree(S05_PACKAGE, copy)
    source = copy / "character/guide.yaml"
    data = yaml.safe_load(source.read_text())
    data["conversation"] = lines
    source.write_text(yaml.safe_dump(data, allow_unicode=True))
    return copy


# ---------------------------------------------------------------------------
# Policy: M05 joins explicitly, reusing S04's Guide treatment
# ---------------------------------------------------------------------------


def test_m05_policy_is_explicit_and_reuses_the_s04_guide_treatment() -> None:
    assert S05_MISSION_ID == MISSION_05_ID == "write-a-short-conversation"
    policy = mission_presentation(MISSION_05_ID)
    assert policy is MISSION_PRESENTATIONS[MISSION_05_ID]
    assert policy is not None
    assert policy.talk_cue and policy.dialogue_focus and policy.meadow_audio
    assert not policy.discovery_label and not policy.celebration
    assert not policy.lantern_waypoint
    assert policy.sprite_aliases == {S05_MOONLIT_GUIDE_QUALIFIED_ID: MOONLIT_GUIDE_QUALIFIED_ID}
    m04 = mission_presentation(MISSION_04_ID)
    assert m04 is not None and m04.sprite_aliases == {}
    for flag in ("talk_cue", "dialogue_focus", "meadow_audio", "lantern_waypoint", "celebration"):
        assert getattr(policy, flag) == getattr(m04, flag), flag


def test_the_alias_names_the_canonical_s05_package_guide() -> None:
    manifest = yaml.safe_load((S05_PACKAGE / "manifest.yaml").read_text())
    (contribution,) = manifest["contributions"]
    assert f"{manifest['package']['id']}:{contribution['id']}" == GUIDE
    assert GUIDE_YAML["name"] == "Moonlit Guide"
    assert GUIDE_YAML["color"] == "blue"
    assert "greeting" not in GUIDE_YAML and 2 <= len(LINES) <= 3


def test_the_s05_alias_never_leaks_outside_m05() -> None:
    for mission_id in (None, *MISSION_PRESENTATIONS, curriculum.MISSION_06_ID):
        if mission_id == MISSION_05_ID:
            continue
        presentation = TrailPresentation(mission_id)
        assert presentation.sprite_identity(GUIDE) == GUIDE
        assert presentation.pose_for(GUIDE) is None


# ---------------------------------------------------------------------------
# Lesson semantics are unchanged
# ---------------------------------------------------------------------------


def test_m05_completion_rule_is_unchanged() -> None:
    rule = ClassroomTrailMissionCompletionRule.ALL_CONVERSATION_NPCS_COMPLETED
    assert MISSION_05.completion_rule is rule
    assert MISSION_05.title == "Write a Conversation"


def test_each_press_shows_the_next_line_and_m05_completes_on_the_final_line() -> None:
    renderer = AccentRenderer()
    scene = _s05(renderer)
    for index, line in enumerate(LINES):
        _talk(scene, renderer)
        assert scene.feedback_message == f"Moonlit Guide: {line}"
        assert scene.mission_is_complete is (index == len(LINES) - 1), index
        _hold(scene, renderer, 0.2)
    # The interaction after the final line restarts at line one, and completion stays.
    _talk(scene, renderer)
    assert scene.feedback_message == f"Moonlit Guide: {LINES[0]}"
    assert scene.mission_is_complete
    assert not scene.is_complete, "the Lantern is a lit world object, not today's target"


def _gameplay_trace(monkeypatch: pytest.MonkeyPatch, *, presented: bool) -> list[object]:
    if not presented:
        monkeypatch.setattr(presentation_module, "mission_presentation", lambda _id: None)
    renderer = AccentRenderer()
    scene = _s05(renderer)
    assert scene._presentation.active is presented
    script = (
        [DirectionalInput(right=True)] * 20
        + [DirectionalInput(up=True)] * 8
        + [DirectionalInput()] * 4
        + [DirectionalInput()] * 400
        + [DirectionalInput(left=True)] * 140
        + [DirectionalInput(down=True)] * 120
    )
    presses = {32, 33, 120, 240, 360, 380}
    trace: list[object] = []
    for index, directions in enumerate(script):
        _frame(scene, renderer, directions, PRESS_E if index in presses else NO_E)
        player = scene.player
        guide = _guide(scene).character
        trace.append(
            (
                player.x_float,
                player.y_float,
                scene.target_qualified_id,
                scene.visited_count,
                scene.spoken_npc_ids,
                scene.completed_conversation_npc_ids,
                scene.mission_is_complete,
                scene.feedback_message,
                (guide.x, guide.y, guide.width, guide.height, guide.color),
            )
        )
    monkeypatch.undo()
    return trace


def test_s05_presentation_never_changes_gameplay(monkeypatch: pytest.MonkeyPatch) -> None:
    presented = _gameplay_trace(monkeypatch, presented=True)
    plain = _gameplay_trace(monkeypatch, presented=False)
    assert presented == plain
    assert any(step[6] for step in presented), "the scripted conversation did complete"
    assert any(not step[6] for step in presented)


# ---------------------------------------------------------------------------
# Trusted art: the S05 package's Guide is drawn as the Moonlit Guide
# ---------------------------------------------------------------------------


def test_canonical_s05_guide_draws_trusted_art_in_its_exact_box_never_a_rectangle() -> None:
    renderer = AccentRenderer()
    scene = _s05(renderer)
    guide = _guide(scene).character
    assert (guide.x, guide.y, guide.width, guide.height) == (540, 220, 100, 100)
    columns = set()
    for index in range(round(6.0 / STEP)):
        _frame(scene, renderer)
        sprites = [values for kind, values in renderer.operations if kind == "sprite"]
        assert sprites[0][:3] == MEADOW_BACKDROP
        (drawn,) = renderer.sprite_ops(GUIDE_SHEET)
        assert drawn[3:7] == (guide.x, guide.y, guide.width, guide.height)
        columns.add(drawn[2])
        box = (guide.x, guide.y, guide.width, guide.height, guide.color)
        assert ("rect", box) not in renderer.operations, index
    assert "blink" in columns


def test_guide_gestures_on_every_line_without_moving() -> None:
    renderer = AccentRenderer()
    scene = _s05(renderer)
    for _ in LINES:
        _talk(scene, renderer)
        seen = []
        for _ in range(round((GUIDE_TALK.duration + 0.3) / STEP)):
            _frame(scene, renderer)
            (drawn,) = renderer.sprite_ops(GUIDE_SHEET)
            seen.append(drawn[2])
            assert drawn[3:7] == (540, 220, 100, 100)
        assert seen[0].startswith("talk-") and not seen[-1].startswith("talk-")


# ---------------------------------------------------------------------------
# Dialogue: each line whole, in order, in the existing bubble
# ---------------------------------------------------------------------------


def test_each_line_is_shown_whole_in_order_with_the_guide_name_tag() -> None:
    renderer = AccentRenderer()
    scene = _s05(renderer)
    for line in (*LINES, LINES[0]):
        _talk(scene, renderer)
        _frame(scene, renderer)
        bubble = scene._presentation.bubble
        assert bubble is not None and bubble.qualified_id == GUIDE and bubble.text == line
        assert " ".join(str(values[0]) for values in _bubble_texts(renderer)) == line
        names = [values[0] for values in _texts(renderer) if values[4] == 20]
        assert names == ["Moonlit Guide"]
        full = f"Moonlit Guide: {line}"
        assert scene.feedback_message == full
        (echo,) = [values for values in _texts(renderer) if values[1:3] == (FEEDBACK_TEXT_X, 560)]
        text = str(echo[0])
        assert text == full or (text.endswith(ELLIPSIS) and full.startswith(text[: -len(ELLIPSIS)]))
        for values in _bubble_texts(renderer):
            text, x, y, _color, size = values
            width, height = renderer.measure_text(str(text), int(size))  # type: ignore[arg-type]
            assert x >= 0 and x + width <= SCREEN_WIDTH, values  # type: ignore[operator]
            assert y > HUD_BOTTOM and y + height <= SCREEN_HEIGHT, values  # type: ignore[operator]
        _hold(scene, renderer, 0.3)


def test_real_fonts_show_every_canonical_line_whole_in_bubble_and_hud(platform) -> None:  # type: ignore[no-untyped-def]  # noqa: F811
    from engine.rendering import Renderer

    class Recording(Renderer):
        def __init__(self, platform) -> None:  # type: ignore[no-untyped-def]
            super().__init__(platform)
            self.texts: list[tuple[object, ...]] = []

        def draw_text(self, *values) -> None:  # type: ignore[no-untyped-def]
            self.texts.append(values)
            super().draw_text(*values)

    renderer = Recording(platform)
    scene = _s05(renderer)
    player = scene.player
    for _ in range(600):
        dx, dy = APPROACH[0] - player.x_float, APPROACH[1] - player.y_float
        if abs(dx) < 3 and abs(dy) < 3:
            break
        scene.update(
            DirectionalInput(left=dx < -2, right=dx > 2, up=dy < -2, down=dy > 2), NO_E, STEP
        )
    for line in LINES:
        scene.update(DirectionalInput(), PRESS_E, STEP)
        scene.update(DirectionalInput(), NO_E, STEP)
        renderer.texts.clear()
        renderer.clear_frame((0, 0, 0))
        scene.render()
        bubble = [values[0] for values in renderer.texts if values[3] == _BUBBLE_TEXT]
        assert " ".join(bubble) == line, "a canonical line must not be shortened"
        assert f"Moonlit Guide: {line}" in [values[0] for values in renderer.texts]
        for text, x, y, _color, size in renderer.texts:
            width, height = renderer.measure_text(text, size)
            assert x + width <= SCREEN_WIDTH and y + height <= SCREEN_HEIGHT, text


def test_a_two_line_support_conversation_gets_a_bubble_per_line(tmp_path: Path) -> None:
    lines = ["The ridge trail went dark.", "Please help me light it again."]
    package = _package_with_conversation(tmp_path, lines)
    renderer = AccentRenderer()
    scene = _s05(renderer, package_roots=(*S05_PACKAGES[:-1], package))
    for index, line in enumerate(lines):
        _talk(scene, renderer)
        assert scene._presentation.bubble is not None
        assert scene._presentation.bubble.text == line
        assert scene.mission_is_complete is (index == 1)
        _hold(scene, renderer, 0.2)


def test_multi_line_bubbles_need_dialogue_focus() -> None:
    class Character:
        name = "Moonlit Guide"

    class NPC:
        qualified_id = GUIDE
        character = Character()
        conversation_lines = LINES

    class View:
        feedback_message = f"Moonlit Guide: {LINES[1]}"

    assert TrailPresentation(MISSION_05_ID)._spoken_line(View(), NPC()) == LINES[1]  # type: ignore[arg-type]
    for mission_id in (curriculum.MISSION_01_ID, curriculum.MISSION_02_ID, None):
        assert TrailPresentation(mission_id)._spoken_line(View(), NPC()) is None  # type: ignore[arg-type]
    View.feedback_message = "Moonlit Guide: something else"
    assert TrailPresentation(MISSION_05_ID)._spoken_line(View(), NPC()) is None  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# The talk cue stays until the final line
# ---------------------------------------------------------------------------


def test_talk_cue_marks_the_guide_until_its_final_line_has_been_shown() -> None:
    renderer = AccentRenderer()
    scene = _s05(renderer)
    _frame(scene, renderer)
    presentation = scene._presentation
    assert presentation.talk_cue_ids(scene) == (GUIDE,)
    (cue,) = _talk_cue_panels(renderer)
    assert cue[0] >= 540 and cue[0] + 30 <= 640 and HUD_BOTTOM < cue[1] < 220  # type: ignore[operator]
    for index in range(len(LINES)):
        _talk(scene, renderer)
        _frame(scene, renderer)
        assert not _talk_cue_panels(renderer), "the bubble replaces the cue while it is up"
        final = index == len(LINES) - 1
        assert presentation.talk_cue_ids(scene) == (() if final else (GUIDE,))
        if not final:
            _hold(scene, renderer, presentation_module.DIALOGUE_MAX_DURATION)
            assert _talk_cue_panels(renderer), "the cue returns between lines"
    _hold(scene, renderer, presentation_module.DIALOGUE_MAX_DURATION)
    assert not _talk_cue_panels(renderer)


# ---------------------------------------------------------------------------
# No leakage: no M02/M03 beat, no celebration, no Lantern marker
# ---------------------------------------------------------------------------


def test_no_m02_or_m03_story_beat_leaks_into_m05() -> None:
    renderer = AccentRenderer()
    scene = _s05(renderer)
    seen: set[object] = set()
    for _ in LINES:
        _talk(scene, renderer)
        _hold(scene, renderer, 0.2)
    _walk_to(scene, renderer, 170, 380)
    _frame(scene, renderer, interact=PRESS_E)
    for _ in range(round(3.5 / STEP)):
        _frame(scene, renderer)
        seen.update(values[0] for values in _texts(renderer))
        assert not renderer.sprite_ops(COMPASS_HALO_SHEET_ID)
        assert not _waypoint_kites(renderer)
    assert scene.mission_is_complete and scene.is_complete
    assert not any("discovered!" in str(text) for text in seen)
    assert "Mission complete!" not in seen
    assert scene._presentation.celebration_start is None
    assert scene._presentation.label is None


def test_m05_layers_stay_bounded_over_a_long_session() -> None:
    renderer = AccentRenderer()
    scene = _s05(renderer)
    _talk(scene, renderer)
    counts = []
    for second in range(40):
        for _ in range(60):
            _frame(scene, renderer, interact=PRESS_E if second % 3 == 0 else NO_E)
        counts.append(len(renderer.operations))
    presentation = scene._presentation
    assert len(presentation.bursts) <= presentation_module.MAX_BURSTS
    assert len(presentation.greet_start) == 1
    assert len(presentation._layouts) <= presentation_module.MAX_CACHED_LAYOUTS
    assert max(counts) - min(counts) < 80, counts


# ---------------------------------------------------------------------------
# Audio: existing cues only
# ---------------------------------------------------------------------------


def _audio_scene(sink: RecordingSink):  # type: ignore[no-untyped-def]
    planned = plan_local_classroom_trail(S05_PACKAGES, player_qualified_id="nova-character:nova")
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(
        AccentRenderer(), planned.plan, mission_id=MISSION_05_ID, audio=sink
    )
    scene.enter()
    return scene


def test_m05_rings_the_moon_bell_on_line_one_and_completes_once() -> None:
    sink = RecordingSink()
    scene = _audio_scene(sink)
    _visit(scene, GUIDE)
    _frames(scene, 120)
    for _ in LINES[1:]:
        _frames(scene, 1, interact=PRESS_E)
        _frames(scene, 120)
    assert scene.mission_is_complete
    effects = [cue for cue in _effects(sink) if cue is not AudioCue.OBJECT_NEAR]
    assert effects == [AudioCue.NPC_TALK, AudioCue.MISSION_COMPLETE]
    assert AudioCue.LANTERN_CHIME not in sink.played
    assert sink.ambience == [("start", AudioCue.AMBIENT_MOON_MEADOW)]
    # Wrapping around starts the conversation again: one more bell, no new motif.
    _frames(scene, 1, interact=PRESS_E)
    _frames(scene, 120)
    assert sink.played.count(AudioCue.NPC_TALK) == 2
    assert sink.played.count(AudioCue.MISSION_COMPLETE) == 1


def test_m05_lantern_chimes_only_when_it_is_actually_inspected() -> None:
    sink = RecordingSink()
    scene = _audio_scene(sink)
    _visit(scene, CRYSTAL_LANTERN_QUALIFIED_ID)
    assert AudioCue.LANTERN_CHIME in sink.played
    assert AudioCue.MISSION_COMPLETE not in sink.played
