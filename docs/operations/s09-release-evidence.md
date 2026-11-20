# S09 Power Up a Device release candidate — 2026-11-20

Prepared in [implementation PR #136](https://github.com/tonyluo2000/explore-studio/pull/136).
Risk: **C**. No merge, deployment, or public Course Kit replacement is authorized by this preparation.
Independent review must name the exact final PR head. Owner approval and a separate one-file
Course Kit publication PR are required before replacing the production download.

## Exact baseline and commit chain

- Main/base verified through GitHub and `git fetch origin main`:
  `6daaf65695eff9ff98b164723752d131f555c5ab`.
- Tested implementation head: `3f602e059447909e9b5be625907111f8c04d589f`.
  This evidence document is committed afterward; its final commit SHA is recorded in the PR
  description and release response. Review must cover that final head, including this document.
- Runtime commit: `ee64c3957661dc574f5ac9e971bf3f687e4dc25f`.
- Candidate materials source: `1ad1213f99ad5a949327efbacf8e2b8f215cb37c`.
  Subsequent changes affect QA, Journey layout, snapshot provenance and operations evidence;
  the candidate's student materials and runtime pin remain identical to that committed source.
- Production observed before implementation: Slides S01–S08; Explorer current Cloud Gate/S08;
  Python current S08 · if / else; both 8/30; S09 unpublished.
- Live Course Kit SHA256:
  `18d39be79996a25c414a0f643464e93cbb38905f92fe74f440bcb90bcabcf3c4`.
- Live materials source: `882419f8226e89855c9cafeee3dad6b8b61afe6f`.
- Live/old runtime pin: `d1e89a1d260ba647dcac09e9237faa397f2faee7`.
  The downloaded live ZIP and the committed production ZIP have identical bytes.

## Package identity, presentation and semantics

Canonical package: `storm-engine` version `0.1.0`, schema `0.1`;
contribution/object: `storm-engine:storm-engine`; M09: `count-object-interactions` / Power It Up.
The canonical task card, starter, runbook, manifest and object YAML remain byte-identical to base.
Authored position `(420, 300)`, purple color, goal `3`, and all authored messages are unchanged.
No gameplay, package schema, student API, or student workspace protection code changes.

Only the exact M09/`storm-engine` package pair opts into Moon Meadow. Reused M09 missions and
S10's comparison mission remain plain. Nova uses trusted art; a private Storm Engine art role
receives bounded charge-cell poses. It does not interpret student response strings. The presentation
reads the real count and authored goal for that role only; it does not expose generic counter
internals to the sprite renderer. Authored color remains the casing/core accent.

The device starts with empty cells. Each action fills another cell and grows the core; the final
state adds a lightning shape and sparks. Filled bars and white ticks communicate progress in
addition to color. The shared prompt, wrapped package feedback, mission HUD, audio and first
completion celebration remain active. Cosmetic spawn `(280, 300)` does not move authored objects.

| Interaction | Count | M09 | Feedback |
|---|---:|---|---|
| Start | 0 | Incomplete | Authored near message |
| 1 | 1 | Incomplete | Authored interaction message + Count 1 / 3 |
| 2 (one before goal) | 2 | Incomplete | Count 2 / 3; one cell empty |
| 3 (exact goal) | 3 | Complete | Count 3 / 3 + authored goal-reached message |
| 4 (post-completion) | 4 | Complete | Count 4 / 3 + same goal message |

No early completion, extra success press, cap, reset or decrement. Post-goal interactions preserve
completion/evidence and do not restart celebration. Tests also exercise authored goals 2, 3, 4, 5,
student-edited colors/messages/coordinates, and absence of NPC/comparison-branch evidence.
M09 gameplay semantics are unchanged. No S10 mechanic is added.

## Python and website publication

- `/students/slides/s09/`: twenty Python-primary teaching cards, canonical one-line Trail command,
  prediction/trace, update, loop, deliberate off-by-one repair, one assertion, validation and launch.
- `/students/learn/s09/`: integer state, updates, loops, off-by-one and a basic assertion, with an
  executable worked example. The existing data-driven Learn route publishes it.
- The canonical starter's loop is already correct; its intended unfinished task is the assertion.
  Students add it, deliberately change `range(1, goal + 1)` to `range(1, goal)`, predict/observe count 2
  and `AssertionError`, restore the stop value, rerun and explain the silent passing check.
- Local Python models counting; YAML declares goal/message; Trail owns session interaction state.
  Student Python does not execute inside Trail. Story continuity does not promise persistent charge.
- Both journeys advance to S09, 9/30. Python topic: Counters and loops. Compact S09 history shows
  `+ 4 earlier Python steps` and S05–S09; the full history shows S01–S09. S08 keeps its eight-step context.
- Explorer current stop: Storm Engine; its story prepares the observatory check. The new map device
  sits clear of the existing Guide bubble. S06 Garden Markers, S07 Sky Lantern and S08 Cloud Gate
  remain historical, session-local cards and maps; S09 never replaces their focus.
- S01–S08 Slides/Learn content and canonical lesson/package files remain unchanged.
- Public detail stops at S09. S10 has calendar title/date and a generic next reference only.
  No S10 Slides, Learn, Journey stop, snapshot, Python objective/capability or comparison teaching.
  Tests scan exported HTML, RSC/text payloads, metadata and JS bundles, including hidden markup.

## Runtime snapshot and identity

HERO: `S09_DEVICE_POWERED`, captured from actual movement and E input at count 3, with Nova,
all charge cells lit, authored goal message, Goals 1 / 1 and mission complete. No compositing.

- Source RGB SHA256: `12f8c433a484c9c577c0900c32c9b1066a0168afa83d07b0036f115a2919c28e`.
- `public/journey/s09/hero.webp` (98,568 bytes):
  `ee6b5cd54700be21ff877b67de5d22eea25f27e9e5e5dc3804f35b032a14a961`.
- `public/journey/s09/hero-480.webp` (36,088 bytes):
  `9cf17d0e132cc61f2ef03c85824566597b5bddaea76f67b5b817f649802b466b`.
- All retained S01–S08 source RGB hashes and published WebP bytes equal main.
  Only fingerprint/provenance metadata refreshes. Earlier capture recipes explicitly exclude the new device.
- `python3 scripts/capture_journey_snapshots.py --check`: fresh.
- `build/s09-release/identity-receipt.json`: all historical RGB and Trail QA PNG hashes.
- Toolchain: Python 3.13.7, pygame 2.6.1, Pillow 11.2.1. No S10 assets.

## Candidate Course Kit — built, not published

- New runtime pin: `ee64c3957661dc574f5ac9e971bf3f687e4dc25f`.
- Candidate SHA256: `df862d82b3529105564cad6958c0240c35ed441ffc53987ff62e286b1429a995`.
- **253 members**; embedded materials source `1ad1213f99ad5a949327efbacf8e2b8f215cb37c`.
- Two deterministic builds are byte-identical. A third rebuild from that immutable Git commit
  through the existing provenance checker is also byte-identical.
- Contains canonical S09 student materials and requirements pinned to the polished S06–S09 runtime.
  No `my-explore-world`, teacher runbook, runtime source, or virtual environment is included.
- Artifacts: `build/s09-release/candidate/explore-studio-course.zip`, `repeat/`, `immutable/`,
  `course-kit-receipt.json`, `course-kit-members.txt`, `candidate-provenance.log`.
  These are ignored local build artifacts, outside the public website directory.
- Fresh install: extracted candidate; new `.venv`; installed its unchanged requirements directly
  from the pinned GitHub archive. PEP 610 identifies the exact new runtime. S08 completes with both
  responses; S09 is polished and completes exactly at goal, then remains complete after another action.
- The shipped `check-my-computer.py` logic reports READY using its supported isolated `home=` argument;
  machine, installed runtime, venv, dependency and real window-launch facts are detected, not mocked.
  Running the CLI at the isolated build path correctly refuses that noncanonical home location.
  No user home folder or environment HOME was changed. See `fresh-readiness.log` and `fresh-acceptance.log`.
- Student workspace replacement/preservation checks remain part of the full suite.
- Production Course Kit remains unchanged, with the live SHA256 above. Do not sync this candidate
  into `public/downloads/` in this implementation PR.

## Validation and visual QA

- Nine requested test files: **606 passed** (`requested-tests-final.log`), including rendered-site tests.
- Full suite: **3375 passed, 1 skipped, 2 existing pygame shutdown-thread warnings** (`full-suite-final.log`).
- `tsc --noEmit`, `eslint .`, `next build --webpack`: pass; all S01–S09 Slides/Learn routes exported.
- Focused Ruff check and workflow YAML parsing: pass. `git diff --check`: pass.
- Snapshot freshness, determinism, runtime/audio/package validation, Course Kit provenance and
  student workspace protection are covered by the full suite.
- Shared browser QA: **46 responsive/accessibility checks passed**, at 390×844 and 1440×1000,
  including all published Slides/Learn pages, Journey, bounded compact-history simulations,
  keyboard links and companion-panel axe checks. Lazy-loaded snapshots are decoded before capture.
- Additional S09 QA: **10 content/listing checks passed** at both sizes: calendar, session listing,
  all S09 Slides/Learn teaching cards and Journey; no document overflow or future comparison text.
- Visually inspected real initial/partial/exact/post-goal Trail frames; readable prompt/goal message,
  reachable device, numeric and cell progression, mission HUD clear of overlays, no clipped text.
  Exact-goal and completion share interaction 3. Captures: `build/s09-release/trail/`.
- Browser screenshots/reports: `build/s09-release/website/` and `website-content/`.
  S06/S07/S08 historical cards remain frozen. Final map screenshot places the new device clear of
  the Guide's speech bubble. Mobile Slides visibly shows only five recent Python steps at S09.

Reproduce runtime proof with `python3 scripts/capture_s09_visual_proof.py build/s09-release/trail`.
For browser scripts use Playwright and axe module paths plus `QA_BROWSER_PATH`, `QA_OUTPUT_DIR`, and
serve the fresh static export on localhost:4177. Scripts: `tests/python_journey_visual_qa.mjs` and
`tests/s09_release_visual_qa.mjs`. Simulated future histories are in memory only.

## Review gate and known limitations

Independent exact-head review is pending; it is not represented as completed by the author.
The final PR description and release response identify the final head. No merge or deployment.
After review, merge and owner approval, prepare a separate one-file Course Kit publication PR.

Existing warnings: Node's TypeScript probe emits a module-type inference warning. The full suite
emitted two existing pygame test-helper shutdown-thread warnings (`tests/test_scenes.py`), with no test failures.
Runtime capture is headless using real pygame rendering/input; it does not constitute a new
physical Windows/WSL device rehearsal. Candidate install acceptance is isolated as described above.
