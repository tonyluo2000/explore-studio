"""Decode-once, frame-cached sprite sheets built on the trusted art catalog.

A sheet is read and verified once, decoded once by the platform, and each
requested frame (at a requested size and facing) is cut and cached once. Any
failure is remembered, logged once, and reported as ``None`` so callers draw
their procedural fallback instead of retrying every frame.

Internal module — not part of the Student API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Final, Protocol

from engine.assets._trusted_art import Color, SpriteSheetSpec, TrustedArtCatalog

_LOGGER = logging.getLogger("explore-studio.assets.sprite-sheets")

#: Upper bound on cached frames; the S02 Trail uses well under this (about
#: 170: every Nova, Pixel, Lantern, reed, Compass ring, and needle frame).
MAX_CACHED_FRAMES: Final = 384


@dataclass(frozen=True, eq=False)
class ImageHandle:
    """Opaque engine-owned image. Only the platform reads ``native``."""

    width: int
    height: int
    native: object = field(repr=False)


class ImageDecoder(Protocol):
    def decode_image(self, data: bytes) -> ImageHandle: ...

    def crop_image(
        self,
        image: ImageHandle,
        x: int,
        y: int,
        width: int,
        height: int,
        out_width: int,
        out_height: int,
        flip_x: bool,
    ) -> ImageHandle: ...


FrameKey = tuple[str, str, str, int, int, bool, Color | None]


class SpriteSheetLibrary:
    """Serve cached frames from trusted sheets through an image decoder."""

    def __init__(self, decoder: ImageDecoder, catalog: TrustedArtCatalog | None = None) -> None:
        self._decoder = decoder
        self._catalog = catalog if catalog is not None else TrustedArtCatalog()
        self._sheets: dict[str, ImageHandle | None] = {}
        self._frames: dict[FrameKey, ImageHandle | None] = {}
        self.decode_count = 0

    @property
    def catalog(self) -> TrustedArtCatalog:
        return self._catalog

    @property
    def cached_frame_count(self) -> int:
        return len(self._frames)

    def spec(self, asset_id: str) -> SpriteSheetSpec | None:
        return self._catalog.spec(asset_id)

    def accent(self, asset_id: str) -> Color | None:
        spec = self._catalog.spec(asset_id)
        return None if spec is None else spec.accent

    def _sheet(self, spec: SpriteSheetSpec) -> ImageHandle | None:
        if spec.asset_id in self._sheets:
            return self._sheets[spec.asset_id]
        sheet: ImageHandle | None = None
        data = self._catalog.read_verified(spec.asset_id)
        if data is not None:
            try:
                self.decode_count += 1
                decoded = self._decoder.decode_image(data)
                if decoded.width < spec.frame_width * len(
                    spec.columns
                ) or decoded.height < spec.frame_height * len(spec.rows):
                    raise ValueError("sheet is smaller than its declared frame grid")
                sheet = decoded
            except Exception:
                _LOGGER.exception("Trusted art %s could not be decoded", spec.asset_id)
                sheet = None
        self._sheets[spec.asset_id] = sheet
        return sheet

    def frame(
        self,
        asset_id: str,
        row: str,
        column: str,
        width: int,
        height: int,
        *,
        flip_x: bool = False,
        tint: Color | None = None,
    ) -> ImageHandle | None:
        """Return one frame scaled to *width* x *height*, or ``None``.

        A *tint* multiplies the frame's color (for neutral art such as the
        student-colored Moon Compass ring); the tinted frame is cached too.
        """
        if width <= 0 or height <= 0:
            return None
        key: FrameKey = (asset_id, row, column, width, height, flip_x, tint)
        if key in self._frames:
            return self._frames[key]
        spec = self._catalog.spec(asset_id)
        cell = None if spec is None else spec.cell(row, column)
        image: ImageHandle | None = None
        if spec is not None and cell is not None:
            sheet = self._sheet(spec)
            if sheet is not None:
                try:
                    image = self._decoder.crop_image(
                        sheet,
                        cell[0],
                        cell[1],
                        spec.frame_width,
                        spec.frame_height,
                        width,
                        height,
                        flip_x,
                    )
                    if tint is not None:
                        # Optional decoder capability; without it, no tinted art.
                        tinter = getattr(self._decoder, "tint_image", None)
                        image = None if tinter is None else tinter(image, tint)
                except Exception:
                    _LOGGER.exception("Trusted art %s frame %s/%s failed", asset_id, row, column)
                    image = None
        if len(self._frames) >= MAX_CACHED_FRAMES:
            self._frames.clear()
        self._frames[key] = image
        return image
