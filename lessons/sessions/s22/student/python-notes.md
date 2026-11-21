# S22 Python Notes — Traceback Detective

## 1. Today’s idea: Regression assertions and one-change debugging

Observe, form a hypothesis, change one thing, rerun and compare evidence. A silent logic error can run successfully while returning the wrong result.

## 2. Predict before running

Predict the printed clue count and compare it with the three CLUES values.

Write the prediction before opening AI help or running code.

## 3. Run and trace your own work

```console
python lessons/sessions/s22/student/starter.py
```

Use the task card for the complete sequence of commands and lesson cut line.
A runnable scaffold or an initially green support test is not proof that your
student-owned TODOs or project decisions are finished.

## 4. What we debugged

Write the assertion that catches the off-by-one in clue_count, watch it fail, then make the smallest repair. Keep separate KeyError and traceback practice in debug.py.

## 5. Evidence to keep

Retest the local function, then hear the Prism Guardian with the switch OFF and ON. Local Python does not repair runtime state automatically.

Record the original prediction, actual result, one tested revision and why the
check protects the behavior you expected. Explain accepted code in your own words.

## 6. Python → package → Trail

Local Python models, transforms, checks or generates data on your computer.
Validated declarative YAML is the world artifact. Trail owns actual session
interaction state; it never imports or executes student Python. New launches
start fresh. A story continuation does not imply a saved game.

Use [Trail checkpoints](trail-checkpoints.md) for the polished world rehearsal and the exact meaning of mission completion.

## 7. Your explanation

Explain regression assertions and one-change debugging with one concrete value from your work. Show what the
check caught, what changed, and what stayed the same. Use the task card’s bounded
AI receipt and teacher-managed Git close; understanding comes before a rushed commit.
