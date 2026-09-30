"""Living-world ambience for the S02 Moon Meadow.

Everything here is a pure function of an injected clock: ants on two fixed
looping trails, drifting firefly motes, swaying reeds, crystal glints,
twinkling stars, and the shrine braziers' flicker. Nothing reads or writes
entity state, nothing collides, and every count is a fixed constant, so the
Trail's gameplay is untouched and the per-frame cost is bounded.

Over the illustrated meadow plate, the effects animate the painted scenery's
own positions (``_meadow_layout``) and the reeds are trusted sprite frames;
over the procedural fallback backdrop they use that backdrop's positions and
procedural shapes, exactly as before.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from engine.rendering._classroom_environment import _CRYSTAL_CLUSTERS, _STARS
from engine.rendering._effects import Color, glow, mix, sparkle
from engine.rendering._meadow_layout import (
    BRIGHT_STARS,
    CRYSTAL_CLUSTERS,
    SHRINE_FLAMES,
    crystal_tip,
)

Point = tuple[float, float]

_GROUND: Final[Color] = (40, 57, 66)
_ANT: Final[Color] = (14, 12, 18)
_ANT_SHINE: Final[Color] = (96, 90, 108)
_ANT_HILL: Final[Color] = (74, 66, 62)
_ANT_HILL_LIGHT: Final[Color] = (96, 86, 78)
_ANT_HOLE: Final[Color] = (24, 22, 24)
_CRUMB: Final[Color] = (170, 236, 244)
_REED: Final[Color] = (70, 110, 94)
_REED_LIGHT: Final[Color] = (104, 150, 118)
_REED_TIP: Final[Color] = (178, 214, 150)
_MOTE: Final[Color] = (150, 255, 196)
_MOTE_CORE: Final[Color] = (236, 255, 232)
_CRYSTAL_GLOW: Final[Color] = (90, 190, 220)
_GLINT: Final[Color] = (236, 250, 255)
_STAR: Final[Color] = (226, 230, 255)


@dataclass(frozen=True)
class AntTrail:
    """A closed two-lane loop: out along one side, home along the other."""

    hill: Point
    loop: tuple[Point, ...]
    ants: int
    speed: float
    phase: float

    @property
    def length(self) -> float:
        return sum(
            math.dist(start, end)
            for start, end in zip(self.loop, self.loop[1:] + self.loop[:1], strict=True)
        )

    def point_at(self, distance: float) -> tuple[float, float, float, float, bool]:
        """Return ``x, y, heading_x, heading_y, returning`` at *distance* along the loop."""
        distance %= self.length
        travelled = 0.0
        points = self.loop
        half = len(points) // 2
        for index, (start, end) in enumerate(zip(points, points[1:] + points[:1], strict=True)):
            segment = math.dist(start, end)
            if travelled + segment >= distance and segment > 0:
                t = (distance - travelled) / segment
                return (
                    start[0] + (end[0] - start[0]) * t,
                    start[1] + (end[1] - start[1]) * t,
                    (end[0] - start[0]) / segment,
                    (end[1] - start[1]) / segment,
                    index >= half,
                )
            travelled += segment
        start, end = points[0], points[1]
        segment = math.dist(start, end) or 1.0
        return (
            start[0],
            start[1],
            (end[0] - start[0]) / segment,
            (end[1] - start[1]) / segment,
            False,
        )


#: Two small colonies on open ground, clear of the start pad, the Compass
#: clearing, the Lantern shrine, and the HUD text rows.
ANT_TRAILS: Final = (
    AntTrail(
        hill=(584.0, 500.0),
        loop=(
            (590.0, 496.0),
            (610.0, 486.0),
            (632.0, 478.0),
            (654.0, 473.0),
            (672.0, 469.0),
            (656.0, 480.0),
            (634.0, 487.0),
            (612.0, 494.0),
        ),
        ants=5,
        speed=15.0,
        phase=0.0,
    ),
    AntTrail(
        hill=(786.0, 522.0),
        loop=(
            (792.0, 518.0),
            (812.0, 510.0),
            (834.0, 505.0),
            (856.0, 500.0),
            (872.0, 497.0),
            (858.0, 508.0),
            (836.0, 514.0),
            (814.0, 520.0),
        ),
        ants=4,
        speed=13.0,
        phase=11.0,
    ),
)
ANT_COUNT: Final = sum(trail.ants for trail in ANT_TRAILS)


@dataclass(frozen=True)
class AntState:
    x: float
    y: float
    heading_x: float
    heading_y: float
    carrying: bool
    step: int


def ant_states(clock: float) -> tuple[AntState, ...]:
    """Every ant's position at *clock*; a pure, bounded function of time."""
    states: list[AntState] = []
    for trail_index, trail in enumerate(ANT_TRAILS):
        length = trail.length
        for ant in range(trail.ants):
            seed = trail_index * 7 + ant
            # Ants pause and hurry a little, like real ants, without state.
            distance = (
                trail.phase
                + ant * length / trail.ants
                + clock * trail.speed * (0.85 + 0.06 * (seed % 4))
                + 3.0 * math.sin(clock * 1.3 + seed * 1.7)
            )
            x, y, hx, hy, returning = trail.point_at(distance)
            wobble = 0.8 * math.sin(distance * 0.9 + seed)
            states.append(
                AntState(
                    x=x - hy * wobble,
                    y=y + hx * wobble,
                    heading_x=hx,
                    heading_y=hy,
                    carrying=returning and seed % 2 == 0,
                    step=int(distance / 2.5) % 2,
                )
            )
    return tuple(states)


