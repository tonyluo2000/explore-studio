# S20 Task Card — Data-Built Mystery Trail

**Role:** Balanced data-fluency milestone

**World payoff:** Generate, validate, and play M15 `complete-actions-in-order`.

**Learning target:** Explain and test a deterministic local YAML transformation
pipeline from structured input to a current-contract playable package.

Use the shared [`Student Quick Start`](../../student-quick-start.md). Use only the
prepared `starter.py` and `mystery-plan.yaml` scaffolding.

## Predict and trace before running

Trace `sun-compass` through every stage:

| Stage | Prediction/evidence |
|---|---|
| input | keys/value you read: ___ |
| transformation | include decision, priority, new fields: ___ |
| output | file path and contribution position: ___ |
| world | object order/message seen: ___ |

Also predict selected count ___, priority total ___, and final three IDs/order ___ .

Checkpoint: teacher initials the four-stage trace before Python runs.

## Core prepared pipeline

1. Read `starter.py`; locate `yaml.safe_load`. Never use unsafe `yaml.load`.
2. Run `python lessons/sessions/s20/student/starter.py`.
3. Complete `valid_record` for the known prepared shape: ID/name/color text,
   nonnegative integer x/y, integer priority, and Boolean include.
4. Explain the existing search (`selected_records`), aggregate (`priority_total`),
   stable sort (`ordered_records`), and transform (`object_document`).
5. Rerun. It writes only schema v0.1 current-contract files beneath
   `student/explorer-package` with stable ordering.

Do not add package fields, classes, or runtime hooks. Avoid comprehensions and
generators in core work; use readable loops in student edits.

## Input → transformation → output → world

| Pipeline step | Concrete artifact |
|---|---|
| safe local input | `mystery-plan.yaml` |
| validate/search/aggregate/sort | in-memory records in `starter.py` |
| transform/write | deterministic `explorer-package/*.yaml` |
| validate/play | fixed M15 Trail reads declarative package only |

Python and YAML file I/O remain local-only. The shared runtime never executes
student Python; only validated declarative package data crosses the boundary.

## World payoff

```console
python lessons/sessions/s20/student/starter.py
explore-package validate lessons/sessions/s20/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s20/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "complete-actions-in-order" \
  --name "S20 Data-Built Mystery Trail"
```

Focus the window; use WASD/arrows and E. Follow Sun Compass → Whisper Stone →
Tide Chime, then speak to Mystery Keeper. Checkpoint: validator pass and M15 payoff.

## Test and deliberate debug

Run the three prepared focused tests before optional edits:

```console
python -m pytest -q lessons/sessions/s20/student/test_pipeline.py
```

- Normal case: four input records select exactly three in priority order.
- Boundary case: exactly three included records succeeds; predict what two does.
- Malformed/invalid record: missing `priority` or a text coordinate fails before
  package writing.

Then build twice from unchanged input and compare generated files/diff: identical
input must produce identical relative files and bytes. Repair one field at a time.

## Support path

Use the prepared input unchanged and fill only validation predicates/tests. The
teacher may provide one field-check shape. Use printed sequence, generated YAML,
validator output, and a teacher Trail demo on low bandwidth.

## Extension path

Change one name/message source value, rebuild twice, and explain the one stable
output change. Comprehensions/generators are optional-extension discussion only.

## Milestone evidence and self-review

- [ ] Structured input safely loaded.
- [ ] Search/aggregate/sort/transform stages explained.
- [ ] Deterministic current-contract YAML generated.
- [ ] Normal, boundary, and malformed tests recorded/passed.
- [ ] Explorer Package validation passed.
- [ ] Playable M15 sequence completed.
- [ ] Transformation explanation: “Record ___ became ___ because ___.”
- [ ] Revision explanation: “I changed ___ after test ___ showed ___.”

## Required evidence/checkpoints

Submit the four-stage record trace, test results, deterministic diff evidence,
package validation, M15 completion, and both milestone explanations.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.** AI may ask one
pipeline question or propose one test only; it may not write pipeline/package code.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s20/student
git diff --staged
git commit -m "Build a data-driven mystery trail"
```

Interpret `M`, `??`, and no output; inspect generated YAML in the staged diff.
Use identity recovery and Control-C cancel/correct/retry. Understanding takes
priority over a rushed commit.
