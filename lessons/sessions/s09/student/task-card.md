# S09 Task Card — Power Up a Device

**Mission:** M09 `count-object-interactions` — Power It Up

**Learning target:** Update an integer counter in a simple loop, predict the
exact success point, repair an off-by-one mistake, and author one assertion.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict before running

For `goal = 3`, write the count after interactions 1, 2, 3, and 4. Circle the
exact interaction where success should first appear.

## Core Python path

1. Trace the first loop pass: starting count, update, and printed count.
2. Run `python lessons/sessions/s09/student/starter.py`.
3. Add one assertion below the TODO that proves the final count equals the goal.
4. Run again. Checkpoint: show all three updates, the silent passing assertion,
   and your predicted success point.

## Deliberate off-by-one debug

Temporarily change the loop to stop at `goal - 1` interactions:

```python
for interaction_number in range(1, goal):
```

Predict the final count, run, read the assertion failure, then restore
`range(1, goal + 1)`. Explain why `range` stops before its second number.

## Python → package → world

| Local Python | Declarative YAML | Visible result |
|---|---|---|
| `goal = 3` | `counter.goal: 3` | Success first appears on interaction 3 |
| count update | successful E interaction | Visible count increases by one |
| success prediction | `when_goal_reached` | Authored message appears at/after goal |

Python does not control runtime state; validated YAML supplies the bounded goal
and message.

## Package and world path

1. Personalize the device and goal-reached message; keep goal from 2 through 5.
2. Validate and launch:

   ```console
   explore-package validate lessons/sessions/s09/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     lessons/sessions/s09/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "count-object-interactions" \
     --name "S09 Power Up a Device"
   ```

3. Press E once at a time. Record count/message after each interaction.
4. Checkpoint: identify the exact first success interaction and M09 completion.

## Support path

Keep goal 3 and use three paper tally marks. The teacher may point to the
assertion shape `assert left == right` without supplying both sides.

## Extension path

Test one interaction after the goal and explain why success remains visible.
Do not add reset, decrement, or cap behavior.

## AI receipt

Record: intent; exact success-point prediction; exact bounded question;
suggestion tested; accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may propose
one boundary case only after your prediction.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s09/student
git diff --staged
git commit -m "Power the storm engine to its goal"
```

Use the Quick Start for Git interpretation and recovery. Understanding comes
before a rushed commit.
