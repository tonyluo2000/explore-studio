# S12 — Allow Either Key

**Canonical mission:** M11 `open-with-either-switch` — Either Switch Opens It

**Audience and format:** Ages 10–14, online, 45 minutes; Python-primary

**Learning objective:** Students can reuse a two-Boolean-parameter function
shape with `or`, predict all four cases, and contrast every result with S11 AND.

**Prerequisite:** S11 completed AND table and shared Quick Start readiness.

## Before class

- Prepare the S11 AND table beside a blank OR table.
- Validate the Storm Rescue Signals package and paste the launch command in chat.
- Use the distinct rescue-navigation story: either beacon gives the pilot a
  route; this is not another two-key vault.
- Prepare low-bandwidth evidence through text output and a teacher demo.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Quick-start check; frame two independent rescue signals. | Explains “any condition may be true.” |
| 0:05–0:14 | 8–10 min | Require four OR predictions and an explicit row-by-row S11 comparison. | Four predictions plus changed/unchanged rows. |
| 0:14–0:27 | 12–14 min | Run the copied AND rule, select a one-signal mismatch, change to `or`, rerun. | Repaired function and selected mismatch explanation. |
| 0:27–0:40 | 11–14 min | Validate/launch M11; show both-off, river-only, hill-only, then optional both-on. | Three required cases and visible rescue payoff. |
| 0:40–0:42 | 2–3 min | Capture evidence and bounded AI receipt. | AND/OR contrast sentence. |
| 0:42–0:45 | 3–5 min | Interpret and stage changes; commit or schedule. | Commit or recovery plan. |

**Teacher cut line:** At 0:27, end extra table discussion after one precise AND/
OR mismatch. At 0:38, prioritize the three M11-required cases over both-on.
Git may finish asynchronously.

## Student task and prediction

Students complete the OR table before execution, then label each row “same as
S11” or “different from S11.” Require a reason for both one-signal rows.

## Deliberate debugging exercise

The starter intentionally carries over S11's `and`. Students select one
one-True case, compare prediction with output, replace only the operator with
`or`, and verify all four rows.

## Expected output and behavior

Correct results are `False`, `True`, `True`, `True`. The world remains locked
only when both signals are off. River-only and hill-only each show the rescue
response; those plus both-off complete M11. Both-on also uses the open response.

## Bounded AI assistance

Follow explain intent → predict → bounded question → test → revise → explain
accepted code. After student work, AI may explain one student-selected mismatch.
It may not supply a table or choose the mismatch first.

## Git close

Use the task-card sequence through `git diff --staged`; interpret status and use
identity/cancel/retry recovery. Understanding comes first.

## Optional extension

Write a fourth-world-state caption for both beacons on without changing schema.

## Teacher notes and answer key

- OR rows: False, True, True, True. AND rows: False, False, False, True.
- The two one-True rows are the differences; both-off and both-on match.
- Answer: `return river_on or hill_on`.
- M11 requires both-off, first-only, and second-only evidence; both-on is useful
  comparison evidence but not required for completion.
- Python illustrates the rule locally; fixed declarative YAML drives the Trail.
