# S01 — Explorer's Field Notes

**Canonical mission:** M01 `visit-all-classroom-objects` — Explore Every Object

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can use `print(...)`, string literals, and
matching quotation marks to record three observations from a local world.

**Prerequisites:** Basic typing, opening a terminal, and finding a file.
No Git client, GitHub account, or clone is required for this session.

## Expedition context

S01 is the arrival chapter, told with the lightest possible touch: Nova has
just landed at the **Landing Site** in **Moon Meadow** and starts field notes.
This is narrative framing only — M01 completion is unchanged, and the story
stays secondary to Python. Do not steer students toward a specific "worth
investigating" answer or mention the Moon Compass; S02 introduces it
independently, and S01 must stand on its own as simple first-day practice.

Slide 1 is the first impression of the whole course: *Explore Studio — Learn
Python. Explore Worlds. Build Your Own.* It introduces Nova (the reference
explorer) and Pixel (Nova's companion), and promises that over the year each
student will create their own explorer, companion, and interactive world with
Python. It is a promise, not a lesson: S01 teaches only running Python,
`print(...)`, strings, quotation marks, output, and basic debugging. Do not
introduce variables; S02 does. Pixel waits by the landing pad in the S01 Trail
for continuity only: it is a character, it never counts toward `Visited`, and
nothing is required of it. See
[Course Identity](../../../docs/course-identity.md).

## Before class

- Complete the
  [clean-Mac and Zoom preflight](../../../docs/classroom-student-workspace.md#teacher-preflight-clean-mac-and-zoom)
  on the actual teaching computer and network.
- Send students `student/task-card.md` and the shared
  `lessons/sessions/student-quick-start.md` before class.
- Deliver the student ZIP distribution built with
  `python3 scripts/build_student_zip.py` and confirm each student unzipped it to
  a supported location.
- Have every student run `python3 check-my-computer.py` and report the final
  result line. Resolve `SETUP HELP NEEDED` before class, not during S01.
- Complete the first-day setup checklist with every student: course folder root,
  `.venv`, Python, `explore-package`, Trail open/close, controls, window
  switching, and screen-sharing readiness. Git identity is not part of S01.
- Confirm `python lessons/sessions/s01/student/starter.py` runs locally.
- Confirm the three example package directories in the world command below
  validate. Screen-share controls; students run their own local copy.
- Ask students to rename or copy the starter only if that matches the class
  setup. Do not edit engine code or package files in this session.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Open on slide 1 (Nova, Pixel, and the year's promise), then show the local Trail: Nova has just landed in Moon Meadow. Ask, “What would an explorer write down here?” | Names one sensory or story detail. |
| 0:05–0:12 | 6–8 min | Model a string literal and `print`. Before running, ask which visible things should count toward M01 completion. | Predicts that world objects—not Nova or Pixel—fill the visited count. |
| 0:12–0:24 | 11–15 min | Open `student/starter.py`. Students personalize exactly three observations, run the file after each change, then choose one detail worth investigating next. | Three readable printed lines and one self-chosen detail, with no forced answer. |
| 0:24–0:37 | 9–13 min | Launch M01. Coach window focus, WASD/arrows, and E; compare the count with the prediction. | The Crystal Lantern visited and the trail reports completion. |
| 0:37–0:42 | 4–6 min | Give the quoting bug below. Students predict the cause, repair it, and rerun. | Explains that an opening quote needs a matching closing quote. |
| 0:42–0:45 | 3–5 min | Ask for one observation and one test result. Confirm the file is saved. | States which line changed and why, with the saved file as evidence. |

**Teacher cut line:** At 0:37, stop setup troubleshooting. Protect one
successful three-line Python run and an M01 observation through the student's
Trail or the low-bandwidth teacher demonstration. Move the quoting repair after
class if necessary; still require the prediction and the student's explanation
of what changed.

## Student task and prediction

Students follow `student/task-card.md`; paste its long command into chat rather
than asking beginners to retype it.

Run the field notes:

```console
python lessons/sessions/s01/student/starter.py
```

Change the three strings to observations from the world. After the three
lines print, have each student pick one detail worth investigating next — an
open choice, not a graded answer. Before starting the trail, write: “I think
___ things count because ___.” Then run:

```console
explore-package trail \
  examples/explorer-packages/nova-character \
  examples/explorer-packages/pixel-companion \
  examples/explorer-packages/crystal-lantern \
  --player "nova-character:nova" \
  --mission-id "visit-all-classroom-objects" \
  --name "S01 Explorer's Field Notes"
```

Use the local movement controls and interact with each world object.

## Deliberate debugging exercise

Predict the error before running this line, then fix only the quotation marks:

```python
print("The lantern flickers near the pond.')
```

Ask: “Where does Python think the string starts, and where should it end?”

## Expected output and behavior

The starter prints three lines in order. Personalized wording may differ.

The Trail opens on Moon Meadow at the Landing Site: Nova, Pixel beside the
landing pad, the Crystal Lantern's shrine down the path, and an empty circle of
standing stones nearby. Nova and Pixel do not increase `Visited`; pressing E
near Pixel shows its greeting but never changes the count. Interacting with the
Crystal Lantern produces `Visited 1 / 1` and `Trail complete!`. The S01 Trail
is silent.

## Bounded AI assistance

Student sequence: explain intent → predict → ask one bounded question → test →
revise → explain accepted code. A suitable question is, “Why does Python say
this one print line has an unfinished string?” AI may explain the error after
the prediction; it may not write the three observations.

## Close

Students save `starter.py` and keep the course folder in the same location for
the next session. Nothing is uploaded and no student account is used.

Point students to `student/python-notes.md` and set the no-code homework from
the task card: imagine an explorer (name, look, one trait) and a companion
(name, kind, one trait, one thing they eventually want it to do). S02 opens
with a share-out of these.

Git is optional and teacher-managed. It is not an S01 prerequisite and must not
block this session. When the class is ready, introduce the Git close from the
shared Quick Start and, if you use it, hand out the Git-managed course folder
described in
[`Classroom Student Workspace`](../../../docs/classroom-student-workspace.md).

## Optional extension

Add one fourth printed observation that uses single quotes correctly. This does
not add or change a mission.

## Teacher notes and answer key

- The "worth investigating" question is open-ended and ungraded. Do not steer
  students toward a specific detail and do not mention the Moon Compass — S02
  introduces it on its own, and S01 must stand alone as simple field-note
  practice.
- Correct bug: `print("The lantern flickers near the pond.")` (matching
  single quotes are also valid).
- Accept creative sentences if each is one valid string passed to `print`.
- Watch for smart quotes pasted from chat and for students counting Pixel as a
  visited object. Pixel is a companion character; M01 completion counts world
  objects. Talking to Pixel is optional and is not evidence.
- The empty stone circle near the landing site is scenery. If students notice
  it, let it stay a field-note mystery: do not say what belongs there.
- If controls fail, check Trail-window focus before changing code. Close the
  window or use Control-C once before relaunching.
- Success means the student can explain literal, string, `print`, prediction,
  and observed M01 behavior—not that their prose matches the sample.
