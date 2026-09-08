# S19 Task Card — Route Planner

**Role:** Python-primary data fluency

**World payoff:** Reuse M15 `complete-actions-in-order`.

**Learning target:** Flatten nested zone records, make a stable sorted copy by
priority, and turn the first three results into a world route.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict before running

Write all four IDs in flattened order: __________________________________.

Write all four after sorting by priority: _______________________________.

Mist Bell and Star Lens both have priority 2. Which stays first, and why? ___

After `ordered = sorted(flat_records, key=...)`, does `flat_records` change? ___

Checkpoint: show the tie-order and mutation predictions before execution.

## Core Python path

1. In `flatten_zones`, use one loop over zones and one loop over each zone's
   `objects`; append each record to `flattened`.
2. In `order_by_priority`, return `sorted(records, key=lambda record:
   record["priority"])`.
3. Run `python lessons/sessions/s19/student/starter.py`.
4. Compare the flat list, sorted copy, and first three IDs with predictions.

Keep this concrete: do not introduce a generalized sorting algorithm or class.

## Nested input → flat/sorted route → M15 world

| Transformation | Result |
|---|---|
| flatten zones | one list in authored zone/object order |
| stable `sorted` by priority | equal keys retain their earlier relative order |
| take first three | River Rune → Mist Bell → Star Lens M15 sequence |

Python remains local. Validated YAML is the shared-runtime source of truth.

## World payoff

```console
explore-package validate lessons/sessions/s19/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s19/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "complete-actions-in-order" \
  --name "S19 Route Planner"
```

Focus the window and interact in the first-three sorted order, then speak to the
Route Keeper. Checkpoint: show the M15 payoff and name the stable tie.

## Test and deliberate debug

- Equal keys: assert Mist Bell appears before Star Lens.
- Missing priority: temporarily remove one key, predict/read the `KeyError`, restore.
- Accidental mutation: try `.sort(key=...)` on a copy, observe that the copy
  changes and the call returns `None`; keep `sorted(...)` in the final function.

## Support path

Move four labeled cards from two zone boxes into one row, then sort the row. The
teacher may supply loop headers. Use printed IDs and a teacher demo on low bandwidth.

## Extension path

Change one priority in local data and predict the route; keep three M15 objects.

## Required evidence/checkpoints

- Flattened order, stable tie order, and mutation prediction before execution.
- New sorted list with original flat list unchanged.
- Recovered equal-key, missing-priority, and accidental-mutation cases.
- Valid package and playable first-three M15 sequence.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may explain
the key function only after your prediction; it may not write the route code.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s19/student/starter.py
git diff --staged
git commit -m "Plan a stable priority route"
```

Commit algorithm work separately from optional story edits. Interpret `M`, `??`,
and no output; recover identity or cancel/correct/retry. Understanding takes
priority over a rushed commit.
