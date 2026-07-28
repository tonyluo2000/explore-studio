"""Explore Studio — named colour registry.

Maps classroom-friendly colour names to engine RGB tuples.  Students
never see RGB values — they use names like ``"gold"`` or ``"brown"``.

The registry is a private dictionary.  To add a colour in a future
milestone, add an entry here — the public API does not change.

Ownership: Student API team.  Internal module.
"""

from __future__ import annotations

from typing import Any

from explore._error import StudentAPIError

# Maps lowercase colour name → (r, g, b).
_COLORS: dict[str, tuple[int, int, int]] = {
    "red": (220, 50, 50),
    "orange": (240, 140, 50),
    "yellow": (240, 210, 50),
    "green": (50, 180, 50),
    "blue": (50, 80, 220),
    "purple": (140, 50, 180),
    "pink": (240, 140, 180),
    "brown": (139, 90, 43),
    "gold": (255, 200, 50),
}

# Cache the sorted list for error messages.
_VALID_NAMES = sorted(_COLORS.keys())


def resolve_color(name: Any) -> tuple[int, int, int]:
    """Translate a named colour to an RGB tuple.

    Args:
        name: A colour name string (case-sensitive, lowercase).

    Returns:
        ``(r, g, b)`` tuple of ints in 0–255.

    Raises:
        StudentAPIError: If *name* is not one of the nine valid colours.
    """
    if not isinstance(name, str) or name not in _COLORS:
        lines = ["Choose from:"]
        # Four names per line for readability.
        for i in range(0, len(_VALID_NAMES), 4):
            lines.append(", ".join(_VALID_NAMES[i : i + 4]) + ".")
        valid_list = "\n".join(lines)
        raise StudentAPIError(f'"{name}" is not a valid colour.\n\n{valid_list}')
    return _COLORS[name]


def valid_color_names() -> list[str]:
    """Return the list of valid colour names (for tests/docs)."""
    return list(_VALID_NAMES)
