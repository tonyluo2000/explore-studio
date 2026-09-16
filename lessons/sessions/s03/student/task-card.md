# S03 Task Card — Make the World React

**Mission:** M03 `make-your-object-respond` — Make It Respond

**Learning target:** Construct an f-string message from an object-name variable
and predict which player event reveals each authored response.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Expedition story

Tonight you join the shared Moonlit expedition. The Moon Compass has a secret
it is hiding — **you choose what that secret is**: a lantern, a fork in the
trail, a clearing, or an idea of your own. Your nearby clue should hint at the
secret without giving it away; your interaction line reveals it.

## The bridge to the world

| Local Python value | Declarative YAML field | Visible world result |
|---|---|---|
| `near_message` | `when_near` | Appears when the player approaches |
| `interacted_message` | `when_interacted` | Appears after E is pressed nearby |

YAML drives the runtime. Python helps you compose and inspect the text locally.

## Predict before running

Complete: "Moving near will show ___; pressing E will show ___." With a
partner, read your clue aloud and have them guess the reveal before either of
you presses E.

## Core path

1. Choose your secret — what the Moon Compass's clue is hiding.
2. In `starter.py`, expand `near_message = f"{object_name}"` into a complete
   nearby clue that hints at the secret. Keep `{object_name}` inside the
   f-string.
3. Write your own reveal line for `interacted_message`, then run the file.
4. Checkpoint: point to the braces and explain what value appears there.
5. Copy only the final message text into the matching YAML fields, then run:

   ```console
   explore-package validate lessons/sessions/s03/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     lessons/sessions/s03/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "make-your-object-respond" \
     --name "S03 Make the World React"
   ```

6. Have your partner read the clue and predict the reveal before pressing E.
   Approach without pressing E; record the near response. Press E; record the
   interaction response. Complete the object interaction.
7. Checkpoint: compare your partner's prediction with the actual reveal, and
   compare both observations with your original event prediction.

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
with your own clue. Ask the teacher to identify the field—not write the
message. **Solo or low-bandwidth:** if you have no partner, write your reveal
prediction on paper before pressing E, or ask the teacher to read the clue
aloud and collect predictions verbally.

## Extension path

Write a second, harder clue that foreshadows the same reveal with less detail,
so a partner has to think longer before predicting it correctly.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.**

## Git close

**ZIP path check:** Do this section only if your course folder is Git-managed (the Derived student repository path) or your class has already started the Git lesson. On the ZIP path before that lesson, skip it — see [Student Quick Start → Later: Git](../../student-quick-start.md#later-git-optional-teacher-managed).

```console
git status --short
git diff
git add lessons/sessions/s03/student
git diff --staged
git commit -m "Add object response messages"
```

Use the Quick Start for status meanings and recovery. A correct explanation is
more important than completing the commit during class.