def _draw_ant(renderer: object, ant: AntState) -> None:
    hx, hy = ant.heading_x, ant.heading_y
    px, py = -hy, hx
    draw_line = renderer.draw_line  # type: ignore[attr-defined]
    draw_circle = renderer.draw_circle  # type: ignore[attr-defined]
    for offset, swing in ((-1.6, 1), (0.0, -1), (1.6, 1)):
        direction = swing if ant.step == 0 else -swing
        base_x = ant.x + hx * offset
        base_y = ant.y + hy * offset
        for side in (-1, 1):
            draw_line(
                round(base_x),
                round(base_y),
                round(base_x + px * side * 3.2 + hx * direction * 1.2),
                round(base_y + py * side * 3.2 + hy * direction * 1.2),
                _ANT,
                1,
            )
    draw_circle(round(ant.x - hx * 3.4), round(ant.y - hy * 3.4), 2, _ANT)
    draw_circle(round(ant.x), round(ant.y), 1, _ANT)
    draw_circle(round(ant.x + hx * 2.8), round(ant.y + hy * 2.8), 2, _ANT)
    draw_circle(
        round(ant.x - hx * 3.8 - px * 0.6), round(ant.y - hy * 3.8 - py * 0.6), 1, _ANT_SHINE
    )
    for side in (-1, 1):
        draw_line(
            round(ant.x + hx * 4),
            round(ant.y + hy * 4),
            round(ant.x + hx * 6 + px * side * 2),
            round(ant.y + hy * 6 + py * side * 2),
            _ANT,
            1,
        )
    if ant.carrying:
        draw_circle(round(ant.x + hx * 6), round(ant.y + hy * 6), 2, _CRUMB)


def _draw_ant_hill(renderer: object, x: float, y: float) -> None:
    renderer.draw_polygon(  # type: ignore[attr-defined]
        (
            (round(x - 13), round(y + 4)),
            (round(x - 6), round(y - 4)),
            (round(x + 6), round(y - 4)),
            (round(x + 13), round(y + 4)),
        ),
        _ANT_HILL,
    )
    renderer.draw_polygon(  # type: ignore[attr-defined]
        ((round(x - 6), round(y - 4)), (round(x + 2), round(y - 4)), (round(x - 4), round(y))),
        _ANT_HILL_LIGHT,
    )
    renderer.draw_circle(round(x), round(y - 3), 2, _ANT_HOLE)  # type: ignore[attr-defined]


