# S18 Task Card — Power Station Scoreboard

**Role:** Python-primary data fluency

**World payoff:** Reuse M09 counters and M13 `compare-a-counter-to-its-goal`.

**Learning target:** Summarize counter records with small helpers and return
values, then test goal boundaries.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Contract and prediction gate

Write the contract before coding:

`summarize_counts([])` returns **`None`** because ___________________________.

For counts 2, 4, 4, predict:

```text
minimum ___  maximum ___  total ___  average ___
IDs tied for maximum ____________________________
at_goal(2, 3) ___  at_goal(3, 3) ___  at_goal(4, 3) ___
```

Checkpoint: teacher confirms empty-input behavior and every prediction.

## Core Python path

1. Run `python lessons/sessions/s18/student/starter.py` after the gate.
2. In `summarize_counts`, use `min(counts)`, `max(counts)`, `sum(counts)`, and
   `total / len(counts)` to replace the four placeholders.
3. Keep the early `if not records: return None` contract.
4. Complete `at_goal` with the S10 boundary comparison and rerun.

## Local counters → authored goal → visible scoreboard

| Local model | Current package field | World result |
|---|---|---|
| `wind-core` goal | counter `goal: 3` | M09 goal message after 3 Trail interactions; M13 reader says below/ready |
| `sun-core` goal | counter `goal: 4` | M09 goal message after 4 Trail interactions |
| `tide-core` goal | counter `goal: 5` | M09 goal message after 5 Trail interactions |

**Python evidence vs. Trail evidence:** all three stations now show their own
count-versus-goal state in the world, one counter per object. The aggregate
values you calculate — `minimum`, `maximum`, `total`, `average`, and the IDs
tied for maximum — summarize all three stations *at once* and have no
matching package field, so they stay local Python evidence. Trail can only
show one station's own goal state at a time; it never displays a summary
across stations.

**LOCAL PYTHON MODEL vs. TRAIL RUNTIME — the counts are not the same
counts.** Your local Python records start from counts 2, 4, 4: `wind-core`
2/3 (below goal), `sun-core` 4/4 (at goal), `tide-core` 4/5 (below goal).
Every Trail counter, by contrast, **starts fresh at 0** when you launch the
package — it does not inherit those local Python counts. Counting from
zero in Trail, Wind Core reaches its goal after 3 interactions, Sun Core
after 4, and Tide Core after 5.

Python remains local. Validated YAML is the shared-runtime source of truth.

## World payoff

Open `objects/wind-core.yaml` and author the existing M09 `goal` field from your
local model. Keep the core value 3, or choose another valid 2–5 value and update
all boundary predictions before launching. Do not add a field. `sun-core.yaml`
and `tide-core.yaml` already have their `goal` fields authored from the same
local model's goal values (4 and 5) so all three stations are visible together;
you do not edit them. Authoring a `goal` value does not set a starting count —
every counter, including these two, still starts at 0 when Trail launches.

```console
explore-package validate lessons/sessions/s18/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s18/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "compare-a-counter-to-its-goal" \
  --name "S18 Power Station Scoreboard"
```

Speak to Station Reader below the authored goal, interact with Wind Core until
that exact goal, observe its M09 goal message, then speak again for the M13
at-goal response. Then visit Sun Core and interact with it until its **4th**
interaction triggers its own M09 goal message, and visit Tide Core and
interact with it until its **5th** interaction triggers its own M09 goal
message. Each Trail counter starts at 0, so these are 4 and 5 fresh
interactions counted from zero — they do not inherit the 4/4 and 4/5 counts
from the local Python model.

## Test and deliberate debug

- Normal: assert the four summary values and the two records tied at maximum.
- Empty: keep/assert the defined `None` result; predict what bare `min([])` does.
- Boundary: assert below False, exactly True, above True; temporarily test `>`
  and explain the equality failure before restoring `>=`.

## Support path

Write counts in one flat list and calculate one measure at a time. Use a number
line for goal 3. Share printed results and teacher world evidence on low bandwidth.

## Extension path

Use one loop to return the IDs tied for maximum. Avoid classes or abstraction.

## Required evidence/checkpoints

- Empty-input contract written before code.
- Predicted min/max/total/average/ties and three boundaries.
- Passing normal, empty, below/exact/above checks.
- Valid package, M09 goal message for all three stations, and both M13
  responses.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may review
your function contract, not write the implementation or calculate answers.

## Git close

**ZIP path check:** Do this section only if your course folder is Git-managed (the Derived student repository path) or your class has already started the Git lesson. On the ZIP path before that lesson, skip it — see [Student Quick Start → Later: Git](../../student-quick-start.md#later-git-optional-teacher-managed).

```console
git status --short
git diff
git add lessons/sessions/s18/student
git diff --staged
git commit -m "Summarize power station counters"
```

Interpret `M`, `??`, and no output; use Git identity and cancel/retry recovery.
Understanding takes priority over a rushed commit.
