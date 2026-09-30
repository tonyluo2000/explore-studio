"""Cosmetic presentation layer for the S02 (M02) Classroom Trail.

The scene owns gameplay. This layer only *observes* the scene after each
update (player position, current target, interaction pulse, visited set,
mission completion) and turns that into animation poses and short effects:

* Nova walks with a distance-driven cycle, faces its motion, breathes and
  blinks when idle; Pixel idles, blinks, and reacts to its greeting.
* The Moon Compass pulses, its needle swings, and sparkles orbit it, all
  positioned from the Compass's actual ``x``/``y`` every frame.
* The Crystal Lantern glows, flickers, sheds sparks, shows a destination
  marker until visited, and flares when inspected.
* Proximity prompts, Pixel's speech bubble, a discovery label, and a brief
  mission-complete celebration.

It is allow-listed to the M02 mission id. For every other Trail it is inert,
so S01 and S03+ rendering is unchanged. It never mutates the scene, never
raises into gameplay, and bounds every effect count.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final, Protocol

from engine.animation import AnimationClip, Facing, SpritePose, facing_from_motion, is_blinking
from engine.rendering._classroom_ambience import draw_air_life, draw_ground_life
from engine.rendering._classroom_environment import (
    MEADOW_FOREGROUND,
    S02_MISSION_ID,
    draw_scenery_plate,
    illustrated_backdrop_available,
)
from engine.rendering._classroom_sprites import (
    CRYSTAL_LANTERN_QUALIFIED_ID,
    MOON_COMPASS_QUALIFIED_ID,
    NOVA_QUALIFIED_ID,
    PIXEL_QUALIFIED_ID,
)
from engine.rendering._effects import (
    Color,
    ease_out,
    ellipse_ring,
    glow,
    mix,
    soft_shadow,
    sparkle,
    supports,
)

_LOGGER = logging.getLogger("explore-studio.rendering.trail-presentation")

SCREEN_WIDTH: Final = 960
SCREEN_HEIGHT: Final = 640
#: The HUD's four mission rows live above this line; overlays stay below it.
HUD_BOTTOM: Final = 150

NOVA_IDLE: Final = AnimationClip("idle", ("idle-0", "idle-1", "idle-2", "idle-3"), 0.34)
NOVA_WALK: Final = AnimationClip("walk", tuple(f"walk-{index}" for index in range(8)), 0.05)
#: Pixels travelled per walk frame, so steps keep pace with the ground: eight
#: frames per 60 px cycle (two 30 px steps), the same pace as Nova V2.
NOVA_STRIDE: Final = 7.5
#: The Compass's rune ring turns 45 degrees (one rune) per loop.
COMPASS_SPIN: Final = AnimationClip("spin", tuple(f"spin-{index:02d}" for index in range(12)), 0.11)
PIXEL_IDLE: Final = AnimationClip("idle", ("idle-0", "idle-1", "idle-2", "idle-3"), 0.36)
PIXEL_GREET: Final = AnimationClip(
    "greet", ("greet-0", "greet-1", "greet-2", "greet-1", "greet-2", "greet-3"), 0.2, loop=False
)
LANTERN_FLICKER: Final = AnimationClip(
    "flicker",
    ("flicker-0", "flicker-2", "flicker-1", "flicker-3", "flicker-1", "flicker-0", "flicker-3"),
    0.12,
)

BUBBLE_DURATION: Final = 4.0
DISCOVERY_DURATION: Final = 0.9
LABEL_DURATION: Final = 1.8
FLARE_DURATION: Final = 1.2
CELEBRATION_DURATION: Final = 3.2
PROMPT_PAUSE: Final = 0.9
MAX_BURSTS: Final = 4
BURST_PARTICLES: Final = 14
CONFETTI_PIECES: Final = 36
LANTERN_SPARKS: Final = 5
COMPASS_SPARKLES: Final = 4

#: Mirrors the Trail HUD layout in ``_classroom_trail_scene`` (a test keeps
#: them equal). The panel only sits behind that text; the text is unchanged.
HUD_TEXT_X: Final = 20
HUD_ROWS_Y: Final = (20, 55, 85, 115)
HUD_FONT: Final = 24
_HUD_PANEL: Final[Color] = (14, 18, 48)
_HUD_PANEL_ALPHA: Final = 168
_HUD_EDGE: Final[Color] = (178, 190, 255)

_PROMPT_FONT: Final = 22
_BUBBLE_FONT: Final = 22
_LABEL_FONT: Final = 24
_BANNER_FONT: Final = 34
_BUBBLE_TEXT_WIDTH: Final = 230

_INK: Final[Color] = (28, 24, 40)
_PANEL: Final[Color] = (20, 24, 40)
_PANEL_TEXT: Final[Color] = (244, 240, 228)
_GOLD: Final[Color] = (240, 208, 112)
_KEY: Final[Color] = (242, 236, 218)
_BUBBLE: Final[Color] = (250, 248, 236)
_BUBBLE_TEXT: Final[Color] = (34, 30, 50)
_LABEL: Final[Color] = (255, 216, 96)
_LABEL_TEXT: Final[Color] = (46, 30, 8)
_BANNER: Final[Color] = (44, 30, 78)
_BANNER_TEXT: Final[Color] = (255, 232, 146)
_WHITE: Final[Color] = (255, 255, 255)
_GROUND: Final[Color] = (40, 57, 66)
_LANTERN_LIGHT: Final[Color] = (255, 196, 104)
_CONFETTI: Final[tuple[Color, ...]] = (
    (255, 208, 80),
    (120, 220, 255),
    (240, 96, 120),
    (150, 240, 150),
    (190, 140, 255),
    (255, 255, 255),
)

Rect = tuple[int, int, int, int]
TextOp = tuple[str, int, int, Color, int]


class _Positioned(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def x(self) -> int: ...

    @property
    def y(self) -> int: ...

    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...


class _Player(_Positioned, Protocol):
    @property
    def x_float(self) -> float: ...

    @property
    def y_float(self) -> float: ...


class _TrailObject(Protocol):
    qualified_id: str

    @property
    def world_object(self) -> _Positioned: ...


class _TrailNPC(Protocol):
    qualified_id: str

    @property
    def character(self) -> _Positioned: ...

    @property
    def conversation_lines(self) -> tuple[str, ...]: ...


class _Mission(Protocol):
    @property
    def title(self) -> str: ...

    @property
    def instructions(self) -> str: ...


class TrailView(Protocol):
    """The read-only scene state this layer observes."""

    @property
    def mission(self) -> _Mission: ...

    @property
    def visited_count(self) -> int: ...

    @property
    def total_objects(self) -> int: ...

    @property
    def player(self) -> _Player: ...

    @property
    def objects(self) -> Sequence[_TrailObject]: ...

    @property
    def npcs(self) -> Sequence[_TrailNPC]: ...

    @property
    def target_qualified_id(self) -> str | None: ...

    @property
    def did_interact_this_frame(self) -> bool: ...

    @property
    def visited_qualified_ids(self) -> frozenset[str]: ...

    @property
    def mission_is_complete(self) -> bool: ...


@dataclass(frozen=True)
class Burst:
    """One short effect anchored to an entity by qualified id."""

    kind: str
    qualified_id: str
    start: float


@dataclass(frozen=True)
class Bubble:
    qualified_id: str
    text: str
    start: float


@dataclass(frozen=True)
class Label:
    qualified_id: str
    text: str
    start: float


def _rect_of(entity: _Positioned) -> Rect:
    return entity.x, entity.y, entity.width, entity.height


def _overlaps(first: Rect, second: Rect) -> bool:
    return (
        first[0] < second[0] + second[2]
        and second[0] < first[0] + first[2]
        and first[1] < second[1] + second[3]
        and second[1] < first[1] + first[3]
    )


def _fits(rect: Rect) -> bool:
    x, y, width, height = rect
    return (
        x >= 4
        and y >= HUD_BOTTOM + 2
        and x + width <= SCREEN_WIDTH - 4
        and (y + height <= SCREEN_HEIGHT - 4)
    )


def _clamp(rect: Rect) -> Rect:
    x, y, width, height = rect
    return (
        max(4, min(x, SCREEN_WIDTH - 4 - width)),
        max(HUD_BOTTOM + 2, min(y, SCREEN_HEIGHT - 4 - height)),
        width,
        height,
    )


def place_panel(
    size: tuple[int, int], candidates: Sequence[tuple[int, int]], avoid: Sequence[Rect]
) -> Rect:
    """Pick the first on-screen candidate that avoids every rect, else clamp the first."""
    width, height = size
    for x, y in candidates:
        rect = (x, y, width, height)
        if _fits(rect) and not any(_overlaps(rect, other) for other in avoid):
            return rect
    x, y = candidates[0]
    return _clamp((x, y, width, height))


def nova_visible_rect(player: _Positioned) -> Rect:
    """The part of Nova's box the art actually covers (helmet to boots)."""
    return (
        player.x + player.width * 20 // 100,
        player.y + player.height * 2 // 100,
        player.width * 56 // 100,
        player.height * 96 // 100,
    )


