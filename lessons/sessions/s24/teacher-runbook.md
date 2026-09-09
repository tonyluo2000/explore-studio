# S24 — Fast Ranger Index

**Role:** Python-primary software fluency

**World reuse:** M15 `complete-actions-in-order`

**Learning objective:** Students can compare repeated linear scans with one
ID→record dictionary by counting inspections, defining duplicate failure, and
proving equivalent ordered results.

**Prerequisite:** S16–S23 lists/dictionaries, searching, validation, and tests.

## Before class

- Confirm Quick Start repository/venv/package command, Trail focus/controls,
  screen sharing, Git identity, accessibility, and low-bandwidth route.
- Prepare paper/tally versions of the 6- and 12-record catalogs.
- Validate the M15 package and paste complete commands in chat.
- Do not introduce timing benchmarks or Big-O terminology as requirements.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: help rangers stop rereading the whole clue catalog. | Names repeated work. |
| 0:04–0:10 | 5–6 min | Trace small counts; ask what doubling changes. | Two count predictions. |
| 0:10–0:28 | 16–18 min | Run scans/index; assert equivalence and duplicate failure. | Counts and passing tests. |
| 0:28–0:35 | 6–7 min | Validate/play the resolved M15 route. | Three IDs visited in order. |
| 0:35–0:42 | 6–7 min | Debug missing/duplicate/order cases; explain cost. | Fail-closed and equality evidence. |
| 0:42–0:45 | 2–3 min | Inspect code+tests; commit or schedule. | Descriptive Git close. |

**Teacher cut line:** At 0:28, stop optional missing-ID work. At 0:35, accept
validator PASS plus teacher M15 demonstration. Protect both count predictions,
equivalence, and duplicate failure. Git may finish asynchronously.

## Student task and prediction

Require hand-counted 6 and 12 predictions before execution. Ask “what happens
when data doubles?” and request a sentence about repeated work, not vocabulary.

## Deliberate debugging exercise

Use duplicate IDs to require `ValueError`, a missing ID to check aligned `None`,
and an accidental set/sort conversion to expose route-order loss.

## Expected output and behavior

Small comparison is `(15, 6, [...])`; larger is `(33, 12, [...])`. Both methods
return identical ordered records. Duplicate index construction fails closed. M15
completes Signal Map → River Token → Summit Bell.

## Bounded AI assistance

Use the canonical workflow. AI may ask one comparison question after predictions;
it may not calculate the table or generate a generalized algorithm.

## Git close

Use status, diff, intentional stage, `git diff --staged`, and a descriptive
code-with-tests commit. Interpret `M`, `??`, no output, identity failure, and
cancel/retry. Understanding takes priority over a rushed commit.

## Optional extension

Move targets earlier and explain changed scan counts without formal notation.

## Teacher notes and answer key

- Size 6 targets positions 4+5+6 = 15; one index build = 6.
- Size 12 targets positions 10+11+12 = 33; one index build = 12.
- Doubling increases the one-time build proportionally; repeated late searches
  redo much more inspection work.
- Equality must preserve list order. Duplicate IDs raise before use.
- This local dictionary never becomes a Trail cache or package field.
