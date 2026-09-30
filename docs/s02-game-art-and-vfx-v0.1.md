# S02 game art and VFX layer v0.1

This slice makes the S02 (M02) Classroom Trail feel like a small video game
without changing what the lesson teaches. Nova is the reference-quality
Explorer. Pixel, the Moon Compass, and the Crystal Lantern get matching
polish, and the Moon Meadow keeps moving when nobody touches the keyboard.

The **art-first pass (V3)** replaced the programmer-art content on top of
the same runtime systems. It adds an illustrated Moon Meadow plate with a
framing foreground, Nova V3 with an eight-frame walk, Pixel V3, a layered
Compass tinted by the student's color, a new Lantern, and authored reeds.
It did not change the engine design, gameplay, or any contract below.

Student Explorers and Companions are **not** implemented here. They are the
next tranche: "Nova has been upgraded. Yours is next."

## Contract

Unchanged:

- the Student API
- package schemas
- mission semantics and M02 completion
- Compass `x`/`y` behavior and entity gameplay coordinates
- sizes, hitboxes, interaction range, and movement speed
- Student Workspace ownership
- the S02 curriculum
- the HUD text and its positions

Everything new is cosmetic, is allow-listed to the M02 mission id, and is
inert for every other Trail, so S01 and S03+ draw exactly what they drew
before.

## Layers

`ClassroomTrailScene.update` runs gameplay first. It then calls
`TrailPresentation.observe`, which only reads the scene's state:

- player position
- current target
- interaction pulse
- visited set
- mission completion

`observe` never raises into gameplay.

`ClassroomTrailScene.render` draws, in order:

1. the static backdrop (`_classroom_environment`): the trusted illustrated
   plate `scenery/moon-meadow` in one opaque blit, or the original procedural
   backdrop when the plate is unavailable;
2. ground life: ants, swaying reeds, crystal glints, twinkling stars, and the
   shrine braziers' flicker (`_classroom_ambience`). Over the plate these
   follow the painted positions in `_meadow_layout`; over the fallback they
   follow the procedural backdrop, which also gets procedural anthills;
3. each world object, then the NPCs, then the player. Each entity draws its
   under-effects (shadow and light), then its sprite at its authoritative
   bounds, then its over-effects (sparkles, rays, sparks, the destination
   arrow);
4. overlay shapes: the framing foreground plate
   `scenery/moon-meadow-foreground`, motes, discovery bursts, confetti, the
   translucent HUD panel, prompt, speech bubble, discovery label, and banner
   panels;
5. the HUD text, which is unchanged and still drawn first among all text;
6. overlay text.

The foreground plate only holds dark plants and a rock in the bottom corners
and a low grass fringe along the bottom edge; a test keeps the playable middle
fully transparent. The HUD panel is two translucent rounded rects measured to
the unchanged HUD rows, so the text, its positions, and its order are exactly
as before while most of the sky stays open.

The sprite calls keep the existing seven-argument
`draw_classroom_sprite(renderer, qualified_id, x, y, width, height, color)`.
The M02 pose travels in a context variable (`classroom_sprite_pose`), so no
existing call site or monkeypatch changes shape.

## Trusted asset pipeline

- `scripts/build_trusted_art.py` is the provenance. It paints every frame
  from code with a small signed-distance-field painter (`scripts/art`, numpy
  and Pillow at build time only; `pip install -e ".[art]"`): analytic
  anti-aliasing, outlines as shape offsets, soft cel shading away from the
  moon, cool rim light, gradients, seeded noise textures, and baked glows.
  It writes PNG sheets plus `engine/assets/trusted/manifest.json`. A rebuild
  reproduces every committed digest; the runtime never imports numpy or
  Pillow.
- The manifest records, for each sheet, its:
  - frame size
  - named rows and columns
  - declared accent color
  - SHA-256
- `TrustedArtCatalog` (pure Python) reads only manifest-listed files inside
  the trusted directory whose bytes match their digest. Missing, tampered,
  escaping, or malformed entries read as unavailable.
- `SpriteSheetLibrary` decodes each sheet once through the platform and caches
  each frame at its requested size and facing. The cache is bounded, and
  failures are remembered and logged once.
- `Renderer.draw_sprite_frame` draws a frame only when the entity's color
  equals the art's declared accent. A recolored package therefore gets the
  posed procedural fallback instead of mismatched art.
- The Moon Compass is the student's color, so its art is neutral and layered:
  `ring` (tinted at draw time by multiplying with the student's color, cached
  per color), `body` (brass bezel, star-chart face, red north marker, white
  glints), a separate needle sheet with 64 pre-rotated angles, and `glass`.
  Every layer is drawn in the Compass's own 80 × 60 box from its `x`/`y`, so
  the art, hover, and all effects move exactly with the student's numbers.
  Without trusted art the procedural Compass is drawn as before.
