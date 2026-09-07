# Explore Studio — Sessions 16–30 Curriculum

> **Status:** Canonical second-half curriculum for the 30-session course.

Sessions 16–30 deepen local Python fluency while reusing the implemented
Missions 01–15 and their declarative world mechanics. Student Python remains
local-only. Only validated declarative Explorer Package artifacts cross into
the shared runtime, and that runtime never executes student Python.

## Second-half arc

| Sessions | Arc | Emphasis |
|---|---|---|
| S16–S20 | Data fluency | Traverse, search, aggregate, sort, and transform data. |
| S21–S24 | Software fluency | Validate, test, debug, decompose, refactor, and reason about algorithm cost. |
| S25–S30 | Independent creation | Plan, construct, review, and present an original capstone. |

Guided code continues through S20. Choice and partial independence begin in
S21. S25 is the formal transition to project-primary work.

## Session rhythms

Python-primary sessions use this 45-minute rhythm:

| Time | Activity |
|---:|---|
| 4 minutes | Creative hook |
| 6 minutes | Concept introduction and prediction |
| 18 minutes | Local Python activity |
| 7 minutes | Explorer Package and world payoff |
| 7 minutes | Test and debug |
| 3 minutes | Git review and descriptive commit |

Project-primary sessions use this 45-minute rhythm:

| Time | Activity |
|---:|---|
| 4 minutes | Creative goal |
| 5 minutes | Plan and prediction |
| 22 minutes | Project build |
| 7 minutes | Playable check |
| 4 minutes | Test and review |
| 3 minutes | Git review and descriptive commit |

S20 is a balanced milestone. It uses the Python-primary timing while treating
the generated package and playable M15 sequence as one integrated outcome.

## Session plans

### S16 — Curator's Atlas

**Python-primary.**

- **Creative goal:** Turn a crowded world into a readable object catalog.
- **Primary Python concept:** Deeper list and dictionary traversal, key access,
  `for`, and `enumerate`.
- **Local Python activity:** Traverse a list of object dictionaries and produce
  numbered labels.
- **World payoff:** Apply the records to an M06-themed collection and tour it.
- **Prediction:** Trace the first two iterations and write the expected output.
- **Test/debug:** Diagnose a missing key, duplicate ID, or incorrect nesting.
- **Bounded AI role:** Explain one iteration only after the student traces it.
- **Git/review habit:** Inspect a focused data-and-code diff, then write a
  descriptive commit.
- **Prerequisite:** S06 collections and loops.

### S17 — Clue Finder

**Python-primary.**

- **Creative goal:** Find the useful clues in a larger catalog.
- **Primary Python concept:** Functions, parameters, return values, searching,
  filtering, and counting.
- **Local Python activity:** Implement `find_by_id`, `filter_by_color`, and
  `count_matching`.
- **World payoff:** Use selected records to determine M03/M06 objects and
  response text.
- **Prediction:** Predict result order and match count before execution.
- **Test/debug:** Exercise no-match, one-match, and multiple-match cases.
- **Bounded AI role:** Suggest one edge case but never write the search.
- **Git/review habit:** Commit implementation and its assertions together.
- **Prerequisite:** S16 traversal.

### S18 — Power Station Scoreboard

**Python-primary.**

- **Creative goal:** Decide which devices need attention.
- **Primary Python concept:** Helper functions, return values, `min`, `max`,
  `sum`, and a simple average.
- **Local Python activity:** Summarize locally modeled counter records.
- **World payoff:** Use results to author M09 goals and demonstrate M13
  branches.
- **Prediction:** Predict the minimum, maximum, total, ties, and goal
  boundaries.
- **Test/debug:** Define the empty-input contract and test below, exactly at,
  and above a goal.
- **Bounded AI role:** Review the stated function contract without supplying its
  body.
- **Git/review habit:** Read source and test diffs before committing.
- **Prerequisite:** S17 functions and S09–S10 counter work.

### S19 — Route Planner

**Python-primary.**

- **Creative goal:** Arrange clues into a deliberate adventure route.
- **Primary Python concept:** Nested data, flattening, `sorted`, key functions,
  and stable ties.
- **Local Python activity:** Flatten zone/object records and sort them by an
  authored priority.
- **World payoff:** Use the first three results as an M15 sequence.
- **Prediction:** Predict tie order and whether the original list changes.
- **Test/debug:** Exercise equal keys, missing priority, and accidental in-place
  mutation.
- **Bounded AI role:** Explain the sort key only after a student prediction.
- **Git/review habit:** Commit the algorithm separately from story-data edits.
- **Prerequisite:** S16–S18.

### S20 — Data-Built Mystery Trail

**Balanced milestone.**

- **Creative goal:** Build a playable trail from a structured plan.
- **Primary Python concept:** A data-transformation pipeline and deterministic
  local structured-file I/O.
