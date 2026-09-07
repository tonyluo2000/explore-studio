# S17 Task Card — Clue Finder

**Role:** Python-primary data fluency

**World payoff:** Reuse M03 messages and M06 `build-an-object-collection`.

**Learning target:** Write small search, filter, and count functions with clear
parameters and return values.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict before running

Without executing, record:

- `find_by_id(clues, "missing")` → ___
- `filter_by_color(clues, "green")` names/order → ___
- `filter_by_color(clues, "blue")` names/order → ___
- `count_matching(clues, "color", "blue")` → ___

Checkpoint: label these no-match, one-match, and multiple-match cases.

## Core Python path

Implement the empty bodies in `starter.py`; none is completed for you:

1. `find_by_id(records, target_id)` returns the matching record or `None`.
2. `filter_by_color(records, target_color)` builds a new result list in original
   order.
3. `count_matching(records, key, expected_value)` returns a number.
4. Run `python lessons/sessions/s17/student/starter.py` and compare order/count.

Use small `for` loops, `if`, and `return`. Do not use a comprehension.

## Python selection → package records → visible clues

| Local selection | Existing package field | World payoff |
|---|---|---|
| record ID | contribution/object ID | Chosen object appears |
| color filter | object `color` | Selected color remains visible |
| selected record | `when_near` / `when_interacted` | M03 clue message |

Python remains local. Validated YAML is the shared-runtime source of truth.

## World payoff

Use your returned records to confirm the prepared package selection: the two blue
clues in returned order plus the one green clue. Personalize one existing
`when_near` or `when_interacted` message from the selected record; add no fields.

```console
explore-package validate lessons/sessions/s17/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s17/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "build-an-object-collection" \
  --name "S17 Clue Finder"
```

Tour the M06 collection and trigger each M03-style near/interacted clue. Checkpoint:
show that the two blue records keep their predicted River Mark/Sky Thread order.

## Test and deliberate debug

Write assertions covering no match, one match, and multiple matches. If a result
returns too early, move the return only after explaining which records still need
inspection. If count returns a list, compare its type with your prediction.

## Support path

Use one function at a time and a paper “results” box. The teacher may provide the
loop header, not the body. Share printed values in chat for low bandwidth.

## Extension path

After core tests, ask a partner or AI for one edge case. Predict it, then add one
assertion; do not redesign the functions.

## Required evidence/checkpoints

- Predicted order/count for no, one, and multiple matches.
- Three student-implemented function bodies.
- Passing tests for all three case sizes.
- Valid M06 package and visible selected clue messages.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may suggest
one edge case only; it must not write `find_by_id`, `filter_by_color`, or
`count_matching`.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s17/student
git diff --staged
git commit -m "Find and test expedition clues"
```

Interpret `M`, `??`, and no output. Use Git identity recovery and Control-C
cancel/correct/retry. Understanding takes priority over a rushed commit.
