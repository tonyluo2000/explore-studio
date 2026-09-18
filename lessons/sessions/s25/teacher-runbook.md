# S25 — Playable Prototype

**Role:** Project-primary production lesson

**Milestone:** B — Playable Prototype

**Reference teacher exemplar:** Stormlight Rescue Trail

**World reuse:** M15 `complete-actions-in-order` plus one student-chosen second
mechanic (counter, toggle, two-toggle, or either-toggle).

**Learning objective:** Students independently combine two supported mechanics
into one coherent prototype, prove it with real package validation and a
deterministic build, play it in Trail, fix one real problem, and explain one
design decision and one technical decision.

**Student-owned action:** The student chooses the premise, every name and
player-facing message, which second mechanic to combine with the route, where
that mechanic sits, one mechanic parameter or goal, and the reflection.

**Prerequisite:** S16–S24 nested data, validation, debugging, composition,
behavior-preserving improvement, package validation, and Git.

**Arc note:** Milestone B closes **S21–S24 Build Quality / Systems Practice** by
asking for all four at once — validate, debug, compose, optimize — on a premise
nobody supplied. The difficulty is ownership and integration, not a new
programming concept.

## Milestone B purpose, and the S26 boundary

Say this out loud at 0:00 and again at 0:45:

> S25 proves: **I can independently build and explain a small working system.**
> S26 begins: **I can design my own larger capstone.**

S25 is deliberately small and finished. Do not let a student start designing the
capstone today, and do not accept capstone ambition as a reason to leave the
prototype unplayable. The scope question for the whole session is "what can you
finish?", not "what could this become?".

## Acceptance criteria — show these on screen at 0:00

| # | Criterion | Evidence |
|---:|---|---|
| 1 | **Plan** — premise, two mechanics, player action, expected result | `milestone.yaml` `plan:` |
| 2 | **Build** — sources produce the intended package deterministically | milestone checker |
| 3 | **Validate** — real package validation passes | `explore-package validate` |
| 4 | **Play** — loads, plans, and launches in Trail | Trail |
| 5 | **Compose** — two supported mechanics coexist meaningfully | milestone checker |
| 6 | **Debug** — one concrete problem and the change that fixed it | `milestone.yaml` |
| 7 | **Explain** — one design decision and one technical decision | `milestone.yaml` |

All seven, or the milestone is incomplete. "Meaningfully" in criterion 5 means
the two mechanics belong to one player experience: a character reads the second
mechanic, or the second mechanic sits on a route object so one player action
feeds both. Two examples copied side by side do not pass, and the checker says
so in those words.

## Before class

- Confirm the shared Quick Start, Python environment, package validator, Trail
  controls, Git identity, accessibility choices, and screen-sharing fallback.
- Keep `student/fixtures.py` unchanged so all five pipeline cases stay
  comparable.
- Confirm `student/project_catalog.py`, `student/milestone.yaml`, and
  `student/explorer-package/` are the learner's editable sources, and that they
  are visibly separate from the fixed fixtures.
- Run the milestone checker once on a clean copy. It is red by design and every
  message names a decision the student has not made yet. Show that output at
  0:00 so nobody reads red as broken.
- Validate the teacher-only `student/recovery-package` and prepare its text-only
  walkthrough without presenting it as completed student work.
- Present Stormlight Rescue Trail as a teacher exemplar, not a required premise.
- Remind students that Python stays local and emits a preview; only reviewed,
  validated declarative YAML enters the existing Trail.
- A student may prepare a premise before class. The plan, predictions, package
  authoring, validation, play, debugging, and reflection remain session work.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 5 min | Frame Milestone B, show the seven acceptance criteria and the red checker. | Students can name what "done" means. |
| 0:05–0:10 | 5 min | Gate authoring on a written plan: premise, two mechanics, where mechanic two sits, player action, expected result. | `milestone.yaml` `plan:` complete; four predictions recorded. |
| 0:10–0:25 | 15 min | Author catalog, pipeline functions, and package, including the second mechanic and the character that reads it. | Replaced placeholders; completed TODO functions; new contribution in the manifest. |
| 0:25–0:32 | 7 min | Focused checks, package validation, deterministic export. | Pipeline output, `valid:` line, `sha256:` digest pasted into `evidence:`. |
| 0:32–0:38 | 6 min | Trail launch and play; correct order, wrong-member reset, second keeper in both states. | Observed payoff and observed reset. |
| 0:38–0:42 | 4 min | Debug one real problem with observe → hypothesis → one change → rerun; use the bounded fallback only if nothing broke. | Named problem and the one change; checker re-run. |
| 0:42–0:45 | 3 min | Reflection and milestone evidence; Git close if the class is Git-managed. | `reflection:` complete; six-item evidence bundle. |

Pacing note: the plan gate at 0:10 is the one that protects the session. A
student who has not chosen a second mechanic by 0:10 will not finish. Choose for
them from the menu if you must — the *placement* decision is the one worth
protecting, not the menu pick.

