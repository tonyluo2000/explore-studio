# S06 — Build a Themed Collection

**Canonical mission:** M06 `build-an-object-collection` — Build a Curious Collection

**Audience and format:** Ages 10–14, online, 45 minutes; Python-primary

**Learning objective:** Students can represent exactly three related objects as
dictionaries in one list, trace the first iteration of one plain `for` loop,
and print a design inventory before transferring values to declarative package
objects.

**Prerequisite:** S05 lists and S02 object properties.

## Before class

- Send `student/task-card.md` and confirm the shared Quick Start preflight.
- Validate both `student/explorer-package/` and the read-only
  `student/recovery-package/`.
- Prepare to check every first-iteration trace before students run Python.
- Keep Python-record debugging and YAML validation visibly separate.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Invite a three-object environmental story. | Names a theme and relationship. |
| 0:05–0:12 | 6–8 min | Model one dictionary lookup and trace only the first loop iteration. | Completed first-iteration trace before execution. |
| 0:12–0:29 | 15–18 min | Students complete exactly three records, run one plain loop, then repair the isolated malformed record. | Three inventory lines and missing-property explanation. |
| 0:29–0:38 | 8–11 min | Use the transfer table; edit/validate the three YAML objects and launch M06. | Valid package and three visible related objects. |
| 0:38–0:42 | 3–5 min | Visit all objects and compare predicted duplicates/missing properties with results. | M06 completion and one story explanation. |
| 0:42–0:45 | 3–5 min | Inspect status/diffs; commit or schedule it. | Descriptive commit or documented plan. |

**Teacher cut line:** At 0:29, stop Python embellishment. Protect the first-loop
trace, one successful three-record inventory, and the malformed-record repair.
At 0:38, use the prevalidated recovery package for a world demonstration if
student YAML remains invalid. Finish Git asynchronously if needed.

## Student task and prediction

Students follow `student/task-card.md`. Require the written first-iteration
trace and duplicate/missing-property prediction before allowing execution.

## Deliberate debugging exercise

`student/debug.py` contains one record with no `y`. Students predict the missing
property, add it, and access it only after the main three-record loop works.
Then they begin a separate YAML validation phase; do not combine error hunts.

## Expected output and behavior

The starter prints exactly three lines in list order. Its third name visibly
contains `TODO` until personalized. After valid transfer, the world contains
exactly three package objects with distinct authored identities and responses.
M06 completes after all classroom objects are interacted with.

## Bounded AI assistance

Workflow: explain intent → predict → bounded question → test → revise → explain
accepted code. AI may explain one iteration only after the student supplies the
first trace. It must not generate the collection, loop, package, or theme.

## Git close

Use the task card sequence through `git diff --staged`. Interpret status before
staging; use shared identity/cancel/retry recovery. Understanding outranks a
rushed live commit.

## Optional extension

Improve the environmental story through the existing three response strings.
Do not add records, loops, package fields, or objects.

## Teacher notes and answer key

- First record: Sun Seed; x is `180`; output is `Sun Seed 180 180 gold`.
- Malformed record: add an integer `y`, for example `"y": 240`, before reading
  `broken_record["y"]`.
- Exactly one list, three dictionaries, and one plain `for` loop are sufficient.
  Reject comprehensions and nested loops as out of scope, not as “more advanced
  solutions.”
- Python prints a planning inventory. Only validated YAML supplies runtime data.
- A YAML failure is repaired from its validator location after Python debugging
  ends. The recovery package is read-only and must validate unchanged.
