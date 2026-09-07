# S07 Task Card — Create a Two-State Prop

**Mission:** M07 `toggle-an-object-state` — Flip a Magic Switch

**Learning target:** Use `False` and `True` to trace a changing local state and
predict a toggle object's color across repeated interactions.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict before running

Complete this trace before Python or the Trail:

| Observation/interaction | Predicted `is_on` | Predicted color |
|---:|---|---|
| Start | `False` | blue |
| After interaction 1 | ______ | ______ |
| After interaction 2 | ______ | ______ |
| After interaction 3 | ______ | ______ |

## Core Python path

1. Read `starter.py`. Its second observation prints the on color but forgets to
   change `is_on`.
2. Predict both printed lines, run the file, then replace the second `False`
   with the correct Boolean value.
3. Run again. Checkpoint: explain that assignment changes this local example;
   it does not reproduce or control Trail internals.

## Python → package → world

| Local Python | Declarative YAML | Visible result |
|---|---|---|
| `False` / `off_color` | `toggle.off_color` | Starting color |
| `True` / `on_color` | `toggle.on_color` | Color after one interaction |

YAML drives the runtime. The Trail owns its own session state and every toggle
starts off.

## Package and world path

1. Personalize the existing supported, distinct off/on colors and messages.
2. Validate and launch:

   ```console
   explore-package validate lessons/sessions/s07/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     lessons/sessions/s07/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "toggle-an-object-state" \
     --name "S07 Create a Two-State Prop"
   ```

3. Interact three times and record every color. Checkpoint: compare the trace
   with the observed off → on → off → on sequence and M07 completion.

## Debug checkpoint

Misconception: “Printing `on_color` automatically makes `is_on` true.” Explain
why that is false, then identify the assignment that changes the local state.

## Support path

Keep blue/gold and point to one assignment at a time. Use the low-bandwidth
route by reading the trace and watching one teacher toggle demonstration.

## Extension path

Choose a different pair of supported, distinct colors and justify how they fit
the object's story. Do not add a third state.

## AI receipt

Record: intent; state/color prediction; exact bounded question; suggestion
tested; accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may check
your completed trace but must not generate the object.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s07/student
git diff --staged
git commit -m "Create a two-state sky lantern"
```

Use the Quick Start for Git interpretation and recovery. Understanding comes
before a rushed commit.
