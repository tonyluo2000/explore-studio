# S02 Task Card — Place Your First Prop

**Mission:** M02 `create-a-classroom-object` — Create Your First Object

**Learning target:** Store a prop's name, integer x/y coordinates, and color in
variables; predict its position; then adjust one coordinate from evidence.

Use the shared [`Student Quick Start`](../../student-quick-start.md) before
beginning.

## The bridge to the world

The YAML object file—not `starter.py`—drives the shared runtime.

| Local Python value | Declarative YAML field | Visible world result |
|---|---|---|
| `object_name` | `name` | Label shown for the prop |
| `x` | `x` | Left/right position; larger moves right |
| `y` | `y` | Up/down position; larger moves down |
| `color` | `color` | Named fill color |

Copy the intended values yourself; Python does not generate or execute the
package. The lesson-safe range is x = 80–800 and y = 100–500. This is a classroom
visibility guide, not a new schema rule. Supported colors are `red`, `orange`,
`yellow`, `green`, `blue`, `purple`, `pink`, `brown`, and `gold`.

## Predict before running

Sketch or describe where `(240, 180)` should appear. Predict what increasing x
by 100 will do before changing anything.

## Core path

1. Personalize `object_name`, `x`, `y`, and `color` in `starter.py`.
2. Run the Python file and explain the type of each value.
3. Put the same values in `explorer-package/objects/compass.yaml`.
4. Validate before launching:

   ```console
   python lessons/sessions/s02/student/starter.py
   explore-package validate lessons/sessions/s02/student/explorer-package
   ```

5. Checkpoint: show `valid: ...` and point to the YAML file that drives runtime.
6. Launch:

   ```console
   explore-package trail \
     examples/explorer-packages/nova-character \
     examples/explorer-packages/crystal-lantern \
     lessons/sessions/s02/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "create-a-classroom-object" \
     --name "S02 Place Your First Prop"
   ```

7. Observe the position, close the Trail, change either x or y once, validate,
   and relaunch. Interact with every world object.
8. Checkpoint: state prediction, coordinate change, and observed movement.

## Debug checkpoint

Explain why `x: "240"` is the wrong type, then repair it without changing the
number. If validation fails, fix only the first reported issue and retry.

## Common S02 failures

- Invalid color: choose one lowercase supported name above.
- YAML indentation: use spaces and align `name`, `x`, `y`, and `color`.
- Off-screen object: return to the lesson-safe range, validate, and relaunch.
- Old position: close the old Trail, save YAML, validate, and relaunch.

## Support path

Keep the sample name/color and change only one coordinate. Ask the teacher to
check indentation before you retype the file.

## Extension path

Make a second evidence-based coordinate adjustment after predicting it.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.**

## Git close

```console
git status --short
git diff
git add lessons/sessions/s02/student
git diff --staged
git commit -m "Place a moon compass prop"
```

Use the Quick Start for `M`, `??`, no-output meanings, cancellation, identity
recovery, and retry. Understanding comes before a rushed commit.
