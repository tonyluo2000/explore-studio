"""Explore Studio engine — rendering subsystem.

Owns frame presentation: clearing, drawing order (future), and frame
finalization. Does not own world state, input interpretation, or
gameplay decisions.

Submodules:
    _renderer  — Renderer: engine-level frame contract (clear → present).

Ownership: Engine team.
"""

from engine.rendering._renderer import Renderer

__all__ = ["Renderer"]
