"""Build the course-owned trusted audio for the Moon Meadow Classroom Trail (S02-S04).

This is the provenance for every WAV under ``engine/assets/trusted_audio``.
The sounds are original: synthesized from code (seeded noise, sines, bell
partials, and simple filters) with the Python standard library only, so a
rebuild is byte-for-byte on any machine with the same Python. Nothing is
recorded, sampled, or downloaded.

The script also writes ``manifest.json``, which records each sound's format,
frame count, and SHA-256 digest. The runtime plays only files listed there
whose bytes match their digest (``engine.assets._trusted_audio``).

Sounds (all 22050 Hz, mono, 16-bit PCM):

* ``ambient/moon-meadow`` — a seamless 10 s night-meadow bed: soft wind,
  two faint distant insects, and a few sparse, restrained shimmer tones.
* ``sfx/footstep-grass-a`` / ``-b`` — two very soft grass brushes.
* ``sfx/object-near`` — a faint glint when Nova reaches something new.
* ``sfx/object-interact`` — a soft wooden tock for any inspected object.
* ``sfx/compass-magic`` — a short crystalline shimmer for the Moon Compass.
* ``sfx/pixel-greeting`` — Pixel's two-blip friendly chirp.
* ``sfx/npc-talk`` — the Moonlit Guide's soft moon bell (no voice).
* ``sfx/lantern-chime`` — a warm glass chime for the Crystal Lantern.
* ``sfx/mission-complete`` — a gentle four-note rising motif (1.7 s).
* ``sfx/ui-mute-toggle`` — a tiny tick confirming audio is back on.

Run from the repository root after changing a sound, then listen and review::

    python3 scripts/build_trail_audio.py

The committed WAVs and manifest are the reviewed artifact; commit them together.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import random
import sys
import wave
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TRUSTED_AUDIO_ROOT = REPO / "engine" / "assets" / "trusted_audio"

SAMPLE_RATE = 22050
CHANNELS = 1
SAMPLE_WIDTH = 2
TAU = 2 * math.pi

Signal = list[float]


# ---------------------------------------------------------------------------
# Small deterministic DSP toolkit
# ---------------------------------------------------------------------------


def silence(seconds: float) -> Signal:
    return [0.0] * round(seconds * SAMPLE_RATE)


def noise(count: int, rng: random.Random) -> Signal:
    return [rng.uniform(-1.0, 1.0) for _ in range(count)]


def biquad(signal: Signal, kind: str, frequency: float, q: float = 0.707) -> Signal:
    """RBJ cookbook low-pass, high-pass, or band-pass (constant peak gain)."""
    w0 = TAU * frequency / SAMPLE_RATE
    alpha = math.sin(w0) / (2 * q)
    cos_w0 = math.cos(w0)
    if kind == "lowpass":
        b0, b1, b2 = (1 - cos_w0) / 2, 1 - cos_w0, (1 - cos_w0) / 2
    elif kind == "highpass":
        b0, b1, b2 = (1 + cos_w0) / 2, -(1 + cos_w0), (1 + cos_w0) / 2
    elif kind == "bandpass":
        b0, b1, b2 = alpha, 0.0, -alpha
    else:
        raise ValueError(kind)
    a0, a1, a2 = 1 + alpha, -2 * cos_w0, 1 - alpha
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    out: Signal = []
    x1 = x2 = y1 = y2 = 0.0
    for x in signal:
        y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        out.append(y)
        x2, x1, y2, y1 = x1, x, y1, y
    return out


def tone(
    frequency: float,
    seconds: float,
    *,
    attack: float = 0.004,
    decay: float = 0.3,
    partials: Sequence[tuple[float, float, float]] = ((1.0, 1.0, 1.0),),
    glide_to: float | None = None,
    vibrato: float = 0.0,
) -> Signal:
    """A struck/sung tone: (ratio, amplitude, decay scale) partials, exp decay."""
    count = round(seconds * SAMPLE_RATE)
    out = [0.0] * count
    for ratio, amplitude, decay_scale in partials:
        phase = 0.0
        tau = max(1e-4, decay * decay_scale)
        for index in range(count):
            t = index / SAMPLE_RATE
            base = frequency
            if glide_to is not None:
                base = frequency + (glide_to - frequency) * min(1.0, t / seconds)
            if vibrato:
                base *= 1 + vibrato * math.sin(TAU * 5.0 * t)
            phase += TAU * base * ratio / SAMPLE_RATE
            envelope = min(1.0, t / attack) * math.exp(-t / tau)
            out[index] += amplitude * envelope * math.sin(phase)
    return out


def envelope(signal: Signal, attack: float, decay: float) -> Signal:
    return [
        sample * min(1.0, (index / SAMPLE_RATE) / attack) * math.exp(-index / SAMPLE_RATE / decay)
        for index, sample in enumerate(signal)
    ]


def mix_into(target: Signal, source: Signal, offset: float, gain: float = 1.0) -> Signal:
    start = round(offset * SAMPLE_RATE)
    end = min(len(target), start + len(source))
    for index in range(start, end):
        target[index] += gain * source[index - start]
    return target


def mix_wrapped(target: Signal, source: Signal, start: int, gain: float = 1.0) -> None:
    """Add *source* into a loop, wrapping past the end so the loop stays seamless."""
    length = len(target)
    for index, sample in enumerate(source):
        target[(start + index) % length] += gain * sample


def edge_fades(signal: Signal, fade_in: float = 0.002, fade_out: float = 0.012) -> Signal:
    count = len(signal)
    rise = max(1, round(fade_in * SAMPLE_RATE))
    fall = max(1, round(fade_out * SAMPLE_RATE))
    for index in range(min(rise, count)):
        signal[index] *= index / rise
    for index in range(min(fall, count)):
        signal[count - 1 - index] *= index / fall
    return signal


def normalize_peak(signal: Signal, peak: float) -> Signal:
    largest = max(abs(sample) for sample in signal) or 1.0
    return [sample * peak / largest for sample in signal]


def normalize_rms(signal: Signal, rms: float) -> Signal:
    current = math.sqrt(sum(sample * sample for sample in signal) / len(signal)) or 1.0
    return [sample * rms / current for sample in signal]


def wav_bytes(signal: Signal) -> bytes:
    frames = bytearray()
    for sample in signal:
        value = max(-32767, min(32767, round(sample * 32767)))
        frames += value.to_bytes(2, "little", signed=True)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(CHANNELS)
        handle.setsampwidth(SAMPLE_WIDTH)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(bytes(frames))
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# The sounds
# ---------------------------------------------------------------------------

#: Bell-like partials: (frequency ratio, amplitude, decay scale).
BELL = ((1.0, 1.0, 1.0), (2.0, 0.32, 0.55), (2.76, 0.18, 0.4), (5.4, 0.05, 0.2))
GLASS = ((1.0, 1.0, 1.0), (2.0, 0.38, 0.6), (3.0, 0.14, 0.4), (6.0, 0.05, 0.08))
SOFT = ((1.0, 1.0, 1.0), (2.0, 0.2, 0.5))


def ambient_moon_meadow() -> Signal:
    """10 s seamless bed: wind under faint insects and sparse shimmer."""
    rng = random.Random(0x4D4F4F4E)  # "MOON"
    length = 10 * SAMPLE_RATE
    overlap = 2 * SAMPLE_RATE
    raw = noise(length + overlap, rng)
    low = biquad(raw, "lowpass", 380.0, 0.6)
    air = biquad(biquad(raw, "highpass", 700.0), "lowpass", 1600.0)
    wind: Signal = []
    for index in range(length + overlap):
        t = index / SAMPLE_RATE
        # Whole cycles per 10 s loop (0.1, 0.2, 0.3 Hz), so the swell repeats cleanly.
        swell = (
            0.62
            + 0.22 * math.sin(TAU * 0.1 * t)
            + 0.1 * math.sin(TAU * 0.3 * t + 1.1)
            + 0.06 * math.sin(TAU * 0.2 * t + 2.3)
        )
        gust = 0.5 + 0.5 * math.sin(TAU * 0.1 * t + 0.7)
        wind.append(swell * (low[index] + 0.18 * gust * air[index]))
    # Equal-power crossfade of the run-on into the head: sample N-1 -> sample 0
    # continues the same filtered noise, so the loop has no seam or click.
    bed = wind[:length]
    for index in range(overlap):
        theta = (index / overlap) * (math.pi / 2)
        bed[index] = wind[length + index] * math.cos(theta) + wind[index] * math.sin(theta)
    bed = normalize_rms(bed, 0.1)

    # Two distant insects: short pulse trains on high carriers, far below the wind.
    insects = [0.0] * length
    for carrier, rate, pulses, period, gain in (
        (4300.0, 15.0, 3, 1.55, 0.010),
        (3650.0, 11.0, 4, 2.45, 0.007),
    ):
        pulse = edge_fades(tone(carrier, 0.028, attack=0.006, decay=0.02), 0.004, 0.01)
        t = rng.uniform(0.0, period)
        while t < 10.0:
            for number in range(pulses):
                mix_wrapped(insects, pulse, round((t + number / rate) * SAMPLE_RATE), gain)
            t += period * rng.uniform(0.8, 1.25)

    # Restrained shimmer: a few soft, high, unrelated pentatonic tones, never a tune.
    shimmer = [0.0] * length
    for start, frequency in ((0.8, 1567.98), (3.9, 2349.32), (6.1, 1760.0), (8.4, 2093.0)):
        note = edge_fades(
            tone(frequency, 3.2, attack=0.7, decay=1.1, partials=SOFT, vibrato=0.002),
            0.01,
            0.3,
        )
        mix_wrapped(shimmer, note, round(start * SAMPLE_RATE), 0.012)

    combined = [bed[i] + insects[i] + shimmer[i] for i in range(length)]
    return [sample * 0.95 for sample in combined]


def footstep(seed: int, center: float) -> Signal:
    rng = random.Random(seed)
    brush = biquad(noise(round(0.085 * SAMPLE_RATE), rng), "bandpass", center, 0.9)
    brush = envelope(brush, 0.004, 0.022)
    thump = tone(95.0, 0.085, attack=0.003, decay=0.016)
    return edge_fades(normalize_peak(mix_into(brush, thump, 0.0, 0.08), 0.6), 0.002, 0.015)


def object_near() -> Signal:
    out = tone(2093.0, 0.45, attack=0.008, decay=0.12, partials=SOFT)
    mix_into(out, tone(3135.96, 0.35, attack=0.01, decay=0.1), 0.06, 0.45)
    return edge_fades(normalize_peak(out, 0.6))


def object_interact() -> Signal:
    rng = random.Random(0x544F434B)  # "TOCK"
    out = tone(620.0, 0.34, attack=0.002, decay=0.07, partials=((1.0, 1.0, 1.0), (2.4, 0.25, 0.5)))
    click = biquad(noise(round(0.02 * SAMPLE_RATE), rng), "lowpass", 2500.0)
    mix_into(out, envelope(click, 0.001, 0.004), 0.0, 0.3)
    return edge_fades(normalize_peak(out, 0.7))


def compass_magic() -> Signal:
    rng = random.Random(0x434F4D50)  # "COMP"
    out = silence(1.15)
    for index, frequency in enumerate((1318.51, 1567.98, 1975.53, 2637.02)):
        note = tone(frequency, 0.9, attack=0.006, decay=0.32, partials=GLASS)
        mix_into(out, note, 0.07 * index, 0.8 - 0.1 * index)
    swish = biquad(noise(round(0.6 * SAMPLE_RATE), rng), "highpass", 5000.0)
    mix_into(out, envelope(swish, 0.12, 0.12), 0.0, 0.12)
    return edge_fades(normalize_peak(out, 0.7), 0.002, 0.08)


def pixel_greeting() -> Signal:
    chip = ((1.0, 1.0, 1.0), (3.0, 0.22, 1.0), (5.0, 0.08, 1.0))
    out = silence(0.34)
    mix_into(out, tone(880.0, 0.1, attack=0.005, decay=0.09, partials=chip, glide_to=1174.66), 0)
    mix_into(
        out, tone(1174.66, 0.16, attack=0.005, decay=0.1, partials=chip, glide_to=1567.98), 0.12
    )
    return edge_fades(normalize_peak(out, 0.7), 0.002, 0.03)


def npc_talk() -> Signal:
    out = tone(783.99, 1.4, attack=0.006, decay=0.5, partials=BELL)
    mix_into(out, tone(1174.66, 1.25, attack=0.008, decay=0.42, partials=BELL), 0.13, 0.5)
    return edge_fades(normalize_peak(out, 0.7), 0.002, 0.15)


def lantern_chime() -> Signal:
    out = tone(523.25, 1.05, attack=0.004, decay=0.38, partials=GLASS)
    mix_into(out, tone(3140.0, 0.12, attack=0.001, decay=0.025), 0.0, 0.25)
    return edge_fades(normalize_peak(out, 0.7), 0.002, 0.12)


def mission_complete() -> Signal:
    out = silence(1.7)
    for start, frequency, decay in (
        (0.0, 523.25, 0.3),
        (0.13, 659.25, 0.3),
        (0.26, 783.99, 0.32),
        (0.42, 1046.5, 0.55),
    ):
        note = tone(frequency, 1.7 - start, attack=0.006, decay=decay, partials=BELL)
        mix_into(out, note, start, 0.85)
    return edge_fades(normalize_peak(out, 0.75), 0.002, 0.2)


def ui_mute_toggle() -> Signal:
    out = tone(1500.0, 0.08, attack=0.001, decay=0.012, partials=((1.0, 1.0, 1.0), (2.0, 0.3, 1)))
    return edge_fades(normalize_peak(out, 0.5), 0.001, 0.01)


@dataclass(frozen=True)
class SoundSpec:
    asset_id: str
    render: Callable[[], Signal]
    loop: bool = False

    @property
    def file(self) -> str:
        return f"{self.asset_id}.wav"


SOUNDS: tuple[SoundSpec, ...] = (
    SoundSpec("ambient/moon-meadow", ambient_moon_meadow, loop=True),
    SoundSpec("sfx/footstep-grass-a", lambda: footstep(0x57414C4B, 1800.0)),
    SoundSpec("sfx/footstep-grass-b", lambda: footstep(0x53544550, 2300.0)),
    SoundSpec("sfx/object-near", object_near),
    SoundSpec("sfx/object-interact", object_interact),
    SoundSpec("sfx/compass-magic", compass_magic),
    SoundSpec("sfx/pixel-greeting", pixel_greeting),
    SoundSpec("sfx/npc-talk", npc_talk),
    SoundSpec("sfx/lantern-chime", lantern_chime),
    SoundSpec("sfx/mission-complete", mission_complete),
    SoundSpec("sfx/ui-mute-toggle", ui_mute_toggle),
)


def build(root: Path = TRUSTED_AUDIO_ROOT, only: Sequence[str] = ()) -> dict[str, object]:
    """Render the sounds into *root* and (re)write its manifest; return the manifest."""
    unknown = set(only) - {spec.asset_id for spec in SOUNDS}
    if unknown:
        raise SystemExit(f"unknown sound ids: {sorted(unknown)}")
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "manifest.json"
    assets: dict[str, object] = {}
    if only and manifest_path.exists():
        assets = json.loads(manifest_path.read_text(encoding="utf-8"))["assets"]
    for spec in SOUNDS:
        if only and spec.asset_id not in only:
            continue
        data = wav_bytes(spec.render())
        path = root / spec.file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        frames = (len(data) - 44) // (CHANNELS * SAMPLE_WIDTH)
        assets[spec.asset_id] = {
            "file": spec.file,
            "sha256": hashlib.sha256(data).hexdigest(),
            "sample_rate": SAMPLE_RATE,
            "channels": CHANNELS,
            "sample_width": SAMPLE_WIDTH,
            "frames": frames,
            "loop": spec.loop,
        }
    manifest = {
        "schema_version": 1,
        "generator": "scripts/build_trail_audio.py",
        "license": "Original, synthesized in-repo; ships under the repository LICENSE.",
        "assets": dict(sorted(assets.items())),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    """Build every sound, or only the asset ids given on the command line."""
    only = tuple(sys.argv[1:] if argv is None else argv)
    manifest = build(only=only)
    for asset_id, entry in manifest["assets"].items():  # type: ignore[union-attr]
        size = (TRUSTED_AUDIO_ROOT / entry["file"]).stat().st_size
        seconds = entry["frames"] / entry["sample_rate"]
        print(
            f"{asset_id}: {entry['file']} {seconds:.2f} s {size / 1024:.1f} KiB "
            f"sha256={entry['sha256'][:12]}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
