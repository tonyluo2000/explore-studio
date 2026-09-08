# S20 — Data-Built Mystery Trail

**Role:** Balanced data-fluency milestone using the Python-primary rhythm

**World reuse:** M15 `complete-actions-in-order`

**Learning objective:** Students can trace and test a deterministic local
pipeline that safely loads prepared YAML, validates a known shape, searches,
aggregates, stably sorts, transforms, writes current-contract YAML, validates
the package, and plays its M15 sequence.

**Prerequisite:** S16–S19 data traversal/search/summary/sort work and shared
Quick Start readiness. Use prepared scaffolding only.

## Before class

- Confirm PyYAML is available through the project environment; do not install
  packages during class.
- Validate the committed generated package and paste build/validate/Trail commands.
- Prepare one `sun-compass` pipeline trace and confirm the prepared
  `student/test_pipeline.py` normal, boundary, and malformed tests run.
- Offer text/YAML diffs and one teacher Trail demonstration for low bandwidth.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: turn a mystery plan into a playable trail. | Names input and desired visible payoff. |
| 0:04–0:10 | 5–6 min | Trace one record through four stages before running. | Input→transform→output→world prediction. |
| 0:10–0:28 | 16–18 min | Run prepared scaffold; complete known-shape checks and three test TODOs. | Safe load, valid records, ordered deterministic files. |
| 0:28–0:35 | 6–7 min | Validate generated package and play first-three M15 route. | Validator success and visible completion. |
| 0:35–0:42 | 6–7 min | Run normal, exactly-three boundary, malformed record, and repeat-output checks. | Passing tests and stable byte comparison. |
| 0:42–0:45 | 2–3 min | Review milestone diff/self-review; commit or schedule. | Explanation and descriptive Git close. |

**Teacher cut line:** At 0:28, stop optional story edits and retain the prepared
transform/write scaffolding. At 0:35, accept successful validation plus a teacher
M15 demo. Protect one complete trace, three tests, and self-review. Git may finish
asynchronously.

## Student task and prediction

Students trace Sun Compass from input record to included selection, priority-1
position, `objects/sun-compass.yaml`, and first M15 object before running Python.

## Deliberate debugging exercise

Normal case builds three ordered objects. Boundary case has exactly three included
records and must pass. A copied malformed record with missing/wrong-type required
data must fail local validation before writing. Run the builder twice to verify
stable file names, contribution order, key order, and bytes.

## Expected output and behavior

Safe loading uses `yaml.safe_load`. Selected priorities total 6 and sort to Sun
Compass, Whisper Stone, Tide Chime. `yaml.safe_dump(..., sort_keys=False)` writes
schema v0.1 deterministically in prepared insertion order. The package validator
passes and M15 completes in that three-object order.

## Bounded AI assistance

Follow explain intent → predict → bounded question → test → revise → explain
accepted code. AI may ask one pipeline question or propose one test only. It may
not generate the pipeline, package, or whole-file answer.

## Git close

Review input, Python, generated YAML, and tests as one milestone diff. Stage only
under S20, inspect `git diff --staged`, and use shared identity/retry guidance.

## Optional extension

Change one prepared story field and verify deterministic regeneration. Advanced
comprehensions/generators remain out of core work.

## Teacher notes and answer key

- Known object shape: nonblank string ID/name/color, integer nonnegative x/y,
  integer priority, Boolean include. Reject booleans where integers are expected.
- Normal: four source records, three included, order 1/2/3, total 6.
- Boundary: exactly three included is valid. Two or four included must fail the
  fixed M15-output check.
- Malformed example: missing `priority` or string coordinate fails before write.
- Stable output means two builds from identical input produce identical relative
  paths and UTF-8 bytes; it does not mean sorting arbitrary keys alphabetically.
- All arbitrary Python and YAML I/O are local. Shared runtime sees only the
  successfully validated declarative Explorer Package.
