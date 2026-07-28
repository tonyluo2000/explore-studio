"""Explore Studio — Student API Object model.

An ``Object`` stores student-facing configuration for one stationary
item in the world plus optional interaction messages.

It does **not** create an engine ``WorldObject`` — translation happens
later in the adapter layer (M4C).

Ownership: Student API team.
"""

from __future__ import annotations

from typing import Any

from explore._character import _FREEZE_MESSAGE, _validate_coordinate, _validate_name
from explore._colors import resolve_color
from explore._error import StudentAPIError


def _validate_message(value: Any, label: str) -> str:
    """Validate an interaction message string.

    Returns the stripped string.  Rejects non-strings, empty, and
    whitespace-only values.
    """
    if not isinstance(value, str):
        raise StudentAPIError(
            f"{label} message must be text (a string), " f"not {type(value).__name__}."
        )
    stripped = value.strip()
    if not stripped:
        raise StudentAPIError(f"{label} message must not be empty.")
    return stripped


class Object:
    """Student-facing configuration for a stationary world object.

    Stores identity, position, colour, and optional interaction
    messages.  The engine provides a fixed size (80 × 60) — students
    do not set this.

    Once the world starts running, the object becomes frozen —
    messages and properties cannot be changed.

    Use :meth:`World.add` to register this object with a world.
    """

    def __init__(
        self,
        *,
        name: str,
        x: int,
        y: int,
        color: str = "brown",
    ) -> None:
        self._name = _validate_name(name, "Object")
        self._x = _validate_coordinate(x, "Object x")
        self._y = _validate_coordinate(y, "Object y")
        self._color_name = color
        self._color_rgb = resolve_color(color)
        self._near_message: str | None = None
        self._interacted_message: str | None = None
        self._frozen = False

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The object's display name."""
        return self._name

    @property
    def x(self) -> int:
        """Left-edge x-coordinate in pixels."""
        return self._x

    @property
    def y(self) -> int:
        """Top-edge y-coordinate in pixels."""
        return self._y

    @property
    def color(self) -> str:
        """The named colour (e.g. ``"brown"``)."""
        return self._color_name

    @property
    def color_rgb(self) -> tuple[int, int, int]:
        """The resolved ``(r, g, b)`` tuple (engine-internal use)."""
        return self._color_rgb

    @property
    def near_message(self) -> str | None:
        """The proximity prompt, or ``None`` if not set."""
        return self._near_message

    @property
    def interacted_message(self) -> str | None:
        """The success message, or ``None`` if not set."""
        return self._interacted_message

    @property
    def frozen(self) -> bool:
        """``True`` once the world starts running."""
        return self._frozen

    # ------------------------------------------------------------------
    # Freeze (called by World.run())
    # ------------------------------------------------------------------

    def _freeze(self) -> None:
        """Lock this object's configuration (engine-internal)."""
        self._frozen = True

    def _check_not_frozen(self) -> None:
        """Raise if the world is already running."""
        if self._frozen:
            raise StudentAPIError(_FREEZE_MESSAGE)

    # ------------------------------------------------------------------
    # Interaction message configuration
    # ------------------------------------------------------------------

    def when_near(self, message: str) -> None:
        """Set the message shown while the character is near this object.

        Args:
            message: Non-empty string (e.g. ``"Press E to explore"``).

        Raises:
            StudentAPIError: If the world is already running.
        """
        self._check_not_frozen()
        self._near_message = _validate_message(message, "when_near")

    def when_interacted(self, message: str) -> None:
        """Set the message shown briefly after a successful interaction.

        Args:
            message: Non-empty string (e.g. ``"You found a treasure!"``).

        Raises:
            StudentAPIError: If the world is already running.
        """
        self._check_not_frozen()
        self._interacted_message = _validate_message(message, "when_interacted")
