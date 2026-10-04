"""Stale Journey snapshots cannot pass, and task-card commands cannot be ambiguous.

The mutation tests copy the files ``--check`` reads into a temporary mirror of
the repository, make one real change there, and run the standalone
``python scripts/capture_journey_snapshots.py --check`` against the mirror. The
real repository is never modified. A change that can alter a captured frame
must make the check fail; audio-only code, website prose, and docs must not.
The runtime pin guard that gates publishing is checked the same way.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts import journey_snapshots as journey
from scripts.journey_snapshots import TaskCardError, parse_trail_command, trail_commands

REPO = journey.REPO
MIRRORED = (
    "engine",
    "explore",
    "scripts",
    "examples/explorer-packages",
    "lessons/sessions",
    "course4teen-website/lib",
    "course4teen-website/journey",
    "course4teen-website/public/journey",
    # Unrelated files, mirrored so the tests can show they do not matter.
    "course4teen-website/app/students/slides/s02/page.tsx",
    "docs/journey-proof/snapshots/README.md",
)


# ---------------------------------------------------------------------------
# A mirror of the repository to mutate
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def pristine(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("pristine")
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
    for entry in MIRRORED:
        source, target = REPO / entry, root / entry
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, ignore=ignore)
        else:
            shutil.copy2(source, target)
    return root


@pytest.fixture
def mirror(pristine: Path, tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    shutil.copytree(pristine, root)
    return root


def _check(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(root / "scripts" / "capture_journey_snapshots.py"), "--check"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _mutate(root: Path, path: str, old: str, new: str) -> None:
    """Replace the first *old* in *path*; fail loudly if the target moved."""
    file = root / path
    text = file.read_text(encoding="utf-8")
    assert old in text, f"mutation target {old!r} is no longer in {path}"
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_the_unmutated_mirror_is_fresh(mirror: Path) -> None:
    result = _check(mirror)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Journey snapshots are fresh." in result.stdout


# ---------------------------------------------------------------------------
# Changes that can alter a captured frame make every affected snapshot stale
# ---------------------------------------------------------------------------

#: (id, path, old, new, fingerprint part the failure must name)
STALE_MUTATIONS = (
    # 1. Engine rendering: the default line width.
    ("rendering", "engine/rendering/_renderer.py", "width: int = 1,", "width: int = 2,", "runtime"),
    # 2. Presentation policy: a mission's Lantern waypoint.
    (
        "presentation-policy",
        "engine/rendering/_mission_presentation.py",
        "lantern_waypoint=True,",
        "lantern_waypoint=False,",
        "runtime",
    ),
    # 3. Registration adapter: a character drawn one pixel to the right.
    (
        "registration-adapter-x",
        "explore/packages/registration_adapter.py",
        "            x=contribution.x,\n            y=contribution.y,",
        "            x=contribution.x + 1,\n            y=contribution.y,",
        "runtime",
    ),
    (
        "registration-adapter-y",
        "explore/packages/registration_adapter.py",
        "            x=contribution.x,\n            y=contribution.y,",
        "            x=contribution.x,\n            y=contribution.y + 1,",
        "runtime",
    ),
    # 4. The package loader / models / planner / Trail construction path.
    (
        "package-set-planner",
        "explore/packages/package_set_planner.py",
        "x=specification.x,",
        "x=specification.x + 1,",
        "runtime",
    ),
    (
        "package-loader",
        "explore/packages/loader.py",
        "def load_explorer_package(",
        "def load_explorer_package(  # mutated\n",
        "runtime",
    ),
    (
        "registration-models",
        "explore/packages/registration_models.py",
        "    x: int\n",
        "    x: int  # mutated\n",
        "runtime",
    ),
    (
        "trail-construction",
        "explore/packages/classroom_trail.py",
        "x=player.x,",
        "x=player.x + 1,",
        "runtime",
    ),
    # 5. Colours.
    ("colors", "explore/_colors.py", '"gold": (255, 200, 50)', '"gold": (255, 201, 50)', "runtime"),
    # The audio bridge draws the audio indicator on the Trail frame.
    (
        "audio-indicator",
        "engine/audio/_trail_audio.py",
        "def draw_indicator(self, renderer: object) -> None:",
        "def draw_indicator(self, renderer: object) -> None:  # mutated",
        "runtime",
    ),
    # 6. Canonical package YAML: geometry and text.
    (
        "package-yaml-geometry",
        "lessons/sessions/s03/student/explorer-package/objects/compass.yaml",
        "\nx: ",
        "\nx: 1",
        "packages",
    ),
    (
        "package-yaml-text",
        "lessons/sessions/s04/student/explorer-package/character/guide.yaml",
        "greeting: ",
        "greeting: Hi. ",
        "packages",
    ),
    (
        "example-package-yaml",
        "examples/explorer-packages/nova-character/character/nova.yaml",
        "\nx: ",
        "\nx: 1",
        "packages",
    ),
    # 7. The fixed time step, and frame selection while walking and holding.
    ("fixed-timestep", "scripts/trail_driver.py", "STEP = 1 / 60", "STEP = 1 / 59", "harness"),
    (
        "walk-arrival-tolerance",
        "scripts/trail_driver.py",
        "if abs(dx) < 3 and abs(dy) < 3:",
        "if abs(dx) < 4 and abs(dy) < 4:",
        "harness",
    ),
    (
        "hold-frame-count",
        "scripts/trail_driver.py",
        "range(round(seconds / STEP))",
        "range(int(seconds / STEP))",
        "harness",
    ),
    # 8. Capture acceptance.
    (
        "acceptance-check",
        "scripts/capture_journey_snapshots.py",
        "if _normalize(text) not in joined:",
        "if False and _normalize(text) not in joined:",
        "harness",
    ),
    # 9. Session capture config: where Nova stands for the S02/S03 moments,
    # and where she arrives for S01.
    (
        "session-capture-config",
        "scripts/journey_snapshots.py",
        'BESIDE_COMPASS: Final = ("walk_to", 250, 230)',
        'BESIDE_COMPASS: Final = ("walk_to", 251, 230)',
        "recipe",
    ),
    (
        "s01-arrival-config",
        "scripts/journey_snapshots.py",
        'AT_LANDING_SITE: Final = ("walk_to", 340, 262)',
        'AT_LANDING_SITE: Final = ("walk_to", 341, 262)',
        "recipe",
    ),
    # The task-card command itself: package order changes draw order.
    (
        "task-card-package-order",
        "lessons/sessions/s04/student/task-card.md",
        "     examples/explorer-packages/nova-character \\\n"
        "     examples/explorer-packages/crystal-lantern \\\n",
        "     examples/explorer-packages/crystal-lantern \\\n"
        "     examples/explorer-packages/nova-character \\\n",
        "recipe",
    ),
)

PART_LABELS = {
    "runtime": journey.FINGERPRINT_PARTS["runtime"],
    "packages": journey.FINGERPRINT_PARTS["packages"],
    "recipe": journey.FINGERPRINT_PARTS["captureRecipe"],
    "harness": journey.FINGERPRINT_PARTS["captureImplementation"],
}


@pytest.mark.parametrize(
    ("path", "old", "new", "part"),
    [mutation[1:] for mutation in STALE_MUTATIONS],
    ids=[mutation[0] for mutation in STALE_MUTATIONS],
)
def test_a_frame_changing_edit_makes_the_check_fail(
    mirror: Path, path: str, old: str, new: str, part: str
) -> None:
    _mutate(mirror, path, old, new)
    result = _check(mirror)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "is stale" in result.stdout
    assert PART_LABELS[part] in result.stdout, result.stdout
    assert "rerun `python scripts/capture_journey_snapshots.py --session S0" in result.stdout


@pytest.mark.parametrize(
    ("path", "sessions"),
    [
        ("lessons/sessions/s04/student/explorer-package/character/guide.yaml", {"S04"}),
        ("examples/explorer-packages/pixel-companion/character/pixel.yaml", {"S01", "S02"}),
    ],
    ids=["s04-guide", "pixel"],
)
def test_a_package_edit_stales_only_the_sessions_that_use_it(
    mirror: Path, path: str, sessions: set[str]
) -> None:
    _mutate(mirror, path, "\nx: ", "\nx: 1")
    result = _check(mirror)
    assert result.returncode == 1
    stale = {line.split()[3] for line in result.stdout.splitlines() if "is stale" in line}
    assert stale == sessions, result.stdout


# ---------------------------------------------------------------------------
# Changes that cannot alter a frame leave the snapshots fresh
# ---------------------------------------------------------------------------

FRESH_MUTATIONS: tuple[tuple[str, Callable[[Path], None]], ...] = (
    # 10. Audio-only implementation and clips.
    (
        "audio-manager",
        lambda root: _mutate(
            root, "engine/audio/_manager.py", "class AudioManager", "# mutated\nclass AudioManager"
        ),
    ),
    (
        "audio-cues",
        lambda root: _mutate(
            root,
            "engine/audio/_cues.py",
            '"""',
            '"""Mutated. ',
        ),
    ),
    (
        "trusted-audio-loader",
        lambda root: _mutate(root, "engine/assets/_trusted_audio.py", '"""', '"""Mutated. '),
    ),
    (
        "trusted-audio-clip",
        lambda root: next((root / "engine/assets/trusted_audio").rglob("*.wav")).write_bytes(
            b"RIFF"
        ),
    ),
    # 11. Unrelated website prose.
    (
        "website-prose",
        lambda root: _mutate(
            root, "course4teen-website/app/students/slides/s02/page.tsx", "Compass", "Kompass"
        ),
    ),
    # 12. Unrelated docs, and the prose around a task card's command.
    (
        "docs",
        lambda root: _mutate(root, "docs/journey-proof/snapshots/README.md", "S02", "S2"),
    ),
    (
        "task-card-prose",
        lambda root: _mutate(root, "lessons/sessions/s03/student/task-card.md", "\n", "\nNote.\n"),
    ),
    (
        "task-card-window-title",
        lambda root: _mutate(
            root, "lessons/sessions/s03/student/task-card.md", '--name "S03 ', '--name "My S03 '
        ),
    ),
)