- Opaque plates decode without an alpha channel, so the background is one
  fast blit.
- `pyproject.toml` ships `engine/assets/trusted/**` as package data, so the
  Course Kit's pinned runtime install includes the art.

| Sheet | Frame | Rows | Columns |
|---|---|---|---|
| `scenery/moon-meadow` | 960 × 640 (opaque) | `night` | `backdrop` |
| `scenery/moon-meadow-foreground` | 960 × 640 | `night` | `frame` |
| `characters/nova` | 100 × 100 | `down`, `up`, `right` (left = mirrored) | `idle-0..3`, `blink`, `walk-0..7` |
| `characters/pixel` | 100 × 100 | `idle` | `idle-0..3`, `blink`, `greet-0..3` |
| `objects/moon-compass` | 80 × 60 | `ring` (tinted), `body`, `glass` | `spin-00..11` |
| `objects/moon-compass-needle` | 80 × 60 | `needle` | `angle-00..63` |
| `objects/crystal-lantern` | 80 × 60 | `glow` | `flicker-0..3` |
| `ambient/reeds` | 32 × 44 | `sway` | `sway-0..8` |

The illustrated meadow communicates the route without words: the start camp
(landing pad, lander, and teal chevrons pointing at the trail), the Compass
clearing (a rune dais inside standing stones on a knoll), and the Lantern
shrine (a warm-lit arch with braziers, a plaza, and steps), joined by one
authored stone path. Warm light pools only at the shrine, so the destination
stands out against the cool moonlit meadow.

## Animation

`engine.animation` holds pure, injected-time selection: `AnimationClip`,
`Facing`, `facing_from_motion`, `is_blinking`, and `SpritePose`.

- Nova's walk frame comes from the distance travelled (7.5 px per frame,
  eight frames per 60 px cycle, the same pace over the ground as V2), so steps
  keep pace with the ground and Nova never slides.
- The Compass's rune ring turns 45° per loop (one rune), its needle sways and
  spins on discovery, and it hovers up to 2 px inside its box.
- Facing follows the dominant motion and holds when Nova stops.
- Idle breathing and blinks run on the presentation clock.
- Pixel's greeting reaction plays for 1.2 s after its greeting and does not
  touch `visited`.

## Bounds

Every effect count is fixed:

| Effect | Count |
|---|---|
| Ants | 9 on 2 trails |
| Motes | 10 |
| Reed clumps | 9 (sprite frames) |
| Crystal glints | 6 |
| Shrine brazier flickers | 2 |
| Compass sparkles | 4 |
| Burst particles per burst | 14 |
| Active bursts | at most 4 |
| Confetti pieces | 36, for 3.2 s only |
| Lantern sparks | 5, plus 6 during a flare |

Glow and shadow textures, translucent panels, and fonts are cached with size
caps. Each trusted sheet is read, digest-checked, and decoded once; each frame
(and each tinted Compass frame) is cut once and cached, well under the
384-frame cap.

Measured headless, a moving and interacting M02 frame took 2.77 ms mean and
4.24 ms p95. The base took 4.01 ms mean, because it re-created its font on
every text draw.

For the art pass, `scripts/capture_s02_visual_proof.py --only benchmark`
times 600 real update + render frames of Nova walking a loop and pressing E
every second. On the same machine the V3 art pass measured about 0.9 ms mean
and 1.0-1.4 ms p95, against about 1.2 ms mean and 1.3-1.7 ms p95 for the
V2 base: the single opaque plate replaces hundreds of procedural draws.

## Seams for the next tranche (not implemented)

- **Student Explorer.**
  - Add a manifest entry (for example `students/<id>/explorer`) with the same
    `down`/`up`/`right` × `idle`/`blink`/`walk` grid.
  - Map the student's qualified id to it where `SPRITE_SHEET_IDS` maps Nova.
  - The walk, facing, blink, and shadow logic in `TrailPresentation._nova_pose`
    is identity-agnostic apart from that lookup.
  - Student-provided art needs its own validation before it can be trusted;
    this slice deliberately accepts only course-owned, digest-listed files.
- **Student Companion.**
  - Reuse Pixel's `idle`/`blink`/`greet` grid and `_pixel_pose`.
  - The speech bubble already takes any single-line greeting from any M02 NPC.
  - Follow or autonomy behavior would be new gameplay, which belongs in the
    scene, not in this cosmetic layer.
- **Accent rule.** Art declares the color it was drawn for, and a mismatch
  falls back to procedural drawing. Student recoloring can later swap in a
  tinted variant or palette mask without touching gameplay.
