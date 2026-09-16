# Classroom Student Workspace

> **Status:** Canonical S01–S30 classroom distribution and bootstrap model.

## Decision

There are two student distribution paths from one reviewed course source.

**The student ZIP distribution is the primary beginner path.** Students unzip
one folder, run the computer check, install pinned course tools once, and start
S01. No Git client, GitHub account, or clone is involved at any point. This is
the path used for S01 onboarding.

**The Git-derived student repository is the later, advanced path.** It is
unchanged and remains available for classes that have reached the Git lesson.

Both paths carry the same reviewed student material, because the ZIP builder
archives the output of the same canonical provisioner. Hardware minimums,
supported devices, and the computer check are documented in
[`Computer Readiness`](computer-readiness.md).

## Student ZIP distribution (primary)

Build the deterministic student archive from a clean Explore Studio checkout at
the approved course materials revision:

```console
python3 scripts/build_student_zip.py dist/
```

The builder provisions a throwaway template with the canonical overlay,
verifies the staged result, and writes `dist/explore-studio-course.zip`. The
same source commit always produces byte-identical archive bytes: every member
uses a fixed timestamp and mode, and members are written in sorted order. The
command prints the archive's SHA-256 so a class can confirm every student
received the same file.

The archive contains exactly one top-level folder, `explore-studio-course`,
holding:

- `START-HERE.md` — the four first-day steps;
- `check-my-computer.py` — the student-facing readiness check;
- `requirements-student.txt` — the exact course platform pin, fetched over
  plain HTTPS so no Git client is needed;
- `lessons/sessions/` — S01–S30 `student/` subtrees, the session index, and the
  Student Quick Start;
- `examples/explorer-packages/` — the four shared example packages;
- `docs/` — computer readiness, this page, and the S01 rehearsal record;
- `course-materials.json` — the non-secret provenance receipt.

The builder refuses to write an archive that contains `.git`, `.venv`, caches,
compiled Python, generated package metadata, teacher runbooks, answer keys,
`explore/`, `engine/`, `scripts/`, `tests/`, credentials, or key material. It
also excludes `requirements-course.txt`, whose `git+https` pin belongs to the
Git-managed path, so the ZIP offers one unambiguous install command.

Tell students exactly where to unzip it: the home folder or Desktop on macOS,
and the Ubuntu home directory such as `/home/student/explore-studio-course`
under WSL — never `/mnt/c`, and never Downloads.

## Git-derived student repository (advanced, later)

