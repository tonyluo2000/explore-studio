# S03 Task Card — Make the World React

**Mission:** M03 `make-your-object-respond` — Make It Respond

**Learning target:** Construct an f-string message from an object-name variable
and predict which player event reveals each authored response.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## The bridge to the world

| Local Python value | Declarative YAML field | Visible world result |
|---|---|---|
| `near_message` | `when_near` | Appears when the player approaches |
| `interacted_message` | `when_interacted` | Appears after E is pressed nearby |

YAML drives the runtime. Python helps you compose and inspect the text locally.

## Predict before running

Complete: “Moving near will show ___; pressing E will show ___.”

## Core path

1. In `starter.py`, expand `near_message = f"{object_name}"` into a complete
   nearby clue. Keep `{object_name}` inside the f-string.
2. Write your own interaction line, then run the file.
3. Checkpoint: point to the braces and explain what value appears there.
4. Copy only the final message text into the matching YAML fields, then run:

   ```console
   explore-package validate lessons/sessions/s03/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     lessons/sessions/s03/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "make-your-object-respond" \
     --name "S03 Make the World React"
   ```

5. Approach without pressing E; record the near response. Press E; record the
   interaction response. Complete the object interaction.
6. Checkpoint: compare both observations with your event prediction.

## Deliberate debug workflow

Use **edit → predict → run → restore**:

1. Save your working line somewhere in your notes.
2. Temporarily remove the closing `}` after `object_name`.
3. Predict the error before running Python.
4. Run and read the final error line.
5. Restore the saved working line and rerun successfully.
6. Explain why swapping the two YAML response values would change the story.

## Support path

Start with `near_message = f"The {object_name} glows."`, then replace `glows`
with your own clue. Ask the teacher to identify the field—not write the message.

## Extension path

Make the near response foreshadow the interaction response without revealing
the whole surprise.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.**

## Git close

```console
git status --short
git diff
git add lessons/sessions/s03/student
git diff --staged
git commit -m "Add object response messages"
```

Use the Quick Start for status meanings and recovery. A correct explanation is
more important than completing the commit during class.
