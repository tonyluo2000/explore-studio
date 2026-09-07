# S15 — Ship a Secret Sequence

**Canonical mission:** M15 `complete-actions-in-order` — Solve the Secret Sequence

**Audience and format:** Ages 10–14, online, 45 minutes; Python-primary first-half capstone

**Learning objective:** Students can decompose a three-object ordered puzzle
into small functions, validate exactly three distinct IDs, trace expected versus
attempted order with loops/state, and verify normal/reset cases with assertions.

**Prerequisite:** S04 functions, S05/S06 lists and loops, S09/S10 assertions and
state tracing, S11–S14 reasoning, and shared Quick Start readiness.

## Before class

- Validate all three required package roots: Nova at
  `examples/explorer-packages/nova-character`, the separate Crystal Lantern at
  `examples/explorer-packages/crystal-lantern`, and the Star Song Sequence at
  `lessons/sessions/s15/student/explorer-package`.
- Prepare three object cards plus an unrelated `crystal-lantern` card.
- Keep the exact Trail reset rules visible to the teacher, not as predictions.
- Arrange a 60-second screen-share presentation order and a text-only option.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Quick-start check and capstone story pitch. | Names the three authored IDs in order. |
| 0:05–0:12 | 6–8 min | Require traces for correct, wrong-member, and unrelated interactions before running. | Three written predictions with progress values. |
| 0:12–0:27 | 13–16 min | Complete distinct-ID validation, inspect small sequence helpers, add normal/reset assertions, test. | Passing normal and reset assertions plus trace output. |
| 0:27–0:38 | 10–13 min | Map IDs to ordinary/toggle/counter objects; validate, launch M15, test reset/unrelated/correct paths. | Exact runtime observations and M15 success. |
| 0:38–0:42 | 3–5 min | Run capstone checklist, canonical self-review, and 60-second presentation. | Creative/Python/test review and short demo. |
| 0:42–0:45 | 3–5 min | Inspect Git status/diffs; commit or schedule. | Descriptive commit or explicit recovery plan. |

**Teacher cut line:** At 0:27, stop optional helper refinements after distinct-ID
validation and the two required assertions. At 0:36, use one teacher Trail demo
for any missing world case. Protect self-review and presentation. Git may finish
asynchronously if setup consumed live time.

## Student task and prediction

Before running, students trace: correct sequence reaches 3; an authored wrong
member resets to 0 and is not immediately reconsidered as a new first step; an
unrelated object leaves progress unchanged. Require state after every interaction.

## Deliberate debugging exercise

The starter's ID validator accepts three entries even if an ID repeats. Students
add distinctness using a small `seen` list/loop or pairwise comparisons. Then
they add a reset assertion such as `star-map` followed by `echo-drum` equals 0.

## Expected output and behavior

The completed validator returns True only for exactly three distinct IDs.
Correct order returns progress 3. `star-map` then wrong authored member
`echo-drum` returns 0; that wrong member does not immediately restart progress.
After `star-map`, unrelated `crystal-lantern` leaves progress 1. In the Trail,
the same rules lead to the keeper's complete response and M15 completion.

## Bounded AI assistance

Workflow: explain intent → predict → bounded question → test → revise → explain
accepted code. AI may suggest tests only. It must never write the sequence
solution, order, trace, assertions, or helper implementation.

## Git close

Follow status/diff/stage/staged diff/commit. Interpret `M`, `??`, and no output;
recover identity or cancel/retry safely. Understanding comes before a rushed
capstone commit.

## Optional extension

Add one student-authored test for an unrelated object before any correct member
or for interaction after completion. Do not alter the fixed three-object rule.

## Teacher notes and answer key

- Distinct validator answer can use a `seen = []` loop and reject an ID already
  in `seen`, or compare all three pairs after checking length.
- Required normal assertion: `assert compare_order(expected, expected) == 3`.
- Reset assertion: `assert compare_order(expected, ["star-map", "echo-drum"]) == 0`.
- Correct trace: 0→1→2→3. Wrong authored member from progress 1: 1→0, with no
  immediate restart. Unrelated interaction from progress 1: 1→1.
- Completed progress never regresses. The counter can count independently; its
  membership in the sequence reacts to the interaction, not its goal.
- The package uses exactly three same-package sequence members: ordinary Star
  Map, toggle Moon Switch, counter Echo Drum. Nova is the player from one example
  package; Crystal Lantern is the unrelated object from a separate example package.
- Student Python remains local; declarative package data alone enters runtime.
