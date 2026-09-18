# S25 Task Card — Playable Prototype

**Role:** Project-primary production lesson

**Milestone:** B — the first session where the project is yours end to end.

**World payoff:** One small prototype a visitor can actually play, built from
the existing M15 ordered route plus one more mechanic you choose.

**Learning target:** Combine two mechanics you already know into one coherent
prototype, prove it with validation and a deterministic build, play it, fix one
real problem, and explain both a design decision and a technical one.

**Where this sits:** S21 you validated. S22 you debugged. S23 you composed two
mechanics into one system. S24 you improved a system without breaking it. S25
asks for all four at once, on a premise nobody gave you.

> Validate → Debug → Compose → Optimize → **Playable Prototype**

Milestone B proves one sentence: *I can independently build and explain a small
working system.* It is not the capstone. S26 is where you design something
larger; today you finish something small.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## What "done" means (0:00–0:05)

Seven acceptance criteria. All seven, or it is not done.

| # | Criterion | How it is checked |
|---:|---|---|
| 1 | **Plan** — premise, two mechanics, player action, expected result | `milestone.yaml` |
| 2 | **Build** — your sources produce the intended package, the same way twice | milestone checker |
| 3 | **Validate** — real package validation passes | `explore-package validate` |
| 4 | **Play** — it loads, plans, and launches in Trail | Trail |
| 5 | **Compose** — two supported mechanics coexist *meaningfully* | milestone checker |
| 6 | **Debug** — one concrete problem you hit, and the change that fixed it | `milestone.yaml` |
| 7 | **Explain** — one design decision and one technical decision | `milestone.yaml` |

"Meaningfully" in criterion 5 means the two mechanics belong to one experience.
Two examples copied side by side do not pass, and the checker says so.

## What you own

Nothing in the starter files makes a creative decision for you. Every
`CHOOSE-ME` is yours:

- the premise — what this place is and why anyone walks it;
- the name of every object and character;
- every player-facing message;
- **which second mechanic** you combine with the route;
- **where that second mechanic sits**, and what that does to the route;
- at least one mechanic parameter or goal;
- your reflection.

The IDs (`first-stop`, `second-stop`, `third-stop`, `route-keeper`) are
scaffolding so the file names, the manifest, and the keeper's sequence already
agree. Renaming them is an optional extension, not the milestone.

## The workflow

```text
Plan → Author → Run focused checks → Validate → Build → Play
     → Debug/fix if needed → Re-run → Reflect
```

Run this at any point to see exactly where you are:

```console
python -m pytest -q lessons/sessions/s25/student/test_milestone.py
```

It starts red on purpose. Nothing is broken — it is counting the decisions you
have not made yet, and each failure names the file and the field.

## Plan (0:05–0:10)

Open `milestone.yaml` and fill in the `plan:` block. Nothing else yet.

### Choose your second mechanic

Mechanic one is fixed: the M15 ordered route, exactly three stops. Mechanic two
is your choice from the supported set:

| Choice | Object gets | Character gets |
|---|---|---|
| `counter` | `counter: {goal: 2–5, when_goal_reached: …}` | `respond_to_counter` |
| `toggle` | `toggle: {off_color, on_color}` (and **no** `color`) | `respond_to_toggle` |
| `two_toggles` | two toggle objects | `respond_to_two_toggles` |
| `either_toggle` | two toggle objects | `respond_to_either_toggle` |

`counter` and `toggle` fit comfortably in this session. The two-toggle options
need a fourth object and are the extension.

### Choose where it sits — this is the real decision

**On one of your three route objects.** One player action feeds both mechanics:
touching that stop advances the route *and* moves the counter or flips the
toggle. Be honest with yourself about the consequence — a counter only ever
counts up and never resets, but touching a route object out of turn sends the
route back to step one. The two mechanics remember different things.

**On a fourth, non-route object.** The two mechanics stay independent. Simpler
to reason about; your keeper's lines have to do the work of connecting them.

