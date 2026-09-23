# S02 — Place Your First Prop

**Canonical mission:** M02 `create-a-classroom-object` — Create Your First Object

**Audience and format:** Ages 9–13, three students online, 45 minutes

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

**The scene and its destination.** Show `student/trail-map.svg` (or the S02
slide map) instead of describing the scene aloud. It is drawn to the real
960 × 640 Trail: Nova starts in the middle with Pixel beside Nova; step 1 is the
Moon Compass, the one thing the student places; step 2 is the Crystal
Lantern, already in the world in the bottom-left corner, which is the trail's
destination. Visiting both world objects in any order completes M02, exactly
as before. In the runtime every thing is a plain colored box and no names are
drawn; the map's symbols and labels are map-only.

**Four sentences carry the lesson.** Say them; do not add narration:

1. "We describe our Explorer with Python." (`explorer.py`)
2. "We describe our Companion with Python." (`companion.py`)
3. "Coordinates decide where things live." (`x`, `y` in `compass.yaml`)
4. "Then we use those ideas in our world." (validate, launch, walk the trail)

**What each student value does today.** `explorer.py` and `companion.py` show
the student's Explorer and Companion values. A newly bootstrapped workspace
prints them as an Explorer Card and a Companion Card; a workspace bootstrapped
before this update prints the earlier simple lines instead — both are correct
S02 evidence. Those values are display-only: they appear in the student's own
output and do not change the Trail. `future_ability` is a plan only. In the
Moon Compass file, `x`, `y`, and `color` change the Trail; `name` is stored
but not drawn. Students walk as Nova, the class example, because S02 has no
student-owned character package.

The Moon Compass framing is narrative only: `object_name`/`x`/`y`/`color`
mechanics, the package schema, and M02 completion are unchanged. The session
ends with a light forward reference — next session the same static instrument
gains a clue and a reveal (S03) — without implying any saved or persistent
runtime state.

## Before class

- Send `student/task-card.md` and confirm the shared Quick Start preflight.
- Remind students of the S01 homework: imagine an explorer and a companion.
- Run the Python starter. From a copy of the student ZIP, run
  `python3 make-my-world.py`, validate
  `../my-explore-world/projects/moon-compass`, run bootstrap again, and confirm
  the second run reports `kept` for every file.
- Keep one already-bootstrapped Student Workspace and the Python starter open
  for the documented setup fallback. Do not spend the protected Python block
  diagnosing one student's computer.
- Prepare a shared screen or sketch with left/right and up/down coordinate
  directions. Keep the activity inside the existing declarative fields.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 4 min | Hook, then one sentence per student: one Explorer or Companion choice. Classify Nova, Pixel, Moon Compass, and Crystal Lantern quickly by pointing at the trail map. Cut extra sharing first. | Gives one ownership choice and names at least one category. |
| 0:04–0:15 | 11 min | **Protected Python teaching:** variables, values, assignment, strings, integers, and coordinates. Model `x = 240` as "store the integer 240 under the name x"; contrast `x = "240"`; have all three students predict and change a value in `starter.py`. | Runs Python, labels a string and integer, and predicts what a coordinate change means. |
| 0:15–0:18 | 3 min | **Hard-boxed bootstrap:** guide `python3 make-my-world.py` once. At 0:18, use the fallback below for anyone not ready; do not take time back from Python practice. | Has a Student Workspace, or moves to the fallback without waiting. |
| 0:18–0:27 | 9 min | Students replace every ownership `TODO` in `explorer.py` and `companion.py` — or, for a student who already personalized these files in an earlier class, check their existing values — then run both and confirm their own values appear. Prompt for Explorer name/appearance/personality/interest and Companion name/kind/personality/specialty/future ability. | Runs both files and shows their own concrete personal choices (as a Card in a new workspace, or as printed lines in an older one); explains that the output does not change the Trail and future ability is planning text only. |
| 0:27–0:35 | 8 min | Edit the **student-owned** `projects/moon-compass/objects/compass.yaml`, predict the spot on the trail map, validate `../my-explore-world/projects/moon-compass`, and launch M02 with that package. | Shows the Student Workspace path, a coordinate prediction, `valid: ...`, and the prop. |
| 0:35–0:40 | 5 min | Change one coordinate from evidence, relaunch, use the quoted-integer bug, and complete M02. | Explains the type fix, observed movement, and mission completion. |
| 0:40–0:43 | 3 min | **Discovery only if time remains:** coordinates, maps, navigation; fiction vs fact for the Moon Compass. | Says what coordinates describe and one real-compass fact. |
| 0:43–0:45 | 2 min | Exit share and S03 preview. Git close is asynchronous and only for Git-managed classes. | Gives one Python answer and one ownership or movement answer. |

