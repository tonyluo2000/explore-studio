# S23 Task Card — Builder's Workshop

**Role:** Python-primary software fluency

**World payoff:** Refactor an S20-style local pipeline while M14 demonstrates
one named style reused by two world objects.

**Learning target:** Decompose one working pipeline into small imported modules
for data I/O, validation/rules, and deterministic build/output without changing
observable behavior.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict and design before coding

Run nothing yet. Circle duplicated/responsibility-mixed code in `starter.py`,
then draw this call/data flow with actual function names:

`starter → data_io → rules → build_output → exact text → package/world`

Label what data enters and returns from each arrow. Checkpoint: propose one
duplication or responsibility candidate before AI or teacher feedback.

## Core Python refactor path

1. Run the exact-output regression **before** changing code:
   `python -m pytest -q lessons/sessions/s23/student/test_refactor.py`.
2. Move only local YAML loading into `data_io.py`; import it and rerun.
3. Move only validation into `rules.py`; import it and rerun.
4. Move only document building/rendering into `build_output.py`; import and rerun.
5. Keep the regression unchanged. Every step must preserve exact output.
6. Do not add classes; small functions, parameters, return values, and imports
   are the point.

## Python modules → shared style → two world objects

| Python responsibility | Declarative parallel | Visible payoff |
|---|---|---|
| one helper reused by callers | one named `workshop-glow` style | two lamps share off/on colors |
| imports connect modules | style references connect objects | both objects behave consistently |

This is an M14 reuse analogy, not new runtime behavior. Python and YAML file I/O
remain local-only; validated declarative package data alone enters Trail.

## World payoff

```console
explore-package validate lessons/sessions/s23/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s23/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "reuse-a-named-toggle-style" \
  --name "S23 Builder's Workshop"
```

Focus the window and toggle both lamps. Checkpoint: output and rendered world are
unchanged while the local Python responsibilities become clearer.

## Test and deliberate debug

Create one temporary import mistake or move a function into the wrong module.
Predict the traceback or exact-output mismatch, reproduce it, restore one line,
and rerun the unchanged regression.

## Support path

Move one function only and use teacher-provided import syntax. Keep the call/data
flow and exact regression. Printed exact output plus a teacher M14 demo is valid
on low bandwidth.

## Extension path

Extract a small `main()` coordinator after all three bounded modules pass.

## Required evidence/checkpoints

- Pre-coding call/data-flow design and student-identified candidate.
- Passing exact-output regression before and after each move.
- Three bounded module responsibilities and working imports.
- Valid package and unchanged two-lamp M14 payoff.
- Isolated behavior-preserving refactor diff.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may point out
duplication only after you identify a candidate; it may not perform the refactor.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s23/student
git diff --staged
git commit -m "Refactor trail builder without changing output"
```

Interpret `M`, `??`, and no output; use Git identity recovery and Control-C
cancel/correct/retry. Keep this refactor isolated from behavior changes. Exact
before/after evidence and understanding takes priority over a rushed commit.