@pytest.mark.parametrize(
    "mutation", [m[1] for m in FRESH_MUTATIONS], ids=[m[0] for m in FRESH_MUTATIONS]
)
def test_a_pixel_inert_edit_keeps_the_check_passing(
    mirror: Path, mutation: Callable[[Path], None]
) -> None:
    mutation(mirror)
    result = _check(mirror)
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# The publication boundary and the manifest schema fail closed
# ---------------------------------------------------------------------------


def _edit_manifest(root: Path, edit: Callable[[dict], None]) -> None:  # type: ignore[type-arg]
    path = root / journey.MANIFEST_PATH.relative_to(REPO)
    document = json.loads(path.read_text(encoding="utf-8"))
    edit(document)
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")


def _copy_entry_as(session: str) -> Callable[[dict], None]:  # type: ignore[type-arg]
    def edit(document: dict) -> None:  # type: ignore[type-arg]
        entry = json.loads(json.dumps(document["snapshots"][-1]))
        entry["session"] = session
        document["snapshots"].append(entry)

    return edit


BOUNDARY_MUTATIONS: tuple[tuple[str, Callable[[Path], None], str], ...] = (
    # 13. A stray asset for a session the website does not publish.
    (
        "stray-s05-asset",
        lambda root: (
            (root / "course4teen-website/public/journey/s05").mkdir(),
            (root / "course4teen-website/public/journey/s05/hero.webp").write_bytes(b"RIFF"),
        ),
        "public/journey/s05/hero.webp is published but not in the manifest",
    ),
    (
        "stray-s01-asset",
        lambda root: (root / "course4teen-website/public/journey/s01/arrival.webp").write_bytes(
            b"RIFF"
        ),
        "public/journey/s01/arrival.webp is published but not in the manifest",
    ),
    # 14. Manifest entries for an unpublished session, a deferred session, or
    # a moment the table does not have.
    (
        "unpublished-session-entry",
        lambda root: _edit_manifest(root, _copy_entry_as("S05")),
        "S05 is not published",
    ),
    (
        "deferred-session-entry",
        lambda root: _mutate(
            root,
            "scripts/journey_snapshots.py",
            '        mission_id="introduce-your-character",\n',
            '        mission_id="introduce-your-character",\n        deferred="waiting",\n',
        ),
        "S04 is deferred",
    ),
    (
        "unknown-moment-entry",
        lambda root: _edit_manifest(root, _copy_entry_as("S01")),
        "manifest entry S01 S04_DIALOGUE: no such moment in the table",
    ),
    (
        "duplicate-entry",
        lambda root: _edit_manifest(root, _copy_entry_as("S04")),
        "is listed twice",
    ),
    # 15. Unsupported, unknown, and missing manifest schemas.
    (
        "schema-version-1",
        lambda root: _edit_manifest(
            root, lambda d: d.update(schema="explore-studio/journey-snapshots@1")
        ),
        "unsupported schema version 'explore-studio/journey-snapshots@1'",
    ),
    (
        "schema-version-3",
        lambda root: _edit_manifest(
            root, lambda d: d.update(schema="explore-studio/journey-snapshots@3")
        ),
        "unsupported schema version",
    ),
    (
        "schema-unknown",
        lambda root: _edit_manifest(root, lambda d: d.update(schema="someone-else/snapshots@2")),
        "unknown schema 'someone-else/snapshots@2'",
    ),
    (
        "schema-missing",
        lambda root: _edit_manifest(root, lambda d: d.pop("schema")),
        "has no schema",
    ),
)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [m[1:] for m in BOUNDARY_MUTATIONS],
    ids=[m[0] for m in BOUNDARY_MUTATIONS],
)
def test_the_check_refuses_anything_outside_the_publication_boundary(
    mirror: Path, mutation: Callable[[Path], None], message: str
) -> None:
    mutation(mirror)
    result = _check(mirror)
    assert result.returncode == 1, result.stdout + result.stderr
    assert message in result.stdout, result.stdout
    assert "Traceback" not in result.stderr, result.stderr


