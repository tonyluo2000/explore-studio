# Student Quick Start

Use this page before S01 and keep it open during every session.

You do **not** need a GitHub account, and you do **not** need to install Git to
start S01. Git is introduced later, when the class is ready for it.

## Your course folder

Work only in the course folder your teacher gave you. It contains
`lessons/sessions/s01` through `s30`, the shared example packages, the computer
check, and an exact course dependency pin. It does not contain engine source or
teacher answer keys. Do not run lesson commands from a separate Explore Studio
platform clone.

Your teacher gives you the folder in one of two ways:

- **ZIP distribution (the usual first-day path).** You unzip one file, which
  creates a folder named `explore-studio-course`. Its `START-HERE.md` has the
  four first-day steps. Nothing in this path uses Git or GitHub.
- **Derived student repository (a later, teacher-managed path).** A Git-managed
  course folder with its own history, used once the class starts saving work
  with Git. It installs from `requirements-course.txt` instead.

Both folders contain the same lesson materials, and every task card works the
same way in either one.

Where to keep your folders (the same on every computer):

| Folder | What it is | Replace it? |
|---|---|---|
| `~/explore-studio-course` | The Course Kit, with its course tools in `.venv`. | **Yes**, with each newer Course Kit. |
| `~/my-explore-world` | Your own work, made in Session 2. | **Never.** Never delete it. |

Both sit directly in your home folder. Not Downloads, not the Desktop, not
inside each other, and on Windows never under `/mnt/c`.

**Windows students:** the one step-by-step guide for WSL, Ubuntu, VS Code, and
getting a newer Course Kit is
[`Windows Setup`](../../docs/windows-wsl-setup.md).

The teacher setup procedure is documented in
[`Classroom Student Workspace`](../../docs/classroom-student-workspace.md).

## Am I ready? (start of every class)

```console
cd ~/explore-studio-course
source .venv/bin/activate
python3 check-my-computer.py
```

Read the summary and the last line. `Course tools: ... (current)` and
`READY FOR EXPLORE STUDIO` mean you can continue. `SETUP HELP NEEDED` means you
should follow the arrow under each `[help]` line, or show those lines to a
teacher or an adult at home first. READY appears only when you are in the
Course Kit, its own `.venv` is active, and the course tools match this Course
Kit. The check never asks for a password or an account and sends nothing
anywhere. What this computer needs is listed in
[`Computer Readiness`](../../docs/computer-readiness.md).

## First-day setup checklist

- [ ] Open a terminal in `~/explore-studio-course`—not Downloads, your home
      folder, or `my-explore-world`.
- [ ] Create the `.venv` inside the course folder if the teacher has not
      already prepared one.
- [ ] Install the exact course requirements and activate the environment.
- [ ] Run `python3 check-my-computer.py` and read the summary and result line.
- [ ] Confirm Python runs.
- [ ] Confirm `explore-package` is available.
- [ ] Open and close one Classroom Trail window.
- [ ] Test WASD or arrow movement and the E interaction key.
- [ ] Make the code editor, terminal, and Trail window easy to switch between.
- [ ] If screen sharing, share the needed window and hide private notifications.

Git identity is not part of this checklist. It belongs to the later Git lesson.

## Start in the right place

The course folder root is the folder containing `START-HERE.md`, `lessons`, and
`check-my-computer.py`. In the terminal:

```console
pwd
ls
```

On Windows, run these checks inside the supported WSL 2 Ubuntu shell. If you
cannot see those course files, stop and ask the teacher before running lesson
commands.

## Install and activate Python

macOS or Linux, from the course folder root:

```console
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-student.txt
python --version
explore-package --help
```

If your teacher gave you the Git-managed course folder instead, use
`requirements-course.txt` in place of `requirements-student.txt`. Everything
else on this page is identical.

Windows students use an Ubuntu shell in **WSL 2 with WSLg**, then run the same
commands above from `~/explore-studio-course`, never under `/mnt/c`.
Native PowerShell Python is not the supported complete-course path because
deterministic export requires POSIX filesystem operations. Open the course in
VS Code with `cd ~/explore-studio-course` and `code .`; the bottom-left corner
must say **WSL**. Every step is in [`Windows Setup`](../../docs/windows-wsl-setup.md).

Make the `.venv` only inside the course folder. Each new Course Kit gets a
fresh `.venv`: never reuse one from an older kit, another folder, or Windows.

Teachers install and verify WSL before class using the linked guidance in
[`Classroom Student Workspace`](../../docs/classroom-student-workspace.md).

