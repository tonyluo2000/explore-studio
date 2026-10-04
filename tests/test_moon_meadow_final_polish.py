"""Focused tests for the final Moon Meadow visual-polish pass.

They cover what this pass adds on top of the S02/S03 presentation: the
student-tinted Compass ground halo (and its line-ring fallback), the Lantern's
waypoint gem, Nova's step dust, the camp, pond, and sky ambience, and the
feedback, prompt, and speech-bubble panels. They check translation with the
student's x/y, bounds, determinism, fallbacks, and that gameplay and HUD text
stay exactly as they were. They assert structure and semantics, not pixels.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

import engine.scenes._classroom_trail_scene as trail_scene_module
from engine.entities import Bounds, WorldObject
from engine.input import DirectionalInput, InteractionInput
from engine.rendering._classroom_ambience import (
    SHOOTING_STAR_DURATION,
    SHOOTING_STAR_PERIOD,
    chevron_pulse,
    draw_ground_life,
    pad_chase,
    shooting_star,
)
from engine.rendering._classroom_sprites import (
    COMPASS_HALO_FRAME,
    COMPASS_HALO_SHEET_ID,
    CRYSTAL_LANTERN_QUALIFIED_ID,
    MOON_COMPASS_QUALIFIED_ID,
    NOVA_QUALIFIED_ID,
    PIXEL_QUALIFIED_ID,
)
from engine.rendering._effects import mix
from engine.rendering._meadow_layout import (
    LANDER_BEACON,
    PAD_CHEVRONS,
    PAD_LIGHTS,
    SHOOTING_STAR_PATHS,
    START_CENTER,
)
from engine.rendering._trail_presentation import (
    COMPLETE_TEXT_Y,
    FEEDBACK_FONT,
    FEEDBACK_TEXT_X,
    FEEDBACK_TEXT_Y,
    HUD_BOTTOM,
    TrailPresentation,
)
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
STEP = 1 / 60
STILL = DirectionalInput()
NO_E = InteractionInput()
E = InteractionInput(interact_pressed=True)
ANYWHERE = Bounds(min_x=-1e6, min_y=-1e6, max_x=1e6, max_y=1e6)
WHITE = (255, 255, 255)
#: The HUD's long instruction row and its short-row card (generous bounds).
HUD_RECTS = ((0, 0, 300, 150), (0, 70, 900, 50))


class PolishRenderer:
    """Records every drawing operation the real Trail renderer offers."""

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

    def of(self, kind: str) -> list[tuple[object, ...]]:
        return [values for recorded, values in self.operations if recorded == kind]


def _scene(renderer: object, *, mission_id: str | None = MISSION_02_ID):  # type: ignore[no-untyped-def]
    planned = plan_local_classroom_trail(S02_PACKAGES, player_qualified_id=NOVA_QUALIFIED_ID)
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(renderer, planned.plan, mission_id=mission_id)
    scene.enter()
    return scene


def _teleport_near(scene, qualified_id: str) -> None:  # type: ignore[no-untyped-def]
    target = next(
        item.world_object if hasattr(item, "world_object") else item.character
        for item in (*scene.objects, *scene.npcs)
        if item.qualified_id == qualified_id
    )
    scene.player.move(target.x - scene.player.x_float, target.y - scene.player.y_float, ANYWHERE)


def _render(scene, renderer: PolishRenderer, directions=STILL, interact=NO_E) -> None:  # type: ignore[no-untyped-def]
    scene.update(directions, interact, STEP)
    renderer.operations.clear()
    scene.render()


def _inside(inner: tuple[int, int, int, int], outer: tuple[int, int, int, int]) -> bool:
    return (
        outer[0] <= inner[0]
        and outer[1] <= inner[1]
        and inner[0] + inner[2] <= outer[0] + outer[2]
        and inner[1] + inner[3] <= outer[1] + outer[3]
    )


def _overlaps(first, second) -> bool:  # type: ignore[no-untyped-def]
    return (
        first[0] < second[0] + second[2]
        and second[0] < first[0] + first[2]
        and first[1] < second[1] + second[3]
        and second[1] < first[1] + first[3]
    )


# ---------------------------------------------------------------------------
# Moon Compass ground halo
# ---------------------------------------------------------------------------


def _compass_under(renderer: PolishRenderer, x: int, y: int, color, clock: float) -> None:  # type: ignore[no-untyped-def]
    presentation = TrailPresentation(MISSION_02_ID)
    presentation.clock = clock
    compass = WorldObject(name="Moon Compass", x=x, y=y, width=80, height=60, color=color)
    presentation.draw_under(renderer, MOON_COMPASS_QUALIFIED_ID, compass, color)


def test_compass_halo_is_centered_under_the_compass_and_travels_with_its_x_y() -> None:
    purple = (140, 50, 180)
    here, there = PolishRenderer(), PolishRenderer()
    _compass_under(here, 240, 180, purple, clock=3.3)
    _compass_under(there, 690, 360, purple, clock=3.3)
    (halo,) = [v for v in here.of("sprite") if v[0] == COMPASS_HALO_SHEET_ID]
    (moved,) = [v for v in there.of("sprite") if v[0] == COMPASS_HALO_SHEET_ID]
    width, height = COMPASS_HALO_FRAME
    assert halo[1] == "halo" and halo[5:7] == (width, height)
    assert (halo[3] + width / 2, halo[4] + height / 2) == (240 + 40, 180 + 54)
    assert moved[:3] == halo[:3]
    assert moved[3:5] == (halo[3] + 450, halo[4] + 180)  # type: ignore[operator]
    # The line-drawn ring is only the fallback.
    assert not here.of("line")


def test_compass_halo_keeps_the_student_color_with_one_fixed_tint_per_color() -> None:
    tints = set()
    for clock in (0.0, 1.1, 2.7, 9.9):
        for color in ((140, 50, 180), (40, 180, 90)):
            renderer = PolishRenderer()
            _compass_under(renderer, 240, 180, color, clock)
            (halo,) = [v for v in renderer.of("sprite") if v[0] == COMPASS_HALO_SHEET_ID]
            assert halo[-1] == {"tint": mix(color, WHITE, 0.4)}
            tints.add(halo[-1]["tint"])  # type: ignore[index]
    assert len(tints) == 2  # no per-frame tint churn in the frame cache


def test_compass_falls_back_to_line_rings_without_the_halo_art() -> None:
    renderer = PolishRenderer(trusted_art=False)
    _compass_under(renderer, 240, 180, (140, 50, 180), clock=3.3)
    assert not renderer.of("sprite")
    assert len(renderer.of("line")) >= 2 * 28  # the two-tier procedural ring


# ---------------------------------------------------------------------------
# Lantern destination and Nova's step dust
# ---------------------------------------------------------------------------


def _waypoint_polygons(renderer: PolishRenderer) -> list[tuple[object, ...]]:
    return [v for v in renderer.of("polygon") if len(v[0]) in (3, 4)]  # type: ignore[arg-type]


def test_lantern_waypoint_shows_until_the_lantern_is_visited_and_never_moves_it() -> None:
    renderer = PolishRenderer()
    scene = _scene(renderer)
    _render(scene, renderer)
    presentation = scene._presentation  # type: ignore[attr-defined]
    lantern = next(
        item.world_object
        for item in scene.objects
        if item.qualified_id == CRYSTAL_LANTERN_QUALIFIED_ID
    )

    def kites() -> list[tuple[object, ...]]:
        renderer.operations.clear()
        presentation.draw_over(renderer, CRYSTAL_LANTERN_QUALIFIED_ID, lantern, lantern.color)
        return [v for v in _waypoint_polygons(renderer) if len(v[0]) == 4]  # type: ignore[arg-type]

    assert kites()
    for points, _color in kites():  # type: ignore[misc]
        for px, py in points:
            assert lantern.x <= px <= lantern.x + lantern.width
            assert HUD_BOTTOM <= py <= lantern.y  # above the Lantern, below the HUD
    _teleport_near(scene, CRYSTAL_LANTERN_QUALIFIED_ID)
    _render(scene, renderer)
    _render(scene, renderer, interact=E)
    assert CRYSTAL_LANTERN_QUALIFIED_ID in scene.visited_qualified_ids
    for _ in range(90):
        _render(scene, renderer)
    assert not kites()
    assert (lantern.x, lantern.y) == (120, 460)


def test_resting_lantern_has_no_line_rays_and_flares_with_rays_when_inspected() -> None:
    renderer = PolishRenderer()
    scene = _scene(renderer)
    _teleport_near(scene, CRYSTAL_LANTERN_QUALIFIED_ID)
    _render(scene, renderer)
    presentation = scene._presentation  # type: ignore[attr-defined]
    lantern = scene.objects[-1].world_object
    renderer.operations.clear()
    presentation.draw_over(renderer, CRYSTAL_LANTERN_QUALIFIED_ID, lantern, lantern.color)
    assert not renderer.of("line")
    _render(scene, renderer, interact=E)
    renderer.operations.clear()
    presentation.draw_over(renderer, CRYSTAL_LANTERN_QUALIFIED_ID, lantern, lantern.color)
    assert len(renderer.of("line")) >= 8


def test_step_dust_is_one_bounded_puff_while_walking_and_none_when_still() -> None:
    renderer = PolishRenderer()
    scene = _scene(renderer)
    presentation = scene._presentation  # type: ignore[attr-defined]
    player = scene.player
    puffs_seen = 0
    for _ in range(60):
        _render(scene, renderer, directions=DirectionalInput(right=True))
        renderer.operations.clear()
        presentation.draw_under(renderer, NOVA_QUALIFIED_ID, player, player.color)
        dust = [v for v in renderer.of("shadow") if v[4] != (6, 10, 16)]
        assert len(dust) <= 1
        for x, y, rx, ry, _color, alpha in dust:  # type: ignore[misc]
            assert abs(x - (player.x + 48)) <= 20 and abs(y - (player.y + 95)) <= 10
            assert rx <= 10 and ry <= 5 and 0 <= alpha <= 72
        puffs_seen += len(dust)
    assert puffs_seen > 0
    for _ in range(3):
        _render(scene, renderer)
    renderer.operations.clear()
    presentation.draw_under(renderer, NOVA_QUALIFIED_ID, player, player.color)
    assert [v[4] for v in renderer.of("shadow")] == [(6, 10, 16)]


# ---------------------------------------------------------------------------
# Living world: camp, pond, and sky
# ---------------------------------------------------------------------------


def test_pad_chase_lights_two_painted_rim_lights_at_a_time() -> None:
    assert len(PAD_LIGHTS) == 12
    for x, y in PAD_LIGHTS:
        assert math.hypot((x - START_CENTER[0]) / 104, (y - START_CENTER[1] - 2) / 36) == (
            pytest.approx(1.0)
        )
    leads = set()
    for step in range(200):
        lights = pad_chase(step * 0.05)
        assert len(lights) == 2
        assert sum(strength for _, strength in lights) == pytest.approx(1.0)
        assert all(0 <= index < 12 and 0 <= strength <= 1 for index, strength in lights)
        leads.add(lights[0][0])
    assert leads == set(range(12))  # the light really travels around the pad


def test_chevrons_pulse_from_the_pad_toward_the_trail() -> None:
    order = []
    for step in range(36):
        index, strength = chevron_pulse(step * 0.05)
        assert 0 <= index < len(PAD_CHEVRONS) and 0 <= strength <= 1
        if strength > 0.9 and (not order or order[-1] != index):
            order.append(index)
    assert order == [0, 1, 2]


def test_shooting_star_is_rare_brief_deterministic_and_stays_in_open_sky() -> None:
    samples = [shooting_star(step * 0.02) for step in range(round(3 * SHOOTING_STAR_PERIOD / 0.02))]
    visible = [star for star in samples if star is not None]
    fraction = len(visible) / len(samples)
    assert fraction == pytest.approx(SHOOTING_STAR_DURATION / SHOOTING_STAR_PERIOD, abs=0.02)
    assert shooting_star(1.0) is None  # never in the first seconds of a lesson
    assert shooting_star(5.0) == shooting_star(5.0)
    for head_x, head_y, tail_x, tail_y, fade in visible:
        assert 0 <= fade <= 1
        for x, y in ((head_x, head_y), (tail_x, tail_y)):
            assert 300 <= x <= 860 and 0 <= y <= 72
            assert not any(_overlaps((x, y, 1, 1), rect) for rect in HUD_RECTS[:1])
    for x0, y0, dx, dy, length in SHOOTING_STAR_PATHS:
        assert y0 + dy * length <= 72 and x0 + dx * length >= 300


def test_illustrated_ambience_adds_bounded_camp_life_and_keeps_its_counts() -> None:
    for clock in (0.1, 2.9, 3.0, 7.7, 600.25):
        renderer = PolishRenderer()
        draw_ground_life(renderer, clock, illustrated=True)
        glows = renderer.of("glow")
        assert len(glows) <= 30
        assert "rect" not in renderer.kinds()
        # Nothing new is a 4-point polygon (the procedural anthill shape).
        assert not [v for v in renderer.of("polygon") if len(v[0]) == 4]  # type: ignore[arg-type]
    beacon = PolishRenderer()
    draw_ground_life(beacon, 0.1, illustrated=True)
    assert any(
        v[:2] == (round(LANDER_BEACON[0]), round(LANDER_BEACON[1])) for v in beacon.of("glow")
    )
    procedural = PolishRenderer(trusted_art=False)
    draw_ground_life(procedural, 3.0, illustrated=False)
    assert not any(
        v[:2] == (round(LANDER_BEACON[0]), round(LANDER_BEACON[1])) for v in procedural.of("glow")
    )


# ---------------------------------------------------------------------------
# HUD, prompt, and dialogue presentation
# ---------------------------------------------------------------------------


def test_feedback_layout_mirrors_the_unchanged_scene_hud() -> None:
    assert FEEDBACK_TEXT_X == trail_scene_module._FEEDBACK_X == trail_scene_module._COMPLETE_X
    assert FEEDBACK_TEXT_Y == trail_scene_module._FEEDBACK_Y
    assert COMPLETE_TEXT_Y == trail_scene_module._COMPLETE_Y
    assert FEEDBACK_FONT == trail_scene_module._FEEDBACK_FONT_SIZE


def test_feedback_message_is_exactly_the_hud_feedback_line() -> None:
    renderer = PolishRenderer()
    scene = _scene(renderer)
    _render(scene, renderer)
    assert scene.feedback_message == "Press E to explore"  # Nova starts beside Pixel
    assert ("Press E to explore", 360, 560) in [v[:3] for v in renderer.of("text")]
    scene.player.move(900 - scene.player.x_float, 520 - scene.player.y_float, ANYWHERE)
    _render(scene, renderer)
    assert scene.feedback_message is None
    assert all(v[2] != 560 for v in renderer.of("text"))
    _teleport_near(scene, CRYSTAL_LANTERN_QUALIFIED_ID)
    _render(scene, renderer)
    assert scene.feedback_message == "The lantern glows warmly."
    _render(scene, renderer, interact=E)
    assert scene.feedback_message == "A tiny crystal spark dances inside!"


def test_feedback_panel_sits_behind_the_feedback_lines_and_before_any_text() -> None:
    renderer = PolishRenderer()
    scene = _scene(renderer)
    _render(scene, renderer)
    panels = [v for v in renderer.of("translucent") if v[1] == (10, 14, 34)]
    assert len(panels) == 1
    ((rect,),) = (panels[0][0],)
    message = scene.feedback_message
    width, height = renderer.measure_text(message, FEEDBACK_FONT)
    assert _inside((FEEDBACK_TEXT_X, FEEDBACK_TEXT_Y, width, height), rect)
    assert rect[0] + rect[2] <= 960 and rect[1] >= HUD_BOTTOM
    kinds = renderer.kinds()
    assert kinds.index("translucent") < kinds.index("text")
    # No feedback line, no panel.
    scene.player.move(900 - scene.player.x_float, 520 - scene.player.y_float, ANYWHERE)
    _render(scene, renderer)
    assert not [v for v in renderer.of("translucent") if v[1] == (10, 14, 34)]


def test_completion_panel_covers_both_bottom_lines() -> None:
    renderer = PolishRenderer()
    scene = _scene(renderer)
    for qualified_id in (MOON_COMPASS_QUALIFIED_ID, CRYSTAL_LANTERN_QUALIFIED_ID):
        _teleport_near(scene, qualified_id)
        _render(scene, renderer)
        _render(scene, renderer, interact=E)
    assert scene.is_complete
    ((rect,),) = (next(v for v in renderer.of("translucent") if v[1] == (10, 14, 34))[0],)
    for text, y in (
        ("Trail complete!", COMPLETE_TEXT_Y),
        (scene.feedback_message, FEEDBACK_TEXT_Y),
    ):
        width, height = renderer.measure_text(text, FEEDBACK_FONT)
        assert _inside((FEEDBACK_TEXT_X, y, width, height), rect), text


def test_prompt_has_a_shadow_and_a_pointer_toward_its_target() -> None:
    renderer = PolishRenderer()
    scene = _scene(renderer)
    _teleport_near(scene, MOON_COMPASS_QUALIFIED_ID)
    _render(scene, renderer)
    gold = (240, 208, 112)
    prompt = next(v for v in renderer.of("translucent") if v[4:6] == (gold, 235))
    shadow = next(v for v in renderer.of("translucent") if v[1] == (4, 6, 16))
    (px, py, pw, ph), (sx, sy, _, _) = prompt[0][0], shadow[0][0]  # type: ignore[index]
    assert (sx, sy) == (px + 2, py + 4)
    pointers = [v for v in renderer.of("polygon") if v[1] == gold]
    assert len(pointers) == 1
    compass = scene.objects[0].world_object
    # The pointer's tip leaves the panel on the side that faces the Compass.
    tip = max(
        pointers[0][0],  # type: ignore[arg-type]
        key=lambda point: max(px - point[0], point[0] - px - pw, py - point[1], point[1] - py - ph),
    )
    assert not (px <= tip[0] <= px + pw and py <= tip[1] <= py + ph)
    panel_center = (px + pw / 2, py + ph / 2)
    compass_center = (compass.x + compass.width / 2, compass.y + compass.height / 2)
    assert math.dist(tip, compass_center) < math.dist(panel_center, compass_center)


def test_speech_bubble_names_its_speaker_without_changing_the_greeting() -> None:
    renderer = PolishRenderer()
    scene = _scene(renderer)
    _render(scene, renderer, interact=E)
    assert scene.target_qualified_id == PIXEL_QUALIFIED_ID
    texts = [v[0] for v in renderer.of("text")]
    assert "Pixel" in texts
    assert any(str(text).startswith("Pixel: Beep!") for text in texts)  # HUD line unchanged
    tag = next(v for v in renderer.of("panel") if v[4] == (58, 86, 214))
    bubble = next(v for v in renderer.of("panel") if v[4] == (250, 248, 236))
    assert tag[1] >= HUD_BOTTOM - 4
    assert _overlaps(tag[:4], bubble[:4])  # the tag sits on the bubble's top edge


@pytest.mark.parametrize("mission_id", (MISSION_06_ID, None))
def test_other_missions_get_none_of_the_new_presentation(mission_id: str | None) -> None:
    renderer = PolishRenderer()
    scene = _scene(renderer, mission_id=mission_id)
    for _ in range(30):
        _render(scene, renderer, directions=DirectionalInput(right=True))
    assert not {"translucent", "sprite", "glow", "shadow"} & set(renderer.kinds())
