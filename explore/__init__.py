"""Explore Studio — Student API v0.1.

The public interface students import from::

    from explore import World, Character, Object

Everything else is internal.  Students never import from ``engine``.

Student API v0.1 is complete — ``world.run()`` launches the engine.
"""

from explore._character import Character
from explore._error import StudentAPIError
from explore._object import Object
from explore._world import World

__all__ = ["Character", "Object", "StudentAPIError", "World"]
