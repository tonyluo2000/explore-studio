# Classroom Preflight

> **Status:** Canonical teacher pre-class readiness flow. Teacher-facing; not
> shipped in the student Course Kit.

Goal: find each student's setup problem **before** lesson time, from a few
lines of text, and never spend the lesson repairing a Windows computer.

The student-side steps are the **Am I ready?** check in
`docs/windows-wsl-setup.md` (shipped in the Course Kit). This page is the
teacher's half.

## Before class (the day before, or 15 minutes before)

Ask every student to run, in **Ubuntu** on Windows or Terminal on a Mac:

```console
cd ~/explore-studio-course
source .venv/bin/activate
python3 check-my-computer.py
```

and to paste or show you the **Summary** block and the result line, for
example:

```text
Summary
  Python: 3.12.3
  Course folder: OK
  Virtual environment: .venv
  Course tools: abc1234 (current)
  Trail dependency: OK

READY FOR EXPLORE STUDIO
```

The pasted text contains no names or account details: home paths print as `~`.

Confirm four things:

1. `Course folder: OK` — they ran it from the Course Kit at
   `~/explore-studio-course`.
2. `Virtual environment: .venv` — the Course Kit's own `.venv` is active.
3. `Course tools: <sha> (current)` — the short commit matches the current
   `requirements-student.txt` pin. You never need to compare 40-character SHAs:
   the check compares them and prints `(current)` or `COURSE TOOLS OUT OF DATE`.
4. `READY FOR EXPLORE STUDIO`.

Also glance at the `Course Kit version` line. It should match the version on
the course website's Prepare page (`/students/prepare/`). An older kit means
the student must follow **Get a newer Course Kit** before class.

Then the student launches one known-safe Trail and closes it. This free-play
command (no `--mission-id`, so the plain Trail) works in every Course Kit:

```console
explore-package trail \
  examples/explorer-packages/nova-character \
  examples/explorer-packages/forest-guide \
  examples/explorer-packages/crystal-lantern \
  examples/explorer-packages/river-fountain \
  --player "nova-character:nova" \
  --name "Preflight"
```

## Reading a failed summary

| Summary says | Meaning | Student fix (all in `docs/windows-wsl-setup.md`) |
|---|---|---|
| `Course folder: WRONG FOLDER` | Ran from the wrong folder, often `~/my-explore-world` | `cd ~/explore-studio-course` and rerun |
| `Course folder: COURSE FOLDER IN WRONG PLACE` | Kit under `/mnt/c`, Downloads, Desktop, or nested | Folders in the wrong place |
| `Virtual environment: VENV NOT ACTIVE` | Forgot to activate, or no `.venv` yet | `source .venv/bin/activate`, or step 5 |
| `Virtual environment: VENV IN WRONG PLACE` | `~/.venv` or another project's environment, or a moved `.venv` | `deactivate`; use only the Course Kit `.venv` |
| `Course tools: COURSE TOOLS NOT INSTALLED` | Install never finished | `python -m pip install -r requirements-student.txt` |
| `Course tools: COURSE TOOLS OUT OF DATE (installed X, needs Y)` | Stale runtime; the Trail will look older than the lesson | `python -m pip install --force-reinstall -r requirements-student.txt`, or a fresh Course Kit |
| `Trail dependency: COURSE TOOLS NOT INSTALLED (pygame missing)` | Graphics library missing | Rerun the install |
| `Python: ... (TOO OLD, needs 3.11+)` | Older Ubuntu (22.04 has 3.10) | Install Ubuntu 24.04 (adult) |

A plain rerun of `pip install -r requirements-student.txt` does **not** fix
`COURSE TOOLS OUT OF DATE`: pip keeps the installed package because its version
number did not change. Use the `--force-reinstall` command or a fresh `.venv`.

If a student's Trail looks materially different from the lesson's slides or
screenshots (for example S03's plain dark Trail with a rectangle Compass), run
this check before debugging their code.

## If a student is not ready when class starts

- **Time-box it.** Give one fix from the table above, at most a couple of
  minutes. Do not spend the lesson repairing WSL, Ubuntu, or Python.
- **Use the teacher-operated fallback.** Share your own Trail window and run the
  lesson commands for that student. The student still owns every decision:
  they make the predictions, choose the values, read and explain the code, and
  reason about each debugging step out loud or in chat. Use the accessibility
  and low-bandwidth route in the Student Quick Start.
- **Fix after class.** Send the student (or family) the matching section of
  `docs/windows-wsl-setup.md` and ask them to send a fresh summary before the
  next class.

Record only device or image identifiers and pass/fail results, never student
credentials or personal data. This flow is manual on purpose: there is no
remote management of student computers.

## Trail sound (S02-S04)

The S02-S04 Moon Meadow Trail plays quiet, optional sound: a soft night
ambience, gentle chimes on interactions, and a short motif on mission
complete. There are no voices, and nothing in a lesson needs sound.

- **Press M** in the Trail window to mute or unmute it. A small
  "Audio: On" / "Audio: Muted" label in the bottom-right corner shows the state.
  Mute before you explain something; the Trail keeps working.
- If Zoom shares your computer's sound when you did not expect it, press M.
- `EXPLORE_STUDIO_AUDIO=muted` starts the Trail muted; `EXPLORE_STUDIO_AUDIO=off`
  never opens audio at all.
- A computer without working audio (common in WSL) simply runs the Trail
  silently. Nothing to fix; every sound has an on-screen twin.
