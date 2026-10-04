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

The **final polish pass** (see [below](#final-polish-pass)) repainted the
plate's lighting and depth, gave Nova a face and a stronger silhouette, set
the Compass in a brass crescent with a tinted ground halo, and integrated the
prompt, dialogue, and feedback surfaces, again on the same runtime systems.

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

Everything new is cosmetic, is allow-listed by mission id, and is inert for
every other Trail, so S01 and S04+ draw exactly what they drew before.

The allow-list is the explicit policy in
`engine/rendering/_mission_presentation.py`:

| Mission | Presentation |
|---|---|
| M02 `create-a-classroom-object` | Moon Meadow, every shared layer, plus the M02-only Compass "discovered!" label and the mission-complete confetti and banner. |
| M03 `make-your-object-respond` | Moon Meadow and the shared layers only: plate and foreground, ambient life, Nova V3, trusted Compass art, entity effects, HUD panel, and the `E` prompt. The canonical S03 Compass (`moon-compass-response:compass`) is aliased onto the trusted Moon Compass art. The student's own `when_near` clue and `when_interacted` reveal carry the story, so the M02 label and celebration stay out. |
| Every other mission | Unchanged plain Trail. |

Proof frames for M03 come from `scripts/capture_s03_visual_proof.py`; see
`docs/visual-proof/s03-moon-meadow/`.

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
| `objects/moon-compass-halo` | 144 × 36 (tinted) | `halo` | `spin-00..15` |
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
| Lantern rays | 8, only during a flare |
| Landing-pad chase lights | 2 glows |
| Trail chevron pulse | 1 glow |
| Lander beacon | 1 glow, 0.3 s of every 1.8 s |
| Pond shimmer | 1 glow, up to 5 glints |
| Shooting star | 3 lines and 1 glow, 0.8 s of every 13 s |
| Nova step dust | 1 soft puff |
| Pixel screen light | 1 glow |

Glow and shadow textures, translucent panels, and fonts are cached with size
caps. Each trusted sheet is read, digest-checked, and decoded once; each frame
(and each tinted Compass frame) is cut once and cached, well under the
384-frame cap.

Measured headless, a moving and interacting M02 frame took 2.77 ms mean and
4.24 ms p95. The base took 4.01 ms mean, because it re-created its font on
every text draw.

For the art pass, `scripts/capture_s02_visual_proof.py --only benchmark`
times 600 real update + render frames of Nova walking a loop and pressing E
every second. On a quiet machine the V3 art pass measured about 0.9 ms mean
and 1.0-1.4 ms p95, against about 1.2 ms mean and 1.3-1.7 ms p95 for the
V2 base: the single opaque plate replaces hundreds of procedural draws.
Under heavy background load (six interleaved runs each), the medians were
2.50 ms mean and 5.39 ms p95 for V3 against 2.66 ms and 5.74 ms for V2, so
the art pass costs no more per frame than the base did.

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

## Final polish pass

The last visual pass for the course. Same contract as above: no gameplay,
geometry, schema, mission, or HUD-text change, and every layer stays
allow-listed to M02/M03.

- **Plate lighting and depth.** Authored ground swells are lit by the moon
  (lit backs, cool fronts) instead of an even speckle of bright grass tips.
  Each landmark tints its own ground: violet at the Compass clearing, teal at
  the camp, and warm at the shrine. The meadow between them settles darker, so
  the eye moves from pool to pool. Low moon-mist wisps and faint moon rays add
  atmospheric depth, and the vignette frames the trail.
- **Grounded props.** Tall props cast long, soft moon shadows away from the
  moon. Grass grows over the base of every prop and over the front rims of
  the pad and dais, and moss ages both platforms. Flower beds are smaller and
  glow less, so landmarks win the eye. The shrine's warm wash up the path is
  now a gentle invitation rather than a hot stripe.
- **Ant colonies.** The ants follow a faint worn path from a sandy hill to a
  fallen moon crystal, and carry glowing crumbs home. The painted raised
  "highway" is gone.
- **Foreground.** Out-of-focus broad leaves, with a few glowing buds, rise up
  both side edges. They stay inside the tested clear zone, so the playable
  middle is still fully transparent.
- **Nova.** Nova now has a hair fringe, big glossy eyes with brows, an open
  smile, and a true glass visor (sky-tinted top, crisp edge, moon glint). A
  heavier outer silhouette line keeps Nova readable at half scale.
  Contact shade seats the helmet on the suit. The walk has a bigger arm swing,
  a springier bob, and a forward lean in profile. The art stays inside the
  same 100 × 100 box: its alpha footprint moved by at most one pixel.
- **Pixel.** Pixel shares the silhouette line. Its screen spills a soft cyan
  light that brightens while it greets.
- **Moon Compass.** The body layer adds a brass crescent-moon cradle with two
  star tips inside the Compass's own 80 × 60 box, so it reads as a treasure.
  The ring is still the student's color. The line-drawn ground rings are
  replaced by the trusted `objects/moon-compass-halo` rune circle. It is
  tinted with a fixed mix of the student's color, so tinted frames cache once
  per color. It is drawn from the Compass's own `x`/`y` and turns one rune
  every 3.5 s. Without the sheet, the two-tier line ring is drawn as before.
- **Crystal Lantern.** The resting Lantern no longer has line rays; rays
  burst only when it is inspected. The bouncing triangle is now a floating,
  faceted gold waypoint gem that points down at the Lantern until it is
  visited. Its warm light is slightly calmer.
- **Living world.** These are drawn over the plate only, as pure functions of
  the presentation clock:
  - a light chases around the landing pad's painted rim lights;
  - the trail chevrons pulse from the pad toward the Compass;
  - the lander's beacon blinks;
  - the pond's moon reflection shimmers;
  - a shooting star crosses the open sky between the HUD rows and the moon
    for 0.8 s of every 13 s;
  - Nova kicks up a soft dust puff at each foot contact.

  The positions live in `_meadow_layout` beside the painted scenery.
- **HUD and dialogue.** A soft translucent card sits behind the bottom
  feedback line (and behind "Trail complete!"). It is measured from the
  scene's read-only `feedback_message`, the exact line the HUD draws, so text,
  font, and position are unchanged. Prompts gain a drop shadow and a pointer
  tab toward their target. Speech bubbles gain a drop shadow and a speaker
  name tag.

Proof frames, side-by-side comparisons, and the written evaluation live in
`docs/visual-proof/moon-meadow-final/`.
