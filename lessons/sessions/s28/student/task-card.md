# S28 Task Card — Capstone Integration

**Role:** Project-primary production lesson

**World payoff:** Generate your current-contract Explorer Package safely and
deterministically, then validate and play existing M14 and M15 behavior.

**Learning target:** Connect your S27 modular core to narrow local YAML input and
output without duplicating rules, escaping the project directory, hiding errors,
or changing runtime behavior.

Use the shared [`Student Quick Start`](../../student-quick-start.md) and continue
your persistent `project-record.md`.

## Integration goal (0:00–0:04)

Keep your own premise, acceptance criteria, responsibility map, S27 contracts,
risks, and decisions. The included Skyglass plan is editable scaffolding. Your
generated package—not any teacher demonstration—is your integration evidence.

Required student-owned helpers:

- `load_plan`
- `write_yaml`
- `build_package`
- thin `main`

Import and call the S27 `data_io`, `validation`, `rules`, and `builder` modules.
Do not copy or rewrite their logic in S28.

## Predict files and Trail behavior (0:04–0:09)

Before execution, record in `project-record.md`:

- exact generated file list;
- selected object IDs;
- stable route order;
- which two objects share the named style;
- expected M15 correct-order and wrong-member/reset behavior.

Trace one ID and message across:

```text
local YAML source → safe load → S27 helpers → document dictionaries
→ bounded YAML files → package validation → Trail plan/play
```

## Implement the boundary (0:09–0:31)

### Safe input

Use `yaml.safe_load`. Accept only the expected mapping/list shape. Resolve the
explicit source path under the S28 student project directory. Reject absolute,
`..`, separator-bearing, outside-root, or broadly scanned input paths.

Translate only expected errors:

- missing file → clear `InputPlanError`;
- YAML parse failure → clear `CorruptPlanError`;
- shaped but invalid plan → `InvalidPlanError` preserving ordered diagnostics;
- valid plan → continue without repair or fallback.

Never use `except Exception`, silent fallback, catch-and-ignore, or automatic
repair.

### Safe deterministic output

The output root is fixed at `student/explorer-package/`; callers do not choose
another root. Validate every contribution ID before constructing a path with it.
Reject `../`, `/`, `\\`, absolute-path text, or any separator-bearing ID.

Use stable filenames/contribution order and:

```python
yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
```

Write UTF-8 bytes. The same input must produce an identical file list, tree, and
bytes on every run. Do not scan the filesystem or write outside the fixed root.

### Reuse the modular core

`build_package` calls the completed S27 validation, flatten/search/filter,
aggregation, stable-order, and document-builder helpers. It then adds only the
existing M15 sequence document, writes the reviewed current-contract documents,
validates the package, and reports its output path and validator evidence.

Run only after completing predictions:

```console
python lessons/sessions/s28/student/starter.py
```

These tests are expected to fail until you complete the TODO functions.
The expected pristine result is **6 failed / 2 passed**. The missing-source and
corrupt-YAML tests pass because the scaffold already demonstrates those two
narrow exception translations; those passes do not mean the integration helpers
are complete because path/shape, writing, semantic-validation, and generation
cases still fail.

```console
python -m pytest -q lessons/sessions/s28/student/test_integration.py
```

Keep `fixtures/` and `fixtures.py` unchanged. The eight cases cover missing
source, corrupt YAML, invalid plan, valid generation, repeated byte identity,
unsafe ID rejection before path construction, generated-package validation, and
expected M14/M15 structure.

## Validate and play two existing mechanics (0:31–0:38)

```console
explore-package validate lessons/sessions/s28/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  lessons/sessions/s28/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "reuse-a-named-toggle-style" \
  --name "My S28 M14 Integration"
```

Run the same Trail command with mission ID `complete-actions-in-order` for M15.
Observe the two shared-style objects and then the correct three-ID sequence. Try
a wrong authored member and record the existing reset behavior. Add no mechanics
or package fields.

## Mapping review

| Source plan field | S27 helper | Generated document/YAML | Visible Trail behavior |
|---|---|---|---|
| station `id` | `find_required`, `order_route`, `build_documents` | manifest + `objects/<id>.yaml` | Stable identity/order |
| `coordinates` | `build_documents` | object `x`, `y` | Position |
| `color` / `toggle_style_id` | validation + `build_documents` | color/style fields | Ordinary or shared M14 style |
| story messages | `build_documents` | `when_near`, `when_interacted` | Object responses |
| package `toggle_style` | validation + `build_documents` | manifest style | Two styled objects |
| `required_station_ids` | `find_required`, `order_route` | guide sequence IDs | M15 ordered behavior |

## Four-path test and review (0:38–0:42)

Use `project-record.md` for missing, corrupt, invalid, and success outcomes;
deterministic byte evidence; validator output; M14/M15 observations; integration
decision; milestone self-review; and AI receipt. Those blanks are not duplicated
here.

## AI boundary

AI may interpret exactly ONE validator diagnostic. First identify it and predict
its likely source; ask one bounded question; make the correction yourself; and
record accept/reject reasoning in `project-record.md`.

AI may NOT write I/O helpers, generate YAML, change package schema, rewrite S27
logic, choose exception handling, or provide final package contents. Do not paste
whole files or request a complete solution.

## Git close (0:42–0:45)

Use status → diff → staged diff and reviewable behavior commits:

1. input loading + failure tests;
2. safe writer + deterministic-output tests;
3. package integration + validation evidence;
4. Trail integration evidence.

```console
git status --short
git diff
git add lessons/sessions/s28/student
git diff --staged
git commit -m "Integrate one safe package boundary"
```

There is no squash requirement. Interpret `M`, `??`, and no output; use identity
recovery and Control-C cancel/correct/retry.

## Support path

Use the prepared valid source plan, `GOLDEN_FILE_LIST`, and the completed
`safe_object_output_path` example. A teacher may demonstrate one mechanic if
Trail time runs short, but cannot provide `build_package` or replace your
premise, deterministic generation, validation, or other mechanic evidence.

## Extension

Change one story/message and prove only the intended object-file bytes change;
file list and repeat-run determinism remain stable.

## Cut line

Protect one valid source read, one deterministic safe package generation,
package validation, one M14 observation, and one M15 observation. Defer polish,
extra files, mechanics, and S29 work.