**Teacher response to every future ability:** "Great. It cannot do all of
that yet. As you learn more Python, you'll teach it how." Do not promise a
specific runtime feature.

**Teacher cut line — setup fallback and cut order:** Bootstrap stops at 0:18 whether or not every
device is ready. A student with setup trouble continues the Python lesson in
`lessons/sessions/s02/student/starter.py`; for the package step, they direct
the teacher's prepared Student Workspace on the shared screen and make the
prediction aloud. Finish their local bootstrap after class. Never consume the
0:04–0:15 teaching block or the 0:18–0:27 Python practice block with setup
troubleshooting.

Cut in this order: Discovery first; then extra discussion, second coordinate
changes, and extra customization; never the core Python explanation/practice.
The opening share-out is one sentence each and categories are a quick check,
not a discussion. Protect one Python run, both personal-file runs when setup
works, one valid student-owned package, one visible placement, and a spoken
prediction. Finish Git asynchronously.

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
and the student-owned declarative object file at
`../my-explore-world/projects/moon-compass/objects/compass.yaml`. Before
launching, sketch or say where `(x, y)` should place the prop — an explorer's
first instrument belongs somewhere it would actually be noticed.

```console
python lessons/sessions/s02/student/starter.py
explore-package validate ../my-explore-world/projects/moon-compass
explore-package trail \
  examples/explorer-packages/nova-character \
  examples/explorer-packages/pixel-companion \
  examples/explorer-packages/crystal-lantern \
  ../my-explore-world/projects/moon-compass \
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
- **Ownership:** Name the Explorer's appearance, personality, and interest or
  favorite subject. Name the Companion's kind, personality, specialty or
  interest, and future ability. Why is that ability only a plan today?
- **Discovery:** What do coordinates describe? How is Nova's fictional Moon
  Compass different from a real magnetic compass?

## Expected output and behavior

Running `explorer.py` and `companion.py` shows two outputs filled with the
student's own values (placeholders print `TODO`). A newly bootstrapped
workspace prints an Explorer Card and a Companion Card; a workspace
bootstrapped before this update prints the earlier simple lines instead —
both are correct. Ask each student to run both files and show that their own
Explorer and Companion choices appear in the terminal; the format (Card vs.
printed lines) is not something to check. The sample Python output of
`starter.py` is:

```text
Moon Compass
240 180
purple
```

Validation reports `valid: moon-compass 0.1.0`. The prop appears as a colored
box at its declared coordinates; its name is not drawn on screen. A larger x moves it right. Pixel stands near Nova's start and
greets when the student presses E nearby; it does not move. The local M02 trail
completes after both world objects (Moon Compass and Crystal Lantern) have
been interacted with; greeting Pixel does not count toward `Visited`.

`make-my-world.py` creates `my-explore-world` next to the course folder and
seeds `projects/moon-compass/`. On a second run it reports every existing file
as `kept` and changes nothing. Replacing the Course Kit cannot touch the
student-owned package.

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
- `starter.py` and the lesson package are disposable Course Kit seeds.
  `my-explore-world` is the student's own work; edit, validate, and launch only
  `projects/moon-compass/`. `make-my-world.py` never overwrites it, and a new
  Course Kit never contains it. If a student deletes one workspace file by
  accident, rerunning bootstrap restores only that missing seed file.
- Accept any complete Explorer and Companion choice set that fits the class's
  norms. Do not collect it; it stays on the student's computer.
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