def test_publish_will_not_relabel_entries_from_an_older_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import capture_journey_snapshots as harness

    old = {**journey.load_manifest(), "schema": "explore-studio/journey-snapshots@1"}
    monkeypatch.setattr(journey, "load_manifest", lambda path=journey.MANIFEST_PATH: old)
    monkeypatch.setattr(harness, "require_pinned_runtime", lambda root=REPO: ("pin", "runtime"))
    monkeypatch.setattr(harness, "toolchain", lambda: {})
    with pytest.raises(harness.CaptureError, match="unsupported schema version.*S03, S04"):
        harness.publish(["S02"])


# ---------------------------------------------------------------------------
# Publishing refuses a runtime that draws differently from the Course Kit pin
# ---------------------------------------------------------------------------


def _pin_history_available() -> bool:
    try:
        journey.runtime_files_at(journey.runtime_pin())
    except (OSError, subprocess.CalledProcessError):
        return False
    return True


needs_pin = pytest.mark.skipif(
    not _pin_history_available(), reason="git history for the runtime pin is not available"
)

PIN_BLOCKING = [m for m in STALE_MUTATIONS if m[4] == "runtime"]


@needs_pin
def test_the_unmutated_runtime_is_the_pinned_runtime(mirror: Path) -> None:
    from scripts.capture_journey_snapshots import require_pinned_runtime

    pin, digest = require_pinned_runtime(mirror)
    assert pin == journey.runtime_pin()
    assert digest == journey.runtime_digest()


