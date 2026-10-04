"""Moon Meadow audio: the manager, the cue table, the trusted sounds, and the
M02-M04 Trail observer.

Audio is optional presentation. These tests pin that it is allow-listed by the
mission presentation policy, reacts only to real state transitions (once per
event), stays bounded, mutes at once, falls back to silence on any failure,
and never changes a single gameplay value.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import wave
from pathlib import Path

import pytest

from engine.assets import TRUSTED_AUDIO_ROOT, TrustedAudioCatalog
from engine.audio import (
    AUDIO_ENV_VAR,
    CUES,
    AudioCue,
    AudioManager,
    AudioMode,
    CueBus,
    TrailAudio,
    audio_mode_from_environment,
)
from engine.audio import _manager as manager_module
from engine.audio import _trail_audio as trail_audio_module
from engine.entities import Bounds
from engine.input import DirectionalInput, InteractionInput
from engine.rendering._classroom_sprites import (
    CRYSTAL_LANTERN_QUALIFIED_ID,
    MOON_COMPASS_QUALIFIED_ID,
    MOONLIT_GUIDE_QUALIFIED_ID,
    NOVA_QUALIFIED_ID,
    PIXEL_QUALIFIED_ID,
)
from engine.rendering._mission_presentation import (
    MISSION_PRESENTATIONS,
    S03_MOON_COMPASS_QUALIFIED_ID,
    mission_presentation,
)
from engine.rendering._trail_presentation import STEP_LENGTH
from explore.curriculum import (
    MISSION_01_ID,
    MISSION_02_ID,
    MISSION_03_ID,
    MISSION_04_ID,
    MISSION_05_ID,
)
from explore.packages.classroom_trail import (
    create_classroom_trail_scene,
    plan_local_classroom_trail,
)
from tests.test_s02_art_pass import S02_PACKAGES, ArtRenderer
from tests.test_s03_presentation import S03_PACKAGES
from tests.test_s04_presentation import S04_PACKAGES

REPO = Path(__file__).resolve().parents[1]
STEP = 1 / 60
STILL = DirectionalInput()
RIGHT = DirectionalInput(right=True)
NO_E = InteractionInput()
PRESS_E = InteractionInput(interact_pressed=True)
ANYWHERE = Bounds(min_x=-10_000, min_y=-10_000, max_x=10_000, max_y=10_000)
LATER_MISSIONS = (
    MISSION_05_ID,
    "build-an-object-collection",
    "toggle-an-object-state",
    "respond-to-object-state",
    "complete-actions-in-order",
)
PACKAGES = {MISSION_02_ID: S02_PACKAGES, MISSION_03_ID: S03_PACKAGES, MISSION_04_ID: S04_PACKAGES}


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


class FakeBackend:
    """Records mixer calls; ``opens`` may be True, False, or ``"raise"``."""

    def __init__(self, *, opens: object = True, fail_loads: tuple[str, ...] = ()) -> None:
        self.opens = opens
        self.fail_loads = fail_loads
        self.open_count = 0
        self.loads: list[float] = []
        self.calls: list[tuple[object, ...]] = []
        self.busy: set[int] = set()
        self.volumes: dict[int, list[float]] = {}

    def open(self, channel_count: int) -> bool:
        self.open_count += 1
        self.calls.append(("open", channel_count))
        if self.opens == "raise":
            raise RuntimeError("no audio device")
        return bool(self.opens)

    def load(self, data: bytes, volume: float) -> object:
        digest = hashlib.sha256(data).hexdigest()
        if digest in self.fail_loads:
            raise ValueError("corrupt wav")
        self.loads.append(volume)
        return ("sound", digest[:8], volume)

    def play(self, channel: int, sound: object, *, loop: bool = False) -> None:
        self.calls.append(("play", channel, sound, loop))

    def is_busy(self, channel: int) -> bool:
        return channel in self.busy

    def set_volume(self, channel: int, volume: float) -> None:
        self.volumes.setdefault(channel, []).append(volume)

    def stop(self, channel: int, fade_ms: int = 0) -> None:
        self.calls.append(("stop", channel, fade_ms))

    def close(self) -> None:
        self.calls.append(("close",))

    def plays(self, channel: int | None = None) -> list[tuple[object, ...]]:
        return [
            call
            for call in self.calls
            if call[0] == "play" and (channel is None or call[1] == channel)
        ]


class CountingCatalog(TrustedAudioCatalog):
    def __init__(self, root: Path = TRUSTED_AUDIO_ROOT) -> None:
        super().__init__(root)
        self.reads: list[str] = []

    def read_verified(self, asset_id: str) -> bytes | None:
        self.reads.append(asset_id)
        return super().read_verified(asset_id)


class RecordingSink:
    """A perfect audio sink: records every request, no cooldowns."""

    def __init__(self, *, available: bool = True, muted: bool = False) -> None:
        self.available = available
        self.muted = muted
        self.played: list[AudioCue] = []
        self.targets: list[tuple[AudioCue, str | None]] = []
        self.ambience: list[tuple[object, ...]] = []
        self.scene: object = None

    def prepare(self) -> bool:
        return self.available

    def play(self, cue: AudioCue) -> str:
        self.played.append(cue)
        self.targets.append((cue, getattr(self.scene, "target_qualified_id", None)))
        return "played"

    def near(self, qualified_id: str) -> int:
        return self.targets.count((AudioCue.OBJECT_NEAR, qualified_id))

    def start_ambience(self, cue: AudioCue = AudioCue.AMBIENT_MOON_MEADOW) -> str:
        self.ambience.append(("start", cue))
        return "started"

    def stop_ambience(self, fade_ms: int = 600) -> None:
        self.ambience.append(("stop",))

    def update(self, dt: float) -> None:
        pass

    def toggle_mute(self) -> bool:
        self.muted = not self.muted
        return self.muted


def _manager(backend: FakeBackend | None = None, **options: object) -> AudioManager:
    options.setdefault("clock", FakeClock())
    return AudioManager(FakeBackend() if backend is None else backend, **options)  # type: ignore[arg-type]


def _scene(mission_id: str, audio: object = None, renderer: object = None):  # type: ignore[no-untyped-def]
    roots = PACKAGES.get(mission_id, S02_PACKAGES)
    planned = plan_local_classroom_trail(roots, player_qualified_id=NOVA_QUALIFIED_ID)
    assert planned.is_planned, planned.issues
    scene = create_classroom_trail_scene(
        renderer if renderer is not None else ArtRenderer(),
        planned.plan,
        mission_id=mission_id,
        audio=audio,
    )
    scene.enter()
    return scene


def _frames(scene, count: int = 1, directions=STILL, interact=NO_E, clock=None) -> None:  # type: ignore[no-untyped-def]
    for _ in range(count):
        scene.update(directions, interact, STEP)
        if clock is not None:
            clock.now += STEP


def _entity(scene, qualified_id: str):  # type: ignore[no-untyped-def]
    for item in (*scene.objects, *scene.npcs):
        if item.qualified_id == qualified_id:
            return item.world_object if hasattr(item, "world_object") else item.character
    raise AssertionError(qualified_id)


def _visit(scene, qualified_id: str, clock=None) -> None:  # type: ignore[no-untyped-def]
    """Stand on *qualified_id* (a teleport, not a walk) and press E once."""
    target = _entity(scene, qualified_id)
    scene.player.move(target.x - scene.player.x_float, target.y - scene.player.y_float, ANYWHERE)
    _frames(scene, 1, clock=clock)
    assert scene.target_qualified_id == qualified_id
    _frames(scene, 1, interact=PRESS_E, clock=clock)


def _effects(sink: RecordingSink) -> list[AudioCue]:
    return [cue for cue in sink.played if cue is not AudioCue.FOOTSTEP_GRASS]


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


def test_audio_is_explicitly_allow_listed_for_m02_m03_m04_only() -> None:
    assert {
        mission_id for mission_id, policy in MISSION_PRESENTATIONS.items() if policy.meadow_audio
    } == {MISSION_02_ID, MISSION_03_ID, MISSION_04_ID}
    # M01 wears the Moon Meadow but stays silent.
    m01 = mission_presentation(MISSION_01_ID)
    assert m01 is not None and not m01.meadow_audio
    for mission_id in LATER_MISSIONS:
        assert mission_presentation(mission_id) is None


@pytest.mark.parametrize("mission_id", (MISSION_01_ID, None, *LATER_MISSIONS))
def test_m01_and_m05_plus_stay_silent_even_with_a_manager(mission_id: str | None) -> None:
    backend = FakeBackend()
    manager = _manager(backend)
    renderer = ArtRenderer()
    scene = _scene(mission_id, manager, renderer)
    _frames(scene, 90, RIGHT)
    for item in scene.objects:
        _visit(scene, item.qualified_id)
    renderer.operations.clear()
    scene.render()
    assert scene.toggle_audio_mute() is None
    scene.exit()
    assert backend.calls == [] and backend.open_count == 0, "the mixer is never even opened"
    assert manager.muted is False
    assert not any(
        kind == "text" and str(values[0]).startswith("Audio:")
        for kind, values in renderer.operations
    )


def test_m02_voices_compass_pixel_lantern_and_completion() -> None:
    sink = RecordingSink()
    scene = _scene(MISSION_02_ID, sink)
    assert sink.ambience == [("start", AudioCue.AMBIENT_MOON_MEADOW)]
    _visit(scene, MOON_COMPASS_QUALIFIED_ID)
    _visit(scene, PIXEL_QUALIFIED_ID)
    _visit(scene, CRYSTAL_LANTERN_QUALIFIED_ID)
    assert scene.mission_is_complete
    _frames(scene, 600)
    effects = [cue for cue in _effects(sink) if cue is not AudioCue.OBJECT_NEAR]
    assert effects == [
        AudioCue.COMPASS_MAGIC,
        AudioCue.PIXEL_GREETING,
        AudioCue.LANTERN_CHIME,
        AudioCue.MISSION_COMPLETE,
    ]
    assert sink.ambience == [("start", AudioCue.AMBIENT_MOON_MEADOW)], "one loop, never restarted"
    scene.exit()
    assert sink.ambience[-1] == ("stop",)


def test_m03_voices_its_aliased_compass_and_completion() -> None:
    sink = RecordingSink()
    scene = _scene(MISSION_03_ID, sink)
    _visit(scene, S03_MOON_COMPASS_QUALIFIED_ID)
    _frames(scene, 600)
    assert scene.mission_is_complete
    assert [cue for cue in _effects(sink) if cue is not AudioCue.OBJECT_NEAR] == [
        AudioCue.COMPASS_MAGIC,
        AudioCue.MISSION_COMPLETE,
    ]
    assert sink.ambience == [("start", AudioCue.AMBIENT_MOON_MEADOW)]


def test_m04_voices_the_guide_and_completion_but_not_an_untouched_lantern() -> None:
    sink = RecordingSink()
    scene = _scene(MISSION_04_ID, sink)
    _visit(scene, MOONLIT_GUIDE_QUALIFIED_ID)
    _frames(scene, 600)
    assert scene.mission_is_complete
    effects = [cue for cue in _effects(sink) if cue is not AudioCue.OBJECT_NEAR]
    assert effects == [AudioCue.NPC_TALK, AudioCue.MISSION_COMPLETE]
    assert AudioCue.LANTERN_CHIME not in sink.played


def test_m04_lantern_chimes_only_when_it_is_actually_inspected() -> None:
    sink = RecordingSink()
    scene = _scene(MISSION_04_ID, sink)
    _visit(scene, CRYSTAL_LANTERN_QUALIFIED_ID)
    assert AudioCue.LANTERN_CHIME in sink.played
    assert AudioCue.MISSION_COMPLETE not in sink.played


# ---------------------------------------------------------------------------
# Event truth
# ---------------------------------------------------------------------------


def test_each_interaction_requests_its_cue_exactly_once() -> None:
    sink = RecordingSink()
    scene = _scene(MISSION_02_ID, sink)
    _visit(scene, MOON_COMPASS_QUALIFIED_ID)
    _frames(scene, 300)
    assert sink.played.count(AudioCue.COMPASS_MAGIC) == 1, "standing near it adds nothing"
    _frames(scene, 1, interact=PRESS_E)
    assert sink.played.count(AudioCue.COMPASS_MAGIC) == 2, "a second press is a second event"


def test_npc_cue_fires_once_per_conversation_start() -> None:
    sink = RecordingSink()
    scene = _scene(MISSION_04_ID, sink)
    _visit(scene, MOONLIT_GUIDE_QUALIFIED_ID)
    _frames(scene, 400)
    assert sink.played.count(AudioCue.NPC_TALK) == 1
    _frames(scene, 1, interact=PRESS_E)
    assert sink.played.count(AudioCue.NPC_TALK) == 2


def test_multi_line_conversation_chimes_only_on_its_first_line() -> None:
    audio = TrailAudio(MISSION_04_ID, RecordingSink())

    class Character:
        name = "Luma"

    class NPC:
        qualified_id = "pkg:luma"
        character = Character()
        conversation_lines = ("Hello!", "The path is north.", "Good luck.")

    class View:
        objects = ()
        npcs = (NPC(),)
        feedback_message = "Luma: Hello!"

    assert audio._starts_conversation(View(), NPC()) is True
    View.feedback_message = "Luma: The path is north."
    assert audio._starts_conversation(View(), NPC()) is False


def test_mission_complete_plays_once_on_the_transition_and_never_replays() -> None:
    sink = RecordingSink()
    scene = _scene(MISSION_04_ID, sink)
    _frames(scene, 120)
    assert AudioCue.MISSION_COMPLETE not in sink.played
    _visit(scene, MOONLIT_GUIDE_QUALIFIED_ID)
    assert AudioCue.MISSION_COMPLETE not in sink.played, "it waits a beat after the greeting"
    _frames(scene, round(trail_audio_module.COMPLETE_DELAY / STEP) + 1)
    assert sink.played.count(AudioCue.MISSION_COMPLETE) == 1
    for _ in range(5):
        _frames(scene, 120)
        _frames(scene, 1, interact=PRESS_E)
    assert sink.played.count(AudioCue.MISSION_COMPLETE) == 1


def _step_away(scene) -> tuple[float, float]:  # type: ignore[no-untyped-def]
    """Teleport out of range of everything; return the offset to come back."""
    for offset in ((0, 300), (0, -300), (300, 0), (-300, 0), (300, 300), (-300, -300)):
        scene.player.move(*offset, ANYWHERE)
        _frames(scene, 2)
        if scene.target_qualified_id is None:
            return (-offset[0], -offset[1])
        scene.player.move(-offset[0], -offset[1], ANYWHERE)
        _frames(scene, 2)
    raise AssertionError("no empty spot nearby")


def test_near_glint_is_once_per_approach_and_stops_after_the_visit() -> None:
    sink = RecordingSink()
    scene = _scene(MISSION_02_ID, sink)
    sink.scene = scene
    compass = _entity(scene, MOON_COMPASS_QUALIFIED_ID)
    scene.player.move(compass.x - scene.player.x_float, compass.y - scene.player.y_float, ANYWHERE)
    _frames(scene, 600)
    assert scene.target_qualified_id == MOON_COMPASS_QUALIFIED_ID
    assert sink.near(MOON_COMPASS_QUALIFIED_ID) == 1, "standing near it never repeats"
    # Leave and come straight back: still within the re-arm window.
    back = _step_away(scene)
    scene.player.move(*back, ANYWHERE)
    _frames(scene, 2)
    assert scene.target_qualified_id == MOON_COMPASS_QUALIFIED_ID
    assert sink.near(MOON_COMPASS_QUALIFIED_ID) == 1
    _frames(scene, 1, interact=PRESS_E)
    back = _step_away(scene)
    _frames(scene, round(trail_audio_module.NEAR_REARM / STEP) + 10)
    scene.player.move(*back, ANYWHERE)
    _frames(scene, 2)
    assert scene.target_qualified_id == MOON_COMPASS_QUALIFIED_ID
    assert sink.near(MOON_COMPASS_QUALIFIED_ID) == 1, "a visited target no longer glints"


def test_near_glint_re_arms_for_a_target_still_waiting() -> None:
    sink = RecordingSink()
    scene = _scene(MISSION_02_ID, sink)
    sink.scene = scene
    compass = _entity(scene, MOON_COMPASS_QUALIFIED_ID)
    scene.player.move(compass.x - scene.player.x_float, compass.y - scene.player.y_float, ANYWHERE)
    _frames(scene, 2)
    back = _step_away(scene)
    _frames(scene, round(trail_audio_module.NEAR_REARM / STEP) + 10)
    scene.player.move(*back, ANYWHERE)
    _frames(scene, 2)
    assert sink.near(MOON_COMPASS_QUALIFIED_ID) == 2


def test_footsteps_follow_real_movement_and_stop_when_nova_stops() -> None:
    sink = RecordingSink()
    scene = _scene(MISSION_02_ID, sink)
    start = scene.player.x_float
    _frames(scene, 120, RIGHT)
    travelled = scene.player.x_float - start
    steps = sink.played.count(AudioCue.FOOTSTEP_GRASS)
    assert travelled > 200
    assert steps == int((travelled + STEP_LENGTH / 2) // STEP_LENGTH)
    assert steps < 120 / 4, "far fewer steps than frames"
    _frames(scene, 300)
    assert sink.played.count(AudioCue.FOOTSTEP_GRASS) == steps, "silent while standing still"


def test_footsteps_are_rate_limited_by_the_manager() -> None:
    clock = FakeClock()
    backend = FakeBackend()
    manager = _manager(backend, clock=clock)
    manager.prepare()
    outcomes = []
    for _ in range(60):
        outcomes.append(manager.play(AudioCue.FOOTSTEP_GRASS))
        clock.now += STEP
    played = outcomes.count("played")
    assert played <= 60 * STEP / CUES[AudioCue.FOOTSTEP_GRASS].cooldown + 1
    assert {call[1] for call in backend.plays()} == {manager_module.FOOTSTEP_CHANNEL}
    sounds = [call[2] for call in backend.plays()]
    assert sounds[0] != sounds[1], "the two grass variants alternate"


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


def test_manager_opens_the_mixer_once_and_decodes_each_sound_once() -> None:
    backend = FakeBackend()
    catalog = CountingCatalog()
    manager = _manager(backend, catalog=catalog)
    assert manager.prepare() and manager.prepare()
    for cue in AudioCue:
        manager.play(cue)
    manager.start_ambience()
    assert backend.open_count == 1
    unique_assets = {asset for spec in CUES.values() for asset in spec.assets}
    assert sorted(catalog.reads) == sorted(unique_assets), "each file read exactly once"
    assert len(backend.loads) == len(unique_assets) == len(manager.loaded_sounds)


def test_volumes_come_from_the_central_cue_table() -> None:
    backend = FakeBackend()
    manager = _manager(backend)
    manager.prepare()
    assert sorted(backend.loads) == sorted(
        spec.volume for spec in CUES.values() for _asset in spec.assets
    )


@pytest.mark.parametrize("opens", (False, "raise"))
def test_missing_mixer_fails_silent_and_logs_once(
    opens: object, caplog: pytest.LogCaptureFixture
) -> None:
    backend = FakeBackend(opens=opens)
    manager = _manager(backend)
    with caplog.at_level(logging.WARNING, logger="explore-studio.audio"):
        assert manager.start_ambience() == "unavailable"
        for _ in range(50):
            for cue in AudioCue:
                manager.play(cue)
        manager.update(STEP)
        manager.toggle_mute()
        manager.stop_ambience()
        manager.shutdown()
    assert backend.open_count == 1, "never retried"
    assert manager.available is False
    assert len(caplog.records) == 1, [record.getMessage() for record in caplog.records]
    assert backend.plays() == []


def test_no_backend_at_all_is_silent() -> None:
    manager = AudioManager(None)
    assert manager.prepare() is False
    assert manager.play(AudioCue.COMPASS_MAGIC) == "unavailable"
    assert manager.start_ambience() == "unavailable"


def test_missing_and_corrupt_assets_only_silence_their_own_cue(tmp_path: Path) -> None:
    shutil.copytree(TRUSTED_AUDIO_ROOT, tmp_path / "audio")
    root = tmp_path / "audio"
    manifest = json.loads((root / "manifest.json").read_text())["assets"]
    (root / manifest["sfx/compass-magic"]["file"]).unlink()
    lantern = root / manifest["sfx/lantern-chime"]["file"]
    lantern.write_bytes(lantern.read_bytes()[:-100] + b"\x00" * 100)
    backend = FakeBackend(fail_loads=(manifest["sfx/npc-talk"]["sha256"],))
    manager = _manager(backend, catalog=TrustedAudioCatalog(root))
    assert manager.prepare()
    assert manager.play(AudioCue.COMPASS_MAGIC) == "missing"
    assert manager.play(AudioCue.LANTERN_CHIME) == "missing", "digest mismatch reads as missing"
    assert manager.play(AudioCue.NPC_TALK) == "missing", "a decode failure reads as missing"
    assert manager.play(AudioCue.PIXEL_GREETING) == "played"
    assert manager.start_ambience() == "started"


def test_unreadable_manifest_means_silence_not_a_crash(tmp_path: Path) -> None:
    (tmp_path / "manifest.json").write_text("{not json")
    manager = _manager(FakeBackend(), catalog=TrustedAudioCatalog(tmp_path))
    assert manager.prepare()
    assert manager.play(AudioCue.COMPASS_MAGIC) == "missing"
    assert manager.start_ambience() == "missing"


def test_cooldown_drops_request_storms() -> None:
    clock = FakeClock()
    manager = _manager(clock=clock)
    assert manager.play(AudioCue.COMPASS_MAGIC) == "played"
    assert manager.play(AudioCue.COMPASS_MAGIC) == "cooldown"
    clock.now += CUES[AudioCue.COMPASS_MAGIC].cooldown + 0.01
    assert manager.play(AudioCue.COMPASS_MAGIC) == "played"


def test_channels_are_fixed_and_bounded_under_load() -> None:
    clock = FakeClock()
    backend = FakeBackend()
    manager = _manager(backend, clock=clock)
    manager.start_ambience()
    backend.busy = set(manager_module.EFFECT_CHANNELS)
    for _ in range(200):
        for cue in AudioCue:
            manager.play(cue)
        clock.now += 1.0
    used = {call[1] for call in backend.plays()}
    assert used <= set(range(manager_module.CHANNEL_COUNT))
    assert backend.calls[0] == ("open", manager_module.CHANNEL_COUNT)
    assert len(manager.events) == manager_module.MAX_EVENTS


def test_ambience_starts_once_and_never_stacks() -> None:
    backend = FakeBackend()
    manager = _manager(backend)
    assert manager.start_ambience() == "started"
    for _ in range(100):
        assert manager.start_ambience() == "already-playing"
    loops = backend.plays(manager_module.AMBIENCE_CHANNEL)
    assert len(loops) == 1 and loops[0][3] is True
    assert manager.play(AudioCue.AMBIENT_MOON_MEADOW) == "not-a-one-shot"


def test_ambience_fades_in_and_out() -> None:
    backend = FakeBackend()
    manager = _manager(backend)
    manager.start_ambience()
    for _ in range(200):
        manager.update(STEP)
    levels = backend.volumes[manager_module.AMBIENCE_CHANNEL]
    assert levels[0] == 0.0 and levels[-1] == 1.0
    assert levels == sorted(levels), "a steady rise"
    assert len(levels) <= round(1.5 / STEP) + 2, "no volume call once it is up"
    manager.stop_ambience()
    assert backend.calls[-1] == (
        "stop",
        manager_module.AMBIENCE_CHANNEL,
        manager_module.AMBIENCE_FADE_OUT_MS,
    )
    assert manager.ambience is None


def test_mute_silences_at_once_and_unmute_never_restarts_the_loop() -> None:
    clock = FakeClock()
    backend = FakeBackend()
    manager = _manager(backend, clock=clock)
    manager.start_ambience()
    for _ in range(120):
        manager.update(STEP)
    assert manager.toggle_mute() is True
    stopped = {call[1] for call in backend.calls if call[0] == "stop"}
    assert stopped == {manager_module.FOOTSTEP_CHANNEL, *manager_module.EFFECT_CHANNELS}
    assert backend.volumes[manager_module.AMBIENCE_CHANNEL][-1] == 0.0
    plays_before = len(backend.plays())
    for cue in AudioCue:
        manager.play(cue)
    assert len(backend.plays()) == plays_before, "no new sound while muted"
    clock.now += 1.0
    assert manager.toggle_mute() is False
    assert backend.volumes[manager_module.AMBIENCE_CHANNEL][-1] > 0
    assert len(backend.plays(manager_module.AMBIENCE_CHANNEL)) == 1, "the loop never restarted"
    assert backend.plays()[-1][1] in manager_module.EFFECT_CHANNELS, "a tiny unmute tick"
    clock.now += 1.0
    assert manager.play(AudioCue.COMPASS_MAGIC) == "played"


def test_rapid_mute_toggling_stays_bounded() -> None:
    clock = FakeClock()
    backend = FakeBackend()
    manager = _manager(backend, clock=clock)
    manager.start_ambience()
    for _ in range(500):
        manager.toggle_mute()
        clock.now += STEP
    assert manager.muted is False
    assert len(backend.plays(manager_module.AMBIENCE_CHANNEL)) == 1
    ticks = [call for call in backend.plays() if call[1] != manager_module.AMBIENCE_CHANNEL]
    assert len(ticks) <= 500 * STEP / CUES[AudioCue.UI_MUTE_TOGGLE].cooldown + 2


def test_muted_at_startup_keeps_the_loop_silent_until_unmuted() -> None:
    backend = FakeBackend()
    manager = _manager(backend, muted=True)
    assert manager.start_ambience() == "started"
    for _ in range(120):
        manager.update(STEP)
    assert set(backend.volumes[manager_module.AMBIENCE_CHANNEL]) == {0.0}
    assert manager.play(AudioCue.COMPASS_MAGIC) == "muted"
    manager.set_muted(False)
    assert backend.volumes[manager_module.AMBIENCE_CHANNEL][-1] > 0


def test_shutdown_is_idempotent_and_silences_later_requests() -> None:
    backend = FakeBackend()
    manager = _manager(backend)
    manager.start_ambience()
    manager.shutdown()
    manager.shutdown()
    assert backend.calls.count(("close",)) == 1
    assert manager.available is False
    assert manager.play(AudioCue.COMPASS_MAGIC) == "unavailable"
    assert manager.loaded_sounds == ()


@pytest.mark.parametrize(
    ("value", "mode"),
    (
        ("", AudioMode.ON),
        ("on", AudioMode.ON),
        ("MUTED", AudioMode.MUTED),
        (" off ", AudioMode.OFF),
        ("loud", AudioMode.ON),
    ),
)
def test_audio_mode_from_environment(value: str, mode: AudioMode) -> None:
    assert audio_mode_from_environment({AUDIO_ENV_VAR: value}) is mode
    assert audio_mode_from_environment({}) is AudioMode.ON


# ---------------------------------------------------------------------------
# Scene integration, indicator, and gameplay parity
# ---------------------------------------------------------------------------


def _indicator(renderer: ArtRenderer) -> list[tuple[object, ...]]:
    return [
        values
        for kind, values in renderer.operations
        if kind == "text" and str(values[0]).startswith("Audio:")
    ]


def test_indicator_shows_state_and_mute_toggles_from_the_scene() -> None:
    clock = FakeClock()
    manager = _manager(FakeBackend(), clock=clock)
    renderer = ArtRenderer()
    scene = _scene(MISSION_02_ID, manager, renderer)
    _frames(scene, 2, clock=clock)
    renderer.operations.clear()
    scene.render()
    (shown,) = _indicator(renderer)
    assert shown[0] == trail_audio_module.INDICATOR_ON
    assert scene.toggle_audio_mute() is True
    renderer.operations.clear()
    scene.render()
    (shown,) = _indicator(renderer)
    assert shown[0] == trail_audio_module.INDICATOR_MUTED
    text, x, y, _color, size = shown
    width, height = renderer.measure_text(text, size)
    assert x >= 0 and x + width <= 960 and y >= 590 and y + height <= 640
    assert scene.toggle_audio_mute() is False


@pytest.mark.parametrize("mission_id", (MISSION_02_ID, MISSION_03_ID, MISSION_04_ID))
def test_no_audio_or_failed_mixer_renders_exactly_like_before(mission_id: str) -> None:
    def operations(audio: object) -> list[tuple[str, tuple[object, ...]]]:
        renderer = ArtRenderer()
        scene = _scene(mission_id, audio, renderer)
        _frames(scene, 30, RIGHT)
        renderer.operations.clear()
        scene.render()
        return renderer.operations

    plain = operations(None)
    assert operations(_manager(FakeBackend(opens=False))) == plain
    assert operations(_manager(FakeBackend(opens="raise"))) == plain
    with_audio = operations(_manager(FakeBackend()))
    assert [op for op in with_audio if op not in plain] != []
    assert [op for op in with_audio if not _is_indicator_op(op)] == plain


def _is_indicator_op(operation: tuple[str, tuple[object, ...]]) -> bool:
    kind, values = operation
    if kind == "text":
        return str(values[0]).startswith("Audio:")
    return kind == "translucent" and values[1:4] == (trail_audio_module._INDICATOR_PANEL, 120, 8)


def _gameplay_trace(mission_id: str, audio: object) -> list[object]:
    clock = getattr(audio, "_clock", None)
    scene = _scene(mission_id, audio)
    targets = [item.qualified_id for item in (*scene.objects, *scene.npcs)]
    script = (
        [RIGHT] * 40
        + [DirectionalInput(up=True)] * 30
        + [DirectionalInput(left=True, down=True)] * 50
        + [STILL] * 10
    )
    trace: list[object] = []

    def record() -> None:
        trace.append(
            (
                scene.player.x_float,
                scene.player.y_float,
                scene.target_qualified_id,
                scene.visited_qualified_ids,
                scene.spoken_npc_ids,
                scene.mission_is_complete,
                scene.feedback_message,
                tuple(
                    (entity.x, entity.y, entity.width, entity.height)
                    for entity in (_entity(scene, qualified_id) for qualified_id in targets)
                ),
            )
        )

    for index, directions in enumerate(script):
        scene.update(directions, PRESS_E if index % 17 == 0 else NO_E, STEP)
        if isinstance(clock, FakeClock):
            clock.now += STEP
        record()
    for qualified_id in targets:
        _visit(scene, qualified_id, clock if isinstance(clock, FakeClock) else None)
        record()
        _frames(scene, 45, clock=clock if isinstance(clock, FakeClock) else None)
        if qualified_id == targets[0] and audio is not None and hasattr(audio, "toggle_mute"):
            scene.toggle_audio_mute()
        record()
    scene.exit()
    return trace


@pytest.mark.parametrize("mission_id", (MISSION_02_ID, MISSION_03_ID, MISSION_04_ID))
def test_gameplay_is_identical_with_audio_muted_or_unavailable(mission_id: str) -> None:
    silent = _gameplay_trace(mission_id, None)
    enabled_backend = FakeBackend()
    enabled = _gameplay_trace(mission_id, _manager(enabled_backend))
    muted = _gameplay_trace(mission_id, _manager(FakeBackend(), muted=True))
    unavailable = _gameplay_trace(mission_id, _manager(FakeBackend(opens=False)))
    recording = _gameplay_trace(mission_id, RecordingSink())
    assert enabled == silent
    assert muted == silent
    assert unavailable == silent
    assert recording == silent
    assert any(step[5] for step in silent), "the script completes the mission"
    assert enabled_backend.plays(), "and audio really played while it did"


def test_long_session_stays_bounded() -> None:
    clock = FakeClock()
    backend = FakeBackend()
    catalog = CountingCatalog()
    manager = _manager(backend, clock=clock, catalog=catalog)
    scene = _scene(MISSION_04_ID, manager)
    for second in range(60):
        directions = (RIGHT, DirectionalInput(left=True), STILL)[second % 3]
        _frames(scene, 60, directions, clock=clock)
        _frames(scene, 1, interact=PRESS_E, clock=clock)
    unique_assets = {asset for spec in CUES.values() for asset in spec.assets}
    assert len(catalog.reads) == len(unique_assets), "no file I/O after startup"
    assert backend.open_count == 1
    assert {call[1] for call in backend.plays()} <= set(range(manager_module.CHANNEL_COUNT))
    assert len(backend.plays(manager_module.AMBIENCE_CHANNEL)) == 1
    assert len(manager.events) <= manager_module.MAX_EVENTS
    assert len(scene._audio._last_near) <= len(scene.objects) + len(scene.npcs)


def test_scene_exit_fades_the_ambience_once() -> None:
    backend = FakeBackend()
    manager = _manager(backend)
    scene = _scene(MISSION_03_ID, manager)
    scene.exit()
    scene.exit()
    fades = [call for call in backend.calls if call[0] == "stop"]
    assert fades == [("stop", manager_module.AMBIENCE_CHANNEL, manager_module.AMBIENCE_FADE_OUT_MS)]


def test_audio_layer_failure_never_reaches_gameplay(caplog: pytest.LogCaptureFixture) -> None:
    class ExplodingSink(RecordingSink):
        def play(self, cue: AudioCue) -> str:
            raise RuntimeError("boom")

        def update(self, dt: float) -> None:
            raise RuntimeError("boom")

    with caplog.at_level(logging.ERROR, logger="explore-studio.audio.trail"):
        scene = _scene(MISSION_02_ID, ExplodingSink())
        for _ in range(3):
            _visit(scene, MOON_COMPASS_QUALIFIED_ID)
            _frames(scene, 30, RIGHT)
    assert scene.visited_qualified_ids == {MOON_COMPASS_QUALIFIED_ID}
    assert len(caplog.records) == 1


# ---------------------------------------------------------------------------
# Platform: the M key and the real mixer
# ---------------------------------------------------------------------------


def test_m_key_toggles_audio_and_e_still_interacts() -> None:
    import pygame

    from engine._config import Config
    from engine._platform import Platform

    platform = Platform(Config())
    platform.initialize()
    try:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m))
        events = platform.poll_frame_events()
        assert events.audio_toggle_pressed is True
        assert events.interaction_pressed is False
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        events = platform.poll_frame_events()
        assert events.audio_toggle_pressed is False
        assert events.interaction_pressed is True
    finally:
        platform.shutdown()


def test_real_mixer_loads_every_trusted_sound(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Pygame backend under SDL's dummy audio driver (no speakers needed)."""
    import pygame

    from engine._platform import PygameAudioBackend

    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.quit()
    try:
        manager = AudioManager(PygameAudioBackend())
        if not manager.prepare():
            pytest.skip("this Pygame build has no mixer")
        assert pygame.mixer.get_num_channels() == manager_module.CHANNEL_COUNT
        unique_assets = {asset for spec in CUES.values() for asset in spec.assets}
        assert set(manager.loaded_sounds) == unique_assets
        assert manager.start_ambience() == "started"
        assert manager.play(AudioCue.MISSION_COMPLETE) == "played"
        assert manager.toggle_mute() is True
        assert manager.toggle_mute() is False
        manager.stop_ambience()
        manager.shutdown()
    finally:
        pygame.quit()


