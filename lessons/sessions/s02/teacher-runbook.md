# S02 — Place Your First Prop

**Canonical mission:** M02 `create-a-classroom-object` — Create Your First Object

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can store an object's name, integer x/y
coordinates, and color in clearly named variables, predict its location, and
adjust one coordinate after a local test.

**Prerequisite:** S01 literals and output.

## Before class

- Run the Python starter and validate `student/explorer-package`.
- Prepare a shared screen or sketch with left/right and up/down coordinate
  directions. Keep the activity inside the existing declarative fields.

## 45-minute runbook

| Time | Teacher move | Student evidence |
|---:|---|---|
| 0:00–0:05 | Invite students to invent a prop with one story purpose. | States a prop name and purpose. |
| 0:05–0:12 | Introduce variables, strings, integers, and coordinates. Ask for a location prediction before showing the world. | Labels name/color as strings, x/y as integers, and predicts a location. |
| 0:12–0:24 | Students personalize the four variables, run the file, and compare output with the matching YAML values. | Prints a name, coordinate pair, and color; explains each variable. |
| 0:24–0:37 | Students edit only supported object fields, validate, launch M02, find the prop, and interact with all objects. | Valid package and completed object tour. |
| 0:37–0:42 | Students move x once, predict the direction, validate, relaunch, and reconcile the result. Use the type bug below if needed. | One evidence-based coordinate adjustment. |
| 0:42–0:45 | Review the prediction and inspect the diff before committing. | Descriptive commit for the prop. |

## Student task and prediction

Personalize the same `object_name`, `x`, `y`, and `color` in the Python starter
and the declarative object file. Before launching, sketch or say where `(x, y)`
should place the prop.

```console
python lessons/sessions/s02/student/starter.py
explore-package validate lessons/sessions/s02/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  examples/explorer-packages/crystal-lantern \
  lessons/sessions/s02/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "create-a-classroom-object" \
  --name "S02 Place Your First Prop"
```

After observing the prop, change either x or y once and repeat validation and
the trail test. Interact with every world object to complete M02.

## Deliberate debugging exercise

Why does this coordinate have the wrong basic type for the package?

```yaml
x: "240"
```

Repair it without changing the intended number, then predict how increasing x
will move the prop.

## Expected output and behavior

The sample Python output is:

```text
Moon Compass
240 180
purple
```

Validation reports `valid: moon-compass 0.1.0`. The prop appears at its declared
coordinates. A larger x moves it right. The local M02 trail completes after all
world objects have been interacted with.

## Bounded AI assistance

Student sequence: explain intent → predict → ask one bounded question → test →
revise → explain accepted code. AI may review variable names only after the
student explains what each stores. It may explain one validation issue; it may
not choose the prop, coordinates, color, or add schema fields.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s02/student
git commit -m "Place a moon compass prop"
```

## Optional extension

Try one second coordinate adjustment, predicting its direction first. Keep one
object contribution and the existing package schema.

## Teacher notes and answer key

- Correct YAML: `x: 240`; removing quotes makes the value an integer.
- `object_name` and `color` are strings; `x` and `y` are integers.
- Python variables are learning practice. YAML remains the validated source for
  the world contribution; no Python is executed from the package.
- Accept any supported color and in-range coordinates that validate. Ask the
  student to explain differences if Python and YAML no longer match.
