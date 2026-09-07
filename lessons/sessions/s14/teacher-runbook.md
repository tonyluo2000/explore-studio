# S14 — Refactor a Shared Look

**Canonical mission:** M14 `reuse-a-named-toggle-style` — Share a Switch Style

**Audience and format:** Ages 10–14, online, 45 minutes; balanced Python/package

**Learning objective:** Students can identify duplicated dictionary data before
refactoring, pass one named style dictionary to two object-building calls, and
map that reuse to one package style referenced by two world objects.

**Prerequisite:** S04 functions/parameters, S06 dictionaries, S07 toggles, and
shared Quick Start readiness.

## Before class

- Validate the Twin Beacon Style package (`schema_version: "0.2"`).
- Display the duplicated inline dictionary from the task card, not the answer.
- Prepare a two-arrow diagram from one style to two beacons.
- Keep color names paired with text labels for accessibility.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Quick-start check; frame matching aurora beacons. | Identifies a shared visual intention. |
| 0:05–0:12 | 6–8 min | Require students to mark duplicated data before naming a refactor. | Duplicate candidate and reason. |
| 0:12–0:25 | 11–14 min | Inspect the runnable starter; replace the second inline dictionary with `shared_style`; predict both descriptions. | One dictionary passed to two calls. |
| 0:25–0:39 | 12–15 min | Trace Python→named package style→two objects; validate, debug a conflict, restore, launch M14. | Valid provenance and both beacons visibly change. |
| 0:39–0:42 | 3–4 min | Explain reuse and capture checkpoints/AI receipt. | One-change/two-consumers explanation. |
| 0:42–0:45 | 3–5 min | Review status and staged diff; commit or schedule. | Commit or recovery plan. |

**Teacher cut line:** At 0:25, stop optional Python renaming after both calls use
one dictionary. At 0:37, stop repeated launches; validation plus one teacher
world demonstration may supply visual evidence. Git may finish asynchronously.

## Student task and prediction

Students must first highlight the repeated style values in the “before” snippet
and propose a candidate name. Only then may they refactor the second call in
`starter.py` to reuse `shared_style`.

## Deliberate debugging exercise

After a clean package validation, students temporarily add `color: "blue"` to
one object that already has `toggle_style_id`. Validation should report the
inline/reference conflict. They remove the inline color, validate again, and
explain that one object must select exactly one style source.

## Expected output and behavior

Both printed dictionaries contain the same style object values. The package has
exactly one named style, `aurora-beacon`, referenced by two objects. Both toggle
between purple and gold and M14 completes after each changes once.

## Bounded AI assistance

Use explain intent → predict → bounded question → test → revise → explain
accepted code. AI may identify duplication only after the student marks and
names a candidate. It must not rewrite the function or package.

## Git close

Use status/diff/stage/staged diff/commit with shared interpretation, identity
recovery, cancel/retry, and understanding-first guidance.

## Optional extension

Rename the style and choose another valid contrasting color pair. Keep exactly
one style and two references; do not add inheritance or runtime behavior.

## Teacher notes and answer key

- Python answer: pass `shared_style` as the fourth argument in both calls.
- Duplication is the repeated `{"off_color": "purple", "on_color": "gold"}`.
- Mapping: local `shared_style` idea → manifest `toggle_styles` entry → two
  `toggle_style_id` references → two matching visible beacons.
- `toggle_style_id` conflicts with inline `color`, `asset_id`, or `toggle`.
- Named styles are validated declarative data resolved before runtime; M14 adds
  no runtime behavior.
