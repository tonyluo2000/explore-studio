"""The Journey snapshot contract: one session-moment table, fingerprints, and the manifest.

Every published session with a canonical ``explore-package trail`` command gets
one required HERO snapshot (the session's learning moment) and at most two
optional ones (``LEARNING_MOMENT``, ``COMPLETE``). This module holds only data
and pure checks, so tests import it without starting pygame;
``scripts/capture_journey_snapshots.py`` drives the real Trail to capture them.

Packages, the player, and the mission come from the session's task card, never
from a second hand-maintained list: :func:`canonical_command` reads the card,
and the table only states what each moment must show. Tests keep the table's
mission and player equal to the card.

The ``presentationFingerprint`` hashes only what can change a captured frame,
in four named parts (see :data:`FINGERPRINT_PARTS`):

``runtime``
    The code and trusted art between task-card package files and the drawn
    frame (:data:`RUNTIME_GROUPS`). The Course Kit runtime pin is compared on
    exactly these files before anything is published.
``packages``
    Every file of every package the task card names.
``captureRecipe``
    The values that say which moment to capture and how to encode it: the
    task-card command, the session row, the moment, the frame size, the WebP
    settings.
``captureImplementation``
    The bytes of the harness that interprets that recipe: the fixed time step,
    real input, frame selection, acceptance checks, and encoding
    (:data:`CAPTURE_IMPLEMENTATION_INPUTS`).

When any part changes the freshness check fails, names the part, and names the
command that recaptures the session.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Final

REPO: Final = Path(__file__).resolve().parents[1]
WEBSITE: Final = REPO / "course4teen-website"
#: Published Journey images, served at ``/journey/sNN/<slug>.webp``.
PUBLIC_JOURNEY: Final = WEBSITE / "public" / "journey"
#: Provenance for the published images. Outside ``public/``, so never served.
MANIFEST_PATH: Final = WEBSITE / "journey" / "snapshots.json"
CALENDAR: Final = WEBSITE / "lib" / "calendar.ts"
SESSIONS_DIR: Final = REPO / "lessons" / "sessions"
SCHEMA_NAME: Final = "explore-studio/journey-snapshots"
SCHEMA_VERSION: Final = 2
SCHEMA: Final = f"{SCHEMA_NAME}@{SCHEMA_VERSION}"
#: Manifest schemas this code can check. Version 1 had no capture
#: implementation fingerprint, so its entries cannot be trusted as fresh.
SUPPORTED_SCHEMAS: Final = frozenset({SCHEMA})
CAPTURE_SCRIPT: Final = "scripts/capture_journey_snapshots.py"

CANONICAL_SIZE: Final = (960, 640)
#: Published widths; each is a downscale of the one canonical source frame.
WIDTHS: Final = (960, 480)
#: Lossy WebP from an opaque RGB frame: no alpha, no EXIF/ICC/XMP, no timestamps.
WEBP_SETTINGS: Final[Mapping[str, object]] = {
    "lossless": False,
    "quality": 90,
    "method": 6,
    "resample": "LANCZOS",
}

HERO, LEARNING_MOMENT, COMPLETE = "HERO", "LEARNING_MOMENT", "COMPLETE"
KINDS: Final = (HERO, LEARNING_MOMENT, COMPLETE)
MAX_OPTIONAL: Final = 2
STANDARD, MOON_MEADOW = "standard", "moon-meadow"

NOVA: Final = "nova-character:nova"
PIXEL: Final = "pixel-companion:pixel"
LANTERN: Final = "crystal-lantern:lantern"
S02_COMPASS: Final = "moon-compass:compass"
S03_COMPASS: Final = "moon-compass-response:compass"
GUIDE: Final = "moonlit-guide:guide"
#: The pre-Moon Meadow S01 cast, retired by Phase B.
FERN: Final = "forest-guide:guide"
FOUNTAIN: Final = "river-fountain:fountain"

S02_PACKAGE: Final = "../my-explore-world/projects/moon-compass"
S03_PACKAGE: Final = "lessons/sessions/s03/student/explorer-package"
S04_PACKAGE: Final = "lessons/sessions/s04/student/explorer-package"

#: The presentation runtime: everything between the task-card package files and
#: the drawn frame, in groups an auditor can read. ``tests/test_journey_snapshots.py``
#: walks the harness's imports statically and fails if it reaches an engine or
#: ``explore`` module that is neither here nor in :data:`RUNTIME_PIXEL_INERT`.
RUNTIME_GROUPS: Final[Mapping[str, tuple[str, ...]]] = {
    # Window size, palette, display setup, and frame clearing.
    "engine-core": ("engine/_color.py", "engine/_config.py", "engine/_platform.py"),
    # The renderer, Moon Meadow environment and layout, sprites, effects, and
    # the per-mission presentation policy.
    "rendering": ("engine/rendering",),
    # Scene update and render order, entities, movement, animation clips,
    # input handling, and proximity (what becomes the target). The scene's
    # audio bridge is here too: the scene calls it every frame and it draws
    # the audio indicator.
    "scene": (
        "engine/scenes",
        "engine/entities",
        "engine/animation",
        "engine/input",
        "engine/interactions",
        "engine/audio/_trail_audio.py",
    ),
    # Course-owned sprite sheets and the code that loads and slices them.
    "trusted-art": (
        "engine/assets/__init__.py",
        "engine/assets/_sprite_sheets.py",
        "engine/assets/_trusted_art.py",
        "engine/assets/trusted",
    ),
    # Mission definitions: targets, completion, and labels drawn on screen.
    "curriculum": ("explore/curriculum",),
    # Package YAML -> scene: loader, models, policy, validator, package-set
    # planner, registration adapter, Trail plan and scene construction, and
    # the colour names they resolve.
    "package-pipeline": ("explore/packages", "explore/_colors.py"),
}
RUNTIME_INPUTS: Final = tuple(path for group in RUNTIME_GROUPS.values() for path in group)

#: Modules the harness imports that cannot change a pixel, and why. Anything
#: else it imports from ``engine`` or ``explore`` must be in :data:`RUNTIME_GROUPS`.
RUNTIME_PIXEL_INERT: Final[Mapping[str, str]] = {
    "engine/audio/__init__.py": "re-exports the audio manager and modes",
    "engine/audio/_cues.py": "sound cue definitions; draws nothing",
    "engine/audio/_manager.py": "audio playback; the harness runs with no audio manager",
    "engine/assets/_trusted_audio.py": "loads trusted audio clips; draws nothing",
    "engine/__init__.py": "re-exports App and Config; the harness never runs App",
    "engine/app.py": "the windowed App loop; the harness drives the scene itself",
    "engine/_logging.py": "logging setup",
    "explore/__init__.py": "re-exports the Student API v0.1 classes",
    "explore/_character.py": "Student API v0.1 Character; the Trail never builds one",
    "explore/_object.py": "Student API v0.1 Object; the Trail never builds one",
    "explore/_world.py": "Student API v0.1 World; the Trail never builds one",
    "explore/_error.py": "the StudentAPIError exception type",
}

#: The capture harness itself. ``captureRecipe`` hashes the table values; these
#: bytes hash the code that turns them into a frame (``STEP``, ``walk_to``,
#: ``hold``, the acceptance checks, ``encode``, package resolution).
CAPTURE_IMPLEMENTATION_INPUTS: Final = (
    "scripts/capture_journey_snapshots.py",
    "scripts/journey_snapshots.py",
    "scripts/trail_driver.py",
)

#: The values ``captureRecipe`` hashes (see :func:`capture_recipe`).
CAPTURE_RECIPE_FIELDS: Final = (
    "session",
    "missionId",
    "player",
    "packages",
    "presentation",
    "mustShow",
    "mustNotShow",
    "moment",
    "canonicalSize",
    "widths",
    "webp",
)

#: The fingerprint parts, in the order they are joined, and what each covers.
FINGERPRINT_PARTS: Final[Mapping[str, str]] = {
    "runtime": "presentation runtime (engine rendering/scene/assets, package pipeline)",
    "packages": "session package files",
    "captureRecipe": "capture recipe or task-card command",
    "captureImplementation": "capture harness implementation",
}

_RUNTIME_SUFFIXES: Final = frozenset({".py", ".json", ".png"})


# ---------------------------------------------------------------------------
# The session-moment table
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PackageText:
    """Text that must be on screen, read from a package file, not restated here.

    ``joined`` text may wrap over several drawn lines (a speech bubble);
    otherwise one ``draw_text`` call must draw exactly ``prefix + value``.
    """

    package: str
    file: str
    key: str
    prefix: str = ""
    joined: bool = False


@dataclass(frozen=True)
class Fixture:
    """A supported student edit, applied to a temporary copy of one package."""

    package: str
    file: str
    values: Mapping[str, int | str]


@dataclass(frozen=True)
class Expect:
    """State the captured frame must be in; every field is checked when set."""

    target: str | None = None
    #: Nothing is the interaction target, so no prompt is drawn.
    untargeted: bool = False
    visited: tuple[str, ...] = ()
    complete: bool = False
    texts: tuple[str | PackageText, ...] = ()
    positions: tuple[tuple[str, int, int], ...] = ()


@dataclass(frozen=True)
class Moment:
    """One snapshot: scripted real input, then a state-checked capture.

    ``steps`` are ``("hold", seconds)``, ``("walk_to", x, y)`` (walk with real
    input until there), ``("tap", direction)`` (one frame of that arrow key,
    which turns the player), and ``("press",)`` (one ``E`` frame). Holds only
    let cosmetic animation settle; :class:`Expect` decides whether the moment
    was reached.
    """

    name: str
    kind: str
    slug: str
    steps: tuple[tuple[object, ...], ...]
    expect: Expect
    fixture: Fixture | None = None


@dataclass(frozen=True)
class Session:
    session: str
    mission_id: str
    player: str
    presentation: str
    #: Scene entities every moment must show on screen (in trusted art when the
    #: presentation has art for them).
    must_show: tuple[str, ...]
    #: Entities, and their art, that must not appear: later sessions' content.
    must_not_show: tuple[str, ...]
    moments: tuple[Moment, ...]
    #: Why this session is not captured yet; it is never published while set.
    deferred: str | None = None

    @property
    def hero(self) -> Moment:
        return next(moment for moment in self.moments if moment.kind == HERO)

    @property
    def command(self) -> str:
        return capture_command(self.session)


#: Where Nova stands on arrival (S01): a few paces onto the Landing Site beside
#: Pixel, out of Pixel's interaction range; beside the Moon Compass (S02/S03);
#: and beside the Guide (S04).
AT_LANDING_SITE: Final = ("walk_to", 340, 262)
BESIDE_COMPASS: Final = ("walk_to", 250, 230)
BESIDE_GUIDE: Final = ("walk_to", 455, 262)

SESSIONS: Final[tuple[Session, ...]] = (
    Session(
        session="S01",
        mission_id="visit-all-classroom-objects",
        player=NOVA,
        presentation=MOON_MEADOW,
        # The arrival cast, each in trusted art, in Moon Meadow; never the
        # retired Fern / River Fountain cast or a later session's content.
        must_show=(NOVA, PIXEL, LANTERN),
        must_not_show=(S02_COMPASS, S03_COMPASS, GUIDE, FERN, FOUNTAIN),
        moments=(
            # The learning world, not completion: Nova facing the camera beside
            # Pixel, the Lantern shrine and the empty stone circle in view, and
            # no prompt, nothing visited.
            Moment(
                name="S01_ARRIVAL",
                kind=HERO,
                slug="hero",
                steps=(("hold", 0.3), AT_LANDING_SITE, ("tap", "down"), ("hold", 2.0)),
                expect=Expect(untargeted=True, positions=((NOVA, 342, 265),)),
            ),
        ),
    ),
    Session(
        session="S02",
        mission_id="create-a-classroom-object",
        player=NOVA,
        presentation=MOON_MEADOW,
        must_show=(NOVA, PIXEL, S02_COMPASS, LANTERN),
        must_not_show=(S03_COMPASS, GUIDE),
        moments=(
            Moment(
                name="S02_COMPASS_PROMPT",
                kind=HERO,
                slug="hero",
                steps=(("hold", 0.3), BESIDE_COMPASS, ("hold", 0.4)),
                expect=Expect(
                    target=S02_COMPASS,
                    texts=(PackageText(S02_PACKAGE, "objects/compass.yaml", "name", "Inspect "),),
                ),
            ),
            Moment(
                name="S02_MOVED_COMPASS",
                kind=LEARNING_MOMENT,
                slug="moved-compass",
                fixture=Fixture(S02_PACKAGE, "objects/compass.yaml", {"x": 690, "y": 360}),
                steps=(("hold", 1.0),),
                expect=Expect(positions=((S02_COMPASS, 690, 360),)),
            ),
        ),
    ),
    Session(
        session="S03",
        mission_id="make-your-object-respond",
        player=NOVA,
        presentation=MOON_MEADOW,
        must_show=(NOVA, S03_COMPASS),
        must_not_show=(PIXEL, LANTERN, S02_COMPASS, GUIDE),
        moments=(
            Moment(
                name="S03_REVEAL",
                kind=HERO,
                slug="hero",
                steps=(BESIDE_COMPASS, ("hold", 0.4), ("press",), ("hold", 0.35)),
                expect=Expect(
                    target=S03_COMPASS,
                    visited=(S03_COMPASS,),
                    complete=True,
                    texts=(PackageText(S03_PACKAGE, "objects/compass.yaml", "when_interacted"),),
                ),
            ),
            Moment(
                name="S03_NEAR_CLUE",
                kind=LEARNING_MOMENT,
                slug="near-clue",
                steps=(BESIDE_COMPASS, ("hold", 0.4)),
                expect=Expect(
                    target=S03_COMPASS,
                    texts=(
                        PackageText(S03_PACKAGE, "objects/compass.yaml", "when_near"),
                        PackageText(S03_PACKAGE, "objects/compass.yaml", "name", "Inspect "),
                    ),
                ),
            ),
        ),
    ),
    Session(
        session="S04",
        mission_id="introduce-your-character",
        player=NOVA,
        presentation=MOON_MEADOW,
        must_show=(NOVA, LANTERN, GUIDE),
        must_not_show=(PIXEL, S02_COMPASS, S03_COMPASS),
        moments=(
            Moment(
                name="S04_DIALOGUE",
                kind=HERO,
                slug="hero",
                steps=(("hold", 0.3), BESIDE_GUIDE, ("hold", 0.5), ("press",), ("hold", 0.6)),
                expect=Expect(
                    target=GUIDE,
                    complete=True,
                    texts=(
                        PackageText(S04_PACKAGE, "character/guide.yaml", "name"),
                        PackageText(S04_PACKAGE, "character/guide.yaml", "greeting", joined=True),
                    ),
                ),
            ),
        ),
    ),
)

SESSIONS_BY_ID: Final[Mapping[str, Session]] = {row.session: row for row in SESSIONS}


def capture_command(session: str) -> str:
    return f"python {CAPTURE_SCRIPT} --session {session}"


def image_path(session: str, slug: str, width: int) -> str:
    """The published path under ``public/``, also the site URL path."""
    suffix = "" if width == CANONICAL_SIZE[0] else f"-{width}"
    return f"journey/{session.lower()}/{slug}{suffix}.webp"


def describe(value: object) -> object:
    """A JSON-ready, order-stable description of table data."""
    if isinstance(value, tuple | list):
        return [describe(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): describe(item) for key, item in sorted(value.items())}
    if hasattr(value, "__dataclass_fields__"):
        return {"type": type(value).__name__, **describe(asdict(value))}  # type: ignore[arg-type]
    return value


# ---------------------------------------------------------------------------
# Canonical sources: task cards, the calendar, the runtime pin
# ---------------------------------------------------------------------------


def published_sessions() -> tuple[str, ...]:
    """Sessions the website publishes (``sessionsWithSlides`` in ``calendar.ts``)."""
    text = CALENDAR.read_text(encoding="utf-8")
    match = re.search(r"sessionsWithSlides[^=]*=\s*\[([^\]]*)\]", text)
    assert match, f"{CALENDAR}: sessionsWithSlides not found"
    return tuple(re.findall(r'"(S\d\d)"', match.group(1)))


def calendar_sessions() -> tuple[str, ...]:
    text = CALENDAR.read_text(encoding="utf-8")
    return tuple(re.findall(r'\{ id: "(S\d\d)"', text))


class TaskCardError(ValueError):
    """A task card's ``explore-package trail`` command is malformed or ambiguous."""


