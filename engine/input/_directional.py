"""Explore Studio engine — directional input.

An immutable snapshot of which directional inputs are currently pressed.
Contains no Pygame types — the platform boundary translates raw key state
into this engine-owned representation.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DirectionalInput:
    """Immutable snapshot of directional input state.

    All four fields are ``bool`` — ``True`` means the corresponding
    direction is currently pressed.

    Attributes:
        left: Left direction pressed.
        right: Right direction pressed.
        up: Up direction pressed.
        down: Down direction pressed.
    """

    left: bool = False
    right: bool = False
    up: bool = False
    down: bool = False

    @property
    def horizontal(self) -> float:
        """Net horizontal intent: -1 (left), +1 (right), or 0."""
        return float(self.right) - float(self.left)

    @property
    def vertical(self) -> float:
        """Net vertical intent: -1 (up), +1 (down), or 0."""
        return float(self.down) - float(self.up)
