"""Cosmetic presentation layer for the S02-S04 (M02-M04) Classroom Trail.

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
* The S04 Moonlit Guide breathes, blinks, and gestures as it greets; its
  moon-staff orb glows, a small speech cue floats over it until it has been
  spoken to, and its greeting gets a larger bubble sized to the whole line.

It is allow-listed by ``_mission_presentation``: M02 gets every layer, M03
gets the shared ones (no discovery label or celebration, since the student's
own clue and reveal tell that story) and draws its canonical Compass with the
same trusted art, and M04 gets the shared ones plus the Guide's talk cue and
dialogue focus, without the Lantern's destination marker. For every other
Trail it is inert, so S01 and S05+ rendering is unchanged. It never mutates
the scene, never raises into gameplay, and bounds every effect count.

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
    draw_scenery_plate,
    illustrated_backdrop_available,
)
from engine.rendering._classroom_sprites import (
    COMPASS_HALO_FRAME,
    COMPASS_HALO_SHEET_ID,
    CRYSTAL_LANTERN_QUALIFIED_ID,
    MOON_COMPASS_QUALIFIED_ID,
    MOONLIT_GUIDE_QUALIFIED_ID,
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
from engine.rendering._mission_presentation import MissionPresentation, mission_presentation

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
#: The ground rune circle turns one rune (30 degrees) every 3.5 seconds.
COMPASS_HALO: Final = AnimationClip("halo", tuple(f"spin-{index:02d}" for index in range(16)), 0.22)
PIXEL_IDLE: Final = AnimationClip("idle", ("idle-0", "idle-1", "idle-2", "idle-3"), 0.36)
PIXEL_GREET: Final = AnimationClip(
    "greet", ("greet-0", "greet-1", "greet-2", "greet-1", "greet-2", "greet-3"), 0.2, loop=False
)
GUIDE_IDLE: Final = AnimationClip("idle", ("idle-0", "idle-1", "idle-2", "idle-3"), 0.42)
#: Lift the hand, open it, wave once, settle: a single gesture as it speaks.
GUIDE_TALK: Final = AnimationClip(
    "talk", ("talk-0", "talk-1", "talk-2", "talk-1", "talk-2", "talk-3"), 0.22, loop=False
)
#: The staff's moon orb in the Guide's 100 x 100 box (``scripts/art/characters``).
GUIDE_ORB: Final = (0.24, 0.19)
LANTERN_FLICKER: Final = AnimationClip(
    "flicker",
    ("flicker-0", "flicker-2", "flicker-1", "flicker-3", "flicker-1", "flicker-0", "flicker-3"),
    0.12,
)

BUBBLE_DURATION: Final = 4.0
#: Dialogue-focus bubbles stay up long enough to read the whole greeting aloud:
#: a base plus a per-word allowance, never shorter than a normal bubble.
DIALOGUE_BASE: Final = 2.0
DIALOGUE_PER_WORD: Final = 0.4
DIALOGUE_MAX_DURATION: Final = 14.0
#: Marks text that was shortened to fit, so nothing is ever clipped silently.
ELLIPSIS: Final = "…"
#: Trailing punctuation and spaces dropped before an ellipsis.
_TRIM: Final = " ,;:—-"
DISCOVERY_DURATION: Final = 0.9
LABEL_DURATION: Final = 1.8
FLARE_DURATION: Final = 1.2
CELEBRATION_DURATION: Final = 3.2
PROMPT_PAUSE: Final = 0.9
MAX_BURSTS: Final = 4
#: Wrapped and fitted text is measured once per distinct line, not per frame.
MAX_CACHED_LAYOUTS: Final = 16
BURST_PARTICLES: Final = 14
CONFETTI_PIECES: Final = 36
LANTERN_SPARKS: Final = 5
COMPASS_SPARKLES: Final = 4

#: Mirrors the Trail HUD layout in ``_classroom_trail_scene`` (a test keeps
#: them equal). The panel only sits behind that text; the text is unchanged.
HUD_TEXT_X: Final = 20
HUD_ROWS_Y: Final = (20, 55, 85, 115)
HUD_FONT: Final = 24
#: The bottom feedback line and the "Trail complete!" line (also mirrored).
FEEDBACK_TEXT_X: Final = 360
FEEDBACK_TEXT_Y: Final = 560
COMPLETE_TEXT_Y: Final = 520
FEEDBACK_FONT: Final = 28
_HUD_PANEL: Final[Color] = (14, 18, 48)
_HUD_PANEL_ALPHA: Final = 168
_HUD_EDGE: Final[Color] = (178, 190, 255)

_PROMPT_FONT: Final = 22
_BUBBLE_FONT: Final = 22
_LABEL_FONT: Final = 24
_BANNER_FONT: Final = 34
_BUBBLE_TEXT_WIDTH: Final = 230
_BUBBLE_MAX_LINES: Final = 4
#: Dialogue focus: a larger font that stays legible at a half-scale share,
#: a wider column, and up to six lines before an explicit ellipsis.
_DIALOGUE_FONT: Final = 24
_DIALOGUE_TEXT_WIDTH: Final = 340
_DIALOGUE_MAX_LINES: Final = 6
_TALK_CUE: Final[Color] = (250, 248, 236)
_ORB_LIGHT: Final[Color] = (150, 220, 255)

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
_SHADOW_INK: Final[Color] = (4, 6, 16)
_DUST: Final[Color] = (160, 180, 186)
_SCREEN_LIGHT: Final[Color] = (90, 230, 230)
#: Distance between Nova's foot contacts (two per 60 px walk cycle).
STEP_LENGTH: Final = NOVA_STRIDE * 4
_WAYPOINT: Final[Color] = (255, 204, 84)
_WAYPOINT_LIGHT: Final[Color] = (255, 242, 186)
_WAYPOINT_SHADE: Final[Color] = (206, 128, 44)
_NAME_TAG: Final[Color] = (58, 86, 214)
_NAME_FONT: Final = 20
_FEEDBACK_PANEL: Final[Color] = (10, 14, 34)
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
    duration: float = BUBBLE_DURATION


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


def guide_visible_rect(npc: _Positioned) -> Rect:
    """The part of the Guide's box the art covers (staff and hood to hem)."""
    return (
        npc.x + npc.width * 20 // 100,
        npc.y + npc.height * 6 // 100,
        npc.width * 64 // 100,
        npc.height * 92 // 100,
    )


