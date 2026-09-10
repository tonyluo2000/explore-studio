# S28 — Capstone Integration

**Role:** Project-primary production lesson

**World reuse:** M14 `reuse-a-named-toggle-style` and M15
`complete-actions-in-order`

**Learning objective:** Students can connect their S27 modular core to narrowly
bounded local YAML input/output, generate byte-stable current-contract Explorer
Package files, preserve validator failures, and verify two existing mechanics.

**Prerequisite:** The student's S26 blueprint, completed S27 helper contracts,
modular core, deterministic document dictionaries, and persistent project
record.

## Before class

- Confirm the shared Quick Start, PyYAML, package validator, Trail controls, Git
  identity, accessibility choices, and screen-sharing fallback.
- Treat the student's premise, S27 modules, and reviewed dictionaries as
  canonical. The included Skyglass plan is editable scaffolding, not a required
  premise.
- Keep `student/fixtures/` and `student/fixtures.py` fixed and read-only. The
  learner owns `source-plan.yaml`, `integration.py`, and the generated/editable
  `explorer-package/`.
- Confirm S28 imports S27 `data_io`, `validation`, `rules`, and `builder`; do not
  let students copy their logic into integration code.
- Validate and plan the student package. Keep any teacher demonstration clearly
  separate and fallback-only; it cannot count as student integration evidence.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 4 min | Connect the S27 in-memory result to the S28 file-boundary goal. | Names the read/build/write/validate responsibilities. |
| 0:04–0:09 | 5 min | Gate execution on exact file and Trail predictions. | File list, IDs, route order, style pair, and M15 prediction. |
| 0:09–0:31 | 22 min | Implement bounded load, deterministic write, and package integration. | Four-path evidence plus path-safety and byte-stability results. |
| 0:31–0:38 | 7 min | Validate/plan the generated package and play M14 and M15. | Shared-style and ordered-sequence observations. |
| 0:38–0:42 | 4 min | Review missing/corrupt/invalid/success paths and integration decision. | Test, validator, and deterministic-export evidence. |
| 0:42–0:45 | 3 min | Use status → diff → staged diff → behavior-based commit. | Intentional staging and descriptive Git history. |

## Prediction gate

Before running code, students record in `project-record.md`:

- the exact generated file list;
- selected object IDs and stable route order;
- which two objects share the named toggle style;
- expected M15 correct-order and wrong-member/reset behavior.

They trace one value across:

```text
local YAML source
→ safe load
→ reused S27 validation/helpers
→ deterministic document dictionaries
→ safe bounded file writing
→ Explorer Package validation
→ Trail plan/play
```

## Integration responsibilities

- `load_plan`: use `yaml.safe_load`; accept only expected mapping/list shapes;
  keep the source path inside the S28 student project area.
- `write_yaml`: use `yaml.safe_dump(..., sort_keys=False)`; confine every write
  to the fixed student package root and return written bytes as evidence.
- `build_package`: reuse S27 validation, flatten/search/filter/order, aggregation,
  and builder helpers; validate identifiers before constructing object paths;
  write a stable file set; run package validation; never turn diagnostics into
  success.
- `main`: remain thin—load, build, report output path and validation evidence.

Do not scan directories, accept arbitrary roots, or reimplement S27 rules.

## Input boundary and narrow failures

The source is one explicit local path under `lessons/sessions/s28/student/`.
Resolve before comparing roots; reject absolute, `..`, separator-bearing, or
outside-root paths. Use `yaml.safe_load` and require only expected dictionary and
list containers. Never use unsafe YAML constructors.

Handle only the expected boundaries:

1. missing input file → named `InputPlanError` with a clear file name;
2. YAML parse failure → named `CorruptPlanError` with a clear corrupt-data message;
3. locally shaped but semantically invalid plan → `InvalidPlanError` preserving
   ordered S27/validator diagnostics, never success;
4. success → fixed output package path, generated-file list, and validation evidence.

Do not use broad `except Exception`, silent fallback, catch-and-ignore, or
automatic repair.

## Output confinement and identifier safety

The output root is the fixed S28 `student/explorer-package/` directory. It is
not a caller-selected path. Every resolved output must remain beneath that root.
Use stable filenames and contribution order.

