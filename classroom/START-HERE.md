# Start Here

Welcome to Explore Studio. Follow these four steps in order. You do **not** need
a GitHub account, and you do **not** need to install Git to begin.

## 1. Put this folder somewhere you can find it

Unzip the course file and move the folder it creates —
`explore-studio-course` — into one of these places:

- **macOS:** your home folder or your Desktop.
- **Windows (WSL 2 Ubuntu):** the Ubuntu home folder, for example
  `/home/student/explore-studio-course`. Do **not** keep it under `/mnt/c`.

Do not leave it in Downloads, and do not work inside the zipped file itself.

## 2. Check that this computer is ready

Open a terminal, go into the course folder, and run:

```console
cd explore-studio-course
python3 check-my-computer.py
```

Read the last line:

- `READY FOR EXPLORE STUDIO` — continue to step 3.
- `SETUP HELP NEEDED` — show the lines marked `[help]` to a teacher or an adult
  at home before continuing.

The check looks only at this computer. It never asks for a password or an
account and never sends anything anywhere.

## 3. Install the course tools once

```console
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-student.txt
explore-package --help
```

This is the only step that needs the internet. If `explore-package` is not
found, make sure the line above it finished and that your prompt shows
`(.venv)`, then run the install command again. Do not install a package by name
on your own.

Run the computer check once more to test a real Trail window:

```console
python3 check-my-computer.py
```

## 4. Start Session 1

Open [`lessons/sessions/s01/student/task-card.md`](lessons/sessions/s01/student/task-card.md)
and follow it. Keep
[`lessons/sessions/student-quick-start.md`](lessons/sessions/student-quick-start.md)
open beside it for controls, troubleshooting, and the accessibility route.

## What is in this folder

| Path | What it is |
|---|---|
| `check-my-computer.py` | The computer check from step 2. |
| `requirements-student.txt` | The exact course tools pinned for this class. |
| `lessons/sessions/` | Your task cards for Sessions 1–30. |
| `examples/explorer-packages/` | The shared world packages lesson commands use. |
| `docs/computer-readiness.md` | What this computer needs, in plain language. |
| `course-materials.json` | A record of which course version you have. |

There are no teacher runbooks or answer keys in this folder, and nothing here
needs an account or a password.

## Later: saving your work with Git

Git is a tool for saving and comparing versions of your work. It is **not**
needed for Session 1 and it is not part of this folder's setup. Your teacher
will introduce it later, or give you a Git-managed course folder when the class
is ready. Everything in Sessions 1 onward runs without it.
