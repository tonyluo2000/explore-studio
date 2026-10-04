# Computer Readiness

> **Status:** Canonical minimum hardware, supported devices, and the
> student-facing computer check for the S01–S30 course.

This page is written to be read by a student, a parent, or a teacher. It is
included in the student ZIP distribution so families can confirm a computer
before the first session.

## Minimum hardware

| Requirement | Minimum | Why it matters |
|---|---|---|
| Memory (RAM) | **8 GB** | The editor, terminal, Classroom Trail window, and a video class run at the same time. |
| Free storage | **5 GB** | Python, the course tools, and the course folder must all fit with room to work. |
| Keyboard | **Physical keyboard** | Every session types code and uses WASD/arrows and the E key. |
| Internet | **Stable connection** | Needed once for setup, and for the live class. Lessons run locally afterward. |
| Microphone | **Required** | Students explain predictions and evidence out loud in every session. |
| Webcam | Recommended | Helpful for class participation; not required to complete a session. |
| Headphones | Recommended | Reduces echo and makes the live class easier to follow. |

## Supported computers

- **macOS** — supported directly.
- **Windows** — supported through **WSL 2 with Ubuntu and WSLg**, not native
  PowerShell Python. Deterministic export needs POSIX filesystem confinement
  and Classroom Trail needs Linux GUI-app support. Keep the course folder at
  `~/explore-studio-course` in the Ubuntu home directory, not under `/mnt/c`.
  Step-by-step setup: [`Windows Setup`](windows-wsl-setup.md).
- **Linux** — works with a normal desktop session.

Python **3.11 or newer** is required on every supported computer.

## Not supported as a primary coding device

A **phone, tablet, or Chromebook is not a supported primary coding device for
this cohort.** These devices cannot run the course's local Python environment,
the `explore-package` command line, and the Classroom Trail window the way every
session requires. A tablet or phone may be used as a second screen for the video
call, but the student still needs a supported Mac, Windows-with-WSL, or Linux
computer with a physical keyboard to do the work.

If a supported computer is not available, contact the teacher before the first
session rather than at the start of S01.

## Run the computer check

The check has two modes.

**Before the course is installed**, a family can test the computer itself with
the standalone `check-my-computer.py` from the course website:

```console
python3 check-my-computer.py --computer-only
```

It checks the operating system, Python 3.11 or newer, memory, storage, the
screen, the internet for the one-time install, and on Ubuntu the `python3-venv`
and `unzip` packages. It ends with `COMPUTER CHECK PASSED` or
`SETUP HELP NEEDED`, and never with READY, because the course is not set up yet.

**After the course tools are installed**, and at the start of every class, run
the full check from the Course Kit with its `.venv` active:

```console
cd ~/explore-studio-course
source .venv/bin/activate
python3 check-my-computer.py
```

It reports each item, then a short summary a teacher can read at a glance, then
exactly one result line:

```text
Summary
  Python: 3.12.3
  Course folder: OK
  Virtual environment: .venv
  Course tools: abc1234 (current)
  Trail dependency: OK

READY FOR EXPLORE STUDIO
```

`READY FOR EXPLORE STUDIO` appears only when every summary item passes;
otherwise the result is `SETUP HELP NEEDED` and the command exits with status 1.
`SETUP HELP NEEDED` does not mean anything is broken: each line marked `[help]`
has an arrow saying what to do next. Lines marked `[note]` are reminders, such
as confirming the physical keyboard by hand; they never make the result READY
on their own. The full check never uses the network.

### What the full check looks at

| Summary or line | `[help]` when |
|---|---|
| Python | The Python running the check is older than 3.11. |
| Course folder | `WRONG FOLDER`: not run from the Course Kit root. `COURSE FOLDER IN WRONG PLACE`: the Course Kit is not exactly `~/explore-studio-course` (under `/mnt/c`, in Downloads, nested, or anywhere else). |
| Virtual environment | `VENV NOT ACTIVE`: the course `.venv` is not active. `VENV IN WRONG PLACE`: another environment is active (such as `~/.venv`), or this `.venv` was moved or copied from another folder. |
| Course tools | `COURSE TOOLS NOT INSTALLED`, or `COURSE TOOLS OUT OF DATE`: the installed course tools commit (read offline from pip's install record) is not the one this Course Kit pins in `requirements-student.txt`. Both short commits are printed. |
| Trail dependency | `pygame`, which draws the Trail, is not installed. |
| Course Kit version | `course-materials.json` is missing. Otherwise it prints the kit version to compare with the course website's Prepare page. |
| Your world folder | `my-explore-world` is inside the Course Kit, where an update would replace it. |
| Trail window opens and closes | A minimal Trail window cannot open (for example, WSLg is missing). |

On Windows it also needs **WSL 2**; WSL 1 is reported as `[help]`. Fixes for
every line are in [`Windows Setup`](windows-wsl-setup.md).

Useful options:

```console
python3 check-my-computer.py --computer-only --skip-network
python3 check-my-computer.py --workspace ~/explore-studio-course
```

## Privacy boundary

The computer check collects no credentials and no personal data. It never asks
for a password, token, account name, or email address; it reads only local
hardware and environment facts; it prints them on the student's own screen; and
it uploads nothing. Only `--computer-only` opens and closes one connection to
confirm the internet works, and it sends no data. Home-directory paths are shortened
to `~` in the printed report so a shared screen or a pasted result does not
expose a name.

Teachers recording pre-class verification should record only device or image
identifiers and pass/fail results.

## Related pages

- `START-HERE.md`, in the top folder of the course — the four first-day steps.
- [`Windows Setup`](windows-wsl-setup.md) — WSL, Ubuntu, VS Code, and getting
  a newer Course Kit.
- [`Classroom Student Workspace`](classroom-student-workspace.md) — how the ZIP
  and the Git-managed course folder are produced.
