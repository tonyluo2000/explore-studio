# S01 Moon Meadow arrival — runtime proof

Every frame here is a real capture of the M01 Classroom Trail. Each comes from
`scripts/capture_s01_visual_proof.py` (headless `SDL_VIDEODRIVER=dummy`, real
directional input, a real `E` press, fixed 60 FPS steps), using the canonical
S01 task-card packages: Nova, Pixel, and the Crystal Lantern. Nothing is
mocked or painted afterwards. The half-scale image is a smooth downscale of a
captured frame, which approximates a Zoom screen share. BEFORE frames are
captured from `main` at `45fad60` with the retired S01 cast (Nova, Fern, the
Crystal Lantern, and the River Fountain) by the same script with
`--only before`.

```console
SDL_VIDEODRIVER=dummy python3 scripts/capture_s01_visual_proof.py docs/visual-proof/s01-moon-meadow-arrival
```

These are review evidence, not website snapshots.

| Evidence | File |
|---|---|
| S01_ARRIVAL (hero: Nova and Pixel at the Landing Site, Lantern shrine and empty stone circle in view, no prompt) | `s01-arrival.png` |
| Exact canonical start (Pixel in range, optional `Talk to Pixel` prompt) | `s01-arrival-start.png` |
| Pixel's optional greeting (`Visited 0 / 1`) | `s01-pixel-hello.png` |
| S01_LANTERN_NEAR (`Inspect Crystal Lantern`, near text) | `s01-lantern-near.png` |
| S01_LANTERN_INTERACT (spark, `Visited 1 / 1`, `Trail complete!`) | `s01-lantern-interact.png` |
| S01_COMPLETE | `s01-complete.png` |
| S01_HALF_SCALE, 480 × 320 (of the hero) | `s01-half-scale-480x320.png` |
| Same cast, no `--mission-id` (plain Trail) | `s01-cast-without-mission-id.png` |
| Arrival-to-Lantern clip | `s01-arrival-to-lantern.gif` |
| Side-by-side, retired S01 vs new S01 | `comparison-arrival.png`, `comparison-lantern.png` |

## What changed for S01

- **Before.** S01 drew the plain Trail: Nova, Fern as a green rectangle, the
  River Fountain as a blue rectangle, and the Lantern; `Visited 0 / 2`.
- **After.** S01 is the arrival chapter in the frozen Moon Meadow. Nova and
  Pixel stand at the Landing Site, the Crystal Lantern glows in its shrine down
  the path, and the empty circle of standing stones sits in the scenery,
  unnamed. `Visited 0 / 1`; only the Lantern counts.
- **Policy.** M01 joins `MISSION_PRESENTATIONS` with the shared layers only:
  no Lantern waypoint (students predict what counts), no M02 "discovered!"
  label or celebration, no talk cue or dialogue focus, and no audio. No
  Compass and no Guide are in the scene.
- **Pixel.** Pixel uses its trusted art and pose. It is an NPC that never
  counts toward `Visited`; its greeting is optional.
- **No `--mission-id`.** A Trail launched without `--mission-id` still runs
  M01's completion rule on the plain Trail, exactly as before, so free-play
  Trails never inherit the S01 story presentation.

## Frozen Moon Meadow

Captures were made with `scripts/capture_s02_visual_proof.py`,
`scripts/capture_s03_visual_proof.py`, and `scripts/capture_s04_visual_proof.py`
on `main` (`45fad60`) and on this branch. All 14 M02 frames, all 4 M03 frames,
and all 14 M04 frames are **pixel-identical**. No trusted art, audio asset,
plate, HUD, or sprite changed.

## Gameplay and performance

`tests/test_s01_presentation.py` replays a scripted M01 run (greet Pixel, walk
to the Lantern, press `E`) with the presentation, without it, and without a
mission id; positions, targets, visits, spoken NPCs, completion, and feedback
are identical. Headless update + render of a moving M01 frame
(`--only benchmark`, 600 frames): mean 0.97 ms, p95 1.46 ms (M02 on `main`:
mean 1.16 ms, p95 1.96 ms).

## Fresh install from the candidate Course Kit

The Course Kit ZIP is `ac4a0d87…69eedd` (253 members, provenance commit
`7dd5d0a`). It was unpacked into a clean `HOME`, given a fresh `.venv`
(Python 3.13.7), and installed with `pip install -r requirements-student.txt`;
the pinned archive `3038cf4` resolved from GitHub.

- `python3 check-my-computer.py`: **READY FOR EXPLORE STUDIO**, course tools
  `3038cf4 (current)`.
- S01 starter prints the three new observations; `nova-character`,
  `pixel-companion`, and `crystal-lantern` validate.
- The canonical task-card `explore-package trail` commands were driven by an
  autopilot that patches only input polling (dummy video and audio drivers):

| Run | Presentation | Mixer | Result |
|---|---|---|---|
| S01 | Moon Meadow, no waypoint, no audio | never opened | `Visited 1 / 1`, complete without talking to Pixel |
| S02 (after `make-my-world.py`) | Moon Meadow, unchanged | opened | `Visited 2 / 2`, complete; Compass, Lantern, completion cues |
| S03 | Moon Meadow, unchanged | opened | `Visited 1 / 1`, complete; Compass, completion cues |
| S04 | Moon Meadow, unchanged | opened | Guide spoken to, complete; Guide, completion cues |
| S01 cast, no `--mission-id` | plain Trail | no audio layer | M01 rules |
