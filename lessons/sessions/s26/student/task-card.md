# S26 Task Card — Capstone Blueprint

**Role:** Project-primary production lesson

**Mission:** M03 `make-your-object-respond` — one-object planning spike

**Learning target:** Turn your own S25 premise into a responsibility map, at
least three precise function contracts, an understandable nested data model,
and one tested source-to-playable-package proof without building the full
capstone.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Goal and ownership (0:00–0:04)

Carry your own S25 premise, evidence, scope, and decisions into
`project-record.md`. The included Skyglass Observatory values are editable
starting data. Stormlight Rescue Trail and `teacher-recovery-package/` are
teacher examples only; neither chooses your premise.

Write three core observable acceptance criteria. Optional criteria belong under
optional scope. Deliberately defer one decision that is not needed for today's
one-object proof.

## Plan and predict (0:04–0:09)

Before running Python, draw or describe:

```text
editable source data → validation → selection/rules → transformation
→ reviewed package values → student explorer-package/ → validation → M03 play
```

Record at least three possible failure points, predict which responsibility
detects each failure, and explain one intermediate data shape. Then predict the
selected station ID and its final object response.

## Build the blueprint (0:09–0:31)

### 1. Create your responsibility map

In `project-record.md`, name the code or artifact that owns every area:

1. data input;
2. validation;
3. selection/rules;
4. transformation;
5. package build/output;
6. validation/play;
7. tests.

Keep validation separate from file I/O. Keep pure rule functions file-free.
Make package build/output explicit; do not hide it inside validation.

### 2. Define at least three function contracts

For each contract record all six parts:

- function name;
- inputs;
- return shape;
- expected error/failure behavior;
- side effects, if any;
- one concrete example.

Do this before completing TODOs in `starter.py`. The scaffold is runnable and
uses neutral placeholder returns; it is not the capstone implementation.

### 3. Keep the nested model understandable

Edit `project_data.py`, preserving:

```text
expedition
└── zones
    └── stations
```

A station may use `id`, `name`, `enabled`, `coordinates`, `color`,
`route_order`, `signal_power`, and `story` messages. No classes are required.
Keep `fixtures.py` unchanged and read-only.

Run the scaffold only after recording predictions:

```console
python lessons/sessions/s26/student/starter.py
```

These tests are expected to fail until you complete the TODO functions.

```console
python -m pytest -q lessons/sessions/s26/student/test_blueprint.py
```

The focused cases are: valid station, absent required ID, malformed nested
shape, duplicate station ID, and deterministic/stable selection order. At least
one acceptance test begins red and must become green during S26. Do not edit the
fixtures or weaken the assertions.

## Playable spike (0:31–0:38)

Prove one small existing-mechanic path only:

- exactly one student-owned object;
- existing M03 `when_near` and `when_interacted` response behavior;
- current Explorer Package contract only;
- validation and interaction evidence.

Review one chosen station into your editable `explorer-package/`:

```console
explore-package validate lessons/sessions/s26/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s26/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "make-your-object-respond" \
  --name "My S26 Blueprint Spike"
```

Approach the object, record `when_near`, interact, record `when_interacted`, and
confirm M03 completes. Do not add objects, mechanics, package fields, runtime
code, or automated YAML writing.

The ownership chain stays:

```text
student editable data → local Python reasoning/transformation
→ reviewed package values → student explorer-package/
→ validation → playable world
```

## Mapping review

| Source data field | Responsible Python function/module | Resulting YAML/package field | Visible Trail effect |
|---|---|---|---|
| station `id` | `select_stations` / `build_package_preview` | contribution `id` and object filename | Identifies my object |
| station `name` | `build_package_preview` | `name` | Object label |
| `coordinates.x`, `coordinates.y` | `build_package_preview` | `x`, `y` | Object position |
| station `color` | `build_package_preview` | `color` | Object style |
| `story.when_near` | `build_package_preview` | `when_near` | Approach response |
| `story.when_interacted` | `build_package_preview` | `when_interacted` | Interaction response |
| `route_order`, `signal_power` | local rules/reasoning only | no YAML field | No direct Trail effect |

Python stays local. Your reviewed declarative YAML drives the Trail.
`project-record.md` is learning evidence, not runtime metadata.

## Test and review (0:38–0:42)

Record focused test output, package validation/planning, near/interact evidence,
one known risk, and one deliberately deferred decision.

### Milestone self-review

- Creative choice I own: ___
- Responsibility or contract I can explain: ___
- Test run and result: ___
- One decision deliberately deferred: ___
- One future helper/function I can name without implementing: ___

## AI receipt

AI may review exactly ONE student-written acceptance criterion for ambiguity.
AI may identify ambiguity and ask a clarifying question.

AI may NOT rewrite the entire criterion, choose the premise, create the
responsibility map, define function contracts, write implementation, generate
the package, or provide test answers.

You decide whether to accept or reject the suggestion and record why:

- criterion reviewed: ___
- ambiguity identified: ___
- clarifying question: ___
- accepted/rejected: ___
- why: ___

Do not paste whole files or ask AI for a complete solution.

## Git close (0:42–0:45)

The lesson materials were supplied as three separate reviewable changes:
blueprint/project record, initial tests, and playable spike. For your work use
status → diff → staged diff → descriptive commit:

```console
git status --short
git diff
git add lessons/sessions/s26/student
git diff --staged
git commit -m "Refine my capstone blueprint"
```

Interpret `M`, `??`, and no output. Use identity recovery and Control-C
cancel/correct/retry. Stage only the files you intended to change.

## Support path

Use `MINIMAL_VALID_EXPEDITION`, the teacher's responsibility cards, and the one
completed non-core contract example. If play is blocked, the teacher may use a
text-only trace or `teacher-recovery-package/`. This reduces scope but does not
replace your premise, map, contracts, acceptance-test work, or package.

## Extension

Identify one future helper/function and its responsibility. Do not implement it.

## Cut line

Protect your responsibility map, three core contracts, one green acceptance
test, and one validated student-owned playable object. Defer complete module
implementation, the full multi-object capstone, extra mechanics, and polish.
