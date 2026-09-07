# S10 Task Card — Check the Boundary

**Mission:** M13 `compare-a-counter-to-its-goal` — Check the Power Level

**Learning target:** Define a small `at_goal(count, goal)` function, use a
Boolean return value, and verify three boundary cases with assertions.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Prediction gate: complete before the comparison is revealed

Do not ask AI, open an answer key, or change `return False` yet. For your chosen
goal, record the expected `True` or `False` result and explain why:

```text
goal - 1 → ______ because __________________________________
goal     → ______ because __________________________________
goal + 1 → ______ because __________________________________
```

Show all three predictions to the teacher. The teacher will then reveal the one
comparison to type in `at_goal`.

## Core Python path

1. After the prediction gate, replace placeholder `False` with the revealed
   comparison. Keep the function to one readable return line.
2. Run the three print calls and compare every result with your predictions.
3. Write three assertions—one each for goal - 1, goal, and goal + 1.
4. Run again. Checkpoint: show three matching results, three silent assertions,
   and explain the return value in plain language.

## Deliberate debugging exercise

Temporarily use `count > goal`. Predict which one of your three assertions will
fail, run, read the failure, then restore the revealed comparison. Explain why
the exact-goal case is the boundary.

## Python → package → world

| Local boundary case | Declarative package state | Visible NPC response |
|---|---|---|
| below goal | counter count below `goal` | `when_below_goal` |
| exact goal or above | count at/above the same goal | `when_at_or_above_goal` |

Python remains local. The package contains plain counter and NPC response data;
the validated Trail evaluates the existing fixed comparison.

## Package and world path

1. Personalize only the two NPC responses; keep its `object_id` linked to the
   same-package counter.
2. Validate and launch:

   ```console
   explore-package validate lessons/sessions/s10/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     lessons/sessions/s10/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "compare-a-counter-to-its-goal" \
     --name "S10 Check the Boundary"
   ```

3. Speak to the Weather Reader below goal. Add sparks until the exact goal, then
   speak again. Checkpoint: record both responses and M13 completion.

## Support path

Use a number line marking goal - 1, goal, and goal + 1. After the prediction
gate, ask the teacher to read the comparison aloud one symbol at a time. Keep
the sample goal and messages.

## Extension path

Only after all three predictions and assertions pass, ask AI or a partner to
propose one additional integer edge case. Predict and explain it before adding
one optional assertion. Do not build a truth table.

## Required self-review

- Creative choice: “I chose ___ because ___.”
- Python change: “I changed ___, which made ___.”
- Test run: “I tested ___ and observed ___.”

## AI receipt

Record: intent; three boundary predictions; exact bounded question; suggestion
tested; accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution. Do not ask AI to
generate a truth table or boundary answers before your own reasoning.** AI may
propose one edge case only after the prediction gate is complete.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s10/student
git diff --staged
git commit -m "Check the storm engine boundary"
```

Use the Quick Start for Git interpretation and recovery. Understanding comes
before a rushed commit.
