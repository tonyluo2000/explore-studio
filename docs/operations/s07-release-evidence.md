# S07 Sky Lantern release candidate — 2026-11-06

S07 is prepared for review on `codex/publish-polished-s07`. Risk: **C**.
Do not merge, deploy, or replace the production Course Kit in this preparation step.
Independent review must name the exact PR head; record its result in the PR and release response.
Production Course Kit replacement still requires exact-head independent review, owner authorization,
merge, and a separate publication step.

## Baseline and scope

- Base: `4fad6962f2c712b4eb86fed223a2010bf1b09303` (`origin/main`, merged Python Journey PR #126).
- Before editing: S01–S06 published, S07 calendar entry unpublished, Python Journey S06 at 6/30,
  Explorer Journey current S06, S07 Python topic internal, and S08+ unpublished.
- Confirmed canonical S07 task card, starter, package and teacher runbook. M07 is
  `toggle-an-object-state` / Flip a Magic Switch; package `sky-lantern-switch`, object Sky Lantern.
- Package YAML and starter bytes are unchanged. Authored position remains `(360, 300)`;
  authored colors remain blue/gold and both authored response strings remain unchanged.
- No mission, scene gameplay, NPC, gate entity, counter, S08 behavior or student-workspace
  protection implementation changes are included.

## Runtime and lesson

S07 opts into Moon Meadow only for its exact mission/package pair. Its private Sky Lantern visual
role reuses the existing Crystal Lantern procedural frame rather than the fixed-gold trusted sprite
sheet, so both authored colors (including supported student edits) remain authoritative. Nova uses
trusted course art. OFF has dim cool glass and no bright core; ON has the authored warm color,
a bright core, greater glow, and rising sparks. The bounded player presentation spawn is `(240, 300)`;
it does not move the package object. The authored prompt/feedback, mission HUD, audio and first
completion effects remain readable and consistent with the earlier polished sessions.

The actual state sequence is `False/blue → True/gold → False/blue → True/gold`.
M07 completes after the first toggle change and stays complete afterward. It does **not** verify
final ON/gold. The final lit ending is a classroom/story target confirmed by observation.

- Slides: `/students/slides/s07/`, with the canonical one-line Trail launch from the task card.
- Learn: `/students/learn/s07/`, with the starter's `False gold` misconception and the repaired
  executable output `False blue` then `True gold`.
- Both tracks advance to S07, 7/30; Python current topic is Boolean state.
- Local Python models the idea, YAML declares colors, and Trail owns runtime session state.
- S01–S06 slides and Learn entries remain unchanged and their Python histories remain session-local.
- S06's Journey illustration now explicitly renders its own S06 state: Garden Markers remains
  focused and Sky Lantern is absent from that historical illustration.
- S08 has no public Slides/Learn route, Journey stop, snapshot, assets, or Python objectives.
  Its calendar title/date and generic hidden-gate handoff are the public boundary.

## Snapshot proof

The S07 HERO is the actual runtime frame after one interaction, with Nova, the gold Sky Lantern,
Moon Meadow and M07 complete. The snapshot acceptance contract checks the lantern is ON separately
from mission completion. It does not infer ON from completion.

- Moment: `S07_LANTERN_ON`.
- Source RGB SHA256: `4f842b864fdf7cf5ad0ae66c1c3de27c27592290a31e135662ef9bc57b281d0a`.
- Public images: `course4teen-website/public/journey/s07/hero.webp` and `hero-480.webp`.
- Freshness check passes; the S07 frame and both WebPs regenerate byte-for-byte.
- All S01–S06 source RGB hashes and published image bytes equal the main baseline. The harness
  recaptured retained moments in memory and refreshed only fingerprint/provenance metadata.

Reproduce using the repository's documented pygame/Pillow capture toolchain:

```console
python3 scripts/capture_journey_snapshots.py --check
python3 scripts/capture_journey_snapshots.py --session S07 --dry-run
python3 scripts/capture_s07_visual_proof.py build/s07-release/trail
```

## Candidate Course Kit — built, not published

- Old runtime pin: `8811a5ceff647d4a6f408bb1aa9764b5cd64c607`.
- New runtime pin: `f2cda35dee4929f98c48eab8c48790ea24c7640a`.
- Course-materials source: `222c6b928f7432edbfcdf8b908e099fd8306a73e`.
- Candidate SHA256: `2c97e66ae07ab9ac5abc321b52a61d8cd942585bdeced786827215c83c88f339`.
- Member count: **253**.
- Two builds from the committed source are byte-identical. Embedded `course-materials.json`
  records the source and runtime commits above. The exact pinned runtime contains polished S06
  and S07, and the ZIP contains the S07 student lesson/package files.
- Candidate: `build/s07-release/explore-studio-course-s07.zip`.
- Receipt: `build/s07-release/course-kit-receipt.json`; repeat build in `build/s07-release/repeat/`.
- `~/my-explore-world` protection is unchanged; the archive contains no student workspace.
- Production ZIP is unchanged, SHA256
  `495a1244a651bdc4c2dec7ed4cd950b1729c9d393ae5df0356d296e7fc83297b`.
  Its independent historical-provenance rebuild test passes.

The candidate artifacts and QA files live in ignored `build/`, outside the website's public tree.
They are available locally for owner review and are reproducible from the recorded source commit.

## Validation

- Full suite with `JOURNEY_SITE_OUT=course4teen-website/out`: **3320 passed, 1 skipped**,
  no failures. Two pygame shutdown-thread warnings were emitted from the existing test event
  helper (`tests/test_scenes.py`); they do not affect the test result.
- The full suite includes all nine requested test files, runtime/audio/package tests, snapshot
  determinism/freshness, repeated post-completion toggles, S06 historical focus, public S08
  boundaries, command copy/paste, and Course Kit/student-workspace replacement protections.
- `tsc --noEmit`, `eslint .`, and `next build --webpack`: pass. The static export contains
  Slides and Learn through S07 only. Rendered-site tests are enabled in the full-suite run.
- `git diff --check`: pass.
- CI runs the new `tests/test_lesson_materials_s07_website.py` and S07 runtime regressions.

## Visual QA

`tests/python_journey_visual_qa.mjs` checks 15 actual routes at each of 390×844 and 1440×1000,
plus four simulated long-history cases per width: **38 checks pass**, no document/panel horizontal
overflow, no checked companion-panel accessibility violations, and keyboard-reachable Journey links.
Future simulation stays in memory and publishes no future routes. Screenshots include S07 Slides,
S07 Learn, Journey overview/Python progression, the frozen S06 card, and the S07 runtime HERO card.

The S07 inline-command overflow found on the first mobile run was repaired by placing the command
in a scrollable code block; the final browser run passes at both requested widths.

Local evidence:

- `build/s07-release/website/report.json` and responsive PNGs.
- `build/s07-release/trail/s07-spawn.png`, `s07-near-off.png`, and interaction 1 ON / 2 OFF / 3 ON PNGs.
- `scripts/capture_s07_visual_proof.py` reproduces the runtime images with real movement and E input.

The OFF-after-completion frame visibly demonstrates why a completed M07 does not establish final ON.
No merge, deployment, or production Course Kit replacement was performed.
