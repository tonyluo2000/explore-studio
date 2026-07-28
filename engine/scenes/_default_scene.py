"""Explore Studio engine — default scene with movement and world object.

A minimal scene that owns one character and one world object. The
character moves via directional input; the world object is stationary.
Both are drawn as solid rectangles.

Drawing order: background → world object → character.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.entities import Bounds, Character, WorldObject
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

# Default world object — a Treasure Chest in the top-left area.
_DEFAULT_OBJECT = WorldObject(
    name="Treasure Chest",
    x=60,
    y=480,
    width=80,
    height=60,
    color=(139, 90, 43),
)


class DefaultScene(Scene):
    """A scene with one character and one stationary world object.

    Drawing order: clear → world object → character → present.
    The character may pass through the object (no collision).
    """

    def __init__(
        self,
        renderer: Renderer,
        character: Character | None = None,
        world_object: WorldObject | None = None,
    ) -> None:
        super().__init__()
        self._renderer = renderer
        self._character = character if character is not None else _DEFAULT_CHARACTER
        self._world_object = world_object if world_object is not None else _DEFAULT_OBJECT

    @property
    def character(self) -> Character:
        return self._character

    @property
    def world_object(self) -> WorldObject:
        return self._world_object

    def on_frame(self, input_state: DirectionalInput, dt: float) -> None:
        """Move the character, then draw object first, character second."""
        super().on_frame(input_state, dt)
        self._move_character(input_state, dt)
        self._draw_world_object()
        self._draw_character()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _move_character(self, inp: DirectionalInput, dt: float) -> None:
        displacement = _MOVEMENT_SPEED * dt
        dx = inp.horizontal * displacement
        dy = inp.vertical * displacement
        bounds = self._window_bounds()
        self._character.move(dx, dy, bounds)

    def _draw_world_object(self) -> None:
        wo = self._world_object
        self._renderer.draw_rect(wo.x, wo.y, wo.width, wo.height, wo.color)

    def _draw_character(self) -> None:
        ch = self._character
        self._renderer.draw_rect(ch.x, ch.y, ch.width, ch.height, ch.color)

    def _window_bounds(self) -> Bounds:
        return Bounds(
            min_x=0,
            min_y=0,
            max_x=960 - self._character.width,
            max_y=640 - self._character.height,
        )
