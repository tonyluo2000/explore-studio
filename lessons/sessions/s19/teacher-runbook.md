# S19 — Route Planner

**Role:** Python-primary data fluency

**World reuse:** M15 `complete-actions-in-order`

**Learning objective:** Students can flatten nested zone/object records, return
a new list from `sorted` with a key function, predict stable tie order, and use
the first three results as an M15 sequence.

**Prerequisite:** S16–S18 traversal, functions, and data reasoning.

## Before class

- Run shared setup checks and validate the Priority Route package.
- Prepare four cards in original nested order; mark two with priority 2.
- Keep `.sort()` and `sorted(...)` examples ready for mutation comparison.
- Prepare text-only route evidence for accessibility/low bandwidth.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: turn two messy zones into one deliberate route. | Names a useful priority rule. |
| 0:04–0:10 | 5–6 min | Predict flattened order, tied order, and original-list state. | Stable-tie and mutation predictions. |
| 0:10–0:28 | 16–18 min | Complete two simple flatten loops and `sorted(..., key=...)`. | Flat list, sorted copy, first three IDs. |
| 0:28–0:35 | 6–7 min | Map first three results to M15 and play the route. | Correct sequence and payoff. |
| 0:35–0:42 | 6–7 min | Debug equal keys, missing priority, and accidental `.sort()` mutation. | Three explained/recovered cases. |
| 0:42–0:45 | 2–3 min | Review algorithm/story diff and commit. | Descriptive Git close. |

**Teacher cut line:** At 0:28, stop route decoration once four records flatten and
sort. At 0:35, accept a teacher M15 demo. Protect stable-tie and mutation
explanations. Git may finish asynchronously.

## Student task and prediction

Students predict flattened order `mist-bell, river-rune, star-lens, echo-shell`,
then sorted order `river-rune, mist-bell, star-lens, echo-shell`. Mist Bell stays
before Star Lens because Python sorting is stable when both keys equal 2.

## Deliberate debugging exercise

Temporarily omit one `priority` to observe/read `KeyError`; restore it. Compare a
copy returned by `sorted` with `.sort()` changing the original list. Equal keys
are not an error: their input order is preserved.

## Expected output and behavior

Flattening preserves zone then object order. `sorted(records, key=lambda
record: record["priority"])` returns a new list and leaves `flat_records`
unchanged. First three IDs drive M15: River Rune, Mist Bell, Star Lens.

## Bounded AI assistance

Use the canonical workflow. AI may explain the sort key only after student
prediction; it may not write flattening/sorting code or determine the route.

## Git close

Commit the algorithm separately from optional story-data edits. Use shared Git
interpretation/recovery and staged-diff review.

## Optional extension

Change one priority and predict the new stable order before running. No generalized
algorithm abstractions.

## Teacher notes and answer key

- Flatten uses one outer zone loop and one inner object loop with `append`.
- Sort answer is `sorted(records, key=lambda record: record["priority"])`.
- Tied Mist Bell/Star Lens retain that relative order; `sorted` does not mutate
  the original, while `list.sort()` does and returns `None`.
- Missing priority raises `KeyError`; restore the authored key.
