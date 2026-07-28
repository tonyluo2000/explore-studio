"""Explore Studio engine — default scene with movement, world object, proximity,
interaction input, and visible feedback.

A minimal scene that owns one character and one world object. The
character moves via directional input; the world object is stationary.
Both are drawn as solid rectangles.

Frame participation is split into two phases:

* **update** — move character, evaluate proximity, evaluate interaction,
  update feedback state.
* **render** — draw world object, draw character, draw feedback text.

The renderer owns frame clearing and presentation.  The scene does not
clear or present.

Internal module — not part of the Student API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from engine.entities import Bounds, Character, WorldObject
from engine.input import DirectionalInput, InteractionInput
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

# --- Feedback ---

# How long the success message remains visible (seconds).
_FEEDBACK_DURATION = 2.0

# Prompt shown while near the chest and no success message is active.
_PROMPT_TEXT = "Press E to explore"

# Success message shown briefly after a valid interaction.
_SUCCESS_TEXT = "You found a treasure!"

# Screen position for feedback text (top-left corner).
# Placed near the lower center, far from the initial Treasure Chest.
_FEEDBACK_X = 360
_FEEDBACK_Y = 560

# Font size for feedback text.
_FEEDBACK_FONT_SIZE = 28

# Text colour — white, readable against the dark background.
_FEEDBACK_COLOR = (240, 240, 240)

# --- Default entities ---

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
    """A scene with one character, one stationary world object,
    proximity-gated interaction, and visible feedback.

    **Update phase** (before clear):
    1. move the character (directional input × dt);
    2. evaluate proximity (character ↔ world object);
    3. evaluate interaction attempt (proximity + E-key press);
    4. update feedback state (timer, message).

    **Render phase** (between clear and present):
    5. draw the world object;
    6. draw the character;
    7. draw current feedback text, if any.

    The character may pass through the object (no collision).

    Attributes:
        is_character_near_object: Read-only — ``True`` when near the
            world object.
        did_interact_this_frame: Read-only — ``True`` only during the
            frame of a valid interaction.
        feedback_remaining: Read-only — seconds remaining for the
            success message (0 when no message is active).
    """

    def __init__(
        self,
        renderer: Renderer,
        character: Character | None = None,
        world_object: WorldObject | None = None,
        *,
        interaction_range: float | int = _DEFAULT_INTERACTION_RANGE,
    ) -> None:
        super().__init__()
        self._renderer = renderer
        self._character = character if character is not None else _DEFAULT_CHARACTER
        self._world_object = world_object if world_object is not None else _DEFAULT_OBJECT
        self._interaction_range = _validate_interaction_range(
            interaction_range, "interaction_range"
        )
        self._range_sq = self._interaction_range * self._interaction_range
        self._is_near: bool = False
        self._interaction_pulse: bool = False
        self._success_remaining: float = 0.0

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

    @property
    def did_interact_this_frame(self) -> bool:
        """``True`` only during the frame where a valid interaction occurred.

        Read-only.  Reset to ``False`` at the start of each update phase.
        Set to ``True`` when both E is newly pressed **and** the
        character is near the object.
        """
        return self._interaction_pulse

    @property
    def feedback_remaining(self) -> float:
        """Seconds remaining for the success message (0 when inactive).

        Read-only.  Updated during ``update()``, not ``render()``.
        """
        return self._success_remaining

    # ------------------------------------------------------------------
    # Frame participation — update (before clear)
    # ------------------------------------------------------------------

    def update(
        self,
        input_state: DirectionalInput,
        interaction_input: InteractionInput,
        dt: float,
    ) -> None:
        """Move, evaluate proximity, evaluate interaction, update feedback."""
        super().update(input_state, interaction_input, dt)
        self._move_character(input_state, dt)
        self._evaluate_proximity()
        self._evaluate_interaction(interaction_input)
        self._update_feedback(dt)

    # ------------------------------------------------------------------
    # Frame participation — render (between clear and present)
    # ------------------------------------------------------------------

    def render(self) -> None:
        """Draw the world object, character, then feedback text."""
        super().render()
        self._draw_world_object()
        self._draw_character()
        self._draw_feedback()

    # ------------------------------------------------------------------
    # Internal: movement
    # ------------------------------------------------------------------

    def _move_character(self, inp: DirectionalInput, dt: float) -> None:
        displacement = _MOVEMENT_SPEED * dt
        dx = inp.horizontal * displacement
        dy = inp.vertical * displacement
        bounds = self._window_bounds()
        self._character.move(dx, dy, bounds)

    # ------------------------------------------------------------------
    # Internal: proximity
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Internal: interaction
    # ------------------------------------------------------------------

    def _evaluate_interaction(self, interaction_input: InteractionInput) -> None:
        """Set the interaction pulse for this frame.

        A valid interaction requires both:
        * the interaction key was newly pressed this frame; and
        * the character is currently near the world object.
        """
        self._interaction_pulse = interaction_input.interact_pressed and self._is_near

    # ------------------------------------------------------------------
    # Internal: feedback
    # ------------------------------------------------------------------

    def _update_feedback(self, dt: float) -> None:
        """Update feedback timer and state.

        When a valid interaction occurs this frame, the success-message
        timer is set to the full configured duration (the current
        frame's *dt* is not subtracted).

        On frames without a new interaction, the timer is reduced by
        *dt* and clamped to zero.

        A later valid interaction while the message is already active
        restarts the timer at the full duration.
        """
        if self._interaction_pulse:
            self._success_remaining = _FEEDBACK_DURATION
        elif self._success_remaining > 0:
            self._success_remaining = max(0.0, self._success_remaining - dt)

    def _draw_feedback(self) -> None:
        """Draw the current feedback message, if any.

        Priority: success message > proximity prompt.

        Only one message is drawn at a time.
        """
        if self._success_remaining > 0:
            self._renderer.draw_text(
                _SUCCESS_TEXT,
                _FEEDBACK_X,
                _FEEDBACK_Y,
                _FEEDBACK_COLOR,
                _FEEDBACK_FONT_SIZE,
            )
        elif self._is_near:
            self._renderer.draw_text(
                _PROMPT_TEXT,
                _FEEDBACK_X,
                _FEEDBACK_Y,
                _FEEDBACK_COLOR,
                _FEEDBACK_FONT_SIZE,
            )

    # ------------------------------------------------------------------
    # Internal: drawing
    # ------------------------------------------------------------------

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
