"""Explore Studio engine — default scene with movement, world object, and proximity.

A minimal scene that owns one character and one world object. The
character moves via directional input; the world object is stationary.
Both are drawn as solid rectangles.

Proximity between the character and the world object is evaluated every
completed frame after movement and before drawing. The result is exposed
as a read-only Boolean property.

Drawing order: clear → world object → character → present.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.entities import Bounds, Character, WorldObject
from engine.input import DirectionalInput
from engine.interactions._proximity import _validate_interaction_range, is_near
from engine.scenes._scene import Scene

if TYPE_CHECKING:
    from engine.rendering import Renderer

# Movement speed in pixels per second.
_MOVEMENT_SPEED = 160.0

# Interaction range in pixels — how close the character must be
# (center-to-center) for proximity to register as "near."
# Owned by the default scene because the range describes behaviour
# between scene-owned objects.
_DEFAULT_INTERACTION_RANGE = 120.0

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

    Per-frame ordering:
    1. move the character (directional input × dt);
    2. evaluate proximity (character ↔ world object);
    3. clear the frame;
    4. draw the world object;
    5. draw the character;
    6. present the frame.

    The character may pass through the object (no collision).

    Attributes:
        is_character_near_object: Read-only Boolean — ``True`` when the
            character's center is within *interaction_range* of the
            world object's center.
    """

    def __init__(
        self,
        renderer: Renderer,
        character: Character | None = None,
        world_object: WorldObject | None = None,
        *,
        background_color: tuple[int, int, int] = (0, 0, 0),
        interaction_range: float | int = _DEFAULT_INTERACTION_RANGE,
    ) -> None:
        super().__init__()
        self._renderer = renderer
        self._background_color = background_color
        self._character = character if character is not None else _DEFAULT_CHARACTER
        self._world_object = world_object if world_object is not None else _DEFAULT_OBJECT
        self._interaction_range = _validate_interaction_range(
            interaction_range, "interaction_range"
        )
        self._range_sq = self._interaction_range * self._interaction_range
        self._is_near: bool = False

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def character(self) -> Character:
        return self._character

    @property
    def world_object(self) -> WorldObject:
        return self._world_object

    @property
    def interaction_range(self) -> float:
        """The positive, finite interaction range in pixels (read-only)."""
        return self._interaction_range

    @property
    def is_character_near_object(self) -> bool:
        """``True`` when the character center is within range of the object.

        Read-only.  Updated once per completed frame, after movement
        and before drawing.  Initial value is ``False``.
        """
        return self._is_near

    # ------------------------------------------------------------------
    # Frame participation
    # ------------------------------------------------------------------

    def on_frame(self, input_state: DirectionalInput, dt: float) -> None:
        """Move the character, evaluate proximity, clear, then draw."""
        super().on_frame(input_state, dt)
        self._move_character(input_state, dt)
        self._evaluate_proximity()
        self._renderer.clear_frame(self._background_color)
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

    def _evaluate_proximity(self) -> None:
        """Update *self._is_near* using current character & object positions.

        Uses center-to-center squared Euclidean distance with an
        inclusive boundary.  Fractional character coordinates are
        preserved.
        """
        ch = self._character
        wo = self._world_object
        self._is_near = is_near(
            ch.x_float,
            ch.y_float,
            ch.width,
            ch.height,
            wo.x,
            wo.y,
            wo.width,
            wo.height,
            self._range_sq,
        )

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
