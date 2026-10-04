"""Journey snapshots regenerate exactly, and only from the right runtime state.

Each published moment is captured from the real Trail twice in one process and
must give the same 960 x 640 frame and the same WebP bytes. On the toolchain
recorded in the manifest the recapture must also equal the committed files.
Elsewhere that comparison is skipped: font rasterization and the WebP encoder
can differ between pygame, SDL_ttf, Pillow, and libwebp builds, so the source
frame hash is authoritative only on the recorded toolchain (see
``docs/journey-proof/snapshots/README.md``).
"""

from __future__ import annotations

import hashlib

import pytest

pytest.importorskip("PIL", reason="Journey snapshot encoding needs Pillow (the [art] extra)")

from engine.rendering._mission_presentation import mission_presentation  # noqa: E402
from scripts import journey_snapshots as journey  # noqa: E402
from scripts.capture_journey_snapshots import (  # noqa: E402
    CaptureError,
    capture_moment,
    encode,
    resolve,
    toolchain,
)
from scripts.journey_snapshots import TrailCommand  # noqa: E402

ENTRIES = {
    (entry["session"], entry["moment"]): entry
    for entry in journey.load_manifest()["snapshots"]  # type: ignore[union-attr]
}
MOMENTS = [
    (row.session, moment.name)
    for row in journey.SESSIONS
    if not row.deferred
    for moment in row.moments
]


def _capture(session: str, name: str) -> bytes:
    row, command = resolve(session)
    moment = next(moment for moment in row.moments if moment.name == name)
    return capture_moment(row, moment, command)


@pytest.mark.parametrize("key", MOMENTS, ids=lambda key: key[1])
def test_moment_regenerates_byte_for_byte(key: tuple[str, str]) -> None:
    first, second = _capture(*key), _capture(*key)
    assert len(first) == 960 * 640 * 3
    assert first == second, f"{key[1]}: two captures of the same moment differ"
    assert encode(first) == encode(second)

    entry = ENTRIES[key]
    if entry["toolchain"] != toolchain():
        pytest.skip(
            f"recorded on {entry['toolchain']}, running on {toolchain()}: "
            "cross-toolchain byte identity is not promised"
        )
    assert hashlib.sha256(first).hexdigest() == entry["sourceRgbSha256"]
    for width, data in encode(first).items():
        assert hashlib.sha256(data).hexdigest() == entry["images"][str(width)]["sha256"]


def test_480_is_a_downscale_of_the_canonical_frame() -> None:
    import io

    from PIL import Image

    rgb = _capture(*MOMENTS[0])
    images = encode(rgb)
    with Image.open(io.BytesIO(images[480])) as small, Image.open(io.BytesIO(images[960])) as big:
        assert small.size == (480, 320) and big.size == (960, 640)
        assert small.mode == big.mode == "RGB"
        reference = big.convert("RGB").resize((480, 320), Image.Resampling.LANCZOS)
        difference = sum(
            abs(a - b) for a, b in zip(small.tobytes(), reference.tobytes(), strict=True)
        ) / len(reference.tobytes())
    assert difference < 4, "the 480w snapshot does not look like the 960w one"


def test_the_plain_s01_trail_cannot_pass_as_the_moon_meadow_hero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import MappingProxyType

    from engine.rendering import _mission_presentation as presentations

    s01 = journey.SESSIONS_BY_ID["S01"]
    assert mission_presentation(s01.mission_id) is not None
    plain = {
        mission: policy
        for mission, policy in presentations.MISSION_PRESENTATIONS.items()
        if mission != s01.mission_id
    }
    monkeypatch.setattr(presentations, "MISSION_PRESENTATIONS", MappingProxyType(plain))
    with pytest.raises(CaptureError, match="standard Trail"):
        _capture("S01", s01.hero.name)


def test_the_retired_s01_cast_cannot_pass_as_the_arrival() -> None:
    row, command = resolve("S01")
    retired = TrailCommand(
        (
            "examples/explorer-packages/nova-character",
            "examples/explorer-packages/forest-guide",
            "examples/explorer-packages/crystal-lantern",
            "examples/explorer-packages/river-fountain",
        ),
        command.options,
    )
    with pytest.raises(CaptureError) as raised:
        capture_moment(row, row.hero, retired)
    message = str(raised.value)
    assert "pixel-companion:pixel is not in the scene" in message
    assert "forest-guide:guide belongs to another session" in message
    assert "river-fountain:fountain belongs to another session" in message


def test_the_s01_arrival_with_a_prompt_is_rejected() -> None:
    # At the exact start Pixel is in range and the Trail offers "Talk to
    # Pixel"; the arrival HERO is the idle frame without a prompt.
    import dataclasses

    row, command = resolve("S01")
    prompted = dataclasses.replace(row.hero, steps=(("hold", 1.2),))
    with pytest.raises(CaptureError, match="target is pixel-companion:pixel, expected no prompt"):
        capture_moment(row, prompted, command)
