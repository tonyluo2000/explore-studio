# S29 Task Card — Expedition Review

**Role:** Project-primary production lesson

**World payoff:** Make your expedition understandable and dependable for its
next visitor while preserving the current M14 and M15 behavior.

**Learning target:** Use evidence-linked review, two bounded refactors, regression
tests, and a complete visitor walkthrough without changing runtime behavior.

Use the shared [`Student Quick Start`](../../student-quick-start.md) and continue
your persistent `project-record.md`. Your real S28 capstone remains primary.

## Review goal (0:00–0:04)

Refactoring changes structure, not promised behavior. The runtime still consumes
validated package YAML; it does not run your local Python pipeline. Start with
your own capstone code, data, generated package, and evidence.

Use `review_harness.py` to capture deterministic evidence. It is support code,
not a replacement for reviewing or refactoring your own work.

## Predict behavior risk before editing (0:04–0:09)

Before any peer, teacher, or AI suggestion:

1. annotate the current diff or code;
2. identify one duplicated record-shaping block;
3. identify one confusing multi-purpose responsibility and ambiguous name;
4. predict what each refactor could break;
5. name the test/evidence that would catch it;
6. predict which output must remain identical.

Record the details in `project-record.md`; the full blanks live there only.

Capture the before snapshot:

```console
python -m pytest -q lessons/sessions/s29/student/test_review_harness.py
```

The focused harness should be green before and after behavior-preserving work.
Do not edit package data merely to make a refactor appear necessary.

## Review and two bounded refactors (0:09–0:31)

Each peer, teacher, or AI observation must cite evidence: a line/function/test,
duplication, confusing name, unclear responsibility, weak regression check, or
observable behavior risk.

Respond to each item with exactly one decision:

- **accept** — state the intended change, behavior to preserve, and regression
  evidence;
- **reject** — give a technical reason tied to evidence;
- **ask one clarification** — state what evidence is missing before deciding.

Complete both required targets in your own project:

1. remove one duplicated record-shaping block;
2. split one confusing multi-purpose function into clearer named helpers and
   improve at least one ambiguous variable or function name.

Add or identify a targeted regression test for each accepted refactor. Preserve
inputs, return values, ordered diagnostics, stable file order/bytes, validation,
and Trail behavior. Review feedback must not replace your code wholesale.

## Prepared practice example

If your real capstone has no honest duplication or confusing function, inspect
the fixed `review-fixtures/prepared_review_example.py`. It is separate,
read-only, practice/support only, and cannot count as your real capstone work.

It contains duplicated record shaping, multi-purpose `run`, and ambiguous `x`.
Use `cases.yaml` and `expected-output.yaml` as before/after regression evidence.
No replacement implementation is provided. Never degrade your real project to
create a refactor target.

## Regression evidence

For each planned refactor, answer:

- What could break?
- Which test or evidence would catch it?
- What output should stay identical?

Required finish evidence:

- before-output file/size/SHA-256 snapshot;
- targeted regression tests;
- after-output snapshot comparison;
- empty deterministic package delta for behavior-preserving changes;
- package still validates and plans;
- manual M14/M15 smoke checklist.

Use `snapshot_package` and `compare_snapshots`; do not update an expected result
until you can explain whether the behavior change was intended.

## Complete visitor walkthrough (0:31–0:38)

Explain the full path to another person:

```text
source input
→ local Python pipeline
→ generated package files
→ package validation
→ Trail
→ representative M14 shared-style observation
→ representative M15 sequence path
```

Point to where data changes shape, which S27/S28 module owns each responsibility,
and which artifact is runtime source of truth. Show the two objects sharing the
M14 style, then the three M15 IDs in order and the existing wrong-member/reset
path. Add no schema fields or mechanics.

## Test and manual smoke (0:38–0:42)

```console
python -m pytest -q lessons/sessions/s29/student/test_review_harness.py
explore-package validate lessons/sessions/s29/student/explorer-package
```

Run targeted regression tests and the full default repository suite where
appropriate. Complete `review-checklist.md`, including planning/launch,
approach/interaction, M14 shared style, M15 correct order, wrong-member/reset,
and clean exit. A teacher-run Trail smoke is acceptable if you explain the path.

## AI boundary

Perform your own review first. AI may then provide at most **TWO evidence-based
review observations**. Each must cite a specific line, function, test, name,
duplication, or behavior risk and explain the concern without replacement code.

You decide accept/reject/clarify, implement changes yourself, and record the
reason. AI may NOT rewrite whole functions, provide the final refactor, replace
peer/teacher review, generate package contents, change architecture, or propose
new runtime features.

## Follow-up Git commit (0:42–0:45)

Preserve review history with follow-up commits such as review notes/tests,
duplication removal, responsibility/naming cleanup, and regression/smoke
evidence. Use status → diff → staged diff.

```console
git status --short
git diff
git diff --staged
git commit -m "Refactor one reviewed responsibility"
```

There is no squash/rewrite requirement. Do not hide the original reviewed state.

## Support, extension, and cut line

Support may narrow work to one function and duplication, provide one
evidence-linked comment, demonstrate comparison, or use the separate practice
fixture. Text diff, printed snapshots, console validation, and teacher-run Trail
are available. The teacher does not silently refactor student code.

Extension: improve one test name or user-facing validation/error message without
changing behavior, then rerun the same evidence chain.

Protect one duplication removal, one responsibility/name improvement, green
regression tests, unchanged deterministic output, package validation, and one
M14/M15 walkthrough. Defer cosmetic cleanup, extra refactors, and new features.