Either is a real design. Record which one you chose and why in
`plan.how_they_connect`, and mirror it in `SECOND_MECHANIC` in
`project_catalog.py`.

### Predict before you run

| Required reasoning | Your prediction |
|---|---|
| Visitor path from first object to the M15 payoff | ___ |
| Invalid-data path: where it stops and what is not generated | ___ |
| Exactly three selected IDs in expected stable order | ___ |
| Expected total `signal_power` | ___ |
| What your second keeper says before and after | ___ |

Record these in `project-record.md`. Checkpoint: name the pipeline stage that
proves each one.

## Author (0:10–0:25)

**Your catalog.** Replace every `CHOOSE-ME` in `project_catalog.py`, including
the `SECOND_MECHANIC` block. Keep exactly three stations for the route.

**Your pipeline.** Complete the TODO bodies in `starter.py`. Do not change the
read-only `fixtures.py`:

```text
validate → filter enabled → search required IDs → count selected
→ aggregate signal power → stable sort → transform preview
```

1. `validate_station` checks the nested record shape and returns a useful error
   list. *(S21: know whether what you built is valid.)*
2. `select_route` filters enabled stations, searches required IDs in requested
   order, and fails if any ID is absent or the result is not exactly three.
3. `signal_total` adds selected `signal_power` values.
4. `ordered_route` returns a stable sorted copy by `route_order`. *(S24: stable
   order is a behavior you preserve, not an accident.)*
5. Keep `transform_preview` as the prepared current-contract scaffold. Do not
   add fields to the runtime schema.

**Your package.** Make the same reviewed changes in `explorer-package/`, then
add your second mechanic.

For `counter`, add this to one object file:

```yaml
counter:
  goal: 3                       # a whole number from 2 through 5
  when_goal_reached: "CHOOSE-ME"
```

and add one character file, `character/signal-keeper.yaml`:

```yaml
name: "CHOOSE-ME"
x: 140
y: 460
color: "pink"
respond_to_counter:
  object_id: "third-stop"       # the object you just gave a counter
  when_below_goal: "CHOOSE-ME"
  when_at_or_above_goal: "CHOOSE-ME"
```

For `toggle`, give one object a `toggle:` block and **delete its `color:` line**
— a toggle brings its own two colors — then use `respond_to_toggle` with
`when_off` and `when_on` instead.

Either way, declare the new file in `manifest.yaml`:

```yaml
  - id: "signal-keeper"
    type: "character"
    path: "character/signal-keeper.yaml"
```

*(S23: two mechanics are a system when one reads the other, not when they share
a folder.)*

## Run focused checks and validate (0:25–0:32)

```console
python lessons/sessions/s25/student/starter.py
python -m pytest -q lessons/sessions/s25/student/test_pipeline.py
```

These pipeline tests are expected to fail until you complete the TODO
functions.

```console
explore-package validate lessons/sessions/s25/student/explorer-package
```

Then build it. The digest is your build receipt: the same sources produce the
same archive every time, and a different digest means something changed.

```console
explore-package export lessons/sessions/s25/student/explorer-package \
  --output my-playable-prototype-0.1.0.explorer-package.zip
```

Paste the printed `valid:` line and the 64-character `sha256:` value into the
`evidence:` block of `milestone.yaml`.

## Play (0:32–0:38)

```console
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s25/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "complete-actions-in-order" \
  --name "My S25 Playable Prototype"
```

Walk your predicted correct order and record the payoff. Then restart and try
first → wrong stop: existing M15 semantics reset progress to zero and do not
immediately reuse that wrong stop as a new first step. Talk to your second
keeper before and after, and check that what it says matches what you planned.

Only reviewed, validated declarative YAML crosses into the runtime. Python
stays local:

```text
premise → editable catalog → completed pipeline → reviewed values
→ package YAML → validation → deterministic build → visible M15 world
```

## Debug and re-run (0:38–0:42)

Use the S22 loop on whatever actually went wrong:

**observe → hypothesis → one change → rerun → compare evidence**

