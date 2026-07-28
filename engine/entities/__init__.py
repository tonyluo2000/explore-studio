"""Explore Studio engine — entity management.

Owns entity lifecycle: characters, world objects, their properties and
behaviors. Manages entity creation, updates, and interaction registration.

Submodules:
    _character  — Character: immutable scene inhabitant.

Ownership: Engine team.
"""

from engine.entities._character import Bounds, Character

__all__ = ["Bounds", "Character"]
