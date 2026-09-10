# S30 Task Card — World Premiere

**Role:** Project-primary production lesson

**World payoff:** Present your substantial original expedition through Mission
16, guide a visitor to every object, and explain the Python and evidence behind
the experience.

**Learning target:** Synthesize your capstone work into a clear technical
demonstration, prove deterministic local export, and recover calmly from one
likely demonstration failure.

Use the shared [`Student Quick Start`](../../student-quick-start.md), your
review-complete S29 capstone, `project-record.md`, and
`premiere-checklist.md`. The included Skyglass package is a runnable comparison
target, not a replacement for your original project.

## Freeze the reviewed starting point (0:00–0:05)

Run `git status --short` and name the exact reviewed commit you are presenting.
Do not add features during premiere rehearsal. Record the premise, visitor
payoff, acceptance criteria, deferred ideas, and clean or understood working
tree in `project-record.md`.

Predict before running anything:

1. which tests will pass;
2. which package members will export, in order;
3. whether two fresh exports will have identical bytes and SHA-256; and
4. what the visitor will observe at each object.

## Produce the final technical receipt (0:05–0:15)

Run the focused suite, then the appropriate complete project suite:

```console
python -m pytest -q lessons/sessions/s30/student/test_premiere_evidence.py
python -m pytest -q
explore-package validate lessons/sessions/s30/student/explorer-package
```

Use `collect_premiere_evidence` with a fresh local output directory to validate,
plan Mission 16, and export twice. The two directories prevent one run from
overwriting the other. Record ordered members, byte count, both SHA-256 values,
and the exact byte comparison. A failed validation, plan, or export stops the
evidence chain; do not present a stale archive as current.

The command-line equivalent uses absolute paths and two fresh directories:

```console
explore-package export /absolute/path/to/explorer-package \
  --output /absolute/path/to/first/skyglass-premiere-1.0.0.explorer-package.zip
explore-package export /absolute/path/to/explorer-package \
  --output /absolute/path/to/second/skyglass-premiere-1.0.0.explorer-package.zip
```

Export is local artifact creation. It is not publication, approval, release,
signing, or deployment.

## Rehearse the explanation (0:15–0:25)

Explain this chain without reading code line by line:

```text
source nested data
→ validation and narrow failure handling
→ at least two meaningful search/filter/count/aggregate/sort operations
→ modular deterministic document generation
→ validated Explorer Package YAML
→ byte-identical local exports
→ Classroom Trail Mission 16
```

Walk through one algorithm in detail: its input shape, intermediate state,
output, ordering rule, boundary behavior, and the test that protects it. Then
show a normal, boundary, invalid, and regression test and tell one debugging or
refactoring story from S25–S29.

## Script the tour and recovery (0:25–0:32)

Write the exact object route before launching. The comparison package uses:

```text
Echo Lens → Wind Dial → Comet Bell
```

Name one likely failure—red test, validation diagnostic, export refusal, Trail
launch problem, or lost window focus. Rehearse: state the symptom, read the
first relevant evidence, make one bounded correction, rerun the exact failed
check, and resume at a named point. Never hide a failure or improvise a field.

## World premiere (0:32–0:41)

Launch the existing local Trail with Mission 16:

```console
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s30/student/explorer-package \
  --player nova-character:nova \
  --mission present-your-capstone-expedition
```

Guide the visitor to every world object. Point out the existing M14 named style
shared by Echo Lens and Wind Dial, then the existing M15 ordered sequence and
wrong-member/reset behavior. Add no new mechanic.

Say this boundary aloud: **Mission 16 Complete means only that the guided object
tour is complete.** It does not certify Python quality, tests, package
validation, presentation quality, approval, publication, or release. Those
assessment items remain in the teacher rubric and evidence record.

## Questions, receipt, and final commit (0:41–0:45)

Answer questions by pointing to code, data, tests, or recorded evidence. Explain
every accepted line and disclose all accepted AI assistance. Update the record,
then use status → diff → staged diff → descriptive final reviewed commit.

An optional capstone tag is local only and must point at that reviewed commit.
Do not publish, deploy, sign, approve, or release anything in this lesson.

## AI boundary, support, and cut line

Complete your own demo script and failure prediction first. AI may ask at most
**TWO rehearsal questions only** about your explanation or evidence. You answer
them. AI may not supply answers, rewrite code, generate the presentation or
package, repair a failure, invent assessment evidence, or add features.

For access or low bandwidth, use printed test/validation/export receipts,
object names and coordinates, a text walkthrough, or a teacher-operated Trail
while you narrate. If time is short, protect green tests, valid package, matching
exports, one algorithm explanation, the recovery script, every-object M16 tour,
and the completion boundary. Defer polish, optional tagging, and extra Q&A.
