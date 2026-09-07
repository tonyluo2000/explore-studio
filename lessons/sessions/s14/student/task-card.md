# S14 Task Card — Refactor a Shared Look

**Mission:** M14 `reuse-a-named-toggle-style` — Share a Switch Style

**Learning target:** Find duplication, then reuse one named style in two Python
object-building calls and two declarative world objects.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict: identify duplication before refactoring

Mark the repeated data and propose a name before opening `starter.py`:

```python
build_switch("North Beacon", 260, 220, {"off_color": "purple", "on_color": "gold"})
build_switch("South Beacon", 500, 380, {"off_color": "purple", "on_color": "gold"})
```

Duplicate candidate: ______. Proposed name: ______. Why shared: ______.

Predict: after one shared style changes, North will ___ and South will ___.

## Core Python path

1. Run `python lessons/sessions/s14/student/starter.py`.
2. Find the duplicated inline style in the second call.
3. Replace only that dictionary with `shared_style` so one style dictionary is
   reused by two calls to `build_switch`.
4. Rerun and explain the Python output. Checkpoint: point to the one definition
   and its two consumers.

## Python → shared style → two world objects

| Python reuse | Package reuse | Visible world result |
|---|---|---|
| one `shared_style` dictionary | one `toggle_styles` entry named `aurora-beacon` | one purple/gold look |
| two calls receive that dictionary | North and South use the same `toggle_style_id` | both beacons change with that look |

Python remains local. Validated YAML v0.2 package data is the Trail's source of
truth.

## Package and world path

1. Locate one style in `manifest.yaml` and its two object references.
2. Validate and launch:

   ```console
   explore-package validate lessons/sessions/s14/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     lessons/sessions/s14/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "reuse-a-named-toggle-style" \
     --name "S14 Refactor a Shared Look"
   ```

3. Focus the window, use WASD/arrows and E, and change both beacons. Checkpoint:
   show both matching state changes and M14 success.

## Deliberate debugging exercise

After a valid check, temporarily add `color: "blue"` beside one
`toggle_style_id`. Predict the validator's complaint, validate, read the
inline/reference conflict, remove `color`, and validate again. Do not keep an
invalid package.

## Support path

Draw one box labeled style with arrows to North and South. Replace only the
fourth argument in the second call. For low bandwidth, provide validation text
and compare the named color labels rather than streaming the Trail.

## Extension path

Choose a different valid pair of contrasting colors or rename the beacons.
Retain exactly one named style referenced twice.

## Required evidence/checkpoints

- Duplication marked and named before refactoring.
- One dictionary reused by two object-building calls.
- Python→style→two-object mapping explanation.
- Conflict seen, restored valid package, and both beacons changed.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may identify
duplication only after you propose a candidate; it may not refactor for you.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s14/student
git diff --staged
git commit -m "Reuse one aurora beacon style"
```

Read `M`, `??`, and no output; inspect the staged diff. If identity fails, set
repository name/email, cancel a stuck command with Control-C, and retry.
Understanding takes priority over a rushed commit.