## Student-owned decisions — and what you must not decide for them

Own it yourself only when the clock forces it, and say so when you do.

| Decision | Teacher may supply under time pressure? |
|---|---|
| Premise and theme | No |
| Object and character names | No |
| Player-facing messages | No |
| Which second mechanic | Yes, from the menu, after 0:10 |
| Where the second mechanic sits | Prefer no; it is the design decision |
| Mechanic parameter or goal | Yes, a default goal of 3 is fine |
| Reflection text | No |

## Likely failure modes and recovery

| Symptom | Cause | Recovery |
|---|---|---|
| `color cannot be combined with toggle` | A `toggle:` block was added but `color:` was left in place. | Delete the object's `color:` line; the toggle supplies both colors. |
| `must reference a world object with counter metadata` | The second keeper's `object_id` points at an object that has no `counter:`. | Point it at the object that carries the mechanic, or add the counter. |
| `must resolve exactly once within this package` | A contribution failed to load, so every reference to it dangles. | Fix the first diagnostic; the dangling references usually clear with it. |
| `goal must be from 2 through 5` | Counter goal out of range. | Choose 2–5. The bound is a runtime contract, not a style rule. |
| Route resets unexpectedly while playing | The player touched a route object out of turn — including a second tap on a route object that carries the counter. | This is correct M15 behavior. Use it: it is the best available "explain a design decision" moment. |
| Checker still red after authoring | A placeholder survives somewhere. | The failure names the exact file and field. Read it rather than hunting. |
| `test_pipeline.py` red | The four TODO functions are incomplete. | Expected until the student finishes them; not a package problem. |
| Pasted digest does not match | The package changed after the digest was pasted. | Re-export and paste again; the failure prints the current digest. |

## Degraded mode if Trail will not launch

Criterion 4 can be satisfied without a working display. In order of preference:

1. The student runs `explore-package trail` on their own machine.
2. The teacher launches the student's package on the shared screen and the
   student calls the moves aloud.
3. Text-only: the student traces first → second → third stop and states the
   keeper's response, then states what the second keeper says below and at goal.
   Pair this with a green `test_package_loads_and_plans_for_trail`, which proves
   the package really plans for Trail even when nothing can be drawn.

Record which mode was used. A text-only trace with a green plan check is an
acceptable Milestone B; a missing package is not.

## Teacher cut line

Protect, in order: a valid authored prototype; two mechanics that mean something
together; validation and build evidence; a brief reflection.

- At 0:25, stop adding objects and polish.
- At 0:32, if the package is not valid, move the student to the bounded
  debugging exercise instead of new authoring.
- At 0:38, defer optional behavior and shorten messages.
- Cut in this order: object count, prose length, Trail launch (teacher demos it),
  Git close (a delayed commit may finish after class).
- Never cut to one mechanic. The two-mechanic composition is the milestone.

## Deliberate debugging exercise

Real problems are common today and are preferred. Do not manufacture one for
every student, and do not treat a smooth build as a failure to debug.

If a student genuinely hits nothing, use the one bounded fallback: point the
second keeper's `object_id` at a route object that carries no counter or toggle,
run the validator, read the diagnostic aloud — it names the file, the field, and
the rule — then restore the correct ID and rerun. The recorded evidence is what
the validator refused and why.

The five fixed `fixtures.py` cases remain available for pipeline practice:
normal valid catalog, exactly-three boundary, absent required ID, malformed
coordinate/type, and a stable-order regression with equal `route_order` values.
Invalid data must raise before `transform_preview`.

## Expected output and behavior

The starter package is **healthy and valid** but entirely unowned: every
authored string is `CHOOSE-ME`, and it declares one mechanic. This is
deliberate. Red checker output at 0:00 means "decisions outstanding", not
"broken download", and the three classes of failure are named in the checker's
own docstring:

- decisions not yet made (`test_plan_*`, `test_*_is_authored`, `test_reflection_*`);
- an invalid package (`test_package_validates`, `test_package_loads_and_plans`);
- missing composition or build evidence (`test_two_supported_mechanics`,
  `test_second_mechanic_is_wired`, `test_build_is_deterministic`).

The fixed fixtures remain the independent source for the five intentionally-red
pipeline tests in `test_pipeline.py`.

For the teacher recovery exemplar, enabled filtering followed by required-ID
search finds exactly `harbor-drum`, `north-lantern`, and `summit-flare`. Stable
sorting produces that order and the total signal power is 12. The preview
contains exactly three current-contract world-object documents and the fixed
three-ID keeper sequence.