#: The single-value options of ``explore-package trail`` (``explore/packages/cli.py``).
#: ``--player`` and ``--mission-id`` decide what a snapshot shows; ``--name`` is
#: the window title. Each may appear once.
TRAIL_OPTIONS: Final = ("--player", "--mission-id", "--name")
#: Options a canonical (snapshot) command must state.
REQUIRED_TRAIL_OPTIONS: Final = ("--player", "--mission-id")


@dataclass(frozen=True)
class TrailCommand:
    packages: tuple[str, ...]
    options: Mapping[str, str] = field(default_factory=dict)

    @property
    def mission_id(self) -> str:
        return self.options["--mission-id"]

    @property
    def player(self) -> str:
        return self.options["--player"]


def task_card(session: str) -> Path:
    return SESSIONS_DIR / session.lower() / "student" / "task-card.md"


def _card_label(card: Path, session: str | None) -> str:
    if session is None and card.name == "task-card.md":
        session = card.parent.parent.name.upper()
    try:
        shown = card.relative_to(REPO).as_posix()
    except ValueError:
        shown = str(card)
    return f"{session or 'task card'} ({shown})"


def parse_trail_command(line: str, *, where: str = "task card") -> TrailCommand:
    """One ``explore-package trail ...`` line, rejecting anything ambiguous.

    Fails on unbalanced quotes, unknown options, an option without a value, any
    repeated option, a repeated package, and a command with no packages.
    """

    def fail(problem: str) -> TaskCardError:
        return TaskCardError(f"{where}: `explore-package trail` command {problem}")

    try:
        tokens = shlex.split(line)
    except ValueError as error:
        raise fail(f"cannot be parsed: {error}") from None
    if tokens[:2] != ["explore-package", "trail"]:
        raise fail("does not start with `explore-package trail`")
    packages: list[str] = []
    options: dict[str, str] = {}
    rest = tokens[2:]
    index = 0
    while index < len(rest):
        token = rest[index]
        index += 1
        if not token.startswith("-"):
            if token in packages:
                raise fail(f"names package {token} twice")
            packages.append(token)
            continue
        flag, equals, value = token.partition("=")
        if flag not in TRAIL_OPTIONS:
            raise fail(f"has unknown option {flag}")
        if flag in options:
            raise fail(f"repeats {flag}")
        if not equals:
            if index == len(rest) or rest[index].startswith("--"):
                raise fail(f"is missing a value for {flag}")
            value = rest[index]
            index += 1
        if not value.strip():
            raise fail(f"has an empty value for {flag}")
        options[flag] = value
    if not packages:
        raise fail("names no packages")
    return TrailCommand(tuple(packages), options)


