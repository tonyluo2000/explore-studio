# S27 Task Card — Capstone Core

**Role:** Project-primary production lesson

**World payoff:** Build deterministic in-memory dictionaries compatible with
existing M06 collection and M14 named-style reuse, then compare them with your
editable package reference.

**Learning target:** Implement your accepted S26 contracts as small imported
helpers without writing YAML or expanding runtime behavior.

Use the shared [`Student Quick Start`](../../student-quick-start.md) and continue
your persistent `project-record.md`.

## Goal (0:00–0:04)

Retain your own S26 premise, three acceptance criteria, responsibility map,
contracts, risks, and deferred decision. The included Skyglass Observatory data
is editable scaffolding, not a required premise.

Your module owners are:

| Module | One responsibility |
|---|---|
| `data_io.py` | provide editable in-memory data and flatten validated zones |
| `validation.py` | produce ordered fail-closed diagnostics |
| `rules.py` | search, filter, aggregate, and stably order records |
| `builder.py` | transform records into deterministic package dictionaries |
| `starter.py` | import and coordinate the modules without owning their logic |

## Predict intermediate shapes (0:04–0:09)

Before implementing each helper, record in `project-record.md`:

- input shape;
- output shape;
- one concrete example;
- one failure/edge case where applicable.

Also write one explicit intermediate-value trace across the entire pipeline:

```text
nested project input
→ ordered diagnostics
→ flattened station records
→ required-ID search
→ enabled filtering
→ aggregation
→ stable route ordering
→ deterministic declarative document dictionaries
```

Do not code until you can show the concrete list/dictionary shape at every
arrow, including where invalid input stops.

## Build the modular core (0:09–0:31)

Implement these student-owned helpers without combining responsibilities:

- `validate_plan`
- `flatten_stations`
- `find_required`
- `select_enabled`
- `order_route`
- `signal_total`
- `build_documents`

Rules and validation stay file-free. `build_documents` returns dictionaries and
does not serialize or write YAML. `starter.py` stays thin.

Validation must fail closed with deterministic diagnostic ordering. Reject
duplicate IDs, wrong container/value types, invalid coordinate/order/power
ranges, and invalid named-style references before building documents.

Run the thin scaffold after predictions:

```console
python lessons/sessions/s27/student/starter.py
```

These tests are expected to fail until you complete the TODO functions.
The expected pristine result is **6 failed / 2 passed**.
`test_accepted_s26_plan_has_no_diagnostics` and
`test_empty_zone_flattens_to_empty_list` pass only because the current TODO
stubs return empty lists.
Those two passes are stub artifacts, not completed work: both `validate_plan`
and `flatten_stations` still need real implementations because other cases fail.

```console
python -m pytest -q lessons/sessions/s27/student/test_core.py
```

Keep `fixtures.py` fixed. The cases cover the accepted nested plan, empty zone,
missing required station, wrong-type record, duplicate ID, stable-order tie,
aggregation, and exact deterministic documents.

## Inspect package-compatible output (0:31–0:38)

The final in-memory value has this shape:

```text
{
  "manifest": {current schema/package/style/contribution fields},
  "objects": [current world-object document dictionaries in stable order],
}
```

It contains exactly one named toggle style. Exactly two objects reference that
style; the third is an ordinary colored object. This is compatible with existing
M06 collection and M14 named-style behavior only.

Compare the exact dictionaries with `explorer-package/`, then validate and plan:

```console
explore-package validate lessons/sessions/s27/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s27/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "build-an-object-collection" \
  --name "My S27 Capstone Core Reference"
```

For the M14 comparison, use the same package with mission ID
`reuse-a-named-toggle-style`. Do not create or overwrite YAML in S27. S28 owns
final package-file writing.

The ownership chain remains:

```text
editable data → local Python reasoning → reviewed YAML
→ student package → validation → M06/M14 play
```

The shared runtime consumes validated YAML only; it never runs student Python.

## Tests and review (0:38–0:42)

Complete the test, intermediate-shape, behavior, and refactoring evidence in
`project-record.md`. That record also contains the only self-review and AI
receipt blanks; they are not duplicated here.

## AI boundary

AI may propose exactly ONE failing test. First predict why it should fail. You
decide whether to use it and record accept/reject reasoning in
`project-record.md`. You implement all production code yourself.

AI may NOT write helper bodies, choose module boundaries, generate package
documents, solve validation, or provide final expected outputs. Do not paste
whole files or ask for a complete solution.

## Git close (0:42–0:45)

Use status → diff → staged diff and small behavior-based commits:

1. validation + tests;
2. flatten/search/filter + tests;
3. ordering/aggregation + tests;
4. document-builder + regression evidence.

```console
git status --short
git diff
git add lessons/sessions/s27/student
git diff --staged
git commit -m "Implement one capstone core behavior"
```

There is no squash requirement. Interpret `M`, `??`, and no output; use identity
recovery and Control-C cancel/correct/retry.

## Support path

Use only the completed non-core `station_ids` example,
`SINGLE_ZONE_REDUCED_PLAN`, the responsibility-card reminder, and the expected
flattened shape (a source-ordered list of station dictionaries). Support reduces
data volume; it does not replace your premise or solve required helpers.

## Extension

Add one second zone while preserving deterministic flatten and stable order.

## Cut line

Protect validation, flattening, one selection/search rule, stable ordering, and
deterministic in-memory document output. Optional aggregation polish may defer.
Do not write YAML, build the full capstone, add mechanics, or polish beyond the
accepted scope.
