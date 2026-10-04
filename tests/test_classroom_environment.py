"""Focused composition tests for the S02 Classroom Trail backdrop and sprites."""

from __future__ import annotations

from pathlib import Path

import pytest

import engine.scenes._classroom_trail_scene as trail_scene_module
from engine.entities import Bounds, WorldObject
from engine.input import DirectionalInput, InteractionInput
from engine.rendering._classroom_environment import S02_MISSION_ID, draw_classroom_backdrop
from engine.rendering._classroom_sprites import (
    CRYSTAL_LANTERN_QUALIFIED_ID,
    MOON_COMPASS_QUALIFIED_ID,
    NOVA_QUALIFIED_ID,
    PIXEL_QUALIFIED_ID,
    draw_classroom_sprite,
)
from engine.scenes import ClassroomTrailObject
from explore.curriculum import MISSION_01_ID, MISSION_02_ID, MISSION_05_ID
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
PIXEL_GREETING = "Pixel: Beep! I'm Pixel. I can't do much yet, but I'm very curious."

Operation = tuple[str, tuple[object, ...]]


class _RecordingRenderer:
    def __init__(self) -> None:
        self.operations: list[Operation] = []

    def draw_rect(self, *values: object) -> None:
        self.operations.append(("rect", values))

    def draw_circle(self, *values: object) -> None:
        self.operations.append(("circle", values))

    def draw_line(self, *values: object) -> None:
        self.operations.append(("line", values))

    def draw_polygon(self, *values: object) -> None:
        self.operations.append(("polygon", values))

    def draw_text(self, *values: object) -> None:
        self.operations.append(("text", values))

    @property
    def text(self) -> list[str]:
        return [str(values[0]) for kind, values in self.operations if kind == "text"]


def _extent(operation: Operation) -> tuple[int, int, int, int]:
    kind, values = operation
    if kind == "rect":
        x, y, width, height = values[:4]
        return x, y, x + width, y + height  # type: ignore[operator]
    if kind == "circle":
        x, y, radius = values[:3]
        return x - radius, y - radius, x + radius, y + radius  # type: ignore[operator]
    if kind == "line":
        x1, y1, x2, y2 = values[:4]
        pad = values[5] // 2 if len(values) > 5 else 0  # type: ignore[operator]
        return (
            min(x1, x2) - pad,  # type: ignore[type-var,operator]
            min(y1, y2) - pad,  # type: ignore[type-var,operator]
            max(x1, x2) + pad,  # type: ignore[type-var,operator]
            max(y1, y2) + pad,  # type: ignore[type-var,operator]
        )
    points = values[0]
    xs = [point[0] for point in points]  # type: ignore[attr-defined]
    ys = [point[1] for point in points]  # type: ignore[attr-defined]
    return min(xs), min(ys), max(xs), max(ys)


def _sprite_extent(qualified_id: str, x: int, y: int, width: int, height: int):
    renderer = _RecordingRenderer()
    assert draw_classroom_sprite(renderer, qualified_id, x, y, width, height, (120, 80, 220))
    extents = [_extent(operation) for operation in renderer.operations]
    return (
        min(extent[0] for extent in extents),
        min(extent[1] for extent in extents),
        max(extent[2] for extent in extents),
        max(extent[3] for extent in extents),
    )


def _s02_scene(
    renderer: object, *, mission_id: str | None = MISSION_02_ID, package_roots=S02_PACKAGES
):
    planned = plan_local_classroom_trail(package_roots, player_qualified_id=NOVA_QUALIFIED_ID)
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=mission_id)
    scene.enter()
    return scene


def _moved_compass_package(tmp_path: Path, x: int, y: int) -> tuple[Path, ...]:
    import shutil

    compass = tmp_path / "moon-compass"
    shutil.copytree(S02_PACKAGES[-1], compass)
    source = compass / "objects" / "compass.yaml"
    source.write_text(source.read_text().replace("x: 240", f"x: {x}").replace("y: 180", f"y: {y}"))
    return (*S02_PACKAGES[:-1], compass)


def test_backdrop_mission_id_matches_the_course_m02_id() -> None:
    assert S02_MISSION_ID == MISSION_02_ID