- **Local Python activity:** With prepared scaffolding, safely load starter
  YAML, validate and transform it, then safely write current-contract
  contribution files with stable ordering.
- **World payoff:** Validate the generated package and play its M15 trail.
- **Prediction:** Trace one record through input, transformation, and output.
- **Test/debug:** Check expected output structure, an invalid record, and the
  Explorer Package validator result.
- **Bounded AI role:** Ask one pipeline question or propose one test only.
- **Git/review habit:** Review the complete milestone diff and record a
  self-review.
- **Prerequisite:** S16–S19.

### S21 — Package Gatekeeper

**Python-primary.**

- **Creative goal:** Stop broken expedition data before it reaches the world.
- **Primary Python concept:** Validation functions and defensive input handling.
- **Local Python activity:** Return an ordered error list for missing fields,
  wrong types, invalid ranges, and duplicate IDs.
- **World payoff:** Observe an invalid package fail closed, repair it, and run
  M06.
- **Prediction:** Identify which checks fail and the expected diagnostic order.
- **Test/debug:** Use table-driven valid and malformed cases.
- **Bounded AI role:** Supply at most one malformed example.
- **Git/review habit:** Commit one validation behavior with its regression test.
- **Prerequisite:** S20 pipeline.

### S22 — Traceback Detective

**Python-primary.**

- **Creative goal:** Restore a broken guardian mystery.
- **Primary Python concept:** Assertions, test cases, traceback frames, and
  exception types.
- **Local Python activity:** Diagnose prepared `KeyError`, off-by-one, and
  incorrect-return failures.
- **World payoff:** Use the repairs to restore M08 or M13 behavior.
- **Prediction:** Identify the first relevant student-code frame and likely
  cause.
- **Test/debug:** Reproduce the failure, make one change, rerun, and add a
  regression test.
- **Bounded AI role:** Give one hint at a time after the traceback is
  interpreted aloud.
- **Git/review habit:** Write a fix commit that states the cause and protected
  behavior.
- **Prerequisite:** S21 validation.

### S23 — Builder's Workshop

**Python-primary.**

- **Creative goal:** Make the trail builder easier to extend without changing
  its world.
- **Primary Python concept:** Decomposition, helper functions, modules, imports,
  and refactoring.
- **Local Python activity:** Split the S20 pipeline into data I/O, rules, and
  build modules.
- **World payoff:** Use M14 to connect declarative reuse with code reuse; the
  rendered result remains unchanged.
- **Prediction:** Draw the call and data flow between modules.
- **Test/debug:** Compare pre-refactor and post-refactor outputs and run the
  regression tests.
- **Bounded AI role:** Point out duplication only after the student identifies
  candidates.
- **Git/review habit:** Create an isolated refactor commit with no intended
  behavior change.
- **Prerequisite:** S20–S22.

### S24 — Fast Ranger Index

**Python-primary.**

- **Creative goal:** Find many clues without repeatedly searching the entire
  catalog.
- **Primary Python concept:** Algorithmic thinking and informal algorithm-cost
  intuition.
- **Local Python activity:** Compare repeated linear scans with building an ID
  dictionary once; count record inspections instead of benchmarking time.
- **World payoff:** Resolve and order an M15 route with the indexed data.
- **Prediction:** Predict inspection counts for small and larger catalogs.
- **Test/debug:** Prove equivalent results and define duplicate-ID behavior.
- **Bounded AI role:** Ask one "what happens when the data doubles?" question.
- **Git/review habit:** Preserve before-and-after evidence in the commit
  message.
- **Prerequisite:** S17 search and S19 sorting.

### S25 — Playable Prototype

**Project-primary milestone.**

- **Creative goal:** Deliver one complete, small adventure loop.
- **Primary Python concept:** Project scope, acceptance criteria, and vertical
  slicing.
- **Local Python activity:** Choose a premise and implement one meaningful
  search, filter, count, aggregate, or sort pipeline.
- **World payoff:** Use one fitting existing mission from M07–M15.
- **Prediction:** Trace the visitor path and one invalid-data path.
- **Test/debug:** Cover normal, boundary, absent, malformed, and regression
  cases.
- **Bounded AI role:** Challenge scope with one bounded question and never
  generate the premise.
- **Git/review habit:** Separate plan and prototype commits and complete a
  milestone self-review.
- **Prerequisite:** S16–S24.

### S26 — Capstone Blueprint

**Project-primary.**

- **Creative goal:** Turn an original adventure idea into a buildable plan.
- **Primary Python concept:** Decomposition, function contracts, data modeling,
  and test planning.
- **Local Python activity:** Create sample nested data, function signatures, a
  responsibility map, and initial tests.
