"""Explore Studio engine — input subsystem.

Owns input interpretation: translates platform events and keyboard state
into engine-owned input representations. Does not own rendering, world
state, or gameplay decisions.

Submodules:
    _directional  — DirectionalInput: immutable directional snapshot.
    _interaction  — InteractionInput: immutable interaction press snapshot.

Ownership: Engine team.
"""

from engine.input._directional import DirectionalInput
from engine.input._interaction import InteractionInput

__all__ = ["DirectionalInput", "InteractionInput"]
