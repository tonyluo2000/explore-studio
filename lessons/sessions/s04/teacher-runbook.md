# S04 — Introduce a Character

**Canonical mission:** M04 `introduce-your-character` — Give Your Character a Voice

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can define and call `greet(name)`, explain how
the parameter changes its output, and use a traceback to repair an argument
error.

**Prerequisite:** S03 strings and function-call syntax.

## Before class

- Run the Python starter and validate the character package.
- Confirm the trail includes one player, the authored NPC, and at least one
  world object. Keep Python functions separate from declarative NPC content.

## 45-minute runbook

| Time | Teacher move | Student evidence |
|---:|---|---|
| 0:00–0:05 | Ask students to describe a character's voice in three words. | Chooses a voice and greeting idea. |
| 0:05–0:12 | Trace function definition, parameter, and two calls. Require exact output predictions first. | Predicts both lines and identifies each argument. |
| 0:12–0:24 | Students personalize the greeting body and call it with two names. | One reusable `greet(name)` and two working calls. |
| 0:24–0:37 | Students author one declarative character greeting, validate, launch M04, and speak to the NPC. | Greeting appears and M04 completes after all interactable NPCs are spoken to. |
| 0:37–0:42 | Run or inspect the argument bug below. Read the final traceback line together; student repairs it. | Explains missing argument and supplies one name. |
| 0:42–0:45 | Compare predicted and actual output, then inspect the diff and commit. | Descriptive commit. |

## Student task and prediction

Before running Python, write the exact two lines you expect. Personalize the
sentence inside `greet` but keep its single `name` parameter and two calls.

```console
python lessons/sessions/s04/student/starter.py
explore-package validate lessons/sessions/s04/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  examples/explorer-packages/crystal-lantern \
  lessons/sessions/s04/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "introduce-your-character" \
  --name "S04 Introduce a Character"
```

Move to the NPC and interact until its greeting appears. Speak to every
interactable NPC in the selected package set to complete M04.

## Deliberate debugging exercise

Predict the last line of the traceback from this call:

```python
greet()
```

Use the words “function,” “parameter,” and “argument” while explaining the fix.
Then call the function with one student-chosen name.

## Expected output and behavior

The sample output is:

```text
Welcome to the Moonlit Trail, Ari!
Welcome to the Moonlit Trail, Sam!
```

The bad call raises a `TypeError` stating that the required `name` argument is
missing. The package validates. In the Trail, interaction displays
`Moonlit Guide: Welcome to the Moonlit Trail, explorer!` and M04 completes.

## Bounded AI assistance

Student sequence: explain intent → predict → ask one bounded question → test →
revise → explain accepted code. A suitable question is, “What does the final
line of this traceback say is missing?” AI may explain the traceback but must
leave the correction and character wording to the student.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s04/student
git commit -m "Give the moonlit guide a greeting"
```

## Optional extension

Add a third call to the same function with a new name and predict its exact
output. Do not add another character or package field.

## Teacher notes and answer key

- Correct call example: `greet("Kai")`.
- `name` is the parameter in the definition; `"Kai"` is the argument in the
  call. The same function body produces personalized output for each argument.
- The package greeting is declarative text, not a Python function. M04 evaluates
  actual NPC greeting behavior through the existing Trail rule.
- If the NPC cannot be reached, first confirm validation and coordinates; do
  not change engine or Student API code.
