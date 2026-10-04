# Start Here

Welcome to Explore Studio. Follow these four steps in order. You do **not** need
a GitHub account, and you do **not** need to install Git to begin.

**On Windows?** Use
[`docs/windows-wsl-setup.md`](docs/windows-wsl-setup.md) for steps 1–3. It is
the full step-by-step guide for WSL, Ubuntu, VS Code, and getting a newer
Course Kit. Then come back here for step 4.

## 1. Put this folder in its one place

This folder, `explore-studio-course`, is the **Course Kit**. It must be exactly
`~/explore-studio-course`: directly inside your home folder.

- **Windows:** your Ubuntu home folder in WSL 2, never under `/mnt/c`. Copy and
  unzip it there with the steps in the Windows guide.
- **macOS:** your home folder (in Finder, **Go → Home**).

Not Downloads, not the Desktop, and not inside another folder. Do not work
inside the zipped file itself.

## 2. Install the course tools once

Open a terminal (the **Ubuntu** terminal on Windows) and run:

```console
cd ~/explore-studio-course
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-student.txt
explore-package --help
```

This is the only step that needs the internet. If `explore-package` is not
found, make sure the line above it finished and that your prompt shows
`(.venv)`, then run the install command again. Do not install a package by name
on your own.

The course tools live only in `~/explore-studio-course/.venv`. Do not make a
`.venv` anywhere else: not in your home folder, and not in `my-explore-world`.

## 3. Check that you are ready

```console
cd ~/explore-studio-course
source .venv/bin/activate
python3 check-my-computer.py
```

The check ends with a short summary and one result line:

```text
  Course tools: abc1234 (current)
  Trail dependency: OK

READY FOR EXPLORE STUDIO
```

(Your seven letters and numbers will differ. What matters is `(current)`.)

- `READY FOR EXPLORE STUDIO` — continue to step 4.
- `SETUP HELP NEEDED` — follow the arrow under each line marked `[help]`, or
  show those lines to a teacher or an adult at home.

Run these three lines at the start of every class: they are the
**Am I ready?** check. The check looks only at this computer. It never asks for
a password or an account and never sends anything anywhere.

To edit code, open the Course Kit in VS Code with `code .` from
`~/explore-studio-course`. On Windows, the bottom-left corner of VS Code must
say **WSL**.

## 4. Start Session 1

Open [`lessons/sessions/s01/student/task-card.md`](lessons/sessions/s01/student/task-card.md)
and follow it. Keep
[`lessons/sessions/student-quick-start.md`](lessons/sessions/student-quick-start.md)
open beside it for controls, troubleshooting, and the accessibility route.

## Your two folders

| Folder | What it is | Replace it? |
|---|---|---|
| `~/explore-studio-course` | This Course Kit: lessons and course tools. | **Yes**, with each newer Course Kit. |
| `~/my-explore-world` | Your own work (from Session 2). | **Never.** Never delete it. |

## From Session 2: make your own world folder

This course folder can be replaced with a newer copy during the year. Your own
explorer, companion, journal (`journey.md`), and editable Explorer Packages live
in a separate folder that is yours:

```console
python3 make-my-world.py
```

It creates `~/my-explore-world` next to this folder, seeds your S02 Moon
Compass under `projects/moon-compass/`, and adds `journey.md`, your **My
Explore Journey** journal for short after-class notes. Running it again only
adds missing files; it never replaces your work — an existing `journey.md` is
never touched. Replacing this Course Kit leaves the
Student Workspace untouched. Your task card for Session 2 shows when to do
this.

## Getting a newer Course Kit

When your teacher hands out a newer Course Kit, or the computer check says the
course tools are out of date, follow **Get a newer Course Kit** in
[`docs/windows-wsl-setup.md`](docs/windows-wsl-setup.md#get-a-newer-course-kit).
In short: move this folder aside, unzip the new one to
`~/explore-studio-course`, make a fresh `.venv`, install, and run
`python3 check-my-computer.py`. Never unzip on top of the old folder, and never
touch `~/my-explore-world`.

If the Trail ever looks older than the class slides, or a lesson command fails
only for you, run `python3 check-my-computer.py` first. An out-of-date setup
can look exactly like a bug.

## What is in this folder

| Path | What it is |
|---|---|
| `check-my-computer.py` | The computer check from step 2. |
| `make-my-world.py` | Makes your own `my-explore-world` folder (Session 2). |
| `my-world-template/` | The blank starting files for your world folder. |
| `requirements-student.txt` | The exact course tools pinned for this class. |
| `lessons/sessions/` | Your task cards for Sessions 1–30, plus Python Notes. |
| `examples/explorer-packages/` | The shared world packages lesson commands use. |
| `docs/computer-readiness.md` | What this computer needs, in plain language. |
| `docs/windows-wsl-setup.md` | Windows, WSL, VS Code, and Course Kit updates, step by step. |
| `course-materials.json` | A record of which course version you have. |

There are no teacher runbooks or answer keys in this folder, and nothing here
needs an account or a password.

## Later: saving your work with Git

Git is a tool for saving and comparing versions of your work. It is **not**
needed for Session 1 and it is not part of this folder's setup. Your teacher
will introduce it later, or give you a Git-managed course folder when the class
is ready. Everything in Sessions 1 onward runs without it.
