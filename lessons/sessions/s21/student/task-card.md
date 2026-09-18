# S21 Task Card — Package Gatekeeper

**Role:** Python-primary software fluency

**World payoff:** Reject malformed local data, repair it, then reuse M06
`build-an-object-collection`.

**Learning target:** Write defensive validation functions that return an ordered
error list for missing fields, wrong types, invalid ranges, and duplicate IDs,
then use the package validator to repair one real broken package yourself.

**Where this sits:** S20 finished the Data Fluency arc — we built a pipeline.
S21 opens **Build Quality / Systems Practice**: now we learn how to tell whether
what we built is valid. Validation is a creator's tool, not a command you run at
the end. For the rest of this arc you own more of the repair: S21 you fix a
validity problem, S22 you fix a bug, S23 you compose a system, S24 you improve
it without breaking it.

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
| empty error list and package validator passes | your repaired package accepted | the M06 collection can run |

Python remains local. The local function does not replace `explore-package`;
validated declarative YAML is the shared-runtime source of truth.

## You repair the broken package

`student/invalid-package` is deliberately broken but safe. You own the repair.

1. **Inspect first.** Read `invalid-package/manifest.yaml`. List what the
   manifest promises the package contains, then list what is actually on disk.
2. **Run the existing validator** and copy its diagnostic exactly:

   ```console
   explore-package validate lessons/sessions/s21/student/invalid-package
   ```

3. **Interpret it.** The diagnostic names a contribution path. Say in one
   sentence what the validator checked and why a manifest promise that no file
   keeps is a validity problem, not a style problem. Do not launch a package
   that fails: fail closed.
4. **Decide, then self-check.** Write the record you will author — its `name`,
   `x`, `y`, `color`, `when_near`, and `when_interacted` are your choices — and
   run it through your own `validate_records` from `starter.py` **before** you
   create the file:

   ```python
   validate_records([{"id": "missing-tool", "name": ..., "x": ..., "y": ..., "color": ...}])
   ```

   Your validator must return `[]` first. Note where `id` comes from: the
   manifest's contribution `id`, not the object file's body. Your local
   validator and the package contract do not have identical shapes, and knowing
   that difference is part of the lesson.
5. **Author the missing file** at `invalid-package/objects/missing-tool.yaml`,
   filling in your own values:

   ```yaml
   name: "___"
   x: ___
   y: ___
   color: "___"
   when_near: "___"
   when_interacted: "___"
   ```

6. **Rerun the same validator command** and record the PASS.
7. **Explain why it now passes.** Name the check that failed before, the exact
   change you made, and why the validator is satisfied now. "I added a file" is
   not the answer; "the manifest declares `objects/missing-tool.yaml` and that
   file now exists and matches the v0.1 world-object contract" is.

Keep coordinates inside the range your own validator enforces and pick a colour
the validator accepts. If your repaired package still fails, read the new
diagnostic before changing anything else — one change, one rerun.

## World payoff and fail-closed check

Now validate and run the already-checked gatekeeper package:

```console
explore-package validate lessons/sessions/s21/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s21/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "build-an-object-collection" \
  --name "S21 Package Gatekeeper"
```

Focus the Trail window; use WASD/arrows and E. Checkpoint: record the failed
validator diagnostic, your repair, the PASS, and all three visible tools.

## Test and deliberate debug

Use table rows named valid, missing, wrong type, invalid range, and duplicate ID.
For each row: predict the ordered list, run, compare, repair one value, rerun.

## Support path

Use the prepared cases and highlight each check category. A teacher may provide
one expected diagnostic, but the student orders the rest. For the repair, a
teacher may read the diagnostic aloud and supply one field value; the remaining
fields and the explanation stay the student's. Printed validator output and a
teacher world tour are valid on low bandwidth.

## Extension path

Add one boundary row for x=40 or x=760 and explain why it is valid.

## Required evidence/checkpoints

- Complete ordered-diagnostic prediction before execution.
- Table-driven valid and malformed results.
- Invalid package fails closed; the copied validator diagnostic and your
  interpretation of it.
- Your authored record passes your own `validate_records` before the file
  exists.
- Your repaired `invalid-package` validates, plus the sentence explaining why.
- Three-object M06 collection runs.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may supply
at most one malformed example; it may not write the validator, order the
answers, interpret the validator diagnostic for you, or author your repair file.

## Git close

**ZIP path check:** Do this section only if your course folder is Git-managed (the Derived student repository path) or your class has already started the Git lesson. On the ZIP path before that lesson, skip it — see [Student Quick Start → Later: Git](../../student-quick-start.md#later-git-optional-teacher-managed).

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