def test_real_mixer_does_not_retry_after_pygame_init_failed_to_open_audio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pygame

    from engine._platform import PygameAudioBackend

    monkeypatch.setenv("SDL_AUDIODRIVER", "no-such-audio-driver")
    pygame.quit()
    pygame.init()
    try:
        assert not pygame.mixer.get_init()
        tries: list[object] = []
        monkeypatch.setattr(pygame.mixer, "init", lambda *a, **k: tries.append(a))
        manager = AudioManager(PygameAudioBackend())
        assert manager.prepare() is False
        assert manager.play(AudioCue.COMPASS_MAGIC) == "unavailable"
        assert tries == []
    finally:
        pygame.quit()


def test_live_runner_wires_mute_and_shuts_audio_down(monkeypatch: pytest.MonkeyPatch) -> None:
    from engine._platform import FrameEvents, Platform
    from explore.packages import classroom_trail

    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.setenv(AUDIO_ENV_VAR, "on")
    created: list[AudioManager] = []
    original_init = AudioManager.__init__

    def recording_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        original_init(self, *args, **kwargs)
        created.append(self)

    script = iter(
        [FrameEvents(), FrameEvents(audio_toggle_pressed=True), FrameEvents(quit_requested=True)]
    )
    monkeypatch.setattr(AudioManager, "__init__", recording_init)
    monkeypatch.setattr(Platform, "poll_frame_events", lambda self: next(script))
    planned = plan_local_classroom_trail(S04_PACKAGES, player_qualified_id=NOVA_QUALIFIED_ID)
    classroom_trail.run_classroom_trail(planned.plan, mission_id=MISSION_04_ID)
    (manager,) = created
    if ("ambient_moon_meadow", "unavailable") in manager.events:
        pytest.skip("this Pygame build has no mixer")
    assert ("ambient_moon_meadow", "started") in manager.events
    assert manager.muted is True, "M muted the live Trail"
    assert manager.available is False, "shut down with the window"