@pytest.mark.parametrize(
    ("qualified_id", "width", "height"),
    (
        (NOVA_QUALIFIED_ID, 100, 100),
        (PIXEL_QUALIFIED_ID, 100, 100),
        (MOON_COMPASS_QUALIFIED_ID, 80, 60),
        (CRYSTAL_LANTERN_QUALIFIED_ID, 80, 60),
        (NOVA_QUALIFIED_ID, 200, 160),
        (PIXEL_QUALIFIED_ID, 160, 200),
        (MOON_COMPASS_QUALIFIED_ID, 160, 120),
        (CRYSTAL_LANTERN_QUALIFIED_ID, 160, 120),
    ),
)
def test_sprites_stay_inside_their_unchanged_bounds(
    qualified_id: str, width: int, height: int
) -> None:
    left, top, right, bottom = _sprite_extent(qualified_id, 300, 200, width, height)

    assert (left, top) >= (300, 200)
    assert (right, bottom) <= (300 + width, 200 + height)
    # Using the bounds well: each sprite spans most of its visual area.
    assert right - left >= width * 60 // 100
    assert bottom - top >= height * 85 // 100


def test_nova_and_pixel_silhouettes_do_not_overlap_at_the_s02_start() -> None:
    nova = _sprite_extent(NOVA_QUALIFIED_ID, 430, 270, 100, 100)
    pixel = _sprite_extent(PIXEL_QUALIFIED_ID, 480, 310, 100, 100)

    assert nova[2] < pixel[0]


def test_backdrop_is_allow_listed_by_explicit_mission() -> None:
    renderer = _RecordingRenderer()

    assert draw_classroom_backdrop(renderer, MISSION_05_ID) is False
    assert draw_classroom_backdrop(renderer, None) is False
    assert renderer.operations == []
    assert draw_classroom_backdrop(_RecordingRenderer(), MISSION_01_ID) is True
    assert draw_classroom_backdrop(renderer, MISSION_02_ID) is True
    assert renderer.operations[0] == ("rect", (0, 0, 960, 170, (17, 19, 34)))


@pytest.mark.parametrize("mission_id", (MISSION_05_ID, None))
def test_other_missions_render_without_any_backdrop(mission_id: str | None) -> None:
    renderer = _RecordingRenderer()
    scene = _s02_scene(renderer, mission_id=mission_id)

    scene.render()

    compass = next(
        item.world_object
        for item in scene.objects
        if item.qualified_id == MOON_COMPASS_QUALIFIED_ID
    )
    # The first draw is the first world object's sprite, not scenery.
    first_extent = _extent(renderer.operations[0])
    assert first_extent[0] >= min(item.world_object.x for item in scene.objects)
    assert compass.x == 240
    assert ("rect", (0, 0, 960, 170, (17, 19, 34))) not in renderer.operations


def test_backdrop_failure_keeps_a_safe_plain_frame() -> None:
    class RectOnlyRenderer:
        def __init__(self) -> None:
            self.text: list[str] = []

        def draw_rect(self, *values: object) -> None:
            pass

        def draw_text(self, text: str, *values: object) -> None:
            self.text.append(text)

    renderer = RectOnlyRenderer()

    assert draw_classroom_backdrop(renderer, MISSION_02_ID) is False  # type: ignore[arg-type]
    scene = _s02_scene(renderer)
    scene.render()
    assert "Visited 0 / 2" in renderer.text


def test_render_layers_backdrop_objects_npc_player_then_hud(monkeypatch) -> None:
    renderer = _RecordingRenderer()
    real_backdrop = trail_scene_module.draw_classroom_backdrop
    real_sprite = trail_scene_module.draw_classroom_sprite

    def backdrop(target, mission_id):
        target.operations.append(("layer", ("backdrop",)))
        return real_backdrop(target, mission_id)

    def sprite(target, qualified_id, *values):
        target.operations.append(("layer", (qualified_id,)))
        return real_sprite(target, qualified_id, *values)

    monkeypatch.setattr(trail_scene_module, "draw_classroom_backdrop", backdrop)
    monkeypatch.setattr(trail_scene_module, "draw_classroom_sprite", sprite)
    scene = _s02_scene(renderer)

    scene.render()

    layers = [values[0] for kind, values in renderer.operations if kind == "layer"]
    assert layers[0] == "backdrop"
    assert set(layers[1:3]) == {MOON_COMPASS_QUALIFIED_ID, CRYSTAL_LANTERN_QUALIFIED_ID}
    assert layers[3:] == [PIXEL_QUALIFIED_ID, NOVA_QUALIFIED_ID]
    kinds = [kind for kind, _ in renderer.operations]
    player_marker = renderer.operations.index(("layer", (NOVA_QUALIFIED_ID,)))
    first_text = kinds.index("text")
    assert first_text > player_marker
    assert set(kinds[first_text:]) == {"text"}


