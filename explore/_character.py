"""Explore Studio — Student API Character model.

A ``Character`` stores student-facing configuration for one movable
inhabitant of the world.  It does **not** create an engine ``Character``
— translation happens later in the adapter layer (M4C).

Ownership: Student API team.
"""

from __future__ import annotations

from typing import Any

from explore._colors import resolve_color
from explore._error import StudentAPIError


def _validate_name(value: Any, label: str) -> str:
    """Validate a display name.

    Returns the stripped string.  Rejects non-strings, empty strings,
    and whitespace-only strings.
    """
    if not isinstance(value, str):
        raise StudentAPIError(f"{label} name must be text (a string), not {type(value).__name__}.")
    stripped = value.strip()
    if not stripped:
        raise StudentAPIError(f"{label} name must not be empty.")
    return stripped


def _validate_coordinate(value: Any, label: str) -> int:
    """Validate a screen coordinate.

    Returns an ``int``.  Rejects bools, floats, negatives, and
    non-numeric types.
    """
    if isinstance(value, bool):
        raise StudentAPIError(
            f"{label} must be a whole number of 0 or greater. " f"You gave: {value}"
        )
    if not isinstance(value, int):
        if isinstance(value, float):
            raise StudentAPIError(
                f"{label} must be a whole number of 0 or greater. " f"You gave: {value}"
            )
        raise StudentAPIError(
            f"{label} must be a whole number of 0 or greater. " f"You gave: {type(value).__name__}"
        )
    if value < 0:
        raise StudentAPIError(
            f"{label} must be a whole number of 0 or greater. " f"You gave: {value}"
        )
    return value


class Character:
    """Student-facing configuration for a movable character.

    Stores identity, position, and colour.  The engine provides a fixed
    size (100 × 100) and movement speed — students do not set these.

    Use :meth:`World.add` to register this character with a world.
    """

    def __init__(
        self,
        *,
        name: str,
        x: int = 430,
        y: int = 270,
        color: str = "gold",
    ) -> None:
        self._name = _validate_name(name, "Character")
        self._x = _validate_coordinate(x, "Character x")
        self._y = _validate_coordinate(y, "Character y")
        self._color_name = color  # validated via resolve_color
        self._color_rgb = resolve_color(color)

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The character's display name."""
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
        """The named colour (e.g. ``"gold"``)."""
        return self._color_name

    @property
    def color_rgb(self) -> tuple[int, int, int]:
        """The resolved ``(r, g, b)`` tuple (engine-internal use)."""
        return self._color_rgb
