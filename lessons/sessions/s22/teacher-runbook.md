# S22 — Traceback Detective

**Role:** Python-primary software fluency

**World reuse:** M08 `respond-to-object-state`

**Learning objective:** Students can run one debugging loop — observe, form a
hypothesis, make one change, rerun, compare evidence — on a prepared failure and
on a bug in their own file, and can tell an input mistake, a contract/validation
mistake, and a logic/behavior mistake apart by where each one surfaces.

**Student-owned action:** The student finds the off-by-one in `clue_count` in
their own `starter.py` from its printed output, writes the assertion that
catches it, watches that assertion fail, makes one change, and reruns.

**Prerequisite:** S21 validation and shared Quick Start readiness.

**Arc note:** Second session of the **S21–S24 Build Quality / Systems Practice**
mini-arc. S21 asked whether the build is valid; S22 asks what to do when it is
valid but wrong. Ownership step: the student diagnoses and repairs a
deterministic bug rather than only reading a teacher fixture's traceback.

## Before class

- Confirm repo/venv, Python, package command, Trail controls/focus, sharing, Git
  identity, and accessibility route with the Quick Start.
- Run each `debug.py` case separately and prepare an unedited recovery copy.
- Run `starter.py` once and confirm it prints `3 regression checks pass` and
  `clues: 2 of ('switch', 'guardian', 'prism')`. That mismatch is deliberate;
  keep an unedited copy so the bug can be restored between learners.
- Validate the package and paste Python plus full Trail commands in chat.
- Prepare a traceback screenshot with framework frames visually de-emphasized.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: investigate why the prism guardian stopped answering. | Names evidence before guesses. |
| 0:04–0:10 | 5–6 min | Model exception type vs relevant frame; require predictions. | Three failure predictions. |
| 0:10–0:28 | 16–18 min | Cycle reproduce/frame/cause/change/rerun/assert. | Three repair receipts. |
| 0:28–0:35 | 6–7 min | Validate and test M08 off/on behavior. | Sleeping/open messages observed. |
| 0:35–0:42 | 6–7 min | Students run the loop on their own `clue_count` bug; break and restore `object_id` to show the contract category. | Assertion seen failing then passing; predicted validator diagnostic. |
| 0:42–0:45 | 2–3 min | Inspect one focused fix+test diff; commit or schedule. | Cause-focused Git close. |

**Teacher cut line:** At 0:28, finish the active case and use recovery support
for remaining cases. At 0:35, accept validator PASS and teacher M08 demonstration.
At 0:40, if the `object_id` demonstration has not happened, run it once yourself
on the shared screen and confirm every student restored their file. Protect one
complete traceback receipt, one regression assertion, and the student's own
`clue_count` repair — that repair is the session's ownership evidence and is cut
last. Git may finish asynchronously.

## Student task and prediction

Do not accept “the red text” as an interpretation. Require exception type, file,
line/function, and predicted cause before an edit.

## Deliberate debugging exercise

- `KeyError`: asks for absent `message`.
- Off-by-one: `clues[len(clues)]` is one past the last index.
- Incorrect return: on/off strings are inverted and trip an assertion.
- `clue_count` in `starter.py`: `len(clues) - 1`. Student-owned, silent, and not
  covered by any shipped assertion — the student must write the check first.

## Three mistake categories

Only these three are supported by what this session actually runs. Do not invent
a fourth.

| Kind | Surfaces as | Session example | Recovery |
|---|---|---|---|
| Syntax/input mistake | A Python traceback naming the exception type | `key-error`, `off-by-one` in `debug.py` | Read the last line for *what*, the first student-code frame for *where*; use an existing key, or `len(clues) - 1` as the index |
| Contract/validation mistake | `explore-package validate` output; no traceback ever appears | `respond_to_toggle.object_id: "no-such-object"` | The diagnostic is `... must resolve exactly once within this package`; restore the real object ID |
| Logic/behavior mistake | Nothing raises; a value or message is simply wrong | `incorrect-return`, and `clue_count` | An assertion you watched fail is the only proof; one change, rerun, compare |

The contract row is why "run it and see if it crashes" is not a complete
strategy: an invalid package is perfectly valid Python.

## Expected output and behavior

Observable evidence for this session:

- Each `debug.py` case raises its documented exception before repair and returns
  cleanly after.
- `starter.py` ships printing `3 regression checks pass` and
  `clues: 2 of ('switch', 'guardian', 'prism')`.
- The student's new assertion fails first. Students who never saw it fail have
  not finished the loop — ask them to reintroduce `- 1` and rerun.
- After the one-character repair, `starter.py` prints `clues: 3 of (...)` and
  all four assertions pass.
- Breaking `object_id` produces a validator diagnostic and no traceback;
  restoring it returns the package to PASS.
- The M08 package validates; the guardian says sleeping while off and open after
  the switch turns on.

## Likely failure modes and recovery

| Failure mode | What you will see | Recovery |
|---|---|---|
| Student edits `clue_count` before writing the assertion | Passing code, no failing-test evidence | Have them restore `- 1`, run the assertion, then repair again |
| Student "fixes" by changing `CLUES` | Count matches but the data was the correct part | The report was wrong, not the clue list; revert the tuple |
| Student changes several things at once | Cannot say which change mattered | Revert to the unedited copy and restart the loop with one change |
| `object_id` left broken after the demonstration | The world payoff never launches | `git diff`, or restore `"prism-switch"` from the recovery copy |
| Shared machine still holds a previous repair | No bug to find | Restore the unedited `starter.py` and `debug.py` between learners |

## Bounded AI assistance

Use the canonical workflow. AI gives one hint at a time only after the student
interprets the traceback. It may not propose a repair before frame/cause
evidence, locate the `clue_count` bug, or write the student's regression
assertion.

## Git close

**ZIP classes:** Skip this step for classes still on the ZIP distribution that have not started the Git lesson yet; use it once the class has a Git-managed course folder. See [Student Quick Start → Later: Git](../student-quick-start.md#later-git-optional-teacher-managed).

Review status, diff, stage, `git diff --staged`, then commit one isolated fix with
its regression test. Interpret `M`, `??`, no output, identity errors, and retry.
Understanding takes priority over a rushed commit.

## Optional extension

Add one exact-message regression without introducing new branch logic.

## Teacher notes and answer key

- Relevant frames are the call inside each prepared function, not Python internals.
- Repairs: use an existing key; use `len(clues) - 1`; return open for True and
  sleeping for False.
- `clue_count` repair: `return len(clues)`. The expected assertion is
  `assert clue_count(CLUES) == 3`, or `== len(CLUES)`.
- Restore clean prepared files between learners if sharing a machine.
- Python stays local; the repaired world payoff is existing declarative M08.
- The broken `object_id` is a demonstration only. It is never committed, and no
  engine, schema, or validator behavior changes in this session.
