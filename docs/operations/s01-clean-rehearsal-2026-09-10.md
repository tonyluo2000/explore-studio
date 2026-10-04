# S01 Clean Student-Flow Rehearsal — 2026-09-10

> **Result:** Pass on macOS using a fresh student checkout and virtual
> environment. The same test is required on pull requests by the Student
> template integration workflow.

## Rehearsal inputs

- student template repository: `tonyluo2000/student-adventure-template`;
- exact template commit: `22afcc5c6f4f24ffd7e67d8ff70b0f8d49f5ff38`;
- course-material candidate: `codex/pre-class-readiness` on 2026-09-10;
- exact installed Explore Studio platform commit:
  `308bc6c0a2b149e8058f46c8f1beece50b793969`; and
- test host: macOS, Python 3.13.7, isolated temporary checkout and `.venv`.

The platform commit was published and independently resolved from the remote
branch before the rehearsal. The temporary student checkout began at the exact
pinned template tree; it did not reuse this repository's virtual environment or
Python import path.

## Later Course Kit platform pin

On 2026-09-26, the Course Kit platform pin advanced to
`715e6cadc3b797d538e5d988f796987d9e5be586` for the narrow S02 procedural
sprite renderer. Later the same day it advanced to
`107a6cd96ef797dd024ace6cd1f88551e69cdff7` for the S02 Trail visual
composition pass (static M02 backdrop and fuller sprites). On 2026-09-27 it
advanced to `0fdd99c03393d6fdb83466d336b8e891ee7c9e80` for Nova V2 and the
living M02 Moon Meadow (trusted sprite sheets, animation, and effects). On
2026-09-30 it advanced to `6a6c664596cfd6f5b5f7219e227b30495e5d4fc9` for the
S02 art-first pass (illustrated Moon Meadow, Nova V3, and Pixel V3), and
later the same day to `4a36ade89f78b3c2cfdf64cea5eb0d7736e6d6a6` for the S02
visual polish pass (painterly plate, varied props, focal lighting). On
2026-10-03 it advanced to `2e5d5ef3ed95c0e20f1c56cb45322eb3bbafac32` to extend the
polished Moon Meadow to S03 (M03). On 2026-10-04 it advanced to
`cc154e8c7c8c99c6bb2a700fbf82e6ddaab64d6f` for the final Moon Meadow visual-polish pass
(lighting and depth, Nova's face and silhouette, the crescent Compass and its
ground halo, and integrated prompts and dialogue). Later on 2026-10-04 it
advanced to `d8f23818c6bde5692a4b4a914b260d6e8be22777` to bring S04 (M04) into the frozen
Moon Meadow (the trusted Moonlit Guide, its talk cue, and the dialogue-focus
bubble). Later on 2026-10-04 it advanced to
`05843ffd7e257a3120a671b009f45fcae33f7391` for the quiet, optional Moon Meadow audio
(ambience, interaction cues, and the M mute key) in S02-S04 (M02-M04). Later on
2026-10-04 it advanced to `3038cf44dc556a6e878141b8e1fbb6c580095aa4` to bring S01 (M01) into the frozen
Moon Meadow as the silent arrival chapter (Nova, a non-counting Pixel, and the
Crystal Lantern; a Trail without `--mission-id` stays plain); the rehearsal above used the retired
S01 cast. Later on 2026-10-04 it advanced to
`b70c8a9e2defdff383c532fd23c783524fcd7717` to bring S05 (M05) into the frozen Moon
Meadow: the S05 package's Moonlit Guide wears the trusted Guide art, each conversation
line gets the existing dialogue bubble, and the existing talk cue and audio are reused.
The original S01 rehearsal inputs and result above remain an unchanged historical
record.

## Student flow exercised

1. Fetched and detached the exact template commit into a new temporary Git
   repository.
2. Provisioned the student-only overlay with
   `scripts/provision_student_workspace.py`.
3. Confirmed 30 student task cards, no teacher runbooks, no S31 directory, and
   no copied `explore/` or `engine/` source.
4. Created a new virtual environment and installed
   `requirements-course.txt`.
5. Confirmed the installed `explore` module came from that environment and the
   `explore-package` command opened its help.
6. Ran the template test suite and validated the template package.
7. Ran `lessons/sessions/s01/student/starter.py` and received the three expected
   classroom-object lines.
8. Validated the `nova-character`, `forest-guide`, `crystal-lantern`, and
   `river-fountain` example packages.
9. Launched the real S01 `explore-package trail` flow with
   `--mission-id visit-all-classroom-objects` under SDL's headless drivers,
   posted a window-close event, and confirmed a clean zero exit.
10. Exported the template package and confirmed the archive was created.

## Outcome and boundary

The automated rehearsal passed (`1 passed in 16.14s`). It exercises the real
derived student repository, exact dependency installation, console script, S01
starter, example packages, and Trail runtime—not imports from the Explore
Studio working checkout.

This was a synthetic pre-class rehearsal. It used no student credentials or
personal data, and it did not test native Windows. Classroom Windows devices
must complete the separate WSL 2/WSLg device check in
[`classroom-student-workspace.md`](../classroom-student-workspace.md).
