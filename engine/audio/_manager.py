"""The Trail's small audio manager: optional, bounded, and never in the way.

It turns semantic cues (``engine.audio._cues``) into sound through a narrow
:class:`AudioBackend` (the Pygame mixer lives behind ``engine._platform``):

* the mixer is opened at most once, on first use, and only for a Trail
  whose presentation policy asks for audio; if that fails, every later
  request is a silent no-op and the failure is logged once;
* every trusted sound is read, digest-checked, and decoded once, up front;
  a missing or corrupt file only silences its own cue;
* six fixed channels, addressed by number: one for the ambience loop, one
  for footsteps, and four for effects (the oldest is reused when all four are
  busy), so nothing allocates per frame;
* per-cue cooldowns drop request storms; mute stops effects at once and
  holds the ambience loop at zero volume, so unmuting never restarts it.

Nothing here can raise into gameplay, and gameplay never reads from here.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import logging
import os
from collections import deque
from collections.abc import Callable, Mapping
from enum import StrEnum
from typing import Final, Protocol

from engine.assets._trusted_audio import TrustedAudioCatalog
from engine.audio._cues import (
    AMBIENCE_FADE_IN,
    AMBIENCE_FADE_OUT_MS,
    CUES,
    AudioCue,
    CueBus,
    CueSpec,
)

_LOGGER = logging.getLogger("explore-studio.audio")

AMBIENCE_CHANNEL: Final = 0
FOOTSTEP_CHANNEL: Final = 1
EFFECT_CHANNELS: Final = (2, 3, 4, 5)
CHANNEL_COUNT: Final = 6
#: The recent cue log kept for tests and evidence; old entries fall off.
MAX_EVENTS: Final = 128

#: ``on`` (default), ``muted`` (start muted; M unmutes), or ``off`` (never
#: open the mixer at all).
AUDIO_ENV_VAR: Final = "EXPLORE_STUDIO_AUDIO"


class AudioMode(StrEnum):
    ON = "on"
    MUTED = "muted"
    OFF = "off"


def audio_mode_from_environment(environ: Mapping[str, str] | None = None) -> AudioMode:
    """Read ``EXPLORE_STUDIO_AUDIO``; anything unrecognized means ``on``."""
    value = (os.environ if environ is None else environ).get(AUDIO_ENV_VAR, "")
    try:
        return AudioMode(value.strip().lower())
    except ValueError:
        return AudioMode.ON


class AudioBackend(Protocol):
    """The few mixer operations the manager needs, on numbered channels."""

    def open(self, channel_count: int) -> bool: ...

    def load(self, data: bytes, volume: float) -> object: ...

    def play(self, channel: int, sound: object, *, loop: bool = False) -> None: ...

    def is_busy(self, channel: int) -> bool: ...

    def set_volume(self, channel: int, volume: float) -> None: ...

    def stop(self, channel: int, fade_ms: int = 0) -> None: ...

    def close(self) -> None: ...


class AudioManager:
    """Semantic cue playback with safe fallback, mute, and bounded channels."""

    def __init__(
        self,
        backend: AudioBackend | None,
        *,
        catalog: TrustedAudioCatalog | None = None,
        muted: bool = False,
        clock: Callable[[], float] | None = None,
        cues: Mapping[AudioCue, CueSpec] = CUES,
    ) -> None:
        self._backend = backend
        self._catalog = catalog if catalog is not None else TrustedAudioCatalog()
        self._cues = cues
        #: Cooldowns run on game time (the dts given to ``update``), so they
        #: are deterministic and match what is on screen; tests may inject one.
        self._elapsed = 0.0
        self._clock = clock if clock is not None else self._game_time
        self._muted = bool(muted)
        self._prepared = False
        self._open = False
        self._closed = False
        self._sounds: dict[str, object] = {}
        self._last_played: dict[AudioCue, float] = {}
        self._rotation: dict[AudioCue, int] = {}
        self._next_effect = 0
        self._ambience: AudioCue | None = None
        self._ambience_level = 0.0
        self._ambience_volume: float | None = None
        self._failed: set[str] = set()
        self.events: deque[tuple[str, str]] = deque(maxlen=MAX_EVENTS)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        """True once the mixer opened; stays False after any open failure."""
        return self._open and not self._closed

    @property
    def muted(self) -> bool:
        return self._muted

    @property
    def ambience(self) -> AudioCue | None:
        """The looping cue now playing (possibly at zero volume while muted)."""
        return self._ambience

    @property
    def loaded_sounds(self) -> tuple[str, ...]:
        return tuple(self._sounds)

    def _game_time(self) -> float:
        return self._elapsed

    def _log_once(self, key: str, message: str, *args: object) -> None:
        if key not in self._failed:
            self._failed.add(key)
            _LOGGER.warning(message, *args)

    def _call(self, operation: str, function: Callable[..., object], *args: object, **kw: object):  # type: ignore[no-untyped-def]
        try:
            return function(*args, **kw)
        except Exception as error:  # noqa: BLE001 - audio must never reach gameplay
            self._log_once(operation, "Trail audio %s failed (%s); continuing", operation, error)
            return None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def prepare(self) -> bool:
        """Open the mixer and decode every cue's sounds, at most once."""
        if self._prepared:
            return self.available
        self._prepared = True
        if self._backend is None or self._closed:
            return False
        if not self._call("open", self._backend.open, CHANNEL_COUNT):
            self._log_once("open", "Trail audio unavailable; continuing silently")
            return False
        self._open = True
        for spec in self._cues.values():
            for asset_id in spec.assets:
                if asset_id in self._sounds:
                    continue
                data = self._catalog.read_verified(asset_id)
                if data is None:
                    self._log_once(f"asset:{asset_id}", "Trail sound %s is unavailable", asset_id)
                    continue
                sound = self._call(f"load:{asset_id}", self._backend.load, data, spec.volume)
                if sound is not None:
                    self._sounds[asset_id] = sound
        return True

    def shutdown(self) -> None:
        """Stop every channel and release the decoded sounds. Idempotent."""
        if self._closed:
            return
        self._closed = True
        if self._open and self._backend is not None:
            self._call("close", self._backend.close)
        self._sounds.clear()
        self._ambience = None

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _record(self, cue: AudioCue, outcome: str) -> str:
        self.events.append((cue.value, outcome))
        return outcome

    def _sound_for(self, cue: AudioCue, spec: CueSpec) -> object | None:
        index = self._rotation.get(cue, 0)
        self._rotation[cue] = (index + 1) % len(spec.assets)
        return self._sounds.get(spec.assets[index])

    def _effect_channel(self) -> int:
        assert self._backend is not None
        for channel in EFFECT_CHANNELS:
            if not self._call("busy", self._backend.is_busy, channel):
                return channel
        # All four are sounding: reuse them in turn, so the count never grows.
        channel = EFFECT_CHANNELS[self._next_effect]
        self._next_effect = (self._next_effect + 1) % len(EFFECT_CHANNELS)
        return channel

    def play(self, cue: AudioCue) -> str:
        """Play one short cue; return what happened (for logs and tests)."""
        spec = self._cues.get(cue)
        if spec is None or spec.bus is CueBus.AMBIENCE:
            return self._record(cue, "not-a-one-shot")
        if not self.prepare() or self._backend is None:
            return self._record(cue, "unavailable")
        if self._muted:
            return self._record(cue, "muted")
        now = self._clock()
        last = self._last_played.get(cue)
        if last is not None and now - last < spec.cooldown:
            return self._record(cue, "cooldown")
        sound = self._sound_for(cue, spec)
        if sound is None:
            return self._record(cue, "missing")
        channel = FOOTSTEP_CHANNEL if spec.bus is CueBus.FOOTSTEPS else self._effect_channel()
        self._call("play", self._backend.play, channel, sound)
        self._call("volume", self._backend.set_volume, channel, 1.0)
        self._last_played[cue] = now
        return self._record(cue, "played")

    def start_ambience(self, cue: AudioCue = AudioCue.AMBIENT_MOON_MEADOW) -> str:
        """Start the looping bed once; asking again while it plays does nothing."""
        spec = self._cues.get(cue)
        if spec is None or spec.bus is not CueBus.AMBIENCE:
            return self._record(cue, "not-a-loop")
        if self._ambience is cue:
            return self._record(cue, "already-playing")
        if not self.prepare() or self._backend is None:
            return self._record(cue, "unavailable")
        sound = self._sound_for(cue, spec)
        if sound is None:
            return self._record(cue, "missing")
        if self._ambience is not None:
            self._call("stop", self._backend.stop, AMBIENCE_CHANNEL)
        self._ambience = cue
        self._ambience_level = 0.0
        self._ambience_volume = None
        self._call("play", self._backend.play, AMBIENCE_CHANNEL, sound, loop=True)
        self._apply_ambience_volume()
        return self._record(cue, "started")

    def stop_ambience(self, fade_ms: int = AMBIENCE_FADE_OUT_MS) -> None:
        """Fade the loop out (immediately when muted); safe to call any time."""
        cue = self._ambience
        if cue is None:
            return
        self._ambience = None
        if self.available and self._backend is not None:
            self._call("stop", self._backend.stop, AMBIENCE_CHANNEL, 0 if self._muted else fade_ms)
        self._record(cue, "stopped")

    def update(self, dt: float) -> None:
        """Advance game time and the ambience fade-in (one volume call at most)."""
        step = dt if isinstance(dt, int | float) and dt == dt else 0.0
        step = max(0.0, min(float(step), 0.25))
        self._elapsed += step
        if self._ambience is None or self._ambience_level >= 1.0:
            return
        self._ambience_level = min(1.0, self._ambience_level + step / AMBIENCE_FADE_IN)
        self._apply_ambience_volume()

    def _apply_ambience_volume(self) -> None:
        if self._ambience is None or self._backend is None or not self.available:
            return
        volume = 0.0 if self._muted else round(self._ambience_level, 3)
        if volume != self._ambience_volume:
            self._ambience_volume = volume
            self._call("volume", self._backend.set_volume, AMBIENCE_CHANNEL, volume)

    # ------------------------------------------------------------------
    # Mute
    # ------------------------------------------------------------------

    def set_muted(self, muted: bool) -> None:
        """Mute or unmute every Trail sound right away."""
        muted = bool(muted)
        if muted == self._muted:
            return
        self._muted = muted
        if self.available and self._backend is not None and muted:
            self._call("stop", self._backend.stop, FOOTSTEP_CHANNEL)
            for channel in EFFECT_CHANNELS:
                self._call("stop", self._backend.stop, channel)
        self._apply_ambience_volume()
        if not muted and self.available:
            self.play(AudioCue.UI_MUTE_TOGGLE)

    def toggle_mute(self) -> bool:
        """Flip mute; return the new state."""
        self.set_muted(not self._muted)
        return self._muted
