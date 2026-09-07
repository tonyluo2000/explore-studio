# Student Quick Start

Use this page before S01 and keep it open during every session.

## First-day setup checklist

- [ ] Open a terminal in the Explore Studio repository—not Downloads or your
      home folder.
- [ ] Activate the project virtual environment.
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

On Windows PowerShell, use `Get-Location` and `Get-ChildItem`. If you cannot see
those repository files, stop and ask the teacher before running lesson commands.

## Activate Python

macOS or Linux:

```console
source .venv/bin/activate
python --version
explore-package --help
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python --version
explore-package --help
```

The prompt often gains `(.venv)` after activation. If `explore-package` says
“command not found” or “not recognized,” confirm the environment is active and
ask the teacher to check installation. Do not install random packages during
class.

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
