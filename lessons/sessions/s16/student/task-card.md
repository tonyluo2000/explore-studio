# S16 Task Card — Curator's Atlas

**Role:** Python-primary data fluency

**World payoff:** Reuse M06 `build-an-object-collection`.

**Learning target:** Traverse a list of object dictionaries with key access,
one `for` loop, and `enumerate` to make a numbered catalog.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict before running

Trace the first two iterations of `enumerate(objects, start=1)`:

| Iteration | `number` | record ID | predicted complete line |
|---|---:|---|---|
| first | ___ | ___ | ___ |
| second | ___ | ___ | ___ |

Checkpoint: explain where the number comes from and where the ID comes from.

## Core Python path

1. Run `python lessons/sessions/s16/student/starter.py` after both traces.
2. Compare the first two lines with the prediction.
3. Complete the TODO so every line also reads the record's `zone` key.
4. Keep exactly one plain `for` loop. Do not use comprehensions or nested loops.
5. Run `python lessons/sessions/s16/student/debug.py` and repair its records one
   fault at a time.

## Python records → package objects → visible collection

| Local record | Declarative object | Visible M06 payoff |
|---|---|---|
| `sun-dial` | `objects/sun-dial.yaml` | Gold Dawn exhibit |
| `rain-jar` | `objects/rain-jar.yaml` | Blue Cloud exhibit |
| `moss-map` | `objects/moss-map.yaml` | Green Grove exhibit |

Python remains local. Validated YAML is the shared-runtime source of truth.

## World payoff

```console
explore-package validate lessons/sessions/s16/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s16/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "build-an-object-collection" \
  --name "S16 Curator's Atlas"
```

Focus the Trail window; use WASD/arrows and E. Tour the three objects in catalog
order. Checkpoint: match every visible name/message to its numbered record.

## Test and deliberate debug

Diagnose all three prepared faults: missing key, duplicate ID, incorrect nesting.
For each: predict the diagnostic, change one record, run, and explain the result.

## Support path

Use a printed record with keys highlighted in matching colors, or paste output in
chat. Keep the prepared records and add only `zone`. A teacher Trail demo plus
text evidence is valid on low bandwidth.

## Extension path

Add one flat `category` key and display it. No comprehensions or nested loops.

## Required evidence/checkpoints

- Two iteration traces before execution.
- Numbered catalog with zone.
- Three named/debugged record problems.
- Valid package and three-object M06 tour.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may explain
one iteration only after your trace; it may not write the catalog loop.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s16/student
git diff --staged
git commit -m "Catalog the curator collection"
```

`M` means modified; `??` means untracked; no output means nothing is pending in
that view. Recover Git identity or cancel/correct/retry as described in Quick
Start. Understanding takes priority over a rushed commit.
