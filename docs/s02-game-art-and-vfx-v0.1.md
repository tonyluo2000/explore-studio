# S02 game art and VFX layer v0.1

This slice makes the S02 (M02) Classroom Trail feel like a small video game
without changing what the lesson teaches. Nova is the reference-quality
Explorer. Pixel, the Moon Compass, and the Crystal Lantern get matching
polish, and the Moon Meadow keeps moving when nobody touches the keyboard.

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

1. the static backdrop (`_classroom_environment`, unchanged);
2. ground life: ants, anthills, swaying reeds, crystal glints, and twinkling
   stars (`_classroom_ambience`);
3. each world object, then the NPCs, then the player. Each entity draws its
   under-effects (shadow and light), then its sprite at its authoritative
   bounds, then its over-effects (sparkles, rays, sparks, the destination
   arrow);
4. overlay shapes: motes, discovery bursts, confetti, prompt, speech bubble,
   discovery label, and banner panels;
5. the HUD text, which is unchanged and still drawn first among all text;
6. overlay text.

The sprite calls keep the existing seven-argument
`draw_classroom_sprite(renderer, qualified_id, x, y, width, height, color)`.
The M02 pose travels in a context variable (`classroom_sprite_pose`), so no
existing call site or monkeypatch changes shape.

## Trusted asset pipeline

- `scripts/build_trusted_art.py` is the provenance. It paints every frame
  from code at 4× on a transparent canvas, smooth-scales it down, and writes
  PNG sheets plus `engine/assets/trusted/manifest.json`.
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
- The Moon Compass stays procedural because its color is the student's
  choice.
- `pyproject.toml` ships `engine/assets/trusted/**` as package data, so the
  Course Kit's pinned runtime install includes the art.

| Sheet | Frame | Rows | Columns |
|---|---|---|---|
| `characters/nova` | 100 × 100 | `down`, `up`, `right` (left = mirrored) | `idle-0..3`, `blink`, `walk-0..3` |
| `characters/pixel` | 100 × 100 | `idle` | `idle-0..3`, `blink`, `greet-0..3` |
| `objects/crystal-lantern` | 80 × 60 | `glow` | `flicker-0..3` |

## Animation

`engine.animation` holds pure, injected-time selection: `AnimationClip`,
`Facing`, `facing_from_motion`, `is_blinking`, and `SpritePose`.

- Nova's walk frame comes from the distance travelled (15 px per frame), so
  steps keep pace with the ground and Nova never slides.
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
| Reed clumps | 9 |
| Burst particles per burst | 14 |
| Active bursts | at most 4 |
| Confetti pieces | 36, for 3.2 s only |
| Lantern sparks | 5, plus 6 during a flare |

Glow and shadow textures and fonts are cached with size caps.

Measured headless, a moving and interacting M02 frame took 2.77 ms mean and
4.24 ms p95. The base took 4.01 ms mean, because it re-created its font on
every text draw.

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
