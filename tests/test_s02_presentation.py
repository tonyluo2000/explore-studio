"""Focused tests for the S02 (M02) Nova V2 art, animation, VFX, and overlays.

These assert semantic render operations and pure state, not screenshot bytes.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import tomllib
from pathlib import Path

import pytest

import engine.scenes._classroom_trail_scene as trail_scene_module
from engine.animation import AnimationClip, Facing, SpritePose, facing_from_motion, is_blinking
from engine.assets import ImageHandle, SpriteSheetLibrary, TrustedArtCatalog
from engine.assets._trusted_art import TRUSTED_ART_ROOT
from engine.entities import Bounds, WorldObject
from engine.input import DirectionalInput, InteractionInput
from engine.rendering._classroom_ambience import (
    ANT_COUNT,
    ANT_TRAILS,
    MOTE_COUNT,
    ant_states,
    mote_states,
    reed_sway,
)
from engine.rendering._classroom_sprites import (
    COMPASS_HALO_SHEET_ID,
    COMPASS_NEEDLE_SHEET_ID,
    COMPASS_SHEET_ID,
    CRYSTAL_LANTERN_QUALIFIED_ID,
    MOON_COMPASS_QUALIFIED_ID,
    NOVA_QUALIFIED_ID,
    PIXEL_QUALIFIED_ID,
    SPRITE_SHEET_IDS,
    classroom_sprite_pose,
    draw_classroom_sprite,
)
from engine.rendering._trail_presentation import (
    BUBBLE_DURATION,
    CELEBRATION_DURATION,
    HUD_BOTTOM,
    MAX_BURSTS,
    NOVA_STRIDE,
    NOVA_WALK,
    TrailPresentation,
    nova_visible_rect,
    place_panel,
    wrap_text,
)
from engine.scenes import ClassroomTrailObject
from explore.curriculum import MISSION_02_ID, MISSION_06_ID
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
PIXEL_GREETING = "Beep! I'm Pixel. I can't do much yet, but I'm very curious."
STEP = 1 / 60
STILL = DirectionalInput()
NO_E = InteractionInput()
E = InteractionInput(interact_pressed=True)
ANYWHERE = Bounds(min_x=-1e6, min_y=-1e6, max_x=1e6, max_y=1e6)


class GameRenderer:
    """Records every operation the full Trail renderer supports."""

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

    def measure_text(self, text: str, font_size: int) -> tuple[int, int]:
        return len(text) * font_size // 2, font_size

    def draw_sprite_frame(self, asset_id: str, row: str, column: str, *values, **options) -> bool:  # type: ignore[no-untyped-def]
        if not self.trusted_art:
            return False
        self._record("sprite", (asset_id, row, column, *values, options))
        return True

    def kinds(self) -> list[str]:
        return [kind for kind, _ in self.operations]

    @property
    def text(self) -> list[str]:
        return [str(values[0]) for kind, values in self.operations if kind == "text"]

    def sprites(self) -> dict[str, tuple[object, ...]]:
        return {str(values[0]): values for kind, values in self.operations if kind == "sprite"}


def _scene(renderer: object, *, mission_id: str | None = MISSION_02_ID, package_roots=S02_PACKAGES):  # type: ignore[no-untyped-def]
    planned = plan_local_classroom_trail(package_roots, player_qualified_id=NOVA_QUALIFIED_ID)
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=mission_id)
    scene.enter()
    return scene


def _moved_compass(tmp_path: Path, x: int, y: int) -> tuple[Path, ...]:
    compass = tmp_path / "moon-compass"
    shutil.copytree(S02_PACKAGES[-1], compass)
    source = compass / "objects" / "compass.yaml"
    source.write_text(source.read_text().replace("x: 240", f"x: {x}").replace("y: 180", f"y: {y}"))
    return (*S02_PACKAGES[:-1], compass)


def _run(scene, seconds: float, directions: DirectionalInput = STILL) -> None:  # type: ignore[no-untyped-def]
    for _ in range(round(seconds / STEP)):
        scene.update(directions, NO_E, STEP)


def _teleport_near(scene, qualified_id: str) -> None:  # type: ignore[no-untyped-def]
    target = next(
        item.world_object if hasattr(item, "world_object") else item.character
        for item in (*scene.objects, *scene.npcs)
        if item.qualified_id == qualified_id
    )
    scene.player.move(target.x - scene.player.x_float, target.y - scene.player.y_float, ANYWHERE)


def _geometry(scene):  # type: ignore[no-untyped-def]
    return tuple(
        (entity.x, entity.y, entity.width, entity.height)
        for entity in (
            scene.player,
            *(npc.character for npc in scene.npcs),
            *(item.world_object for item in scene.objects),
        )
    )


# ---------------------------------------------------------------------------
# Trusted asset pipeline
# ---------------------------------------------------------------------------


class FakeDecoder:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.decoded = 0
        self.crops: list[tuple[object, ...]] = []

    def decode_image(self, data: bytes) -> ImageHandle:
        self.decoded += 1
        if self.fail:
            raise ValueError("corrupt image")
        return ImageHandle(8192, 8192, data)

    def crop_image(self, image, x, y, width, height, out_width, out_height, flip_x):  # type: ignore[no-untyped-def]
        self.crops.append((x, y, width, height, out_width, out_height, flip_x))
        return ImageHandle(out_width, out_height, (x, y, flip_x))


TRUSTED_SCENERY_IDS = {
    "scenery/moon-meadow",
    "scenery/moon-meadow-foreground",
    COMPASS_SHEET_ID,
    COMPASS_NEEDLE_SHEET_ID,
    COMPASS_HALO_SHEET_ID,
    "ambient/reeds",
}


def test_manifest_lists_every_trusted_sheet_with_matching_digests() -> None:
    manifest = json.loads((TRUSTED_ART_ROOT / "manifest.json").read_text())
    assert set(manifest["assets"]) == set(SPRITE_SHEET_IDS.values()) | TRUSTED_SCENERY_IDS
    for entry in manifest["assets"].values():
        data = (TRUSTED_ART_ROOT / entry["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_trusted_art_declares_the_package_colors_it_was_drawn_for() -> None:
    from explore._colors import resolve_color

    catalog = TrustedArtCatalog()
    assert catalog.spec("characters/nova").accent == resolve_color("gold")
    assert catalog.spec("characters/pixel").accent == resolve_color("blue")
    assert catalog.spec("objects/crystal-lantern").accent == resolve_color("yellow")


def test_sheets_decode_once_and_frames_are_cached() -> None:
    decoder = FakeDecoder()
    library = SpriteSheetLibrary(decoder)

    first = library.frame("characters/nova", "right", "walk-2", 100, 100, flip_x=True)
    again = library.frame("characters/nova", "right", "walk-2", 100, 100, flip_x=True)
    other = library.frame("characters/nova", "down", "idle-0", 100, 100)

    assert first is again and first is not None and other is not None
    assert decoder.decoded == 1
    assert decoder.crops == [
        (700, 200, 100, 100, 100, 100, True),
        (0, 0, 100, 100, 100, 100, False),
    ]
    assert library.frame("characters/nova", "sideways", "idle-0", 100, 100) is None
    assert library.frame("characters/nova", "down", "dance", 100, 100) is None
    assert library.frame("characters/unknown", "down", "idle-0", 100, 100) is None


def test_frame_cache_is_bounded() -> None:
    from engine.assets._sprite_sheets import MAX_CACHED_FRAMES

    library = SpriteSheetLibrary(FakeDecoder())
    for size in range(1, MAX_CACHED_FRAMES + 40):
        library.frame("characters/pixel", "idle", "idle-0", size, size)
    assert library.cached_frame_count <= MAX_CACHED_FRAMES


def _copied_catalog(tmp_path: Path) -> Path:
    root = tmp_path / "trusted"
    shutil.copytree(TRUSTED_ART_ROOT, root)
    return root


def test_tampered_sheet_fails_its_digest_and_reads_as_unavailable(tmp_path: Path) -> None:
    root = _copied_catalog(tmp_path)
    sheet = root / "characters/nova/nova.png"
    sheet.write_bytes(sheet.read_bytes() + b"tampered")
    decoder = FakeDecoder()
    library = SpriteSheetLibrary(decoder, TrustedArtCatalog(root))

    assert library.catalog.read_verified("characters/nova") is None
    assert library.frame("characters/nova", "down", "idle-0", 100, 100) is None
    assert decoder.decoded == 0
    assert library.frame("characters/pixel", "idle", "idle-0", 100, 100) is not None


def test_missing_sheet_and_missing_manifest_fall_back_safely(tmp_path: Path) -> None:
    root = _copied_catalog(tmp_path)
    (root / "characters/pixel/pixel.png").unlink()
    assert TrustedArtCatalog(root).read_verified("characters/pixel") is None
    (root / "manifest.json").unlink()
    assert TrustedArtCatalog(root).asset_ids() == ()
    assert TrustedArtCatalog(root).read_verified("characters/nova") is None


@pytest.mark.parametrize(
    "mutation",
    (
        lambda manifest: manifest.update(schema_version=99),
        lambda manifest: manifest["assets"]["characters/nova"].update(file="../../../evil.png"),
        lambda manifest: manifest["assets"]["characters/nova"].update(sha256="not-a-digest"),
        lambda manifest: manifest["assets"]["characters/nova"].update(frame_width=0),
    ),
)
def test_malformed_or_escaping_manifest_entries_are_rejected(tmp_path: Path, mutation) -> None:  # type: ignore[no-untyped-def]
    root = _copied_catalog(tmp_path)
    manifest = json.loads((root / "manifest.json").read_text())
    mutation(manifest)
    (root / "manifest.json").write_text(json.dumps(manifest))
    (tmp_path / "evil.png").write_bytes(b"\x89PNG")

    assert TrustedArtCatalog(root).read_verified("characters/nova") is None


def test_undecodable_sheet_is_attempted_once_then_remembered() -> None:
    decoder = FakeDecoder(fail=True)
    library = SpriteSheetLibrary(decoder)

    for _ in range(5):
        assert library.frame("characters/nova", "down", "idle-0", 100, 100) is None
    assert decoder.decoded == 1


def test_platform_decodes_real_sheets_with_transparency() -> None:
    import pygame

    from engine._config import Config
    from engine._platform import Platform

    platform = Platform(Config())
    platform.initialize()
    try:
        library = SpriteSheetLibrary(platform)
        frame = library.frame("characters/nova", "down", "idle-0", 100, 100)
        mirrored = library.frame("characters/nova", "right", "walk-1", 100, 100, flip_x=True)
        scaled = library.frame("objects/crystal-lantern", "glow", "flicker-2", 160, 120)
        assert frame is not None and mirrored is not None and scaled is not None
        surface = frame.native
        assert isinstance(surface, pygame.Surface)
        assert (frame.width, frame.height) == (100, 100)
        assert (scaled.width, scaled.height) == (160, 120)
        assert surface.get_at((1, 1)).a == 0  # transparent corner
        assert surface.get_at((48, 60)).a == 255  # opaque suit
        platform.draw_image(frame, 10, 10)
        with pytest.raises(ValueError, match="could not be decoded"):
            platform.decode_image(b"not a png")
    finally:
        platform.shutdown()


def test_renderer_refuses_art_drawn_for_a_different_accent() -> None:
    from engine.rendering import Renderer

    class Platform:
        def __init__(self) -> None:
            self.images: list[object] = []

        decode_image = FakeDecoder().decode_image
        crop_image = FakeDecoder().crop_image

        def draw_image(self, image, x, y) -> None:  # type: ignore[no-untyped-def]
            self.images.append((image, x, y))

    platform = Platform()
    renderer = Renderer(platform)  # type: ignore[arg-type]

    assert renderer.draw_sprite_frame(
        "characters/nova", "down", "idle-0", 430, 270, 100, 100, accent=(255, 200, 50)
    )
    assert not renderer.draw_sprite_frame(
        "characters/nova", "down", "idle-0", 430, 270, 100, 100, accent=(1, 2, 3)
    )
    assert len(platform.images) == 1


def test_trusted_art_ships_in_the_runtime_distribution() -> None:
    configuration = tomllib.loads((REPO / "pyproject.toml").read_text())
    patterns = configuration["tool"]["setuptools"]["package-data"]["engine"]
    assert "assets/trusted/manifest.json" in patterns
    assert "assets/trusted/**/*.png" in patterns
    engine_root = REPO / "engine"
    shipped = {
        path.relative_to(engine_root).as_posix()
        for pattern in patterns
        for path in engine_root.glob(pattern)
    }
    manifest = json.loads((TRUSTED_ART_ROOT / "manifest.json").read_text())
    assert {f"assets/trusted/{entry['file']}" for entry in manifest["assets"].values()} <= shipped


# ---------------------------------------------------------------------------
# Animation selection
# ---------------------------------------------------------------------------


def test_clip_frame_selection_is_deterministic() -> None:
    clip = AnimationClip("idle", ("a", "b", "c"), 0.5)
    assert [clip.frame_at(t) for t in (0.0, 0.49, 0.5, 1.2, 1.5, 3.1)] == [
        "a",
        "a",
        "b",
        "c",
        "a",
        "a",
    ]
    once = AnimationClip("greet", ("a", "b"), 0.2, loop=False)
    assert once.frame_at(5.0) == "b"
    assert clip.frame_at(float("nan")) == "a"
    assert len(NOVA_WALK.frames) == 8
    assert [NOVA_WALK.frame_at_distance(d, 7.5) for d in (0, 7, 7.5, 16, 23, 60, 61)] == [
        "walk-0",
        "walk-0",
        "walk-1",
        "walk-2",
        "walk-3",
        "walk-0",
        "walk-0",
    ]
    # Eight frames per 60 px cycle: the same pace over the ground as before.
    assert NOVA_STRIDE * len(NOVA_WALK.frames) == 60


def test_facing_follows_the_dominant_motion_and_holds_when_still() -> None:
    assert facing_from_motion(3, 1, Facing.DOWN) is Facing.RIGHT
    assert facing_from_motion(-3, 1, Facing.DOWN) is Facing.LEFT
    assert facing_from_motion(1, -3, Facing.DOWN) is Facing.UP
    assert facing_from_motion(0, 2, Facing.UP) is Facing.DOWN
    assert facing_from_motion(2, 2, Facing.UP) is Facing.RIGHT
    assert facing_from_motion(0, 0, Facing.LEFT) is Facing.LEFT
    assert is_blinking(0.05, period=3, duration=0.1)
    assert not is_blinking(0.5, period=3, duration=0.1)


@pytest.mark.parametrize(
    ("directions", "row", "flip"),
    (
        (DirectionalInput(right=True), "right", False),
        (DirectionalInput(left=True), "right", True),
        (DirectionalInput(up=True), "up", False),
        (DirectionalInput(down=True), "down", False),
    ),
)
def test_nova_faces_its_movement_and_walks_with_changing_frames(directions, row, flip) -> None:  # type: ignore[no-untyped-def]
    renderer = GameRenderer()
    scene = _scene(renderer)
    columns = set()
    for _ in range(40):
        scene.update(directions, NO_E, STEP)
        renderer.operations.clear()
        scene.render()
        nova = renderer.sprites()["characters/nova"]
        assert nova[1] == row and nova[-1]["flip_x"] is flip
        columns.add(nova[2])
    assert columns == set(NOVA_WALK.frames)  # animates, not slides

    _run(scene, 1.0)
    renderer.operations.clear()
    scene.render()
    nova = renderer.sprites()["characters/nova"]
    assert nova[1] == row and nova[2] in {"idle-0", "idle-1", "idle-2", "idle-3", "blink"}


def test_idle_nova_breathes_and_blinks_over_time() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    columns = set()
    for _ in range(round(5 / STEP)):
        scene.update(STILL, NO_E, STEP)
        renderer.operations.clear()
        scene.render()
        columns.add(renderer.sprites()["characters/nova"][2])
    assert {"idle-0", "idle-1", "idle-2", "idle-3", "blink"} <= columns


def test_sprite_frames_fill_the_unchanged_entity_bounds() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    _run(scene, 0.5, DirectionalInput(right=True))
    renderer.operations.clear()
    scene.render()
    sprites = renderer.sprites()
    player = scene.player
    assert sprites["characters/nova"][3:7] == (player.x, player.y, 100, 100)
    pixel = scene.npcs[0].character
    assert sprites["characters/pixel"][3:7] == (pixel.x, pixel.y, 100, 100)
    lantern = next(
        item.world_object
        for item in scene.objects
        if item.qualified_id == CRYSTAL_LANTERN_QUALIFIED_ID
    )
    assert sprites["objects/crystal-lantern"][3:7] == (lantern.x, lantern.y, 80, 60)


def test_animation_never_changes_gameplay_geometry_or_state() -> None:
    animated = _scene(GameRenderer())
    plain = _scene(GameRenderer())
    plain._presentation.active = False  # type: ignore[attr-defined]
    script = (
        [DirectionalInput(right=True)] * 30
        + [STILL] * 300
        + [DirectionalInput(left=True, up=True)] * 50
    )
    for directions in script:
        for scene in (animated, plain):
            scene.update(directions, NO_E, STEP)
            scene.render()
        assert _geometry(animated) == _geometry(plain)
        assert animated.target_qualified_id == plain.target_qualified_id
    assert (animated.player.x_float, animated.player.y_float) == (
        plain.player.x_float,
        plain.player.y_float,
    )
    assert animated.visited_qualified_ids == plain.visited_qualified_ids == frozenset()


def test_posed_sprite_falls_back_to_procedural_art_when_frames_are_unavailable() -> None:
    renderer = GameRenderer(trusted_art=False)
    pose = SpritePose(row="right", column="walk-0", flip_x=True, bob=1, stride=1)

    with classroom_sprite_pose(pose):
        assert draw_classroom_sprite(
            renderer, NOVA_QUALIFIED_ID, 300, 200, 100, 100, (255, 200, 50)
        )
    kinds = set(renderer.kinds())
    assert {"rect", "circle", "polygon"} <= kinds and "sprite" not in kinds
    for kind, values in renderer.operations:
        if kind == "rect":
            x, y, width, height = values[:4]  # type: ignore[misc]
            assert x >= 300 and x + width <= 400 and y >= 200 and y + height <= 300


def test_a_recolored_explorer_uses_procedural_art_instead_of_mismatched_art() -> None:
    from engine.rendering import Renderer

    class Platform:
        decode_image = FakeDecoder().decode_image
        crop_image = FakeDecoder().crop_image

        def draw_image(self, *values: object) -> None:
            raise AssertionError("mismatched art must not be drawn")

        def draw_rect(self, *values: object) -> None:
            pass

        draw_circle = draw_line = draw_polygon = draw_rect

    renderer = Renderer(Platform())  # type: ignore[arg-type]
    with classroom_sprite_pose(SpritePose(row="down", column="idle-0")):
        assert draw_classroom_sprite(renderer, NOVA_QUALIFIED_ID, 0, 0, 100, 100, (200, 0, 0))


# ---------------------------------------------------------------------------
# Pixel
# ---------------------------------------------------------------------------


def test_pixel_idles_and_reacts_to_its_greeting_without_changing_semantics() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    pixel = scene.npcs[0].character
    idle_columns = set()
    for _ in range(round(5 / STEP)):
        scene.update(STILL, NO_E, STEP)
        renderer.operations.clear()
        scene.render()
        idle_columns.add(renderer.sprites()["characters/pixel"][2])
    assert {"idle-0", "idle-1", "idle-2", "idle-3", "blink"} <= idle_columns

    assert scene.target_qualified_id == PIXEL_QUALIFIED_ID
    scene.update(STILL, E, STEP)
    greet_columns = set()
    for _ in range(40):
        scene.update(STILL, NO_E, STEP)
        renderer.operations.clear()
        scene.render()
        greet_columns.add(renderer.sprites()["characters/pixel"][2])
    assert {"greet-0", "greet-1", "greet-2"} <= greet_columns
    assert scene.visited_count == 0
    assert scene.visited_qualified_ids == frozenset()
    assert (pixel.x, pixel.y, pixel.width, pixel.height) == (480, 310, 100, 100)


def test_pixel_greeting_appears_in_a_speech_bubble_and_the_unchanged_hud() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    scene.update(STILL, E, STEP)
    renderer.operations.clear()
    scene.render()

    assert f"Pixel: {PIXEL_GREETING}" in renderer.text  # HUD line unchanged
    bubble_text = " ".join(
        text
        for text in renderer.text
        if text in PIXEL_GREETING and text not in (PIXEL_GREETING, "Pixel")
    )
    assert bubble_text == PIXEL_GREETING
    assert "Pixel" in renderer.text  # the bubble's speaker name tag
    panels = [values for kind, values in renderer.operations if kind == "panel"]
    bubble = next(values for values in panels if values[4] == (250, 248, 236))
    rect = bubble[:4]
    assert not _overlap(rect, nova_visible_rect(scene.player))
    for item in scene.objects:
        world_object = item.world_object
        assert not _overlap(
            rect, (world_object.x, world_object.y, world_object.width, world_object.height)
        )

    _run(scene, BUBBLE_DURATION + 0.1)
    renderer.operations.clear()
    scene.render()
    assert not any(text in PIXEL_GREETING for text in renderer.text[4:] if text != "Talk to Pixel")


def _overlap(first, second) -> bool:  # type: ignore[no-untyped-def]
    return (
        first[0] < second[0] + second[2]
        and second[0] < first[0] + first[2]
        and first[1] < second[1] + second[3]
        and second[1] < first[1] + first[3]
    )


def test_speech_bubble_moves_to_the_other_side_when_nova_stands_there() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    pixel = scene.npcs[0].character
    scene.player.move(pixel.x + 60 - scene.player.x_float, 0, ANYWHERE)
    scene.update(STILL, NO_E, STEP)
    assert scene.target_qualified_id == PIXEL_QUALIFIED_ID
    scene.update(STILL, E, STEP)
    renderer.operations.clear()
    scene.render()
    bubble = next(
        values
        for kind, values in renderer.operations
        if kind == "panel" and values[4] == (250, 248, 236)
    )
    assert not _overlap(bubble[:4], nova_visible_rect(scene.player))


# ---------------------------------------------------------------------------
# Living world
# ---------------------------------------------------------------------------


def test_ambient_counts_are_fixed_and_bounded() -> None:
    assert ANT_COUNT == 9 and MOTE_COUNT == 10
    for clock in (0.0, 1.7, 33.3, 900.0, 86_400.0):
        ants = ant_states(clock)
        motes = mote_states(clock)
        assert len(ants) == ANT_COUNT and len(motes) == MOTE_COUNT
        for ant in ants:
            assert 570 <= ant.x <= 880 and 460 <= ant.y <= 530
        for x, y, brightness in motes:
            assert 0 <= x <= 960 and HUD_BOTTOM <= y <= 640 and 0 <= brightness <= 1


def test_ants_really_crawl_along_their_trails() -> None:
    before = ant_states(0.0)
    after = ant_states(2.0)
    moved = [math.dist((a.x, a.y), (b.x, b.y)) for a, b in zip(before, after, strict=True)]
    assert all(distance > 5 for distance in moved)
    assert ant_states(2.0) == after  # deterministic
    assert sum(trail.ants for trail in ANT_TRAILS) == ANT_COUNT
    assert reed_sway(0.0, 100) != reed_sway(1.0, 100)


def test_world_keeps_moving_while_nova_stands_still_for_five_seconds() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    frames = []
    for second in range(6):
        _run(scene, 1.0 if second else 0.0)
        renderer.operations.clear()
        scene.render()
        frames.append(list(renderer.operations))
    assert (scene.player.x, scene.player.y) == (430, 270)
    for earlier, later in zip(frames, frames[1:], strict=False):
        assert earlier != later


def test_ambience_draws_nothing_that_touches_gameplay_and_no_rectangles() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    before = _geometry(scene)
    presentation = scene._presentation  # type: ignore[attr-defined]
    presentation.clock = 12.5
    presentation.draw_ground(renderer)
    presentation.draw_overlay(renderer, scene)
    assert _geometry(scene) == before
    assert "rect" not in renderer.kinds()


def test_frame_cost_is_bounded() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    _run(scene, 3.0)
    renderer.operations.clear()
    scene.render()
    assert len(renderer.operations) < 900
    assert renderer.kinds().count("glow") < 40


# ---------------------------------------------------------------------------
# Moon Compass and Crystal Lantern
# ---------------------------------------------------------------------------


def _compass_effects(renderer: GameRenderer, x: int, y: int, clock: float) -> list:  # type: ignore[type-arg]
    presentation = TrailPresentation(MISSION_02_ID)
    presentation.clock = clock
    compass = WorldObject(name="Moon Compass", x=x, y=y, width=80, height=60, color=(140, 50, 180))
    presentation.draw_under(renderer, MOON_COMPASS_QUALIFIED_ID, compass, compass.color)
    with classroom_sprite_pose(presentation.pose_for(MOON_COMPASS_QUALIFIED_ID)):
        draw_classroom_sprite(renderer, MOON_COMPASS_QUALIFIED_ID, x, y, 80, 60, compass.color)
    presentation.draw_over(renderer, MOON_COMPASS_QUALIFIED_ID, compass, compass.color)
    return renderer.operations


def _shift(value: object, dx: int, dy: int) -> object:
    if isinstance(value, tuple) and len(value) == 2 and all(isinstance(v, int) for v in value):
        return (value[0] + dx, value[1] + dy)
    if isinstance(value, tuple):
        return tuple(_shift(item, dx, dy) for item in value)
    return value


def test_compass_effects_travel_exactly_with_student_coordinates() -> None:
    canonical = _compass_effects(GameRenderer(), 240, 180, clock=4.2)
    moved = _compass_effects(GameRenderer(), 690, 360, clock=4.2)
    kinds = {kind for kind, _ in canonical}
    assert {"glow", "shadow", "polygon"} <= kinds
    assert len(canonical) == len(moved)
    assert "sprite" in kinds  # the layered trusted Compass art
    for (kind, before), (_, after) in zip(canonical, moved, strict=True):
        if kind == "sprite":
            assert after[:3] == before[:3]  # same sheet, row, and frame
            assert after[3:5] == (before[3] + 450, before[4] + 180)  # type: ignore[operator]
            assert after[5:] == before[5:]
        elif kind == "polygon":
            assert after[0] == _shift(before[0], 450, 180)
        elif kind == "line":
            assert after[:4] == (before[0] + 450, before[1] + 180, before[2] + 450, before[3] + 180)
        else:
            assert after[:2] == (before[0] + 450, before[1] + 180)  # type: ignore[operator]
            assert after[2:] == before[2:]


def test_compass_needle_and_aura_animate_over_time() -> None:
    early = _compass_effects(GameRenderer(), 240, 180, clock=0.3)
    later = _compass_effects(GameRenderer(), 240, 180, clock=1.4)
    assert early != later


def test_scene_compass_effects_follow_the_moved_package(tmp_path: Path) -> None:
    renderer = GameRenderer()
    scene = _scene(renderer, package_roots=_moved_compass(tmp_path, 690, 360))
    scene.render()
    glows = [values for kind, values in renderer.operations if kind == "glow"]
    assert any(values[:2] == (730, 387) for values in glows)
    assert not any(values[:2] == (280, 207) for values in glows)


def test_lantern_reads_as_the_destination_and_flares_when_inspected() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    scene.render()
    lantern_glows = [
        values for kind, values in renderer.operations if kind == "glow" and values[2] >= 80
    ]
    assert lantern_glows  # warm light around the Lantern
    presentation = scene._presentation  # type: ignore[attr-defined]
    _teleport_near(scene, CRYSTAL_LANTERN_QUALIFIED_ID)
    scene.update(STILL, NO_E, STEP)
    assert scene.target_qualified_id == CRYSTAL_LANTERN_QUALIFIED_ID
    assert presentation._flare_strength(CRYSTAL_LANTERN_QUALIFIED_ID) == 0
    scene.update(STILL, E, STEP)
    assert presentation._flare_strength(CRYSTAL_LANTERN_QUALIFIED_ID) > 0.9
    assert scene.visited_qualified_ids == {CRYSTAL_LANTERN_QUALIFIED_ID}
    lantern = next(
        item.world_object
        for item in scene.objects
        if item.qualified_id == CRYSTAL_LANTERN_QUALIFIED_ID
    )
    assert (lantern.x, lantern.y) == (120, 460)


def test_discovery_label_appears_on_first_compass_visit_only() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    _teleport_near(scene, MOON_COMPASS_QUALIFIED_ID)
    scene.update(STILL, E, STEP)
    renderer.operations.clear()
    scene.render()
    assert "Moon Compass discovered!" in renderer.text
    assert scene.visited_count == 1

    _run(scene, 2.0)
    scene.update(STILL, E, STEP)
    renderer.operations.clear()
    scene.render()
    assert "Moon Compass discovered!" not in renderer.text
    assert scene.visited_count == 1
    presentation = scene._presentation  # type: ignore[attr-defined]
    assert len(presentation.bursts) <= MAX_BURSTS


# ---------------------------------------------------------------------------
# Prompts, completion, ordering, and M02-only rules
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("qualified_id", "prompt"),
    (
        (PIXEL_QUALIFIED_ID, "Talk to Pixel"),
        (MOON_COMPASS_QUALIFIED_ID, "Inspect Moon Compass"),
        (CRYSTAL_LANTERN_QUALIFIED_ID, "Inspect Crystal Lantern"),
    ),
)
def test_prompts_appear_only_for_the_valid_nearby_target(qualified_id: str, prompt: str) -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    _teleport_near(scene, qualified_id)
    scene.update(STILL, NO_E, STEP)
    assert scene.target_qualified_id == qualified_id
    renderer.operations.clear()
    scene.render()
    assert prompt in renderer.text and "E" in renderer.text
    assert sum(text.startswith(("Talk to", "Inspect")) for text in renderer.text) == 1

    scene.player.move(900 - scene.player.x_float, 540 - scene.player.y_float, ANYWHERE)
    scene.update(STILL, NO_E, STEP)
    assert scene.target_qualified_id is None
    renderer.operations.clear()
    scene.render()
    assert not any(text.startswith(("Talk to", "Inspect")) for text in renderer.text)


def test_prompts_never_change_interaction_logic() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    plain = _scene(GameRenderer())
    plain._presentation.active = False  # type: ignore[attr-defined]
    for current in (scene, plain):
        _teleport_near(current, MOON_COMPASS_QUALIFIED_ID)
        current.update(STILL, NO_E, STEP)
        current.update(STILL, E, STEP)
    assert scene.visited_qualified_ids == plain.visited_qualified_ids
    assert scene.target_qualified_id == plain.target_qualified_id


def test_prompt_panels_stay_on_screen_below_the_hud_and_off_nova() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    for qualified_id in (
        PIXEL_QUALIFIED_ID,
        MOON_COMPASS_QUALIFIED_ID,
        CRYSTAL_LANTERN_QUALIFIED_ID,
    ):
        _teleport_near(scene, qualified_id)
        scene.update(STILL, NO_E, STEP)
        renderer.operations.clear()
        scene.render()
        panel = next(values for kind, values in renderer.operations if kind == "panel")
        x, y, width, height = panel[:4]  # type: ignore[misc]
        assert x >= 0 and y >= HUD_BOTTOM and x + width <= 960 and y + height <= 640


def test_place_panel_prefers_free_space_and_clamps_as_a_last_resort() -> None:
    avoid = ((100, 200, 100, 100),)
    assert place_panel((50, 20), ((120, 220), (300, 220)), avoid) == (300, 220, 50, 20)
    assert place_panel((50, 20), ((-40, 10),), ()) == (4, HUD_BOTTOM + 2, 50, 20)
    lines = wrap_text("one two three four five", 40, lambda text: (len(text) * 5, 10))
    assert lines == ("one two", "three", "four", "five")


def test_mission_completion_is_unchanged_and_celebrated_briefly() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    for qualified_id in (MOON_COMPASS_QUALIFIED_ID, CRYSTAL_LANTERN_QUALIFIED_ID):
        _teleport_near(scene, qualified_id)
        scene.update(STILL, NO_E, STEP)
        scene.update(STILL, E, STEP)
    assert scene.visited_count == 2 and scene.mission_is_complete and scene.is_complete
    renderer.operations.clear()
    scene.render()
    assert renderer.text[0] == "Visited 2 / 2"
    assert "Mission state: Complete" in renderer.text
    assert "Trail complete!" in renderer.text
    assert "Mission complete!" in renderer.text
    confetti = [values for kind, values in renderer.operations if kind == "polygon"]
    assert confetti

    _run(scene, CELEBRATION_DURATION + 0.1)
    renderer.operations.clear()
    scene.render()
    assert "Mission complete!" not in renderer.text
    assert "Trail complete!" in renderer.text  # the HUD's own text is unchanged


def test_celebration_does_not_repeat_on_later_interactions() -> None:
    scene = _scene(GameRenderer())
    for qualified_id in (MOON_COMPASS_QUALIFIED_ID, CRYSTAL_LANTERN_QUALIFIED_ID):
        _teleport_near(scene, qualified_id)
        scene.update(STILL, NO_E, STEP)
        scene.update(STILL, E, STEP)
    presentation = scene._presentation  # type: ignore[attr-defined]
    started = presentation.celebration_start
    _run(scene, 1.0)
    scene.update(STILL, E, STEP)
    assert presentation.celebration_start == started


def test_render_order_keeps_hud_text_first_after_all_shapes() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    scene.update(STILL, E, STEP)  # Pixel greeting: bubble plus HUD
    renderer.operations.clear()
    scene.render()
    kinds = renderer.kinds()
    first_text = kinds.index("text")
    assert set(kinds[first_text:]) == {"text"}
    assert renderer.text[:4] == [
        "Visited 0 / 2",
        "Mission: Create Your First Object",
        scene.mission.instructions,
        "Mission state: Incomplete",
    ]
    sprite_order = [values[0] for kind, values in renderer.operations if kind == "sprite"]
    # The illustrated plate is first, the framing foreground comes after Nova.
    assert sprite_order[0] == "scenery/moon-meadow"
    assert sprite_order[-1] == "scenery/moon-meadow-foreground"
    entities = [asset for asset in sprite_order if asset.startswith(("objects/", "characters/"))]
    assert entities == [
        "objects/crystal-lantern",
        COMPASS_HALO_SHEET_ID,
        COMPASS_SHEET_ID,
        COMPASS_SHEET_ID,
        COMPASS_NEEDLE_SHEET_ID,
        COMPASS_SHEET_ID,
        "characters/pixel",
        "characters/nova",
    ]
    first_entity = next(
        index
        for index, (kind, values) in enumerate(renderer.operations)
        if kind == "sprite" and str(values[0]).startswith(("objects/", "characters/"))
    )
    assert 0 < kinds.index("shadow") < first_entity  # ground and shadows beneath entities


@pytest.mark.parametrize("mission_id", (MISSION_06_ID, None))
def test_other_missions_are_untouched_by_the_presentation_layer(mission_id: str | None) -> None:
    # None is a Trail launched without --mission-id: M01 rules, plain Trail.
    renderer = GameRenderer()
    scene = _scene(renderer, mission_id=mission_id)
    scene.update(STILL, NO_E, STEP)
    renderer.operations.clear()
    scene.render()
    first = list(renderer.operations)
    _run(scene, 3.0)
    renderer.operations.clear()
    scene.render()
    assert renderer.operations == first
    assert not {"glow", "shadow", "panel", "sprite"} & set(renderer.kinds())
    presentation = scene._presentation  # type: ignore[attr-defined]
    assert not presentation.active and presentation.pose_for(NOVA_QUALIFIED_ID) is None


def test_unknown_m02_entity_keeps_the_rectangle_fallback_with_effects_on() -> None:
    renderer = GameRenderer()
    scene = _scene(renderer)
    unknown = ClassroomTrailObject(
        "student-package:new-object",
        WorldObject(name="New", x=700, y=420, width=80, height=60, color=(10, 20, 30)),
    )
    scene._objects = (*scene._objects, unknown)  # type: ignore[attr-defined]
    _run(scene, 1.0)
    scene.render()
    assert ("rect", (700, 420, 80, 60, (10, 20, 30))) in renderer.operations


def test_presentation_failures_never_reach_gameplay(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    renderer = GameRenderer()
    scene = _scene(renderer)

    def explode(*args: object) -> None:
        raise RuntimeError("simulated effect failure")

    monkeypatch.setattr(TrailPresentation, "_observe", explode)
    monkeypatch.setattr(trail_scene_module.TrailPresentation, "_draw_under", explode)
    scene.update(STILL, E, STEP)
    scene.render()
    assert scene.spoken_npc_ids == {PIXEL_QUALIFIED_ID}
    assert "Visited 0 / 2" in renderer.text


def test_same_inputs_render_the_same_frames() -> None:
    first, second = GameRenderer(), GameRenderer()
    scenes = (_scene(first), _scene(second))
    for directions in [DirectionalInput(right=True)] * 20 + [STILL] * 40:
        for scene in scenes:
            scene.update(directions, NO_E, STEP)
            scene.render()
    assert first.operations == second.operations
