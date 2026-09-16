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
  and Classroom Trail needs Linux GUI-app support. Keep the course folder in
  the Ubuntu home directory, not under `/mnt/c`.
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

From inside the course folder:

```console
python3 check-my-computer.py
```

The check runs on the system Python before anything is installed, so it can be
used to decide whether a computer will work at all. It reports each item above
and ends with exactly one of these lines:

```text
READY FOR EXPLORE STUDIO
SETUP HELP NEEDED
```

`SETUP HELP NEEDED` means one line marked `[help]` needs an adult's attention.
It does not mean anything is broken. Lines marked `[note]` are reminders to
confirm something by hand, such as the physical keyboard; they never change the
result on their own.

Run the check a second time after the first-session install. Once the course
tools are present, the check also opens and closes one minimal Trail window so a
graphics or WSLg problem is found before class instead of during it.

Useful options:

```console
python3 check-my-computer.py --workspace /path/to/explore-studio-course
python3 check-my-computer.py --skip-network
```

## Privacy boundary

The computer check collects no credentials and no personal data. It never asks
for a password, token, account name, or email address; it reads only local
hardware and environment facts; it prints them on the student's own screen; and
it uploads nothing. Its single network step opens and closes a connection to
confirm the internet works and sends no data. Home-directory paths are shortened
to `~` in the printed report so a shared screen or a pasted result does not
expose a name.

Teachers recording pre-class verification should record only device or image
identifiers and pass/fail results.

## Related pages

- `START-HERE.md`, in the top folder of the course — the four first-day steps.
- [`Classroom Student Workspace`](classroom-student-workspace.md) — how the ZIP
  and the Git-managed course folder are produced.
