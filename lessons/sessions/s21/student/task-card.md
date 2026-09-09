# S21 Task Card — Package Gatekeeper

**Role:** Python-primary software fluency

**World payoff:** Reject malformed local data, repair it, then reuse M06
`build-an-object-collection`.

**Learning target:** Write defensive validation functions that return an ordered
error list for missing fields, wrong types, invalid ranges, and duplicate IDs.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict before running

Read the malformed table in `starter.py`. Before running, number every expected
diagnostic in this fixed order: record shape → missing fields → wrong types →
invalid ranges → duplicate ID. Checkpoint: explain why one record can produce
more than one error and predict the complete printed order.

## Core Python path

1. Run `python lessons/sessions/s21/student/starter.py`.
2. Compare the returned error list—not only its contents—with your prediction.
3. Add the one table-driven case for a non-dictionary record at the TODO.
4. Change one field at a time in a copied malformed case and rerun.
5. Keep this as small functions and ordinary loops; do not build a generic
   validation framework.

## Python check → package gate → visible world

| Local result | Declarative result | Visible result |
|---|---|---|
| nonempty ordered error list | invalid data stays rejected | Trail is not launched |
| empty error list and package validator passes | repaired M06 package accepted | three ranger tools appear |

Python remains local. The local function does not replace `explore-package`;
validated declarative YAML is the shared-runtime source of truth.

## World payoff and fail-closed check

First validate `student/invalid-package`: it must fail, so do not launch it.
Then validate and run the repaired package:

```console
explore-package validate lessons/sessions/s21/student/invalid-package
explore-package validate lessons/sessions/s21/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s21/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "build-an-object-collection" \
  --name "S21 Package Gatekeeper"
```

Focus the Trail window; use WASD/arrows and E. Checkpoint: record the failed
validator diagnostic, the repaired PASS, and all three visible tools.

## Test and deliberate debug

Use table rows named valid, missing, wrong type, invalid range, and duplicate ID.
For each row: predict the ordered list, run, compare, repair one value, rerun.

## Support path

Use the prepared cases and highlight each check category. A teacher may provide
one expected diagnostic, but the student orders the rest. Printed validator
output and a teacher world tour are valid on low bandwidth.

## Extension path

Add one boundary row for x=40 or x=760 and explain why it is valid.

## Required evidence/checkpoints

- Complete ordered-diagnostic prediction before execution.
- Table-driven valid and malformed results.
- Invalid package fails closed; repaired package validates.
- Three-object M06 collection runs.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may supply
at most one malformed example; it may not write the validator or order answers.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s21/student
git diff --staged
git commit -m "Validate package records in order"
```

`M` means modified; `??` means untracked; no output means nothing is pending in
that view. Use identity recovery and Control-C cancel/correct/retry from Quick
Start. Commit one validation behavior with its regression case. Understanding
takes priority over a rushed commit.
