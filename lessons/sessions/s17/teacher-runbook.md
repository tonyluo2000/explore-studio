# S17 — Clue Finder

**Role:** Python-primary data fluency

**World reuse:** M03 message mechanics with M06 `build-an-object-collection`

**Learning objective:** Students can implement and test small `find_by_id`,
`filter_by_color`, and `count_matching` functions using parameters, loops, and
return values while preserving original result order.

**Prerequisite:** S16 traversal and earlier functions/parameters.

## Before class

- Run shared setup checks and validate the Clue Finder package.
- Keep completed search bodies hidden; prepare no/one/multiple result cards.
- Paste the Trail command in chat and prepare text-only message evidence.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: find useful clues in an expedition catalog. | Chooses a target ID/color. |
| 0:04–0:10 | 5–6 min | Predict result order/count for no, one, and multiple matches. | Three predictions before code. |
| 0:10–0:28 | 16–18 min | Students implement the three empty function bodies with simple loops. | Returned record/None, ordered list, integer count. |
| 0:28–0:35 | 6–7 min | Use returned records to select M03 near/interacted messages in an M06 collection. | Selected clues visible in original order. |
| 0:35–0:42 | 6–7 min | Add assertions for no/one/multiple matches; test one edge case. | Passing assertions and explanation. |
| 0:42–0:45 | 2–3 min | Review source/test diff and commit together. | Descriptive Git close. |

**Teacher cut line:** At 0:28, stop message customization; require all three
functions at core level. At 0:35, accept package validation and a teacher visual.
Protect the no/one/multiple tests. Git may finish asynchronously.

## Student task and prediction

Before execution, students predict `find_by_id("missing")`, one green filter,
the two blue records in original order, and their count.

## Deliberate debugging exercise

Common faults: returning inside the loop after the first non-match, reversing
filter order, or returning the matching list instead of its count. Students use
the three cases to isolate one fault at a time.

## Expected output and behavior

`find_by_id` returns one record or `None`; `filter_by_color` returns a new ordered
list; `count_matching` returns an integer. Blue results remain River Mark then Sky
Thread. The package visualizes selected records and M03 near/interacted messages.

## Bounded AI assistance

Use the canonical workflow. AI may suggest exactly one edge case only after the
student implements and predicts. It must never write a search function.

## Git close

Commit implementations and assertions together after status, diff, stage, and
staged-diff interpretation. Use shared recovery guidance.

## Optional extension

Search one other existing key/value without generalizing the function design.

## Teacher notes and answer key

- No match: `None`/empty list/0 as appropriate; one green match: Moss Arrow;
  multiple blue matches: River Mark, Sky Thread; count 2.
- Correct functions each use one loop and return only after examining the right
  records. Preserve append order.
- Python selection is local reasoning; authored current-contract package fields
  drive the visible world.
