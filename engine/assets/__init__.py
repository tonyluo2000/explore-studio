"""Explore Studio engine — asset management.

Owns asset loading, caching, and provision to other subsystems. Manages
images, sounds, and fonts. Assets are referenced by name; the subsystem
handles the file system details.

Submodules:
    _trusted_art   — TrustedArtCatalog: manifest-listed, digest-verified,
                     course-owned sprite sheets (no Pygame).
    _sprite_sheets — SpriteSheetLibrary: decode-once, frame-cached sheets
                     behind an opaque ImageHandle.

Ownership: Engine team.
"""

from engine.assets._sprite_sheets import ImageHandle, SpriteSheetLibrary
from engine.assets._trusted_art import TRUSTED_ART_ROOT, SpriteSheetSpec, TrustedArtCatalog

__all__ = [
    "TRUSTED_ART_ROOT",
    "ImageHandle",
    "SpriteSheetLibrary",
    "SpriteSheetSpec",
    "TrustedArtCatalog",
]