def trail_commands(card: Path, *, session: str | None = None) -> list[TrailCommand]:
    """Each ``explore-package trail`` command on a task card, strictly parsed."""
    where = _card_label(card, session)
    joined = re.sub(r"\\\r?\n", " ", card.read_text(encoding="utf-8"))
    return [
        parse_trail_command(line.strip(), where=where)
        for line in joined.splitlines()
        if line.strip().startswith("explore-package trail")
    ]


def canonical_command(session: str) -> TrailCommand | None:
    """The session's one canonical Trail command (the one naming a mission)."""
    card = task_card(session)
    if not card.is_file():
        return None
    commands = [
        command
        for command in trail_commands(card, session=session)
        if "--mission-id" in command.options
    ]
    if not commands:
        return None
    if len(commands) != 1:
        raise TaskCardError(
            f"{_card_label(card, session)}: {len(commands)} `explore-package trail` "
            "commands name --mission-id; expected one canonical command"
        )
    missing = [flag for flag in REQUIRED_TRAIL_OPTIONS if flag not in commands[0].options]
    if missing:
        raise TaskCardError(
            f"{_card_label(card, session)}: the canonical `explore-package trail` command "
            f"has no {', '.join(missing)}"
        )
    return commands[0]


def student_copy_seeds() -> Mapping[str, Path]:
    """Student Workspace paths on task cards -> the Course Kit seed they start from."""
    from scripts.make_my_world import S02_PACKAGE_SEED, STUDENT_S02_PACKAGE, WORKSPACE_NAME

    return {(Path("..", WORKSPACE_NAME) / STUDENT_S02_PACKAGE).as_posix(): REPO / S02_PACKAGE_SEED}


