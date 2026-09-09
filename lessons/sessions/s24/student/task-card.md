# S24 Task Card — Fast Ranger Index

**Role:** Python-primary software fluency

**World payoff:** Resolve three IDs efficiently, preserve their requested order,
then play that ordered route with existing M15 `complete-actions-in-order`.

**Learning target:** Compare repeated linear searches with one ID→record dictionary
by counting record inspections and proving the returned results are equivalent.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict before running

For requested IDs in the last three positions, count inspections by hand:

| Catalog size | repeated scans | build one ID dictionary | predicted route order |
|---:|---:|---:|---|
| 6 | ___ | ___ | ___ |
| 12 | ___ | ___ | ___ |

Count inspected records, not seconds. Predict what happens to each count when
the data doubles. Checkpoint: explain why dictionary construction inspects every
record once and why repeated scans start again for every requested ID.

## Core Python path

1. Trace the 6-record row before running `starter.py`.
2. Run `python lessons/sessions/s24/student/starter.py` and compare exact counts.
3. Trace the 12-record row, rerun, then complete the TODO assertion.
4. Keep `assert scanned == indexed`: both approaches must return equivalent
   records in requested order.
5. Add duplicate ID data and confirm index creation raises `ValueError` before
   returning a partial result.

No Big-O notation is required. Do not benchmark elapsed time and do not create a
runtime index/cache feature.

## Python lookup → ordered IDs → visible M15 route

| Local result | Declarative route member | Visible order |
|---|---|---|
| `signal-map` | Signal Map | first |
| `river-token` | River Token | second |
| `summit-bell` | Summit Bell | third |

Python remains local. The ID dictionary is a local reasoning tool; validated
declarative YAML remains the Trail source of truth.

## World payoff

```console
explore-package validate lessons/sessions/s24/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s24/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "complete-actions-in-order" \
  --name "S24 Fast Ranger Index"
```

Focus the window and interact Signal Map → River Token → Summit Bell. Checkpoint:
the keeper completes only after the route resolved by both local approaches.

## Test and deliberate debug

- Equal results: assert scanned and indexed record lists match exactly.
- Duplicate ID: define fail-closed behavior as `ValueError` while building.
- Missing ID: both approaches return `None` in the same requested position.
- Accidental order change: compare full lists, not sets.

## Support path

Use tally marks beside each record and trace only size 6. The teacher may provide
the first target count. Printed IDs/counts and a teacher M15 demo are valid on low
bandwidth.

## Extension path

Try one requested ID near the front and explain why the scan count changes while
the one-time index build count does not.

## Required evidence/checkpoints

- Small and larger predictions before execution.
- Inspection counts: small `(15, 6)` and larger `(33, 12)`.
- Equivalent ordered results assertion.
- Explicit duplicate-ID failure test.
- Valid package and completed three-object M15 route.
- Answer: “When data doubles, what changes and why?”

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may ask one
cost-comparison question after your counts; it may not provide the count table.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s24/student
git diff --staged
git commit -m "Compare ranger lookup inspection counts"
```

Interpret `M`, `??`, and no output; use identity recovery and Control-C
cancel/correct/retry. Stage code with its equivalence/duplicate tests.
Understanding takes priority over a rushed commit.
