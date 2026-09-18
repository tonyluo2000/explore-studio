# S24 Task Card — Fast Ranger Index

**Role:** Python-primary software fluency

**World payoff:** Resolve three IDs efficiently, preserve their requested order,
then play that ordered route with existing M15 `complete-actions-in-order`.

**Learning target:** Compare repeated linear searches with one ID→record
dictionary by counting record inspections, then improve code you already have —
clarity, duplication, naming, stable order, player-facing text — while proving
the behavior did not change.

**What "optimize" means here:** making the thing easier to read, easier to
change, reliably ordered, and nicer to play. It does **not** mean making it
faster. The only cost claim in this session is counted record inspections,
because that is the only thing you actually measure. Do not say something "runs
faster" unless you timed it, and this session does not time anything.

**Where this sits:** S21 validated, S22 debugged, S23 composed. S24 is the last
step before S25: take a system that already works and make it better without
breaking it. That is most of what real building is.

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

## Improve it without changing what it does

Bring your S23 system if you have it, or use `route_briefing()` in
`starter.py` — it is the fixture for this step. It is already correct. It is
also copy-pasted three times, and its names (`r0`, `t0`, `out`) say nothing.

1. **Record the behavior first.** Run `behavior_signature()` and save the exact
   result. This is your evidence, and you take it *before* you touch anything.
2. **Name the improvement before making it.** Say which of these you are doing
   and why: removing duplication, clearer names, simpler logic, stable
   ordering, or better player-facing text. One improvement, stated out loud.
3. **Make it.** `route_briefing` should end up as one loop over `ROUTE` with
   names a reader understands. Do not add a class, a framework, or a new file.
4. **Prove nothing changed.** Run `behavior_signature()` again and compare it
   with the saved one. They must be identical, including list order:

   ```python
   before = behavior_signature()
   # ... your improvement ...
   assert behavior_signature() == before
   ```

   Comparing by hand is fine too — but compare the *whole* thing, in order.
5. **Say what you did not claim.** Your improvement made the code clearer. It
   did not make it faster, and you have no measurement that says otherwise.

If the signature changes, you did not improve the code — you changed it. Undo
and try again with a smaller step.

### Player-facing polish (optional, same rule)

If you improve the wording in your package's `when_near`/`when_interacted` text,
the rule is unchanged: the route still completes in the same order and M15 still
finishes. Clearer text, identical behavior.

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
- Improvement that quietly changed behavior: reorder `ROUTE`, rerun
  `behavior_signature()`, and watch the comparison fail. Restore it. This is why
  you record the signature before editing and not after.

## Support path

Use tally marks beside each record and trace only size 6. The teacher may provide
the first target count. For the improvement, renaming `r0`/`t0`/`out` alone is a
complete, honest improvement — the loop can wait. Printed IDs/counts and a
teacher M15 demo are valid on low bandwidth.

## Extension path

Try one requested ID near the front and explain why the scan count changes while
the one-time index build count does not.

## Required evidence/checkpoints

- Small and larger predictions before execution.
- Inspection counts: small `(15, 6)` and larger `(33, 12)`.
- Equivalent ordered results assertion.
- Explicit duplicate-ID failure test.
- The `behavior_signature()` you recorded **before** your improvement.
- The improvement you named, and the same signature afterwards.
- One sentence stating what your improvement did **not** claim.
- Valid package and completed three-object M15 route.
- Answer: “When data doubles, what changes and why?”

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may ask one
cost-comparison question after your counts; it may not provide the count table,
rewrite `route_briefing` for you, or tell you which improvement to make.

## Git close

**ZIP path check:** Do this section only if your course folder is Git-managed (the Derived student repository path) or your class has already started the Git lesson. On the ZIP path before that lesson, skip it — see [Student Quick Start → Later: Git](../../student-quick-start.md#later-git-optional-teacher-managed).

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
