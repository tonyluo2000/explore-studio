# S04 Moonlit Guide — runtime proof

Every frame here is a real capture of the M04 Classroom Trail. Each comes from
`scripts/capture_s04_visual_proof.py` (headless `SDL_VIDEODRIVER=dummy`, real
directional input, a real `E` press, fixed 60 FPS steps), using the canonical
S04 task-card packages: Nova, the Crystal Lantern, and
`lessons/sessions/s04/student/explorer-package`. Nothing is mocked or painted
afterwards. Half-scale images are smooth downscales of a captured frame, which
approximates a Zoom screen share. Close-ups are plain crops scaled up 3×.
BEFORE frames are captured from `main` at `032b394` by the same script with
`--only before`.

```console
SDL_VIDEODRIVER=dummy python3 scripts/capture_s04_visual_proof.py docs/visual-proof/s04-moonlit-guide
```

| Evidence | File |
|---|---|
| S04_IDLE | `s04-idle.png` |
| S04_GUIDE_VISIBLE | `s04-guide-visible.png` |
| S04_APPROACH (Nova beside the Guide, `Talk to Moonlit Guide`) | `s04-approach.png` |
| S04_DIALOGUE (canonical greeting) | `s04-dialogue.png` |
| S04_COMPLETE (after the bubble's reading time) | `s04-complete.png` |
| S04_HALF_SCALE, 480 × 320 | `s04-half-scale-480x320.png` |
| S04_DIALOGUE_STRESS (longest greeting shown whole, 5 lines) | `s04-dialogue-stress.png`, `s04-dialogue-stress-480x320.png` |
| Overflow greeting (explicit `…`, never silently clipped) | `s04-dialogue-overflow.png`, `s04-dialogue-overflow-480x320.png` |
| S04_LIVING_WORLD_5S | `s04-living-world-5s.gif`, `s04-living-world-5s.png`, `s04-living-world-strip.png` |
| Approach and greet clip | `s04-approach-and-greet.gif` |
| Guide close-up (idle, talking) | `guide-closeup-idle.png`, `guide-closeup-talking.png` |
| Side-by-side, standard rectangle vs new S04 | `comparison-idle.png`, `comparison-dialogue.png` |
| Side-by-side Guide close-up and half scale | `comparison-guide-closeup.png`, `comparison-half-scale-480x320.png` |

## What changed for S04

- **Before.** S04 drew the plain Trail. The Guide was a 100 × 100 blue
  rectangle, and the greeting appeared only as one HUD line that ran off the
  right edge of the window.
- **After.** S04 sits in the frozen Moon Meadow. The Guide is a friendly,
  hooded moon-sage with a crescent-moon staff, drawn from the trusted sheet
  `characters/moonlit-guide` at its canonical box (540, 220, 100 × 100).
  - It breathes, blinks, waves once when greeted, and its orb glows.
  - A small floating speech cue marks it until it has been spoken to.
  - The greeting appears whole in a larger bubble with a `Moonlit Guide`
    name tag.
  - The bottom HUD echo stays on screen and ends in `…`.
- **Lantern.** The Lantern keeps its art, light, and flicker. Its gold
  destination gem is gone in M04, because M04 completes by talking, not by
  visiting the Lantern.
- **Completion.** There is no M02 confetti or "discovered!" label. M04
  completion is shown by the unchanged `Mission state: Complete` row.

## Frozen Moon Meadow

Captures were made with `scripts/capture_s02_visual_proof.py` and
`scripts/capture_s03_visual_proof.py` on `main` and on this branch. All 14 M02
frames and all 4 M03 frames are **pixel-identical**. The plate, foreground,
ambience, HUD, Nova, Pixel, the Compass, and the Lantern art are unchanged.

## Gameplay and performance

- **Gameplay.** A scripted M04 run gives an identical trace with and without
  the presentation layer. The trace covers player x/y, target, visited and
  spoken sets, completion, `feedback_message`, the Guide's x/y/size/color, and
  object positions (`tests/test_s04_presentation.py`).
- **Performance.** Headless update + render over 600 frames, three runs each:

| Trail | mean ms | p95 ms |
|---|---|---|
| M02, `main` | 0.91–0.93 | 1.00–1.04 |
| M02, this branch | 0.91–0.94 | 0.98–1.05 |
| M04, `main` (plain Trail) | 0.15 | 0.16–0.17 |
| M04, this branch (Moon Meadow) | 0.81–0.86 | 0.93–0.94 |

  M04 now costs what any Moon Meadow mission costs, well inside a 16.7 ms
  frame. The Guide sheet is decoded once and its frames are cached. Text
  layout is memoized in a bounded cache (16 entries). The talk cue and glows
  are fixed counts.

## Known limits

- **Bubble length.** The bubble holds up to six lines of a 340 px column at
  24 px, about 180 characters. Longer student greetings end in `…` in the
  bubble. Validation is unchanged: the Student API sets no length limit.
- **`Visited 0 / 1` row.** The shared HUD row still counts the Lantern as
  visited-object progress. M04 completion is the `Mission state` row. The
  shared HUD semantics were deliberately left unchanged.
- **Guide color.** Trusted art is declared for the canonical `color: "blue"`.
  Another color draws a posed procedural guide in that color, never a
  rectangle.
