# S02 — Place Your First Prop

**Canonical mission:** M02 `create-a-classroom-object` — Create Your First Object

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can store names, integer x/y coordinates, and
a color in clearly named variables, explain which values are strings and which
are integers, predict an object's location, and adjust one coordinate after a
local test.

**Prerequisite:** S01 literals and output.

## Python first, world second

S02 is a variables lesson. The explorer/companion share-out, the Moon Compass,
and the Discovery segment exist to give variables, assignment, strings, and
integers something worth describing. When time is short, protect the Python.
Every student should leave able to answer: *What did I learn in Python? What
did my Python let me build? What did I discover about the real world?* See
[Course Identity](../../../docs/course-identity.md) for the course-wide model.

## Expedition context

Nova is the reference explorer and Pixel is Nova's companion: a small,
curious, somewhat cautious robot. The Moon Compass is a **tool**, not a
companion; the Crystal Lantern is a **world object**. Keep the four categories
explicit.

Pixel is a static character package (`examples/explorer-packages/pixel-companion`)
with a greeting. It stays where it was placed. It does not follow Nova,
remember anything between sessions, carry items, or decide anything. Say so if
students ask. Those are future abilities students will program, not features
of today's runtime.

The Moon Compass framing is narrative only: `object_name`/`x`/`y`/`color`
mechanics, the package schema, and M02 completion are unchanged. The session
ends with a light forward reference — next session the same static instrument
gains a clue and a reveal (S03) — without implying any saved or persistent
runtime state.

## Before class

- Send `student/task-card.md` and confirm the shared Quick Start preflight.
- Remind students of the S01 homework: imagine an explorer and a companion.
- Run the Python starter and validate `student/explorer-package`.
- From a copy of the student ZIP, run `python3 make-my-world.py` once, then
  again, and confirm the second run reports `kept` for every file.
- Prepare a shared screen or sketch with left/right and up/down coordinate
  directions. Keep the activity inside the existing declarative fields.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Welcome back. Show Nova and Pixel (slide 1). Today: use Python to start creating your own explorer and companion. | Names Nova as explorer and Pixel as companion. |
| 0:05–0:10 | 4–5 min | Share-out of the S01 homework: explorer name, look, trait; companion name, kind, trait; one future ability. Answer every ability with the line below. | States an explorer, a companion, and one future ability. |
| 0:10–0:15 | 4–5 min | Explorer / Companion / Tool / World object. Classify Nova, Pixel, Moon Compass, Crystal Lantern. Transition: explorers need tools. | Classifies all four correctly. |
| 0:15–0:25 | 9–11 min | Variables, values, assignment, strings, integers. Model `x = 240` as "store the integer 240 under the name x", and contrast `x = "240"`. Students run `python3 make-my-world.py` and replace the `TODO` strings in `explorer.py` and `companion.py`. | Runs both personal files; explains why each value is a string. |
| 0:25–0:34 | 8–10 min | Coordinates and the Moon Compass: personalize the starter, run it, copy values into `compass.yaml`, predict the position, validate, launch M02. | Labels types, predicts a position, shows `valid: ...` and the prop. |
| 0:34–0:39 | 4–6 min | Change one coordinate from evidence and relaunch. Use the quoted-integer bug. | Explains the type fix and one observed movement. |
| 0:39–0:42 | 2–4 min | What We Discovered: coordinates, maps, navigation. Fiction vs fact for the Moon Compass. | Says what coordinates describe and one real-compass fact. |
| 0:42–0:45 | 3–5 min | What We Learned in Python, then the exit check. Git close only for Git-managed classes. | Brief exit-check answers. |

**Teacher response to every future ability:** "Great. It cannot do all of
that yet. As you learn more Python, you'll teach it how." Do not promise a
specific runtime feature.

**Teacher cut line:** At 0:34, stop creative changes. Protect the variables
explanation, one run of the student's own `explorer.py`, one valid package,
one visible placement, and a spoken coordinate prediction. If relaunch takes
too long, demonstrate the predicted adjustment once. Shorten Discovery to its
fiction-vs-fact table before cutting Python. Finish Git asynchronously.

## Student task and prediction

Students work from `student/task-card.md`, including its explicit value mapping,
safe visibility range, supported colors, and troubleshooting steps.

Personal files first (strings), then the Moon Compass (integers). From the
course folder root:

```console
python3 make-my-world.py
python ../my-explore-world/explorer.py
python ../my-explore-world/companion.py
```

Personalize the same `object_name`, `x`, `y`, and `color` in the Python starter
and the declarative object file. Before launching, sketch or say where `(x, y)`
should place the prop — an explorer's first instrument belongs somewhere it
would actually be noticed.

```console
python lessons/sessions/s02/student/starter.py
explore-package validate lessons/sessions/s02/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  examples/explorer-packages/pixel-companion \
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
will move the prop. The Python version of the same bug is in the student's
Python Notes: `x = "240"` then `print(x + 100)` raises `TypeError`.

## What We Discovered (2–3 minutes)

Use `student/discovery.md`. Keep it short and label fiction and fact:

- **In Nova's world:** the Moon Compass is a fictional exploration tool.
- **In our world:** coordinates are numbers that describe position; latitude
  and longitude locate places on Earth; before GPS, navigators used maps,
  compasses, the Sun and stars, and records of speed, direction, and time; a
  magnetic compass lines up with Earth's magnetic field.

Do not turn this into a history lecture. One question is enough: "What do
coordinates describe?"

## What We Learned in Python and exit check

Point to `student/python-notes.md`, then ask a few students each:

- **Python:** What is a variable? Which values today were strings? Which were
  integers? What does changing `x` do?
- **Ownership:** What is your explorer called? Your companion? What trait did
  you choose? What is one future ability you want to program?
- **Discovery:** What do coordinates describe? How is Nova's fictional Moon
  Compass different from a real magnetic compass?

## Expected output and behavior

The sample Python output is:

```text
Moon Compass
240 180
purple
```

Validation reports `valid: moon-compass 0.1.0`. The prop appears at its declared
coordinates. A larger x moves it right. Pixel stands near Nova's start and
greets when the student presses E nearby; it does not move. The local M02 trail
completes after both world objects (Moon Compass and Crystal Lantern) have
been interacted with; greeting Pixel does not count toward `Visited`.

`make-my-world.py` creates `my-explore-world` next to the course folder. On a
second run it reports every existing file as `kept` and changes nothing.

## Bounded AI assistance

Student sequence: explain intent → predict → ask one bounded question → test →
revise → explain accepted code. AI may review variable names only after the
student explains what each stores. It may explain one validation issue; it may
not choose the prop, coordinates, color, the student's explorer or companion,
or add schema fields.

## Git close

**ZIP classes:** Skip this step for classes still on the ZIP distribution that have not started the Git lesson yet; use it once the class has a Git-managed course folder. See [Student Quick Start → Later: Git](../student-quick-start.md#later-git-optional-teacher-managed).

```console
git status --short
git diff
git add lessons/sessions/s02/student
git diff --staged
git commit -m "Place a moon compass prop"
```

`my-explore-world` is outside the course folder, so this commit does not
include it. That is expected; no S02 step requires Git.

## Optional extension

Try one second coordinate adjustment, predicting its direction first. Keep one
object contribution and the existing package schema.

## Teacher notes and answer key

- Variables: a variable is a name that stores a value. `object_name` and
  `color` are strings; `x` and `y` are integers. In the personal files, every
  value is a string.
- Correct YAML: `x: 240`; removing quotes makes the value an integer.
- `x = "240"` stores text; `print(x + 100)` raises
  `TypeError: can only concatenate str (not "int") to str`. With `x = 240` it
  prints `340`.
- Categories: Nova = explorer, Pixel = companion, Moon Compass = tool, Crystal
  Lantern = world object. Pixel is never a tool; the Moon Compass is never a
  companion.
- Discovery answer: coordinates describe position. The Moon Compass is
  fictional; a real magnetic compass responds to Earth's magnetic field and
  points roughly toward magnetic north.
- `starter.py` is disposable practice for today. `my-explore-world` is the
  student's own work; `make-my-world.py` never overwrites it, and a new Course
  Kit never contains it. If a student deletes a personal file by accident,
  rerunning `make-my-world.py` restores only the blank template for that file.
- Accept any explorer, companion, and future ability that fit the class's
  norms. Do not collect them; they stay on the student's computer.
- The "first instrument" framing and placement question are narrative only —
  do not imply the compass is saved, persisted, or carried between sessions.
  S03 introduces its clue-and-reveal behavior as new authored content, not as
  continuity from today's state.
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
