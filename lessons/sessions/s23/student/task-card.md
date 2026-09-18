# S23 Task Card — Builder's Workshop

**Role:** Python-primary software fluency

**World payoff:** Refactor an S20-style local pipeline, then compose your own
small system where M14 style reuse and an M08-style responding keeper work
together in one package.

**Learning target:** Decompose one working pipeline into small imported modules
for data I/O, validation/rules, and deterministic build/output without changing
observable behavior — then use that pipeline to build one package where **two
mechanics you already know coexist on purpose**.

**Where this sits:** S21 checked validity, S22 fixed what was wrong. S23 is the
first time you put pieces *together*: a shared toggle style and a keeper whose
line depends on one of those toggles are not two unrelated examples pasted side
by side — the keeper reads the lamp. That is a small system, and S25 asks you
for a bigger one.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict and design before coding

Run nothing yet. Circle duplicated/responsibility-mixed code in `starter.py`,
then draw this call/data flow with actual function names:

`starter → data_io → rules → build_output → exact text → package/world`

Label what data enters and returns from each arrow. Checkpoint: propose one
duplication or responsibility candidate before AI or teacher feedback.

Then find the place where the two mechanics meet. `validate_data` already
refuses a plan whose keeper watches an object the plan does not contain.
Predict: which module does that rule belong in, and why is it a *rule* rather
than a *build* step?

## Core Python refactor path

1. Run the exact-output regression **before** changing code:
   `python -m pytest -q lessons/sessions/s23/student/test_refactor.py`.
2. Move only local YAML loading into `data_io.py`; import it and rerun.
3. Move only validation into `rules.py`; import it and rerun.
4. Move only document building/rendering into `build_output.py`; import and rerun.
5. Keep the regression unchanged. Every step must preserve exact output.
6. Do not add classes; small functions, parameters, return values, and imports
   are the point.

## Compose your own system

`workshop-plan.yaml` is the teacher's system. `my-system.yaml` is yours, and it
ships full of `CHOOSE-ME`.

Your system must make **two mechanics work together**:

1. one named toggle style reused by **both** objects (the M14 mechanic), and
2. one keeper whose spoken line depends on **one of those objects** (the M08
   mechanic).

Replace every `CHOOSE-ME`. Your decisions are real ones:

- both object names,
- the style's off and on colours,
- the keeper's name and colour,
- **which lamp the keeper watches**,
- the keeper's off line and on line, in your own words.

Then run:

```console
python -m pytest -q lessons/sessions/s23/student/test_refactor.py
```

Before you author anything, the composition tests **fail on purpose** — that is
the starting line, not a mistake. `test_pipeline_output_matches_exact_snapshot`
passes from the first minute and must keep passing; the three failing
`my_system` tests go green only when your system exists.

`compose_text()` refuses to build while any `CHOOSE-ME` remains, and the
composition tests check that one style is shared by both lamps, that the
keeper's `object_id` names a lamp that exists in *your* plan, and that your two
keeper lines differ from each other and from the teacher's.

Checkpoint: say in one sentence what a player has to *do* before your keeper
changes its line. If the answer does not mention toggling the lamp it watches,
your two mechanics are sitting next to each other, not working together.

The exact-output regression still guards `workshop-plan.yaml` and is untouched
by your system. Two plans, two oracles: one proves the refactor changed nothing,
the other proves your composition is well formed.

## Python modules → composed package → visible system

| Python responsibility | Declarative parallel | Visible payoff |
|---|---|---|
| one helper reused by callers | one named `workshop-glow` style | two lamps share off/on colors |
| imports connect modules | style references connect objects | both objects behave consistently |
| one rule spans two parts | keeper's `object_id` names a lamp | the keeper's line changes when that lamp is toggled |

This is an M14 reuse analogy, not new runtime behavior. The keeper's response is
the existing declarative `respond_to_toggle` contract, not a new engine feature.
Python and YAML file I/O remain local-only; validated declarative package data
alone enters Trail.

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

Focus the window, talk to the Workshop Keeper **before** toggling anything, then
toggle both lamps and talk to it again. Checkpoint: the exact output and the
rendered world are unchanged by your refactor, while the keeper's two lines show
the two mechanics touching each other.

## Test and deliberate debug

Create one temporary import mistake or move a function into the wrong module.
Predict the traceback or exact-output mismatch, reproduce it, restore one line,
and rerun the unchanged regression.

## Support path

Move one function only and use teacher-provided import syntax. Keep the call/data
flow and exact regression. For the composition, a teacher may supply one colour
and one object name; the watched lamp and both keeper lines stay yours. Printed
exact output plus a teacher M14 demo is valid on low bandwidth.

## Extension path

Extract a small `main()` coordinator after all three bounded modules pass.

## Required evidence/checkpoints

- Pre-coding call/data-flow design and student-identified candidate.
- Passing exact-output regression before and after each move.
- Three bounded module responsibilities and working imports.
- `my-system.yaml` with no `CHOOSE-ME` left and all composition tests passing.
- Your one-sentence answer for what a player must do before your keeper's line
  changes.
- Valid package and the M14 payoff, with the keeper answering differently off
  and on.
- Isolated behavior-preserving refactor diff.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may point out
duplication only after you identify a candidate; it may not perform the
refactor, choose which lamp your keeper watches, or write your keeper's lines.

## Git close

**ZIP path check:** Do this section only if your course folder is Git-managed (the Derived student repository path) or your class has already started the Git lesson. On the ZIP path before that lesson, skip it — see [Student Quick Start → Later: Git](../../student-quick-start.md#later-git-optional-teacher-managed).

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