def package_root(argument: str) -> Path:
    seeds = student_copy_seeds()
    if argument in seeds:
        return seeds[argument]
    path = Path(argument)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{argument} is outside the Course Kit and has no known seed")
    return REPO / path


def runtime_pin() -> str:
    """The commit the Course Kit installs the runtime from."""
    from scripts.provision_student_workspace import COURSE_PLATFORM_COMMIT

    return COURSE_PLATFORM_COMMIT


# ---------------------------------------------------------------------------
# Presentation fingerprint
# ---------------------------------------------------------------------------


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(entries: Iterable[tuple[str, str]]) -> str:
    lines = "".join(f"{path}\0{digest}\n" for path, digest in sorted(entries))
    return _sha256(lines.encode("utf-8"))


def _is_runtime_file(path: str) -> bool:
    parts = Path(path).parts
    return "__pycache__" not in parts and Path(path).suffix in _RUNTIME_SUFFIXES


def runtime_files(root: Path = REPO) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for entry in RUNTIME_INPUTS:
        path = root / entry
        candidates = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        for candidate in candidates:
            relative = candidate.relative_to(root).as_posix()
            if _is_runtime_file(relative):
                files[relative] = candidate.read_bytes()
    return files


def runtime_files_at(commit: str, root: Path = REPO) -> dict[str, bytes]:
    """The :data:`RUNTIME_INPUTS` files as committed at *commit* (needs git history)."""
    listing = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--name-only", commit, "--", *RUNTIME_INPUTS],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    names = [name for name in listing.split("\0") if name and _is_runtime_file(name)]
    request = "".join(f"{commit}:{name}\n" for name in names).encode("utf-8")
    output = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=root, input=request, check=True, capture_output=True
    ).stdout
    files: dict[str, bytes] = {}
    cursor = 0
    for name in names:
        header_end = output.index(b"\n", cursor)
        size = int(output[cursor:header_end].split()[2])
        files[name] = output[header_end + 1 : header_end + 1 + size]
        cursor = header_end + 1 + size + 1
    return files


