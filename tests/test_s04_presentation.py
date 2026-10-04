"""S04 (M04) gets the Moon Meadow and a trusted Moonlit Guide, without gameplay change.

These tests pin M04's explicit presentation policy, the Guide's trusted-art
routing and safe fallbacks, that the Guide (not the Lantern) carries the
mission cue, the dialogue-focus bubble (canonical text preserved, no silent
clipping, always on screen), that no M02/M03 story beat leaks in, that M05+
are untouched, and that a scripted M04 run is identical with and without
presentation.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml

import engine.rendering._trail_presentation as presentation_module
from engine.assets import TRUSTED_ART_ROOT, TrustedArtCatalog
from engine.input import DirectionalInput, InteractionInput
from engine.rendering._classroom_environment import MEADOW_BACKDROP
from engine.rendering._classroom_sprites import (
    COMPASS_HALO_SHEET_ID,
    CRYSTAL_LANTERN_QUALIFIED_ID,
    MOONLIT_GUIDE_QUALIFIED_ID,
    NOVA_QUALIFIED_ID,
    SPRITE_SHEET_IDS,
    draw_classroom_sprite,
)
from engine.rendering._mission_presentation import (
    MISSION_PRESENTATIONS,
    S04_MISSION_ID,
    mission_presentation,
)
from engine.rendering._trail_presentation import (
    _BUBBLE_TEXT,
    _WAYPOINT,
    BUBBLE_DURATION,
    DIALOGUE_MAX_DURATION,
    ELLIPSIS,
    FEEDBACK_FONT,
    FEEDBACK_TEXT_X,
    GUIDE_IDLE,
    GUIDE_TALK,
    HUD_BOTTOM,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TrailPresentation,
    fit_line,
    wrap_text,
)
from explore import curriculum
from explore._colors import resolve_color
from explore.curriculum import MISSION_02_ID, MISSION_03_ID, MISSION_04_ID
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from tests.test_s02_art_pass import S02_PACKAGES, ArtRenderer

REPO = Path(__file__).resolve().parents[1]
S04_PACKAGE = REPO / "lessons/sessions/s04/student/explorer-package"
#: Exactly the packages of the canonical S04 ``explore-package trail`` command.
S04_PACKAGES = (
    REPO / "examples/explorer-packages/nova-character",
    REPO / "examples/explorer-packages/crystal-lantern",
    S04_PACKAGE,
)
GUIDE_YAML = yaml.safe_load((S04_PACKAGE / "character/guide.yaml").read_text())
GUIDE_SHEET = "characters/moonlit-guide"
STEP = 1 / 60
STILL = DirectionalInput()
NO_E = InteractionInput()
PRESS_E = InteractionInput(interact_pressed=True)
#: Beside the Guide and in interaction range, like the S04 visual proof.
APPROACH = (455.0, 262.0)
LONG_GREETING = (
    "Welcome, brave explorer! I'm Luma, keeper of the Moonlit Trail, and every lantern "
    "beyond the ridge went dark last night, so please help me find the three lost lights "
    "before dawn. I will wait right here by the old stone path and keep my staff glowing "
    "so you can always find your way back to me."
)


class AccentRenderer(ArtRenderer):
    """Refuses a trusted frame for the wrong accent, exactly like the real Renderer."""

    catalog = TrustedArtCatalog()

    def draw_sprite_frame(self, asset_id, row, column, *values, **options):  # type: ignore[no-untyped-def]
        accent = options.get("accent")
        spec = self.catalog.spec(asset_id)
        if spec is None or (accent is not None and spec.accent != accent):
            return False
        return super().draw_sprite_frame(asset_id, row, column, *values, **options)


def _scene(renderer: object, *, mission_id: str = MISSION_04_ID, package_roots=S04_PACKAGES):  # type: ignore[no-untyped-def]
    planned = plan_local_classroom_trail(package_roots, player_qualified_id=NOVA_QUALIFIED_ID)
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=mission_id)
    scene.enter()
    return scene


def _frame(scene, renderer: ArtRenderer, directions=STILL, interact=NO_E) -> None:  # type: ignore[no-untyped-def]
    scene.update(directions, interact, STEP)
    renderer.operations.clear()
    scene.render()


def _walk_to(scene, renderer: ArtRenderer, x: float, y: float) -> None:  # type: ignore[no-untyped-def]
    player = scene.player
    for _ in range(600):
        dx, dy = x - player.x_float, y - player.y_float
        if abs(dx) < 3 and abs(dy) < 3:
            return
        _frame(
            scene,
            renderer,
            DirectionalInput(left=dx < -2, right=dx > 2, up=dy < -2, down=dy > 2),
        )
    raise AssertionError(f"Nova never reached {(x, y)}")


def _greet(scene, renderer: ArtRenderer) -> None:  # type: ignore[no-untyped-def]
    _walk_to(scene, renderer, *APPROACH)
    assert scene.target_qualified_id == MOONLIT_GUIDE_QUALIFIED_ID
    _frame(scene, renderer, interact=PRESS_E)


def _guide(scene):  # type: ignore[no-untyped-def]
    return next(npc for npc in scene.npcs if npc.qualified_id == MOONLIT_GUIDE_QUALIFIED_ID)


def _texts(renderer: ArtRenderer) -> list[tuple[object, ...]]:
    return [values for kind, values in renderer.operations if kind == "text"]


def _package_with_guide(tmp_path: Path, **fields: object) -> Path:
    copy = tmp_path / "moonlit-guide"
    shutil.copytree(S04_PACKAGE, copy)
    source = copy / "character/guide.yaml"
    data = yaml.safe_load(source.read_text())
    data.update(fields)
    source.write_text(yaml.safe_dump(data, allow_unicode=True))
    return copy


def _bubble_texts(renderer: ArtRenderer) -> list[tuple[object, ...]]:
    return [values for values in _texts(renderer) if values[3] == _BUBBLE_TEXT]


# ---------------------------------------------------------------------------
# Policy: M04 joins explicitly; M05+ stay plain
# ---------------------------------------------------------------------------


def test_m04_policy_is_explicit_and_withholds_m02_m03_beats() -> None:
    assert S04_MISSION_ID == MISSION_04_ID == "introduce-your-character"
    policy = mission_presentation(MISSION_04_ID)
    assert policy is not None
    assert policy.talk_cue and policy.dialogue_focus
    assert not policy.discovery_label and not policy.celebration
    assert not policy.lantern_waypoint
    assert policy.sprite_aliases == {}
    assert TrailPresentation(MISSION_04_ID).active


@pytest.mark.parametrize(
    "mission_id",
    [
        getattr(curriculum, f"MISSION_{number:02d}_ID")
        for number in range(5, 17)
        if hasattr(curriculum, f"MISSION_{number:02d}_ID")
    ],
)
def test_m05_and_later_keep_the_plain_trail(mission_id: str) -> None:
    assert mission_id not in MISSION_PRESENTATIONS
    assert not TrailPresentation(mission_id).active
    if mission_id == curriculum.MISSION_14_ID:
        return  # M14 needs an authored toggle style, so no S04-package scene exists.
    renderer = ArtRenderer()
    scene = _scene(renderer, mission_id=mission_id)
    _frame(scene, renderer)
    assert not scene._presentation.active
    sprites = [values for kind, values in renderer.operations if kind == "sprite"]
    assert not sprites, "M05+ must not draw any trusted art"
    guide = _guide(scene).character
    box = (guide.x, guide.y, guide.width, guide.height, guide.color)
    assert ("rect", box) in renderer.operations, "the Guide keeps its plain rectangle"


def test_guide_is_posed_only_so_no_other_mission_draws_it() -> None:
    renderer = ArtRenderer()
    drawn = draw_classroom_sprite(
        renderer, MOONLIT_GUIDE_QUALIFIED_ID, 540, 220, 100, 100, (50, 80, 220)  # type: ignore[arg-type]
    )
    assert not drawn
    assert renderer.operations == []
    for mission_id in (curriculum.MISSION_01_ID, MISSION_02_ID, MISSION_03_ID):
        presentation = TrailPresentation(mission_id)
        assert presentation.pose_for("moonlit-conversation:guide") is None
    # S05's guide is a different package; even M04 does not dress it.
    assert TrailPresentation(MISSION_04_ID).pose_for("moonlit-conversation:guide") is None


# ---------------------------------------------------------------------------
# Trusted Guide art and fallbacks
# ---------------------------------------------------------------------------


def test_guide_maps_to_its_trusted_sheet_for_the_canonical_blue() -> None:
    assert SPRITE_SHEET_IDS[MOONLIT_GUIDE_QUALIFIED_ID] == GUIDE_SHEET
    spec = TrustedArtCatalog().spec(GUIDE_SHEET)
    assert spec is not None
    assert (spec.frame_width, spec.frame_height) == (100, 100)
    assert spec.rows == ("idle",)
    assert spec.columns == (*GUIDE_IDLE.frames, "blink", "talk-0", "talk-1", "talk-2", "talk-3")
    assert set(GUIDE_TALK.frames) <= set(spec.columns)
    assert spec.accent == resolve_color(GUIDE_YAML["color"]) == (50, 80, 220)
    assert TrustedArtCatalog().read_verified(GUIDE_SHEET) is not None


def test_canonical_guide_draws_trusted_art_in_its_exact_box_never_a_rectangle() -> None:
    renderer = AccentRenderer()
    scene = _scene(renderer)
    guide = _guide(scene).character
    assert (guide.name, guide.x, guide.y) == ("Moonlit Guide", GUIDE_YAML["x"], GUIDE_YAML["y"])
    assert (guide.width, guide.height) == (100, 100)
    columns = set()
    for index in range(round(6.0 / STEP)):
        _frame(scene, renderer)
        (drawn,) = renderer.sprite_ops(GUIDE_SHEET)
        assert drawn[1] == "idle"
        assert drawn[3:7] == (guide.x, guide.y, guide.width, guide.height)
        columns.add(drawn[2])
        box = (guide.x, guide.y, guide.width, guide.height, guide.color)
        assert ("rect", box) not in renderer.operations, index
    assert set(GUIDE_IDLE.frames) <= columns and "blink" in columns
    assert (guide.x, guide.y) == (540, 220)


def test_guide_gestures_once_when_greeted_without_moving() -> None:
    renderer = AccentRenderer()
    scene = _scene(renderer)
    _greet(scene, renderer)
    guide = _guide(scene).character
    seen = []
    for _ in range(round((GUIDE_TALK.duration + 0.5) / STEP)):
        _frame(scene, renderer)
        (drawn,) = renderer.sprite_ops(GUIDE_SHEET)
        seen.append(drawn[2])
        assert drawn[3:7] == (540, 220, 100, 100)
    assert seen[0].startswith("talk-") and not seen[-1].startswith("talk-")
    assert (guide.x, guide.y, guide.width, guide.height) == (540, 220, 100, 100)


def test_another_guide_color_keeps_its_meaning_through_the_posed_fallback(
    tmp_path: Path,
) -> None:
    package = _package_with_guide(tmp_path, color="purple")
    renderer = AccentRenderer()
    scene = _scene(renderer, package_roots=(*S04_PACKAGES[:-1], package))
    _frame(scene, renderer)
    guide = _guide(scene).character
    assert guide.color == resolve_color("purple")
    assert not renderer.sprite_ops(GUIDE_SHEET), "blue art must not wear another color"
    assert ("rect", (540, 220, 100, 100, guide.color)) not in renderer.operations
    polygons = [values for kind, values in renderer.operations if kind == "polygon"]
    assert any(values[1] == guide.color for values in polygons), "cloak keeps the authored color"


def test_missing_trusted_art_falls_back_to_the_procedural_guide() -> None:
    renderer = ArtRenderer(trusted_art=False)
    scene = _scene(renderer)
    _frame(scene, renderer)
    assert ("rect", (540, 220, 100, 100, (50, 80, 220))) not in renderer.operations
    assert any(kind == "polygon" for kind, _ in renderer.operations)


def test_unknown_npc_in_m04_keeps_the_rectangle_fallback(tmp_path: Path) -> None:
    package = _package_with_guide(tmp_path)
    manifest = package / "manifest.yaml"
    manifest.write_text(manifest.read_text().replace('id: "moonlit-guide"', 'id: "my-guide"'))
    renderer = AccentRenderer()
    scene = _scene(renderer, package_roots=(*S04_PACKAGES[:-1], package))
    _frame(scene, renderer)
    (npc,) = scene.npcs
    assert npc.qualified_id == "my-guide:guide"
    assert not renderer.sprite_ops(GUIDE_SHEET)
    assert ("rect", (540, 220, 100, 100, (50, 80, 220))) in renderer.operations


# ---------------------------------------------------------------------------
# Focus: the Guide carries the cue, the Lantern no longer pulls
# ---------------------------------------------------------------------------


def _waypoint_kites(renderer: ArtRenderer) -> list[tuple[object, ...]]:
    return [
        values
        for kind, values in renderer.operations
        if kind == "polygon" and values[1] == _WAYPOINT
    ]


def test_m04_lantern_stays_lit_but_loses_its_destination_marker() -> None:
    renderer = AccentRenderer()
    scene = _scene(renderer)
    for _ in range(30):
        _frame(scene, renderer)
        assert renderer.sprite_ops("objects/crystal-lantern"), "the Lantern is still drawn"
        assert not _waypoint_kites(renderer)
    lantern = scene.objects[0]
    assert lantern.qualified_id == CRYSTAL_LANTERN_QUALIFIED_ID
    assert (lantern.world_object.x, lantern.world_object.y) == (120, 460)
    assert lantern.when_near == "The lantern glows warmly."


def test_m02_lantern_destination_marker_is_preserved() -> None:
    renderer = AccentRenderer()
    scene = _scene(renderer, mission_id=MISSION_02_ID, package_roots=S02_PACKAGES)
    _frame(scene, renderer)
    assert _waypoint_kites(renderer)


def test_talk_cue_marks_the_guide_until_it_has_been_spoken_to() -> None:
    renderer = AccentRenderer()
    scene = _scene(renderer)
    _frame(scene, renderer)
    presentation = scene._presentation
    assert presentation.talk_cue_ids(scene) == (MOONLIT_GUIDE_QUALIFIED_ID,)
    cue_panels = [
        values
        for kind, values in renderer.operations
        if kind == "panel" and values[2:4] == (30, 20)
    ]
    (cue,) = cue_panels
    assert cue[0] >= 540 and cue[0] + 30 <= 640 and HUD_BOTTOM < cue[1] < 220
    _greet(scene, renderer)
    assert scene.mission_is_complete
    for _ in range(30):
        _frame(scene, renderer)
    assert presentation.talk_cue_ids(scene) == ()
    assert not [
        values
        for kind, values in renderer.operations
        if kind == "panel" and values[2:4] == (30, 20)
    ]
    for mission_id in (MISSION_02_ID, MISSION_03_ID):
        assert TrailPresentation(mission_id).talk_cue_ids(scene) == ()


def test_prompt_names_the_guide_as_the_interaction() -> None:
    renderer = AccentRenderer()
    scene = _scene(renderer)
    _walk_to(scene, renderer, *APPROACH)
    _frame(scene, renderer)
    assert scene._presentation.prompt_text(scene) == "Talk to Moonlit Guide"
    assert "Talk to Moonlit Guide" in [values[0] for values in _texts(renderer)]


# ---------------------------------------------------------------------------
# Dialogue: canonical text, speaker, no silent clipping, on screen
# ---------------------------------------------------------------------------


def test_canonical_greeting_is_shown_whole_with_the_guide_name_tag() -> None:
    renderer = AccentRenderer()
    scene = _scene(renderer)
    _greet(scene, renderer)
    _frame(scene, renderer)
    greeting = GUIDE_YAML["greeting"]
    assert scene.feedback_message == f"Moonlit Guide: {greeting}"
    bubble = scene._presentation.bubble
    assert bubble is not None and bubble.text == greeting
    lines = [values[0] for values in _bubble_texts(renderer)]
    assert " ".join(lines) == greeting
    names = [values[0] for values in _texts(renderer) if values[4] == 20]
    assert names == ["Moonlit Guide"]
    assert not any("Pixel" in str(values[0]) for values in _texts(renderer))


def test_hud_echo_fits_on_screen_with_an_explicit_ellipsis_and_keeps_state() -> None:
    renderer = AccentRenderer()
    scene = _scene(renderer)
    _greet(scene, renderer)
    echo = [values for values in _texts(renderer) if values[1:3] == (FEEDBACK_TEXT_X, 560)]
    (line,) = echo
    full = f"Moonlit Guide: {GUIDE_YAML['greeting']}"
    assert scene.feedback_message == full
    text = str(line[0])
    assert text.endswith(ELLIPSIS) and full.startswith(text[: -len(ELLIPSIS)])
    assert FEEDBACK_TEXT_X + renderer.measure_text(text, FEEDBACK_FONT)[0] <= SCREEN_WIDTH - 8


def test_hud_echo_is_untouched_outside_dialogue_focus() -> None:
    long_line = "Pixel: " + "very " * 60
    renderer = ArtRenderer()
    for mission_id in (MISSION_02_ID, MISSION_03_ID, curriculum.MISSION_05_ID):
        assert TrailPresentation(mission_id).fit_feedback(renderer, long_line) == long_line
    assert TrailPresentation(MISSION_04_ID).fit_feedback(renderer, None) is None
    short = "Moonlit Guide: Hi!"
    assert TrailPresentation(MISSION_04_ID).fit_feedback(renderer, short) == short


def test_reading_time_scales_with_the_greeting_but_m02_keeps_its_bubble() -> None:
    renderer = AccentRenderer()
    scene = _scene(renderer)
    _greet(scene, renderer)
    bubble = scene._presentation.bubble
    assert bubble is not None
    assert BUBBLE_DURATION < bubble.duration <= DIALOGUE_MAX_DURATION
    m02 = _scene(AccentRenderer(), mission_id=MISSION_02_ID, package_roots=S02_PACKAGES)
    m02_renderer = AccentRenderer()
    _frame(m02, m02_renderer, interact=PRESS_E)
    assert m02._presentation.bubble is not None
    assert m02._presentation.bubble.duration == BUBBLE_DURATION
    assert all(values[4] == 22 for values in _bubble_texts(m02_renderer))


def test_wrap_never_drops_text_silently() -> None:
    def measure(text: str) -> tuple[int, int]:
        return len(text) * 10, 20

    words = LONG_GREETING.split()
    lines = wrap_text(LONG_GREETING, 300, measure, 6)
    assert len(lines) == 6 and lines[-1].endswith(ELLIPSIS)
    assert all(measure(line)[0] <= 300 for line in lines)
    shown = " ".join(lines)[: -len(ELLIPSIS)].split()
    assert shown == words[: len(shown)]
    # Fits: every word, no marker. An unbroken word is split, never clipped.
    assert " ".join(wrap_text("Hello there, explorer.", 300, measure, 6)) == (
        "Hello there, explorer."
    )
    giant = "A" * 70
    pieces = wrap_text(giant, 300, measure, 6)
    assert "".join(pieces) == giant and all(measure(line)[0] <= 300 for line in pieces)
    assert fit_line("short", 300, measure) == "short"
    assert fit_line(LONG_GREETING, 300, measure).endswith(ELLIPSIS)


def _on_screen(renderer: ArtRenderer) -> None:
    for values in _texts(renderer):
        text, x, y, _color, size = values
        width, height = renderer.measure_text(str(text), int(size))  # type: ignore[arg-type]
        assert x >= 0 and x + width <= SCREEN_WIDTH, values  # type: ignore[operator]
        assert y >= 0 and y + height <= SCREEN_HEIGHT, values  # type: ignore[operator]


@pytest.mark.parametrize("greeting", [GUIDE_YAML["greeting"], LONG_GREETING, "Hi!"])
@pytest.mark.parametrize("nova", [APPROACH, (580.0, 320.0), (630.0, 200.0), (470.0, 150.0)])
def test_dialogue_bubble_stays_on_screen_below_the_hud(
    tmp_path: Path, greeting: str, nova: tuple[float, float]
) -> None:
    package = _package_with_guide(tmp_path, greeting=greeting)
    renderer = AccentRenderer()
    scene = _scene(renderer, package_roots=(*S04_PACKAGES[:-1], package))
    _walk_to(scene, renderer, *nova)
    assert scene.target_qualified_id == MOONLIT_GUIDE_QUALIFIED_ID, nova
    _frame(scene, renderer, interact=PRESS_E)
    _frame(scene, renderer)
    lines = _bubble_texts(renderer)
    assert lines
    _on_screen(renderer)
    for values in lines:
        assert values[2] > HUD_BOTTOM  # type: ignore[operator]
    bubble = [
        values
        for kind, values in renderer.operations
        if kind == "panel" and values[4] == (250, 248, 236) and values[2] > 30
    ]
    bx, by, bw, bh, *_rest = bubble[0]
    assert bx >= 0 and bx + bw <= SCREEN_WIDTH and by > HUD_BOTTOM and by + bh <= SCREEN_HEIGHT
    # At a half-scale share the text is still at least 12 px tall.
    assert all(values[4] >= 24 for values in lines)


def test_real_fonts_show_the_canonical_greeting_whole_on_screen(platform) -> None:  # type: ignore[no-untyped-def]
    from engine.rendering import Renderer

    class Recording(Renderer):
        def __init__(self, platform) -> None:  # type: ignore[no-untyped-def]
            super().__init__(platform)
            self.texts: list[tuple[object, ...]] = []

        def draw_text(self, *values) -> None:  # type: ignore[no-untyped-def]
            self.texts.append(values)
            super().draw_text(*values)

    renderer = Recording(platform)
    scene = _scene(renderer)
    player = scene.player
    for _ in range(600):
        dx, dy = APPROACH[0] - player.x_float, APPROACH[1] - player.y_float
        if abs(dx) < 3 and abs(dy) < 3:
            break
        scene.update(
            DirectionalInput(left=dx < -2, right=dx > 2, up=dy < -2, down=dy > 2), NO_E, STEP
        )
    scene.update(STILL, PRESS_E, STEP)
    scene.update(STILL, NO_E, STEP)
    renderer.clear_frame((0, 0, 0))
    scene.render()
    lines = [values[0] for values in renderer.texts if values[3] == _BUBBLE_TEXT]
    assert " ".join(lines) == GUIDE_YAML["greeting"], "canonical greeting must not be shortened"
    for text, x, y, _color, size in renderer.texts:
        width, height = renderer.measure_text(text, size)
        assert x + width <= SCREEN_WIDTH and y + height <= SCREEN_HEIGHT, text


@pytest.fixture
def platform():  # type: ignore[no-untyped-def]
    from engine._config import Config
    from engine._platform import Platform

    instance = Platform(Config())
    instance.initialize()
    yield instance
    instance.shutdown()


# ---------------------------------------------------------------------------
# No leakage, gameplay parity, bounded cost
# ---------------------------------------------------------------------------


def test_no_m02_or_m03_story_beat_leaks_into_m04() -> None:
    renderer = AccentRenderer()
    scene = _scene(renderer)
    seen: set[object] = set()
    _greet(scene, renderer)
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
    sprites = [values for kind, values in renderer.operations if kind == "sprite"]
    assert sprites[0][:3] == MEADOW_BACKDROP


def _gameplay_trace(monkeypatch: pytest.MonkeyPatch, *, presented: bool) -> list[object]:
    if not presented:
        monkeypatch.setattr(presentation_module, "mission_presentation", lambda _id: None)
    renderer = AccentRenderer()
    scene = _scene(renderer)
    assert scene._presentation.active is presented
    script = (
        [DirectionalInput(right=True)] * 20
        + [DirectionalInput(up=True)] * 8
        + [STILL] * 4
        + [DirectionalInput(left=True)] * 140
        + [DirectionalInput(down=True)] * 120
        + [STILL] * 4
    )
    presses = {32, 33, 40, 300, 301}
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
                scene.mission_is_complete,
                scene.is_complete,
                scene.feedback_message,
                (guide.x, guide.y, guide.width, guide.height, guide.color),
                tuple(
                    (item.world_object.x, item.world_object.y, item.world_object.width)
                    for item in scene.objects
                ),
            )
        )
    monkeypatch.undo()
    return trace


def test_s04_presentation_never_changes_gameplay(monkeypatch: pytest.MonkeyPatch) -> None:
    presented = _gameplay_trace(monkeypatch, presented=True)
    plain = _gameplay_trace(monkeypatch, presented=False)
    assert presented == plain
    assert any(step[5] for step in presented), "the scripted greeting did land"
    assert any(not step[5] for step in presented)


def test_m04_layers_stay_bounded_over_a_long_session() -> None:
    renderer = AccentRenderer()
    scene = _scene(renderer)
    _greet(scene, renderer)
    counts = []
    for second in range(40):
        for _ in range(60):
            _frame(scene, renderer, interact=PRESS_E if second % 7 == 0 else NO_E)
        counts.append(len(renderer.operations))
    presentation = scene._presentation
    assert len(presentation.bursts) <= presentation_module.MAX_BURSTS
    assert len(presentation.greet_start) == 1
    assert len(presentation._layouts) <= presentation_module.MAX_CACHED_LAYOUTS
    assert max(counts) - min(counts) < 80, counts


# ---------------------------------------------------------------------------
# Trusted art provenance
# ---------------------------------------------------------------------------


def test_guide_sheet_is_listed_with_a_matching_digest() -> None:
    manifest = json.loads((TRUSTED_ART_ROOT / "manifest.json").read_text())["assets"]
    entry = manifest[GUIDE_SHEET]
    assert entry["file"] == "characters/moonlit-guide/guide.png"
    path = (TRUSTED_ART_ROOT / entry["file"]).resolve()
    assert path.is_relative_to(TRUSTED_ART_ROOT.resolve())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]


def test_guide_sheet_rebuilds_byte_for_byte(tmp_path: Path) -> None:
    pytest.importorskip("numpy")
    pytest.importorskip("PIL")
    import sys

    sys.path[:0] = [str(REPO / "scripts")]
    try:
        from scripts import build_trusted_art
    finally:
        sys.path.remove(str(REPO / "scripts"))
    shutil.copy(TRUSTED_ART_ROOT / "manifest.json", tmp_path / "manifest.json")
    rebuilt = build_trusted_art.build(tmp_path, only=(GUIDE_SHEET,))
    committed = json.loads((TRUSTED_ART_ROOT / "manifest.json").read_text())
    assert rebuilt == committed
    assert (tmp_path / "characters/moonlit-guide/guide.png").read_bytes() == (
        TRUSTED_ART_ROOT / "characters/moonlit-guide/guide.png"
    ).read_bytes()
