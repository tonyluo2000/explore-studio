"""Course-owned trusted art catalog.

Only files listed in ``trusted/manifest.json`` can be read, only from inside
the trusted directory, and only when their bytes match the recorded SHA-256
digest. Anything missing, malformed, tampered with, or outside the directory
reads as unavailable (``None``) so callers keep their procedural fallback.

This module is pure Python: it never imports Pygame and never decodes images.
The platform decodes verified bytes; see ``engine.assets._sprite_sheets``.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final

_LOGGER = logging.getLogger("explore-studio.assets.trusted-art")

#: Directory that ships inside the ``engine`` distribution package.
TRUSTED_ART_ROOT: Final = Path(__file__).resolve().parent / "trusted"
MANIFEST_NAME: Final = "manifest.json"
SUPPORTED_MANIFEST_SCHEMA: Final = 1

Color = tuple[int, int, int]


@dataclass(frozen=True)
class SpriteSheetSpec:
    """One manifest entry: a grid of equal frames with named rows and columns."""

    asset_id: str
    file: str
    sha256: str
    frame_width: int
    frame_height: int
    rows: tuple[str, ...]
    columns: tuple[str, ...]
    accent: Color

    def cell(self, row: str, column: str) -> tuple[int, int] | None:
        """Return the pixel origin of one named frame, or ``None`` if unknown."""
        if row not in self.rows or column not in self.columns:
            return None
        return (
            self.columns.index(column) * self.frame_width,
            self.rows.index(row) * self.frame_height,
        )


def _positive_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("frame dimensions must be positive integers")
    return value


def _names(value: object) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(name, str) or not name for name in value)
        or len(set(value)) != len(value)
    ):
        raise ValueError("rows and columns must be non-empty lists of unique names")
    return tuple(value)


def _color(value: object) -> Color:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(
            isinstance(channel, bool) or not isinstance(channel, int) or not 0 <= channel <= 255
            for channel in value
        )
    ):
        raise ValueError("accent must be an RGB list")
    return (value[0], value[1], value[2])


def _parse_entry(asset_id: str, entry: object) -> SpriteSheetSpec:
    if not isinstance(entry, dict):
        raise ValueError("asset entries must be objects")
    file = entry.get("file")
    digest = entry.get("sha256")
    if not isinstance(file, str) or not file.endswith(".png"):
        raise ValueError("asset file must be a .png path")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError("asset sha256 must be 64 lowercase hex characters")
    return SpriteSheetSpec(
        asset_id=asset_id,
        file=file,
        sha256=digest,
        frame_width=_positive_int(entry.get("frame_width")),
        frame_height=_positive_int(entry.get("frame_height")),
        rows=_names(entry.get("rows")),
        columns=_names(entry.get("columns")),
        accent=_color(entry.get("accent")),
    )


class TrustedArtCatalog:
    """Read-only, digest-verified access to course-owned sprite sheets."""

    def __init__(self, root: Path = TRUSTED_ART_ROOT) -> None:
        self._root = Path(root)
        self._specs: dict[str, SpriteSheetSpec] | None = None

    @property
    def root(self) -> Path:
        return self._root

    def _load_manifest(self) -> dict[str, SpriteSheetSpec]:
        if self._specs is not None:
            return self._specs
        specs: dict[str, SpriteSheetSpec] = {}
        try:
            raw = json.loads((self._root / MANIFEST_NAME).read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or raw.get("schema_version") != SUPPORTED_MANIFEST_SCHEMA:
                raise ValueError("unsupported trusted art manifest schema")
            assets = raw.get("assets")
            if not isinstance(assets, dict):
                raise ValueError("manifest assets must be an object")
            for asset_id, entry in sorted(assets.items()):
                specs[asset_id] = _parse_entry(asset_id, entry)
        except (OSError, ValueError) as error:
            _LOGGER.warning("Trusted art manifest unavailable (%s); using procedural art", error)
            specs = {}
        self._specs = specs
        return specs

    def spec(self, asset_id: str) -> SpriteSheetSpec | None:
        """Return the manifest entry for *asset_id*, or ``None``."""
        return self._load_manifest().get(asset_id)

    def asset_ids(self) -> tuple[str, ...]:
        return tuple(self._load_manifest())

    def read_verified(self, asset_id: str) -> bytes | None:
        """Return the sheet bytes only when they match the recorded digest."""
        spec = self.spec(asset_id)
        if spec is None:
            return None
        root = self._root.resolve()
        path = (root / spec.file).resolve()
        if not path.is_relative_to(root):
            _LOGGER.warning("Trusted art %s points outside the trusted directory", asset_id)
            return None
        try:
            data = path.read_bytes()
        except OSError as error:
            _LOGGER.warning("Trusted art %s is unavailable (%s)", asset_id, error)
            return None
        if hashlib.sha256(data).hexdigest() != spec.sha256:
            _LOGGER.warning("Trusted art %s failed its digest check", asset_id)
            return None
        return data