Write the real problem in `milestone.yaml`. A validation error, a keeper line
that fired in the wrong state, a route that reset when you did not expect it,
or a red pipeline test are all real problems. Do not invent one.

**If genuinely nothing broke,** do this one bounded exercise instead. Point your
second keeper's `object_id` at a route object that has no counter or toggle,
then run the validator:

```console
explore-package validate lessons/sessions/s25/student/explorer-package
```

Read the diagnostic aloud — it names the file, the field, and the rule. Put the
correct ID back, rerun, and record what the validator refused and why. That is
your debugging evidence.

Then re-run everything:

```console
python -m pytest -q lessons/sessions/s25/student/test_milestone.py
```

## Reflect and hand in evidence (0:42–0:45)

Fill in the `reflection:` block of `milestone.yaml`. Short answers:

- What did you choose to build?
- Which two mechanics did you combine?
- What problem did you hit and how did you fix it?
- What would you improve with 15 more minutes?

### Your milestone evidence

Six things, all of which you already have:

1. `milestone.yaml` plan;
2. your authored `project_catalog.py` and `explorer-package/`;
3. green `test_milestone.py` output;
4. the `explore-package validate` PASS line;
5. the deterministic build digest;
6. `milestone.yaml` reflection.

There is nothing to submit anywhere else.

## Review the catalog-to-world mapping

Before editing YAML, compare the pipeline's selected and ordered preview with
`explorer-package/` and record the review in `project-record.md`.

| Student catalog value | Reviewed package/runtime value |
|---|---|
| station `id` | manifest contribution `id`, object filename, and sequence object ID |
| station `name` and story text | object `name`, `when_near`, and `when_interacted` |
| `world.x` and `world.y` | object `x` and `y` coordinates |
| `world.color` | object `color` style |
| `route_order` | order of the keeper's `respond_to_sequence.object_ids` |
| `signal_power` | local reasoning/aggregation evidence only; it is not copied into runtime YAML |
| `SECOND_MECHANIC` | local planning only; the package says it in `counter:`/`toggle:` and the reading character |

Local Python helps you reason, transform, and validate. Validated package YAML
drives the visible world. The shared runtime never executes student Python.

## Cut line

If time runs short, protect these in order:

1. a valid authored prototype;
2. two mechanics that mean something together;
3. validation and build evidence;
4. a brief reflection.

Cut polish first: fewer objects, shorter messages, put the second mechanic on a
route object instead of adding a fourth one, and let the teacher drive the Trail
launch. Do **not** drop to one mechanic — that is the milestone.

## Support path

If building stalls, the teacher may validate and demonstrate
`recovery-package/`. That package is teacher-only, partial recovery: using it
does not complete your student-owned project artifact. You still provide every
prediction and explain at least one completed function, then later finish your
own editable catalog and `explorer-package/`.

## Extension path

Add one non-route fourth station. It may be enabled or disabled, but it must
not change the required three selected IDs. Do not add a fourth sequence
member; M15 keeps its fixed three-step requirement. Renaming the scaffolding
IDs to match your premise is the other extension — rename the file, the
manifest entry, and the keeper's sequence together.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may ask or
answer **one bounded scope-critique question only**, for example, “Which part
could be deferred?” AI cannot invent your premise, acceptance criteria,
pipeline, function bodies, route solution, or test answers.

## Git close

**ZIP path check:** Do this section only if your course folder is Git-managed (the Derived student repository path) or your class has already started the Git lesson. On the ZIP path before that lesson, skip it — see [Student Quick Start → Later: Git](../../student-quick-start.md#later-git-optional-teacher-managed).

Planning and prototype implementation belong in separate commits. Reflection
comes first; a delayed commit may finish after class. For your prototype change,
use:

```console
git status --short
git diff
git add lessons/sessions/s25/student
git diff --staged
git commit -m "Complete my two-mechanic playable prototype"
```

Interpret `M`, `??`, and no output. Use identity recovery and Control-C
cancel/correct/retry. Stage only the intended code, test, and package evidence;
understanding takes priority over a rushed commit.
