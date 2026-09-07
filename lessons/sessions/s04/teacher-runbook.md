# S04 — Introduce a Character

**Canonical mission:** M04 `introduce-your-character` — Give Your Character a Voice

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can define and call `greet(name)`, explain how
the parameter changes its output, and use a traceback to repair an argument
error.

**Prerequisite:** S03 strings and function-call syntax.

## Before class

- Send `student/task-card.md` and confirm the shared Quick Start preflight.
- Run the Python starter and validate the character package.
- Confirm the trail includes one player, the authored NPC, and at least one
  world object. Keep Python functions separate from declarative NPC content.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Ask students to describe a character's voice in three words. | Chooses a voice and greeting idea. |
| 0:05–0:12 | 6–8 min | Trace definition, parameter, f-string elements, and the existing call. Require exact output prediction. | Identifies parameter and argument. |
| 0:12–0:24 | 11–15 min | Students replace the setting TODO, add one function call, and use the support shape only if needed. | One reusable `greet(name)` and two working calls. |
| 0:24–0:37 | 9–13 min | Students author plain greeting text in YAML, validate, launch M04, and speak to the NPC. | Greeting appears and M04 completes. |
| 0:37–0:42 | 4–6 min | Students predict `greet()` failure, locate the traceback file/line, repair the argument, and rerun. | Explains the traceback and correction. |
| 0:42–0:45 | 3–5 min | Compare output and inspect status/diffs; commit or schedule it. | Descriptive commit or documented plan. |

**Teacher cut line:** At 0:35, stop voice revisions. Protect two successful
function calls, the parameter/argument explanation, and one observed NPC
greeting. Defer the extension and, if needed, the commit.

## Student task and prediction

Students follow `student/task-card.md`. The starter intentionally leaves the
setting value and second function call for student work.

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

Before student work, output includes the visible placeholder
`TODO: name your setting` and only Ari. After replacing the setting and adding
the second call, the recovery example produces:

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
git diff --staged
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
- Indentation: the two function-body lines must use the same four spaces.
- Misspelled function name: compare the call with the exact `greet` definition.
- Wrong or missing argument: one name string belongs inside the call's
  parentheses; do not add another parameter to hide the error.
- Traceback location: read the final line for the error type, then move upward
  to the first line naming `starter.py` and its line number.
- The task card contains a small recovery shape, not a completed replacement
  file. Use the shared Quick Start for Git and operational recovery.
