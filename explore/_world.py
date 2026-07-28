"""Explore Studio — Student API World model.

A ``World`` collects student-facing entities and, in M4C, will launch
the engine.  In this milestone only registration, cardinality, and
validation are implemented — ``run()`` is a deferred stub.

Ownership: Student API team.
"""

from __future__ import annotations

from explore._character import Character, _validate_name
from explore._error import StudentAPIError
from explore._object import Object


class World:
    """Student-facing container for one Character and one Object.

    In v0.1 a world holds exactly one of each.  Duplicate registration
    raises a friendly error.  ``run()`` is deferred to M4C.

    Usage::

        world = World("Treasure Island")
        world.add(explorer)
        world.add(chest)
        # world.run()  ← available in M4C
    """

    def __init__(self, name: str) -> None:
        self._name = _validate_name(name, "World")
        self._character: Character | None = None
        self._object: Object | None = None

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """The world's display name (appears in the window title bar)."""
        return self._name

    @property
    def character(self) -> Character | None:
        """The registered Character, or ``None``."""
        return self._character

    @property
    def object(self) -> Object | None:
        """The registered Object, or ``None``."""
        return self._object

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def add(self, entity: Character | Object) -> None:
        """Register a Character or Object with this world.

        Exactly one Character and one Object are permitted.  Adding a
        second of either type raises ``StudentAPIError``.

        Configuration (e.g. ``chest.when_near(...)``) may be set before
        or after calling ``add()`` — the entity stores its own config.

        Args:
            entity: A ``Character`` or ``Object`` instance.

        Raises:
            StudentAPIError: If a Character or Object is already
                registered, or if *entity* is not a recognised type.
        """
        if isinstance(entity, Character):
            if self._character is not None:
                raise StudentAPIError(
                    "This world already has a character.\n"
                    "Student API v0.1 supports one character at a time."
                )
            self._character = entity
        elif isinstance(entity, Object):
            if self._object is not None:
                raise StudentAPIError(
                    "This world already has an object.\n"
                    "Student API v0.1 supports one object at a time."
                )
            self._object = entity
        else:
            raise StudentAPIError(
                "You can only add a Character or an Object to the world.\n"
                f"You gave: {type(entity).__name__}"
            )

    # ------------------------------------------------------------------
    # Execution (deferred)
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Launch the world (not yet implemented).

        Raises:
            NotImplementedError: Always.  Execution is implemented in
                Task M4C (World Adapter and Execution).
        """
        raise NotImplementedError(
            "Student API execution is implemented in Task M4C.\n"
            "For now, your Character and Object are ready — "
            "the engine will launch them soon!"
        )