def runtime_digest(files: Mapping[str, bytes] | None = None) -> str:
    files = runtime_files() if files is None else files
    return _digest((path, _sha256(data)) for path, data in files.items())


def capture_implementation_digest(root: Path = REPO) -> str:
    """The harness source (:data:`CAPTURE_IMPLEMENTATION_INPUTS`), byte for byte."""
    return _digest(
        (path, _sha256((root / path).read_bytes())) for path in CAPTURE_IMPLEMENTATION_INPUTS
    )


def packages_digest(packages: Iterable[str]) -> str:
    """Every file of every package, keyed by the task-card argument it came from."""
    entries = []
    for argument in packages:
        root = package_root(argument)
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            relative = path.relative_to(root)
            if "__pycache__" in relative.parts or relative.name.startswith("."):
                continue
            entries.append((f"{argument}/{relative.as_posix()}", _sha256(path.read_bytes())))
    return _digest(entries)


def capture_recipe(row: Session, moment: Moment, command: TrailCommand) -> dict[str, object]:
    return {
        "session": row.session,
        "missionId": command.mission_id,
        "player": command.player,
        "packages": list(command.packages),
        "presentation": row.presentation,
        "mustShow": list(row.must_show),
        "mustNotShow": list(row.must_not_show),
        "moment": describe(moment),
        "canonicalSize": list(CANONICAL_SIZE),
        "widths": list(WIDTHS),
        "webp": describe(WEBP_SETTINGS),
    }


