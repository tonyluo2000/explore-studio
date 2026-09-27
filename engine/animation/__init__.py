"""Explore Studio engine — animation subsystem.

Owns frame-based animation: sprite sequences, timing, and transitions.
Cosmetic only — animations do not affect world state. Provides animation
triggers for entities and UI elements.

Submodules:
    _clips — AnimationClip, Facing, SpritePose: pure, time- or
             distance-driven frame selection.

Ownership: Engine team.
"""

from engine.animation._clips import (
    AnimationClip,
    Facing,
    SpritePose,
    facing_from_motion,
    is_blinking,
)

__all__ = ["AnimationClip", "Facing", "SpritePose", "facing_from_motion", "is_blinking"]
