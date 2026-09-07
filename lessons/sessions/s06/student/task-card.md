# S06 Task Card — Build a Themed Collection

**Mission:** M06 `build-an-object-collection` — Build a Curious Collection

**Learning target:** Represent exactly three themed objects as dictionaries in
one list and use one plain `for` loop to print their design inventory.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict and trace before running

Do not run `starter.py` yet. Trace the first loop iteration on paper:

```text
object_record is the record named: __________
object_record["x"] is: __________
the first printed line will be: ______________________________
```

Also circle any duplicate name/coordinate and any missing property you predict
will cause trouble.

## Core Python path

1. Check the first-iteration trace with a teacher or partner.
2. Replace the third record's TODO name. Keep exactly three records and the
   fields `name`, `x`, `y`, and `color` in each.
3. Run `python lessons/sessions/s06/student/starter.py`.
4. Checkpoint: show three inventory lines and explain one dictionary lookup.
5. Do not add a comprehension, nested loop, or second loop.

## Python debugging first

Keep Python debugging separate from YAML debugging:

```console
python lessons/sessions/s06/student/debug.py
```

The deliberately malformed record is missing one property. Predict it, add it,
then print that value. Checkpoint: explain why the original record was
incomplete. Finish this before editing package YAML.

## Transfer table

Python records help plan; validated YAML drives the visible world.

| Python record | Package object file | Visible world object |
|---|---|---|
| `objects[0]` | `objects/sun-seed.yaml` | Sun Seed |
| `objects[1]` | `objects/rain-bell.yaml` | Rain Bell |
| `objects[2]` | `objects/wind-flower.yaml` | Your third themed object |

Copy the intended values yourself. Python never executes from the package.

## Package and world path

1. Edit only one package object file at a time. Keep three distinct names,
   positions, colors, near responses, and interaction responses.
2. Validate YAML only after Python is working:

   ```console
   explore-package validate lessons/sessions/s06/student/explorer-package
   ```

3. Launch M06:

   ```console
   explore-package trail \
     examples/explorer-packages/nova-character \
     lessons/sessions/s06/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "build-an-object-collection" \
     --name "S06 Build a Themed Collection"
   ```

4. Checkpoint: find and interact with all three objects; explain how their order
   or placement tells one environmental story.

## Support path and recovery package

Use `student/recovery-package/` only after recording the error from your own
package. It is a prevalidated, read-only fallback for completing the world
observation. Do not merge its files into a partly edited package.

## Extension path

Strengthen the relationship among the three responses without adding a fourth
object or another loop.

## AI receipt

Record: intent; first-iteration prediction; exact bounded question; suggestion
tested; accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may explain
one loop iteration only after your trace exists.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s06/student
git diff --staged
git commit -m "Build a three-object starlight garden"
```

Use the Quick Start for `M`, `??`, no output, identity recovery, cancellation,
and retry. Understanding takes priority over a rushed commit.
