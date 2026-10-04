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
  unless the working tree's presentation runtime is byte-identical to the
  runtime at the pin. A test re-reads the pin from git to confirm this.
- Presentation fingerprints, per moment: `S02_COMPASS_PROMPT` `97b2108a3017…`,
  `S02_MOVED_COMPASS` `55442af80d38…`, `S03_REVEAL` `d767adcb0628…`,
  `S03_NEAR_CLUE` `9efc9cfe11b6…`, `S04_DIALOGUE` `f96dd97f00e4…`. The full
  values are in the manifest.
- A fingerprint hashes three parts:
  - **runtime:** the engine rendering, scenes, animation, entities, input,
    interactions, trusted art, `explore/curriculum`, and the Trail plan → scene
    adapter. It excludes audio and the rest of the repository.
  - **packages:** every file of each task-card package.
  - **capture:** the moment recipe, the task-card command, the frame size, and
    the WebP settings.

  When any part changes, `tests/test_journey_snapshots.py` fails with a
  message that names the part, for example: "Journey snapshot for S03
  (S03_REVEAL) is stale: session package files changed; rerun `python
  scripts/capture_journey_snapshots.py --session S03`".
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
`scripts/journey_snapshots.py` expects `moon-meadow` and has a `deferred`
reason. While that reason is set:

- the harness refuses to publish S01;
- tests require that there is no `public/journey/s01/` and no S01 manifest
  entry.

Even with the reason removed, the plain Trail cannot pass: the capture check
requires the Moon Meadow backdrop and trusted art. A test proves that today's
S01 frame is rejected.

After Phase B lands and the Course Kit pin includes it:

1. Delete the `deferred=` line from the S01 row. If Phase B's arrival should
   also require Pixel and the Lantern, add them to the row's `must_show`.
2. Run `python scripts/capture_journey_snapshots.py --session S01`.
3. Regenerate the contact sheet.

Before the pin bump, `--session S01 --preview DIR` shows the frame without
publishing it.