@needs_pin
@pytest.mark.parametrize(
    ("path", "old", "new"),
    [mutation[1:4] for mutation in PIN_BLOCKING],
    ids=[mutation[0] for mutation in PIN_BLOCKING],
)
def test_a_runtime_change_blocks_publishing(mirror: Path, path: str, old: str, new: str) -> None:
    from scripts.capture_journey_snapshots import CaptureError, require_pinned_runtime

    _mutate(mirror, path, old, new)
    with pytest.raises(CaptureError, match="differs from the Course Kit runtime pin"):
        require_pinned_runtime(mirror)


@needs_pin
@pytest.mark.parametrize(
    "mutation", [m[1] for m in FRESH_MUTATIONS], ids=[m[0] for m in FRESH_MUTATIONS]
)
def test_a_pixel_inert_change_does_not_block_publishing(
    mirror: Path, mutation: Callable[[Path], None]
) -> None:
    from scripts.capture_journey_snapshots import require_pinned_runtime

    mutation(mirror)
    require_pinned_runtime(mirror)


# ---------------------------------------------------------------------------
# Task-card commands: strict, fail-closed parsing
# ---------------------------------------------------------------------------

CANONICAL = {
    "S01": (
        (
            "examples/explorer-packages/nova-character",
            "examples/explorer-packages/pixel-companion",
            "examples/explorer-packages/crystal-lantern",
        ),
        "visit-all-classroom-objects",
    ),
    "S02": (
        (
            "examples/explorer-packages/nova-character",
            "examples/explorer-packages/pixel-companion",
            "examples/explorer-packages/crystal-lantern",
            "../my-explore-world/projects/moon-compass",
        ),
        "create-a-classroom-object",
    ),
    "S03": (
        (
            "examples/explorer-packages/nova-character",
            "lessons/sessions/s03/student/explorer-package",
        ),
        "make-your-object-respond",
    ),
    "S04": (
        (
            "examples/explorer-packages/nova-character",
            "examples/explorer-packages/crystal-lantern",
            "lessons/sessions/s04/student/explorer-package",
        ),
        "introduce-your-character",
    ),
}