def capture_recipe_digest(row: Session, moment: Moment, command: TrailCommand) -> str:
    return _sha256(json.dumps(capture_recipe(row, moment, command), sort_keys=True).encode())


def fingerprint_parts(
    row: Session,
    moment: Moment,
    command: TrailCommand,
    runtime: str | None = None,
    implementation: str | None = None,
) -> dict[str, str]:
    """The four :data:`FINGERPRINT_PARTS`, computed from the working tree."""
    return {
        "runtime": runtime_digest() if runtime is None else runtime,
        "packages": packages_digest(command.packages),
        "captureRecipe": capture_recipe_digest(row, moment, command),
        "captureImplementation": (
            capture_implementation_digest() if implementation is None else implementation
        ),
    }


def presentation_fingerprint(parts: Mapping[str, str]) -> str:
    joined = "\n".join(f"{key}={parts[key]}" for key in FINGERPRINT_PARTS)
    return "sha256:" + _sha256(joined.encode("utf-8"))


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, object]:
    if not path.is_file():
        return {"schema": SCHEMA, "snapshots": []}
    return json.loads(path.read_text(encoding="utf-8"))


def schema_problem(manifest: Mapping[str, object]) -> str | None:
    """Why this code cannot check *manifest*, or ``None`` if its schema is supported."""
    schema = manifest.get("schema")
    if schema is None:
        return f"{MANIFEST_PATH.name} has no schema; expected {SCHEMA}"
    if not isinstance(schema, str) or not re.fullmatch(rf"{re.escape(SCHEMA_NAME)}@\d+", schema):
        return f"{MANIFEST_PATH.name} has unknown schema {schema!r}; expected {SCHEMA}"
    if schema not in SUPPORTED_SCHEMAS:
        return (
            f"{MANIFEST_PATH.name} has unsupported schema version {schema!r}; expected {SCHEMA}. "
            "Recapture with `python scripts/capture_journey_snapshots.py --all-published`"
        )
    return None