- **World payoff:** Run a small M03/M05 or state-mechanic spike.
- **Prediction:** Trace data from source to declarative artifact and identify
  failure points.
- **Test/debug:** Make one acceptance test pass without building the entire
  project.
- **Bounded AI role:** Review one acceptance criterion for ambiguity.
- **Git/review habit:** Commit the blueprint, tests, and spike as distinct
  changes.
- **Prerequisite:** S25 prototype.

### S27 — Capstone Core

**Project-primary.**

- **Creative goal:** Build the Python system that creates or checks the
  adventure.
- **Primary Python concept:** Independent helper design, modules,
  transformations, and validation.
- **Local Python activity:** Implement the central pipeline behind the S26
  contracts.
- **World payoff:** Generate or transform M06/M14-compatible contributions.
- **Prediction:** Explain each pipeline stage and intermediate shape.
- **Test/debug:** Add unit, boundary, and invalid-data cases.
- **Bounded AI role:** Propose one failing test; the student owns the
  implementation.
- **Git/review habit:** Make small behavior-based commits.
- **Prerequisite:** An accepted S26 blueprint.

### S28 — Capstone Integration

**Project-primary.**

- **Creative goal:** Connect the Python work to the complete playable story.
- **Primary Python concept:** Structured-file boundaries and narrow exception
  handling.
- **Local Python activity:** Read source data, build known YAML fields, handle
  expected file and parse failures, validate, and export locally.
- **World payoff:** Demonstrate the chosen existing dialogue, toggle, counter,
  style, or sequence mechanics.
- **Prediction:** Enumerate generated files and expected Trail behavior.
- **Test/debug:** Exercise a missing file, corrupt data, validation failure, and
  successful path.
- **Bounded AI role:** Interpret one diagnostic code; the student makes the
  correction.
- **Git/review habit:** Include validation evidence in the integration commit.
- **Prerequisite:** S27 core.

### S29 — Expedition Review

**Project-primary.**

- **Creative goal:** Make the capstone understandable and dependable for
  another person.
- **Primary Python concept:** Code review, refactoring, naming, and regression
  testing.
- **Local Python activity:** Review a peer or teacher diff, address actionable
  comments, remove duplication, and simplify one confusing function.
- **World payoff:** Conduct a complete visitor walkthrough using an applicable
  M01–M15.
- **Prediction:** State which behavior each proposed refactor could affect.
- **Test/debug:** Run the full suite and a manual smoke test.
- **Bounded AI role:** Offer at most two evidence-based review observations.
- **Git/review habit:** Respond with follow-up commits instead of hiding review
  history.
- **Prerequisite:** Integrated S28 capstone.

### S30 — World Premiere

**Project-primary.**

- **Creative goal:** Present a substantial original expedition and explain how
  it works.
- **Primary Python concept:** Synthesis, technical explanation, and
  demonstration recovery.
- **Local Python activity:** Run the clean test suite, validate, export twice to
  confirm determinism, and rehearse one algorithm walkthrough.
- **World payoff:** Run proposed M16 as a final guided tour. Until M16 is
  separately authorized and implemented, M01 provides the exact existing
  completion-rule fallback.
- **Prediction:** Script the demo path and recovery from one likely failure.
- **Test/debug:** Show final regression and package-validation evidence.
- **Bounded AI role:** Ask rehearsal questions only; the student explains all
  accepted code.
- **Git/review habit:** Create a final reviewed commit and optional local
  capstone tag; do not deploy.
- **Prerequisite:** S29 review-complete capstone.

## Python progression

The integrated strand progresses through:

`traversal → search/filter/count → functions/returns → aggregation → nested
data → sorting → deterministic transformation/file I/O → validation →
defensive handling → assertions/tracebacks → decomposition/modules →
refactoring → algorithm-cost intuition → independent project construction`

Simple classes are not required in the core course. Dictionaries and nested
data are the preferred representation because they align directly with YAML
and Explorer Package data. A local-only dataclass may be offered as an optional
advanced extension after S23, but it is not assessed, serialized as a runtime
object, or required by the shared artifact contract.

## Mission strategy

Sessions and Missions are no longer 1:1. S16–S29 require no new canonical
Mission; they reuse Missions 01–15 as visual and playable contexts for local
Python work.

One future Mission 16 is proposed only for S30:

- **ID:** `present-your-capstone-expedition`
- **Title:** `Share Your Expedition`
- **Completion rule:** reuse `ALL_OBJECTS_VISITED`
- **Purpose:** provide capstone-specific instructions and a visible final Trail
  completion while the assessment rubric separately covers Python, validation,
  explanation, and presentation.

M16 is proposed, not implemented or authorized by this curriculum document.
Adding it requires a separate reviewed decision. It must add no Explorer
Package field, runtime behavior, Trail state, or completion rule. No Missions
17–30 are presently justified.

