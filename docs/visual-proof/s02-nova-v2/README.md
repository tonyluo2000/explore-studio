# S02 Nova V2 and living Moon Meadow — runtime proof

Every image here is a real 960 × 640 frame from the Classroom Trail runtime.
They were captured headlessly (`SDL_VIDEODRIVER=dummy`) by
[`scripts/capture_s02_visual_proof.py`](../../../scripts/capture_s02_visual_proof.py),
which drives the actual M02 scene with the reviewed S02 packages. It uses real
directional input, real `E` presses, and fixed 60 FPS time steps. Nothing is
painted afterwards, and none of these are mockups.

| File | What it shows |
|---|---|
| `before.png` | Authoritative base `5e9df255ee7a8a66b4ff01393c1b6de43a53ccec` (PR #103), captured from that checkout with the same script (`--only before`). |
| `nova-idle.png` | Nova V2 after 1.2 s standing still: trusted sprite frame, soft grounded shadow, and the `[E] Talk to Pixel` prompt, since Pixel is the valid nearby target. |
| `nova-walking.png` | Nova walking up (back view: helmet vents, backpack, bedroll). |
| `nova-walking-right.png`, `nova-walking-left.png`, `nova-walking-down.png` | The other facings mid-stride (left is the mirrored side view). |
| `pixel-greeting.png` | After `E` near Pixel: Pixel's happy greeting frame and the greeting in a speech bubble placed clear of Nova and the Compass. The unchanged HUD line still shows the greeting. |
| `compass-prompt.png`, `compass-interaction.png` | `[E] Inspect Moon Compass`, then the discovery burst, needle spin, and `Moon Compass discovered!` label (`Visited 1 / 2`). |
| `lantern-prompt.png`, `lantern-interaction.png` | The bouncing destination arrow and `[E] Inspect Crystal Lantern`, then the Lantern flare. |
| `mission-complete.png` | `Visited 2 / 2`: the brief `Mission complete!` banner and confetti below the HUD band. The HUD's own `Trail complete!` and mission state are unchanged. |
| `living-world-idle-5s.png`, `living-world-idle-5.5s.png` | Nova untouched for 5 s and 5.5 s. Ants, motes, reeds, crystal glints, stars, Compass, Lantern, Pixel, and Nova's breathing all differ between the two frames. |
| `moved-compass.png` | Only the student-owned Compass moved from `(240, 180)` to `(690, 360)` in a temporary package copy. Its sprite, aura, sparkles, and shadow all moved with it; the clearing stays a static waypoint. |
| `half-scale-zoom.png` | `pixel-greeting.png` smoothly scaled to 480 × 320, approximating a Zoom share. |
| `nova-walk-and-greet.gif` | About 8 s at 480 × 320: idle, walking in all four directions, then greeting Pixel. |
| `living-world-idle.gif` | 5 s at 480 × 320 with no input at all. |

Reproduce, from the repository root:

```console
SDL_VIDEODRIVER=dummy python3 scripts/capture_s02_visual_proof.py docs/visual-proof/s02-nova-v2
git worktree add /tmp/base 5e9df255ee7a8a66b4ff01393c1b6de43a53ccec
PYTHONPATH=/tmp/base SDL_VIDEODRIVER=dummy \
  python3 scripts/capture_s02_visual_proof.py docs/visual-proof/s02-nova-v2 --only before
```

GIF encoding uses Pillow when it is installed. Pillow is a local capture
convenience only and is not a project dependency.
