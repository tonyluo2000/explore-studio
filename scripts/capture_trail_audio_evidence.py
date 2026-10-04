"""Record evidence for the Moon Meadow audio, since sound cannot be screenshotted.

Drives the real M01-M05 Trail scenes headlessly with the real Pygame mixer
(SDL's ``dummy`` audio driver, so no speakers are needed) and fixed 60 FPS
steps, then reports:

* ``assets`` — every trusted sound: duration, size, format, peak and RMS
  level in the file and at its cue volume;
* ``events`` — a frame-stamped cue log per mission from a scripted run, to
  show each cue fires once per real event and the completion motif once;
* ``parity`` — the same scripted gameplay trace with audio on, muted, and
  with the mixer unavailable (a bogus SDL audio driver), compared by digest;
* ``benchmark`` — update + render time with and without audio;
* ``preview OUT.wav`` — an offline mix of the scripted M02 run at the real
  cue volumes, to listen to the classroom balance (not committed).

    python3 scripts/capture_trail_audio_evidence.py assets|events|parity|benchmark
    python3 scripts/capture_trail_audio_evidence.py preview OUT.wav
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import statistics
import subprocess
import sys
import time
import wave
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import pygame  # noqa: E402

from engine.assets import TRUSTED_AUDIO_ROOT, TrustedAudioCatalog  # noqa: E402
from engine.audio import CUES, AudioCue, AudioManager  # noqa: E402

STEP = 1 / 60
EXAMPLES = REPO / "examples/explorer-packages"
SESSIONS = REPO / "lessons/sessions"
MISSIONS = {
    "M01": (
        "visit-all-classroom-objects",
        (EXAMPLES / "nova-character", EXAMPLES / "pixel-companion", EXAMPLES / "crystal-lantern"),
    ),
    "M02": (
        "create-a-classroom-object",
        (
            EXAMPLES / "nova-character",
            EXAMPLES / "pixel-companion",
            EXAMPLES / "crystal-lantern",
            SESSIONS / "s02/student/explorer-package",
        ),
    ),
    "M03": (
        "make-your-object-respond",
        (EXAMPLES / "nova-character", SESSIONS / "s03/student/explorer-package"),
    ),
    "M04": (
        "introduce-your-character",
        (
            EXAMPLES / "nova-character",
            EXAMPLES / "crystal-lantern",
            SESSIONS / "s04/student/explorer-package",
        ),
    ),
    "M05": (
        "write-a-short-conversation",
        (EXAMPLES / "nova-character", EXAMPLES / "pixel-companion", EXAMPLES / "crystal-lantern"),
    ),
}


class Trail:
    """One real Trail scene, the real renderer, and (optionally) real audio."""

    def __init__(self, mission: str, *, audio: str = "on") -> None:
        from engine._config import Config
        from engine._platform import Platform
        from engine.rendering import Renderer
        from explore.packages.classroom_trail import (
            create_classroom_trail_scene,
            plan_local_classroom_trail,
        )

        mission_id, roots = MISSIONS[mission]
        self.config = Config()
        self.platform = Platform(self.config)
        self.platform.initialize()
        self.renderer = Renderer(self.platform)
        self.frame = 0
        self.log: list[tuple[int, str, str]] = []
        self.audio: AudioManager | None = None
        if audio != "none":
            self.audio = AudioManager(self.platform.audio_backend(), muted=audio == "muted")
            self._wrap(self.audio)
        planned = plan_local_classroom_trail(roots, player_qualified_id="nova-character:nova")
        assert planned.is_planned, planned.issues
        self.scene = create_classroom_trail_scene(
            self.renderer, planned.plan, mission_id=mission_id, audio=self.audio
        )
        self.scene.enter()

    def _wrap(self, manager: AudioManager) -> None:
        """Stamp each cue outcome with the frame it happened on."""
        for name in ("play", "start_ambience"):
            original = getattr(manager, name)

            def stamped(*args, _original=original, **kwargs):  # type: ignore[no-untyped-def]
                outcome = _original(*args, **kwargs)
                cue = args[0] if args else AudioCue.AMBIENT_MOON_MEADOW
                self.log.append((self.frame, AudioCue(cue).value, outcome))
                return outcome

            setattr(manager, name, stamped)

    def step(self, *, interact: bool = False, **keys: bool) -> None:
        from engine.input import DirectionalInput, InteractionInput

        self.frame += 1
        self.scene.update(
            DirectionalInput(**keys), InteractionInput(interact_pressed=interact), STEP
        )
        self.platform.clear_frame(self.config.background_color)
        self.scene.render()

    def close(self) -> None:
        self.scene.exit()
        if self.audio is not None:
            self.audio.shutdown()
        self.platform.shutdown()


def _walk_to(trail: Trail, x: float, y: float) -> None:
    player = trail.scene.player
    for _ in range(900):
        dx, dy = x - player.x_float, y - player.y_float
        if abs(dx) < 3 and abs(dy) < 3:
            return
        trail.step(left=dx < -2, right=dx > 2, up=dy < -2, down=dy > 2)
    raise AssertionError(f"Nova never reached {(x, y)}")


def _visit_all(trail: Trail) -> list[tuple[object, ...]]:
    """Walk to every object and NPC in order, press E twice, idle; return a trace."""
    scene = trail.scene
    trace: list[tuple[object, ...]] = []
    targets = [item.qualified_id for item in (*scene.objects, *scene.npcs)]
    for qualified_id in targets:
        entity = next(
            getattr(item, "world_object", None) or item.character
            for item in (*scene.objects, *scene.npcs)
            if item.qualified_id == qualified_id
        )
        _walk_to(trail, entity.x - 70, entity.y)
        for _ in range(30):
            trail.step()
        for _ in range(2):
            trail.step(interact=True)
            for _ in range(45):
                trail.step()
        if qualified_id == targets[0]:
            scene.toggle_audio_mute()
            for _ in range(10):
                trail.step()
            scene.toggle_audio_mute()
        trace.append(
            (
                round(scene.player.x_float, 6),
                round(scene.player.y_float, 6),
                scene.target_qualified_id,
                sorted(scene.visited_qualified_ids),
                sorted(scene.spoken_npc_ids),
                scene.mission_is_complete,
                scene.feedback_message,
            )
        )
    for _ in range(120):
        trail.step()
    return trace


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


def _dbfs(value: float) -> str:
    return f"{20 * math.log10(value):.1f}" if value > 0 else "-inf"


def report_assets() -> None:
    manifest = json.loads((TRUSTED_AUDIO_ROOT / "manifest.json").read_text())["assets"]
    volume_of = {asset: spec.volume for spec in CUES.values() for asset in spec.assets}
    cue_of = {asset: cue.value for cue, spec in CUES.items() for asset in spec.assets}
    total = 0
    print("| Sound | Cue | Duration | Size | Format | Peak | RMS | Cue volume | Played peak |")
    print("|---|---|---|---|---|---|---|---|---|")
    for asset_id, entry in manifest.items():
        path = TRUSTED_AUDIO_ROOT / entry["file"]
        size = path.stat().st_size
        total += size
        with wave.open(str(path), "rb") as handle:
            data = handle.readframes(handle.getnframes())
            rate, channels, width = (
                handle.getframerate(),
                handle.getnchannels(),
                handle.getsampwidth(),
            )
        samples = [
            int.from_bytes(data[i : i + 2], "little", signed=True) / 32767
            for i in range(0, len(data), 2)
        ]
        peak = max(abs(sample) for sample in samples)
        rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
        volume = volume_of[asset_id]
        loop = " (loop)" if entry["loop"] else ""
        print(
            f"| `{asset_id}`{loop} | `{cue_of[asset_id]}` | {len(samples) / rate:.2f} s | "
            f"{size / 1024:.1f} KiB | {rate} Hz / {channels} ch / {8 * width}-bit | "
            f"{_dbfs(peak)} dBFS | {_dbfs(rms)} dBFS | {volume:.2f} | {_dbfs(peak * volume)} dBFS |"
        )
    print(f"\nTotal: {len(manifest)} files, {total} bytes ({total / 1024:.1f} KiB)")


def report_events() -> None:
    for mission in MISSIONS:
        trail = Trail(mission)
        _visit_all(trail)
        trail.close()
        log = [entry for entry in trail.log if entry[1] != "footstep_grass"]
        steps = [entry for entry in trail.log if entry[1] == "footstep_grass"]
        played_steps = sum(1 for entry in steps if entry[2] == "played")
        print(f"\n### {mission} ({MISSIONS[mission][0]}) — {trail.frame} frames")
        if not trail.log:
            print("\nNo cue requested: this mission has no Moon Meadow audio.")
            continue
        print("\n| Frame | Cue | Outcome |\n|---|---|---|")
        for frame, cue, outcome in log:
            print(f"| {frame} | `{cue}` | {outcome} |")
        print(
            f"\nFootsteps: {len(steps)} requested, {played_steps} played "
            f"over {trail.frame} frames."
        )
        complete = [entry for entry in trail.log if entry[1] == "mission_complete"]
        print(f"Mission complete: {len(complete)} request(s).")


def _trace_digest(mission: str, audio: str) -> str:
    code = (
        "import json,sys;sys.argv=['x'];"
        "import scripts.capture_trail_audio_evidence as e;"
        f"t=e.Trail({mission!r},audio={audio!r});trace=e._visit_all(t);"
        "available=bool(t.audio and t.audio.available);t.close();"
        "print(json.dumps([trace, available]))"
    )
    env = dict(os.environ)
    if audio == "unavailable":
        env["SDL_AUDIODRIVER"] = "no-such-audio-driver"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    trace, available = json.loads(result.stdout.strip().splitlines()[-1])
    digest = hashlib.sha256(json.dumps(trace).encode()).hexdigest()[:16]
    return f"{digest} (mixer open: {available})"


def report_parity() -> None:
    print("| Mission | No manager | Audio on | Muted at start | Mixer unavailable |")
    print("|---|---|---|---|---|")
    for mission in MISSIONS:
        digests = [_trace_digest(mission, mode) for mode in ("none", "on", "muted", "unavailable")]
        same = len({digest.split()[0] for digest in digests}) == 1
        print(f"| {mission} | " + " | ".join(digests) + f" |{' identical' if same else ' DIFFER'}")


def report_benchmark(frames: int = 900) -> None:
    pattern = ["right"] * 40 + ["up"] * 30 + ["left"] * 160 + ["down"] * 140 + ["right"] * 120
    for mission in ("M02", "M04"):
        for audio in ("none", "on", "on", "none"):
            trail = Trail(mission, audio=audio)
            for _ in range(60):
                trail.step()
            samples = []
            for index in range(frames):
                key = pattern[index % len(pattern)]
                start = time.perf_counter()
                trail.step(**{key: True}, interact=index % 60 == 0)
                samples.append((time.perf_counter() - start) * 1000)
            channels = pygame.mixer.get_num_channels() if pygame.mixer.get_init() else 0
            trail.close()
            samples.sort()
            print(
                f"{mission} audio={audio:<4} frames={frames} "
                f"mean_ms={statistics.fmean(samples):.3f} "
                f"p95_ms={samples[int(len(samples) * 0.95) - 1]:.3f} mixer_channels={channels}"
            )


def render_preview(out: Path) -> None:
    """Mix the scripted M02 run offline at the real cue volumes."""
    trail = Trail("M02")
    _visit_all(trail)
    trail.close()
    catalog = TrustedAudioCatalog()
    rate = 22050

    def load(asset_id: str) -> list[float]:
        data = catalog.read_verified(asset_id)
        assert data is not None
        with wave.open(io.BytesIO(data), "rb") as handle:
            raw = handle.readframes(handle.getnframes())
        return [
            int.from_bytes(raw[i : i + 2], "little", signed=True) / 32767
            for i in range(0, len(raw), 2)
        ]

    length = round((trail.frame * STEP + 2.0) * rate)
    mix = [0.0] * length
    bed = load("ambient/moon-meadow")
    ambience = CUES[AudioCue.AMBIENT_MOON_MEADOW].volume
    for index in range(length):
        mix[index] += bed[index % len(bed)] * ambience * min(1.0, index / (1.5 * rate))
    rotation: dict[str, int] = {}
    for frame, cue, outcome in trail.log:
        if outcome != "played":
            continue
        spec = CUES[AudioCue(cue)]
        turn = rotation.get(cue, 0)
        rotation[cue] = turn + 1
        sound = load(spec.assets[turn % len(spec.assets)])
        start = round(frame * STEP * rate)
        for index, sample in enumerate(sound[: max(0, length - start)]):
            mix[start + index] += sample * spec.volume
    peak = max(abs(sample) for sample in mix)
    frames = b"".join(
        max(-32767, min(32767, round(sample * 32767))).to_bytes(2, "little", signed=True)
        for sample in mix
    )
    with wave.open(str(out), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(frames)
    print(f"wrote {out}: {length / rate:.1f} s, mix peak {_dbfs(peak)} dBFS")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", choices=("assets", "events", "parity", "benchmark", "preview"))
    parser.add_argument("output", type=Path, nargs="?")
    args = parser.parse_args(argv)
    if args.report == "preview":
        if args.output is None:
            parser.error("preview needs an OUT.wav path")
        render_preview(args.output)
    else:
        {
            "assets": report_assets,
            "events": report_events,
            "parity": report_parity,
            "benchmark": report_benchmark,
        }[args.report]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
