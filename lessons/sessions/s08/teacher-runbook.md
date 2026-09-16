# S08 — Build an If/Else Guardian

**Canonical mission:** M08 `respond-to-object-state` — Make an If/Else Character

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can predict and explain both branches of a
small `if`/`else`, repair an inverted condition, and author the matching fixed
NPC response to one same-package toggle.

**Prerequisite:** S07 Boolean state and S04 character authoring.

**Expedition thread:** This is the gate S06 and S07 pointed toward. The
Guardian's refusal is the recoverable loop that carries the session:

1. Speak to the Guardian while the switch is off — it refuses passage.
2. The refusal names the fix: "Wake the sky switch, then come speak with me
   again." The clue always comes before the student can act on it.
3. Student toggles the Sky Switch.
4. Student speaks to the Guardian again.
5. The Guardian's response changes to grant passage narratively.

**Critical honesty:** The engine has no collision or locked-path system — a
student can always walk past the Guardian. "Blocked" here means the Guardian's
*spoken response*, not a barrier. Teach it exactly that way: the story gates
progress, not physics. Do not tell students or families that the world
"locks" the gate.

## Before class

- Send the task card and confirm shared Quick Start readiness.
- Validate the two-contribution package and prepare False/True branch cards.
- Withhold execution until both student predictions are recorded.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Ask how a guardian could refuse, then explain how, with a clue. | Authors a refusal that teaches and an acceptance that follows it. |
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
same-package toggle ID. In the Trail, speaking while off records the off branch
— the Guardian's refusal, which names the Sky Switch as the fix; after one
toggle, speaking records the on branch — the Guardian's acceptance — and
completes M08. Nothing about player movement changes at any point; only the
Guardian's line does.

## Bounded AI assistance

Workflow: explain intent → predict → bounded question → test → revise → explain
accepted code. AI may compare the two recorded predictions with results. It may
not generate, invert, or replace the branch logic.

## Git close

**ZIP classes:** Skip this step for classes still on the ZIP distribution that have not started the Git lesson yet; use it once the class has a Git-managed course folder. See [Student Quick Start → Later: Git](../student-quick-start.md#later-git-optional-teacher-managed).

Follow the task card through staged diff and descriptive commit. Use shared Git
interpretation and recovery; allow asynchronous completion.

## Optional extension

Strengthen the guardian voice in the two existing response strings only — keep
the refusal actionable (it must still name the fix) and the acceptance clearly
welcoming.

## Teacher notes and answer key

- Correct local condition: `if is_on` returns the open response; `else` returns
  sleeping.
- Off must be displayed before or after on; M08 requires evidence for both.
- The NPC does not toggle the object. Students toggle the object separately,
  then talk to the NPC again.
- `object_id` must remain unqualified, exact, and same-package.
