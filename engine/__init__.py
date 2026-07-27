"""Explore Studio — educational game engine.

The engine provides the platform on which students build Explorer World.
It handles rendering, input, world state, interactions, and persistence
so students can focus on creative programming.

Subsystems:
    world       — World state: grid, entities, global variables.
    rendering   — Translates world state into visual output.
    scenes      — Scene lifecycle and transitions.
    input       — Keyboard and mouse event interpretation.
    entities    — Character and object lifecycle.
    interactions — Interaction detection and dispatch.
    dialogue    — Conversation rendering and progression.
    animation   — Frame-based sprite animation.
    audio       — Sound playback (optional).
    persistence — Save/load and format migration.
    ui          — Menus, HUD, and text overlays.
    assets      — Image, sound, and font management.

Public interface:
    App         — Application entry point and lifecycle.
    Config      — Engine configuration.
    init_logging — Centralized logging setup.
"""

from engine._config import Config
from engine._logging import init_logging
from engine.app import App

__all__ = ["App", "Config", "init_logging"]
