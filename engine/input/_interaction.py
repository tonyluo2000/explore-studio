"""Explore Studio engine — interaction input.

An immutable snapshot of whether the interaction key was newly pressed
this frame.  Contains no Pygame types — the platform boundary translates
raw key events into this engine-owned representation.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InteractionInput:
    """Immutable snapshot of interaction input state.

    Represents an **edge-triggered** key press — ``True`` only when
    the interaction key (E) was newly pressed this frame.  Held keys
    produce ``False`` on subsequent frames until released and pressed
    again.

    This is intentionally different from ``DirectionalInput``, which
    represents continuous held-key state.

    Attributes:
        interact_pressed: ``True`` when the interaction key was newly
            pressed this frame.
    """

    interact_pressed: bool = False
