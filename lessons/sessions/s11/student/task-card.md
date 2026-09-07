# S11 Task Card — Require Both Keys

**Mission:** M10 `require-all-switches-on` — Unlock the Secret

**Learning target:** Use Boolean `and` in a two-parameter function and prove
that all conditions must be true before the Twin Star Vault opens.

Use the shared [`Student Quick Start`](../../student-quick-start.md). Confirm the
repository location, activate `.venv`, and check Python and `explore-package`.

## Predict before running

Complete all four rows and explain each one. Do not run the starter yet.

| Sun key | Moon key | Should the vault open? | Why? |
|---|---|---|---|
| False | False | ___ | ___ |
| False | True | ___ | ___ |
| True | False | ___ | ___ |
| True | True | ___ | ___ |

Checkpoint: show the completed four-case truth table to the teacher.

## Core Python path

1. Run `python lessons/sessions/s11/student/starter.py`.
2. Compare every observed result with your predictions; circle one mismatch.
3. Repair `both_keys(first_on, second_on)` with one `and` expression. Do not add
   an `if`/`else`; this lesson combines conditions directly.
4. Rerun and record expected versus observed results for all four cases.

## Python → package → visible world

| Python case | Package data | Visible result |
|---|---|---|
| one or both values False | two toggle IDs, not all on | Vault Keeper fallback response |
| both values True | the same two toggle IDs, both on | Vault Keeper success response |

Python remains local. Validated YAML is the Trail's source of truth.

## Package and world path

1. Personalize the two response messages without changing field names or IDs.
2. Validate, then launch:

   ```console
   explore-package validate lessons/sessions/s11/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     lessons/sessions/s11/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "require-all-switches-on" \
     --name "S11 Require Both Keys"
   ```

3. Focus the Trail window. Use WASD/arrows and E. Speak to the keeper with one
   key off, then with both on. Checkpoint: capture both responses and M10 success.

## Deliberate debugging exercise

The starter ignores the second key. Name the first case where prediction and
output differ, change only the return expression, test, revise, and explain.

## Support path

Say “Sun AND Moon” aloud for each row. Use T/F cards or chat reactions. Keep the
provided package and messages. If the Trail is slow, read validation/output in
chat and use one teacher demonstration.

## Extension path

Create a new vault name and two response lines. Keep the exact two-toggle rule.

## Required evidence/checkpoints

- Four predictions made before execution.
- Flawed and repaired output comparison.
- Valid package plus fallback and both-on world evidence.
- One-sentence explanation: “AND is true only when ___.”

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may inspect
your completed truth table only after your prediction and flag one discrepancy.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s11/student
git diff --staged
git commit -m "Build a two-key star vault"
```

`M` is modified; `??` is untracked; no status output means no uncommitted
changes. No `git diff` output means no unstaged tracked changes. If identity
fails, set repository `user.name`/`user.email`, cancel with Control-C if needed,
and retry. Understanding takes priority over a rushed commit.
