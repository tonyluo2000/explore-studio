# S07 — Create a Two-State Prop

**Canonical mission:** M07 `toggle-an-object-state` — Flip a Magic Switch

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can assign and distinguish `False` and `True`,
trace state and color across repeated interactions, and author one valid
declarative two-state prop.

**Prerequisite:** S02 types and S06 object authoring.

## Before class

- Send the task card and confirm shared Quick Start readiness.
- Validate the starter package; prepare a visible four-row state trace.
- Emphasize that local assignment illustrates change without mimicking runtime
  internals.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Ask what changes between two story states. | Names one prop and two appearances. |
| 0:05–0:12 | 6–8 min | Introduce Boolean literals and complete the interaction trace predictions. | Four predicted state/color rows. |
| 0:12–0:24 | 11–15 min | Run the local misconception, repair the assignment, and explain the two outputs. | `False blue`, then `True gold`. |
| 0:24–0:37 | 9–13 min | Edit only the inline toggle fields, validate, launch M07, and interact repeatedly. | Valid toggle and observed alternation. |
| 0:37–0:42 | 4–6 min | Reconcile every predicted row with observed color/state and M07 evidence. | Correct off/on trace. |
| 0:42–0:45 | 3–5 min | Inspect status/diffs; commit or schedule it. | Descriptive commit or plan. |

**Teacher cut line:** At 0:35, stop color/message revisions. Protect the local
Boolean correction and at least two observed interactions showing both states.
Use a teacher demonstration if needed; complete Git asynchronously.

## Student task and prediction

Students use `student/task-card.md` and must fill the full four-row trace before
running either activity.

## Deliberate debugging exercise

The starter prints an on color without changing `is_on`. Students reject the
misconception that printing a label mutates state and repair only the second
assignment.

## Expected output and behavior

Before repair, Python prints `False blue` and `False gold`. After repair it
prints `False blue` and `True gold`. The package validates with one inline
toggle. Trail state begins off and alternates on/off on each successful targeted
interaction; M07 completes after the toggle first changes.

## Bounded AI assistance

Workflow: explain intent → predict → bounded question → test → revise → explain
accepted code. AI may check the student's trace after completion, but may not
generate the object or replace the prediction.

## Git close

Follow the task card through staged diff and descriptive commit. Use shared
status, identity, cancellation, and asynchronous recovery guidance.

## Optional extension

Choose another supported distinct color pair and explain its story meaning.

## Teacher notes and answer key

- Trace: start False/blue; interaction 1 True/gold; interaction 2 False/blue;
  interaction 3 True/gold.
- Correct local line: `is_on = True` before the second print.
- Python assignment is only a model for reasoning. Runtime starts each toggle
  off, changes only the targeted toggle, and retains session-only state.
- Top-level `color` must not be added beside inline `toggle`; both colors must
  be supported and distinct.