@pytest.mark.parametrize("session", sorted(CANONICAL))
def test_canonical_commands_parse_exactly(session: str) -> None:
    command = journey.canonical_command(session)
    assert command is not None
    packages, mission = CANONICAL[session]
    assert command.packages == packages  # order preserved
    assert command.mission_id == mission
    assert command.player == "nova-character:nova"
    assert command.options["--name"].startswith(f"{session} ")


def test_every_task_card_command_in_the_course_parses() -> None:
    for session in journey.calendar_sessions():
        journey.canonical_command(session)


def _card(tmp_path: Path, command: str, session: str = "S09") -> Path:
    card = tmp_path / "lessons" / "sessions" / session.lower() / "student" / "task-card.md"
    card.parent.mkdir(parents=True)
    card.write_text(f"# {session}\n\n```console\n{command}\n```\n", encoding="utf-8")
    return card


MULTILINE = (
    "explore-package trail \\\n"
    "  examples/explorer-packages/nova-character \\\n"
    "  lessons/sessions/s09/student/explorer-package \\\n"
    '  --player "nova-character:nova" \\\n'
    '  --mission-id "count-object-interactions" \\\n'
    '  --name "S09   Power Up a Device\'s Core"'
)


def test_multiline_command_with_quoted_name_keeps_whitespace_and_order(tmp_path: Path) -> None:
    [command] = trail_commands(_card(tmp_path, MULTILINE))
    assert command.packages == (
        "examples/explorer-packages/nova-character",
        "lessons/sessions/s09/student/explorer-package",
    )
    assert command.player == "nova-character:nova"
    assert command.mission_id == "count-object-interactions"
    assert command.options["--name"] == "S09   Power Up a Device's Core"


