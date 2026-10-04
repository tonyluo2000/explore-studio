"""The published Journey snapshots: contract, publication boundary, and freshness.

Nothing here captures a frame; ``tests/test_journey_snapshot_determinism.py``
drives the real Trail. These checks keep the committed WebP files and
``course4teen-website/journey/snapshots.json`` honest: every snapshot belongs to
a published session, shows that session's canonical task-card command, carries
no later session's content, and still matches the runtime and packages that
produced it.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from engine.rendering._mission_presentation import mission_presentation
from explore.curriculum import get_course_mission
from scripts import journey_snapshots as journey
from scripts.journey_snapshots import (
    HERO,
    KINDS,
    MAX_OPTIONAL,
    MOON_MEADOW,
    PUBLIC_JOURNEY,
    SESSIONS,
    SESSIONS_BY_ID,
)

MANIFEST = journey.load_manifest()
ENTRIES: list[dict] = MANIFEST["snapshots"]  # type: ignore[assignment,type-arg]
PUBLISHED = journey.published_sessions()
ACTIVE_ROWS = [row for row in SESSIONS if not row.deferred]
S01 = SESSIONS_BY_ID["S01"]


def _entry_id(entry: dict) -> str:  # type: ignore[type-arg]
    return f"{entry['session']}:{entry['moment']}"


def _public_file(src: str) -> Path:
    return journey.WEBSITE / "public" / src.lstrip("/")


def _webp_size(data: bytes) -> tuple[int, int]:
    """Width and height of a simple lossy WebP (RIFF / WEBP / ``VP8 `` keyframe)."""
    assert data[:4] == b"RIFF" and data[8:12] == b"WEBP", "not a WebP file"
    assert data[12:16] == b"VP8 ", f"expected a plain lossy VP8 chunk, got {data[12:16]!r}"
    assert data[23:26] == b"\x9d\x01\x2a", "missing VP8 keyframe start code"
    width = int.from_bytes(data[26:28], "little") & 0x3FFF
    height = int.from_bytes(data[28:30], "little") & 0x3FFF
    return width, height


def _package_id(argument: str) -> str:
    manifest = yaml.safe_load((journey.package_root(argument) / "manifest.yaml").read_text("utf-8"))
    return manifest["package"]["id"]


# ---------------------------------------------------------------------------
# The table agrees with the task cards, the calendar, and the runtime
# ---------------------------------------------------------------------------


def test_every_published_trail_session_has_a_row_and_no_other_session_does() -> None:
    with_trail = {s for s in PUBLISHED if journey.canonical_command(s) is not None}
    assert {row.session for row in SESSIONS} == with_trail, (
        "Each published session with a canonical trail command needs exactly one row in "
        "scripts/journey_snapshots.py SESSIONS (and no unpublished session may have one)."
    )


@pytest.mark.parametrize("row", SESSIONS, ids=lambda row: row.session)
def test_row_matches_its_task_card_command(row) -> None:  # type: ignore[no-untyped-def]
    command = journey.canonical_command(row.session)
    assert command is not None
    assert row.mission_id == command.mission_id
    assert row.player == command.player
    get_course_mission(row.mission_id)
    for moment in row.moments:
        if moment.fixture is not None:
            assert moment.fixture.package in command.packages, moment.name
        for spec in moment.expect.texts:
            if isinstance(spec, journey.PackageText):
                assert spec.package in command.packages, (moment.name, spec)
    if row.deferred:
        # A deferred row's task card may still be changing; it is checked
        # once the deferral is lifted.
        return
    package_ids = {_package_id(argument) for argument in command.packages}
    for qualified_id in row.must_show:
        assert qualified_id.split(":")[0] in package_ids, (row.session, qualified_id)


@pytest.mark.parametrize("row", SESSIONS, ids=lambda row: row.session)
def test_row_has_one_hero_and_at_most_two_optional_moments(row) -> None:  # type: ignore[no-untyped-def]
    kinds = [moment.kind for moment in row.moments]
    assert kinds.count(HERO) == 1 and kinds[0] == HERO
    assert len(kinds) - 1 <= MAX_OPTIONAL
    assert set(kinds) <= set(KINDS)
    assert row.hero.slug == "hero"
    slugs = [moment.slug for moment in row.moments]
    assert len(set(slugs)) == len(slugs)
    assert all(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug) for slug in slugs)
    assert all(moment.name.startswith(f"{row.session}_") for moment in row.moments)


@pytest.mark.parametrize("row", ACTIVE_ROWS, ids=lambda row: row.session)
def test_active_rows_expect_the_presentation_the_runtime_gives(row) -> None:  # type: ignore[no-untyped-def]
    gets_moon_meadow = mission_presentation(row.mission_id) is not None
    assert gets_moon_meadow == (row.presentation == MOON_MEADOW), row.session


def test_each_row_excludes_entities_later_sessions_introduce() -> None:
    for index, row in enumerate(SESSIONS):
        if row.deferred:
            # Its task card is still changing; checked once the deferral is lifted.
            continue
        command = journey.canonical_command(row.session)
        assert command is not None
        own = {_package_id(argument) for argument in command.packages}
        for later in SESSIONS[index + 1 :]:
            for qualified_id in later.must_show:
                if qualified_id.split(":")[0] not in own:
                    assert qualified_id in row.must_not_show, (row.session, qualified_id)


def test_s04_lantern_is_present_without_a_destination_marker() -> None:
    # The S04 HERO shows the Lantern lit but never marked as the goal: M04 is
    # completed by talking to the Guide.
    assert "crystal-lantern:lantern" in SESSIONS_BY_ID["S04"].must_show
    policy = mission_presentation(SESSIONS_BY_ID["S04"].mission_id)
    assert policy is not None and not policy.lantern_waypoint


# ---------------------------------------------------------------------------
# S05 is the conversation in progress at the S04 spot
# ---------------------------------------------------------------------------


def test_s05_row_states_the_conversation_contract() -> None:
    s05 = SESSIONS_BY_ID["S05"]
    assert not s05.deferred and s05.presentation == MOON_MEADOW
    assert s05.mission_id == "write-a-short-conversation"
    # The same spot as S04, with the S05 package's own Guide and no other Guide.
    assert set(s05.must_show) == {journey.NOVA, journey.LANTERN, journey.S05_GUIDE}
    assert {journey.GUIDE, journey.PIXEL, journey.S02_COMPASS, journey.S03_COMPASS} <= set(
        s05.must_not_show
    )
    assert set(journey.S06_OBJECTS) <= set(s05.must_not_show)
    assert _package_id("lessons/sessions/s06/student/explorer-package") == "starlight-garden"
    s06_card = journey.canonical_command("S06")
    assert s06_card is not None and journey.S05_PACKAGE not in s06_card.packages
    assert [moment.kind for moment in s05.moments] == [HERO]
    hero = s05.hero
    assert hero.name == "S05_CONVERSATION" and hero.fixture is None
    # A learning moment, not completion: the Guide is the target, the middle
    # line (dialogue[1]) is on screen, and M05 is still incomplete.
    expect = hero.expect
    assert expect.target == journey.S05_GUIDE and not expect.complete
    assert expect.visited == ()
    assert [step for step in hero.steps if step == ("press",)] == [("press",)] * 2
    lines = yaml.safe_load(
        (journey.package_root(journey.S05_PACKAGE) / "character/guide.yaml").read_text("utf-8")
    )["conversation"]
    assert len(lines) == 3, "two presses must stop before the final line"
    texts = [spec for spec in expect.texts if isinstance(spec, journey.PackageText)]
    indexed = [spec for spec in texts if spec.index is not None]
    assert {(spec.key, spec.index, spec.joined) for spec in indexed} == {
        ("conversation", 1, True),
        ("conversation", 1, False),
    }


def test_s05_hero_shows_no_completion_or_later_content() -> None:
    [entry] = [entry for entry in ENTRIES if entry["session"] == "S05"]
    assert (entry["moment"], entry["kind"]) == ("S05_CONVERSATION", HERO)
    assert entry["presentation"] == MOON_MEADOW and entry["fixture"] is None
    text = json.dumps(entry).lower()
    for word in ("s06", "starlight", "sun-seed", "rain-bell", "wind-flower", "collection"):
        assert word not in text, word
    assert sorted(path.name for path in (PUBLIC_JOURNEY / "s05").iterdir()) == [
        "hero-480.webp",
        "hero.webp",
    ]


# ---------------------------------------------------------------------------
# Step recipes are checked before anything is driven
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("step", "message"),
    [
        (("tap",), "takes 1 operand"),
        (("tap", "down", "up"), "takes 1 operand"),
        (("tap", "sideways"), "not a tap direction"),
        (("hold",), "takes 1 operand"),
        (("hold", 0.3, 0.4), "takes 1 operand"),
        (("walk_to", 455), "takes 2 operand"),
        (("press", 1), "takes 0 operand"),
        (("jump",), "unknown step"),
    ],
)
def test_malformed_steps_are_a_clear_capture_error(step, message) -> None:  # type: ignore[no-untyped-def]
    import dataclasses

    from scripts.capture_journey_snapshots import CaptureError, check_steps

    moment = dataclasses.replace(S01.hero, steps=(step,))
    with pytest.raises(CaptureError, match=message):
        check_steps(moment)


def test_every_table_recipe_is_well_formed() -> None:
    from scripts.capture_journey_snapshots import check_steps

    for row in SESSIONS:
        for moment in row.moments:
            check_steps(moment)


# ---------------------------------------------------------------------------
# S01 is the Moon Meadow arrival, and only that
# ---------------------------------------------------------------------------


def test_s01_is_published_as_the_moon_meadow_arrival() -> None:
    assert not S01.deferred, "S01 is canonical Moon Meadow; it must not be deferred"
    assert MANIFEST["deferred"] == []
    assert mission_presentation(S01.mission_id) is not None, "M01 lost its Moon Meadow"
    s01_entries = [entry for entry in ENTRIES if entry["session"] == "S01"]
    assert [(entry["moment"], entry["kind"]) for entry in s01_entries] == [("S01_ARRIVAL", HERO)]
    assert s01_entries[0]["presentation"] == MOON_MEADOW
    assert s01_entries[0]["fixture"] is None
    assert sorted(path.name for path in (PUBLIC_JOURNEY / "s01").iterdir()) == [
        "hero-480.webp",
        "hero.webp",
    ]


def test_s01_row_states_the_moon_meadow_arrival_contract() -> None:
    # The arrival cast is Nova, Pixel, and the Crystal Lantern, each drawn in
    # trusted art; the retired Fern / River Fountain cast and every later
    # session's Compass and Guide are excluded.
    assert S01.presentation == MOON_MEADOW
    assert set(S01.must_show) == {journey.NOVA, journey.PIXEL, journey.LANTERN}
    assert set(S01.must_not_show) == {
        journey.S02_COMPASS,
        journey.S03_COMPASS,
        journey.GUIDE,
        journey.S05_GUIDE,
        journey.FERN,
        journey.FOUNTAIN,
    }
    assert [moment.kind for moment in S01.moments] == [HERO]
    # The world, not completion: no prompt, nothing visited, not complete.
    expect = S01.hero.expect
    assert expect.untargeted and expect.target is None
    assert expect.visited == () and not expect.complete
    assert S01.hero.fixture is None
    # The retired cast's qualified IDs are real, so the exclusion can bite.
    assert _package_id("examples/explorer-packages/forest-guide") == journey.FERN.split(":")[0]
    assert (
        _package_id("examples/explorer-packages/river-fountain") == journey.FOUNTAIN.split(":")[0]
    )


def test_s01_metadata_names_no_later_session_or_retired_content() -> None:
    [entry] = [entry for entry in ENTRIES if entry["session"] == "S01"]
    text = json.dumps(entry).lower()
    for word in ("compass", "guide", "moonlit", "fern", "fountain", "forest", "river"):
        assert word not in text, word
    caption = f"{entry['session']} {entry['kind']}: {entry['moment']}"  # the contact sheet's
    assert caption == "S01 HERO: S01_ARRIVAL"


def test_harness_refuses_deferred_and_unpublished_sessions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import dataclasses

    from scripts.capture_journey_snapshots import CaptureError, publish

    deferred = dataclasses.replace(S01, deferred="waiting for a runtime change")
    monkeypatch.setattr(journey, "SESSIONS_BY_ID", {**SESSIONS_BY_ID, "S01": deferred})
    with pytest.raises(CaptureError, match="S01 is deferred"):
        publish(["S01"])
    with pytest.raises(CaptureError, match="not published"):
        publish(["S06"])


# ---------------------------------------------------------------------------
# The manifest
# ---------------------------------------------------------------------------


def test_manifest_header_matches_the_contract() -> None:
    assert MANIFEST["schema"] == journey.SCHEMA == "explore-studio/journey-snapshots@2"
    assert journey.schema_problem(MANIFEST) is None
    assert MANIFEST["fingerprintParts"] == list(journey.FINGERPRINT_PARTS)
    assert MANIFEST["fingerprintInputs"] == journey.fingerprint_inputs()
    for entry in ENTRIES:
        assert list(entry["fingerprintParts"]) == list(journey.FINGERPRINT_PARTS), entry
    assert MANIFEST["canonicalFrame"] == {"width": 960, "height": 640}
    assert MANIFEST["widths"] == [960, 480]
    assert MANIFEST["webp"] == dict(journey.WEBP_SETTINGS)
    assert [item["session"] for item in MANIFEST["deferred"]] == [  # type: ignore[union-attr]
        row.session for row in SESSIONS if row.deferred
    ]


def test_manifest_lists_exactly_the_active_rows_moments() -> None:
    expected = [f"{row.session}:{moment.name}" for row in ACTIVE_ROWS for moment in row.moments]
    assert [_entry_id(entry) for entry in ENTRIES] == expected, (
        "Every non-deferred row needs its HERO and optional moments captured: "
        "rerun python scripts/capture_journey_snapshots.py --all-published"
    )


def test_published_snapshot_set_is_the_reviewed_one() -> None:
    # Adding a session, a HERO, or an extra is a reviewed change to this set.
    published: dict[str, list[tuple[str, str]]] = {}
    for entry in ENTRIES:
        published.setdefault(entry["session"], []).append((entry["kind"], entry["moment"]))
    assert published == {
        "S01": [(HERO, "S01_ARRIVAL")],
        "S02": [(HERO, "S02_COMPASS_PROMPT"), ("LEARNING_MOMENT", "S02_MOVED_COMPASS")],
        "S03": [(HERO, "S03_REVEAL"), ("LEARNING_MOMENT", "S03_NEAR_CLUE")],
        "S04": [(HERO, "S04_DIALOGUE")],
        "S05": [(HERO, "S05_CONVERSATION")],
    }


@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
def test_entry_matches_calendar_task_card_and_table(entry) -> None:  # type: ignore[no-untyped-def]
    session = entry["session"]
    assert session in journey.calendar_sessions() and session in PUBLISHED
    row = SESSIONS_BY_ID[session]
    moment = next(m for m in row.moments if m.name == entry["moment"])
    command = journey.canonical_command(session)
    assert command is not None
    assert entry["kind"] == moment.kind
    assert entry["missionId"] == command.mission_id == row.mission_id
    get_course_mission(entry["missionId"])
    assert entry["packages"] == list(command.packages)
    assert entry["player"] == command.player
    assert entry["presentation"] == row.presentation
    gets_moon_meadow = mission_presentation(entry["missionId"]) is not None
    assert gets_moon_meadow == (entry["presentation"] == MOON_MEADOW)
    assert entry["fixture"] == (journey.describe(moment.fixture) if moment.fixture else None)
    assert entry["captureCommand"] == row.command


@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
def test_entry_images_exist_with_correct_size_and_hash(entry) -> None:  # type: ignore[no-untyped-def]
    assert sorted(entry["images"], key=int) == ["480", "960"]
    row = SESSIONS_BY_ID[entry["session"]]
    slug = next(moment.slug for moment in row.moments if moment.name == entry["moment"])
    for width_key, image in entry["images"].items():
        width = int(width_key)
        assert image["src"] == "/" + journey.image_path(row.session, slug, width)
        data = _public_file(image["src"]).read_bytes()
        assert _webp_size(data) == (width, width * 2 // 3) == (image["width"], image["height"])
        assert len(data) == image["bytes"]
        assert hashlib.sha256(data).hexdigest() == image["sha256"]
    assert re.fullmatch(r"[0-9a-f]{64}", entry["sourceRgbSha256"])


def test_960_snapshots_stay_within_the_size_budget() -> None:
    for entry in ENTRIES:
        assert entry["images"]["960"]["bytes"] <= 150_000, _entry_id(entry)
        assert entry["images"]["480"]["bytes"] < entry["images"]["960"]["bytes"]


def test_runtime_commit_is_the_pin_or_draws_identically() -> None:
    pin = journey.runtime_pin()
    for entry in ENTRIES:
        assert re.fullmatch(r"[0-9a-f]{40}", entry["runtimeCommit"]), _entry_id(entry)
        if entry["runtimeCommit"] != pin:
            # An older pin is still truthful only if the current one draws the same.
            assert entry["fingerprintParts"]["runtime"] == journey.runtime_digest(), entry


def test_runtime_commit_really_contains_the_captured_runtime() -> None:
    commits = {entry["runtimeCommit"] for entry in ENTRIES}
    for commit in commits:
        try:
            files = journey.runtime_files_at(commit)
        except subprocess.CalledProcessError:
            pytest.skip(f"git history for {commit} is not available (shallow checkout)")
        digest = journey.runtime_digest(files)
        for entry in ENTRIES:
            if entry["runtimeCommit"] == commit:
                assert (
                    entry["fingerprintParts"]["runtime"] == digest
                ), f"{_entry_id(entry)}: the runtime pin {commit} does not draw this snapshot"


# ---------------------------------------------------------------------------
# Publication boundary: only published sessions, nothing from the future
# ---------------------------------------------------------------------------


def test_public_journey_holds_only_manifest_files() -> None:
    listed = {_public_file(image["src"]) for entry in ENTRIES for image in entry["images"].values()}
    present = {path for path in PUBLIC_JOURNEY.rglob("*") if path.is_file()}
    assert present == listed, "public/journey/ may hold only files the manifest publishes"
    directories = {path.name for path in PUBLIC_JOURNEY.iterdir()}
    assert directories == {row.session.lower() for row in ACTIVE_ROWS}


def test_manifest_and_public_files_name_no_unpublished_session() -> None:
    text = journey.MANIFEST_PATH.read_text(encoding="utf-8")
    named = set(re.findall(r"\bS(\d\d)\b", text, flags=re.I))
    assert {f"S{number}" for number in named} <= set(PUBLISHED), named
    for path in PUBLIC_JOURNEY.rglob("*"):
        match = re.search(r"s(\d\d)", path.relative_to(PUBLIC_JOURNEY).as_posix())
        assert match and f"S{match.group(1)}" in PUBLISHED, path
    for session in journey.calendar_sessions():
        if session in PUBLISHED:
            continue
        command = journey.canonical_command(session)
        if command is None:
            continue
        own_packages = {
            argument
            for row in SESSIONS
            for argument in journey.canonical_command(row.session).packages  # type: ignore[union-attr]
        }
        for argument in set(command.packages) - own_packages:
            assert argument not in text, f"{session} package {argument} leaked into the manifest"
        if command.mission_id not in {row.mission_id for row in SESSIONS}:
            assert command.mission_id not in text, f"{session} mission leaked"


def test_manifest_is_not_served_publicly() -> None:
    assert "public" not in journey.MANIFEST_PATH.relative_to(journey.WEBSITE).parts
    assert json.loads(journey.MANIFEST_PATH.read_text(encoding="utf-8")) == MANIFEST


# ---------------------------------------------------------------------------
# Freshness: inputs that draw the frame have not changed since capture
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("entry", ENTRIES, ids=_entry_id)
def test_snapshot_is_fresh(entry) -> None:  # type: ignore[no-untyped-def]
    reason = journey.stale_reason(entry)
    assert reason is None, reason


def test_fingerprint_notices_a_runtime_change(monkeypatch: pytest.MonkeyPatch) -> None:
    entry = ENTRIES[0]
    real = journey.runtime_files()
    changed = {**real, "engine/rendering/_effects.py": real["engine/rendering/_effects.py"] + b"#"}
    monkeypatch.setattr(journey, "runtime_files", lambda root=journey.REPO: changed)
    reason = journey.stale_reason(entry)
    assert reason is not None
    assert f"Journey snapshot for {entry['session']}" in reason and "is stale" in reason
    assert "presentation runtime" in reason
    assert f"--session {entry['session']}" in reason


def test_fingerprint_ignores_audio_and_unrelated_code() -> None:
    inputs = journey.runtime_files()
    assert inputs and all(path.startswith(("engine/", "explore/")) for path in inputs)
    assert not any(path.startswith("engine/assets/trusted_audio/") for path in inputs)
    for inert in ("engine/audio/_manager.py", "engine/audio/_cues.py", "engine/app.py"):
        assert inert not in inputs
    assert "engine/assets/_trusted_audio.py" not in inputs
    assert "engine/rendering/_trail_presentation.py" in inputs
    assert any(path.startswith("engine/assets/trusted/") for path in inputs)


def test_fingerprint_covers_the_package_pipeline_and_colours() -> None:
    inputs = journey.runtime_files()
    for path in (
        "explore/_colors.py",
        "explore/packages/registration_adapter.py",
        "explore/packages/loader.py",
        "explore/packages/models.py",
        "explore/packages/package_set_planner.py",
        "explore/packages/classroom_trail.py",
        "engine/rendering/_mission_presentation.py",
        "engine/audio/_trail_audio.py",
    ):
        assert path in inputs, path
    assert set(journey.CAPTURE_IMPLEMENTATION_INPUTS) == {
        "scripts/capture_journey_snapshots.py",
        "scripts/journey_snapshots.py",
        "scripts/trail_driver.py",
    }


def test_capture_recipe_fields_are_what_the_recipe_hashes() -> None:
    row = ACTIVE_ROWS[0]
    command = journey.canonical_command(row.session)
    assert command is not None
    recipe = journey.capture_recipe(row, row.hero, command)
    assert tuple(recipe) == journey.CAPTURE_RECIPE_FIELDS


# ---------------------------------------------------------------------------
# The runtime input set is complete: a static walk of the harness's imports
# ---------------------------------------------------------------------------


def _module_file(name: str) -> Path | None:
    parts = name.split(".")
    if parts[0] not in {"engine", "explore"}:
        return None
    base = journey.REPO.joinpath(*parts)
    if (base / "__init__.py").is_file():
        return base / "__init__.py"
    if base.with_suffix(".py").is_file():
        return base.with_suffix(".py")
    return None


def _imported_names(path: Path, module: str) -> set[str]:
    """Every module name *path* may import, read from its syntax tree (never run)."""
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                anchor = package.split(".")[: len(package.split(".")) - node.level + 1]
                base = ".".join(anchor + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            names.add(base)
            names.update(f"{base}.{alias.name}" for alias in node.names)
    with_parents = set(names)
    for name in names:
        parts = name.split(".")
        with_parents.update(".".join(parts[:index]) for index in range(1, len(parts)))
    return with_parents


def _harness_import_closure() -> set[str]:
    """Repo-relative engine/explore files reachable from the capture harness."""
    pending = [
        (journey.REPO / path, "scripts." + Path(path).stem)
        for path in journey.CAPTURE_IMPLEMENTATION_INPUTS
    ]
    seen: set[Path] = set()
    while pending:
        path, module = pending.pop()
        for name in _imported_names(path, module):
            found = _module_file(name)
            if found is not None and found not in seen:
                seen.add(found)
                pending.append((found, name))
    return {path.relative_to(journey.REPO).as_posix() for path in seen}


def _covered(path: str, entries) -> bool:  # type: ignore[no-untyped-def]
    return any(path == entry or path.startswith(entry + "/") for entry in entries)


def test_every_module_the_harness_reaches_is_fingerprinted_or_pixel_inert() -> None:
    closure = _harness_import_closure()
    # The walk must reach the scene-construction layers the reviewer named.
    assert {
        "explore/_colors.py",
        "explore/packages/registration_adapter.py",
        "explore/packages/loader.py",
        "explore/packages/package_set_planner.py",
        "explore/packages/models.py",
        "engine/scenes/_classroom_trail_scene.py",
    } <= closure
    unclassified = sorted(
        path
        for path in closure
        if not _covered(path, journey.RUNTIME_INPUTS)
        and not _covered(path, journey.RUNTIME_PIXEL_INERT)
    )
    assert not unclassified, (
        "The capture harness imports these modules, but they are neither in "
        "journey_snapshots.RUNTIME_GROUPS nor justified in RUNTIME_PIXEL_INERT: "
        f"{unclassified}"
    )


def test_pixel_inert_entries_are_real_reached_and_disjoint_from_the_runtime() -> None:
    closure = _harness_import_closure()
    for path, reason in journey.RUNTIME_PIXEL_INERT.items():
        assert reason, path
        assert any(_covered(module, [path]) for module in closure), f"{path} is never imported"
        assert not _covered(path, journey.RUNTIME_INPUTS), path
        assert not any(_covered(entry, [path]) for entry in journey.RUNTIME_INPUTS), path


def test_no_tracked_runtime_file_is_skipped_by_the_suffix_filter() -> None:
    try:
        listing = subprocess.run(
            ["git", "ls-files", "-z", "--", *journey.RUNTIME_INPUTS],
            cwd=journey.REPO,
            check=True,
            capture_output=True,
        ).stdout.decode("utf-8")
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git is not available")
    tracked = {name for name in listing.split("\0") if name}
    assert tracked and tracked == set(journey.runtime_files()), (
        "every tracked file under RUNTIME_GROUPS must be hashed; extend _RUNTIME_SUFFIXES "
        "or move the file"
    )


# ---------------------------------------------------------------------------
# CI runs whenever a fingerprint input changes
# ---------------------------------------------------------------------------

WORKFLOW = journey.REPO / ".github" / "workflows" / "journey-snapshots.yml"


def _workflow_paths() -> list[str]:
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    triggers = document.get("on", document.get(True))  # YAML 1.1 reads `on` as True
    pull_request, push = triggers["pull_request"]["paths"], triggers["push"]["paths"]
    assert pull_request == push, "pull_request and push must watch the same paths"
    return pull_request


def _glob(pattern: str) -> re.Pattern[str]:
    """GitHub's path filter syntax: ``**`` crosses directories, ``*`` does not."""
    out = ""
    index = 0
    while index < len(pattern):
        if pattern.startswith("**", index):
            out, index = out + ".*", index + 2
        elif pattern[index] == "*":
            out, index = out + "[^/]*", index + 1
        else:
            out, index = out + re.escape(pattern[index]), index + 1
    return re.compile(out)


