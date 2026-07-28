"""Explore Studio — Student API v0.1.

The public interface students import from::

    from explore import World, Character, Object

Everything else is internal.  Students never import from ``engine``.

Current milestone: **M4B — Student Model Foundation**.
Execution (``world.run()``) is deferred to M4C.
"""

from explore._character import Character
from explore._error import StudentAPIError
from explore._object import Object
from explore._world import World

__all__ = ["Character", "Object", "StudentAPIError", "World"]
