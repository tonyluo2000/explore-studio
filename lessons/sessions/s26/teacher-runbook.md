# S26 — Capstone Blueprint

**Role:** Project-primary production lesson

**Reference teacher exemplar:** Stormlight Rescue Trail

**World reuse:** M03 `make-your-object-respond`

**Learning objective:** Students can decompose their own capstone into named
responsibilities, define at least three function contracts, model an expedition
with nested zones and stations, and prove one planned data-to-package path with
one validated, playable object.

**Prerequisite:** S25 student premise, playable prototype, project record, and
the S01–S25 Python, testing, package, Trail, and Git practices.

## Before class

- Confirm the shared Quick Start, Python environment, package validator, Trail
  controls, Git identity, accessibility choices, and screen-sharing fallback.
- Treat the student's S25 premise and project record as canonical. Stormlight
  Rescue Trail is a teacher exemplar only; never replace the student's premise.
- Keep `student/fixtures.py` fixed and read-only. The learner owns
  `student/project_data.py`, `student/starter.py`, `student/project-record.md`,
  and `student/explorer-package/`.
- Validate the student spike and the separate teacher-only recovery package.
- Reinforce that Python reasons about and previews data locally. Only reviewed,
  current-schema YAML enters the existing Trail; student Python is not runtime
  metadata and is never executed by the shared runtime.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 4 min | State the blueprint goal and reconnect to the student's S25 premise. | Premise plus three core acceptance criteria. |
| 0:04–0:09 | 5 min | Gate execution on a data-flow prediction and failure ownership. | Source-to-package flow, three failure points, owners, and one intermediate shape. |
| 0:09–0:31 | 22 min | Build the responsibility map and at least three complete function contracts; implement only enough for one acceptance test. | Seven mapped responsibilities, contracts, and focused test evidence. |
| 0:31–0:38 | 7 min | Review one student station into one M03 package object, validate, and play. | One student-owned object responds on approach and interaction. |
| 0:38–0:42 | 4 min | Review criteria, tests, mapping, risks, deferred work, and milestone evidence. | Explainable blueprint and self-review. |
| 0:42–0:45 | 3 min | Use status → diff → staged diff → descriptive commit. | Reviewable student change. |

## Planning and prediction gate

Before Python runs, the student draws or describes this flow:

```text
editable project_data.py → validation → stable selection/rules
→ transformation preview → reviewed package values
→ student explorer-package/ → validation → playable M03 world
```

They identify at least three possible failures, predict which responsibility
detects each failure, and explain one intermediate data shape. Useful examples
are an absent station ID, a malformed `zones`/`stations` shape, and duplicate
station IDs. Examples prompt thinking; students create their own map.

## Required responsibility map

The student creates a map in `project-record.md` showing which code owns each:

1. data input;
2. validation;
3. selection/rules;
4. transformation;
5. package build/output;
6. validation/play;
7. tests.

Keep validation separate from file I/O. Pure rule functions stay file-free.
Package build/output is an explicit responsibility even though S26 stops at a
reviewed preview and manual YAML edit rather than automatic file writing.

### Responsibility cards for support

- **Input card:** editable nested data, no validation decisions.
- **Validation card:** inspect shapes and values, return errors, no file access.
- **Rule card:** select and order already-validated records, no file access.
- **Transform card:** map selected records to current package fields.
- **Output card:** compare reviewed preview with student YAML.
- **Play card:** validate/package-plan and exercise the existing M03 behavior.
- **Test card:** prove valid, invalid, duplicate, and stable-order cases.

These cards reduce cognitive load; they do not fill in the student's map.

## Function contracts

Students define at least three core function contracts before implementation.
Every contract records: function name; inputs; return shape; expected
error/failure behavior; side effects, if any; and one concrete example.

Completed support example:

| Contract field | Example |
|---|---|
| Function name | `station_ids(stations)` |
| Inputs | A list of already-validated station dictionaries |
| Return shape | A new list of ID strings in input order |
| Error/failure behavior | Precondition: validation already succeeded; otherwise `KeyError` is allowed |
| Side effects | None; does not mutate input and does not read/write files |
| Concrete example | `[{'id': 'echo-stone'}]` → `['echo-stone']` |

