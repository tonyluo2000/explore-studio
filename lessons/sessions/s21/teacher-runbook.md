# S21 — Package Gatekeeper

**Role:** Python-primary software fluency

**World reuse:** M06 `build-an-object-collection`

**Learning objective:** Students can defensively validate record shape, required
fields, types, ranges, and unique IDs while returning diagnostics in a stable,
predicted order.

**Prerequisite:** S20's known-shape pipeline and shared Quick Start readiness.

## Before class

- Confirm repository, venv, `explore-package`, Trail controls/focus, sharing,
  accessibility route, and Git identity with the Quick Start.
- Confirm `invalid-package` fails validation and `explorer-package` validates.
- Paste both validator commands and the complete M06 launch command in chat.
- Prepare printed malformed records and ordered diagnostic cards.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: appoint gatekeepers for expedition data. | Names why one unsafe field. |
| 0:04–0:10 | 5–6 min | Fix the diagnostic order; require predictions. | Ordered failure list. |
| 0:10–0:28 | 16–18 min | Run table cases; add one malformed case and repair it. | Valid/malformed assertions pass. |
| 0:28–0:35 | 6–7 min | Show invalid package fail closed, then launch repaired M06. | Failure, PASS, three visible tools. |
| 0:35–0:42 | 6–7 min | Test missing/type/range/duplicate cases one change at a time. | Explains error order and repair. |
| 0:42–0:45 | 2–3 min | Review behavior plus test in staged diff; commit or schedule. | Regression-focused Git close. |

**Teacher cut line:** At 0:28, stop extra case writing. At 0:35, accept the
validator PASS and teacher M06 demo. Protect one full ordered prediction and one
student-added regression case. Git may finish asynchronously.

## Student task and prediction

Students must predict every failing category and its printed order before running.
Ask why duplicate detection appears after per-record field/type/range checks.

## Deliberate debugging exercise

The malformed table combines an invalid x range, wrong y type, unsupported color,
missing name, and duplicate ID. The invalid package has a missing contribution
path and must fail closed; it is never a Trail launch root.

## Expected output and behavior

The starter prints `valid []` then the five diagnostics in the documented order.
The invalid package fails validation. The repaired package validates and M06
shows Compass Flag, Field Lens, and Echo Marker.

## Bounded AI assistance

Workflow: explain intent → predict → bounded question → test → revise → explain
accepted code. AI may supply at most one malformed example after predictions. It
may not write a validator, reorder the errors, or provide a complete solution.

## Git close

Use status, diff, intentional stage, `git diff --staged`, and a descriptive
behavior-plus-regression commit. Interpret `M`, `??`, and no output; use identity
and cancellation/retry guidance. Understanding beats a rushed commit.

## Optional extension

Test one inclusive coordinate boundary without expanding validation scope.

## Teacher notes and answer key

- Expected order: y type, x range, unsupported color, missing name, duplicate ID.
- Non-dictionary row returns `record N: expected a dictionary`.
- Multiple errors are useful; fail-closed means no launch after validation fails.
- Local Python teaches reasoning only; the existing package validator remains
  authoritative for YAML entering Trail.
