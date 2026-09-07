# S13 Task Card — Turn the Rule Around

**Mission:** M12 `invert-a-switch-condition` — Turn the Rule Around

**Learning target:** Use `not` to invert one Boolean condition and explain why
world response text is not the same thing as Python syntax.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict before running

The moonflower wakes when the sun lamp is not on. Complete both rows first.

| `is_on` | Prediction for `not is_on` | Explanation |
|---|---|---|
| False | ___ | ___ |
| True | ___ | ___ |

Checkpoint: show both rows before running the starter.

## Core Python path

1. Run `python lessons/sessions/s13/student/starter.py`.
2. Compare its unchanged-value output with both predictions.
3. Change the function to exactly `return not is_on`, then rerun.
4. Explain why one `not` inverts and two `not`s return to the starting value.

## Python → package → visible world

| Python idea | Declarative package state | Visible garden result |
|---|---|---|
| `not False` | lamp OFF; authored `when_off` text | Moonflowers open |
| `not True` | lamp ON; authored `when_on` text | Moonflowers curl up |

Swapping authored response text can imitate inversion in this narrow world case,
but it is not general `not` syntax. The YAML has fixed state labels; only local
Python evaluates `not`.

Python remains local. Validated YAML is the Trail's source of truth.

## Package and world path

1. Personalize the two response texts without swapping field names.
2. Validate and launch:

   ```console
   explore-package validate lessons/sessions/s13/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     lessons/sessions/s13/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "invert-a-switch-condition" \
     --name "S13 Turn the Rule Around"
   ```

3. Focus the window; use WASD/arrows and E. Speak to the gardener with the lamp
   OFF, switch it ON, and speak again. Checkpoint: both messages and M12 success.

## Deliberate debugging exercise

Debug the starter's original-value result and the mistaken expectation “two
NOTs invert more.” Record expected versus observed for each row, then explain
the corrected result.

## Support path

Flip an ON/OFF card over once for `not`; flip it twice for `not not`. Keep the
provided package. Low-bandwidth evidence can be the two printed rows and teacher
world demonstration.

## Extension path

Write one new OFF-special and ON-ordinary pair for a nocturnal creature.

## Required evidence/checkpoints

- Both predictions before execution.
- Correct `return not is_on` and two matching rows.
- Both M12 world responses.
- Explanation separating response-text swapping from general `not` syntax.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may challenge
your explanation after you write it; it must not supply the explanation.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s13/student
git diff --staged
git commit -m "Invert the moonflower rule"
```

Interpret `M`, `??`, and no output; inspect the staged diff. Use identity
recovery and Control-C/correct/retry guidance when needed. Understanding takes
priority over a rushed commit.
