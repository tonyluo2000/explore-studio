# Student Quick Start

Use this page before S01 and keep it open during every session.

## Your course repository

Work only in the **derived student repository** provided by your teacher. It
starts from the official student template and already contains
`lessons/sessions/s01` through `s30`, the shared example packages, and
`requirements-course.txt`. It does not contain engine source or teacher answer
keys. Do not run lesson commands from a separate Explore Studio platform clone.

The teacher setup procedure is documented in
[`Classroom Student Workspace`](../../docs/classroom-student-workspace.md).

## First-day setup checklist

- [ ] Open a terminal in your derived student repository—not Downloads or your
      home folder.
- [ ] Create a fresh project virtual environment if the teacher has not already
      prepared one.
- [ ] Install the exact course requirements and activate the environment.
- [ ] Confirm Python runs.
- [ ] Confirm `explore-package` is available.
- [ ] Open and close one Classroom Trail window.
- [ ] Test WASD or arrow movement and the E interaction key.
- [ ] Confirm Git knows your name and email.
- [ ] Make the code editor, terminal, and Trail window easy to switch between.
- [ ] If screen sharing, share the needed window and hide private notifications.

## Start in the right place

The repository root is the folder containing `README.md`, `lessons`, and
`pyproject.toml`. In the terminal:

```console
pwd
ls
```

On Windows, run these checks inside the supported WSL 2 Ubuntu shell. If you
cannot see those repository files, stop and ask the teacher before running
lesson commands.

## Install and activate Python

macOS or Linux:

```console
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-course.txt
python --version
explore-package --help
```

Windows students use an Ubuntu shell in **WSL 2 with WSLg**, then run the same
commands above. Keep the repository under the Linux home directory, for example
`/home/student/explorer-course`, not under `/mnt/c`. Native PowerShell Python is
not the supported complete-course path because deterministic export requires
POSIX filesystem operations.

Teachers install and verify WSL before class using the linked guidance in
[`Classroom Student Workspace`](../../docs/classroom-student-workspace.md).

The prompt often gains `(.venv)` after activation. If `explore-package` says
“command not found,” confirm the environment is active and rerun
`python -m pip install -r requirements-course.txt`. If it is still missing,
stop and ask the teacher. Do not install an unpinned package by name.

## Launch, control, stop, and relaunch the Trail

1. Copy the complete Trail command from your session task card.
2. Run it from the repository root.
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
| `No such file` | Repository location and spelling | Use `pwd`/`ls`; return to the repository root. |
| `python` or `explore-package` not found | Virtual environment | Activate `.venv`; ask the teacher if it remains unavailable. |
| YAML validation points to a line | Indentation, spelling, quotes, and value type | Change one reported issue, save, and validate again. Never invent a field. |
| Trail window opens but keys do nothing | Window focus | Click the Trail window, then try WASD/arrows and E. |
| Object or NPC seems missing | Validation and coordinates | Confirm validation passed and compare x/y with the task card's safe range. |
| Old behavior still appears | Unsaved file or old Trail process | Close the window, save, validate, and relaunch. |
| Screen sharing is slow | Video bandwidth | Stop sharing the Trail; report text output and use the accessibility route. |

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

## Git close: read before you commit

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

If Git says your identity is unknown, set it for this repository and retry:

```console
git config user.name "Your Name"
git config user.email "your-school-email@example.com"
git commit -m "Describe your change"
```

Replace both examples with your real class identity. If a command is wrong or
still running, press Control-C once, read the prompt, correct the command, and
retry. Never rush or guess through a Git message: understanding the status and
diff takes priority over finishing the commit during the live session.
