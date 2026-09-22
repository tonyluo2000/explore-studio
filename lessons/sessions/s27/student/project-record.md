# My Persistent Capstone Project Record — S27

This carries my student-owned S25/S26 premise, scope, decisions, and evidence
forward. S26 handed me a capstone blueprint and one bounded first-slice target;
the responsibility map and the function contracts below are mine to write here,
derived from that blueprint. It is not runtime metadata. The task card points
here instead of duplicating self-review and AI receipt blanks.

## Premise and acceptance criteria carried forward

- My place, purpose, and visitor payoff: ___
- What remains from my S25 prototype: ___
- What my S26 blueprint accepted: ___
1. Core acceptance criterion: ___
2. Core acceptance criterion: ___
3. Core acceptance criterion: ___
4. Optional criterion: ___

## Responsibility map carried forward

Derived here from my S26 blueprint's first slice: one job per module, and a
reason each job belongs where I put it.

| Responsibility | Owning module/artifact | Why |
|---|---|---|
| Data input | ___ | ___ |
| Validation | ___ | ___ |
| Selection/rules | ___ | ___ |
| Transformation | ___ | ___ |
| Package build/output | ___ | ___ |
| Validation/play | ___ | ___ |
| Tests | ___ | ___ |

## Accepted function contracts

Write each helper's contract here from my blueprint's first slice: its input,
return, failure, side effects, and one example. Record any accepted
clarification once implementation starts.

| Helper | Input shape | Output shape | Example | Failure/edge case | Side effects |
|---|---|---|---|---|---|
| `validate_plan` | ___ | ___ | ___ | ___ | ___ |
| `flatten_stations` | ___ | ___ | ___ | ___ | ___ |
| `find_required` | ___ | ___ | ___ | ___ | ___ |
| `select_enabled` | ___ | ___ | ___ | ___ | ___ |
| `order_route` | ___ | ___ | ___ | ___ | ___ |
| `signal_total` | ___ | ___ | ___ | ___ | ___ |
| `build_documents` | ___ | ___ | ___ | ___ | ___ |

## Whole-pipeline intermediate-value trace

- Nested project input shape/value: ___
- Ordered diagnostics value: ___
- Flattened station-record list: ___
- Required-ID search result: ___
- Enabled-filter result: ___
- Aggregated signal value: ___
- Stable route-order result: ___
- Deterministic document dictionary shape: ___
- Failure boundary and value that does not get built: ___

## Implemented helpers and evidence

| Helper | Implemented? | Focused test/result | Behavior I can explain |
|---|---|---|---|
| `validate_plan` | ___ | ___ | ___ |
| `flatten_stations` | ___ | ___ | ___ |
| `find_required` | ___ | ___ | ___ |
| `select_enabled` | ___ | ___ | ___ |
| `order_route` | ___ | ___ | ___ |
| `signal_total` | ___ | ___ | ___ |
| `build_documents` | ___ | ___ | ___ |

## Package-compatible output evidence

- Exact-output regression result: ___
- One named style and two references confirmed: ___
- M06-compatible package validation/planning: ___
- M14-compatible style reuse evidence: ___
- YAML remained manually reviewed and was not written by Python: ___

## Risks, refactoring, and deferred decisions

- Known risk 1: ___
- Known risk 2: ___
- One refactoring decision and why: ___
- One decision deliberately deferred: ___

## Milestone self-review

- Creative choice I still own: ___
- Small helper I can explain: ___
- Failure behavior I verified: ___
- Intermediate value I can trace: ___
- Next bounded step: ___

## AI one-test receipt

Leave blank if AI was not used.

- My prediction before asking: ___
- The one failing test proposed: ___
- Why it should fail: ___
- Accepted/rejected: ___
- My reason: ___
- Production code I wrote myself: ___