#: Reed clumps (x, ground y) that sway: around the pond and on open ground.
REED_CLUMPS: Final = (
    (26.0, 318.0),
    (142.0, 316.0),
    (112.0, 284.0),
    (262.0, 420.0),
    (704.0, 456.0),
    (178.0, 604.0),
    (604.0, 300.0),
    (452.0, 240.0),
    (942.0, 478.0),
)
REED_SHEET: Final = "ambient/reeds"
REED_FRAME: Final = (32, 44)
REED_SWAY_FRAMES: Final = 9
#: Largest ``reed_sway`` magnitude; maps onto the outermost sway frames.
_REED_SWAY_RANGE: Final = 4.3
_REED_BLADES: Final = ((-5.0, 14.0), (-1.5, 20.0), (2.0, 17.0), (5.5, 12.0))


def reed_sway(clock: float, x: float) -> float:
    """Horizontal tip offset (pixels) of one reed clump at *clock*."""
    # A slow gust envelope makes the sway breathe instead of ticking.
    gust = 0.75 + 0.25 * math.sin(clock * 0.37 + x * 0.011)
    return gust * (2.7 * math.sin(clock * 1.5 + x * 0.037) + 0.9 * math.sin(clock * 2.9 + x * 0.05))


def reed_column(sway: float) -> str:
    """The trusted reed frame whose lean is nearest to *sway* pixels."""
    t = max(-1.0, min(1.0, sway / _REED_SWAY_RANGE))
    return f"sway-{round((t + 1) / 2 * (REED_SWAY_FRAMES - 1))}"


def _draw_reed_sprites(renderer: object, clock: float) -> bool:
    draw_frame = getattr(renderer, "draw_sprite_frame", None)
    if draw_frame is None:
        return False
    width, height = REED_FRAME
    for x, y in REED_CLUMPS:
        column = reed_column(reed_sway(clock, x))
        if not draw_frame(
            REED_SHEET, "sway", column, round(x - width / 2), round(y - height + 2), width, height
        ):
            return False
    return True


def _draw_reeds(renderer: object, clock: float) -> None:
    draw_line = renderer.draw_line  # type: ignore[attr-defined]
    for x, y in REED_CLUMPS:
        sway = reed_sway(clock, x)
        for index, (dx, height) in enumerate(_REED_BLADES):
            bend = sway * height / 18
            base = (round(x + dx), round(y))
            middle = (round(x + dx + bend * 0.35), round(y - height * 0.55))
            tip = (round(x + dx * 1.2 + bend), round(y - height))
            color = _REED_LIGHT if index % 2 else _REED
            draw_line(*base, *middle, color, 2)
            draw_line(*middle, *tip, color, 2)
            if index == 1:
                renderer.draw_circle(*tip, 2, _REED_TIP)  # type: ignore[attr-defined]


def _draw_crystal_shimmer(renderer: object, clock: float) -> None:
    for index, (x, y) in enumerate(_CRYSTAL_CLUSTERS):
        pulse = 0.5 + 0.5 * math.sin(clock * 1.7 + index * 1.9)
        glow(renderer, x + 1, y - 10, 22, _CRYSTAL_GLOW, 0.16 + 0.16 * pulse)
        cycle = (clock + index * 1.1) % 4.4
        if cycle < 0.6:
            size = 5 * math.sin(math.pi * cycle / 0.6)
            sparkle(renderer, x + 1, y - 21, size, _GLINT)


_VIOLET_GLOW: Final[Color] = (170, 120, 255)
_FLAME: Final[Color] = (255, 170, 80)


def _draw_painted_crystal_shimmer(renderer: object, clock: float) -> None:
    """Breathe light into the painted crystals and glint their tallest tips."""
    for index, cluster in enumerate(CRYSTAL_CLUSTERS):
        x, y, scale, hue = cluster
        tip_x, tip_y = crystal_tip(cluster)
        color = _VIOLET_GLOW if hue else _CRYSTAL_GLOW
        pulse = 0.5 + 0.5 * math.sin(clock * 1.7 + index * 1.9)
        glow(renderer, x, y - 14 * scale, round(30 * scale), color, 0.1 + 0.14 * pulse)
        period = 4.4 + 0.53 * index
        cycle = (clock + index * 1.1) % period
        if cycle < 0.8:
            # An eased glint (slow in, slow out) rather than a linear blink.
            size = 5.5 * math.sin(math.pi * cycle / 0.8) ** 2
            glow(renderer, tip_x, tip_y, 9, color, 0.5 * size / 5.5)
            sparkle(renderer, tip_x, tip_y, size, _GLINT)