def _triggers_ci(path: str) -> bool:
    return any(_glob(pattern).fullmatch(path) for pattern in _workflow_paths())


def _fingerprinted_paths() -> set[str]:
    paths = set(journey.runtime_files())
    paths.update(journey.CAPTURE_IMPLEMENTATION_INPUTS)
    for row in SESSIONS:
        command = journey.canonical_command(row.session)
        assert command is not None
        for argument in command.packages:
            root = journey.package_root(argument)
            for path in root.rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts:
                    paths.add(path.relative_to(journey.REPO).as_posix())
        paths.add(journey.task_card(row.session).relative_to(journey.REPO).as_posix())
    return paths


def test_every_fingerprint_input_triggers_the_journey_workflow() -> None:
    missed = sorted(path for path in _fingerprinted_paths() if not _triggers_ci(path))
    assert not missed, f"{WORKFLOW.name} paths miss fingerprint inputs: {missed}"
    for path in (
        journey.MANIFEST_PATH,
        journey.CALENDAR,
        PUBLIC_JOURNEY / "s02" / "hero.webp",
        PUBLIC_JOURNEY / "s05" / "stray.webp",
        journey.REPO / "scripts" / "make_my_world.py",
        journey.REPO / "scripts" / "provision_student_workspace.py",
    ):
        assert _triggers_ci(path.relative_to(journey.REPO).as_posix()), path


def test_the_journey_workflow_ignores_unrelated_changes() -> None:
    for path in (
        "README.md",
        "docs/architecture.md",
        "course4teen-website/app/page.tsx",
        "course4teen-website/app/students/slides/s02/page.tsx",
        "explore/_world.py",
    ):
        assert not _triggers_ci(path), path


def test_the_journey_workflow_runs_the_standalone_check() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "python scripts/capture_journey_snapshots.py --check" in text
    assert "tests/test_journey_snapshot_freshness.py" in text
