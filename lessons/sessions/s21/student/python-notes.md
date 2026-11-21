# S21 Python Notes — Package Gatekeeper

## 1. Today’s idea: Defensive validation and ordered diagnostics

A validator reports errors in a predictable order: container shape, missing fields, types, ranges and duplicate IDs. Invalid data must fail closed.

## 2. Predict before running

Predict each diagnostic for the malformed table row and the missing contribution file in invalid-package.

Write the prediction before opening AI help or running code.

## 3. Run and trace your own work

```console
python lessons/sessions/s21/student/starter.py
```

Use the task card for the complete sequence of commands and lesson cut line.
A runnable scaffold or an initially green support test is not proof that your
student-owned TODOs or project decisions are finished.

## 4. What we debugged

Add the requested non-dictionary case before changing the validator. Repair the genuinely invalid package with your own values, not by bypassing validation.

## 5. Evidence to keep

Show the failing diagnostic and the later PASS. Tour the repaired valid package; mission completion is not a substitute for validation evidence.

Record the original prediction, actual result, one tested revision and why the
check protects the behavior you expected. Explain accepted code in your own words.

## 6. Python → package → Trail

Local Python models, transforms, checks or generates data on your computer.
Validated declarative YAML is the world artifact. Trail owns actual session
interaction state; it never imports or executes student Python. New launches
start fresh. A story continuation does not imply a saved game.

Use [Trail checkpoints](trail-checkpoints.md) for the polished world rehearsal and the exact meaning of mission completion.

## 7. Your explanation

Explain defensive validation and ordered diagnostics with one concrete value from your work. Show what the
check caught, what changed, and what stayed the same. Use the task card’s bounded
AI receipt and teacher-managed Git close; understanding comes before a rushed commit.
