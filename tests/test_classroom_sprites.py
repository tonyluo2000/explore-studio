"""Focused routing and geometry tests for the S02 procedural sprites."""

from __future__ import annotations

import pytest

from engine.entities import Character, WorldObject
from engine.rendering._classroom_sprites import (
    _SPRITE_DRAWERS,
    CRYSTAL_LANTERN_QUALIFIED_ID,
    MOON_COMPASS_QUALIFIED_ID,
    NOVA_QUALIFIED_ID,
    PIXEL_QUALIFIED_ID,
    draw_classroom_sprite,
)
from engine.scenes import (
    ClassroomTrailNPC,
    ClassroomTrailObject,
    ClassroomTrailScene,
)
from explore.curriculum import MISSION_02


class _RecordingRenderer:
    def __init__(self) -> None:
        self.operations: list[tuple[str, tuple[object, ...]]] = []

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


@pytest.mark.parametrize(
    ("qualified_id", "expected_operations"),
    (
        (NOVA_QUALIFIED_ID, {"rect", "circle", "line", "polygon"}),
        (PIXEL_QUALIFIED_ID, {"rect", "circle", "line"}),
        (MOON_COMPASS_QUALIFIED_ID, {"circle", "line", "polygon"}),
        (CRYSTAL_LANTERN_QUALIFIED_ID, {"rect", "circle", "line", "polygon"}),
    ),
)
def test_s02_qualified_ids_route_to_procedural_sprites(
    qualified_id: str,
    expected_operations: set[str],
) -> None:
    renderer = _RecordingRenderer()

    rendered = draw_classroom_sprite(renderer, qualified_id, 100, 120, 80, 60, (120, 80, 220))

    assert rendered is True
    assert expected_operations <= {operation for operation, _ in renderer.operations}


def test_unknown_identity_requests_rectangle_fallback_without_drawing() -> None:
    renderer = _RecordingRenderer()

    rendered = draw_classroom_sprite(
        renderer, "student-package:new-object", 10, 20, 80, 60, (1, 2, 3)
    )

    assert rendered is False
    assert renderer.operations == []


def test_unexpected_sprite_error_requests_safe_rectangle_fallback(monkeypatch) -> None:
    renderer = _RecordingRenderer()

    def fail(*args: object) -> None:
        raise RuntimeError("simulated sprite failure")

    monkeypatch.setitem(_SPRITE_DRAWERS, NOVA_QUALIFIED_ID, fail)

    assert (
        draw_classroom_sprite(renderer, NOVA_QUALIFIED_ID, 10, 20, 100, 100, (255, 200, 50))
        is False
    )


def test_scene_routes_all_four_s02_identities_and_preserves_geometry(monkeypatch) -> None:
    renderer = _RecordingRenderer()
    player = Character(
        name="Mutable display name",
        x=430,
        y=270,
        width=100,
        height=100,
        color=(255, 200, 50),
    )
    compass = ClassroomTrailObject(
        MOON_COMPASS_QUALIFIED_ID,
        WorldObject(
            name="Renamed compass",
            x=240,
            y=180,
            width=80,
            height=60,
            color=(140, 55, 190),
        ),
    )
    lantern = ClassroomTrailObject(
        CRYSTAL_LANTERN_QUALIFIED_ID,
        WorldObject(
            name="Renamed lantern",
            x=120,
            y=460,
            width=80,
            height=60,
            color=(245, 220, 35),
        ),
    )
    unknown = ClassroomTrailObject(
        "student-package:new-object",
        WorldObject(
            name="Unknown",
            x=700,
            y=420,
            width=80,
            height=60,
            color=(10, 20, 30),
        ),
    )
    pixel = ClassroomTrailNPC(
        PIXEL_QUALIFIED_ID,
        Character(
            name="Renamed robot",
            x=480,
            y=310,
            width=100,
            height=100,
            color=(50, 80, 220),
        ),
        greeting="Hello!",
    )
    entities = (
        player,
        compass.world_object,
        lantern.world_object,
        unknown.world_object,
        pixel.character,
    )
    before = tuple((entity.x, entity.y, entity.width, entity.height) for entity in entities)
    routed: list[str | None] = []

    def record_route(
        renderer: object,
        qualified_id: str | None,
        x: int,
        y: int,
        width: int,
        height: int,
        color: tuple[int, int, int],
    ) -> bool:
        del renderer, x, y, width, height, color
        routed.append(qualified_id)
        return qualified_id != unknown.qualified_id

    monkeypatch.setattr(
        "engine.scenes._classroom_trail_scene.draw_classroom_sprite",
        record_route,
    )
    scene = ClassroomTrailScene(
        renderer,  # type: ignore[arg-type]
        player,
        (compass, lantern, unknown),
        (pixel,),
        mission=MISSION_02,
        player_qualified_id=NOVA_QUALIFIED_ID,
    )
    scene.enter()

    scene.render()

    assert set(routed) == {
        NOVA_QUALIFIED_ID,
        PIXEL_QUALIFIED_ID,
        MOON_COMPASS_QUALIFIED_ID,
        CRYSTAL_LANTERN_QUALIFIED_ID,
        unknown.qualified_id,
    }
    assert ("rect", (700, 420, 80, 60, (10, 20, 30))) in renderer.operations
    after = tuple((entity.x, entity.y, entity.width, entity.height) for entity in entities)
    assert after == before
