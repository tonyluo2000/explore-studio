"""Deterministic, cosmetic frame selection.

Every function here is a pure function of injected time or distance, so tests
can pick exact frames without sleeping. Nothing here reads or writes entity
geometry: a pose only says which picture to draw inside unchanged bounds.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum


class Facing(StrEnum):
    """Which way a character is looking on screen."""

    DOWN = "down"
    UP = "up"
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class AnimationClip:
    """A named sequence of sheet columns shown for equal durations."""

    name: str
    frames: tuple[str, ...]
    frame_duration: float
    loop: bool = True

    def __post_init__(self) -> None:
        if not self.frames:
            raise ValueError("a clip needs at least one frame")
        if not self.frame_duration > 0:
            raise ValueError("frame_duration must be positive")

    @property
    def duration(self) -> float:
        return self.frame_duration * len(self.frames)

    def index_at(self, elapsed: float) -> int:
        """Return the frame index shown *elapsed* seconds into the clip."""
        if not math.isfinite(elapsed) or elapsed <= 0:
            return 0
        index = int(elapsed / self.frame_duration)
        if self.loop:
            return index % len(self.frames)
        return min(index, len(self.frames) - 1)

    def frame_at(self, elapsed: float) -> str:
        return self.frames[self.index_at(elapsed)]

    def frame_at_distance(self, distance: float, stride: float) -> str:
        """Pick a frame from distance travelled so feet keep pace with motion."""
        if stride <= 0:
            raise ValueError("stride must be positive")
        if not math.isfinite(distance) or distance <= 0:
            return self.frames[0]
        return self.frames[int(distance / stride) % len(self.frames)]


def facing_from_motion(dx: float, dy: float, previous: Facing) -> Facing:
    """Face the dominant direction of motion; keep *previous* when still.

    Horizontal motion wins ties, so diagonal walking shows the side view.
    """
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return previous
    if abs(dx) >= abs(dy):
        return Facing.RIGHT if dx > 0 else Facing.LEFT
    return Facing.DOWN if dy > 0 else Facing.UP


def is_blinking(clock: float, *, period: float, duration: float, offset: float = 0.0) -> bool:
    """Return True during a short blink that repeats every *period* seconds."""
    if period <= 0 or duration <= 0:
        return False
    return (clock + offset) % period < duration


@dataclass(frozen=True)
class SpritePose:
    """Cosmetic drawing instructions for one entity in one frame.

    ``row``/``column`` name a trusted sprite-sheet frame. The remaining fields
    drive the procedural fallback. None of them can move or resize the entity.
    """

    row: str | None = None
    column: str | None = None
    flip_x: bool = False
    bob: int = 0
    stride: int = 0
    blink: bool = False
    needle_angle: float = 0.0
