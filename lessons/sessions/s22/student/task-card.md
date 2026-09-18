# S22 Task Card — Traceback Detective

**Role:** Python-primary software fluency

**World payoff:** Repair three local failures, then confirm existing M08
`respond-to-object-state` behavior.

**Learning target:** Use exception types, traceback frames, assertions, and
regression tests to explain and protect one-change repairs, including one bug
you find and fix in your own file.

**Where this sits:** S21 asked whether what you built is *valid*. S22 asks what
to do when it is valid but still *wrong*. This is the debugging loop you will
rely on in S23, S24, and the S25 prototype: **observe → hypothesis → one change
→ rerun → compare evidence**.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict before running

For each prepared case—`key-error`, `off-by-one`, `incorrect-return`—write the
expected exception or failed assertion. Point to the first relevant frame inside
`student/debug.py`, then predict the cause before changing code. Checkpoint: the
last traceback line names the failure; the first relevant student-code frame
shows where to investigate.

## Core Python detective loop

Run the same five steps on every bug in this session:

**observe → hypothesis → one change → rerun → compare evidence**

For one case at a time:

1. **Observe:** reproduce the failure with
   `python lessons/sessions/s22/student/debug.py`, and name the exception and
   the first relevant student-code frame/line.
2. **Hypothesis:** predict the cause aloud or in chat before touching anything.
3. **One change:** make exactly one edit.
4. **Rerun:** run the same command again.
5. **Compare evidence:** say what changed between the two runs, then add one
   regression assertion to `starter.py` and run it.

Do not change all three failures at once.

## Your own bug

The three prepared cases are a teacher fixture. This one is in your file.

Run `python lessons/sessions/s22/student/starter.py`. It prints
`3 regression checks pass` and then a clue count. **Observe:** the printed count
disagrees with the `CLUES` tuple printed next to it. None of the shipped
assertions notice, which is exactly why it survived.

Run the full loop yourself:

1. **Observe** the two numbers and state the mismatch precisely.
2. **Hypothesis:** read `clue_count` and predict, in one sentence, why it is off
   and by how much. Do not edit yet.
3. Write the assertion at the TODO that would have caught this. Run it and watch
   it **fail** — a regression test you never saw fail proves nothing.
4. **One change** in `clue_count`, then **rerun**.
5. **Compare evidence:** the assertion now passes, the printed count matches
   `CLUES`, and the three original checks still pass.

Keep the assertion. It is the part of the repair that lasts.

## Python repair → validated package → guardian payoff

| Local evidence | Declarative evidence | Visible result |
|---|---|---|
| correct return + regression assertion | existing toggle/guardian package validates | off: sleeping; on: open |

Python remains local and does not mimic Trail internals. Validated declarative
YAML is the shared-runtime source of truth.

## World payoff

```console
explore-package validate lessons/sessions/s22/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s22/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "respond-to-object-state" \
  --name "S22 Traceback Detective"
```

Focus the window, approach Prism Guardian, observe the off response, toggle Prism
Switch with E, then observe the on response. Checkpoint: match both messages to
the repaired regression expectations.

## Three kinds of mistake

Not every bug announces itself the same way. Name the kind before you hunt:

| Kind | Where it shows up | This session's example |
|---|---|---|
| Input mistake | Python traceback, usually `KeyError`/`IndexError` | `key-error`, `off-by-one` in `debug.py` |
| Contract/validation mistake | `explore-package validate` output, no traceback at all | a `respond_to_toggle.object_id` that names no object in the package |
| Logic/behavior mistake | Nothing crashes; a value or message is simply wrong | `incorrect-return` in `debug.py`, and `clue_count` in your `starter.py` |

The contract case is the one a traceback will never find for you. Prove it:
temporarily change `object_id` in
`explorer-package/character/prism-guardian.yaml` to `no-such-object`, predict
the diagnostic, run the validator, then **restore the original value** before
the world payoff.

## Test and deliberate debug

Prepared failures are a `KeyError`, an off-by-one `IndexError`, and an assertion
caused by an incorrect return value. Capture a short receipt for each:
reproduced → frame → predicted cause → one change → rerun → regression assertion.

## Support path

Use a printed traceback with library frames faded and student frames boxed. The
teacher may reveal the exception type, but not the repair. Text output plus a
teacher guardian demo is valid on low bandwidth.

## Extension path

Write one assertion for the off state after all core regression receipts pass.

## Support path addition

If time is short, the teacher may name the *kind* of mistake in `clue_count`.
The hypothesis, the assertion, the one change, and the comparison stay yours.

## Required evidence/checkpoints

- Three exception/failure predictions.
- First relevant student-code frame for each.
- One-change rerun receipts.
- Regression assertion/test after each repair.
- Your own `clue_count` bug: the observed mismatch, your one-sentence
  hypothesis, the assertion failing, the one change, and the assertion passing.
- The contract/validation diagnostic you predicted, plus the restored
  `object_id`.
- M08 off/on guardian behavior restored.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI gives one hint
at a time only after you interpret the traceback; it may not provide the repair,
locate your `clue_count` bug for you, or write your regression assertion.

## Git close

**ZIP path check:** Do this section only if your course folder is Git-managed (the Derived student repository path) or your class has already started the Git lesson. On the ZIP path before that lesson, skip it — see [Student Quick Start → Later: Git](../../student-quick-start.md#later-git-optional-teacher-managed).

```console
git status --short
git diff
git add lessons/sessions/s22/student
git diff --staged
git commit -m "Fix guardian failure and protect its behavior"
```

`M`, `??`, and no output have the Quick Start meanings. Use identity recovery
and Control-C cancel/correct/retry. State the cause and protected behavior in the
commit; understanding takes priority over a rushed commit.