Each student works in one independent Git repository created from the pinned
[`student-adventure-template`](https://github.com/tonyluo2000/student-adventure-template).
Before the repository is given to the student, the teacher provisions the
student-only course overlay from one reviewed Explore Studio checkout.

The derived repository contains:

- the template's student-owned package, tests, and Git history;
- `lessons/sessions/s01` through `s30`, with only each `student/` subtree;
- the shared Student Quick Start and session index;
- the four declarative example packages used by lesson commands;
- an exact course dependency pin and a non-secret provenance receipt.

It does not contain teacher runbooks, answer keys, `explore/`, or `engine/`.
The Explore Studio platform remains an installed dependency. This preserves
independent student ownership while making every lesson path and Git command in
the task cards valid from the student repository root.

## Teacher preflight: clean Mac and Zoom

Complete this on the actual teaching Mac before preparing student repositories:

1. Confirm `python3 --version` reports Python 3.11 or newer. Install it before
   class if the command is unavailable. `git --version` is needed only on the
   teaching computer, to build the ZIP or provision the Git-managed path; no
   student device needs Git for S01.
2. Confirm the Mac can reach GitHub and Python package indexes on the network
   that will be used for setup. The first installation is not offline.
3. Install or update the Zoom desktop client. Join the actual class meeting
   from the teaching Mac and a test participant device; verify microphone,
   speakers or headphones, camera choice, chat, and the planned host/admission
   settings.
4. Share the terminal or Trail window once. Complete any macOS screen sharing
   permission prompt and restart Zoom if requested, then test sharing again.
5. Turn off private notifications and prepare the documented low-bandwidth
   route: pasted commands in chat plus text evidence instead of Trail video.
6. Send the meeting link and passcode through the approved private channel.
   Never place meeting credentials in Git, course files, screenshots, or logs.

No hosted Explore Studio service, student login, API credential, secret, Git
client, or GitHub account is required for S01. Network access to the pinned
archive and the package index is needed only during setup; the starter, package
validation, and Classroom Trail run locally afterward.

## Teacher provisioning

Start with two separate clean checkouts: this repository at the approved course
materials revision and one new repository created from the pinned student
template. From the Explore Studio checkout, run:

```console
python3 scripts/provision_student_workspace.py /absolute/path/to/student-repository
```

The command validates all 30 student material directories and required example
packages before copying. It refuses a target without template markers, a target
that already contains course paths, a target containing platform/engine source,
or a source containing S31 materials. It never overwrites an existing course
overlay.

Review and commit the provisioned files in the student's repository before
delivery. Do not commit `.venv`, generated archives, credentials, or teacher
materials. `course-materials.json` records the exact source revision and the
course platform pin without personal data. Provisioning also ignores generated
Python `*.egg-info/` metadata so the first install does not pollute the
student's Git status.

## Student bootstrap — macOS or Linux

From the derived student repository root:

```console
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-course.txt
explore-package --help
python -m pytest -q
```

Students on the ZIP path install `requirements-student.txt` instead and have no
template test suite to run; everything else is identical.

Do not reuse a virtual environment made before provisioning. If
`explore-package` is missing, stop and rerun the exact requirements command in
the active environment; do not install an unpinned package by name.

## Student bootstrap — Windows through WSL 2

The complete course supports Windows through **WSL 2 with Ubuntu and WSLg**, not
native PowerShell Python. Deterministic export needs POSIX filesystem
confinement, and Classroom Trail needs Linux GUI-app support.

An administrator installs WSL before class using Microsoft's official
[`wsl --install` guidance](https://learn.microsoft.com/windows/wsl/install).
Store the repository under the Linux home directory, such as
`/home/student/explorer-course`, rather than `/mnt/c`; this follows Microsoft's
official [WSL filesystem guidance](https://learn.microsoft.com/windows/wsl/filesystems).
Confirm WSLg can open Linux GUI applications using Microsoft's
[GUI-app prerequisites](https://learn.microsoft.com/windows/wsl/tutorials/gui-apps).

Then use the macOS/Linux bootstrap commands inside the Ubuntu shell. Do not mix
a Windows-created `.venv` with WSL, and do not wait until an export session to
discover that WSLg or the repository location is unsuitable.

## Required pre-class verification

For every classroom device or image:

0. run `python3 check-my-computer.py` and record the final result line;
1. build a fresh student ZIP, or create a derived student repository through the
   provisioning command;
2. create a new virtual environment and install `requirements-course.txt`;
3. confirm the `explore-package` executable exists and opens its help;
4. run the template tests and S01 starter;
5. validate all four S01 example packages;
6. launch and cleanly close the S01 Classroom Trail; and
7. confirm controls, window focus, and screen-sharing choices; confirm Git
   identity only for classes already on the Git-managed path.

Record only device/image identifiers and pass/fail results. Do not record
student credentials or personal data.

The first automated clean-room execution is recorded in the
[S01 clean student-flow rehearsal](operations/s01-clean-rehearsal-2026-09-10.md).

## Ownership and update boundary

Students on the ZIP path own the unzipped folder on their own computer and
commit nothing. Students on the Git path commit only inside their derived
repository. Teachers retain runbooks and answer keys in Explore Studio. A later reviewed course-material update is
reprovisioned into a new clean student repository; this bootstrap deliberately
does not merge or overwrite an active student's work.

The course ends at S30. Provisioning and ZIP building add no S31 material and
change no engine, schema, runtime, Mission, publication, approval, or deployment
behavior.
