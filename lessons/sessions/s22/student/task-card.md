# S22 Task Card — Traceback Detective

**Role:** Python-primary software fluency

**World payoff:** Repair three local failures, then confirm existing M08
`respond-to-object-state` behavior.

**Learning target:** Use exception types, traceback frames, assertions, and
regression tests to explain and protect one-change repairs.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict before running

For each prepared case—`key-error`, `off-by-one`, `incorrect-return`—write the
expected exception or failed assertion. Point to the first relevant frame inside
`student/debug.py`, then predict the cause before changing code. Checkpoint: the
last traceback line names the failure; the first relevant student-code frame
shows where to investigate.

## Core Python detective loop

For one case at a time:

1. **Reproduce** the failure with `python lessons/sessions/s22/student/debug.py`.
2. Name the exception and first relevant student-code frame/line.
3. **Predict** the cause aloud or in chat.
4. Make exactly one change and rerun.
5. Add one regression assertion to `starter.py`, then run it.

Do not change all three failures at once. `starter.py` is runnable scaffolding;
complete its TODO only after the prepared failure is understood.

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

## Required evidence/checkpoints

- Three exception/failure predictions.
- First relevant student-code frame for each.
- One-change rerun receipts.
- Regression assertion/test after each repair.
- M08 off/on guardian behavior restored.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI gives one hint
at a time only after you interpret the traceback; it may not provide the repair.

## Git close

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
