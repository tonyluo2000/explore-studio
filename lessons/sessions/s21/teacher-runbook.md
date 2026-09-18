# S21 — Package Gatekeeper

**Role:** Python-primary software fluency

**World reuse:** M06 `build-an-object-collection`

**Learning objective:** Students can defensively validate record shape, required
fields, types, ranges, and unique IDs while returning diagnostics in a stable,
predicted order, and can repair one genuinely invalid Explorer Package
themselves using the existing validator's diagnostic.

**Student-owned action:** The student interprets the real validator diagnostic
for `student/invalid-package`, authors the missing contribution file with their
own field values, reruns the validator, and explains why it now passes.

**Prerequisite:** S20's known-shape pipeline and shared Quick Start readiness.

**Arc note:** First session of the **S21–S24 Build Quality / Systems Practice**
mini-arc, which follows S16–S20 Data Fluency and prepares S25 Milestone B. The
bridge line for students is: "We built a pipeline in S20; now we learn how to
tell whether what we built is valid." Ownership across the arc rises as
validate → debug → compose → optimize, so S25 is not the first ownership jump.

## Before class

- Confirm repository, venv, `explore-package`, Trail controls/focus, sharing,
  accessibility route, and Git identity with the Quick Start.
- Confirm `invalid-package` fails validation and `explorer-package` validates.
- Paste both validator commands and the complete M06 launch command in chat.
- Prepare printed malformed records and ordered diagnostic cards.
- Keep a clean copy of `invalid-package` so the broken state can be restored
  between learners sharing a machine; students create a file inside it.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: appoint gatekeepers for expedition data. | Names why one unsafe field. |
| 0:04–0:10 | 5–6 min | Fix the diagnostic order; require predictions. | Ordered failure list. |
| 0:10–0:28 | 16–18 min | Run table cases; add one malformed case and repair it. | Valid/malformed assertions pass. |
| 0:28–0:35 | 6–7 min | Students read the real diagnostic, author the missing file, rerun. | Diagnostic, repair, PASS, explanation. |
| 0:35–0:42 | 6–7 min | Test missing/type/range/duplicate cases one change at a time. | Explains error order and repair. |
| 0:42–0:45 | 2–3 min | Review behavior plus test in staged diff; commit or schedule. | Regression-focused Git close. |

**Teacher cut line:** At 0:28, stop extra case writing. At 0:32, if the repair
is not passing yet, supply one field value and keep the student's explanation.
At 0:35, accept the validator PASS and a teacher M06 demo instead of every
student launching. Protect one full ordered prediction, the student-authored
repair with its explanation, and one student-added regression case. Git may
finish asynchronously.

## Student task and prediction

Students must predict every failing category and its printed order before running.
Ask why duplicate detection appears after per-record field/type/range checks.

## Deliberate debugging exercise

The malformed table combines an invalid x range, wrong y type, unsupported color,
missing name, and duplicate ID. The invalid package has a missing contribution
path and must fail closed; it is never a Trail launch root until the student
repairs it.

## Expected output and behavior

Observable evidence for this session:

- The starter prints `valid []` then the five diagnostics in the documented
  order.
- `explore-package validate lessons/sessions/s21/student/invalid-package`
  fails with `FILE_MISSING: contributions[0].path ... declares missing file
  "objects/missing-tool.yaml"`.
- The student's authored record returns `[]` from their own `validate_records`
  before the file is written.
- The same validator command passes after the student creates
  `invalid-package/objects/missing-tool.yaml` with their own field values.
- The student's sentence names the failed check, the change, and why the
  validator is satisfied — not just "I added a file."
- `explorer-package` validates and M06 shows Compass Flag, Field Lens, and Echo
  Marker.

## Likely failure modes and recovery

| Failure mode | What you will see | Recovery |
|---|---|---|
| Student "repairs" by deleting the manifest entry | Validator passes but the package is empty of the promised object | Restore the entry; the contract is the promise, the file is the obligation |
| Unsupported colour chosen | `is not a valid colour; choose from: ...` | Read the listed options in the diagnostic and pick one |
| `x`/`y` written as text | `must be a whole number of 0 or greater` | Remove the quotes; compare with the wrong-type row in the starter table |
| Empty or whitespace field | `must not be empty or whitespace-only` | Author real text; placeholders are not repairs |
| Wrong file name or folder | The original `FILE_MISSING` diagnostic repeats unchanged | Match the manifest path exactly, including `objects/` |
| Repair not restored between learners | Next student sees a passing package and no diagnostic | Delete `invalid-package/objects/missing-tool.yaml` before the next run |

## Bounded AI assistance

Workflow: explain intent → predict → bounded question → test → revise → explain
accepted code. AI may supply at most one malformed example after predictions. It
may not write a validator, reorder the errors, interpret the package validator's
diagnostic, author the student's repair file, or provide a complete solution.

## Git close

**ZIP classes:** Skip this step for classes still on the ZIP distribution that have not started the Git lesson yet; use it once the class has a Git-managed course folder. See [Student Quick Start → Later: Git](../student-quick-start.md#later-git-optional-teacher-managed).

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
- The repair adds only a file. No manifest, schema, or validator semantics
  change, and no new field is invented: `name`, `x`, `y`, `color`, `when_near`,
  and `when_interacted` are all v0.1 world-object fields that already exist.
- `id` is deliberately absent from the object file body. It comes from the
  manifest contribution, which is why the student's local `validate_records`
  shape and the package contract are not identical. Make that difference
  explicit rather than smoothing it over.
