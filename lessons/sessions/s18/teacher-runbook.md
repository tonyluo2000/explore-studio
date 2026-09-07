# S18 — Power Station Scoreboard

**Role:** Python-primary data fluency

**World reuse:** M09 `count-object-interactions` and M13
`compare-a-counter-to-its-goal`

**Learning objective:** Students can state an empty-input contract, use helper
functions with `min`, `max`, `sum`, and simple average, identify ties, and test
below/exactly/above a goal.

**Prerequisite:** S17 functions and S09–S10 counter/boundary work.

## Before class

- Run shared setup checks; validate the Power Station Scoreboard package.
- Prepare count cards 2, 4, 4 and a number line around goal 3.
- Require the empty-input decision before any summary code.
- Offer text results and a teacher Trail demonstration for low bandwidth.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: decide which power device needs attention. | States one useful scoreboard measure. |
| 0:04–0:10 | 5–6 min | Predict min/max/total/average/ties/boundary and define empty input. | Written contract and predictions. |
| 0:10–0:28 | 16–18 min | Complete summary placeholders and `at_goal` return; compare outputs. | Correct returned summary and boundary values. |
| 0:28–0:35 | 6–7 min | Author an existing M09 goal, validate/launch, and observe both M13 branches. | Goal message plus below/at-goal evidence. |
| 0:35–0:42 | 6–7 min | Assert empty, below, exact, above, and tied maximum behavior. | Passing cases and one repaired mismatch. |
| 0:42–0:45 | 2–3 min | Review source/test diffs and commit or schedule. | Descriptive Git close. |

**Teacher cut line:** At 0:28, stop extra statistics after min/max/total/average.
At 0:35, preserve below and exact-goal M13 evidence; above may remain local.
Protect the empty-input contract. Git may finish asynchronously.

## Student task and prediction

Students decide and write `summarize_counts([]) returns None` before coding, then
predict minimum 2, maximum 4, total 10, average 10/3, a two-way maximum tie, and
goal-3 results for 2/3/4.

## Deliberate debugging exercise

Run `min([])` only after predicting the failure, then restore the early empty
return. Test an incorrect `count > goal` at equality. For ties, distinguish the
maximum value from the records sharing it.

## Expected output and behavior

The nonempty summary returns min 2, max 4, total 10, average `10 / 3`; empty
returns `None`. Boundary results are False, True, True. The Wind Core reaches its
M09 goal at three interactions; Station Reader displays M13 below and at/above.

## Bounded AI assistance

Follow the canonical workflow. AI may review the student's written function
contract only, not the implementation or answers.

## Git close

Read code and test diffs, stage, inspect `git diff --staged`, and commit with
shared status/identity/retry guidance.

## Optional extension

Return the IDs tied for maximum using a simple loop after core evidence.

## Teacher notes and answer key

- `minimum = min(counts)`, `maximum = max(counts)`, `total = sum(counts)`, and
  `average = total / len(counts)` after the empty guard.
- `at_goal` returns `count >= goal`; 2/3/4 against 3 yields False/True/True.
- Sun Core and Tide Core tie at count 4.
- The authored counter goal is current-contract data; local summaries do not run
  inside Trail.
