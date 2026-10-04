# Journey snapshots: S02–S04 (review evidence)

Review-only evidence for the published Journey snapshots. The published files
live in `course4teen-website/public/journey/sNN/`, and their provenance lives
in `course4teen-website/journey/snapshots.json`, which is not served. This
folder holds only a contact sheet of those files, so the images are not
duplicated here.

![Contact sheet: one row per session, HERO first, 480w](contact-sheet.png)

## What was captured

Each snapshot is a real Classroom Trail frame. It is driven headlessly with the
session's canonical task-card command (packages, `--player`, `--mission-id`),
real input, and fixed 1/60 s steps. The audio manager is off, as with
`EXPLORE_STUDIO_AUDIO=off`, so there is no audio indicator and gameplay is
unchanged. A frame is accepted only after the harness has checked the state it
shows: the target, the text actually drawn, trusted art actually drawn for
every required entity, and no art or entity from a later session.

| Session | Moment | Kind | File | 960w | 480w |
| --- | --- | --- | --- | ---: | ---: |
| S02 | `S02_COMPASS_PROMPT` | HERO | `journey/s02/hero.webp` | 93,166 B | 33,918 B |
| S02 | `S02_MOVED_COMPASS` | LEARNING_MOMENT | `journey/s02/moved-compass.webp` | 93,546 B | 34,374 B |
| S03 | `S03_REVEAL` | HERO | `journey/s03/hero.webp` | 93,946 B | 34,392 B |
| S03 | `S03_NEAR_CLUE` | LEARNING_MOMENT | `journey/s03/near-clue.webp` | 92,898 B | 34,356 B |
| S04 | `S04_DIALOGUE` | HERO | `journey/s04/hero.webp` | 96,326 B | 35,194 B |

What each check verifies:

- **S02 HERO:** Nova is beside the Moon Compass and `Inspect Moon Compass` is
  drawn. Nova, Pixel, the Compass, and the Lantern are drawn in trusted art.
  There is no Guide and no S03 Compass.
- **S02 moved Compass:** a temporary copy of the student Compass is set to the
  repo-canonical `x: 690`, `y: 360`, and the Compass is drawn there.
- **S03 HERO:** after `E`, the package's `when_interacted` text is drawn and M03
  is Complete. The trusted Compass art is drawn. There is no Pixel, Lantern, or
  Guide.
- **S03 near clue:** before `E`, the package's `when_near` text and the prompt
  are drawn, and nothing has been visited.
- **S04 HERO:** the Moonlit Guide's whole greeting is in the bubble, with the
  `Moonlit Guide` speaker tag. The Guide and the Lantern are drawn in trusted
  art. The Lantern has no waypoint marker, because M04 has no
  `lantern_waypoint`. There is no S05 content.

## Provenance

- Runtime pin (Course Kit `COURSE_PLATFORM_COMMIT`):
  `05843ffd7e257a3120a671b009f45fcae33f7391`. The harness refuses to publish
  unless the working tree's presentation runtime (every `runtime` file below)
  is byte-identical to the runtime at the pin. A test re-reads the pin from
  git to confirm this.
- Manifest schema: `explore-studio/journey-snapshots@2`. `--check` refuses a
  missing, unknown, or unsupported schema. Version 1 had no capture
  implementation fingerprint, so its entries were recaptured, not relabelled.
  The S02–S04 source frames and all ten WebP files came out byte-identical to
  the version 1 capture.
- Presentation fingerprints, per moment: `S02_COMPASS_PROMPT` `527b3bc108b7…`,
  `S02_MOVED_COMPASS` `260f32bcc720…`, `S03_REVEAL` `633a3b1acff9…`,
  `S03_NEAR_CLUE` `d81d2414554b…`, `S04_DIALOGUE` `b58791b818be…`. The full
  values are in the manifest.
