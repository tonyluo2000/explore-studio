"""Moon Meadow audio for the S02-S04 (M02-M04) Classroom Trail.

Like ``TrailPresentation``, this layer only *observes* the scene after each
update and never writes to it. It turns real state transitions into semantic
cues for an :class:`~engine.audio._manager.AudioManager`:

* the Moon Meadow ambience starts when the scene enters and fades when it
  exits; it is one loop, started once;
* a footstep at each of Nova's foot contacts (every ``STEP_LENGTH`` px of
  actual movement, the same cadence as the drawn step dust), none when still;
* a faint glint when Nova comes into range of an object or NPC it has not yet
  visited or spoken to, re-armed per target only after ``NEAR_REARM`` s away;
* on an actual interaction: the Compass's shimmer, the Lantern's chime,
  Pixel's chirp, the Moonlit Guide's (or any NPC's) moon bell when a
  conversation starts, or a soft tock for any other object;
* the mission-complete motif once, on the incomplete -> complete transition,
  a beat after the interaction that caused it.

Audio is allow-listed by the mission presentation policy (``meadow_audio``):
M02-M04 only, so S01 and S05+ stay silent. Every cue has a visual twin, so a
muted or soundless Trail loses nothing. A small "Audio" indicator (M to
toggle) is drawn only while a mixer is actually open.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import logging
import math
from typing import Final, Protocol

from engine.audio._cues import FOOTSTEPS, AudioCue
from engine.rendering._classroom_sprites import (
    CRYSTAL_LANTERN_QUALIFIED_ID,
    MOON_COMPASS_QUALIFIED_ID,
    PIXEL_QUALIFIED_ID,
)
from engine.rendering._mission_presentation import mission_presentation
from engine.rendering._trail_presentation import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STEP_LENGTH,
    TrailView,
)

_LOGGER = logging.getLogger("explore-studio.audio.trail")

#: Seconds Nova must be out of a target's range before it can glint again.
NEAR_REARM: Final = 5.0
#: The completion motif waits this long, so the cue that completed the
#: mission is heard first instead of under it.
COMPLETE_DELAY: Final = 0.45

INDICATOR_ON: Final = "Audio: On (M to mute)"
INDICATOR_MUTED: Final = "Audio: Muted (M to unmute)"
_INDICATOR_FONT: Final = 18
_INDICATOR_MARGIN: Final = 10
_INDICATOR_TEXT: Final = (206, 212, 240)
_INDICATOR_PANEL: Final = (14, 18, 48)


class AudioSink(Protocol):
    """What the Trail asks of an audio manager."""

    @property
    def available(self) -> bool: ...

    @property
    def muted(self) -> bool: ...

    def prepare(self) -> bool: ...

    def play(self, cue: AudioCue) -> str: ...

    def start_ambience(self, cue: AudioCue = ...) -> str: ...

    def stop_ambience(self, fade_ms: int = ...) -> None: ...

    def update(self, dt: float) -> None: ...

    def toggle_mute(self) -> bool: ...


class TrailAudio:
    """Observe one Trail scene and voice its mission-gated audio cues."""

    def __init__(
        self,
        mission_id: str,
        sink: AudioSink | None,
        start: tuple[float, float] | None = None,
    ) -> None:
        policy = mission_presentation(mission_id)
        self.active = sink is not None and policy is not None and policy.meadow_audio
        self._sink = sink if self.active else None
        self._aliases = policy.sprite_aliases if policy is not None else {}
        self.clock = 0.0
        self._previous_position = start
        self._stride = STEP_LENGTH / 2
        self._previous_target: str | None = None
        self._last_near: dict[str, float] = {}
        self._previous_complete: bool | None = None
        self._complete_at: float | None = None
        self._started = False
        self._failed: set[str] = set()
        self._indicator_layout: dict[str, tuple[int, int]] = {}

    # ------------------------------------------------------------------
    # Safety
    # ------------------------------------------------------------------

    def _log_once(self, layer: str) -> None:
        if layer not in self._failed:
            self._failed.add(layer)
            _LOGGER.exception("Trail audio layer %r failed; skipping it", layer)

    def _cue(self, cue: AudioCue) -> None:
        if self._sink is not None:
            self._sink.play(cue)

    # ------------------------------------------------------------------
    # Scene lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Open audio and start the ambience loop (scene entered)."""
        if self._sink is None or self._started:
            return
        self._started = True
        try:
            if self._sink.prepare():
                self._sink.start_ambience(AudioCue.AMBIENT_MOON_MEADOW)
        except Exception:
            self._log_once("start")

    def stop(self) -> None:
        """Fade the ambience out (scene exited); idempotent."""
        if self._sink is None or not self._started:
            return
        self._started = False
        self._complete_at = None
        try:
            self._sink.stop_ambience()
        except Exception:
            self._log_once("stop")

    def toggle_mute(self) -> bool | None:
        """Flip mute for an audio-enabled Trail; ``None`` when it has no audio."""
        if self._sink is None or not self._sink.available:
            return None
        try:
            return self._sink.toggle_mute()
        except Exception:
            self._log_once("mute")
            return None

    # ------------------------------------------------------------------
    # Observation (called after every scene update)
    # ------------------------------------------------------------------

    def observe(self, view: TrailView, dt: float) -> None:
        if self._sink is None:
            return
        try:
            self._observe(view, dt)
        except Exception:
            self._log_once("observe")

    def _observe(self, view: TrailView, dt: float) -> None:
        assert self._sink is not None
        step = dt if isinstance(dt, int | float) and math.isfinite(dt) else 0.0
        step = max(0.0, min(float(step), 0.25))
        self.clock += step
        self._sink.update(step)

        # Footsteps: one per foot contact of real movement, never when still.
        player = view.player
        position = (player.x_float, player.y_float)
        previous = self._previous_position or position
        distance = math.hypot(position[0] - previous[0], position[1] - previous[1])
        self._previous_position = position
        if distance > 1e-6:
            self._stride += distance
            if self._stride >= STEP_LENGTH:
                self._stride %= STEP_LENGTH
                if FOOTSTEPS:
                    self._cue(AudioCue.FOOTSTEP_GRASS)
        else:
            # The first step after a pause lands half a stride in.
            self._stride = STEP_LENGTH / 2

        target = view.target_qualified_id
        interacted = view.did_interact_this_frame and target is not None
        if interacted:
            assert target is not None
            self._react_to_interaction(view, target)
        elif target is not None and target != self._previous_target:
            self._maybe_near(view, target)
        if target is not None:
            self._last_near[target] = self.clock
        self._previous_target = target

        complete = view.mission_is_complete
        if self._previous_complete is False and complete:
            self._complete_at = self.clock + COMPLETE_DELAY
        self._previous_complete = complete
        if self._complete_at is not None and self.clock >= self._complete_at:
            self._complete_at = None
            self._cue(AudioCue.MISSION_COMPLETE)

    def _maybe_near(self, view: TrailView, target: str) -> None:
        """Glint for a target still waiting to be visited or spoken to."""
        spoken = getattr(view, "spoken_npc_ids", frozenset())
        if target in view.visited_qualified_ids or target in spoken:
            return
        last = self._last_near.get(target)
        if last is not None and self.clock - last < NEAR_REARM:
            return
        self._cue(AudioCue.OBJECT_NEAR)

    def _role(self, qualified_id: str) -> str:
        return self._aliases.get(qualified_id, qualified_id)

    def _react_to_interaction(self, view: TrailView, target: str) -> None:
        if any(item.qualified_id == target for item in view.objects):
            role = self._role(target)
            self._cue(
                {
                    MOON_COMPASS_QUALIFIED_ID: AudioCue.COMPASS_MAGIC,
                    CRYSTAL_LANTERN_QUALIFIED_ID: AudioCue.LANTERN_CHIME,
                }.get(role, AudioCue.OBJECT_INTERACT)
            )
            return
        npc = next((item for item in view.npcs if item.qualified_id == target), None)
        if npc is None or not self._starts_conversation(view, npc):
            return
        if self._role(target) == PIXEL_QUALIFIED_ID:
            self._cue(AudioCue.PIXEL_GREETING)
        else:
            self._cue(AudioCue.NPC_TALK)

    @staticmethod
    def _starts_conversation(view: TrailView, npc: object) -> bool:
        """A greeting always starts one; a longer conversation only on line one."""
        lines = getattr(npc, "conversation_lines", ())
        if len(lines) <= 1:
            return True
        name = getattr(getattr(npc, "character", None), "name", None)
        return getattr(view, "feedback_message", None) == f"{name}: {lines[0]}"

    # ------------------------------------------------------------------
    # Indicator
    # ------------------------------------------------------------------

    def indicator_text(self) -> str | None:
        """The bottom-right audio state, only while a mixer is open."""
        if self._sink is None or not self._sink.available:
            return None
        return INDICATOR_MUTED if self._sink.muted else INDICATOR_ON

    def draw_indicator(self, renderer: object) -> None:
        text = self.indicator_text()
        if text is None:
            return
        try:
            self._draw_indicator(renderer, text)
        except Exception:
            self._log_once("indicator")

    def _draw_indicator(self, renderer, text: str) -> None:  # type: ignore[no-untyped-def]
        size = self._indicator_layout.get(text)
        if size is None:
            size = renderer.measure_text(text, _INDICATOR_FONT)
            self._indicator_layout[text] = size
        width, height = size
        x = SCREEN_WIDTH - _INDICATOR_MARGIN - 8 - width
        y = SCREEN_HEIGHT - _INDICATOR_MARGIN - 4 - height
        if hasattr(renderer, "draw_translucent_panel"):
            renderer.draw_translucent_panel(
                ((x - 8, y - 4, width + 16, height + 8),), _INDICATOR_PANEL, 120, 8
            )
        renderer.draw_text(text, x, y, _INDICATOR_TEXT, _INDICATOR_FONT)
