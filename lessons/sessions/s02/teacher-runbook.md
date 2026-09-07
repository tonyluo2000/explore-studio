# S02 — Place Your First Prop

**Canonical mission:** M02 `create-a-classroom-object` — Create Your First Object

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can store an object's name, integer x/y
coordinates, and color in clearly named variables, predict its location, and
adjust one coordinate after a local test.

**Prerequisite:** S01 literals and output.

## Before class

- Send `student/task-card.md` and confirm the shared Quick Start preflight.
- Run the Python starter and validate `student/explorer-package`.
- Prepare a shared screen or sketch with left/right and up/down coordinate
  directions. Keep the activity inside the existing declarative fields.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Invite students to invent a prop with one story purpose. | States a prop name and purpose. |
| 0:05–0:12 | 6–8 min | Introduce variables, types, and coordinates; display the Python → YAML → world map from the task card. | Labels types, names the runtime-driving file, and predicts a location. |
| 0:12–0:24 | 11–15 min | Students personalize variables, run Python, and transfer the same values to supported YAML fields. | Prints and explains all four values. |
| 0:24–0:37 | 9–13 min | Students validate, launch M02, observe the prop, then predict and make one coordinate adjustment. | Valid package, visible movement, and completed object tour. |
| 0:37–0:42 | 4–6 min | Use the quoted-integer bug or troubleshoot one observed mismatch. | Explains type and one evidence-based adjustment. |
| 0:42–0:45 | 3–5 min | Review the prediction and inspect status/diffs; commit now or schedule completion. | Descriptive commit or documented commit plan. |

**Teacher cut line:** At 0:34, stop creative changes. Protect one valid package,
one visible placement, and a spoken coordinate prediction. If relaunch takes too
long, demonstrate the predicted adjustment once and finish Git asynchronously.

## Student task and prediction

Students work from `student/task-card.md`, including its explicit value mapping,
safe visibility range, supported colors, and troubleshooting steps.

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
git diff --staged
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
- The task-card range x = 80–800 and y = 100–500 is a lesson visibility guide,
  not a new validator rule.
- For invalid colors, use the supported list. For YAML indentation, align the
  four object fields with spaces. For off-screen coordinates, return to the safe
  range, save, validate, close the old Trail, and relaunch.
- Use the shared Quick Start for Git identity/status recovery. Do not sacrifice
  the student's mapping explanation to force a live commit.
