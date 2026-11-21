# S18 Python Notes — Power Station Scoreboard

## 1. Today’s idea: Aggregation, helpers and empty-input contracts

min and max choose extremes, sum combines counts, and an average divides total by the number of records. State the empty-input result before computing.

## 2. Predict before running

For counts 2, 4, 4 predict minimum 2, maximum 4, total 10, average 10/3, and the maximum tie.

Write the prediction before opening AI help or running code.

## 3. Run and trace your own work

```console
python lessons/sessions/s18/student/starter.py
```

Use the task card for the complete sequence of commands and lesson cut line.
A runnable scaffold or an initially green support test is not proof that your
student-owned TODOs or project decisions are finished.

## 4. What we debugged

The summary uses placeholder zeros; at_goal also has a placeholder. Fix each independently and keep the defined empty-list result None.

## 5. Evidence to keep

Test empty input and goal boundaries. Charge each real core independently; the Station Reader compares only Wind Core, not the local summary or the other cores.

Record the original prediction, actual result, one tested revision and why the
check protects the behavior you expected. Explain accepted code in your own words.

## 6. Python → package → Trail

Local Python models, transforms, checks or generates data on your computer.
Validated declarative YAML is the world artifact. Trail owns actual session
interaction state; it never imports or executes student Python. New launches
start fresh. A story continuation does not imply a saved game.

Use [Trail checkpoints](trail-checkpoints.md) for the polished world rehearsal and the exact meaning of mission completion.

## 7. Your explanation

Explain aggregation, helpers and empty-input contracts with one concrete value from your work. Show what the
check caught, what changed, and what stayed the same. Use the task card’s bounded
AI receipt and teacher-managed Git close; understanding comes before a rushed commit.
