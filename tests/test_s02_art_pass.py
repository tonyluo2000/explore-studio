"""Focused tests for the S02 art-first pass: the illustrated Moon Meadow.

They check the trusted asset contract (grids, digests, opacity, packaging),
the tinted Compass layers and their translation invariant, the foreground's
keep-out zone, the HUD panel's parity with the unchanged HUD layout, safe
fallback, and that frames are decoded and cut once rather than per frame.
They assert structure and semantics, not exact pixel colors.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

import engine.scenes._classroom_trail_scene as trail_scene_module
from engine.assets import SpriteSheetLibrary, TrustedArtCatalog
from engine.assets._sprite_sheets import MAX_CACHED_FRAMES
from engine.assets._trusted_art import TRUSTED_ART_ROOT
from engine.input import DirectionalInput, InteractionInput
from engine.rendering._classroom_ambience import (
    REED_CLUMPS,
    REED_SHEET,
    draw_ground_life,
    reed_column,
    shrine_flame_flicker,
)
from engine.rendering._classroom_environment import (
    MEADOW_BACKDROP,
    MEADOW_FOREGROUND,
    draw_classroom_backdrop,
    illustrated_backdrop_available,
)
from engine.rendering._classroom_sprites import (
    COMPASS_NEEDLE_SHEET_ID,
    COMPASS_SHEET_ID,
    MOON_COMPASS_QUALIFIED_ID,
    NOVA_QUALIFIED_ID,
    classroom_sprite_pose,
    compass_needle_column,
    draw_classroom_sprite,
)
from engine.rendering._meadow_layout import BRIGHT_STARS, SHRINE_FLAMES
from engine.rendering._trail_presentation import (
    HUD_FONT,
    HUD_ROWS_Y,
    HUD_TEXT_X,
    TrailPresentation,
)
from explore.curriculum import MISSION_01_ID, MISSION_02_ID
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)

REPO = Path(__file__).resolve().parents[1]
S02_PACKAGES = (
    REPO / "examples/explorer-packages/nova-character",
    REPO / "examples/explorer-packages/pixel-companion",
    REPO / "examples/explorer-packages/crystal-lantern",
    REPO / "lessons/sessions/s02/student/explorer-package",
)
STEP = 1 / 60
STILL = DirectionalInput()
NO_E = InteractionInput()
PURPLE = (140, 50, 180)


class ArtRenderer:
    """Records drawing operations, including trusted frames and panels."""

    def __init__(self, *, trusted_art: bool = True) -> None:
        self.operations: list[tuple[str, tuple[object, ...]]] = []
        self.trusted_art = trusted_art

    def _record(self, kind: str, values: tuple[object, ...]) -> None:
        self.operations.append((kind, values))

    def draw_rect(self, *values: object) -> None:
        self._record("rect", values)

    def draw_circle(self, *values: object) -> None:
        self._record("circle", values)

    def draw_line(self, *values: object) -> None:
        self._record("line", values)

    def draw_polygon(self, *values: object) -> None:
        self._record("polygon", values)

    def draw_text(self, *values: object) -> None:
        self._record("text", values)

    def draw_glow(self, *values: object) -> None:
        self._record("glow", values)

    def draw_soft_ellipse(self, *values: object) -> None:
        self._record("shadow", values)

    def draw_rounded_rect(self, *values: object) -> None:
        self._record("panel", values)

    def draw_translucent_panel(self, *values: object) -> None:
        self._record("translucent", values)

    def measure_text(self, text: str, font_size: int) -> tuple[int, int]:
        return len(text) * font_size // 2, font_size

    def draw_sprite_frame(self, asset_id: str, row: str, column: str, *values, **options) -> bool:  # type: ignore[no-untyped-def]
        if not self.trusted_art:
            return False
        self._record("sprite", (asset_id, row, column, *values, options))
        return True

    def kinds(self) -> list[str]:
        return [kind for kind, _ in self.operations]

    def sprite_ops(self, asset_id: str) -> list[tuple[object, ...]]:
        return [
            values for kind, values in self.operations if kind == "sprite" and values[0] == asset_id
        ]


def _scene(renderer: object, *, mission_id: str = MISSION_02_ID, package_roots=S02_PACKAGES):  # type: ignore[no-untyped-def]
    planned = plan_local_classroom_trail(package_roots, player_qualified_id=NOVA_QUALIFIED_ID)
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=mission_id)
    scene.enter()
    return scene


def _manifest() -> dict[str, dict[str, object]]:
    return json.loads((TRUSTED_ART_ROOT / "manifest.json").read_text())["assets"]


@pytest.fixture
def platform():  # type: ignore[no-untyped-def]
    from engine._config import Config
    from engine._platform import Platform

    instance = Platform(Config())
    instance.initialize()
    yield instance
    instance.shutdown()


# ---------------------------------------------------------------------------
# Trusted asset contract
# ---------------------------------------------------------------------------


def test_every_trusted_sheet_matches_its_declared_frame_grid(platform) -> None:  # type: ignore[no-untyped-def]
    catalog = TrustedArtCatalog()
    for asset_id, entry in _manifest().items():
        data = catalog.read_verified(asset_id)
        assert data is not None, asset_id
        image = platform.decode_image(data)
        assert image.width == entry["frame_width"] * len(entry["columns"]), asset_id  # type: ignore[operator,arg-type]
        assert image.height == entry["frame_height"] * len(entry["rows"]), asset_id  # type: ignore[operator,arg-type]


def test_character_and_object_frames_map_one_to_one_onto_gameplay_boxes() -> None:
    manifest = _manifest()
    for asset_id in ("characters/nova", "characters/pixel"):
        assert (manifest[asset_id]["frame_width"], manifest[asset_id]["frame_height"]) == (100, 100)
    for asset_id in ("objects/crystal-lantern", COMPASS_SHEET_ID, COMPASS_NEEDLE_SHEET_ID):
        assert (manifest[asset_id]["frame_width"], manifest[asset_id]["frame_height"]) == (80, 60)
    for asset_id in (MEADOW_BACKDROP[0], MEADOW_FOREGROUND[0]):
        assert (manifest[asset_id]["frame_width"], manifest[asset_id]["frame_height"]) == (960, 640)
    nova = manifest["characters/nova"]
    assert nova["rows"] == ["down", "up", "right"]
    assert nova["columns"] == [
        "idle-0",
        "idle-1",
        "idle-2",
        "idle-3",
        "blink",
        *(f"walk-{index}" for index in range(8)),
    ]
    assert len(manifest[COMPASS_NEEDLE_SHEET_ID]["columns"]) == 64  # type: ignore[arg-type]


def test_meadow_plate_is_opaque_and_the_foreground_keeps_gameplay_clear(platform) -> None:  # type: ignore[no-untyped-def]
    import pygame

    library = SpriteSheetLibrary(platform)
    backdrop = library.frame(*MEADOW_BACKDROP, 960, 640)
    foreground = library.frame(*MEADOW_FOREGROUND, 960, 640)
    assert backdrop is not None and foreground is not None
    plate = backdrop.native
    assert isinstance(plate, pygame.Surface)
    assert not plate.get_flags() & pygame.SRCALPHA  # one fast opaque blit
    frame = foreground.native
    assert isinstance(frame, pygame.Surface)
    # Framing plants stay at the edges: the playable middle is fully clear.
    for x in range(60, 900, 12):
        for y in range(0, 560, 12):
            assert frame.get_at((x, y)).a == 0, (x, y)
    assert any(frame.get_at((x, 636)).a > 0 for x in range(0, 960, 8))


def test_new_trusted_art_ships_in_the_runtime_distribution() -> None:
    import tomllib

    patterns = tomllib.loads((REPO / "pyproject.toml").read_text())["tool"]["setuptools"][
        "package-data"
    ]["engine"]
    engine_root = REPO / "engine"
    shipped = {
        path.relative_to(engine_root).as_posix()
        for pattern in patterns
        for path in engine_root.glob(pattern)
    }
    for entry in _manifest().values():
        assert f"assets/trusted/{entry['file']}" in shipped


# ---------------------------------------------------------------------------
# Tinted Moon Compass
# ---------------------------------------------------------------------------


def test_compass_needle_column_covers_the_circle() -> None:
    assert compass_needle_column(0.0) == "angle-00"
    assert compass_needle_column(math.tau / 4) == "angle-16"
    assert compass_needle_column(-math.tau / 4) == "angle-48"
    assert compass_needle_column(math.tau * 3) == "angle-00"
    assert compass_needle_column(float("nan")) == "angle-00"


def _draw_compass(
    renderer: ArtRenderer, x: int, y: int, color: tuple[int, int, int], clock: float
) -> None:
    presentation = TrailPresentation(MISSION_02_ID)
    presentation.clock = clock
    with classroom_sprite_pose(presentation.pose_for(MOON_COMPASS_QUALIFIED_ID)):
        assert draw_classroom_sprite(renderer, MOON_COMPASS_QUALIFIED_ID, x, y, 80, 60, color)


def test_compass_draws_tinted_ring_body_needle_and_glass_in_its_own_box() -> None:
    renderer = ArtRenderer()
    _draw_compass(renderer, 240, 180, PURPLE, clock=2.0)
    layers = [(values[0], values[1]) for kind, values in renderer.operations if kind == "sprite"]
    assert layers == [
        (COMPASS_SHEET_ID, "ring"),
        (COMPASS_SHEET_ID, "body"),
        (COMPASS_NEEDLE_SHEET_ID, "needle"),
        (COMPASS_SHEET_ID, "glass"),
    ]
    sprites = [values for kind, values in renderer.operations if kind == "sprite"]
    assert sprites[0][-1] == {"tint": PURPLE}  # only the ring carries the student's color
    assert all(values[-1] == {} for values in sprites[1:])
    for values in sprites:
        x, y, width, height = values[3:7]  # type: ignore[misc]
        assert (x, width, height) == (240, 80, 60)
        assert 180 <= y <= 182  # a gentle hover inside the unchanged box


def test_student_color_changes_only_the_ring_tint() -> None:
    purple, gold = ArtRenderer(), ArtRenderer()
    _draw_compass(purple, 240, 180, PURPLE, clock=3.3)
    _draw_compass(gold, 240, 180, (255, 200, 50), clock=3.3)
    for (_, first), (_, second) in zip(purple.operations, gold.operations, strict=True):
        assert first[:-1] == second[:-1]
    assert purple.operations[0][1][-1] != gold.operations[0][1][-1]


def test_compass_art_and_hover_translate_exactly_with_student_coordinates() -> None:
    for clock in (0.0, 0.7, 4.2, 9.9):
        here, there = ArtRenderer(), ArtRenderer()
        _draw_compass(here, 240, 180, PURPLE, clock)
        _draw_compass(there, 690, 360, PURPLE, clock)
        for (_, before), (_, after) in zip(here.operations, there.operations, strict=True):
            assert after[:3] == before[:3]
            assert after[3:5] == (before[3] + 450, before[4] + 180)  # type: ignore[operator]


def test_compass_keeps_its_procedural_fallback_without_trusted_art() -> None:
    renderer = ArtRenderer(trusted_art=False)
    _draw_compass(renderer, 240, 180, PURPLE, clock=1.0)
    assert "sprite" not in renderer.kinds()
    assert {"circle", "polygon"} <= set(renderer.kinds())


def test_platform_tints_neutral_art_and_caches_the_result(platform) -> None:  # type: ignore[no-untyped-def]
    library = SpriteSheetLibrary(platform)
    neutral = library.frame(COMPASS_SHEET_ID, "ring", "spin-00", 80, 60)
    tinted = library.frame(COMPASS_SHEET_ID, "ring", "spin-00", 80, 60, tint=PURPLE)
    again = library.frame(COMPASS_SHEET_ID, "ring", "spin-00", 80, 60, tint=PURPLE)
    assert neutral is not None and tinted is not None and tinted is again
    # The ring's brightest band (the right side of the ring) takes the color.
    before = neutral.native.get_at((63, 27))  # type: ignore[attr-defined]
    after = tinted.native.get_at((63, 27))  # type: ignore[attr-defined]
    assert before.a == after.a > 0
    assert after.g < after.b and after.g < after.r  # purple, not grey


# ---------------------------------------------------------------------------
# Scenery, ambience, and fallback
# ---------------------------------------------------------------------------


def test_m02_backdrop_is_one_trusted_plate_with_procedural_fallback() -> None:
    renderer = ArtRenderer()
    assert draw_classroom_backdrop(renderer, MISSION_02_ID)  # type: ignore[arg-type]
    assert renderer.operations == [("sprite", (*MEADOW_BACKDROP, 0, 0, 960, 640, {}))]

    fallback = ArtRenderer(trusted_art=False)
    assert draw_classroom_backdrop(fallback, MISSION_02_ID)  # type: ignore[arg-type]
    assert "polygon" in fallback.kinds() and "sprite" not in fallback.kinds()

    other = ArtRenderer()
    assert not draw_classroom_backdrop(other, MISSION_01_ID)  # type: ignore[arg-type]
    assert other.operations == []


def test_foreground_plate_is_drawn_after_every_entity_and_before_hud_text() -> None:
    renderer = ArtRenderer()
    scene = _scene(renderer)
    scene.update(STILL, NO_E, STEP)
    renderer.operations.clear()
    scene.render()
    sprites = [values[0] for kind, values in renderer.operations if kind == "sprite"]
    assert sprites.index(MEADOW_FOREGROUND[0]) > sprites.index("characters/nova")
    kinds = renderer.kinds()
    foreground_index = next(
        index
        for index, (kind, values) in enumerate(renderer.operations)
        if kind == "sprite" and values[0] == MEADOW_FOREGROUND[0]
    )
    assert foreground_index < kinds.index("text")


def test_reed_column_maps_sway_onto_nine_frames() -> None:
    assert reed_column(0.0) == "sway-4"
    assert reed_column(-4.3) == "sway-0" and reed_column(-99.0) == "sway-0"
    assert reed_column(4.3) == "sway-8" and reed_column(99.0) == "sway-8"


def test_illustrated_ambience_animates_the_painted_scenery() -> None:
    renderer = ArtRenderer()
    draw_ground_life(renderer, 7.0, illustrated=True)
    reeds = renderer.sprite_ops(REED_SHEET)
    assert len(reeds) == len(REED_CLUMPS)
    assert all(values[5:7] == (32, 44) for values in reeds)
    glows = [values[:2] for kind, values in renderer.operations if kind == "glow"]
    assert len(glows) >= len(SHRINE_FLAMES)
    # No procedural anthill polygons: the painted plate already has the hills.
    anthills = [
        values
        for kind, values in renderer.operations
        if kind == "polygon" and len(values[0]) == 4  # type: ignore[arg-type]
    ]
    assert anthills == []
    twinkles = ArtRenderer()
    for clock in (0.5 + index * 0.37 for index in range(40)):
        draw_ground_life(twinkles, clock, illustrated=True)
    star_points = {
        (values[0][0][0], values[0][2][1])  # type: ignore[index]
        for kind, values in twinkles.operations
        if kind == "polygon" and len(values[0]) == 8  # type: ignore[arg-type]
    }
    assert any((round(x), round(y)) in star_points for x, y in BRIGHT_STARS)


def test_procedural_ambience_is_unchanged_when_the_plate_is_unavailable() -> None:
    renderer = ArtRenderer(trusted_art=False)
    draw_ground_life(renderer, 7.0, illustrated=False)
    kinds = renderer.kinds()
    assert "sprite" not in kinds and "rect" not in kinds
    assert kinds.count("polygon") >= 2  # the two procedural anthills
    assert not illustrated_backdrop_available(renderer)


def test_shrine_flame_flicker_is_bounded_and_alive() -> None:
    values = [shrine_flame_flicker(index * 0.05, 0) for index in range(200)]
    assert all(0.5 <= value <= 1.0 for value in values)
    assert len({round(value, 3) for value in values}) > 20


# ---------------------------------------------------------------------------
# HUD presentation
# ---------------------------------------------------------------------------


def test_hud_panel_mirrors_the_unchanged_hud_layout() -> None:
    assert HUD_TEXT_X == trail_scene_module._PROGRESS_X == trail_scene_module._MISSION_X
    assert HUD_ROWS_Y == (
        trail_scene_module._PROGRESS_Y,
        trail_scene_module._MISSION_TITLE_Y,
        trail_scene_module._MISSION_INSTRUCTIONS_Y,
        trail_scene_module._MISSION_STATE_Y,
    )
    assert HUD_FONT == trail_scene_module._PROGRESS_FONT_SIZE


def test_hud_panel_sits_behind_every_hud_row_and_is_drawn_before_text() -> None:
    renderer = ArtRenderer()
    scene = _scene(renderer)
    scene.update(STILL, NO_E, STEP)
    renderer.operations.clear()
    scene.render()
    panels = [values for kind, values in renderer.operations if kind == "translucent"]
    hud = next(values for values in panels if len(values[0]) == 2)  # type: ignore[arg-type]
    rects = hud[0]
    texts = [values for kind, values in renderer.operations if kind == "text"][:4]
    for text, x, y, _color, size in texts:
        width, height = renderer.measure_text(str(text), int(size))  # type: ignore[arg-type]
        assert any(
            rx <= x and ry <= y and x + width <= rx + rw and y + height <= ry + rh  # type: ignore[operator]
            for rx, ry, rw, rh in rects  # type: ignore[union-attr]
        ), text
    kinds = renderer.kinds()
    assert kinds.index("translucent") < kinds.index("text")
    # The panel hugs the text: sky beside the short rows stays open.
    short_right = max(rx + rw for rx, _, rw, rh in rects if rh > 60)  # type: ignore[union-attr]
    for point in ((short_right + 20, 30), (short_right + 20, 125)):
        assert not any(
            rx <= point[0] < rx + rw and ry <= point[1] < ry + rh
            for rx, ry, rw, rh in rects  # type: ignore[union-attr]
        ), point


def test_other_missions_get_no_hud_panel_or_scenery() -> None:
    renderer = ArtRenderer()
    scene = _scene(renderer, mission_id=MISSION_01_ID)
    scene.update(STILL, NO_E, STEP)
    renderer.operations.clear()
    scene.render()
    assert not {"translucent", "sprite", "glow"} & set(renderer.kinds())


# ---------------------------------------------------------------------------
# Caching and per-frame cost on the real platform
# ---------------------------------------------------------------------------


def test_real_trail_reads_each_sheet_once_and_caches_every_frame(platform, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from engine.rendering import Renderer

    reads: list[str] = []
    original = TrustedArtCatalog.read_verified

    def counting(self, asset_id: str):  # type: ignore[no-untyped-def]
        reads.append(asset_id)
        return original(self, asset_id)

    monkeypatch.setattr(TrustedArtCatalog, "read_verified", counting)
    renderer = Renderer(platform)
    scene = _scene(renderer)
    walk = [DirectionalInput(right=True)] * 30 + [DirectionalInput(left=True)] * 60
    for directions in walk + [STILL] * 120:
        scene.update(directions, NO_E, STEP)
        platform.clear_frame((0, 0, 0))
        scene.render()
    warmed = len(reads)
    cached = renderer.sprite_sheets.cached_frame_count
    for directions in walk + [STILL] * 60:
        scene.update(directions, NO_E, STEP)
        platform.clear_frame((0, 0, 0))
        scene.render()
    assert len(reads) == warmed == len(set(reads))  # each sheet read and verified once
    assert renderer.sprite_sheets.decode_count == len(set(reads))
    assert cached <= renderer.sprite_sheets.cached_frame_count < MAX_CACHED_FRAMES
