# S02 art-first pass — runtime proof

Every image here is a real 960 × 640 frame from the Classroom Trail runtime.
They were captured headlessly (`SDL_VIDEODRIVER=dummy`) by
[`scripts/capture_s02_visual_proof.py`](../../../scripts/capture_s02_visual_proof.py).
The script drives the actual M02 scene with the reviewed S02 packages, real
directional input, real `E` presses, and fixed 60 FPS time steps. Nothing is
painted afterwards, and none of these are mockups. PNGs are recompressed
losslessly, so their pixels are exactly what the runtime drew.

| Evidence | File | What it shows |
|---|---|---|
| BEFORE_CURRENT | `before-current.png` | Authoritative base `e89c96a7c0f8f2fc5582590f5721c465206bf85c` (PR #104), captured from that checkout with the same script (`--only before`) after 1.2 s idle. |
| ART_PASS_IDLE | `art-pass-idle.png` | The same moment after the art pass: illustrated Moon Meadow, Nova V3, Pixel V3, layered Compass, Lantern shrine, HUD panel, and the `[E] Talk to Pixel` prompt. |
| NOVA_WALK_LEFT | `nova-walk-left.png` | Nova V3 mid-stride walking left (the mirrored side view). |
| NOVA_WALK_RIGHT | `nova-walk-right.png` | Nova V3 mid-stride walking right. |
| PIXEL_GREETING | `pixel-greeting.png` | After `E` near Pixel: the waving greeting frame and the speech bubble. The unchanged HUD line still shows the greeting. |
| COMPASS_PROMPT | `compass-prompt.png` | `[E] Inspect Moon Compass` beside the rune dais. |
| COMPASS_INTERACTION | `compass-interaction.png` | Discovery burst, needle spin, and `Moon Compass discovered!` (`Visited 1 / 2`). |
| LANTERN_PROMPT | `lantern-prompt.png` | `[E] Inspect Crystal Lantern` inside the warm shrine, with the destination arrow and the lit braziers. |
| LANTERN_INTERACTION | `lantern-interaction.png` | The Lantern flare. |
| MISSION_COMPLETE | `mission-complete.png` | `Visited 2 / 2`, the `Mission complete!` banner, and confetti; the HUD's own `Trail complete!` and mission state are unchanged. |
| LIVING_WORLD_5S | `living-world-5s.png`, `living-world-5.5s.png` | Nova untouched for 5 s and 5.5 s: ants, motes, reeds, crystal glints, stars, braziers, the Compass ring and needle, the Lantern, Pixel, and Nova's breathing all differ between the two frames. |
| HALF_SCALE_480x320 | `half-scale-480x320.png` | `compass-prompt.png` smoothly scaled to 480 × 320, approximating a Zoom share. |
| MOVED_COMPASS | `moved-compass.png` | Only the student-owned Compass moved from `(240, 180)` to `(690, 360)` in a temporary package copy. Its ring, needle, glass, hover, aura, sparkles, and shadow all moved with it; the clearing stays a static waypoint. |
| Walking GIF | `nova-walking.gif` | About 4 s at 480 × 320: Nova walking left, up, right, and down, then stopping. |
| Living-world GIF | `living-world-5s.gif` | 5 s at 480 × 320 with no input at all. |

Reproduce, from the repository root:

```console
SDL_VIDEODRIVER=dummy python3 scripts/capture_s02_visual_proof.py docs/visual-proof/s02-art-pass
git worktree add /tmp/base e89c96a7c0f8f2fc5582590f5721c465206bf85c
PYTHONPATH=/tmp/base SDL_VIDEODRIVER=dummy \
  python3 scripts/capture_s02_visual_proof.py docs/visual-proof/s02-art-pass --only before
```

Frame timing uses the same script:

```console
SDL_VIDEODRIVER=dummy python3 scripts/capture_s02_visual_proof.py /tmp/unused --only benchmark
PYTHONPATH=/tmp/base SDL_VIDEODRIVER=dummy \
  python3 scripts/capture_s02_visual_proof.py /tmp/unused --only benchmark
```

GIF encoding and the lossless PNG recompression use Pillow when it is
installed. Pillow is a local capture convenience here and is not a runtime
dependency.
