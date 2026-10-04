"""The published Journey snapshots: contract, publication boundary, and freshness.

Nothing here captures a frame; ``tests/test_journey_snapshot_determinism.py``
drives the real Trail. These checks keep the committed WebP files and
``course4teen-website/journey/snapshots.json`` honest: every snapshot belongs to
a published session, shows that session's canonical task-card command, carries
no later session's content, and still matches the runtime and packages that
produced it.
"""

from __future__ import annotations

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
# S01 waits for Phase B and can never be published from the plain Trail
# ---------------------------------------------------------------------------


def test_s01_is_deferred_with_a_reason_or_published_as_moon_meadow() -> None:
    s01_entries = [entry for entry in ENTRIES if entry["session"] == "S01"]
    if S01.deferred:
        assert len(S01.deferred) > 40, "say why S01 is deferred"
        assert not s01_entries, "S01 is deferred but has published snapshots"
        assert not (PUBLIC_JOURNEY / "s01").exists(), "S01 is deferred but has public files"
        deferred = {item["session"]: item for item in MANIFEST["deferred"]}  # type: ignore[union-attr]
        assert deferred["S01"]["reason"] == S01.deferred
        assert deferred["S01"]["captureCommand"] == S01.command
    else:
        assert (
            mission_presentation(S01.mission_id) is not None
        ), "S01's deferral was lifted but the runtime still gives M01 the plain Trail"
        assert {entry["moment"] for entry in s01_entries} >= {S01.hero.name}
    assert S01.presentation == MOON_MEADOW, "the S01 HERO must be the Moon Meadow arrival"


def test_harness_refuses_deferred_and_unpublished_sessions() -> None:
    from scripts.capture_journey_snapshots import CaptureError, publish

    if S01.deferred:
        with pytest.raises(CaptureError, match="S01 is deferred"):
            publish(["S01"])
    with pytest.raises(CaptureError, match="not published"):
        publish(["S05"])


# ---------------------------------------------------------------------------
# The manifest
# ---------------------------------------------------------------------------


def test_manifest_header_matches_the_contract() -> None:
    assert MANIFEST["schema"] == journey.SCHEMA
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
    assert not any(path.startswith("engine/audio/") for path in inputs)
    assert not any("trusted_audio" in path for path in inputs)
    assert "engine/rendering/_trail_presentation.py" in inputs
    assert any(path.startswith("engine/assets/trusted/") for path in inputs)
