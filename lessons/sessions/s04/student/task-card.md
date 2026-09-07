# S04 Task Card — Introduce a Character

**Mission:** M04 `introduce-your-character` — Give Your Character a Voice

**Learning target:** Define and call `greet(name)`, explain its parameter, and
use a traceback to repair an argument problem.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## The bridge to the world

| Local Python idea | Declarative YAML field | Visible world result |
|---|---|---|
| Personalized `greet(name)` output | `greeting` | NPC speaks one authored greeting |

The function runs locally. YAML contains plain text and drives the Trail.

## Predict before running

Read the first function call and write its exact output. Predict what name a
second call should insert.

## Core path

1. In `starter.py`, replace the TODO value used by the `{place}` f-string
   element with your setting name.
2. Add one second `greet("...")` call with a name you choose.
3. Run Python. Checkpoint: explain function, parameter, and argument using your
   two output lines.
4. Personalize the plain YAML `greeting`, validate, and launch:

   ```console
   explore-package validate lessons/sessions/s04/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     examples/explorer-packages/crystal-lantern \
     lessons/sessions/s04/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "introduce-your-character" \
     --name "S04 Introduce a Character"
   ```

5. Speak to the NPC. Checkpoint: report its exact greeting and M04 result.

## Debug checkpoint

Temporarily replace the second call with `greet()`. Predict the final traceback
line, run it, find the file and line location, then restore a call with one name.

## Support path

Compare your code with this recovery shape, then type only the missing pieces:

```python
place = "Moonlit Trail"
print(f"Welcome to {place}, {name}!")
greet("Sam")
```

Keep these lines inside/after the existing function where they belong. Ask the
teacher to point to the location rather than paste a completed file.

## Extension path

Add a third call and predict its exact output. Do not add another package field.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.**

## Git close

```console
git status --short
git diff
git add lessons/sessions/s04/student
git diff --staged
git commit -m "Give the moonlit guide a greeting"
```

Use the Quick Start for status meanings, identity recovery, cancellation, and
retry. Understanding takes priority over a rushed commit.
