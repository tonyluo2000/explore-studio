# S14 Python Notes — Refactor a Shared Look

## 1. Today’s idea: Named dictionaries, parameters and reuse

Pass one style dictionary into multiple calls. In YAML one toggle style can supply the same two authored colors to distinct objects.

## 2. Predict before running

Predict which objects change when you edit the shared style, and which state each interaction changes.

Write the prediction before opening AI help or running code.

## 3. Run and trace your own work

```console
python lessons/sessions/s14/student/starter.py
```

Use the task card for the complete sequence of commands and lesson cut line.
A runnable scaffold or an initially green support test is not proof that your
student-owned TODOs or project decisions are finished.

## 4. What we debugged

A style reference and inline toggle definition cannot coexist on one object. Validate a focused edit before relaunching.

## 5. Evidence to keep

Inspect both beacon colors and toggle each one. Sharing a look does not couple their Boolean states; M14 checks both objects changed.

Record the original prediction, actual result, one tested revision and why the
check protects the behavior you expected. Explain accepted code in your own words.

## 6. Python → package → Trail

Local Python models, transforms, checks or generates data on your computer.
Validated declarative YAML is the world artifact. Trail owns actual session
interaction state; it never imports or executes student Python. New launches
start fresh. A story continuation does not imply a saved game.

Use [Trail checkpoints](trail-checkpoints.md) for the polished world rehearsal and the exact meaning of mission completion.

## 7. Your explanation

Explain named dictionaries, parameters and reuse with one concrete value from your work. Show what the
check caught, what changed, and what stayed the same. Use the task card’s bounded
AI receipt and teacher-managed Git close; understanding comes before a rushed commit.