Validate a contribution ID against the existing lowercase slug rule before the
ID is interpolated into any path. Reject `../`, `/`, `\\`, absolute-path text,
and all separator-bearing IDs. The completed `safe_object_output_path` is the
single support helper example; students still implement all required integration
helpers and must explain why validation precedes path construction.

Write UTF-8 bytes using `yaml.safe_dump(document, sort_keys=False,
allow_unicode=True)` or an equivalent deterministic call. The same input must
produce the same file list, tree, and bytes on every run.

## Existing-world payoff

The generated package uses existing schema 0.2 only:

- M14: one named `observatory-glow` toggle style is referenced by exactly two
  objects;
- M15: one existing `respond_to_sequence` character references the three stable
  route IDs.

No new package fields, schema, runtime behavior, Trail logic, or Mission logic
is introduced. A teacher may demonstrate the second mechanic if Trail time runs
short, but the student still owns deterministic generation and validation
evidence.

## Source-to-world mapping

| Source plan field | Reused S27 helper | Generated document | YAML file | Visible Trail behavior |
|---|---|---|---|---|
| station `id` | `find_required`, `order_route`, `build_documents` | contribution `id` | manifest and `objects/<id>.yaml` | Stable object identity/order |
| `coordinates.x/y` | `build_documents` | object `x`, `y` | object file | Object position |
| `color` / `toggle_style_id` | validation + `build_documents` | object `color` or style reference | manifest/object files | Ordinary color or shared M14 style |
| `story.when_near/when_interacted` | `build_documents` | response fields | object file | Approach/interaction messages |
| package `toggle_style` | validation + `build_documents` | one `toggle_styles` entry | manifest | Two objects share M14 style |
| `required_station_ids` | `find_required`, `order_route` | `respond_to_sequence.object_ids` | `character/sky-guide.yaml` | Existing M15 ordered sequence |

## Intentional-red baseline

The fixed learner cases cover missing source, corrupt YAML, semantically invalid
plan, successful generation, repeated byte identity, unsafe ID rejection before
path construction, generated-package validation, and M14/M15 structure.

The pristine result is **6 failed / 2 passed**. The missing-source and
corrupt-YAML tests pass because the scaffold already demonstrates two narrow
exception translations. Those passes do not mean `load_plan`, `write_yaml`, or
`build_package` is complete: path/shape confinement, writing, validation, and
generation cases remain red. The learner suite stays outside default discovery;
a bounded correct implementation makes all eight tests green.

## Project record and AI boundary

Continue one persistent record with S25–S27 premise, criteria, responsibility
map, contracts, risks, evidence, and deferred decisions. Add file predictions,
four path outcomes, deterministic bytes, validator evidence, M14/M15
observations, and one integration/debugging decision. The task card points to
the record rather than duplicating self-review or AI blanks.

AI may interpret exactly ONE validator diagnostic. The student first identifies
the diagnostic, predicts its likely source, asks one bounded question, makes the
correction, and records accept/reject reasoning. AI may NOT write I/O helpers,
generate YAML, change package schema, rewrite S27 logic, choose exception
handling, or provide final package contents.

## Git close

Use reviewable behavior commits after status → diff → staged diff:

1. input loading + failure tests;
2. safe writer + deterministic-output tests;
3. package integration + validation evidence;
4. Trail integration evidence.

There is no squash requirement. Explain `M`, `??`, no output, identity recovery,
and Control-C cancel/correct/retry.

## Support path

Use the prepared valid source plan, `GOLDEN_FILE_LIST`, and the one completed
safe-output-path helper. If Trail time runs short, demonstrate one existing
mechanic while the student explains the other predicted behavior. Never provide
a complete `build_package`; support lowers scope and does not replace the
student's premise or integration evidence.

## Extension

Change one story/message value and prove only its intended generated object file
content changes while the file list and repeat-run byte determinism remain.

## Teacher cut line

By 0:38 protect one valid source read, one deterministic safe package
generation, package validation, one M14 observation, and one M15 observation.
If time is short, teacher-demo the second mechanic but preserve student-owned
generation and validation. Defer polish, extra files, mechanics, and S29 work.

## Teacher notes

- Review the unsafe-ID case first: rejection must occur before constructing a
  path containing the student value.
- Compare bytes, not parsed-YAML equality, on the second generation.
- Preserve validator diagnostic codes/locations/messages in evidence.
- Do not add S29+ materials, engine/schema/Student API/Trail/Mission/runtime
  behavior, deployment, authentication, or Phase E work.