def test_windows_line_endings_still_join_continuations(tmp_path: Path) -> None:
    card = _card(tmp_path, MULTILINE)
    card.write_bytes(card.read_bytes().replace(b"\n", b"\r\n"))
    [command] = trail_commands(card)
    assert command.mission_id == "count-object-interactions"


def test_equals_form_is_accepted() -> None:
    command = parse_trail_command("explore-package trail pkg --player=a:b --mission-id=m")
    assert (command.packages, command.player, command.mission_id) == (("pkg",), "a:b", "m")


REJECTED = (
    # 16. Duplicate --player, even with the same value.
    ("duplicate-player", MULTILINE + ' \\\n  --player "pixel-companion:pixel"', "repeats --player"),
    (
        "duplicate-player-same",
        MULTILINE + ' \\\n  --player "nova-character:nova"',
        "repeats --player",
    ),
    ("duplicate-player-equals", MULTILINE + " --player=nova-character:nova", "repeats --player"),
    # 17. Duplicate --mission-id.
    ("duplicate-mission", MULTILINE + " --mission-id other-mission", "repeats --mission-id"),
    ("duplicate-name", MULTILINE + ' --name "Again"', "repeats --name"),
    # 18. Missing values.
    (
        "missing-player-value",
        "explore-package trail pkg --mission-id m --player",
        "is missing a value for --player",
    ),
    (
        "player-followed-by-flag",
        "explore-package trail pkg --player --mission-id m",
        "is missing a value for --player",
    ),
    (
        "missing-mission-value",
        "explore-package trail pkg --player a:b --mission-id",
        "is missing a value for --mission-id",
    ),
    (
        "empty-mission-value",
        'explore-package trail pkg --player a:b --mission-id ""',
        "empty value",
    ),
    ("empty-equals-value", "explore-package trail pkg --player= --mission-id m", "empty value"),
    # Other malformed commands.
    ("unknown-option", "explore-package trail pkg --player a:b --mission-id m --fast", "unknown"),
    ("unbalanced-quote", 'explore-package trail pkg --player "a:b --mission-id m', "cannot be"),
    ("duplicate-package", "explore-package trail pkg pkg --player a:b --mission-id m", "twice"),
    ("no-packages", "explore-package trail --player a:b --mission-id m", "names no packages"),
)


@pytest.mark.parametrize(
    ("command", "message"), [r[1:] for r in REJECTED], ids=[r[0] for r in REJECTED]
)
def test_malformed_commands_fail_closed_naming_session_card_and_flag(
    tmp_path: Path, command: str, message: str
) -> None:
    card = _card(tmp_path, command)
    with pytest.raises(TaskCardError) as raised:
        trail_commands(card)
    error = str(raised.value)
    assert message in error
    assert error.startswith(f"S09 ({card})")
    assert not isinstance(raised.value.__cause__, StopIteration)


def test_canonical_command_requires_player_and_one_mission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(journey, "SESSIONS_DIR", tmp_path / "lessons" / "sessions")
    _card(tmp_path, "explore-package trail pkg --mission-id m", session="S09")
    with pytest.raises(TaskCardError, match=r"S09 .*has no --player"):
        journey.canonical_command("S09")
    _card(
        tmp_path,
        "explore-package trail a --player p:q --mission-id m\n"
        "explore-package trail b --player p:q --mission-id n",
        session="S10",
    )
    with pytest.raises(TaskCardError, match=r"S10 .*2 `explore-package trail` commands"):
        journey.canonical_command("S10")


def test_a_malformed_canonical_command_fails_the_standalone_check(mirror: Path) -> None:
    _mutate(
        mirror,
        "lessons/sessions/s03/student/task-card.md",
        '--player "nova-character:nova"',
        '--player "nova-character:nova" --player "pixel-companion:pixel"',
    )
    result = _check(mirror)
    assert result.returncode == 1
    assert "S03 (lessons/sessions/s03/student/task-card.md)" in result.stdout
    assert "repeats --player" in result.stdout
    assert "Traceback" not in result.stderr
