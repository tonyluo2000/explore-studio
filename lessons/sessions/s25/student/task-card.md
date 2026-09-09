# S25 Task Card — Playable Prototype

**Role:** Project-primary production lesson

**World payoff:** Build one complete, bounded adventure loop with existing M15
`complete-actions-in-order` and exactly three route objects.

**Learning target:** Turn your own premise into exactly three core observable
acceptance criteria, then complete and test a fail-closed Python pipeline whose
reviewed preview maps to your valid three-step package. Criteria 4–5 are optional
extensions.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Choose and scope (0:00–0:04)

You may prepare your premise before class. The included Moonlit Garden project is
an editable starting point, while Stormlight Rescue Trail is a teacher recovery
example only. Choose your own:

- place and reason for the route;
- three station names and visitor-facing messages;
- keeper name and success message.

Record the premise in `project-record.md`. Write **exactly 3 core observable
acceptance criteria**. Each must be checkable by a printed result, a test,
package validation, or a visitor action. Criteria 4–5 are optional extensions.
Keep one three-object vertical slice; mark extra fields, polish, and optional
behavior “deferred.”

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

Edit your three records in `project_catalog.py`, then complete the TODO bodies in
`starter.py` without changing the fixed read-only `fixtures.py`:

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
```

These tests are expected to fail until you complete the TODO functions.

```console
python -m pytest -q lessons/sessions/s25/student/test_pipeline.py
```

## Playable check (0:31–0:38)

Python remains local. Only reviewed, validated declarative YAML crosses into the
existing runtime. Your editable project demonstrates the bridge:

```text
student premise → editable catalog → completed pipeline
→ reviewed selected/ordered values → student package YAML
→ validation → visible M15 world
```

```console
explore-package validate lessons/sessions/s25/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s25/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "complete-actions-in-order" \
  --name "My S25 Playable Prototype"
```

Try your predicted correct order and record completion. Then restart and try first
→ wrong authored member: existing M15 semantics reset progress to zero and do not
immediately reuse that wrong member as a new first step. Your premise and names
may differ; the fixed requirement is three.

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

Local Python helps you reason, transform, and validate. Validated package YAML
drives the visible world. The shared runtime never executes student Python.

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

- Exactly three core observable acceptance criteria; criteria 4–5 are optional.
- Visitor-path trace and invalid-data prediction made before execution.
- Expected selected IDs/order and total power made before execution.
- Pipeline output and five-case test results.
- Valid package and planned/played M15 result for exactly three route objects.
- Milestone self-review with all four prompts completed.

## Support path

Use the prepared three-record `EXACTLY_THREE_CATALOG` and transformation scaffold.
If building stalls, the teacher may validate `recovery-package/` and give a
text-only or Trail demonstration. That package is teacher-only, partial recovery:
using it does not complete your student-owned project artifact. You still
provide every prediction and explain at least one completed function, then later
finish your own editable catalog and `explorer-package/`.

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
