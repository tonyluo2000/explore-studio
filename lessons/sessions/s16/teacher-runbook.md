# S16 — Curator's Atlas

**Role:** Python-primary data fluency

**World reuse:** M06 `build-an-object-collection`

**Learning objective:** Students can read deeper list/dictionary records by key,
trace `enumerate` for two iterations, and produce a numbered object catalog with
one plain loop.

**Prerequisite:** S06 collections/loops and the shared Quick Start.

## Before class

- Confirm repository, virtual environment, Python, `explore-package`, Trail
  controls/focus, screen sharing, and Git identity using the Quick Start.
- Validate the Curator's Atlas package and paste the full launch command in chat.
- Prepare two paper/chat trace boxes labeled iteration 1 and iteration 2.
- Offer printed output and a teacher world tour for low-bandwidth access.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: turn a crowded museum into a readable atlas. | Names why numbering helps a visitor. |
| 0:04–0:10 | 5–6 min | Introduce record keys and `enumerate`; require two traces. | First two iteration values and output predictions. |
| 0:10–0:28 | 16–18 min | Run starter, add zone access, compare output, then use `debug.py`. | Numbered catalog and three diagnosed data faults. |
| 0:28–0:35 | 6–7 min | Validate/launch the M06 collection and tour in catalog order. | Three visible catalog objects visited. |
| 0:35–0:42 | 6–7 min | Repair missing key, duplicate ID, and wrong nesting one at a time. | Clean local rerun and explanation. |
| 0:42–0:45 | 2–3 min | Inspect focused diff and commit or schedule it. | Descriptive Git close. |

**Teacher cut line:** At 0:28, stop catalog decoration after one zone is added.
At 0:35, accept validation plus a text-described tour. Protect all three data
diagnoses. Git may finish asynchronously.

## Student task and prediction

Students complete first-two-iteration traces before running. Require the list
position, `number`, record ID, and predicted printed line for each.

## Deliberate debugging exercise

`debug.py` contains a missing `zone`, a duplicate `sun-dial` ID, and one record
nested under `object`. Students identify the category, repair one record, rerun,
and repeat. Do not introduce a comprehension or nested loop.

## Expected output and behavior

The final catalog starts `1. Sun Dial`, `2. Rain Jar`, `3. Moss Map` and includes
each ID, color, and zone. `enumerate(..., start=1)` supplies display numbers while
the records retain their authored IDs. M06 shows the same three-object collection.

## Bounded AI assistance

Workflow: explain intent → predict → bounded question → test → revise → explain
accepted code. AI may explain one iteration only after the student traces it.
It may not rewrite the loop or repair the whole data set.

## Git close

Use status, diff, stage, `git diff --staged`, and a descriptive commit. Interpret
`M`, `??`, and no output; use identity and Control-C retry guidance. Understanding
takes priority over a rushed commit.

## Optional extension

Add a readable `category` key to each flat record and one catalog field. Keep one
loop; no comprehensions or nested loops.

## Teacher notes and answer key

- First trace: number 1, `sun-dial`; second: number 2, `rain-jar`.
- Student edit: add `{record['zone']}` to the f-string.
- Correct debugging keeps `id`, `name`, `color`, and `zone` at the same record
  level and makes every ID unique.
- Python remains local; only validated package data enters the shared Trail.