def pixel_visible_rect(npc: _Positioned) -> Rect:
    return (
        npc.x + npc.width * 34 // 100,
        npc.y + npc.height * 4 // 100,
        npc.width * 62 // 100,
        npc.height * 92 // 100,
    )


def wrap_text(
    text: str, max_width: int, measure: Callable[[str], tuple[int, int]]
) -> tuple[str, ...]:
    """Greedy word wrap using the renderer's own text measurement."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if current and measure(candidate)[0] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return tuple(lines[:4])


class TrailPresentation:
    """Observe one Trail scene and draw its M02-only cosmetic layer."""

    def __init__(self, mission_id: str, start: tuple[float, float] | None = None) -> None:
        self.active = mission_id == S02_MISSION_ID
        self.clock = 0.0
        self.facing = Facing.DOWN
        self.moving = False
        self.walk_distance = 0.0
        self.still_time = 0.0
        self.bursts: tuple[Burst, ...] = ()
        self.bubble: Bubble | None = None
        self.label: Label | None = None
        self.greet_start: dict[str, float] = {}
        self.celebration_start: float | None = None
        self._previous_position: tuple[float, float] | None = start
        self._previous_complete: bool | None = None
        self._visited: frozenset[str] = frozenset()
        self._failed_layers: set[str] = set()

    # ------------------------------------------------------------------
    # Observation (called after every scene update)
    # ------------------------------------------------------------------

    def observe(self, view: TrailView, dt: float) -> None:
        """Advance the cosmetic clock and react to what just happened."""
        if not self.active:
            return
        try:
            self._observe(view, dt)
        except Exception:
            self._log_once("observe")

    def _observe(self, view: TrailView, dt: float) -> None:
        step = dt if isinstance(dt, int | float) and math.isfinite(dt) else 0.0
        step = max(0.0, min(float(step), 0.25))
        self.clock += step
        player = view.player
        position = (player.x_float, player.y_float)
        previous = self._previous_position or position
        dx, dy = position[0] - previous[0], position[1] - previous[1]
        distance = math.hypot(dx, dy)
        if distance > 1e-6:
            self.moving = True
            self.walk_distance += distance
            self.facing = facing_from_motion(dx, dy, self.facing)
            self.still_time = 0.0
        else:
            self.moving = False
            self.still_time += step
        self._previous_position = position

        target_id = view.target_qualified_id
        if view.did_interact_this_frame and target_id is not None:
            self._react_to_interaction(view, target_id)

        complete = view.mission_is_complete
        if self._previous_complete is False and complete:
            self.celebration_start = self.clock
        self._previous_complete = complete
        self._visited = view.visited_qualified_ids

    def _react_to_interaction(self, view: TrailView, target_id: str) -> None:
        trail_object = next((item for item in view.objects if item.qualified_id == target_id), None)
        if trail_object is not None:
            newly_visited = target_id not in self._visited
            kind = {
                MOON_COMPASS_QUALIFIED_ID: "discovery",
                CRYSTAL_LANTERN_QUALIFIED_ID: "flare",
            }.get(target_id, "pulse")
            self.bursts = (*self.bursts, Burst(kind, target_id, self.clock))[-MAX_BURSTS:]
            if newly_visited and target_id == MOON_COMPASS_QUALIFIED_ID:
                self.label = Label(
                    target_id, f"{trail_object.world_object.name} discovered!", self.clock
                )
            if self.bubble is not None:
                self.bubble = None
            return
        npc = next((item for item in view.npcs if item.qualified_id == target_id), None)
        if npc is None:
            return
        self.greet_start[target_id] = self.clock
        lines = npc.conversation_lines
        # Only a single-line greeting becomes a bubble; the HUD still shows it too.
        self.bubble = Bubble(target_id, lines[0], self.clock) if len(lines) == 1 else None

    # ------------------------------------------------------------------
    # Poses
    # ------------------------------------------------------------------

    def pose_for(self, qualified_id: str | None) -> SpritePose | None:
        """Return this frame's cosmetic pose, or ``None`` outside M02."""
        if not self.active or qualified_id is None:
            return None
        if qualified_id == NOVA_QUALIFIED_ID:
            return self._nova_pose()
        if qualified_id == PIXEL_QUALIFIED_ID:
            return self._pixel_pose(qualified_id)
        if qualified_id == CRYSTAL_LANTERN_QUALIFIED_ID:
            return SpritePose(row="glow", column=LANTERN_FLICKER.frame_at(self.clock))
        if qualified_id == MOON_COMPASS_QUALIFIED_ID:
            return SpritePose(
                row="ring",
                column=COMPASS_SPIN.frame_at(self.clock),
                needle_angle=self.needle_angle(qualified_id),
                bob=round(1 + math.sin(self.clock * 1.8)),
            )
        return None

    def _nova_pose(self) -> SpritePose:
        row = "right" if self.facing in (Facing.LEFT, Facing.RIGHT) else self.facing.value
        flip = self.facing is Facing.LEFT
        if self.moving:
            column = NOVA_WALK.frame_at_distance(self.walk_distance, NOVA_STRIDE)
            index = NOVA_WALK.frames.index(column)
            # Fallback hints for the procedural sprite: dip on each contact,
            # lift the left boot then the right one across the cycle.
            return SpritePose(
                row=row,
                column=column,
                flip_x=flip,
                bob=(1, 0, 0, 0, 1, 0, 0, 0)[index],
                stride=(0, 1, 1, 1, 0, -1, -1, -1)[index],
            )
        if is_blinking(self.clock, period=3.8, duration=0.14, offset=0.9):
            return SpritePose(row=row, column="blink", flip_x=flip, blink=True)
        column = NOVA_IDLE.frame_at(self.still_time)
        return SpritePose(
            row=row, column=column, flip_x=flip, bob=(0, 0, 1, 0)[NOVA_IDLE.frames.index(column)]
        )

    def _pixel_pose(self, qualified_id: str) -> SpritePose:
        greet = self.greet_start.get(qualified_id)
        if greet is not None and self.clock - greet < PIXEL_GREET.duration:
            return SpritePose(row="idle", column=PIXEL_GREET.frame_at(self.clock - greet))
        if is_blinking(self.clock, period=4.3, duration=0.15, offset=2.1):
            return SpritePose(row="idle", column="blink", blink=True)
        column = PIXEL_IDLE.frame_at(self.clock)
        return SpritePose(
            row="idle", column=column, bob=(0, 1, 1, 1)[PIXEL_IDLE.frames.index(column)]
        )

    def needle_angle(self, qualified_id: str) -> float:
        angle = 0.36 * math.sin(self.clock * 1.4) + 0.1 * math.sin(self.clock * 3.7)
        burst = self._latest_burst(qualified_id, "discovery", DISCOVERY_DURATION)
        if burst is not None:
            angle += math.tau * ease_out((self.clock - burst.start) / DISCOVERY_DURATION)
        return angle

    def _latest_burst(self, qualified_id: str, kind: str, duration: float) -> Burst | None:
        for burst in reversed(self.bursts):
            if (
                burst.qualified_id == qualified_id
                and burst.kind == kind
                and 0 <= self.clock - burst.start < duration
            ):
                return burst
        return None

    # ------------------------------------------------------------------
    # Layers
    # ------------------------------------------------------------------

    def _log_once(self, layer: str) -> None:
        if layer not in self._failed_layers:
            self._failed_layers.add(layer)
            _LOGGER.exception("Trail presentation layer %r failed; skipping it", layer)

    def _guard(self, layer: str, draw, *args: object) -> object:  # type: ignore[no-untyped-def]
        try:
            return draw(*args)
        except Exception:
            self._log_once(layer)
            return None

    def draw_ground(self, renderer: object) -> None:
        """Ambient ground life: above the backdrop, below every entity."""
        if self.active:
            self._guard("ground", self._draw_ground, renderer)

    def _draw_ground(self, renderer: object) -> None:
        illustrated = illustrated_backdrop_available(renderer)
        draw_ground_life(renderer, self.clock, illustrated=illustrated)

    def draw_under(
        self, renderer: object, qualified_id: str | None, entity: _Positioned, color: Color
    ) -> None:
        """Shadows and light that sit beneath one entity's sprite."""
        if self.active and qualified_id is not None:
            self._guard("under", self._draw_under, renderer, qualified_id, entity, color)

    def draw_over(
        self, renderer: object, qualified_id: str | None, entity: _Positioned, color: Color
    ) -> None:
        """Effects that travel with one entity, drawn right after its sprite."""
        if self.active and qualified_id is not None:
            self._guard("over", self._draw_over, renderer, qualified_id, entity, color)

    def _draw_under(
        self, renderer: object, qualified_id: str, entity: _Positioned, color: Color
    ) -> None:
        x, y, width, height = _rect_of(entity)
        if qualified_id == NOVA_QUALIFIED_ID:
            pose = self._nova_pose()
            soft_shadow(
                renderer,
                x + width * 0.48,
                y + height * 0.955,
                width * 22 // 100 - pose.bob,
                max(2, height * 5 // 100),
                120,
            )
        elif qualified_id == PIXEL_QUALIFIED_ID:
            soft_shadow(
                renderer,
                x + width * 0.64,
                y + height * 0.955,
                width * 29 // 100,
                max(2, height * 5 // 100),
                120,
            )
        elif qualified_id == MOON_COMPASS_QUALIFIED_ID:
            cx, cy = x + width / 2, y + height * 0.45
            soft_shadow(
                renderer, cx, y + height * 0.95, width * 30 // 100, max(2, height * 7 // 100), 110
            )
            boost = 0.0
            burst = self._latest_burst(qualified_id, "discovery", DISCOVERY_DURATION)
            if burst is not None:
                boost = 0.5 * (1 - (self.clock - burst.start) / DISCOVERY_DURATION)
            pulse = 0.5 + 0.5 * math.sin(self.clock * 2.2)
            radius = max(8, min(width, height))
            # A dark moon-shadow ring first, so the light pops against the terrain.
            soft_shadow(renderer, cx, cy + height * 0.1, radius * 11 // 10, radius * 7 // 10, 70)
            # Outer violet aura, then the student-colored body light, then a hot core.
            glow(
                renderer,
                cx,
                cy,
                radius * 150 // 100,
                mix(color, (150, 110, 255), 0.55),
                0.22 + 0.05 * pulse + boost * 0.6,
            )
            glow(
                renderer,
                cx,
                cy,
                radius * 95 // 100,
                mix(color, _WHITE, 0.25),
                0.42 + 0.2 * pulse + boost,
            )
            glow(
                renderer,
                cx,
                cy,
                radius * 58 // 100,
                mix(color, _WHITE, 0.55),
                0.3 + 0.15 * pulse + boost,
            )
            # A two-tier rune ring on the ground: a bright inner band, a faint outer one.
            ring_y = y + height * 0.9
            for tier, (scale_x, scale_y, fade) in enumerate(
                ((0.62, 0.16, 0.2), (0.82, 0.22, 0.45))
            ):
                breathe = 1 + 0.03 * math.sin(self.clock * 1.6 + tier * 1.4)
                ellipse_ring(
                    renderer,
                    cx,
                    ring_y,
                    width * scale_x * breathe,
                    height * scale_y * breathe,
                    mix(mix(color, _WHITE, 0.45), _GROUND, fade - 0.12 * pulse - boost * 0.5),
                    2 if tier == 0 else 1,
                )
        elif qualified_id == CRYSTAL_LANTERN_QUALIFIED_ID:
            cx, cy = x + width / 2, y + height * 0.52
            flicker = 0.5 + 0.3 * math.sin(self.clock * 9.1) + 0.2 * math.sin(self.clock * 23.3)
            flare = self._flare_strength(qualified_id)
            soft_shadow(
                renderer, cx, y + height * 0.97, width * 24 // 100, max(2, height * 6 // 100), 100
            )
            glow(
                renderer,
                cx,
                cy,
                max(width, height) * 115 // 100,
                _LANTERN_LIGHT,
                0.46 + 0.1 * flicker + 0.4 * flare,
            )
            glow(
                renderer,
                cx,
                cy - height * 0.1,
                max(width, height) * 45 // 100,
                mix(color, _WHITE, 0.4),
                0.42 + 0.1 * flicker + 0.4 * flare,
            )

    def _flare_strength(self, qualified_id: str) -> float:
        burst = self._latest_burst(qualified_id, "flare", FLARE_DURATION)
        if burst is None:
            return 0.0
        return 1 - (self.clock - burst.start) / FLARE_DURATION

    def _draw_over(
        self, renderer: object, qualified_id: str, entity: _Positioned, color: Color
    ) -> None:
        x, y, width, height = _rect_of(entity)
        if qualified_id == MOON_COMPASS_QUALIFIED_ID:
            cx, cy = x + width / 2, y + height * 0.45
            light = mix(color, _WHITE, 0.72)
            for index in range(COMPASS_SPARKLES):
                # Slow orbits and staggered, eased twinkles read as deliberate
                # magic instead of a metronome.
                angle = (
                    self.clock * 0.55
                    + index * math.tau / COMPASS_SPARKLES
                    + 0.35 * math.sin(self.clock * 0.7 + index)
                )
                phase = (self.clock / (2.3 + 0.41 * index) + index * 0.29) % 1.0
                twinkle = math.sin(math.pi * phase) ** 3
                sx = cx + width * 0.64 * math.cos(angle)
                sy = cy + height * 0.58 * math.sin(angle)
                glow(renderer, sx, sy, 8, light, 0.5 * twinkle)
                sparkle(renderer, sx, sy, 1.5 + 4.0 * twinkle, light)
        elif qualified_id == CRYSTAL_LANTERN_QUALIFIED_ID:
            self._draw_lantern_over(renderer, qualified_id, x, y, width, height)

    def _draw_lantern_over(
        self, renderer: object, qualified_id: str, x: int, y: int, width: int, height: int
    ) -> None:
        cx, cy = x + width / 2, y + height * 0.5
        flare = self._flare_strength(qualified_id)
        ray = mix((255, 226, 150), _GROUND, 0.35 - 0.3 * flare)
        reach = height * 0.62
        for index in range(8):
            angle = self.clock * 0.25 + index * math.tau / 8
            length = 8 + 4 * math.sin(self.clock * 2.3 + index * 1.3) + 14 * flare
            inner = reach + 2
            renderer.draw_line(  # type: ignore[attr-defined]
                round(cx + inner * math.cos(angle)),
                round(cy + inner * 0.8 * math.sin(angle)),
                round(cx + (inner + length) * math.cos(angle)),
                round(cy + (inner + length) * 0.8 * math.sin(angle)),
                ray,
                2,
            )
        for index in range(LANTERN_SPARKS + (6 if flare > 0 else 0)):
            speed = (0.42 + 0.07 * index) if index < LANTERN_SPARKS else 1.4
            progress = self.clock * speed + index / LANTERN_SPARKS
            phase = progress % 1.0
            # Each rise drifts on its own arc, so the sparks never repeat a loop.
            drift = math.sin(math.floor(progress) * 2.7 + index * 1.9)
            sx = cx + 14 * drift * phase + 9 * math.sin(index * 2.1 + phase * 4.2)
            sy = cy - 6 - phase * (46 if index < LANTERN_SPARKS else 70)
            strength = math.sin(math.pi * phase)
            glow(renderer, sx, sy, 7, (255, 210, 120), 0.6 * strength)
            if strength > 0.3:
                renderer.draw_circle(  # type: ignore[attr-defined]
                    round(sx), round(sy), 1, mix(_GROUND, (255, 244, 200), strength)
                )
        if flare > 0:
            progress = 1 - flare
            ellipse_ring(
                renderer,
                cx,
                y + height * 0.9,
                20 + 70 * ease_out(progress),
                8 + 26 * ease_out(progress),
                mix((255, 226, 150), _GROUND, progress),
            )
        if qualified_id not in self._visited:
            # Destination marker: a bouncing arrow until the Lantern is visited.
            bob = 4 * abs(math.sin(self.clock * 3.0))
            tip = y - 4 - bob
            glow(renderer, cx, tip - 8, 14, (255, 210, 110), 0.45)
            renderer.draw_polygon(  # type: ignore[attr-defined]
                (
                    (round(cx - 9), round(tip - 13)),
                    (round(cx + 9), round(tip - 13)),
                    (round(cx), round(tip + 1)),
                ),
                _INK,
            )
            renderer.draw_polygon(  # type: ignore[attr-defined]
                (
                    (round(cx - 6), round(tip - 11)),
                    (round(cx + 6), round(tip - 11)),
                    (round(cx), round(tip - 2)),
                ),
                (255, 214, 96),
            )

    # ------------------------------------------------------------------
    # Overlay: air life, bursts, celebration, prompts, bubble, labels
    # ------------------------------------------------------------------

    def draw_overlay(self, renderer: object, view: TrailView) -> tuple[TextOp, ...]:
        """Draw overlay shapes; return overlay text to draw after the HUD."""
        if not self.active:
            return ()
        self._guard("foreground", draw_scenery_plate, renderer, MEADOW_FOREGROUND)
        self._guard("air", draw_air_life, renderer, self.clock)
        self._guard("bursts", self._draw_bursts, renderer, view)
        self._guard("celebration", self._draw_confetti, renderer)
        if not supports(renderer, "draw_rounded_rect", "measure_text", "draw_text"):
            return ()
        self._guard("hud-panel", self._draw_hud_panel, renderer, view)
        texts: list[TextOp] = []
        for layer, draw in (
            ("prompt", self._draw_prompt),
            ("bubble", self._draw_bubble),
            ("label", self._draw_label),
            ("banner", self._draw_banner),
        ):
            result = self._guard(layer, draw, renderer, view)
            if result:
                texts.extend(result)  # type: ignore[arg-type]
        return tuple(texts)

    def draw_overlay_text(self, renderer: object, texts: Sequence[TextOp]) -> None:
        """Draw overlay text after the HUD so mission text stays first."""
        for text, x, y, color, size in texts:
            self._guard("text", renderer.draw_text, text, max(0, x), max(0, y), color, size)  # type: ignore[attr-defined]

    def _entity(self, view: TrailView, qualified_id: str) -> _Positioned | None:
        for item in view.objects:
            if item.qualified_id == qualified_id:
                return item.world_object
        for npc in view.npcs:
            if npc.qualified_id == qualified_id:
                return npc.character
        return None

    def _draw_bursts(self, renderer: object, view: TrailView) -> None:
        for burst in self.bursts:
            elapsed = self.clock - burst.start
            if burst.kind == "flare" or not 0 <= elapsed < DISCOVERY_DURATION:
                continue
            entity = self._entity(view, burst.qualified_id)
            if entity is None:
                continue
            x, y, width, height = _rect_of(entity)
            cx, cy = x + width / 2, y + height * 0.45
            progress = elapsed / DISCOVERY_DURATION
            ellipse_ring(
                renderer,
                cx,
                cy,
                16 + 60 * ease_out(progress),
                10 + 36 * ease_out(progress),
                mix((255, 240, 190), _GROUND, progress),
            )
            for index in range(BURST_PARTICLES):
                angle = index * math.tau / BURST_PARTICLES + 0.3
                reach = 18 + 58 * ease_out(progress)
                px = cx + reach * math.cos(angle)
                py = cy + reach * 0.75 * math.sin(angle) - 10 * progress
                size = 5 * (1 - progress) + 1
                color = _WHITE if index % 2 else (255, 222, 120)
                glow(renderer, px, py, 8, color, 0.5 * (1 - progress))
                sparkle(renderer, px, py, size, color)

    def _draw_confetti(self, renderer: object) -> None:
        if self.celebration_start is None:
            return
        elapsed = self.clock - self.celebration_start
        if not 0 <= elapsed < CELEBRATION_DURATION:
            return
        # Confetti falls from just below the HUD band so mission text stays readable.
        for index in range(CONFETTI_PIECES):
            seed = (index * 7919 + 13) % 997
            x0 = 20 + seed * (SCREEN_WIDTH - 40) / 997
            fall = 150 + (index % 5) * 30
            y = HUD_BOTTOM + 6 - (index % 6) * 22 + elapsed * fall
            if y > SCREEN_HEIGHT + 8 or y < HUD_BOTTOM + 6:
                continue
            x = x0 + 16 * math.sin(elapsed * 3 + index)
            spin = elapsed * (4 + index % 3) + index
            half_w = 4 * abs(math.cos(spin)) + 1
            half_h = 2.5
            color = _CONFETTI[index % len(_CONFETTI)]
            renderer.draw_polygon(  # type: ignore[attr-defined]
                (
                    (round(x - half_w), round(y - half_h)),
                    (round(x + half_w), round(y - half_h + 1)),
                    (round(x + half_w), round(y + half_h)),
                    (round(x - half_w), round(y + half_h - 1)),
                ),
                color,
            )

    def hud_panel_rects(self, renderer, view: TrailView) -> tuple[Rect, ...]:  # type: ignore[no-untyped-def]
        """Two rounded rects hugging the HUD rows: the short rows and the long one."""
        state = "Complete" if view.mission_is_complete else "Incomplete"
        rows = (
            f"Visited {view.visited_count} / {view.total_objects}",
            f"Mission: {view.mission.title}",
            view.mission.instructions,
            f"Mission state: {state}",
        )
        widths = [renderer.measure_text(text, HUD_FONT)[0] for text in rows]
        row_height = renderer.measure_text("Ag", HUD_FONT)[1]
        pad = 10
        short = max(widths[0], widths[1], widths[3])
        top = HUD_ROWS_Y[0] - 8
        return (
            (HUD_TEXT_X - pad, top, short + 2 * pad, HUD_ROWS_Y[3] + row_height + 8 - top),
            (HUD_TEXT_X - pad, HUD_ROWS_Y[2] - 6, widths[2] + 2 * pad, row_height + 12),
        )

    def _draw_hud_panel(self, renderer, view: TrailView) -> None:  # type: ignore[no-untyped-def]
        if not supports(renderer, "draw_translucent_panel", "measure_text"):
            return
        renderer.draw_translucent_panel(
            self.hud_panel_rects(renderer, view),
            _HUD_PANEL,
            _HUD_PANEL_ALPHA,
            12,
            _HUD_EDGE,
            70,
            True,
        )

    def _player_rect(self, view: TrailView) -> Rect:
        return nova_visible_rect(view.player)

    def prompt_text(self, view: TrailView) -> str | None:
        """Return the proximity prompt for the current valid target, if any."""
        target_id = view.target_qualified_id
        if target_id is None:
            return None
        if (
            self.bubble is not None
            and self.bubble.qualified_id == target_id
            and (self.clock - self.bubble.start < BUBBLE_DURATION)
        ):
            return None
        for burst in reversed(self.bursts):
            if burst.qualified_id == target_id and self.clock - burst.start < PROMPT_PAUSE:
                return None
        greet = self.greet_start.get(target_id)
        if greet is not None and self.clock - greet < PROMPT_PAUSE:
            return None
        for item in view.objects:
            if item.qualified_id == target_id:
                return f"Inspect {item.world_object.name}"
        for npc in view.npcs:
            if npc.qualified_id == target_id:
                return f"Talk to {npc.character.name}"
        return None

    def _draw_prompt(self, renderer, view: TrailView) -> tuple[TextOp, ...]:  # type: ignore[no-untyped-def]
        text = self.prompt_text(view)
        target_id = view.target_qualified_id
        entity = None if target_id is None else self._entity(view, target_id)
        if text is None or entity is None:
            return ()
        text_width, text_height = renderer.measure_text(text, _PROMPT_FONT)
        key = 22
        width = 8 + key + 8 + text_width + 10
        height = max(key, text_height) + 10
        x, y, w, h = _rect_of(entity)
        if target_id == PIXEL_QUALIFIED_ID:
            x, y, w, h = pixel_visible_rect(entity)
        cx = x + w // 2
        rect = place_panel(
            (width, height),
            (
                (cx - width // 2, y - height - 6),
                (cx - width // 2, y + h + 6),
                (x + w + 8, y + h // 2 - height // 2),
                (x - width - 8, y + h // 2 - height // 2),
            ),
            (self._player_rect(view),),
        )
        px, py, _, _ = rect
        if supports(renderer, "draw_translucent_panel"):
            renderer.draw_translucent_panel(((px, py, width, height),), _PANEL, 222, 9, _GOLD, 235)
        else:
            renderer.draw_rounded_rect(px, py, width, height, _PANEL, 8, _GOLD, 2)
        key_x, key_y = px + 8, py + (height - key) // 2
        renderer.draw_rounded_rect(key_x, key_y, key, key, _KEY, 5, _INK, 1)
        key_width, key_height = renderer.measure_text("E", _PROMPT_FONT)
        return (
            (
                "E",
                key_x + (key - key_width) // 2,
                key_y + (key - key_height) // 2 + 1,
                _INK,
                _PROMPT_FONT,
            ),
            (
                text,
                key_x + key + 8,
                py + (height - text_height) // 2 + 1,
                _PANEL_TEXT,
                _PROMPT_FONT,
            ),
        )

    def _draw_bubble(self, renderer, view: TrailView) -> tuple[TextOp, ...]:  # type: ignore[no-untyped-def]
        bubble = self.bubble
        if bubble is None or not 0 <= self.clock - bubble.start < BUBBLE_DURATION:
            return ()
        speaker = self._entity(view, bubble.qualified_id)
        if speaker is None:
            return ()
        lines = wrap_text(
            bubble.text, _BUBBLE_TEXT_WIDTH, lambda line: renderer.measure_text(line, _BUBBLE_FONT)
        )
        if not lines:
            return ()
        line_height = renderer.measure_text("Ag", _BUBBLE_FONT)[1] + 2
        text_width = max(renderer.measure_text(line, _BUBBLE_FONT)[0] for line in lines)
        width, height = text_width + 24, line_height * len(lines) + 18
        sx, sy, sw, sh = (
            pixel_visible_rect(speaker)
            if bubble.qualified_id == PIXEL_QUALIFIED_ID
            else _rect_of(speaker)
        )
        head_y = sy + sh * 30 // 100
        avoid = [self._player_rect(view), *(_rect_of(item.world_object) for item in view.objects)]
        rect = place_panel(
            (width, height),
            (
                (sx + sw + 14, head_y - height // 2),
                (sx - width - 14, head_y - height // 2),
                (sx + sw // 2 - width // 2, sy - height - 14),
                (sx + sw // 2 - width // 2, sy + sh + 14),
            ),
            avoid,
        )
        bx, by, _, _ = rect
        anchor_x = sx + sw // 2
        anchor_y = head_y
        if bx >= sx + sw:
            tail = (
                (bx + 2, by + height // 2 - 7),
                (bx + 2, by + height // 2 + 7),
                (sx + sw + 2, anchor_y),
            )
        elif bx + width <= sx:
            tail = (
                (bx + width - 2, by + height // 2 - 7),
                (bx + width - 2, by + height // 2 + 7),
                (sx - 2, anchor_y),
            )
        elif by + height <= sy:
            tail = (
                (anchor_x - 7, by + height - 2),
                (anchor_x + 7, by + height - 2),
                (anchor_x, sy - 2),
            )
        else:
            tail = ((anchor_x - 7, by + 2), (anchor_x + 7, by + 2), (anchor_x, sy + sh + 2))
        renderer.draw_polygon(tail, _INK)
        renderer.draw_rounded_rect(bx, by, width, height, _BUBBLE, 12, _INK, 2)
        inner_tail = tuple(
            (
                round(px + (sum(p[0] for p in tail) / 3 - px) * 0.3),
                round(py + (sum(p[1] for p in tail) / 3 - py) * 0.3),
            )
            for px, py in tail
        )
        renderer.draw_polygon(inner_tail, _BUBBLE)
        return tuple(
            (line, bx + 12, by + 10 + index * line_height, _BUBBLE_TEXT, _BUBBLE_FONT)
            for index, line in enumerate(lines)
        )

    def _draw_label(self, renderer, view: TrailView) -> tuple[TextOp, ...]:  # type: ignore[no-untyped-def]
        label = self.label
        if label is None or not 0 <= self.clock - label.start < LABEL_DURATION:
            return ()
        entity = self._entity(view, label.qualified_id)
        if entity is None:
            return ()
        progress = (self.clock - label.start) / LABEL_DURATION
        text_width, text_height = renderer.measure_text(label.text, _LABEL_FONT)
        width, height = text_width + 24, text_height + 12
        x, y, w, h = _rect_of(entity)
        rise = round(12 * ease_out(progress))
        rect = place_panel(
            (width, height),
            (
                (x + w // 2 - width // 2, y - height - 10 - rise),
                (x + w // 2 - width // 2, y + h + 8 + rise),
            ),
            (self._player_rect(view),),
        )
        lx, ly, _, _ = rect
        renderer.draw_rounded_rect(lx, ly, width, height, _LABEL, 10, _INK, 2)
        sparkle(renderer, lx - 2, ly + 2, 5, _WHITE)
        sparkle(renderer, lx + width + 1, ly + height - 3, 4, _WHITE)
        return ((label.text, lx + 12, ly + 7, _LABEL_TEXT, _LABEL_FONT),)

    def _draw_banner(self, renderer, view: TrailView) -> tuple[TextOp, ...]:  # type: ignore[no-untyped-def]
        del view
        if self.celebration_start is None:
            return ()
        elapsed = self.clock - self.celebration_start
        if not 0 <= elapsed < CELEBRATION_DURATION:
            return ()
        text = "Mission complete!"
        text_width, text_height = renderer.measure_text(text, _BANNER_FONT)
        width, height = text_width + 76, text_height + 18
        x = (SCREEN_WIDTH - width) // 2
        y = HUD_BOTTOM + 10
        renderer.draw_rounded_rect(x, y, width, height, _BANNER, 14, _GOLD, 3)
        twinkle = 0.5 + 0.5 * math.sin(elapsed * 8)
        for star_x in (x + 20, x + width - 20):
            sparkle(renderer, star_x, y + height / 2, 6 + 3 * twinkle, (255, 222, 120))
        return ((text, x + 38, y + 10, _BANNER_TEXT, _BANNER_FONT),)