def fingerprint_inputs() -> dict[str, object]:
    """What each fingerprint part hashes, recorded in the manifest for auditors."""
    return {
        "runtime": {group: list(paths) for group, paths in RUNTIME_GROUPS.items()},
        "runtimePixelInert": dict(RUNTIME_PIXEL_INERT),
        "packages": "every file of each task-card package (a Student Workspace copy "
        "resolves to its Course Kit seed)",
        "captureRecipe": list(CAPTURE_RECIPE_FIELDS),
        "captureImplementation": list(CAPTURE_IMPLEMENTATION_INPUTS),
    }


def manifest_header() -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "canonicalFrame": {"width": CANONICAL_SIZE[0], "height": CANONICAL_SIZE[1]},
        "widths": list(WIDTHS),
        "webp": dict(WEBP_SETTINGS),
        "hashPolicy": (
            "sourceRgbSha256 (the raw 960x640 RGB frame) is authoritative for regeneration "
            "on the recorded toolchain; image sha256 values verify the committed files. "
            "WebP and font rasterization bytes are not promised across toolchains."
        ),
        "fingerprintParts": list(FINGERPRINT_PARTS),
        "fingerprintInputs": fingerprint_inputs(),
        "deferred": [
            {
                "session": row.session,
                "moment": row.hero.name,
                "kind": HERO,
                "reason": row.deferred,
                "captureCommand": row.command,
            }
            for row in SESSIONS
            if row.deferred
        ],
    }


