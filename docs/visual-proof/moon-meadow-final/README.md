# Moon Meadow final visual-polish pass: runtime proof

Real 960 × 640 frames from the Classroom Trail runtime. Nothing is mocked or
painted afterwards. They were captured headlessly with
`scripts/capture_s02_visual_proof.py` (M02) and
`scripts/capture_s03_visual_proof.py` (M03), using the reviewed packages,
real directional input, real `E` presses, and fixed 60 FPS steps.

**BEFORE** frames come from the same scripts run inside a checkout of `main`
at `5c0d545`, with that checkout's own runtime and art. **AFTER** frames come
from this branch. The half-scale image is a smooth downscale of a captured
frame, which approximates a Zoom screen share.

| Evidence | File |
|---|---|
| Side-by-side, idle | `comparison-idle.png` |
| Side-by-side, Compass prompt | `comparison-compass-prompt.png` |
| Side-by-side, Pixel greeting (dialogue) | `comparison-pixel-greeting.png` |
| Side-by-side, moved Compass (x 690, y 360) | `comparison-moved-compass.png` |
| Side-by-side, 480 × 320 half scale | `comparison-half-scale-480x320.png` |
| Side-by-side, S03 reveal | `comparison-s03-reveal.png` |
| Close-ups: Nova and Pixel, Compass (3×) | `comparison-nova-pixel-closeup.png`, `comparison-compass-closeup.png` |
| 960 × 640 stills | `art-pass-idle.png`, `compass-prompt.png`, `compass-interaction.png`, `lantern-prompt.png`, `mission-complete.png`, `pixel-greeting.png`, `nova-walk-right.png` |
| 480 × 320 | `half-scale-480x320.png` |
| Moved Compass | `moved-compass.png` |
| Living world, 5 s (Nova untouched) | `living-world-strip.png` (one frame per second), `living-world-5s.png`, `living-world-5s.gif` |
| Walking clip | `nova-walking.gif` |
| S03 clue and reveal | `s03/s03-near-clue.png`, `s03/s03-reveal.png` |

## What improved

- **Nova.** This is the biggest character gain. Nova now has a face and a
  personality: a hair fringe, big glossy eyes, brows, an open smile, and a
  real glass visor. A heavier outer silhouette line keeps Nova readable on the
  busy meadow and at 480 × 320. The walk swings and bobs more, and leans
  forward in profile. Each step kicks up a small dust puff.
- **Scene depth and lighting.** This is the biggest scene gain. The even
  green speckle is gone:
  - Rolling swells catch the moon, and tall props cast long, soft shadows.
  - The three landmarks sit in their own colored light pools (violet clearing,
    teal camp, warm shrine) with a darker meadow between them.
  - Mist and moon rays add atmosphere, and out-of-focus leaves frame the
    corners.
  - Grass grows over prop bases and platform rims, so things sit *in* the
    meadow instead of on it.
- **Compass.** It now reads as a treasure: it sits in a brass crescent moon,
  with the student's color on the ring. A tinted rune circle lies on the
  ground beneath it. The circle replaces the aliased line rings and travels
  with the student's `x`/`y` (see `comparison-moved-compass.png`).
- **Destination.** The Lantern's resting line rays are gone, and the hot
  stripe of light up the shrine path is calmer. A floating gold waypoint gem
  replaces the triangle arrow.
- **Living world.** Over 5 s the world clearly keeps moving without noise:
  - a light chases around the landing pad and the chevrons pulse toward the
    trail;
  - the lander's beacon blinks and the pond shimmers;
  - ants carry glowing crystal crumbs home;
  - a rare shooting star crosses the open sky (0.8 s of every 13 s).
- **HUD and dialogue.** The bottom feedback line sits on a soft card instead
  of floating text. Prompts have a shadow and a pointer tab toward their
  target. Pixel's bubble has a shadow and a "Pixel" name tag. All HUD text,
  fonts, and positions are unchanged.

## What is still imperfect

- **Text font.** It is still Pygame's default font. A storybook display font
  would do more for the "real game" feel than any remaining paint, but no
  redistributable font is bundled, and adding one is asset-pipeline scope.
- **Characters versus plate.** The characters are crisper than the painterly
  plate. The silhouette line and contact shadows help, but Nova and Pixel
  still read slightly as sprites on a painting.
- **Overall brightness.** The scene is a little darker overall than a bright
  storybook target, by design for the moonlit mood. On a dim projector, the
  lower-right meadow (behind the feedback card) is quiet and low in detail.
- **Compass halo over the dais.** At its canonical spot, the Compass halo sits
  over the dais's own painted rings, so the two read as a slight double ring.
  When the Compass is moved, only the halo travels, which is correct.
- **Visible-world motion.** Ambient motion is runtime overlay only. The
  painted grass and leaves do not move (only the reeds sway).

## Frame cost

The benchmark is `scripts/capture_s02_visual_proof.py --only benchmark`:
600 real update and render frames of Nova walking a loop and pressing `E`
every second. Over five interleaved runs on the same machine:

| Runtime | Median mean | Median p95 |
|---|---|---|
| `main` (5c0d545) | 0.95 ms | 1.07 ms |
| Final polish | 0.98 ms | 1.14 ms |

That is about +0.03 ms per frame. Every new effect is a fixed count:

| Effect | Per frame |
|---|---|
| Compass halo | 1 cached sprite |
| Pad chase | 2 glows |
| Chevron pulse | 1 glow |
| Beacon | 1 glow |
| Pond | 1 glow, up to 5 glints |
| Shooting star | 3 lines and 1 glow |
| Step dust | 1 puff |
| Pixel screen light | 1 glow |

None of them reads from disk.
