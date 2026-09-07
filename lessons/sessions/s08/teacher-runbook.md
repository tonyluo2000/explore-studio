# S08 — Build an If/Else Guardian

**Canonical mission:** M08 `respond-to-object-state` — Make an If/Else Character

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can predict and explain both branches of a
small `if`/`else`, repair an inverted condition, and author the matching fixed
NPC response to one same-package toggle.

**Prerequisite:** S07 Boolean state and S04 character authoring.

## Before class

- Send the task card and confirm shared Quick Start readiness.
- Validate the two-contribution package and prepare False/True branch cards.
- Withhold execution until both student predictions are recorded.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Ask how one guardian could react to a sleeping and awake gate. | Authors two contrasting intentions. |
| 0:05–0:12 | 6–8 min | Read `if`/`else` aloud and collect both predictions before execution. | False/True responses plus plain-language rule. |
| 0:12–0:25 | 11–15 min | Run the inverted branch, compare result, repair only the condition, and retest. | Correct output and branch explanation. |
| 0:25–0:38 | 10–13 min | Map branches to YAML, validate, launch M08, speak off, toggle, then speak on. | Both visible branches and M08 completion. |
| 0:38–0:42 | 3–5 min | Reconcile prediction and result; collect AI receipt if used. | Evidence for both states. |
| 0:42–0:45 | 3–5 min | Inspect status/diffs; commit or schedule it. | Descriptive commit or plan. |

**Teacher cut line:** At 0:35, stop response-writing. Protect both Python branch
results and both Trail NPC responses. If relaunch is blocked, demonstrate one
state change while the student narrates; defer Git, not reasoning.

## Student task and prediction

Students follow `student/task-card.md`. Require both predictions and a spoken
plain-language condition before running the deliberately inverted starter.

## Deliberate debugging exercise

The starter uses `if not is_on`, incorrectly choosing the open response for
False. Students identify the mismatch from evidence and change only the
condition to `if is_on`.

## Expected output and behavior

Before repair, output order is open then sleeping. After repair, it is sleeping
then open. The package validates only when the NPC references the exact
same-package toggle ID. In the Trail, speaking while off records the off branch;
after one toggle, speaking records the on branch and completes M08.

## Bounded AI assistance

Workflow: explain intent → predict → bounded question → test → revise → explain
accepted code. AI may compare the two recorded predictions with results. It may
not generate, invert, or replace the branch logic.

## Git close

Follow the task card through staged diff and descriptive commit. Use shared Git
interpretation and recovery; allow asynchronous completion.

## Optional extension

Strengthen the guardian voice in the two existing response strings only.

## Teacher notes and answer key

- Correct local condition: `if is_on` returns the open response; `else` returns
  sleeping.
- Off must be displayed before or after on; M08 requires evidence for both.
- The NPC does not toggle the object. Students toggle the object separately,
  then talk to the NPC again.
- `object_id` must remain unqualified, exact, and same-package.
