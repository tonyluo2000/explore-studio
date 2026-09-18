# S23 — Builder's Workshop

**Role:** Python-primary software fluency

**World reuse:** M14 `reuse-a-named-toggle-style` (the package also carries an
existing `respond_to_toggle` character; M14 remains the mission)

**Learning objective:** Students can design a call/data flow and move a working
local pipeline into bounded data I/O, validation/rules, and build/output modules
while an exact-output regression proves behavior is preserved, then use that
pipeline to author one package in which a shared toggle style and a
toggle-reading keeper depend on each other.

**Student-owned action:** The student fills in `my-system.yaml` — object names,
style colours, keeper name and colour, **which lamp the keeper watches**, and
both keeper lines — and makes the composition tests pass.

**Prerequisite:** S20 pipeline plus S21–S22 validation/regression habits.

**Arc note:** Third session of the **S21–S24 Build Quality / Systems Practice**
mini-arc. This is the rehearsal for S25: the first time students combine two
mechanics they already know into one thing that behaves like a system. Both
mechanics are existing declarative contracts — `toggle_styles` reuse and
`respond_to_toggle` — so nothing about the engine, schema, or missions changes.

## Before class

- Confirm Quick Start readiness: repo/venv, package command, Trail focus/controls,
  screen sharing, Git identity, and accessible/low-bandwidth route.
- Run the committed exact regression and validate the M14 package.
- Prepare clean starter copies and paste commands in chat.
- Draw three empty responsibility boxes; do not fill student arrows in advance.
- Confirm `my-system.yaml` still ships with every `CHOOSE-ME` in place, and keep
  a clean copy for machines shared between learners.
- Expect a red bar at the start: three `my_system` tests in `test_refactor.py`
  fail until the student authors their system (2 passed, 3 failed). Say so
  before anyone runs them.
  `test_pipeline_output_matches_exact_snapshot` passes from minute one and is
  the only one that must never go red.
- Have one worked composition of your own ready to show *only* at the cut line,
  and never before students choose their own watched lamp.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: reorganize a busy workshop without changing its products. | Names behavior to preserve. |
| 0:04–0:10 | 5–6 min | Require duplication candidate and call/data-flow design. | Labeled three-module diagram. |
| 0:10–0:28 | 16–18 min | Move one responsibility at a time (rerun the exact test each time), then have students fill `my-system.yaml`. | Imports work, output stays exact, no `CHOOSE-ME` left, composition tests pass. |
| 0:28–0:35 | 6–7 min | Validate and play: keeper line before toggling, then after. | Two different keeper lines; both lamps changed. |
| 0:35–0:42 | 6–7 min | Diagnose one import/placement mistake; rerun both regressions. | Before/after PASS evidence. |
| 0:42–0:45 | 2–3 min | Inspect isolated refactor diff; commit or schedule. | No intended behavior change. |

**Teacher cut line:** This session carries a refactor *and* a composition, so cut
the refactor first — it is the part students have already rehearsed in S20.

- At 0:20, stop the refactor wherever it is and move everyone to the
  composition. Two moved modules is a complete session; use the support import
  for the third or leave it for homework.
- At 0:26, if a student is still choosing, supply one colour and one object name
  so the watched lamp and both keeper lines stay theirs.
- At 0:35, accept validator PASS plus a teacher M14 demo rather than every
  student launching Trail.

Protect, in this order: the call/data-flow diagram, one exact before/after
regression, and the student's own composition with its watched lamp. The
composition is this session's ownership evidence and is cut last. Git may finish
asynchronously.

## Student task and prediction

Students identify a candidate before teacher/AI confirmation and label parameters
and return values on arrows before moving code.

## Deliberate debugging exercise

Use one missing/wrong import or a function placed in the wrong responsibility.
The unchanged exact-output regression is the oracle; do not “fix” its snapshot.

A second, cheaper case for the composition: point a keeper at a lamp ID that the
plan does not contain and predict which layer complains. `validate_data` rejects
it locally with `keeper must watch one of this plan's objects`; if the same
mistake reached a real package, `explore-package validate` would say the
`object_id` `must resolve exactly once within this package`. Two layers, one
rule — that is what makes it a system rather than two parts.

## Expected output and behavior

Observable evidence for this session:

- `test_refactor.py`'s exact snapshot test passes before the refactor, after
  every module move, and at the end. The serialized documents for
  `workshop-plan.yaml` never change.
- `my-system.yaml` contains no `CHOOSE-ME`, and `compose_text()` raises a clear
  `ValueError` until that is true.
- The composition tests pass: exactly one style shared by both lamps, exactly
  one keeper, its `object_id` naming a lamp in the student's own plan, and two
  distinct keeper lines that differ from the teacher's.
- The M14 package validates. Design Lamp and Build Lamp share one named
  blue-to-gold style, and the Workshop Keeper says a different line before and
  after Design Lamp is toggled.
- The student can say, in one sentence, what a player must do before their
  keeper's line changes.

## Likely failure modes and recovery

| Failure mode | What you will see | Recovery |
|---|---|---|
| Student edits `expected-output.txt` to make the refactor pass | Green tests, silently changed behavior | Revert the snapshot; the snapshot is the oracle, never the fix |
| Keeper watches an ID that is not in the plan | `keeper must watch one of this plan's objects` | Compare the `watches` value with the two object `id`s, not their names |
| Both keeper lines say the same thing | `keeper off and on lines must differ` | The point of the mechanic is a visible difference; rewrite one line |
| Student keeps the teacher's keeper lines | `test_my_system_choices_are_my_own` fails | Their system needs their words; supply a colour instead if they are stuck |
| Placeholder left in one field | `my-system.yaml still contains CHOOSE-ME` | Search the file for `CHOOSE-ME`; the message names the whole file, not the field |
| Two mechanics side by side, not connected | Tests pass but the student cannot answer the checkpoint question | Ask what the player does before the keeper changes; if nothing, the keeper is not reading a lamp |

## Bounded AI assistance

Use the canonical workflow. AI may identify duplication only after the student
proposes a candidate. It may not write modules or change expected output.

## Git close

**ZIP classes:** Skip this step for classes still on the ZIP distribution that have not started the Git lesson yet; use it once the class has a Git-managed course folder. See [Student Quick Start → Later: Git](../student-quick-start.md#later-git-optional-teacher-managed).

Use status, diff, intentional stage, `git diff --staged`, and an isolated
behavior-preserving refactor commit. Interpret `M`, `??`, no output, identity
failure, and retry. Understanding and exact evidence outrank speed.

## Optional extension

Extract a coordinator without adding classes or changing output.

## Teacher notes and answer key

- `data_io`: `yaml.safe_load`; `rules`: known-shape errors *including* the two
  keeper rules; `build_output`: deterministic current-contract documents and
  rendering for both the lamps and the keeper.
- Correct flow returns data; modules do not rely on shared mutable globals.
- If snapshot changes, inspect implementation first; do not update expected text.
- M14 is an analogy for reuse, not Python execution in Trail.
- The composition uses only existing v0.1 contribution fields: `toggle_styles`
  with `toggle_style_id`, and a character `respond_to_toggle`. No new field,
  mission, completion rule, or cross-package reference is introduced.
- The mission stays M14 (`ALL_TOGGLE_OBJECTS_CHANGED`). The keeper is visible
  behavior that makes the system legible; it is not a new completion condition.
