"""Capture the published Journey snapshots from the real Classroom Trail.

Each moment in ``scripts/journey_snapshots.py`` is driven headlessly
(``SDL_VIDEODRIVER=dummy``) with its session's canonical task-card packages,
player, and mission, real input, and fixed 1/60 s steps. The frame is checked
against the moment's expected state (target, text actually drawn, trusted art
actually drawn, no later session's content) before it is accepted, then
encoded as a 960w WebP and a 480w WebP downscaled from that same frame.

    python scripts/capture_journey_snapshots.py --session S02
    python scripts/capture_journey_snapshots.py --all-published
    python scripts/capture_journey_snapshots.py --check          # no capture
    python scripts/capture_journey_snapshots.py --all-published --dry-run
    python scripts/capture_journey_snapshots.py --session S01 --preview OUT

Publishing writes ``course4teen-website/public/journey/sNN/`` and updates
``course4teen-website/journey/snapshots.json``. It refuses deferred sessions,
sessions the website does not publish, and a working tree whose presentation
runtime differs from the Course Kit runtime pin. ``--preview`` writes PNG and
WebP files to a review directory only and never publishes, so it may capture a
deferred session or an unpinned runtime.

``--check`` fails on an unsupported manifest schema, on any published file or
manifest entry outside the publication boundary, on a stale fingerprint, and
on a committed image that differs from the manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import platform
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts import journey_snapshots as journey  # noqa: E402
from scripts.journey_snapshots import (  # noqa: E402
    CANONICAL_SIZE,
    MOON_MEADOW,
    PUBLIC_JOURNEY,
    WEBP_SETTINGS,
    WIDTHS,
    Fixture,
    Moment,
    PackageText,
    Session,
    TrailCommand,
)


class CaptureError(RuntimeError):
    """A moment did not reach its expected state, or capture is not allowed."""


@dataclass(frozen=True)
class Capture:
    row: Session
    moment: Moment
    command: TrailCommand
    rgb: bytes
    images: dict[int, bytes]
    parts: dict[str, str]


# ---------------------------------------------------------------------------
# Driving one moment
# ---------------------------------------------------------------------------


def _apply_fixture(fixture: Fixture, root: Path, directory: Path) -> Path:
    copy = directory / Path(fixture.package).name
    shutil.copytree(root, copy)
    source = copy / fixture.file
    text = source.read_text(encoding="utf-8")
    for key, value in fixture.values.items():
        rendered = str(value) if isinstance(value, int) else f'"{value}"'
        text, count = re.subn(rf"^{re.escape(key)}:.*$", f"{key}: {rendered}", text, flags=re.M)
        if count != 1:
            raise CaptureError(f"fixture {fixture.file}: expected one top-level {key}")
    source.write_text(text, encoding="utf-8")
    return copy


def _package_text(spec: PackageText) -> str:
    import yaml

    data = yaml.safe_load((journey.package_root(spec.package) / spec.file).read_text("utf-8"))
    value = data[spec.key]
    assert isinstance(value, str), (spec, value)
    return spec.prefix + value


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _verify(trail, row: Session, moment: Moment) -> list[str]:  # type: ignore[no-untyped-def]
    """Every reason the current frame is not the moment it claims to be."""
    import pygame

    from engine.rendering._classroom_environment import MEADOW_BACKDROP
    from engine.rendering._classroom_sprites import (
        COMPASS_SHEET_ID,
        MOON_COMPASS_QUALIFIED_ID,
        SPRITE_SHEET_IDS,
    )
    from engine.rendering._mission_presentation import mission_presentation
    from engine.rendering._trail_presentation import TrailPresentation

    problems: list[str] = []
    scene, renderer, expect = trail.scene, trail.renderer, moment.expect
    if pygame.display.get_surface().get_size() != CANONICAL_SIZE:
        problems.append(f"frame is {pygame.display.get_surface().get_size()}")

    drawn = {(asset, x) for asset, x, _, _, _, ok in renderer.sprites if ok}
    sheets_drawn = {asset for asset, _ in drawn}
    moon_meadow = mission_presentation(row.mission_id) is not None
    if moon_meadow != (row.presentation == MOON_MEADOW):
        given = "Moon Meadow" if moon_meadow else "the standard Trail"
        problems.append(
            f"runtime gives {row.mission_id} {given}, the table expects {row.presentation}"
        )
    if row.presentation == MOON_MEADOW and MEADOW_BACKDROP[0] not in sheets_drawn:
        problems.append("the Moon Meadow backdrop was not drawn")

    presentation = TrailPresentation(row.mission_id)

    def sheet(qualified_id: str) -> str | None:
        identity = presentation.sprite_identity(qualified_id)
        if identity == MOON_COMPASS_QUALIFIED_ID:
            return COMPASS_SHEET_ID
        return SPRITE_SHEET_IDS.get(identity) if identity is not None else None

    entities = {row.player: scene.player}
    entities.update((npc.qualified_id, npc.character) for npc in scene.npcs)
    entities.update((item.qualified_id, item.world_object) for item in scene.objects)
    width, height = CANONICAL_SIZE
    for qualified_id in row.must_show:
        entity = entities.get(qualified_id)
        if entity is None:
            problems.append(f"{qualified_id} is not in the scene")
            continue
        inside_x = 0 <= entity.x <= width - entity.width
        inside_y = 0 <= entity.y <= height - entity.height
        if not (inside_x and inside_y):
            problems.append(f"{qualified_id} is off screen")
        expected_sheet = sheet(qualified_id)
        if row.presentation == MOON_MEADOW and expected_sheet is None:
            problems.append(f"{qualified_id} has no trusted art in {row.mission_id}")
        elif expected_sheet is not None and (expected_sheet, entity.x) not in drawn:
            problems.append(f"{qualified_id} fell back instead of drawing {expected_sheet}")
    for qualified_id in row.must_not_show:
        if qualified_id in entities:
            problems.append(f"{qualified_id} belongs to another session but is in the scene")
    # No character or object art for anything the scene does not contain.
    entity_sheets = {sheet(qualified_id) for qualified_id in entities}
    for asset in sorted(sheets_drawn & ({*SPRITE_SHEET_IDS.values(), COMPASS_SHEET_ID})):
        if asset not in entity_sheets:
            problems.append(f"{asset} was drawn but no entity in the scene wears it")

    if expect.target is not None and scene.target_qualified_id != expect.target:
        problems.append(f"target is {scene.target_qualified_id}, expected {expect.target}")
    if expect.untargeted and scene.target_qualified_id is not None:
        problems.append(f"target is {scene.target_qualified_id}, expected no prompt")
    if set(scene.visited_qualified_ids) != set(expect.visited):
        visited = sorted(scene.visited_qualified_ids)
        problems.append(f"visited {visited}, expected {list(expect.visited)}")
    if scene.mission_is_complete != expect.complete:
        complete = scene.mission_is_complete
        problems.append(f"mission complete is {complete}, expected {expect.complete}")
    for qualified_id, x, y in expect.positions:
        entity = entities.get(qualified_id)
        if entity is None or (entity.x, entity.y) != (x, y):
            problems.append(f"{qualified_id} is not at ({x}, {y})")
    joined = _normalize(" ".join(renderer.texts))
    for spec in expect.texts:
        text = spec if isinstance(spec, str) else _package_text(spec)
        if isinstance(spec, PackageText) and spec.joined:
            if _normalize(text) not in joined:
                problems.append(f"the whole text {text!r} is not on screen")
        elif text not in renderer.texts:
            problems.append(f"{text!r} was not drawn")
    return problems


def capture_moment(row: Session, moment: Moment, command: TrailCommand) -> bytes:
    """Drive the real Trail to *moment* and return the checked 960x640 RGB frame."""
    import pygame

    from scripts.trail_driver import Trail

    with tempfile.TemporaryDirectory() as temporary:
        roots = []
        for argument in command.packages:
            root = journey.package_root(argument)
            if moment.fixture is not None and moment.fixture.package == argument:
                root = _apply_fixture(moment.fixture, root, Path(temporary))
            roots.append(root)
        if moment.fixture is not None and moment.fixture.package not in command.packages:
            raise CaptureError(f"{moment.name}: fixture package is not on the task card")
        trail = Trail(roots, mission_id=command.mission_id, player=command.player)
        try:
            for step in moment.steps:
                action, *values = step
                if action == "hold":
                    trail.hold(float(values[0]))  # type: ignore[arg-type]
                elif action == "walk_to":
                    trail.walk_to(int(values[0]), int(values[1]))  # type: ignore[arg-type]
                elif action == "tap" and values[0] in ("left", "right", "up", "down"):
                    trail.step(**{str(values[0]): True})
                elif action == "press":
                    trail.press()
                else:
                    raise CaptureError(f"{moment.name}: unknown step {step}")
            problems = _verify(trail, row, moment)
            if problems:
                raise CaptureError(f"{moment.name} was not reached: " + "; ".join(problems))
            return pygame.image.tobytes(pygame.display.get_surface(), "RGB")
        finally:
            trail.close()


def encode(rgb: bytes) -> dict[int, bytes]:
    """Both published WebP widths, each from the one canonical frame."""
    from PIL import Image

    source = Image.frombytes("RGB", CANONICAL_SIZE, rgb)
    images = {}
    for width in WIDTHS:
        height = width * CANONICAL_SIZE[1] // CANONICAL_SIZE[0]
        resample = getattr(Image.Resampling, str(WEBP_SETTINGS["resample"]))
        frame = (
            source
            if (width, height) == CANONICAL_SIZE
            else source.resize((width, height), resample)
        )
        buffer = io.BytesIO()
        frame.save(
            buffer,
            "WEBP",
            lossless=WEBP_SETTINGS["lossless"],
            quality=WEBP_SETTINGS["quality"],
            method=WEBP_SETTINGS["method"],
        )
        images[width] = buffer.getvalue()
    return images


def toolchain() -> dict[str, str]:
    import PIL
    import pygame
    from PIL import features

    return {
        "python": platform.python_version(),
        "pygame": pygame.version.ver,
        "sdl": ".".join(map(str, pygame.get_sdl_version())),
        "sdlTtf": ".".join(map(str, pygame.font.get_sdl_ttf_version())),
        "pillow": PIL.__version__,
        "libwebp": str(features.version("webp")),
        "platform": f"{sys.platform}-{platform.machine()}",
    }


def resolve(session: str) -> tuple[Session, TrailCommand]:
    row = journey.SESSIONS_BY_ID.get(session)
    if row is None:
        raise CaptureError(f"{session} has no row in the Journey snapshot table")
    command = journey.canonical_command(session)
    if command is None:
        raise CaptureError(f"{session}'s task card has no canonical trail command")
    if (command.mission_id, command.player) != (row.mission_id, row.player):
        raise CaptureError(
            f"{session}: the table says {row.mission_id} / {row.player} but the task card "
            f"says {command.mission_id} / {command.player}"
        )
    return row, command


def capture_session(session: str, *, runtime: str) -> list[Capture]:
    row, command = resolve(session)
    implementation = journey.capture_implementation_digest()
    captures = []
    for moment in row.moments:
        print(f"capturing {moment.name} ...", flush=True)
        rgb = capture_moment(row, moment, command)
        parts = journey.fingerprint_parts(row, moment, command, runtime, implementation)
        captures.append(Capture(row, moment, command, rgb, encode(rgb), parts))
    return captures


# ---------------------------------------------------------------------------
# Publishing, checking, previewing
# ---------------------------------------------------------------------------


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_entry(capture: Capture, runtime_commit: str, tools: dict[str, str]) -> dict:  # type: ignore[type-arg]
    row, moment = capture.row, capture.moment
    images = {}
    for width, data in capture.images.items():
        images[str(width)] = {
            "src": "/" + journey.image_path(row.session, moment.slug, width),
            "width": width,
            "height": width * CANONICAL_SIZE[1] // CANONICAL_SIZE[0],
            "bytes": len(data),
            "sha256": _sha256(data),
        }
    return {
        "session": row.session,
        "moment": moment.name,
        "kind": moment.kind,
        "missionId": capture.command.mission_id,
        "packages": list(capture.command.packages),
        "player": capture.command.player,
        "presentation": row.presentation,
        "fixture": journey.describe(moment.fixture) if moment.fixture else None,
        "runtimeCommit": runtime_commit,
        "presentationFingerprint": journey.presentation_fingerprint(capture.parts),
        "fingerprintParts": capture.parts,
        "sourceRgbSha256": _sha256(capture.rgb),
        "images": images,
        "toolchain": tools,
        "captureCommand": row.command,
    }


def require_pinned_runtime(root: Path = REPO) -> tuple[str, str]:
    """The pin and the runtime digest, if the tree at *root* draws what the pin draws.

    Compares every :data:`journey.RUNTIME_GROUPS` file, so a change to the
    package pipeline or colours blocks publishing just as a renderer change does.
    """
    pin = journey.runtime_pin()
    here = journey.runtime_digest(journey.runtime_files(root))
    try:
        pinned = journey.runtime_digest(journey.runtime_files_at(pin))
    except Exception as error:  # noqa: BLE001
        raise CaptureError(f"cannot read the runtime pin {pin} from git: {error}") from error
    if here != pinned:
        raise CaptureError(
            f"the working tree's presentation runtime differs from the Course Kit runtime pin "
            f"{pin}; publish only after the pin advances (use --preview to look now)"
        )
    return pin, here


def publish(sessions: list[str]) -> None:
    published = journey.published_sessions()
    for session in sessions:
        row = journey.SESSIONS_BY_ID.get(session)
        if session not in published:
            raise CaptureError(f"{session} is not published on the website; refusing")
        if row is not None and row.deferred:
            raise CaptureError(
                f"{session} is deferred: {row.deferred} When it is ready, delete `deferred=` "
                f"from its row in scripts/journey_snapshots.py and rerun `{row.command}`."
            )
    pin, runtime = require_pinned_runtime()
    tools = toolchain()
    manifest = journey.load_manifest()
    entries = [e for e in manifest.get("snapshots", []) if e["session"] not in sessions]  # type: ignore[union-attr]
    problem = journey.schema_problem(manifest)
    if problem and entries:
        # Entries kept from an older schema would carry fingerprints this code
        # cannot check; recapture them rather than relabel them.
        kept = sorted({entry.get("session") for entry in entries})
        raise CaptureError(f"{problem}; this run would keep {', '.join(kept)} unrecaptured")
    for session in sessions:
        captures = capture_session(session, runtime=runtime)
        directory = PUBLIC_JOURNEY / session.lower()
        if directory.exists():
            shutil.rmtree(directory)
        for capture in captures:
            for width, data in capture.images.items():
                published = journey.image_path(session, capture.moment.slug, width)
                path = journey.WEBSITE / "public" / published
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                print(f"wrote {path.relative_to(REPO)} ({len(data):,} bytes)")
            entries.append(manifest_entry(capture, pin, tools))
    journey.write_manifest(entries)
    print(f"updated {journey.MANIFEST_PATH.relative_to(REPO)}")


def check() -> list[str]:
    """Schema, publication boundary, freshness, and file integrity, without capturing."""
    manifest = journey.load_manifest()
    failures = journey.publication_problems(manifest)
    if failures:
        # Entries outside the contract cannot be fingerprinted meaningfully.
        return failures
    runtime = journey.runtime_digest()
    implementation = journey.capture_implementation_digest()
    for entry in manifest.get("snapshots", []):  # type: ignore[union-attr]
        try:
            reason = journey.stale_reason(entry, runtime, implementation)
        except journey.TaskCardError as error:
            reason = str(error)
        if reason:
            failures.append(reason)
        for image in entry["images"].values():
            path = journey.WEBSITE / "public" / image["src"].lstrip("/")
            if not path.is_file() or _sha256(path.read_bytes()) != image["sha256"]:
                failures.append(f"{path.relative_to(REPO)} is missing or differs from the manifest")
    return failures


def dry_run(sessions: list[str]) -> list[str]:
    """Recapture in memory and compare with the manifest; write nothing."""
    snapshots = journey.load_manifest().get("snapshots", [])
    manifest = {(e["session"], e["moment"]): e for e in snapshots}  # type: ignore[union-attr]
    same_tools = None
    differences = []
    for session in sessions:
        for capture in capture_session(session, runtime=journey.runtime_digest()):
            entry = manifest.get((session, capture.moment.name))
            if entry is None:
                differences.append(f"{capture.moment.name}: not in the manifest")
                continue
            same_tools = entry["toolchain"] == toolchain()
            if _sha256(capture.rgb) != entry["sourceRgbSha256"]:
                differences.append(f"{capture.moment.name}: source frame differs")
            for width, data in capture.images.items():
                if _sha256(data) != entry["images"][str(width)]["sha256"]:
                    differences.append(f"{capture.moment.name}: {width}w WebP bytes differ")
            print(f"{capture.moment.name}: compared")
    if differences and same_tools is False:
        print("note: this toolchain differs from the recorded one; byte equality is not promised")
    return differences


def preview(sessions: list[str], out: Path) -> None:
    import pygame

    for session in sessions:
        for capture in capture_session(session, runtime=journey.runtime_digest()):
            stem = out / session.lower() / capture.moment.slug
            stem.parent.mkdir(parents=True, exist_ok=True)
            surface = pygame.image.frombytes(capture.rgb, CANONICAL_SIZE, "RGB")
            pygame.image.save(surface, str(stem.with_suffix(".png")))
            for width, data in capture.images.items():
                suffix = "" if width == CANONICAL_SIZE[0] else f"-{width}"
                stem.with_name(f"{stem.name}{suffix}.webp").write_bytes(data)
            print(f"wrote {stem}.png and WebP previews (not published)")


def contact_sheet(out: Path) -> None:
    """Review-only sheet of the published 480w snapshots, one session per row."""
    from PIL import Image, ImageDraw

    entries = journey.load_manifest().get("snapshots", [])
    rows: dict[str, list[dict]] = {}  # type: ignore[type-arg]
    for entry in entries:  # type: ignore[union-attr]
        rows.setdefault(entry["session"], []).append(entry)
    tile_w, tile_h, label = 480, 320, 26
    columns = max(len(row) for row in rows.values())
    sheet = Image.new("RGB", (columns * tile_w, len(rows) * (tile_h + label)), (24, 26, 40))
    draw = ImageDraw.Draw(sheet)
    for row_index, (session, row) in enumerate(rows.items()):
        for column, entry in enumerate(row):
            x, y = column * tile_w, row_index * (tile_h + label)
            path = journey.WEBSITE / "public" / entry["images"]["480"]["src"].lstrip("/")
            with Image.open(path) as image:
                sheet.paste(image.convert("RGB"), (x, y + label))
            caption = f"{session} {entry['kind']}: {entry['moment']}"
            draw.text((x + 8, y + 7), caption, fill=(240, 236, 220))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, optimize=True)
    print(f"wrote {out}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--session", action="append", help="e.g. S02 (repeatable)")
    target.add_argument("--all-published", action="store_true", help="every non-deferred row")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify freshness; no capture")
    mode.add_argument("--dry-run", action="store_true", help="recapture and compare; no writes")
    mode.add_argument("--preview", type=Path, metavar="DIR", help="write review files to DIR only")
    mode.add_argument("--contact-sheet", type=Path, metavar="PNG", help="review-only contact sheet")
    args = parser.parse_args(argv)

    if args.check:
        failures = check()
        print("\n".join(failures) if failures else "Journey snapshots are fresh.")
        return 1 if failures else 0
    if args.contact_sheet:
        contact_sheet(args.contact_sheet)
        return 0
    if args.all_published:
        published = journey.published_sessions()
        sessions = [
            row.session for row in journey.SESSIONS if not row.deferred and row.session in published
        ]
    elif args.session:
        sessions = [session.upper() for session in args.session]
    else:
        parser.error("choose --session or --all-published")
    try:
        if args.preview:
            preview(sessions, args.preview)
        elif args.dry_run:
            differences = dry_run(sessions)
            print("\n".join(differences) if differences else "Recaptured byte-for-byte.")
            return 1 if differences else 0
        else:
            publish(sessions)
    except (CaptureError, journey.TaskCardError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