def test_backdrop_is_static_and_compass_sprite_follows_student_coordinates(
    tmp_path: Path,
) -> None:
    canonical_renderer = _RecordingRenderer()
    moved_renderer = _RecordingRenderer()
    canonical = _s02_scene(canonical_renderer)
    moved = _s02_scene(moved_renderer, package_roots=_moved_compass_package(tmp_path, 690, 360))
    backdrop_renderer = _RecordingRenderer()
    draw_classroom_backdrop(backdrop_renderer, MISSION_02_ID)
    backdrop_length = len(backdrop_renderer.operations)

    canonical.render()
    moved.render()

    assert canonical_renderer.operations[:backdrop_length] == backdrop_renderer.operations
    assert moved_renderer.operations[:backdrop_length] == backdrop_renderer.operations
    canonical_compass = _sprite_extent(MOON_COMPASS_QUALIFIED_ID, 240, 180, 80, 60)
    moved_compass = _sprite_extent(MOON_COMPASS_QUALIFIED_ID, 690, 360, 80, 60)
    assert moved_compass == (
        canonical_compass[0] + 450,
        canonical_compass[1] + 180,
        canonical_compass[2] + 450,
        canonical_compass[3] + 180,
    )
    compass = next(
        item.world_object
        for item in moved.objects
        if item.qualified_id == MOON_COMPASS_QUALIFIED_ID
    )
    assert (compass.x, compass.y, compass.width, compass.height) == (690, 360, 80, 60)


def test_rendering_never_changes_entity_geometry() -> None:
    renderer = _RecordingRenderer()
    scene = _s02_scene(renderer)
    entities = (
        scene.player,
        *(npc.character for npc in scene.npcs),
        *(item.world_object for item in scene.objects),
    )
    before = [(entity.x, entity.y, entity.width, entity.height) for entity in entities]

    for _ in range(3):
        scene.render()

    assert [(entity.x, entity.y, entity.width, entity.height) for entity in entities] == before
    assert (scene.player.x, scene.player.y) == (430, 270)
    assert (scene.npcs[0].character.x, scene.npcs[0].character.y) == (480, 310)


def test_unknown_m02_entity_keeps_the_rectangle_fallback() -> None:
    renderer = _RecordingRenderer()
    scene = _s02_scene(renderer)
    unknown = ClassroomTrailObject(
        "student-package:new-object",
        WorldObject(name="New", x=700, y=420, width=80, height=60, color=(10, 20, 30)),
    )
    scene._objects = (*scene._objects, unknown)  # type: ignore[attr-defined]

    scene.render()

    assert ("rect", (700, 420, 80, 60, (10, 20, 30))) in renderer.operations


def test_m02_hud_greeting_and_completion_text_are_unchanged() -> None:
    renderer = _RecordingRenderer()
    scene = _s02_scene(renderer)
    anywhere = Bounds(min_x=-1e6, min_y=-1e6, max_x=1e6, max_y=1e6)

    scene.render()
    assert renderer.text[:4] == [
        "Visited 0 / 2",
        "Mission: Create Your First Object",
        scene.mission.instructions,
        "Mission state: Incomplete",
    ]

    pixel = scene.npcs[0].character
    scene.player.move(pixel.x - scene.player.x_float, pixel.y - scene.player.y_float, anywhere)
    scene.update(DirectionalInput(), InteractionInput(interact_pressed=True), 0.0)
    renderer.operations.clear()
    scene.render()
    assert PIXEL_GREETING in renderer.text

    for item in scene.objects:
        scene.player.move(
            item.world_object.x - scene.player.x_float,
            item.world_object.y - scene.player.y_float,
            anywhere,
        )
        scene.update(DirectionalInput(), InteractionInput(interact_pressed=True), 0.0)
    renderer.operations.clear()
    scene.render()

    assert renderer.text[0] == "Visited 2 / 2"
    assert "Mission state: Complete" in renderer.text
    assert scene.mission_is_complete
    assert (pixel.x, pixel.y) == (480, 310)