def write_manifest(snapshots: list[dict[str, object]], path: Path = MANIFEST_PATH) -> None:
    order = {
        (row.session, moment.name): (row_index, moment_index)
        for row_index, row in enumerate(SESSIONS)
        for moment_index, moment in enumerate(row.moments)
    }
    ordered = sorted(snapshots, key=lambda entry: order[(entry["session"], entry["moment"])])  # type: ignore[index]
    document = {**manifest_header(), "snapshots": ordered}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def publication_problems(manifest: Mapping[str, object]) -> list[str]:
    """Manifest entries and public files that must not be published, without capturing."""
    problem = schema_problem(manifest)
    if problem:
        return [problem]
    problems = []
    published = published_sessions()
    seen: set[tuple[str, str]] = set()
    listed: set[Path] = set()
    for entry in manifest.get("snapshots", []):  # type: ignore[union-attr]
        session, name = entry.get("session"), entry.get("moment")
        row = SESSIONS_BY_ID.get(session)
        if session not in published:
            problems.append(f"manifest entry {session} {name}: {session} is not published")
        elif row is None:
            problems.append(f"manifest entry {session} {name}: {session} has no snapshot row")
        elif row.deferred:
            problems.append(f"manifest entry {session} {name}: {session} is deferred")
        elif name not in {moment.name for moment in row.moments}:
            problems.append(f"manifest entry {session} {name}: no such moment in the table")
        if (session, name) in seen:
            problems.append(f"manifest entry {session} {name} is listed twice")
        seen.add((session, name))
        for image in entry.get("images", {}).values():
            listed.add(WEBSITE / "public" / image["src"].lstrip("/"))
    if PUBLIC_JOURNEY.exists():
        for path in sorted(p for p in PUBLIC_JOURNEY.rglob("*") if p.is_file()):
            if path not in listed:
                shown = path.relative_to(REPO).as_posix()
                problems.append(f"{shown} is published but not in the manifest")
    return problems


def stale_reason(
    entry: Mapping[str, object], runtime: str | None = None, implementation: str | None = None
) -> str | None:
    """Why a manifest entry no longer matches its inputs, or ``None`` if fresh."""
    row = SESSIONS_BY_ID[entry["session"]]  # type: ignore[index]
    moment = next(m for m in row.moments if m.name == entry["moment"])
    command = canonical_command(row.session)
    assert command is not None
    parts = fingerprint_parts(row, moment, command, runtime, implementation)
    if presentation_fingerprint(parts) == entry["presentationFingerprint"]:
        return None
    recorded = entry.get("fingerprintParts", {})
    changed = [key for key in FINGERPRINT_PARTS if recorded.get(key) != parts[key]]  # type: ignore[union-attr]
    return (
        f"Journey snapshot for {row.session} ({moment.name}) is stale: "
        f"{', '.join(FINGERPRINT_PARTS[key] for key in changed) or 'fingerprint'} changed; "
        f"rerun `{row.command}`"
    )
