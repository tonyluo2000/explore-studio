# S11 — Require Both Keys

**Canonical mission:** M10 `require-all-switches-on` — Unlock the Secret

**Audience and format:** Ages 10–14, online, 45 minutes; Python-primary

**Learning objective:** Students can complete a four-case truth table, define a
two-Boolean-parameter function using `and`, compare predicted and observed
results, and connect the rule to the existing two-toggle AND world behavior.

**Prerequisite:** S07 Boolean state, S08 conditions, shared Quick Start, and a
working local Python/venv and `explore-package` command.

## Before class

- Confirm students are in the repository root and can run local Python.
- Validate the Twin Star Vault package and prepare the long Trail command in chat.
- Keep the answer key hidden until all four prediction rows are complete.
- Offer the shared low-bandwidth route: printed output, package fields, and a
  teacher Trail demonstration are acceptable evidence.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Quick-start check; frame two celestial keys that must both turn. | Python/venv ready; states “all conditions must be true.” |
| 0:05–0:13 | 7–9 min | Withhold the operator; require all four truth-table predictions and reasons. | Four completed cases before running. |
| 0:13–0:26 | 12–14 min | Run the flawed function, locate the mismatch, repair it with `and`, and rerun. | Correct function and expected-versus-observed comparison. |
| 0:26–0:40 | 12–15 min | Map the table to two toggles; validate, launch M10, show fallback and success. | Both authored NPC branches and M10 completion. |
| 0:40–0:42 | 2–3 min | Capture checkpoints and AI receipt if used. | Explanation of why both-on is unique. |
| 0:42–0:45 | 3–5 min | Interpret status/diffs; commit or schedule it. | Descriptive commit or recovery plan. |

**Teacher cut line:** At 0:26, stop extra Python examples and keep the four-case
comparison. At 0:38, stop relaunching after one fallback and one both-on result;
use screenshots/text evidence if needed. Git may finish asynchronously.

## Student task and prediction

Students use `student/task-card.md`. Do not let them run `starter.py` until all
four rows are filled. This is direct Boolean composition, not another S08
if/else exercise: the function should return the `and` expression itself.

## Deliberate debugging exercise

The runnable starter incorrectly returns only `first_on`. Students locate the
case `True, False`, where observed True disagrees with predicted False, then
replace the return with `first_on and second_on` and retest all four rows.

## Expected output and behavior

The repaired output ends in `False, False, False, True` in case order. In the
Trail, either key off produces `when_not_all_on`; both keys on produces
`when_all_on`. Students must display both branches to complete M10.

## Bounded AI assistance

Workflow: explain intent → predict → bounded question → test → revise → explain
accepted code. Only after the student completes the table may AI inspect it and
flag one discrepancy. It may not fill the table or write the function.

## Git close

Use the task card and shared Git interpretation/recovery. Confirm `M`, `??`, no
output, and the staged diff before a descriptive commit. Understanding outranks
a rushed commit.

## Optional extension

Rename the keys and responses while preserving exactly two inputs and the AND
rule. Do not add nesting or new runtime behavior.

## Teacher notes and answer key

- Cases `(False, False)`, `(False, True)`, `(True, False)`, `(True, True)` return
  `False`, `False`, `False`, `True`.
- Answer: `return first_on and second_on`.
- The faulty return accidentally ignores the second parameter.
- The package's plain fields reference two same-package toggles. Local Python is
  never imported or run by the Trail.
- If keys appear inactive: validate, save, relaunch, focus the Trail window, use
  WASD/arrows, approach a key, and tap E once.
