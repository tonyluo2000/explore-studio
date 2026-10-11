"""Explore Studio engine — audio subsystem.

Owns sound playback: sound effects, ambient audio, and optional background
music. Event-driven and entirely optional — the world must be fully
functional with audio disabled.

Submodules:
    _cues        — AudioCue: the semantic cue names and the one mix table
                   (sound, volume, cooldown) that voices them.
    _manager     — AudioManager: safe mixer start, decode-once sounds, fixed
                   channels, cooldowns, mute, and silent fallback.
    _trail_audio — TrailAudio: the M02-M05 Moon Meadow observer that turns
                   real scene transitions into cues.

Ownership: Engine team.
"""

from engine.audio._cues import CUES, AudioCue, CueBus, CueSpec
from engine.audio._manager import (
    AUDIO_ENV_VAR,
    AudioBackend,
    AudioManager,
    AudioMode,
    audio_mode_from_environment,
)
from engine.audio._trail_audio import AudioSink, TrailAudio

__all__ = [
    "AUDIO_ENV_VAR",
    "CUES",
    "AudioBackend",
    "AudioCue",
    "AudioManager",
    "AudioMode",
    "AudioSink",
    "CueBus",
    "CueSpec",
    "TrailAudio",
    "audio_mode_from_environment",
]
