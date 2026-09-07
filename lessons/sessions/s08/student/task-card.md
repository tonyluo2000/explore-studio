# S08 Task Card — Build an If/Else Guardian

**Mission:** M08 `respond-to-object-state` — Make an If/Else Character

**Learning target:** Predict both branches of an `if`/`else`, repair an inverted
condition, and connect one declarative NPC response to one same-package toggle.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict both branches before execution

Do not run `starter.py` yet. Write the response that should result for:

```text
is_on is False → __________________________________
is_on is True  → __________________________________
```

Explain the intended condition in plain language: “If ___, then ___; otherwise
___.”

## Core Python path

1. Run `starter.py` only after both predictions exist.
2. Compare output with the predictions. The condition is deliberately inverted.
3. Repair only the condition; keep the small `if`/`else` structure.
4. Run again. Checkpoint: point to the branch selected by each Boolean value.

## Python → package → world

| Local branch | Declarative response | Visible result |
|---|---|---|
| `is_on` is `False` | `when_off` | Guardian gives the sleeping response |
| `is_on` is `True` | `when_on` | Guardian gives the open response |

The Python function runs locally. The package declares a same-package object ID
and two plain responses; the Trail evaluates its own toggle state.

## Package and world path

1. Personalize both responses without changing `object_id`.
2. Validate and launch:

   ```console
   explore-package validate lessons/sessions/s08/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     lessons/sessions/s08/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "respond-to-object-state" \
     --name "S08 Build an If/Else Guardian"
   ```

3. Speak to the guardian while the switch is off. Toggle once, then speak again.
4. Checkpoint: record both exact responses and M08 completion.

## Debug checkpoint

Explain why `if not is_on` sends `False` to the open response in this starter.
Repair the condition and reconcile prediction versus result.

## Support path

Use two labeled cards, `False` and `True`, and physically move one beneath the
matching branch before editing. Keep the sample package wording.

## Extension path

Rewrite the two guardian responses in a consistent character voice. Do not add
branches, conditions, or package fields.

## AI receipt

Record: intent; both branch predictions; exact bounded question; suggestion
tested; accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may compare
your predictions with observed output but must not generate branch logic.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s08/student
git diff --staged
git commit -m "Connect a guardian to the cloud gate"
```

Use the Quick Start for Git interpretation and recovery. Understanding comes
before a rushed commit.
