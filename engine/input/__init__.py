"""Explore Studio engine — input subsystem.

Owns input interpretation: translates platform events and keyboard state
into engine-owned input representations. Does not own rendering, world
state, or gameplay decisions.

Submodules:
    _directional  — DirectionalInput: immutable directional snapshot.

Ownership: Engine team.
"""

from engine.input._directional import DirectionalInput

__all__ = ["DirectionalInput"]
