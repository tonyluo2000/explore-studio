# S09 — Power Up a Device

**Canonical mission:** M09 `count-object-interactions` — Power It Up

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can update an integer counter toward a bounded
goal with a simple loop, predict the exact success interaction, diagnose an
off-by-one error, and write one basic assertion.

**Prerequisite:** S06 loops and S02 integer values.

## Before class

- Send the task card and confirm shared Quick Start readiness.
- Validate the counter package and prepare four visible tally marks.
- Do not supply the complete assertion before a student states what must be
  equal after the loop.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Frame repeated sparks charging a device. | Predicts a bounded goal. |
| 0:05–0:12 | 6–8 min | Trace one update and collect counts 1–4 plus exact success point. | Written count trace with interaction 3 circled. |
| 0:12–0:27 | 13–16 min | Run the loop, author one assertion, create the off-by-one case, read failure, and restore. | Passing assertion and explanation. |
| 0:27–0:38 | 9–12 min | Map goal/message to YAML, validate, launch M09, and interact one press at a time. | Count feedback and M09 completion. |
| 0:38–0:42 | 3–5 min | Compare exact success point and test one post-goal interaction if time. | Prediction/result reconciliation. |
| 0:42–0:45 | 3–5 min | Inspect status/diffs; commit or schedule it. | Descriptive commit or plan. |

**Teacher cut line:** At 0:27, require a restored passing loop and one
student-authored assertion, then move to the world. At 0:38, stop relaunching;
protect the exact-success explanation and defer Git if needed.

## Student task and prediction

Students use `student/task-card.md`. Require the four-count trace and circled
success point before running Python or the Trail.

## Deliberate debugging exercise

Changing the stop value from `goal + 1` to `goal` produces only two iterations
for goal 3. The student predicts `count == 2`, observes the assertion failure,
and restores the correct range.

## Expected output and behavior

The correct starter prints `1 1`, `2 2`, and `3 3`; a correct assertion
`assert count == goal` passes silently. The package goal is 3. Trail feedback
increments once per successful targeted interaction, success first appears on
interaction 3, counts may continue beyond goal, and M09 completes at the goal.

## Bounded AI assistance

Workflow: explain intent → predict → bounded question → test → revise → explain
accepted code. AI may suggest one boundary case only after the student's exact
success prediction. It may not write the loop or assertion.

## Git close

Follow the task card through staged diff and descriptive commit. Use shared Git
recovery and permit asynchronous completion.

## Optional extension

Observe interaction goal + 1 and explain continued counting without adding new
runtime mechanics.

## Teacher notes and answer key

- Goal 3 trace: counts 1, 2, 3, 4; first success is interaction 3.
- Student assertion: `assert count == goal`.
- Off-by-one form `range(1, goal)` stops before 3 and ends at count 2.
- Package `goal` accepts only non-Boolean integers 2–5. Runtime increments once,
  does not reset or cap, and shows the goal message whenever count is at least
  the goal.