def _split_word(word: str, max_width: int, measure: Callable[[str], tuple[int, int]]) -> list[str]:
    """Break one word wider than the column into pieces that each fit."""
    if measure(word)[0] <= max_width:
        return [word]
    pieces: list[str] = []
    current = ""
    for character in word:
        if current and measure(current + character)[0] > max_width:
            pieces.append(current)
            current = character
        else:
            current += character
    if current:
        pieces.append(current)
    return pieces


def fit_line(text: str, max_width: int, measure: Callable[[str], tuple[int, int]]) -> str:
    """Return *text* if it fits, else its longest prefix that fits plus an ellipsis."""
    if measure(text)[0] <= max_width:
        return text
    words = text.split()
    while len(words) > 1:
        words.pop()
        candidate = " ".join(words).rstrip(_TRIM) + ELLIPSIS
        if measure(candidate)[0] <= max_width:
            return candidate
    head = words[0] if words else ""
    while head and measure(head + ELLIPSIS)[0] > max_width:
        head = head[:-1]
    return head + ELLIPSIS


def wrap_text(
    text: str,
    max_width: int,
    measure: Callable[[str], tuple[int, int]],
    max_lines: int = _BUBBLE_MAX_LINES,
) -> tuple[str, ...]:
    """Greedy word wrap using the renderer's own text measurement.

    A word wider than the column is broken across lines. Text beyond
    *max_lines* is never dropped silently: the last line ends in an ellipsis.
    """
    lines: list[str] = []
    current = ""
    for word in text.split():
        for piece in _split_word(word, max_width, measure):
            candidate = f"{current} {piece}" if current else piece
            if current and measure(candidate)[0] > max_width:
                lines.append(current)
                current = piece
            else:
                current = candidate
    if current:
        lines.append(current)
    if len(lines) <= max_lines:
        return tuple(lines)
    kept = lines[:max_lines]
    last = kept[-1]
    while last and measure(last + ELLIPSIS)[0] > max_width:
        last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
    kept[-1] = last.rstrip(_TRIM) + ELLIPSIS
    return tuple(kept)