- A fingerprint hashes four parts. The manifest's `fingerprintInputs` lists
  exactly what each one covers:
  - **runtime** (`RUNTIME_GROUPS` in `scripts/journey_snapshots.py`):
    everything between the package files and the drawn frame.
    - `engine-core`: `engine/_color.py`, `_config.py`, `_platform.py`.
    - `rendering`: `engine/rendering/**`, including the per-mission
      presentation policy.
    - `scene`: `engine/scenes/**`, `entities/**`, `animation/**`, `input/**`,
      `interactions/**`, and `engine/audio/_trail_audio.py`. The scene calls
      the audio bridge every frame, and it draws the audio indicator.
    - `trusted-art`: the trusted sprite sheets and the code that loads them.
    - `curriculum`: `explore/curriculum/**`.
    - `package-pipeline`: `explore/packages/**` (loader, models, policy,
      validator, package-set planner, registration adapter, Trail plan and
      scene construction) and `explore/_colors.py`.

    Excluded, each with a reason in `RUNTIME_PIXEL_INERT`: audio playback and
    cues, the trusted audio loader and clips, the windowed `App` loop,
    logging, and the Student API v0.1 classes. A test walks the harness's
    imports statically. It fails if the harness reaches an `engine` or
    `explore` module that is neither fingerprinted nor justified there.
  - **packages:** every file of each task-card package.
  - **captureRecipe:** the task-card command (packages in order, `--player`,
    `--mission-id`), the session row, the moment, the frame size, and the
    WebP settings.
  - **captureImplementation:** the bytes of
    `scripts/capture_journey_snapshots.py`, `scripts/journey_snapshots.py`,
    and `scripts/trail_driver.py`. These hold the fixed time step, real
    input, frame selection, acceptance checks, and encoding. Any edit to
    these files needs a recapture, which only refreshes the manifest when
    the frames are unchanged.

  When any part changes, `--check` and `tests/test_journey_snapshots.py` fail
  with a message that names the part, for example: "Journey snapshot for S03
  (S03_REVEAL) is stale: session package files changed; rerun `python
  scripts/capture_journey_snapshots.py --session S03`".
  `tests/test_journey_snapshot_freshness.py` makes real edits in a temporary
  mirror of the repository and runs `--check` against it. Edits to rendering,
  presentation policy, the registration adapter, the
  loader/models/planner/Trail construction, colours, package YAML, the time
  step, frame selection, acceptance, session config, or the task-card command
  must fail it. Audio-only code, website prose, docs, and the window title must
  not.
- Publishing also refuses unless every `runtime` file in the working tree
  matches the Course Kit runtime pin. So a package-pipeline or colour edit
  blocks publishing just as a renderer edit does.
- The Journey snapshots workflow watches every fingerprint input. A test
  matches the workflow's path filters against the real input files, so the
  two lists cannot drift apart.
- Toolchain at capture: Python 3.13.7, pygame 2.6.1, SDL 2.28.4, SDL_ttf
  2.20.1, Pillow 12.3.0, libwebp 1.6.0, darwin-arm64.

## Encoding and hashes

- Canonical source frame: 960×640 RGB. It is not committed.
- Published: a 960w WebP, and a 480w WebP downscaled from the same source with
  `LANCZOS`. Neither is rendered separately.
- WebP: lossy, quality 90, method 6. The input is opaque RGB, so the output is a
  plain `VP8 ` chunk with no alpha, EXIF, ICC, XMP, or timestamps. Each image is
  well under the 150 KB budget.
- **Hash policy:**
  - `sourceRgbSha256` (the raw frame) is authoritative for regeneration on the
    recorded toolchain.
  - The `images.*.sha256` values verify the committed files on any machine.
  - Byte identity across toolchains is not promised: font rasterization and
    the WebP encoder can differ between pygame, SDL_ttf, Pillow, and libwebp
    builds.

  `tests/test_journey_snapshot_determinism.py` always captures each moment
  twice and requires identical frames and WebP bytes. It compares against the
  manifest only when the toolchain matches, and skips that comparison with an
  explanation otherwise.

## Regenerate

```bash
python scripts/capture_journey_snapshots.py --all-published
python scripts/capture_journey_snapshots.py --session S03
python scripts/capture_journey_snapshots.py --check
python scripts/capture_journey_snapshots.py --all-published --dry-run
python scripts/capture_journey_snapshots.py --session S02 --preview /tmp/journey-preview
python scripts/capture_journey_snapshots.py --contact-sheet docs/journey-proof/snapshots/contact-sheet.png
```

Snapshot encoding needs Pillow, from `pip install -e ".[dev,art]"`.

## S01 is deferred

S01 is deliberately not captured. Phase B is bringing S01 into Moon Meadow,
and the current runtime still gives M01 the standard Trail. The S01 row in
`scripts/journey_snapshots.py` has a `deferred` reason. While that reason is
set:

- the harness refuses to publish S01;
- `--check` and the tests reject any `public/journey/s01/` file and any S01
  manifest entry.

The row already states the post-Phase B contract, so nothing has to be
remembered when the deferral is lifted:

- presentation: `moon-meadow` (the Moon Meadow backdrop must be drawn);
- `must_show`: Nova, Pixel, and the Crystal Lantern, each drawn in trusted art;
- `must_not_show`: both Moon Compasses, the Moonlit Guide, and the retired
  Fern (`forest-guide:guide`) and River Fountain (`river-fountain:fountain`).

Today's S01 card still names Fern and the Fountain, so even with the reason
removed the plain Trail cannot pass. A test proves that today's S01 frame is
rejected.

After Phase B (#114) lands and this branch is updated onto it:

1. Delete the `deferred=` line from the S01 row.
2. Run `python scripts/capture_journey_snapshots.py --all-published`. Editing
   `journey_snapshots.py` changes the capture implementation fingerprint, so
   S02–S04 are recaptured too.
3. Regenerate the contact sheet.

Before then, `--session S01 --preview DIR` shows the frame without publishing
it.
