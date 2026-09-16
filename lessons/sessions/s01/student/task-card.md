# S01 Task Card — Explorer's Field Notes

**Mission:** M01 `visit-all-classroom-objects` — Explore Every Object

**Learning target:** Use `print(...)` and string literals to record three world
observations, then repair mismatched quotation marks.

## Get ready

Complete the first-day checklist in the shared
[`Student Quick Start`](../../student-quick-start.md). Be able to show the
course folder root, a `READY FOR EXPLORE STUDIO` result from
`python3 check-my-computer.py`, an active `.venv`, a working
`explore-package --help`, the Trail window, the controls, and your
screen-sharing choice.

You do not need Git or a GitHub account for this session.

## Predict before running

Write: “I think ___ visible things will increase `Visited` because ___.” Decide
whether the player, Fern, the lantern, and the fountain should count.

## Core path

1. Open `lessons/sessions/s01/student/starter.py`.
2. Replace its three strings with your own observations. Keep exactly three
   `print(...)` calls.
3. Run:

   ```console
   python lessons/sessions/s01/student/starter.py
   ```

4. Checkpoint: show three separate printed lines and explain what a string is.
5. Paste this complete command into the terminal from the repository root:

   ```console
   explore-package trail \
     examples/explorer-packages/nova-character \
     examples/explorer-packages/forest-guide \
     examples/explorer-packages/crystal-lantern \
     examples/explorer-packages/river-fountain \
     --player "nova-character:nova" \
     --mission-id "visit-all-classroom-objects" \
     --name "S01 Explorer's Field Notes"
   ```

6. Click the Trail window for focus. Move with WASD/arrows and press E once near
   each world object.
7. Checkpoint: compare the final visited count with your prediction.
8. Close the Trail window. To retry: edit, save, run the same command again.

## Debug checkpoint

Predict the error, then repair only the quotation marks:

```python
print("The lantern flickers near the fountain.')
```

Evidence: explain where Python thinks the string begins and ends.

## Support path

Ask the teacher to paste the Trail command in chat. If streaming is difficult,
report your three printed observations and watch the teacher demonstrate which
objects increase the visited count.

## Extension path

Add a fourth observation using matching single quotes. This does not change the
mission.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.**

## Close

Save `starter.py` and keep your course folder where you can find it next
session. Your work stays on your own computer; nothing is uploaded and no
account is involved.

Understanding what you changed matters more than finishing every path during
class. Be ready to say which line you edited and why.

**Optional, only if your teacher has started the Git lesson:** record this
session with the Git close in the
[`Student Quick Start`](../../student-quick-start.md). S01 is complete without
it.