The prompt often gains `(.venv)` after activation. If `explore-package` says
“command not found,” confirm the environment is active and rerun the install
command. If it is still missing, stop and ask the teacher. Do not install an
unpinned package by name.

Then run `python3 check-my-computer.py`. With the course tools installed, it
confirms they match this Course Kit and opens and closes one small test window.

## Launch, control, stop, and relaunch the Trail

1. Copy the complete Trail command from your session task card.
2. Run it from the course folder root.
3. Click once inside the Trail window so it has keyboard focus.
4. Move with **WASD** or the **arrow keys**.
5. Press **E** near an object or character to interact.
6. Stop by closing the Trail window. If the terminal is still busy, return to
   it and press **Control-C** once.
7. Edit and validate before running the same Trail command again.

If keys do nothing, click the Trail window and try again. Do not hold E down;
press and release it once per interaction.

## Accessibility and low-bandwidth route

Tell the teacher what route helps you participate:

- Use keyboard-only navigation and ask a partner or teacher to describe object
  locations and visible messages.
- Read or paste printed output and validation results in chat instead of
  streaming the Trail window.
- Use object names, coordinates, and text as evidence; color is never the only
  required evidence.
- Ask the teacher to paste long commands in chat and read them in smaller
  chunks.
- If the Trail cannot run smoothly, predict from the package fields, watch one
  teacher demonstration, and explain the expected behavior. Retry locally
  after class without losing the concept evidence.

## Common failures

| What you see | Check first | Safe recovery |
|---|---|---|
| `No such file` | Course folder location and spelling | Use `pwd`/`ls`; return to the course folder root. |
| `python` or `explore-package` not found | Virtual environment | Activate `.venv`; ask the teacher if it remains unavailable. |
| YAML validation points to a line | Indentation, spelling, quotes, and value type | Change one reported issue, save, and validate again. Never invent a field. |
| Trail window opens but keys do nothing | Window focus | Click the Trail window, then try WASD/arrows and E. |
| Object or NPC seems missing | Validation and coordinates | Confirm validation passed and compare x/y with the task card's safe range. |
| Old behavior still appears | Unsaved file or old Trail process | Close the window, save, validate, and relaunch. |
| The Trail looks older than the slides, or a command fails only for you | Out-of-date Course Kit or `.venv` | Run `python3 check-my-computer.py`; if it reports `[help]`, follow [Windows Setup](../../docs/windows-wsl-setup.md#when-the-trail-looks-wrong-check-your-setup-first). |
| Screen sharing is slow | Video bandwidth | Stop sharing the Trail; report text output and use the accessibility route. |
| Setup problems you cannot place | Computer readiness | Run `python3 check-my-computer.py` and show the `[help]` lines to an adult. |

Read the final error line first. Change one thing at a time and retest.

## AI receipt

Use AI only after making your own prediction. Record this evidence in your task
card or class notes:

```text
Intent: I am trying to ...
Prediction: Before testing, I think ...
Exact bounded question: I asked ...
Suggestion tested: I tested ...
Accepted/rejected change: I accepted/rejected ... because ...
Student explanation: The accepted code or data means ...
```

**Do not paste whole files or ask AI for a complete solution.** Ask about one
line, error, or mismatch. Test suggestions locally and keep only changes you can
explain.

Canonical workflow: explain intent → predict → bounded question → test → revise
→ explain accepted code.

## Saving your work

Save every file in your editor before you run it. Your work stays in your course
folder on your own computer; nothing is uploaded and no account is involved.

Keep your course folder in the same place all term so your work is easy to find.

## Later: Git (optional, teacher-managed)

Git is a tool for recording and comparing versions of your work. **It is not
required for S01**, and no session is blocked without it. Your teacher decides
when the class starts using it and will give you a Git-managed course folder at
that point.

When that lesson arrives, this is the close you will use:

```console
git status --short
git diff
git add <the lesson files you changed>
git diff --staged
git commit -m "Describe your change"
```

- `M` means Git sees a modified tracked file.
- `??` means Git sees an untracked file; confirm it belongs to your work before
  adding it.
- No output from `git status --short` means there are no uncommitted changes.
- No output from `git diff` means there are no unstaged tracked changes. After
  `git add`, use `git diff --staged` to see what will be committed.

If Git says your identity is unknown, set it for that folder and retry:

```console
git config user.name "Your Name"
git config user.email "your-school-email@example.com"
git commit -m "Describe your change"
```

Replace both examples with your real class identity. If a command is wrong or
still running, press Control-C once, read the prompt, correct the command, and
retry. Never rush or guess through a Git message: understanding the status and
diff takes priority over finishing the commit during the live session.