The example is not one of the core TODO functions and provides no test answer.

## Nested model and learner tests

Use the understandable shape `expedition → zones → stations`. A station may
contain `id`, `name`, `enabled`, `coordinates`, `color`, `route_order`,
`signal_power`, and student-authored story/message fields. No classes are
required. `student/project_data.py` is editable; `student/fixtures.py` is fixed.

The focused learner cases cover a valid station, absent required ID, malformed
nested shape, duplicate station ID, and deterministic/stable selection order.
The pristine learner suite is intentionally red and excluded from default
repository discovery. A bounded student implementation should make it green.

## Small playable spike

Build exactly one student-owned object using only existing M03
`make-your-object-respond` behavior: `when_near` and `when_interacted`. Review
one selected station's current-contract values into the editable student
package, validate it, plan the Trail with Nova, approach it, and interact with
it. The spike proves ownership/data/package flow; it is not the full capstone.

The separate `teacher-recovery-package/` is teacher-only. It can preserve a
one-object M03 demonstration when blocked, but does not complete the student's
artifact. Even in recovery, protect the student's premise, responsibility map,
three contracts, prediction, and explanation of one data shape.

## Mapping review

| Source data field | Responsible Python function/module | Resulting package field | Visible Trail effect |
|---|---|---|---|
| station `id` | `select_stations` / `build_package_preview` | manifest contribution `id` and object filename | Identifies the student's object |
| station `name` | `build_package_preview` | object `name` | Labels the object |
| `coordinates.x`, `coordinates.y` | `build_package_preview` | object `x`, `y` | Places the object |
| station `color` | `build_package_preview` | object `color` | Styles the object |
| `story.when_near` | `build_package_preview` | object `when_near` | Appears on approach |
| `story.when_interacted` | `build_package_preview` | object `when_interacted` | Appears on interaction |
| `route_order`, `signal_power` | local selection/reasoning only | no S26 YAML field | No direct Trail effect |

## AI boundary

AI may review exactly ONE student-written acceptance criterion for ambiguity. It
may identify ambiguity and ask a clarifying question. It may NOT rewrite the
entire criterion, choose the premise, create the responsibility map, define
function contracts, write implementation, generate the package, or provide test
answers. The student accepts or rejects the suggestion and records why.

## Git review

The supplied repository history separates the blueprint/project record, initial
tests, and playable spike into three reviewable commits. For student work, retain
status → diff → staged diff → descriptive commit:

```console
git status --short
git diff
git add lessons/sessions/s26/student
git diff --staged
git commit -m "Refine my capstone blueprint"
```

Explain `M`, `??`, no output, identity recovery, and Control-C
cancel/correct/retry. Stage only intended student-owned files.

## Milestone evidence and teacher cut line

By the end of S26 protect: the responsibility map; three core contracts; one
acceptance test green; and one validated student-owned playable object. At 0:31
stop broad implementation. At 0:38 defer complete modules, the full multi-object
capstone, extra mechanics, and polish. Preserve test output, package validation,
the M03 interaction trace, self-review, AI receipt if used, and Git reasoning.

## Support path

Use the responsibility cards, completed non-core contract example, and
`MINIMAL_VALID_EXPEDITION`. If play is blocked, use the teacher-only recovery
package for a text-only or Trail demonstration. Support reduces scope; it never
replaces the student's premise or authorship.

## Extension

Identify one future helper/function and record its proposed responsibility and
contract name without implementing it.

## Teacher notes

- A correct implementation validates container shapes before iterating, checks
  station required fields/types, rejects duplicate IDs, raises for an absent
  required ID, and uses Python's stable sorting by `route_order` only.
- Validation functions and selection rules perform no file I/O.
- The one-object student and recovery packages must remain materially distinct.
- Do not add S27+ materials, runtime/schema/API behavior, Trail or Mission
  mechanics, deployment, authentication, or Phase E work.
