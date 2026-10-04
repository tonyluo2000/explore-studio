# Moon Meadow Trail audio v0.1

This tranche adds quiet, optional sound to the frozen S02-S04 (M02-M04) Moon
Meadow: a night-meadow ambience, soft footsteps, and restrained cues for the
Compass, Pixel, the Moonlit Guide, the Crystal Lantern, and mission complete.
It is presentation only, like the [art and VFX layer](s02-game-art-and-vfx-v0.1.md).

After this tranche the audio direction is frozen too. Later changes are limited
to correctness bugs, volume or readability fixes, and lesson-specific semantic
cues that a future session actually needs.

## Contract

Unchanged:

- gameplay, mission semantics, and completion
- movement speed, hitboxes, interaction range, and entity coordinates
- every visual layer: the backdrop, Nova, Pixel, the Compass, the Guide,
  lighting, ambience visuals, and the HUD design
- lesson content and the Student API

Audio never decides anything. Every cue has a visual twin, and the gameplay
trace is identical with audio on, muted, or unavailable (see the tests).
There is no voice acting, text-to-speech, streaming, network audio, or
procedural music.

## Architecture

| Piece | Role |
|---|---|
| `engine/audio/_cues.py` | `AudioCue`: the semantic cue names, and `CUES`, the **one** mix table (sound, volume, bus, cooldown). |
| `engine/audio/_manager.py` | `AudioManager`: opens the mixer once, decodes each sound once, plays cues on six fixed channels, applies cooldowns and mute, and falls back to silence. |
| `engine/audio/_trail_audio.py` | `TrailAudio`: watches the Trail scene after each update and turns real state transitions into cues. It also draws the mute indicator. |
| `engine/assets/_trusted_audio.py` | `TrustedAudioCatalog`: plays only the manifest-listed, digest-verified WAVs. |
| `engine/_platform.py` | `PygameAudioBackend` (the only Pygame mixer code) and the **M** key in `FrameEvents`. |
| `scripts/build_trail_audio.py` | Synthesizes every sound and writes the manifest. |

Code that presents the Trail asks for a cue, such as "the Compass was used". It
never names a file. `TrailAudio` is built by the Trail scene next to
`TrailPresentation` and has the same rules: it is read-only, mission-gated,
bounded, and every layer is guarded.

Audio exists only when the live runner (`explore-package trail`) creates an
`AudioManager`. Tests, visual-proof captures, and other callers get a silent
Trail unless they pass one in.

### Policy

Eligibility is the explicit `meadow_audio` flag on `MissionPresentation`
(`engine/rendering/_mission_presentation.py`):

| Mission | Audio |
|---|---|
| M01 | None. The mixer is never opened. |
| M02 | Ambience, footsteps, near glint, Compass, Pixel, Lantern, completion |
| M03 | Ambience, footsteps, near glint, Compass (aliased canonical S03 Compass), completion |
| M04 | Ambience, footsteps, near glint, Guide moon bell, completion. The Lantern chimes only if it is actually inspected. |
| M05+ | None, until a session opts in explicitly. |

### Event truth

| Cue | Fires when | Guard |
|---|---|---|
| `ambient_moon_meadow` | The scene enters. It fades out over 600 ms when the scene exits. | One loop on a dedicated channel; asking again does nothing. It fades in over 1.5 s. |
| `footstep_grass` | Each foot contact of real movement: every 30 px travelled, the same cadence as the drawn step dust | None while Nova stands still. 0.12 s cap. Two variants alternate. |
| `object_near` | Nova comes into range of an object or NPC it has not yet visited or spoken to | Re-arms only after 5 s out of that target's range. 1.5 s cap. |
| `compass_magic` / `lantern_chime` / `object_interact` | An actual E interaction with that object | One per interaction event. 0.6 s / 0.6 s / 0.25 s caps. |
| `pixel_greeting` / `npc_talk` | An actual E interaction that starts a conversation (a greeting, or line one of a longer one) | One per conversation start. 0.6 s cap. |
| `mission_complete` | The mission state goes from incomplete to complete | Plays once, 0.45 s after the interaction that completed the mission, and never again for that scene. |
| `ui_mute_toggle` | Unmuting | Confirms that sound is back. |

Cooldowns use game time (the frame `dt`), not wall time, so they are deterministic.

## Sounds

All sounds are original. `scripts/build_trail_audio.py` synthesizes them from
seeded noise, sines, bell partials, and simple filters, using only the Python
standard library. A rebuild is byte-for-byte identical, and a test checks
this. They ship under the repository license. All of them are 22050 Hz, mono,
16-bit PCM WAV. The total is 11 files and 719 KiB, of which 431 KiB is the
10 s ambience loop.

The runtime reads only the files listed in `engine/assets/trusted_audio/manifest.json`
whose bytes match their SHA-256. A missing, corrupt, or tampered file silences
only its own cue.

## Mix

The volumes live only in `engine/audio/_cues.py`:

| Level | Cues | Volume | Played peak |
|---|---|---|---|
| Very low | ambience | 0.12 | about -39 dBFS RMS |
| Very low | footsteps | 0.06 | -29 dBFS |
| Low | near glint, unmute tick | 0.10-0.12 | -24 dBFS |
| Low-medium | Pixel, objects, Compass, Lantern, Guide | 0.18-0.24 | -18 to -15.5 dBFS |
| Medium | mission complete | 0.28 | -13.6 dBFS |

Even with every channel at its loudest cue at once, the mix stays below full
scale. A test checks this.

## Mute and fallback

- **M** toggles every Trail sound. Gameplay never sees the key. Muting stops
  the effects at once and holds the ambience loop at zero volume, so unmuting
  never restarts it. A small "Audio: On (M to mute)" / "Audio: Muted (M to
  unmute)" label sits in the bottom-right corner, but only while a mixer is
  actually open.
- `EXPLORE_STUDIO_AUDIO=muted` starts muted. `EXPLORE_STUDIO_AUDIO=off` never
  opens the mixer.
- If the mixer is missing, there is no audio device (common in WSL), or a
  driver errors out, the Trail runs silently. The failure is logged once and
  never retried. When `pygame.init()` has already failed to open audio, the
  backend does not try again.
- To drop footsteps, set `FOOTSTEPS = False` in `_cues.py`. Nothing else changes.

## Performance

The six mixer channels are fixed: ambience, footsteps, and four effects
channels. When all four effects channels are busy, the oldest is reused. Each
file is read and decoded once, when the Trail starts. The cue log keeps the
last 128 entries. No disk I/O happens per frame. Frame time and the full
evidence are in [`docs/audio-proof/trail-audio/`](audio-proof/trail-audio/README.md).

## Teacher guidance

Press **M** to mute during an explanation. Audio is optional, and a silent
Trail loses nothing. If Zoom unexpectedly captures your computer's sound, press
**M**. See [Classroom Preflight](operations/classroom-preflight.md#trail-sound-s02-s04).
