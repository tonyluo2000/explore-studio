# S10 — Check the Boundary

**Canonical mission:** M13 `compare-a-counter-to-its-goal` — Check the Power Level

**Audience and format:** Ages 10–14, online, 45 minutes; Python-primary

**Learning objective:** Students can define `at_goal(count, goal)`, return the
result of `count >= goal`, predict goal - 1/exact goal/goal + 1 before seeing the
comparison, and verify all three cases with assertions.

**Prerequisite:** S09 counters and S04 functions.

**Expedition thread:** The Weather Reader is the observatory's threshold
check on the engine charged in S09's story. The goal is not an arbitrary
number — it is the exact charge the story treats as "enough to launch," which
is why the exact-goal case matters pedagogically: real thresholds are almost
always about whether "just enough" counts, not only "too little" versus
"plenty."

1. Student predicts what should happen at goal - 1, exactly at goal, and
   goal + 1, before any code decides for them.
2. The revealed comparison, `count >= goal`, is the Weather Reader's rule:
   reaching the goal exactly must count as ready, not almost-ready.
3. Below goal, the Weather Reader names what is missing; at or above goal, it
   declares the storm ready to launch.
4. This session's engine begins uncharged again — the story continues from
   S09, but the Trail state does not.

**Critical honesty:** This is a fresh package instance, not a saved
continuation of S09's charge — do not tell students the engine "remembers"
last session. Preserve `count >= goal` exactly; changing it to `count >
goal` is the one intentional boundary flip for the debugging exercise, and it
must be restored before the checkpoint. There is no second, hidden threshold
or executable rule beyond the same-package counter's authored goal.

## Before class

- Send the task card but do not reveal this runbook's answer key.
- Confirm shared Quick Start readiness and validate the counter/NPC package.
- Prepare a number line. Require written explanations for all three prediction
  rows before revealing `count >= goal`.
- Do not allow AI-generated truth tables or answers before student reasoning.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Frame a Weather Reader deciding whether a storm can launch. | States what “enough power” means. |
| 0:05–0:14 | 8–10 min | Withhold the operator; collect goal - 1, goal, and goal + 1 predictions and reasons. | Three completed prediction rows. |
| 0:14–0:30 | 14–17 min | Reveal `count >= goal`; students complete the one-line function, compare outputs, add three assertions, then debug `>`. | Correct return and three passing assertions. |
| 0:30–0:39 | 8–11 min | Map boundary states to declarative responses, validate, launch M13, and display below/exact-goal responses. | Both NPC branches and M13 completion. |
| 0:39–0:42 | 3–4 min | Complete creative/Python/test self-review and consider one student-predicted edge case. | Three-part self-review. |
| 0:42–0:45 | 3–5 min | Inspect status/diffs; commit or schedule it. | Descriptive commit or plan. |

**Teacher cut line:** At 0:30, end optional Python discussion. Protect all three
predictions, the one-line return, and three assertions. At 0:39, stop relaunching
and protect both M13 response explanations plus the canonical self-review. Git
may finish asynchronously.

## Student task and prediction

Students follow `student/task-card.md`. Check the three written boundary rows
before saying or displaying the final comparison. The placeholder function is
runnable but deliberately returns False for every case.

## Deliberate debugging exercise

Replace `>=` temporarily with `>`. The exact-goal assertion must fail while the
other two remain consistent. Students restore `>=` and explain inclusion of the
boundary.

## Expected output and behavior

For goal 3, the final outputs are `False`, `True`, `True`. The function is:

```python
def at_goal(count, goal):
    return count >= goal
```

The three assertions verify goal - 1 is False, exact goal is True, and goal + 1
is True. In the Trail, the NPC shows the below response before enough object
interactions and the at-or-above response at goal; displaying both completes
M13. Talking to the NPC does not increment the counter.

## Bounded AI assistance

Workflow: explain intent → predict → bounded question → test → revise → explain
accepted code. AI must not generate a truth table, comparison, or boundary
answers before all three predictions. Afterward it may propose exactly one edge
case, which the student predicts and explains before testing.

## Git close

**ZIP classes:** Skip this step for classes still on the ZIP distribution that have not started the Git lesson yet; use it once the class has a Git-managed course folder. See [Student Quick Start → Later: Git](../student-quick-start.md#later-git-optional-teacher-managed).

Follow the task card through staged diff and descriptive commit. Use shared Git
interpretation/recovery and allow asynchronous completion.

## Optional extension

Test one additional integer edge case only after the core predictions and three
assertions. Keep the function to one comparison and one return.

## Teacher notes and answer key

- Goal - 1: False; exact goal: True; goal + 1: True.
- Required comparison: `count >= goal`.
- Assertions for goal 3 may be `assert at_goal(2, 3) is False`,
  `assert at_goal(3, 3) is True`, and `assert at_goal(4, 3) is True`.
- `count > goal` fails at exact equality. That is the deliberate boundary bug.
- The package NPC references the same-package counter. Runtime uses that
  counter's authored goal; there is no second threshold or executable rule.