## Reuse plan

| Sessions | Existing Mission or mechanic reused |
|---|---|
| S16–S17 | M03 and M06 authored responses and collections |
| S18 | M09 counters and M13 boundary comparison |
| S19–S20 | M15 deterministic ordered route |
| S21 | M02/M06 plus existing package diagnostics |
| S22 | M08 or M13 visible branch repair |
| S23 | M14 declarative reuse as a parallel to code reuse |
| S24 | M15 indexed route resolution |
| S25 | One student-selected M07–M15 context |
| S26 | M03/M05 or one existing state-mechanic spike |
| S27 | M06/M14 generated collections or styles |
| S28 | Existing dialogue, toggle, counter, comparison, style, or sequence mechanics |
| S29 | Any representative M01–M15 walkthrough |
| S30 | Proposed M16, with M01 as the zero-new-content fallback |

Only one exact Trail mission needs to be active for a demonstration. A package
may still combine multiple compatible existing mechanics.

## Runtime and package boundary

Sessions 16–30 justify zero new runtime needs:

- no engine capability;
- no Explorer Package field or schema;
- no Trail behavior or state;
- no completion rule; and
- no shared execution of Python.

Curriculum-side starter datasets, pytest scaffolds, review rubrics, and
deterministic builder examples are teaching materials, not runtime contracts.
Local Python may read and write structured data because YAML is the authentic
package boundary. Only output accepted by the current package validator may be
exported or consumed by the shared runtime.

The following remain local Python or curriculum concepts and must not become
runtime fields:

- loops and comprehensions;
- functions, parameters, return values, and helpers;
- Python lists, dictionaries, and intermediate structures;
- search, filter, count, aggregate, and sort operations;
- indexes, caches, and algorithm choice;
- assertions, tests, and fixtures;
- tracebacks and exceptions;
- modules, imports, classes, and dataclasses;
- file names and build steps;
- AI prompts and review metadata;
- generalized callbacks, expressions, or executable behavior; and
- project, rubric, presentation, or deployment metadata.

## AI progression

- **S16–S20:** Bounded explanation and test prompts after prediction.
- **S21–S24:** Diagnostic and review hints only after the student provides
  evidence.
- **S25–S28:** Scope critic or test proposer only; AI does not select the
  premise or implement the project.
- **S29–S30:** Bounded code reviewer and rehearsal audience.

Every optional AI interaction retains:

`explain intent → predict → bounded question → test → revise → explain accepted
code`

Students accept AI-suggested code only when they can explain every line and
show the supporting test evidence.

## Git and review progression

Every session retains `status → diff → descriptive commit`.

- **S16–S20:** Use focused diffs, commit code and its tests together, and add a
  milestone self-review at S20.
- **S21–S24:** Create regression commits, keep refactors isolated, and preserve
  before-and-after evidence.
- **S25–S28:** Keep the plan, core behavior, and integration in separate,
  reviewable commits.
- **S29:** Review a peer or teacher diff and respond with follow-up commits.
- **S30:** Create a final reviewed commit and optional local tag. Publishing and
  deployment are not part of the course.

## Milestone rubrics

### S20 — Data-built mystery trail

The scaffolded milestone includes:

- structured input;
- search, aggregation, sorting, and transformation;
- deterministic current-contract YAML;
- normal, boundary, and invalid-data tests;
- successful Explorer Package validation;
- a playable M15 sequence; and
- the student's explanation of one transformation and one revision.

### S25 — Playable vertical slice

The original bounded prototype includes:

- three to five observable acceptance criteria;
- a documented data model and function decomposition;
- one meaningful algorithmic pipeline;
- normal, boundary, absent, malformed, and regression cases;
- one existing Trail mechanic working end to end; and
- a reviewed diff plus the remaining capstone build plan.

### S30 — Capstone expedition

The substantial original project includes:

- sensibly modular local Python;
- nested data;
- at least two meaningful search, filter, count, aggregate, or sort operations;
- validation and narrow defensive handling;
- automated normal, boundary, invalid, and regression tests;
- deterministic Explorer Package generation or transformation;
- at least two compatible existing world mechanics;
- successful validation, deterministic local export, and a playable
  walkthrough; and
- a presentation covering decomposition, algorithm choice, tests, one
  debugging or refactoring story, and all accepted AI assistance.

## Scope boundary

This document completes the approved 30-session curriculum architecture. It
does not implement Mission 16, modify Missions 01–15, add Mission 17–30, or
change any engine, Explorer Package, Student API, Classroom Trail, test, or
runtime contract. Student Python runs locally only; the shared runtime consumes
only validated declarative artifacts. Deployment, authentication, publishing,
and Phase E remain parked.