def shrine_flame_flicker(clock: float, index: int) -> float:
    """Brightness (0.5-1.0) of one painted shrine brazier at *clock*."""
    flicker = 0.5 + 0.3 * math.sin(clock * 8.3 + index * 2.1) + 0.2 * math.sin(clock * 19.7 + index)
    return 0.5 + 0.5 * max(0.0, min(1.0, flicker))


def _draw_shrine_flames(renderer: object, clock: float) -> None:
    for index, (x, y) in enumerate(SHRINE_FLAMES):
        strength = shrine_flame_flicker(clock, index)
        glow(renderer, x, y - 6, 20, _FLAME, 0.35 * strength)


#: Firefly-like motes: fixed anchors, bounded drift, gentle twinkle.
MOTE_ANCHORS: Final = (
    (118.0, 300.0),
    (362.0, 250.0),
    (700.0, 226.0),
    (884.0, 300.0),
    (660.0, 404.0),
    (300.0, 566.0),
    (758.0, 600.0),
    (58.0, 520.0),
    (520.0, 514.0),
    (930.0, 548.0),
)
MOTE_COUNT: Final = len(MOTE_ANCHORS)


def mote_states(clock: float) -> tuple[tuple[float, float, float], ...]:
    """Return ``(x, y, brightness)`` for every mote at *clock*."""
    states = []
    for index, (x, y) in enumerate(MOTE_ANCHORS):
        phase = index * 2.39
        states.append(
            (
                x + 14 * math.sin(clock * 0.33 + phase) + 4 * math.sin(clock * 0.81 + phase * 2.3),
                y
                + 9 * math.sin(clock * 0.47 + phase * 1.7)
                + 3 * math.sin(clock * 0.19 + phase * 0.6)
                - 4 * math.sin(clock * 0.9 + phase),
                0.25 + 0.75 * max(0.0, math.sin(clock * 1.25 + phase)) ** 2,
            )
        )
    return tuple(states)


#: A handful of the backdrop's bright stars twinkle.
TWINKLING_STARS: Final = tuple(star for index, star in enumerate(_STARS) if index % 7 == 0)[:8]


def _draw_twinkles(renderer: object, clock: float, stars: tuple[tuple[float, float], ...]) -> None:
    for index, (x, y) in enumerate(stars):
        strength = max(0.0, math.sin(clock * 0.9 + index * 2.3))
        if strength > 0.55:
            sparkle(renderer, x, y, 1 + 3 * (strength - 0.55) / 0.45, _STAR)


def draw_ground_life(renderer: object, clock: float, *, illustrated: bool = False) -> None:
    """Ground-level ambience drawn above the backdrop, below every entity.

    *illustrated* says the painted meadow plate is the backdrop, so effects
    follow its scenery (its anthills are painted); otherwise they follow the
    procedural backdrop.
    """
    if illustrated:
        _draw_twinkles(renderer, clock, BRIGHT_STARS)
        _draw_painted_crystal_shimmer(renderer, clock)
        _draw_shrine_flames(renderer, clock)
    else:
        _draw_twinkles(renderer, clock, TWINKLING_STARS)
        _draw_crystal_shimmer(renderer, clock)
    if not _draw_reed_sprites(renderer, clock):
        _draw_reeds(renderer, clock)
    if not illustrated:
        for trail in ANT_TRAILS:
            _draw_ant_hill(renderer, *trail.hill)
    for ant in ant_states(clock):
        _draw_ant(renderer, ant)


def draw_air_life(renderer: object, clock: float) -> None:
    """Airborne motes drawn above the entities, below the HUD."""
    for x, y, brightness in mote_states(clock):
        glow(renderer, x, y, 10, _MOTE, 0.55 * brightness)
        if brightness > 0.35:
            renderer.draw_circle(  # type: ignore[attr-defined]
                round(x), round(y), 1, mix(_GROUND, _MOTE_CORE, brightness)
            )
