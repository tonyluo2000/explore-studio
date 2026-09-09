# S25 Task Card — Playable Prototype

**Role:** Project-primary production lesson

**World payoff:** Build one complete, bounded adventure loop with existing M15
`complete-actions-in-order` and exactly three route objects.

**Learning target:** Turn your own premise into 3–5 observable acceptance
criteria, then complete and test a fail-closed Python pipeline whose reviewed
preview maps to a valid three-step package.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Choose and scope (0:00–0:04)

The included Stormlight Rescue Trail is a teacher example only. Choose your own:

- place and reason for the route;
- three station names and visitor-facing messages;
- keeper name and success message.

Write **3–5 observable acceptance criteria**. Each must be checkable by a printed
result, a test, package validation, or a visitor action. Keep one three-object
vertical slice; mark extra fields, polish, and optional behavior “deferred.”

## Predict before running (0:04–0:09)

No execution until all four are complete:

| Required reasoning | Your prediction |
|---|---|
| Visitor path from first object to M15 payoff | ___ |
| Invalid-data path: where it stops and what is not generated | ___ |
| Exactly three selected IDs in expected stable order | ___ |
| Expected total `signal_power` | ___ |

Checkpoint: explain which pipeline stage proves each prediction.

## Build the core pipeline (0:09–0:31)

Complete the TODO bodies in `starter.py` without changing `fixtures.py`:

```text
validate → filter enabled → search required IDs → count selected
→ aggregate signal power → stable sort → transform preview
```

1. `validate_station` checks the prepared nested record shape and returns a
   useful error list.
2. `select_route` filters enabled stations, searches required IDs in requested
   order, and fails if any ID is absent or the result is not exactly three.
3. `signal_total` adds selected `signal_power` values.
4. `ordered_route` returns a stable sorted copy by `route_order`.
5. Keep `transform_preview` as the prepared current-contract scaffold. Do not
   add fields to the runtime schema or automate unreviewed file writing.

Run:

```console
python lessons/sessions/s25/student/starter.py
python -m pytest -q lessons/sessions/s25/student/test_pipeline.py
```

## Playable check (0:31–0:38)

Python remains local. Only reviewed, validated declarative YAML crosses into the
existing runtime. The prepared recovery package demonstrates the bridge:

```text
local catalog → tested pipeline preview → reviewed package YAML → visible M15 route
```

```console
explore-package validate lessons/sessions/s25/student/recovery-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s25/student/recovery-package \
  --player "nova-character:nova" \
  --mission-id "complete-actions-in-order" \
  --name "S25 Playable Prototype"
```

For the teacher example, try the predicted correct order and record completion.
Then restart and try first → wrong authored member: existing M15 semantics reset
progress to zero and do not immediately reuse that wrong member as a new first
step. Your own premise and names may differ; the fixed requirement is three.

## Test and review (0:38–0:42)

Record one result for every prepared category:

- normal valid catalog;
- exactly-three boundary;
- absent required ID (fail closed before preview);
- malformed coordinate/type (fail closed before preview);
- stable-order regression with equal `route_order` values.

Capture pipeline output, package validation, a visitor-path trace, and the M15
correct-order/wrong-member result.

## Milestone self-review

- Creative choice I own: ___
- Python change I can explain: ___
- Test run and result: ___
- One thing deliberately deferred to keep scope bounded: ___

## Required evidence/checkpoints

- 3–5 observable acceptance criteria.
- Visitor-path trace and invalid-data prediction made before execution.
- Expected selected IDs/order and total power made before execution.
- Pipeline output and five-case test results.
- Valid package and planned/played M15 result for exactly three route objects.
- Milestone self-review with all four prompts completed.

## Support path

Use the prepared three-record `EXACTLY_THREE_CATALOG` and transformation scaffold.
If building stalls, validate the recovery package and explain one function while
the teacher gives a text-only or Trail demonstration. Predictions still come
first.

## Extension path

Add one non-route fourth station. It may be enabled or disabled, but it must not
change the required three selected IDs. Do not add a fourth sequence member;
M15 keeps its fixed three-step requirement.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may ask or
answer **one bounded scope-critique question only**, for example, “Which criterion
could be deferred?” AI cannot invent your premise, acceptance criteria, pipeline,
function bodies, route solution, or test answers.

## Git close (0:42–0:45)

Planning and prototype implementation belong in separate commits. For your
prototype change, use:

```console
git status --short
git diff
git add lessons/sessions/s25/student
git diff --staged
git commit -m "Complete my three-stop playable prototype"
```

Interpret `M`, `??`, and no output. Use identity recovery and Control-C
cancel/correct/retry. Stage only the intended code, test, and package evidence;
understanding takes priority over a rushed commit.
