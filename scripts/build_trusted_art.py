"""Build the course-owned trusted art for the S02 Classroom Trail.

This is the provenance for every PNG under ``engine/assets/trusted``. The art
is original and painted from code by the small signed-distance-field painter
in ``scripts/art`` (numpy + Pillow, build time only): analytic anti-aliasing,
outlines as shape offsets, soft cel shading, rim light, gradients, seeded
noise textures, and additive glows. The script also writes ``manifest.json``,
which records each sheet's frame grid, declared accent color, and SHA-256
digest. The runtime loads only files listed in that manifest whose bytes
match their digest, and never imports numpy or Pillow.

Sheets:

* ``scenery/moon-meadow`` — the opaque 960 x 640 illustrated background plate.
* ``scenery/moon-meadow-foreground`` — transparent framing plants over entities.
* ``characters/nova`` — Nova V3: idle, blink, and an 8-frame walk per facing.
* ``characters/pixel`` — Pixel V3: idle, blink, and a greeting wave.
* ``objects/moon-compass`` — ring (tinted by the student's color), body, glass.
* ``objects/moon-compass-needle`` — the needle at 64 pre-rotated angles.
* ``objects/crystal-lantern`` — the lantern and its flickering crystal flame.
* ``ambient/reeds`` — a cattail clump at nine sway angles.

Run from the repository root after changing the art, then review the PNGs::

    pip install -e ".[art]"
    python3 scripts/build_trusted_art.py

The committed PNGs and manifest are the reviewed artifact; regenerating them
with a different numpy or Pillow build may change bytes, so always commit the
pair together.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "scripts"), str(REPO)]

from art import characters, meadow, objects  # noqa: E402
from art.paint import sheet  # noqa: E402
from PIL import Image  # noqa: E402

TRUSTED_ROOT = REPO / "engine" / "assets" / "trusted"

Color = tuple[int, int, int]


@dataclass(frozen=True)
class SheetSpec:
    asset_id: str
    file: str
    frame: tuple[int, int]
    rows: Sequence[str]
    columns: Sequence[str]
    accent: Color
    draw: Callable[[str, str], Image.Image]
    opaque: bool = False


def _scenery(
    canvas_factory: Callable[[], object], *, opaque: bool
) -> Callable[[str, str], Image.Image]:
    def draw(_row: str, _column: str) -> Image.Image:
        return canvas_factory().image(opaque=opaque)  # type: ignore[attr-defined]

    return draw


SHEETS: tuple[SheetSpec, ...] = (
    SheetSpec(
        "scenery/moon-meadow",
        "scenery/moon-meadow/background.png",
        (meadow.WIDTH, meadow.HEIGHT),
        ("night",),
        ("backdrop",),
        meadow.GROUND_MID,
        _scenery(meadow.paint_background, opaque=True),
        opaque=True,
    ),
    SheetSpec(
        "scenery/moon-meadow-foreground",
        "scenery/moon-meadow/foreground.png",
        (meadow.WIDTH, meadow.HEIGHT),
        ("night",),
        ("frame",),
        meadow.FG_DARK,
        _scenery(meadow.paint_foreground, opaque=False),
    ),
    SheetSpec(
        "characters/nova",
        "characters/nova/nova.png",
        (100, 100),
        characters.NOVA_ROWS,
        characters.NOVA_COLUMNS,
        characters.NOVA_ACCENT,
        characters.nova_frame,
    ),
    SheetSpec(
        "characters/pixel",
        "characters/pixel/pixel.png",
        (100, 100),
        characters.PIXEL_ROWS,
        characters.PIXEL_COLUMNS,
        characters.PIXEL_ACCENT,
        lambda _row, column: characters.pixel_frame(column),
    ),
    SheetSpec(
        "objects/moon-compass",
        "objects/moon-compass/compass.png",
        objects.COMPASS_FRAME,
        objects.COMPASS_ROWS,
        objects.COMPASS_SPIN,
        objects.COMPASS_ACCENT,
        objects.compass_frame,
    ),
    SheetSpec(
        "objects/moon-compass-needle",
        "objects/moon-compass/needle.png",
        objects.COMPASS_FRAME,
        ("needle",),
        objects.NEEDLE_COLUMNS,
        objects.COMPASS_ACCENT,
        lambda _row, column: objects.needle_frame(column),
    ),
    SheetSpec(
        "objects/crystal-lantern",
        "objects/crystal-lantern/lantern.png",
        objects.LANTERN_FRAME,
        objects.LANTERN_ROWS,
        objects.LANTERN_COLUMNS,
        objects.LANTERN_ACCENT,
        lambda _row, column: objects.lantern_frame(column),
    ),
    SheetSpec(
        "ambient/reeds",
        "ambient/reeds/reeds.png",
        objects.REED_FRAME,
        objects.REED_ROWS,
        objects.REED_COLUMNS,
        objects.REED_ACCENT,
        lambda _row, column: objects.reed_frame(column),
    ),
)


def _render(spec: SheetSpec) -> Image.Image:
    frames = [[spec.draw(row, column) for column in spec.columns] for row in spec.rows]
    for row in frames:
        for frame in row:
            if frame.size != spec.frame:
                raise ValueError(f"{spec.asset_id} frame is {frame.size}, expected {spec.frame}")
    if spec.opaque:
        return frames[0][0].convert("RGB")
    return sheet(frames)


def build(root: Path = TRUSTED_ROOT, only: Sequence[str] = ()) -> dict[str, object]:
    manifest_path = root / "manifest.json"
    previous: dict[str, object] = {}
    if only and manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))["assets"]
    assets: dict[str, object] = {}
    for spec in SHEETS:
        destination = root / spec.file
        if only and spec.asset_id not in only and spec.asset_id in previous:
            assets[spec.asset_id] = previous[spec.asset_id]
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        _render(spec).save(destination, format="PNG", optimize=True)
        assets[spec.asset_id] = {
            "file": spec.file,
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "frame_width": spec.frame[0],
            "frame_height": spec.frame[1],
            "rows": list(spec.rows),
            "columns": list(spec.columns),
            "accent": list(spec.accent),
        }
    manifest = {
        "schema_version": 1,
        "generator": "scripts/build_trusted_art.py",
        "assets": assets,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    """Build every sheet, or only the asset ids given on the command line."""
    only = tuple(sys.argv[1:] if argv is None else argv)
    manifest = build(only=only)
    for asset_id, entry in manifest["assets"].items():  # type: ignore[union-attr]
        size = (TRUSTED_ROOT / entry["file"]).stat().st_size
        print(f"{asset_id}: {entry['file']} {size // 1024} KiB sha256={entry['sha256'][:12]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