def test_audio_off_never_creates_a_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    from engine._platform import FrameEvents, Platform
    from explore.packages import classroom_trail

    monkeypatch.setenv(AUDIO_ENV_VAR, "off")
    seen: list[object] = []
    original = classroom_trail.create_classroom_trail_scene

    def spy(*args, **kwargs):  # type: ignore[no-untyped-def]
        seen.append(kwargs.get("audio"))
        return original(*args, **kwargs)

    monkeypatch.setattr(classroom_trail, "create_classroom_trail_scene", spy)
    monkeypatch.setattr(
        Platform, "poll_frame_events", lambda self: FrameEvents(quit_requested=True)
    )
    planned = plan_local_classroom_trail(S02_PACKAGES, player_qualified_id=NOVA_QUALIFIED_ID)
    classroom_trail.run_classroom_trail(planned.plan, mission_id=MISSION_02_ID)
    assert seen == [None]


# ---------------------------------------------------------------------------
# Trusted sounds
# ---------------------------------------------------------------------------


def _manifest() -> dict[str, dict[str, object]]:
    return json.loads((TRUSTED_AUDIO_ROOT / "manifest.json").read_text())["assets"]


def _samples(path: Path) -> list[int]:
    with wave.open(str(path), "rb") as handle:
        data = handle.readframes(handle.getnframes())
    return [int.from_bytes(data[i : i + 2], "little", signed=True) for i in range(0, len(data), 2)]


