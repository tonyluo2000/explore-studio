# S23 — Builder's Workshop

**Role:** Python-primary software fluency

**World reuse:** M14 `reuse-a-named-toggle-style`

**Learning objective:** Students can design a call/data flow and move a working
local pipeline into bounded data I/O, validation/rules, and build/output modules
while an exact-output regression proves behavior is preserved.

**Prerequisite:** S20 pipeline plus S21–S22 validation/regression habits.

## Before class

- Confirm Quick Start readiness: repo/venv, package command, Trail focus/controls,
  screen sharing, Git identity, and accessible/low-bandwidth route.
- Run the committed exact regression and validate the M14 package.
- Prepare clean starter copies and paste commands in chat.
- Draw three empty responsibility boxes; do not fill student arrows in advance.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: reorganize a busy workshop without changing its products. | Names behavior to preserve. |
| 0:04–0:10 | 5–6 min | Require duplication candidate and call/data-flow design. | Labeled three-module diagram. |
| 0:10–0:28 | 16–18 min | Move one responsibility at a time; rerun exact test each time. | Imports work; output stays exact. |
| 0:28–0:35 | 6–7 min | Validate/play the two-lamp M14 reuse analogy. | Both objects share style behavior. |
| 0:35–0:42 | 6–7 min | Diagnose one import/placement mistake; rerun regression. | Before/after PASS evidence. |
| 0:42–0:45 | 2–3 min | Inspect isolated refactor diff; commit or schedule. | No intended behavior change. |

**Teacher cut line:** At 0:28, stop after two modules and use the support import
for the third. At 0:35, accept validator PASS plus teacher M14 demo. Protect the
diagram and exact before/after regression. Git may finish asynchronously.

## Student task and prediction

Students identify a candidate before teacher/AI confirmation and label parameters
and return values on arrows before moving code.

## Deliberate debugging exercise

Use one missing/wrong import or a function placed in the wrong responsibility.
The unchanged exact-output regression is the oracle; do not “fix” its snapshot.

## Expected output and behavior

`test_refactor.py` passes before and after. Exact serialized documents do not
change. The M14 package validates, and Design Lamp/Build Lamp share one named
blue-to-gold style.

## Bounded AI assistance

Use the canonical workflow. AI may identify duplication only after the student
proposes a candidate. It may not write modules or change expected output.

## Git close

Use status, diff, intentional stage, `git diff --staged`, and an isolated
behavior-preserving refactor commit. Interpret `M`, `??`, no output, identity
failure, and retry. Understanding and exact evidence outrank speed.

## Optional extension

Extract a coordinator without adding classes or changing output.

## Teacher notes and answer key

- `data_io`: `yaml.safe_load`; `rules`: known-shape errors; `build_output`:
  deterministic current-contract documents/rendering.
- Correct flow returns data; modules do not rely on shared mutable globals.
- If snapshot changes, inspect implementation first; do not update expected text.
- M14 is an analogy for reuse, not Python execution in Trail.