def _overlap_area(first: Rect, second: Rect) -> int:
    width = min(first[0] + first[2], second[0] + second[2]) - max(first[0], second[0])
    height = min(first[1] + first[3], second[1] + second[3]) - max(first[1], second[1])
    return max(0, width) * max(0, height)


def place_clear_panel(
    size: tuple[int, int], candidates: Sequence[tuple[int, int]], avoid: Sequence[Rect]
) -> Rect:
    """Clamp every candidate on screen and pick the one covering the least of *avoid*.

    Unlike :func:`place_panel` the fallback is never simply the first
    candidate pushed on screen (which can land on the speaker itself).
    """
    best: Rect | None = None
    best_cover = -1
    for x, y in candidates:
        rect = _clamp((x, y, size[0], size[1]))
        cover = sum(_overlap_area(rect, other) for other in avoid)
        if best is None or cover < best_cover:
            best, best_cover = rect, cover
        if cover == 0:
            break
    assert best is not None
    return best


class TrailPresentation:
    """Observe one Trail scene and draw its mission-gated cosmetic layer."""

    def __init__(self, mission_id: str, start: tuple[float, float] | None = None) -> None:
        policy = mission_presentation(mission_id)
        self.active = policy is not None
        #: Inactive missions get the empty policy: no extras and no aliases.
        self.policy = policy or MissionPresentation()
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
        self._spoken: frozenset[str] = frozenset()
        self._layouts: dict[tuple[object, ...], object] = {}
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
        if self._previous_complete is False and complete and self.policy.celebration:
            self.celebration_start = self.clock
        self._previous_complete = complete
        self._visited = view.visited_qualified_ids
        # Read-only NPC evidence (M04's completion state); views without it
        # simply show every talk cue.
        spoken = getattr(view, "spoken_npc_ids", None)
        self._spoken = spoken if isinstance(spoken, frozenset) else frozenset()

    def _react_to_interaction(self, view: TrailView, target_id: str) -> None:
        trail_object = next((item for item in view.objects if item.qualified_id == target_id), None)
        if trail_object is not None:
            newly_visited = target_id not in self._visited
            role = self.sprite_identity(target_id)
            kind = {
                MOON_COMPASS_QUALIFIED_ID: "discovery",
                CRYSTAL_LANTERN_QUALIFIED_ID: "flare",
            }.get(role, "pulse")
            self.bursts = (*self.bursts, Burst(kind, target_id, self.clock))[-MAX_BURSTS:]
            if newly_visited and role == MOON_COMPASS_QUALIFIED_ID and self.policy.discovery_label:
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
        if len(lines) != 1:
            self.bubble = None
            return
        duration = BUBBLE_DURATION
        if self.policy.dialogue_focus:
            reading = DIALOGUE_BASE + DIALOGUE_PER_WORD * len(lines[0].split())
            duration = max(BUBBLE_DURATION, min(DIALOGUE_MAX_DURATION, reading))
        self.bubble = Bubble(target_id, lines[0], self.clock, duration)

    # ------------------------------------------------------------------
    # Poses
    # ------------------------------------------------------------------

    def sprite_identity(self, qualified_id: str | None) -> str | None:
        """The trusted-art identity *qualified_id* is drawn as in this mission.

        Only an active mission's explicit aliases apply, so every other Trail
        keeps its exact package identities (and their rectangle fallback).
        """
        if qualified_id is None:
            return None
        return self.policy.sprite_aliases.get(qualified_id, qualified_id)

    def pose_for(self, qualified_id: str | None) -> SpritePose | None:
        """Return this frame's cosmetic pose, or ``None`` outside M02/M03."""
        if not self.active or qualified_id is None:
            return None
        role = self.sprite_identity(qualified_id)
        if role == NOVA_QUALIFIED_ID:
            return self._nova_pose()
        if role == PIXEL_QUALIFIED_ID:
            return self._pixel_pose(qualified_id)
        if role == MOONLIT_GUIDE_QUALIFIED_ID:
            return self._guide_pose(qualified_id)
        if role == CRYSTAL_LANTERN_QUALIFIED_ID:
            return SpritePose(row="glow", column=LANTERN_FLICKER.frame_at(self.clock))
        if role == MOON_COMPASS_QUALIFIED_ID:
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

    def _guide_pose(self, qualified_id: str) -> SpritePose:
        greet = self.greet_start.get(qualified_id)
        if greet is not None and self.clock - greet < GUIDE_TALK.duration:
            return SpritePose(row="idle", column=GUIDE_TALK.frame_at(self.clock - greet))
        if is_blinking(self.clock, period=4.9, duration=0.16, offset=1.3):
            return SpritePose(row="idle", column="blink", blink=True)
        column = GUIDE_IDLE.frame_at(self.clock)
        return SpritePose(
            row="idle", column=column, bob=(0, 0, 1, 0)[GUIDE_IDLE.frames.index(column)]
        )

    def _greet_strength(self, qualified_id: str, duration: float) -> float:
        """1 at the moment an NPC greets, easing to 0 over *duration* seconds."""
        greet = self.greet_start.get(qualified_id)
        if greet is None or not 0 <= self.clock - greet < duration:
            return 0.0
        return 1 - (self.clock - greet) / duration

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

    def _layout(self, key: tuple[object, ...], compute: Callable[[], object]) -> object:
        """Bounded memo for text layout, so steady frames do not re-measure."""
        if key not in self._layouts:
            if len(self._layouts) >= MAX_CACHED_LAYOUTS:
                self._layouts.clear()
            self._layouts[key] = compute()
        return self._layouts[key]

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
        role = self.sprite_identity(qualified_id)
        if role == NOVA_QUALIFIED_ID:
            pose = self._nova_pose()
            soft_shadow(
                renderer,
                x + width * 0.48,
                y + height * 0.955,
                width * 22 // 100 - pose.bob,
                max(2, height * 5 // 100),
                120,
            )
            if self.moving:
                self._draw_step_dust(renderer, x + width * 0.48, y + height * 0.95)
        elif role == PIXEL_QUALIFIED_ID:
            soft_shadow(
                renderer,
                x + width * 0.64,
                y + height * 0.955,
                width * 29 // 100,
                max(2, height * 5 // 100),
                120,
            )
            # Pixel's screen spills a little cyan light, brighter while it greets.
            greet = self.greet_start.get(qualified_id)
            cheer = (
                1 - (self.clock - greet) / PIXEL_GREET.duration
                if greet is not None and 0 <= self.clock - greet < PIXEL_GREET.duration
                else 0.0
            )
            glow(
                renderer,
                x + width * 0.65,
                y + height * 0.36,
                max(8, width * 42 // 100),
                _SCREEN_LIGHT,
                0.12 + 0.03 * math.sin(self.clock * 1.7) + 0.2 * cheer,
            )
        elif role == MOONLIT_GUIDE_QUALIFIED_ID:
            soft_shadow(
                renderer,
                x + width * 0.53,
                y + height * 0.96,
                width * 30 // 100,
                max(2, height * 5 // 100),
                125,
            )
            # Moonlight from the staff pools softly on the ground around the hem.
            glow(
                renderer,
                x + width * 0.4,
                y + height * 0.9,
                max(10, width * 40 // 100),
                _ORB_LIGHT,
                0.1 + 0.03 * math.sin(self.clock * 1.3),
            )
        elif role == MOON_COMPASS_QUALIFIED_ID:
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
            # The trusted rune circle on the ground, in the student's color; the
            # line-drawn two-tier ring is its fallback.
            ring_y = y + height * 0.9
            if self._draw_compass_halo(renderer, cx, ring_y, color):
                return
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
        elif role == CRYSTAL_LANTERN_QUALIFIED_ID:
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
                0.4 + 0.08 * flicker + 0.4 * flare,
            )
            glow(
                renderer,
                cx,
                cy - height * 0.1,
                max(width, height) * 45 // 100,
                mix(color, _WHITE, 0.4),
                0.42 + 0.1 * flicker + 0.4 * flare,
            )

    def _draw_step_dust(self, renderer: object, foot_x: float, foot_y: float) -> None:
        """One soft puff kicked up behind Nova at each foot contact."""
        if not supports(renderer, "draw_soft_ellipse"):
            return
        age = (self.walk_distance % STEP_LENGTH) / STEP_LENGTH
        if age >= 0.6:
            return
        behind = {Facing.LEFT: 1, Facing.RIGHT: -1}.get(self.facing, 0)
        renderer.draw_soft_ellipse(  # type: ignore[attr-defined]
            round(foot_x + behind * (8 + 10 * age)),
            round(foot_y - 2 - 5 * age),
            round(4 + 6 * age),
            round(2 + 3 * age),
            _DUST,
            round(72 * (1 - age / 0.6)),
        )

    def _draw_compass_halo(
        self, renderer: object, cx: float, ground_y: float, color: Color
    ) -> bool:
        """Lay the tinted rune circle under the Compass; ``False`` when unavailable."""
        draw_frame = getattr(renderer, "draw_sprite_frame", None)
        if draw_frame is None:
            return False
        width, height = COMPASS_HALO_FRAME
        return bool(
            draw_frame(
                COMPASS_HALO_SHEET_ID,
                "halo",
                COMPASS_HALO.frame_at(self.clock),
                round(cx - width / 2),
                round(ground_y - height / 2),
                width,
                height,
                # A fixed tint per student color, so the tinted frames cache once.
                tint=mix(color, _WHITE, 0.4),
            )
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
        role = self.sprite_identity(qualified_id)
        if role == MOON_COMPASS_QUALIFIED_ID:
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
        elif role == CRYSTAL_LANTERN_QUALIFIED_ID:
            self._draw_lantern_over(renderer, qualified_id, x, y, width, height)
        elif role == MOONLIT_GUIDE_QUALIFIED_ID:
            # The staff's moon orb breathes, and brightens while the Guide speaks.
            cheer = self._greet_strength(qualified_id, GUIDE_TALK.duration + 0.6)
            glow(
                renderer,
                x + width * GUIDE_ORB[0],
                y + height * GUIDE_ORB[1],
                max(8, width * 24 // 100),
                _ORB_LIGHT,
                0.2 + 0.07 * math.sin(self.clock * 1.9) + 0.3 * cheer,
            )

    def _draw_lantern_over(
        self, renderer: object, qualified_id: str, x: int, y: int, width: int, height: int
    ) -> None:
        cx, cy = x + width / 2, y + height * 0.5
        flare = self._flare_strength(qualified_id)
        if flare > 0:
            # Light bursts outward only when the Lantern is inspected.
            ray = mix((255, 226, 150), _GROUND, 0.75 - 0.7 * flare)
            reach = height * 0.62
            for index in range(8):
                angle = index * math.tau / 8 + 0.2
                length = 6 + 20 * ease_out(1 - flare)
                inner = reach + 2 + 10 * ease_out(1 - flare)
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
        if self.policy.lantern_waypoint and qualified_id not in self._visited:
            self._draw_waypoint(renderer, cx, y - 4)

    def _draw_waypoint(self, renderer: object, cx: float, tip_y: float) -> None:
        """Destination marker: a floating gold gem pointing down at the Lantern."""
        float_y = 3.0 * math.sin(self.clock * 2.4)
        tip = tip_y - 2 + float_y
        top, mid, half = tip - 26, tip - 18, 9.0
        glow(renderer, cx, mid, 20, (255, 206, 110), 0.38 + 0.08 * math.sin(self.clock * 2.4))
        draw_polygon = renderer.draw_polygon  # type: ignore[attr-defined]

        def kite(inset: float) -> tuple[tuple[int, int], ...]:
            return (
                (round(cx), round(top + inset)),
                (round(cx + half - inset), round(mid)),
                (round(cx), round(tip - inset * 1.4)),
                (round(cx - half + inset), round(mid)),
            )

        draw_polygon(kite(0), _INK)
        draw_polygon(kite(2), _WAYPOINT)
        lit = kite(2)
        # Moonlit upper-right facet and a shaded lower-left one give it volume.
        draw_polygon((lit[0], lit[1], (round(cx), round(mid))), _WAYPOINT_LIGHT)
        draw_polygon(((round(cx), round(mid)), lit[3], lit[2]), _WAYPOINT_SHADE)
        twinkle = 0.5 + 0.5 * math.sin(self.clock * 3.1)
        sparkle(renderer, cx + 2, top + 6, 1.5 + 2.0 * twinkle, _WHITE)

    # ------------------------------------------------------------------
    # Overlay: air life, bursts, celebration, prompts, bubble, labels
    # ------------------------------------------------------------------

    def draw_overlay(self, renderer: object, view: TrailView) -> tuple[TextOp, ...]:
        """Draw overlay shapes; return overlay text to draw after the HUD."""
        if not self.active:
            return ()
        self._guard("foreground", draw_scenery_plate, renderer, MEADOW_FOREGROUND)
        self._guard("air", draw_air_life, renderer, self.clock)
        if self.policy.talk_cue:
            self._guard("talk-cue", self._draw_talk_cues, renderer, view)
        self._guard("bursts", self._draw_bursts, renderer, view)
        self._guard("celebration", self._draw_confetti, renderer)
        if not supports(renderer, "draw_rounded_rect", "measure_text", "draw_text"):
            return ()
        self._guard("hud-panel", self._draw_hud_panel, renderer, view)
        self._guard("feedback-panel", self._draw_feedback_panel, renderer, view)
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

    def talk_cue_ids(self, view: TrailView) -> tuple[str, ...]:
        """Interactable NPCs not yet spoken to: exactly what M04 still needs."""
        if not self.policy.talk_cue:
            return ()
        return tuple(
            npc.qualified_id
            for npc in view.npcs
            if npc.conversation_lines and npc.qualified_id not in self._spoken
        )

    def _draw_talk_cues(self, renderer: object, view: TrailView) -> None:
        if not supports(renderer, "draw_rounded_rect", "draw_polygon", "draw_circle"):
            return
        bubble = self.bubble
        for qualified_id in self.talk_cue_ids(view):
            if (
                bubble is not None
                and bubble.qualified_id == qualified_id
                and 0 <= self.clock - bubble.start < bubble.duration
            ):
                continue
            entity = self._entity(view, qualified_id)
            if entity is None:
                continue
            x, y, w, _ = self._anchor_rect(qualified_id, entity)
            self._draw_talk_cue(renderer, x + w * 0.55, y - 6)

    def _draw_talk_cue(self, renderer: object, cx: float, bottom: float) -> None:
        """A small floating speech balloon with three dots: "talk to me"."""
        float_y = 3.0 * math.sin(self.clock * 2.2)
        width, height = 30, 20
        left = round(cx - width / 2)
        top = round(max(HUD_BOTTOM + 2, bottom - height - 8 + float_y))
        glow(renderer, cx, top + height / 2, 22, (200, 220, 255), 0.3)
        renderer.draw_polygon(  # type: ignore[attr-defined]
            (
                (left + 8, top + height - 2),
                (left + 16, top + height - 2),
                (left + 9, top + height + 7),
            ),
            _INK,
        )
        renderer.draw_rounded_rect(left, top, width, height, _TALK_CUE, 9, _INK, 2)  # type: ignore[attr-defined]
        renderer.draw_polygon(  # type: ignore[attr-defined]
            (
                (left + 10, top + height - 3),
                (left + 15, top + height - 3),
                (left + 10, top + height + 3),
            ),
            _TALK_CUE,
        )
        for index in range(3):
            # The dots light up in turn, like someone about to speak.
            lit = 0.5 + 0.5 * math.sin(self.clock * 4.0 - index * 0.9)
            renderer.draw_circle(  # type: ignore[attr-defined]
                left + 8 + index * 7, top + height // 2, 2, mix((150, 160, 200), _NAME_TAG, lit)
            )

    def _anchor_rect(self, qualified_id: str | None, entity: _Positioned) -> Rect:
        """The rect prompts and bubbles point at: the art's visible body, if known."""
        role = self.sprite_identity(qualified_id)
        if role == PIXEL_QUALIFIED_ID:
            return pixel_visible_rect(entity)
        if role == MOONLIT_GUIDE_QUALIFIED_ID:
            return guide_visible_rect(entity)
        return _rect_of(entity)

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

    def feedback_panel_rect(self, renderer, view: TrailView) -> Rect | None:  # type: ignore[no-untyped-def]
        """A soft card hugging the HUD's bottom feedback lines, if any are shown."""
        lines: list[tuple[str, int, int]] = []
        if getattr(view, "is_complete", False):
            lines.append(("Trail complete!", FEEDBACK_TEXT_X, COMPLETE_TEXT_Y))
        message = self.fit_feedback(renderer, getattr(view, "feedback_message", None))
        if isinstance(message, str) and message.strip():
            lines.append((message, FEEDBACK_TEXT_X, FEEDBACK_TEXT_Y))
        if not lines:
            return None
        pad_x, pad_y = 14, 8
        right = 0
        top, bottom = SCREEN_HEIGHT, 0
        for text, x, y in lines:
            width, height = renderer.measure_text(text, FEEDBACK_FONT)
            right = max(right, x + width)
            top, bottom = min(top, y), max(bottom, y + height)
        left = FEEDBACK_TEXT_X - pad_x
        right = min(SCREEN_WIDTH - 2, right + pad_x)
        return (left, top - pad_y, right - left, bottom - top + 2 * pad_y)

    def fit_feedback(self, renderer: object, message: str | None) -> str | None:
        """The HUD feedback line as drawn: unchanged, except under dialogue focus.

        With dialogue focus a line too long for the screen (a full greeting
        echoed after the speaker's name) is shortened with an explicit
        ellipsis, since the speech bubble already shows every word. The
        scene's ``feedback_message`` state itself is never changed.
        """
        if (
            not self.active
            or not self.policy.dialogue_focus
            or not isinstance(message, str)
            or not supports(renderer, "measure_text")
        ):
            return message
        try:
            return self._layout(  # type: ignore[return-value]
                ("feedback", message),
                lambda: fit_line(
                    message,
                    SCREEN_WIDTH - 8 - FEEDBACK_TEXT_X,
                    lambda line: renderer.measure_text(line, FEEDBACK_FONT),  # type: ignore[attr-defined]
                ),
            )
        except Exception:
            self._log_once("feedback-fit")
            return message

    def _draw_feedback_panel(self, renderer, view: TrailView) -> None:  # type: ignore[no-untyped-def]
        if not supports(renderer, "draw_translucent_panel", "measure_text"):
            return
        rect = self.feedback_panel_rect(renderer, view)
        if rect is None:
            return
        renderer.draw_translucent_panel((rect,), _FEEDBACK_PANEL, 150, 14, _HUD_EDGE, 46, True)

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
            and (self.clock - self.bubble.start < self.bubble.duration)
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
        x, y, w, h = self._anchor_rect(target_id, entity)
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
            renderer.draw_translucent_panel(((px + 2, py + 4, width, height),), _SHADOW_INK, 96, 10)
            renderer.draw_translucent_panel(((px, py, width, height),), _PANEL, 226, 9, _GOLD, 235)
        else:
            renderer.draw_rounded_rect(px, py, width, height, _PANEL, 8, _GOLD, 2)
        self._draw_pointer(renderer, (px, py, width, height), (x, y, w, h))
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

    def _draw_pointer(self, renderer: object, panel: Rect, target: Rect) -> None:
        """A small tab on the prompt panel pointing at the thing it names."""
        px, py, pw, ph = panel
        tx, ty, tw, th = target
        center = max(px + 14, min(px + pw - 14, tx + tw // 2))
        middle = max(py + 8, min(py + ph - 8, ty + th // 2))
        if py + ph <= ty:
            outer = ((center - 7, py + ph - 1), (center + 7, py + ph - 1), (center, py + ph + 7))
            inner = ((center - 5, py + ph - 3), (center + 5, py + ph - 3), (center, py + ph + 4))
        elif py >= ty + th:
            outer = ((center - 7, py + 1), (center + 7, py + 1), (center, py - 7))
            inner = ((center - 5, py + 3), (center + 5, py + 3), (center, py - 4))
        elif px >= tx + tw:
            outer = ((px + 1, middle - 7), (px + 1, middle + 7), (px - 7, middle))
            inner = ((px + 3, middle - 5), (px + 3, middle + 5), (px - 4, middle))
        elif px + pw <= tx:
            outer = ((px + pw - 1, middle - 7), (px + pw - 1, middle + 7), (px + pw + 7, middle))
            inner = ((px + pw - 3, middle - 5), (px + pw - 3, middle + 5), (px + pw + 4, middle))
        else:
            return
        renderer.draw_polygon(outer, _GOLD)  # type: ignore[attr-defined]
        renderer.draw_polygon(inner, _PANEL)  # type: ignore[attr-defined]

    def _draw_bubble(self, renderer, view: TrailView) -> tuple[TextOp, ...]:  # type: ignore[no-untyped-def]
        bubble = self.bubble
        if bubble is None or not 0 <= self.clock - bubble.start < bubble.duration:
            return ()
        speaker = self._entity(view, bubble.qualified_id)
        if speaker is None:
            return ()
        focus = self.policy.dialogue_focus
        font = _DIALOGUE_FONT if focus else _BUBBLE_FONT
        column = _DIALOGUE_TEXT_WIDTH if focus else _BUBBLE_TEXT_WIDTH
        max_lines = _DIALOGUE_MAX_LINES if focus else _BUBBLE_MAX_LINES
        lines: tuple[str, ...] = self._layout(  # type: ignore[assignment]
            ("bubble", bubble.text, font, column, max_lines),
            lambda: wrap_text(
                bubble.text, column, lambda line: renderer.measure_text(line, font), max_lines
            ),
        )
        if not lines:
            return ()
        line_height = renderer.measure_text("Ag", font)[1] + 2
        text_width = max(renderer.measure_text(line, font)[0] for line in lines)
        width, height = text_width + 24, line_height * len(lines) + 18
        sx, sy, sw, sh = self._anchor_rect(bubble.qualified_id, speaker)
        head_y = sy + sh * 30 // 100
        avoid = [self._player_rect(view), *(_rect_of(item.world_object) for item in view.objects)]
        candidates = [
            (sx + sw + 14, head_y - height // 2),
            (sx - width - 14, head_y - height // 2),
            (sx + sw // 2 - width // 2, sy - height - 14),
            (sx + sw // 2 - width // 2, sy + sh + 14),
        ]
        if focus:
            # Keep the speaker, the HUD feedback card, and the player all in view,
            # and fall back to whichever spot covers the least of them.
            avoid.append((sx, sy, sw, sh))
            feedback = self.feedback_panel_rect(renderer, view)
            if feedback is not None:
                avoid.append(feedback)
            candidates += [
                (sx + sw - width, sy + sh + 14),
                (sx, sy + sh + 14),
                (sx + sw + 14, sy + sh - height),
                (sx - width - 14, sy + sh - height),
                (sx + sw + 14, sy),
                (sx - width - 14, sy),
            ]
            rect = place_clear_panel((width, height), candidates, avoid)
        else:
            rect = place_panel((width, height), candidates, avoid)
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
        if supports(renderer, "draw_translucent_panel"):
            renderer.draw_translucent_panel(((bx + 3, by + 5, width, height),), _SHADOW_INK, 90, 13)
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
        texts = [
            (line, bx + 12, by + 10 + index * line_height, _BUBBLE_TEXT, font)
            for index, line in enumerate(lines)
        ]
        # A small name tag on the bubble's top edge says who is talking.
        name = getattr(speaker, "name", None)
        if isinstance(name, str) and name.strip():
            name_width, name_height = renderer.measure_text(name, _NAME_FONT)
            tag_w, tag_h = name_width + 16, name_height + 6
            tag_x, tag_y = bx + 10, max(HUD_BOTTOM - 4, by - tag_h + 6)
            renderer.draw_rounded_rect(tag_x, tag_y, tag_w, tag_h, _NAME_TAG, 8, _INK, 2)
            texts.append((name, tag_x + 8, tag_y + 4, _WHITE, _NAME_FONT))
        return tuple(texts)

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
