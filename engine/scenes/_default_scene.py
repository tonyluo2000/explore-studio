"""Explore Studio engine — default empty scene.

A minimal scene that owns one character and draws it as a solid
rectangle each frame. No gameplay, no objects, no assets, no input.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.entities import Character
from engine.scenes._scene import Scene

if TYPE_CHECKING:
    from engine.rendering import Renderer

# Default character composition — centered in the 960×640 window.
_DEFAULT_CHARACTER = Character(
    name="Explorer",
    x=430,
    y=270,
    width=100,
    height=100,
    color=(255, 200, 50),
)


class DefaultScene(Scene):
    """A scene that owns one character and draws it each frame.

    The character is created at scene construction time. It is
    immutable — position, size, and color are fixed for this milestone.
    """

    def __init__(self, renderer: Renderer, character: Character | None = None) -> None:
        """Create a DefaultScene.

        Args:
            renderer: The engine renderer used to draw the character.
            character: The character to display. Uses a default
                centered character if not provided.
        """
        super().__init__()
        self._renderer = renderer
        self._character = character if character is not None else _DEFAULT_CHARACTER

    @property
    def character(self) -> Character:
        """The scene's character (read-only)."""
        return self._character

    def on_frame(self) -> None:
        """Draw the character as a filled rectangle."""
        super().on_frame()
        ch = self._character
        self._renderer.draw_rect(ch.x, ch.y, ch.width, ch.height, ch.color)