def test_every_cue_has_a_listed_sound_with_a_matching_digest_and_format() -> None:
    manifest = _manifest()
    assert {asset for spec in CUES.values() for asset in spec.assets} == set(manifest)
    assert set(CUES) == set(AudioCue)
    for asset_id, entry in manifest.items():
        path = (TRUSTED_AUDIO_ROOT / str(entry["file"])).resolve()
        assert path.is_relative_to(TRUSTED_AUDIO_ROOT.resolve())
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], asset_id
        with wave.open(str(path), "rb") as handle:
            assert handle.getframerate() == entry["sample_rate"] == 22050
            assert handle.getnchannels() == entry["channels"] == 1
            assert handle.getsampwidth() == entry["sample_width"] == 2
            assert handle.getnframes() == entry["frames"]
        assert TrustedAudioCatalog().read_verified(asset_id) == data


def test_sounds_are_short_small_and_classroom_quiet() -> None:
    manifest = _manifest()
    total = sum((TRUSTED_AUDIO_ROOT / str(e["file"])).stat().st_size for e in manifest.values())
    assert total < 800 * 1024
    for asset_id, entry in manifest.items():
        seconds = int(entry["frames"]) / int(entry["sample_rate"])  # type: ignore[call-overload]
        if entry["loop"]:
            assert asset_id == "ambient/moon-meadow" and seconds == 10.0
        else:
            assert seconds <= 2.0, asset_id
    assert int(manifest["sfx/mission-complete"]["frames"]) / 22050 <= 2.0  # type: ignore[call-overload]
    # Worst case: every channel at its loudest cue's peak at once stays under full scale.
    peaks = {
        asset_id: max(abs(sample) for sample in _samples(TRUSTED_AUDIO_ROOT / str(entry["file"])))
        / 32767
        for asset_id, entry in manifest.items()
    }
    loudest = {
        bus: max(
            peaks[asset] * spec.volume
            for spec in CUES.values()
            if spec.bus is bus
            for asset in spec.assets
        )
        for bus in CueBus
    }
    assert loudest[CueBus.AMBIENCE] + loudest[CueBus.FOOTSTEPS] + 4 * loudest[CueBus.EFFECTS] < 1.0
    volumes = {cue: spec.volume for cue, spec in CUES.items()}
    assert max(volumes, key=volumes.__getitem__) is AudioCue.MISSION_COMPLETE
    quiet = (AudioCue.AMBIENT_MOON_MEADOW, AudioCue.FOOTSTEP_GRASS, AudioCue.OBJECT_NEAR)
    assert max(volumes[cue] for cue in quiet) < min(
        volumes[cue] for cue in AudioCue if cue not in (*quiet, AudioCue.UI_MUTE_TOGGLE)
    )


def test_ambience_loop_has_no_seam() -> None:
    samples = _samples(TRUSTED_AUDIO_ROOT / "ambient/moon-meadow.wav")
    steps = [abs(b - a) for a, b in zip(samples, samples[1:], strict=False)]
    typical = sorted(steps)[len(steps) // 2]
    assert abs(samples[0] - samples[-1]) <= max(steps) and abs(samples[0] - samples[-1]) < 8 * max(
        typical, 1
    )


def test_sounds_rebuild_byte_for_byte(tmp_path: Path) -> None:
    from scripts import build_trail_audio

    rebuilt = build_trail_audio.build(tmp_path)
    committed = json.loads((TRUSTED_AUDIO_ROOT / "manifest.json").read_text())
    assert rebuilt == committed
    for entry in committed["assets"].values():
        assert (tmp_path / entry["file"]).read_bytes() == (
            TRUSTED_AUDIO_ROOT / entry["file"]
        ).read_bytes()
