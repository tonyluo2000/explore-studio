# S22 — Traceback Detective

**Role:** Python-primary software fluency

**World reuse:** M08 `respond-to-object-state`

**Learning objective:** Students can reproduce a failure, identify its exception
and first relevant student-code traceback frame, predict a cause, make one repair,
rerun, and add a regression assertion.

**Prerequisite:** S21 validation and shared Quick Start readiness.

## Before class

- Confirm repo/venv, Python, package command, Trail controls/focus, sharing, Git
  identity, and accessibility route with the Quick Start.
- Run each `debug.py` case separately and prepare an unedited recovery copy.
- Validate the package and paste Python plus full Trail commands in chat.
- Prepare a traceback screenshot with framework frames visually de-emphasized.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: investigate why the prism guardian stopped answering. | Names evidence before guesses. |
| 0:04–0:10 | 5–6 min | Model exception type vs relevant frame; require predictions. | Three failure predictions. |
| 0:10–0:28 | 16–18 min | Cycle reproduce/frame/cause/change/rerun/assert. | Three repair receipts. |
| 0:28–0:35 | 6–7 min | Validate and test M08 off/on behavior. | Sleeping/open messages observed. |
| 0:35–0:42 | 6–7 min | Rerun regression assertions; restore one bug to prove detection. | Failed then passing regression. |
| 0:42–0:45 | 2–3 min | Inspect one focused fix+test diff; commit or schedule. | Cause-focused Git close. |

**Teacher cut line:** At 0:28, finish the active case and use recovery support
for remaining cases. At 0:35, accept validator PASS and teacher M08 demonstration.
Protect one complete traceback receipt and regression assertion. Git may finish
asynchronously.

## Student task and prediction

Do not accept “the red text” as an interpretation. Require exception type, file,
line/function, and predicted cause before an edit.

## Deliberate debugging exercise

- `KeyError`: asks for absent `message`.
- Off-by-one: `clues[len(clues)]` is one past the last index.
- Incorrect return: on/off strings are inverted and trip an assertion.

## Expected output and behavior

The repaired starter prints `3 regression checks pass`. The M08 package validates;
guardian says sleeping while off and open after the switch turns on.

## Bounded AI assistance

Use the canonical workflow. AI gives one hint at a time only after the student
interprets the traceback. It may not propose a repair before frame/cause evidence.

## Git close

Review status, diff, stage, `git diff --staged`, then commit one isolated fix with
its regression test. Interpret `M`, `??`, no output, identity errors, and retry.
Understanding takes priority over a rushed commit.

## Optional extension

Add one exact-message regression without introducing new branch logic.

## Teacher notes and answer key

- Relevant frames are the call inside each prepared function, not Python internals.
- Repairs: use an existing key; use `len(clues) - 1`; return open for True and
  sleeping for False.
- Restore clean prepared files between learners if sharing a machine.
- Python stays local; the repaired world payoff is existing declarative M08.
