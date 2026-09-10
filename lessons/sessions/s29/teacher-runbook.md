# S29 — Expedition Review

**Role:** Project-primary production lesson

**World reuse:** M14 `reuse-a-named-toggle-style` and M15
`complete-actions-in-order`

**Learning objective:** Students can review evidence before changing code,
complete two bounded behavior-preserving refactors, respond technically to
review feedback, and explain the full capstone path to another person.

**Prerequisite:** The student's S25–S28 premise, persistent project record,
modular Python pipeline, deterministic integration boundary, and valid package.

## Before class

- Keep the student's real S28 capstone and premise as the primary artifact. Do
  not introduce artificial defects just to manufacture refactoring work.
- Confirm the student package validates and plans, and capture a byte snapshot
  with `student/review_harness.py` before any edit.
- Keep `student/review-fixtures/` fixed and read-only. It is clearly separate
  practice/support material and never counts as a refactor of the real capstone.
- Print `student/review-checklist.md` when screen sharing or bandwidth is poor.
- Require the student's own annotated review before peer, teacher, or AI input.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 4 min | Frame review as making the expedition dependable for another person. | Names behavior and runtime source of truth. |
| 0:04–0:09 | 5 min | Gate editing on annotations and risk predictions. | Duplication, responsibility/name, risk, catching test, unchanged output. |
| 0:09–0:31 | 22 min | Coach two bounded refactors without replacing student code. | Duplication removed; responsibility/name clarified; targeted tests. |
| 0:31–0:38 | 7 min | Listen to one complete visitor walkthrough. | Source-to-Trail explanation with M14 and M15 observations. |
| 0:38–0:42 | 4 min | Compare snapshots, validate, run tests, and complete smoke checklist. | Regression, deterministic bytes, validation, and manual smoke evidence. |
| 0:42–0:45 | 3 min | Review response and follow-up commit. | Decision-linked commit preserving review history. |

## Review-first gate

Before editing or asking any reviewer, the student annotates the current diff or
code and records in `student/project-record.md`:

- one duplicated record-shaping site;
- one confusing multi-purpose responsibility and one ambiguous name;
- what each proposed refactor could break;
- which test or evidence would catch that break;
- which package output should remain byte-identical.

Only after this student review may a peer, teacher, or AI offer observations.
Reject requests to paste whole functions for replacement.

## Evidence-linked review workflow

Every review observation points to a line, function, test, name, duplication,
unclear responsibility, or observable behavior risk. The student responds with
exactly one disposition: **accept**, **reject**, or **ask one clarification**.

For an accepted item, the record states the intended change, behavior to
preserve, and regression evidence. For a rejected item, it gives a technical
reason. A clarification names the missing evidence and is resolved before code
changes. Feedback never replaces the student's implementation wholesale.

## Two bounded refactor targets

1. Remove one duplicated record-shaping block by extracting or reusing one
   clearly named responsibility.
2. Split one confusing multi-purpose function into clearer named helpers and
   improve at least one ambiguous variable or function name.

Keep inputs, returned values, ordered diagnostics, deterministic package files,
and visible Trail behavior unchanged unless the student has explicitly recorded
a different intended behavior. Add or identify a targeted regression test for
each accepted change.

## Prepared review fixture

If the real capstone has no honest duplication or confusing responsibility, use
`student/review-fixtures/prepared_review_example.py` for practice. It contains:

- duplicated record shaping in `shape_records` and `shape_enabled_records`;
- multi-purpose `run` validation/filtering/formatting/count behavior;
- ambiguous parameter name `x` and function name `run`.

The YAML cases and expected output are fixed before/after evidence. Students may
annotate or copy the example into a disposable practice area, but must not edit
the read-only fixture, call it their capstone, or replace their project evidence
with it. The fixture deliberately has no completed refactor solution.

## Regression and deterministic evidence

Use `snapshot_package` before the first edit and after each refactor. Record the
stable relative file list, byte sizes, and SHA-256 digests. Use
`compare_snapshots` to show an empty delta where behavior is unchanged.

Required evidence:

- before-output snapshot;
- targeted regression test for duplication removal;
- targeted regression test for responsibility/naming refactor;
- after-output comparison;
- identical deterministic package bytes for unchanged behavior;
- package validation and planning success;
- existing M14 and M15 smoke observations.

Refactoring is not complete because code looks cleaner. It is complete when the
student can connect the change to regression evidence and preserved behavior.

## Visitor walkthrough

The student gives one uninterrupted explanation:

```text
source input
→ local Python pipeline
→ generated package files
→ package validation
→ Trail
→ representative M14 shared-style observation
→ representative M15 sequence path
```

Ask where source data changes into selected/ordered records, where records
change into package documents, which S27/S28 module owns each responsibility,
and why validated YAML—not student Python—is the runtime source of truth.

For M14, confirm the two shared-style objects. For M15, walk the three IDs in
order and note existing wrong-member/reset behavior. No new mechanic is needed.

## Tests and manual smoke

Run the focused learner harness, package validation/planning, targeted regression
tests, and full default repository suite where appropriate. Complete the manual
checklist in `review-checklist.md`: launch/plan, approach and interact, shared
style, ordered sequence, wrong-member/reset, and clean exit. A teacher-run Trail
demonstration is acceptable for the smoke path if the student explains it.

## Project record and AI boundary

Continue the persistent S25–S28 record. Add review observations,
accept/reject/clarify decisions, predicted risk per refactor, targeted regression
evidence, before/after output evidence, validation/planning, manual smoke, and
one lesson learned. Do not duplicate those blanks in the task card.

AI may provide at most **TWO evidence-based review observations**, only after the
student's own review. Each must cite a specific line, function, test, name,
duplication, or risk and explain the concern without replacement code. The
student decides accept/reject/clarify, implements the change, and records why.

AI may NOT rewrite whole functions, provide the final refactor, replace peer or
teacher review, generate package contents, change architecture, or propose new
runtime features.

## Git close

Preserve review history with follow-up commits such as:

1. review notes / test evidence;
2. duplication-removal refactor;
3. responsibility/naming refactor;
4. final regression/smoke evidence.

Use status → diff → staged diff. There is no squash or rewrite requirement, and
the original reviewed state must remain visible.

## Support, accessibility, extension, and cut line

If stuck, narrow to one function and one duplication site, give one
evidence-linked review comment, or use the prepared fixture. Demonstrate snapshot
comparison, but never silently perform the refactor. Text diff, printed
before/after output, console validation, and teacher-run Trail are valid access
paths.

Extension: improve one test name or one user-facing validation/error message
without changing behavior, then repeat the evidence chain.

By 0:38 protect one duplication removal, one responsibility/name improvement,
green regression tests, unchanged deterministic output, package validation, and
one M14/M15 walkthrough. Defer cosmetic polish, extra refactors, and new
features. Do not add S30 materials or engine/schema/Student API/Trail/Mission/
runtime behavior, deployment, authentication, or Phase E work.
