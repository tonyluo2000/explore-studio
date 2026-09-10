# S27 — Capstone Core

**Role:** Project-primary production lesson

**World reuse:** M06 `build-an-object-collection` and M14
`reuse-a-named-toggle-style`

**Learning objective:** Students can implement their accepted S26 contracts as
small imported helpers that validate nested project data and deterministically
build in-memory dictionaries compatible with the current Explorer Package.

**Prerequisite:** The student's S26 premise, responsibility map, function
contracts, nested `expedition → zones → stations` plan, and project record.

## Before class

- Confirm the shared Quick Start, Python environment, package validator, Trail
  controls, Git identity, and accessibility fallback.
- Treat the student's S26 project record and accepted contracts as canonical.
  The included Skyglass values are editable scaffolding, not a required premise.
- Keep `student/fixtures.py` fixed and read-only. The learner owns the nested
  data and TODO helpers in `data_io.py`, `validation.py`, `rules.py`, and
  `builder.py`; `starter.py` remains a thin import/coordination layer.
- Validate and plan the editable package reference. S27 compares deterministic
  in-memory dictionaries with YAML but never writes YAML files. File writing is
  S28 work.
- Reinforce that the shared runtime consumes validated YAML only and never runs
  student Python.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 4 min | Reconnect the S26 contracts to the modular-core goal. | Names the protected premise, criteria, and module owners. |
| 0:04–0:09 | 5 min | Gate each helper on predicted shapes and one whole-pipeline trace. | Input/output/example/edge predictions plus explicit intermediate values. |
| 0:09–0:31 | 22 min | Implement and test validation, data access, rules, ordering, and aggregation in small steps. | Small single-purpose helpers and focused test evidence. |
| 0:31–0:38 | 7 min | Build deterministic document dictionaries and compare with package YAML. | Exact manifest/object dictionary match; package validates and plans. |
| 0:38–0:42 | 4 min | Review diagnostics, regression output, behavior evidence, and one refactor. | Explainable failure and deterministic-output evidence. |
| 0:42–0:45 | 3 min | Use status → diff → staged diff → behavior-based commit. | Intentional staging and descriptive Git history. |

## Predict before each helper

Before implementing every required helper, the student records its input shape,
output shape, one concrete example, and one failure/edge case where applicable.
Before any implementation, require one explicit intermediate-value trace across:

```text
nested project input
→ ordered diagnostics
→ flattened station records
→ required-ID search
→ enabled filtering
→ aggregation
→ stable route ordering
→ deterministic declarative document dictionaries
```

Ask which module owns each value and why. Do not accept “the pipeline handles
it” without a concrete list/dictionary shape.

## Module responsibilities

- `data_io.py`: expose editable in-memory input and flatten validated zones;
  no validation policy and no file writing.
- `validation.py`: `validate_plan`, ordered fail-closed diagnostics, no file I/O.
- `rules.py`: required-ID search, enabled filtering, stable ordering, and signal
  aggregation; pure and file-free.
- `builder.py`: transform selected records into deterministic current-contract
  manifest/object dictionaries; no YAML serialization or file writing.
- `starter.py`: thin imports and orchestration only.

Required student-owned helpers are `validate_plan`, `flatten_stations`,
`find_required`, `select_enabled`, `order_route`, `signal_total`, and
`build_documents`. Keep every function small and single-purpose.

## Validation discipline

Preserve S21/S26 behavior: fail closed; return deterministic diagnostics in
documented order; reject malformed containers, wrong types, invalid coordinate,
order, and power ranges, duplicate station IDs, and invalid style references.
Validation remains separate from file I/O. Pure rules remain file-free.

Diagnostic order is: plan container/name/package/style/zones shape; then each
zone in source order; then each station in source order; then duplicate IDs.
Do not sort diagnostics after producing them because source order is evidence.

## Deterministic document payoff

`build_documents` returns in-memory dictionaries only. The expected shape has a
`manifest` dictionary and an `objects` list in stable route order. It uses only
existing schema 0.2 fields. Exactly one named toggle style appears, and exactly
two station objects reference it. A third ordinary object keeps the result
compatible with the existing M06 collection exercise; the two styled objects
reuse existing M14 behavior. No new package or runtime behavior is introduced.

Students compare the dictionaries with `student/explorer-package/`. They do not
write, generate, or overwrite YAML in S27. The student package remains an
editable visible target/reference artifact representing their premise.

## Focused tests

The fixed fixtures include: accepted S26 nested plan; empty-zone boundary;
missing required station; wrong-type record; duplicate ID; stable-order/tie
case; and expected deterministic document dictionaries. The pristine learner
suite is intentionally red and remains outside default repository discovery.
A correct bounded implementation makes every learner test green.

## Project record and evidence

Students continue one persistent record: premise, acceptance criteria,
responsibility map, contracts, risks, evidence, and deferred decision. S27 adds
implemented helpers, an intermediate-shape trace, behavior/test evidence, and
one refactoring decision. The task card points to the record rather than
duplicating self-review or AI receipt blanks.

## AI boundary

AI may propose exactly ONE failing test. Before asking, the student predicts why
the test should fail. The student decides whether to use it and records
accept/reject reasoning. AI may NOT write helper bodies, choose module
boundaries, generate package documents, solve validation, or provide final
expected outputs. The student implements all production code.

## Git close

Use small behavior-based commits after status → diff → staged diff:

1. validation + tests;
2. flatten/search/filter + tests;
3. ordering/aggregation + tests;
4. document-builder + regression evidence.

```console
git status --short
git diff
git add lessons/sessions/s27/student
git diff --staged
git commit -m "Implement one capstone core behavior"
```

There is no squash requirement. Explain `M`, `??`, no output, identity recovery,
and Control-C cancel/correct/retry.

## Support path

- Completed pure helper example only: `station_ids(stations)` returns IDs in
  input order without mutation or file access. It is not a required helper.
- Use `SINGLE_ZONE_REDUCED_PLAN` to reduce the amount of data, not the student's
  premise or contract ownership.
- Responsibility card reminder: input belongs to `data_io`; diagnostics to
  `validation`; decisions to `rules`; documents to `builder`.
- Expected flatten-stage shape: a list of station dictionaries in source order.

Support does not provide required helper bodies or solve the whole pipeline.

## Extension

Add one second zone while preserving deterministic flatten and stable route
order behavior. Do not add package fields or mechanics.

## Teacher cut line

By 0:38 protect validation, flattening, one required-ID selection/search rule,
stable ordering, and deterministic in-memory document output. Optional signal
aggregation polish may defer. Do not trade correctness for YAML writing, full
capstone assembly, extra mechanics, or polish.

## Teacher notes

- Stable sorting uses `route_order` only; equal values preserve selected order.
- `find_required` searches in requested-ID order and fails on the first absent
  ID. `select_enabled` then rejects required records that are disabled.
- Exact-output regression should compare plain dictionaries and lists, not YAML
  text formatting.
- Do not add S28+ materials, engine/schema/Student API/Trail/Mission/runtime
  behavior, deployment, authentication, or Phase E work.
