# S12 Task Card — Allow Either Key

**Mission:** M11 `open-with-either-switch` — Either Switch Opens It

**Learning target:** Use Boolean `or` so any one active rescue signal can guide
the pilot, then contrast that rule with S11 AND: any condition may be true.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict before running

Complete all four OR cases before execution. Copy the S11 AND result into the
last column and mark each row same/different.

| River signal | Hill signal | OR prediction | S11 AND: same/different? |
|---|---|---|---|
| False | False | ___ | ___ |
| False | True | ___ | ___ |
| True | False | ___ | ___ |
| True | True | ___ | ___ |

Checkpoint: explain why either one-signal case changes from S11.

## Core Python path

1. Run `python lessons/sessions/s12/student/starter.py`.
2. Select one case where copied AND disagrees with your OR prediction.
3. Replace only `and` with `or`; rerun all four cases.
4. Compare S11 and S12 truth tables row by row in one sentence each.

## Python → package → visible world

| Local rule | Declarative state | Visible rescue result |
|---|---|---|
| both False | both toggles off | Pilot reports no signal |
| either value True | first, second, or both toggles on | Pilot sees a safe route |

Python remains local. Validated YAML is the Trail's source of truth.

## Package and world path

1. Personalize signal messages, keeping IDs and response fields valid.
2. Validate and launch:

   ```console
   explore-package validate lessons/sessions/s12/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     lessons/sessions/s12/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "open-with-either-switch" \
     --name "S12 Allow Either Key"
   ```

3. With window focus, use WASD/arrows and E. Show both-off, river-only, and
   hill-only to the pilot. If time permits, test both-on. Checkpoint: M11 success.

## Deliberate debugging exercise

The starter mistakenly uses AND. Choose a one-True case, state expected versus
observed, repair the operator, and explain why the other one-True row also changes.

## Support path

Use two drawn signal lamps and point to any lit lamp. Keep the provided YAML.
For low bandwidth, share the four printed lines and watch one teacher Trail run.

## Extension path

Rename the signals for a sea, mountain, or space rescue. Preserve the OR rule.

## Required evidence/checkpoints

- Four OR predictions before execution and a full S11 comparison.
- One selected mismatch before the repair.
- Correct local output and three required M11 world cases.
- Explanation: “OR is false only when ___.”

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may explain
one mismatch you selected only after you completed both tables.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s12/student
git diff --staged
git commit -m "Guide a rescue with either signal"
```

Interpret `M`, `??`, and no output before staging. Review `git diff --staged`.
Use repository Git identity recovery, Control-C cancellation, and retry guidance
from Quick Start. Understanding takes priority over a rushed commit.