The recovery package validates and plans with Nova using existing package and
Trail behavior, and it now demonstrates the same two-mechanic shape students are
asked for: the M15 route, plus a counter on `summit-flare` that the Flare
Watcher reads with `respond_to_counter`. Harbor Drum → North Lantern → Summit
Flare completes the route and leaves the counter at 1 of 2; one more tap on
Summit Flare reaches the goal without disturbing the finished route, because a
completed sequence no longer resets. Harbor Drum → Summit Flare resets progress
to zero without immediately treating Summit Flare as step one. No Python,
catalog-only fields, or new behavior enters the runtime.

## Supported mechanics only

Every mechanic S25 uses already exists in the current contracts. Nothing here
extends the engine or the package schema:

- ordered three-object sequences (`respond_to_sequence`);
- counters (`counter`, `respond_to_counter`) — counters increment only, goals
  are whole numbers from 2 through 5;
- toggles (`toggle`, `toggle_style_id`, `respond_to_toggle`,
  `respond_to_two_toggles`, `respond_to_either_toggle`) — toggle state is a
  changed/current flag, not a state machine;
- dialogue (`greeting`, `conversation`).

There is no persistence across sessions, no inventory, no collision or physical
locking, no currency, health, or general score, no arbitrary variable store, and
no cross-package semantic reference. If a student's premise needs one of those,
the fix is the wording of the premise, not the engine. One character carries at
most one response mechanic, so a second mechanic needs a second character.

## Milestone evidence

Six items, all produced by work the student already did:

1. `milestone.yaml` plan;
2. authored `project_catalog.py` and `explorer-package/`;
3. green `test_milestone.py` output;
4. the `explore-package validate` PASS line;
5. the deterministic build digest from `explore-package export`;
6. `milestone.yaml` reflection.

There is no submission system. Review the six items in front of the student.

## Project-primary structure and runtime boundary

Use this reusable S25 structure for later project-primary lessons without adding
S26–S30 materials now: teacher runbook; task card; persistent project record;
machine-checkable milestone plan/reflection; editable catalog; runnable
incomplete scaffold; fixed fixtures; focused intentionally-red learner tests;
milestone checker; editable student Explorer Package; separate teacher-only
recovery exemplar; milestone evidence; AI receipt; Git close; and support,
extension, and cut-line guidance.

The ownership chain is: student premise → editable catalog → completed local
pipeline → reviewed selected/ordered values → student package YAML → validation
→ deterministic build → visible M15 world. Local Python helps students reason,
transform, and validate. Validated package YAML drives the world. The shared
runtime never executes student Python.

## Recovery-package boundary

`student/recovery-package/` is a teacher-only fallback that preserves a playable
demonstration when a student is blocked. Using it does not complete the
student-owned project artifact. The student must later finish their own editable
catalog and `student/explorer-package/`. Even under recovery, the student still
provides all predictions and explains at least one completed pipeline function.

## Bounded AI assistance

Use the canonical receipt: intent; prediction; exact bounded question;
suggestion tested; accepted/rejected change; student explanation. AI may ask or
answer one bounded scope-critique question only, such as “Which part could be
deferred?” AI cannot invent the premise, acceptance criteria, pipeline, function
bodies, route solution, or test answers. Enforce the whole-file ban.

## Git close

**ZIP classes:** Skip this step for classes still on the ZIP distribution that have not started the Git lesson yet; use it once the class has a Git-managed course folder. See [Student Quick Start → Later: Git](../student-quick-start.md#later-git-optional-teacher-managed).

The repository history must keep planning separate from implementation. The plan
commit comes first; the prototype code, package, and evidence use a second
descriptive commit. Students still perform status, diff, intentional staging,
staged diff, and commit for their own change. Explain `M`, `??`, no output,
identity recovery, and Control-C cancel/correct/retry. Reflection comes before
the commit; a delayed commit may finish after class.

## Optional extension

Add one enabled or disabled non-route fourth station, then prove the required
selection and the fixed three-step M15 sequence do not change. Do not add a
fourth sequence member. Renaming the scaffolding IDs to match the premise is the
other extension; the object file, the manifest entry, and the keeper's sequence
must be renamed together.

## Teacher notes and answer key

- Recovery selected IDs/order: `harbor-drum`, `north-lantern`, `summit-flare`.
- Recovery total power: `3 + 4 + 5 = 12`.
- Boundary: exactly three valid enabled records succeeds.
- Absent: `select_route` raises `ValueError` naming the absent ID before preview.
- Malformed: a text coordinate is rejected by `validate_station` before preview.
- Regression: equal order records stay in their selected/search order because
  Python's `sorted` is stable; do not add an ID tie-breaker.
- A complete pipeline solution validates every station before filtering, searches
  only enabled records, checks the selected count is exactly three, sums power,
  makes a sorted copy, and transforms only after all earlier gates succeed.
- The cheapest complete second mechanic is a `counter:` block on one route object
  plus one new character with `respond_to_counter`: one new file and one manifest
  line.
- Reflection answers must name one design decision and one technical/debugging
  decision. "It worked" is not a debugging decision.
