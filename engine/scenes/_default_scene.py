"""Explore Studio engine — default scene with movement.

A minimal scene that owns one character, moves it according to
directional input each frame, and draws it as a solid rectangle.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.entities import Bounds, Character
from engine.input import DirectionalInput
from engine.scenes._scene import Scene

if TYPE_CHECKING:
    from engine.rendering import Renderer

# Movement speed in pixels per second.
_MOVEMENT_SPEED = 160.0

# Default character — centered in the 960×640 window.
_DEFAULT_CHARACTER = Character(
    name="Explorer",
    x=430,
    y=270,
    width=100,
    height=100,
    color=(255, 200, 50),
)


class DefaultScene(Scene):
    """A scene that owns one character, moves it via input, and draws it.

    Movement speed is owned by the scene. Diagonal movement applies
    full speed on both axes (documented simplification — diagonal
    movement is faster than cardinal).
    """

    def __init__(self, renderer: Renderer, character: Character | None = None) -> None:
        super().__init__()
        self._renderer = renderer
        self._character = character if character is not None else _DEFAULT_CHARACTER

    @property
    def character(self) -> Character:
        return self._character

    def on_frame(self, input_state: DirectionalInput, dt: float) -> None:
        """Move the character based on input, then draw it."""
        super().on_frame(input_state, dt)
        self._move_character(input_state, dt)
        self._draw_character()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _move_character(self, inp: DirectionalInput, dt: float) -> None:
        """Calculate displacement and move the character within bounds."""
        displacement = _MOVEMENT_SPEED * dt
        dx = inp.horizontal * displacement
        dy = inp.vertical * displacement
        bounds = self._window_bounds()
        self._character.move(dx, dy, bounds)

    def _draw_character(self) -> None:
        ch = self._character
        self._renderer.draw_rect(ch.x, ch.y, ch.width, ch.height, ch.color)

    def _window_bounds(self) -> Bounds:
        """Return bounds keeping the character inside the window."""
        # The default window is 960×640; we derive bounds from character size.
        return Bounds(
            min_x=0,
            min_y=0,
            max_x=960 - self._character.width,
            max_y=640 - self._character.height,
        )
