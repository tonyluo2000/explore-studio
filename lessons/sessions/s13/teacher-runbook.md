# S13 — Turn the Rule Around

**Canonical mission:** M12 `invert-a-switch-condition` — Turn the Rule Around

**Audience and format:** Ages 10–14, online, 45 minutes; Python-primary, lighter

**Learning objective:** Students can predict both rows of one Boolean input,
return `not is_on`, and explain inversion separately from authored world text.

**Prerequisite:** S08 single-toggle responses and S11–S12 Boolean operators.

## Before class

- Validate the Moonflower Garden package and prepare an ON/OFF card.
- Keep this session intentionally lighter; protect explanation over extra edits.
- Prepare accessibility evidence using text labels, never color alone.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Quick-start check; ask when a moonflower wakes if it prefers darkness. | Plain-language inversion prediction. |
| 0:05–0:11 | 5–7 min | Require both truth-table rows before running. | Two predictions with reasons. |
| 0:11–0:23 | 10–13 min | Run the original-value bug, replace it with `not is_on`, and compare. | Correct return and revised explanation. |
| 0:23–0:37 | 12–15 min | Map OFF/ON to response text; validate, launch M12, show both states. | Both NPC responses and M12 completion. |
| 0:37–0:42 | 4–6 min | Challenge the student's text-versus-syntax explanation; capture evidence. | Answer to one counterexample question. |
| 0:42–0:45 | 3–5 min | Git status/diffs and commit or schedule. | Commit or recovery plan. |

**Teacher cut line:** At 0:23, stop extra Boolean examples. At 0:37, accept
validated fields plus teacher-demonstrated states if Trail friction occurs. Keep
the syntax-versus-text explanation; Git may finish asynchronously.

## Student task and prediction

Students predict False and True inputs before running. The intended function is
exactly `return not is_on`.

## Deliberate debugging exercise

The starter returns the original `is_on` value—the result a double negative
would produce. Students replace it with one `not`, rerun, and repair the mistaken
expectation that two negatives make a stronger inversion.

## Expected output and behavior

Correct rows are `False True` and `True False`. In the world the special
moonflower response appears while the lamp is OFF; the ordinary response appears
while ON. Both states complete M12.

## Bounded AI assistance

Use the canonical workflow. After the student explains the result, AI may ask
one challenging counterexample such as whether renaming messages changes a
number or Boolean. It must not supply the explanation or truth table.

## Git close

Follow task-card status, diff, stage, staged diff, and descriptive commit steps
with shared recovery guidance.

## Optional extension

Invent a different creature active only when one condition is false; do not add
runtime syntax or fields.

## Teacher notes and answer key

- `not False` is True; `not True` is False.
- Answer: `return not is_on`; `not not is_on` returns the original value.
- Swapping `when_off` and `when_on` text can imitate inversion in this narrow
  two-response world case, but YAML text is not general Python `not` syntax. It
  cannot invert arbitrary values or expressions.
- Trail behavior remains the existing fixed one-toggle response model.
