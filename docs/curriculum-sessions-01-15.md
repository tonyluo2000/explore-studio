# Explore Studio — Sessions 01–15 Curriculum

> **Status:** Canonical first-half curriculum for the 30-session course.

Sessions 01–15 integrate real Python practice with the implemented Missions
01–15 declarative world-building foundation. Mission IDs, mission definitions,
Explorer Package v0.2, Student API v0.1, and Classroom Trail v0.11 remain
unchanged. Mission 13 is taught immediately after Mission 09 without renumbering
either mission.

## Session rhythm

Every 45-minute online session uses the same bounded rhythm:

| Time | Activity |
|---:|---|
| 5 minutes | Creative hook |
| 7 minutes | Concept introduction and prediction |
| 12 minutes | Python activity |
| 13 minutes | Explorer Package and world activity |
| 5 minutes | Test and debug |
| 3 minutes | Review and descriptive Git commit |

Early Python activities should remain approximately 5–10 lines. Later
activities may grow toward 15–25 lines as students learn to decompose a problem.

## Canonical session mapping

| Session | Catalog mission | Title | Emphasis |
|---|---|---|---|
| S01 | M01 `visit-all-classroom-objects` | Explore Every Object | Balanced |
| S02 | M02 `create-a-classroom-object` | Create Your First Object | Balanced |
| S03 | M03 `make-your-object-respond` | Make It Respond | Balanced |
| S04 | M04 `introduce-your-character` | Give Your Character a Voice | Balanced |
| S05 | M05 `write-a-short-conversation` | Write a Conversation | Balanced |
| S06 | M06 `build-an-object-collection` | Build a Curious Collection | **Python-primary** |
| S07 | M07 `toggle-an-object-state` | Flip a Magic Switch | Balanced |
| S08 | M08 `respond-to-object-state` | Make an If/Else Character | Balanced |
| S09 | M09 `count-object-interactions` | Power It Up | Balanced |
| S10 | M13 `compare-a-counter-to-its-goal` | Check the Power Level | **Python-primary** |
| S11 | M10 `require-all-switches-on` | Unlock the Secret | **Python-primary** |
| S12 | M11 `open-with-either-switch` | Either Switch Opens It | **Python-primary** |
| S13 | M12 `invert-a-switch-condition` | Turn the Rule Around | **Python-primary** |
| S14 | M14 `reuse-a-named-toggle-style` | Share a Switch Style | Balanced |
| S15 | M15 `complete-actions-in-order` | Solve the Secret Sequence | **Python-primary** |

This teaching order is deliberate: the Mission 13 comparison follows the
Mission 09 counter that supplies its values, then students compose Boolean
conditions with AND, OR, and NOT. Stable mission numbers and IDs do not change.

## Session plans

### S01 — Explorer's Field Notes

- **Creative goal:** Tour the shared world and record three discoveries.
- **Programming concept:** `print`, literals, and string values.
- **Python activity:** Print three short observations about objects in the world.
- **World activity:** Complete M01 by interacting with every classroom object.
- **Prediction:** Identify which visible things should count toward completion.
- **Test/debug:** Compare predicted and observed interactions; repair one quoting
  or syntax error in the Python notes.
- **Bounded AI role:** Explain an error only after the student predicts its cause.
- **Prerequisite:** Basic typing and file navigation.

### S02 — Place Your First Prop

- **Creative goal:** Add a personally themed prop to the world.
- **Programming concept:** Variables and basic string and integer types.
- **Python activity:** Store and print the object's name, x/y coordinates, and
  color using clearly named variables.
- **World activity:** Complete M02 by authoring the matching package object.
- **Prediction:** Sketch or describe where the coordinates will place the object.
- **Test/debug:** Validate, run, and adjust one coordinate based on observation.
- **Bounded AI role:** Review variable names after the student explains each one.
- **Prerequisite:** S01 literals and output.

### S03 — Make the World React

- **Creative goal:** Give the prop a surprising nearby clue and interaction line.
- **Programming concept:** String composition and f-strings.
- **Python activity:** Build both messages from an object-name variable.
- **World activity:** Complete M03 with `when_near` and `when_interacted` text.
- **Prediction:** State which player action should reveal each message.
- **Test/debug:** Exercise proximity and interaction separately; fix blank,
  misplaced, or malformed text.
- **Bounded AI role:** Suggest revisions only after the student writes both lines.
- **Prerequisite:** S02 variables and strings.

### S04 — Introduce a Character

- **Creative goal:** Give an original character a recognizable voice.
- **Programming concept:** Function definitions and parameters.
- **Python activity:** Define and call a small `greet(name)` function with two
  different names.
- **World activity:** Complete M04 by authoring the character greeting.
- **Prediction:** Write the exact output expected from both function calls.
- **Test/debug:** Read and repair an indentation, spelling, or argument error.
- **Bounded AI role:** Explain the traceback while leaving the correction to the
  student.
- **Prerequisite:** S03 strings and function-call syntax.

### S05 — Script a Conversation

- **Creative goal:** Write a short exchange with a beginning and ending.
- **Programming concept:** Lists, order, indexing, and length.
- **Python activity:** Store 2–3 dialogue lines in a list and inspect individual
  entries and `len(...)`.
- **World activity:** Complete M05 with the ordered conversation lines.
- **Prediction:** Identify the first line, final line, and what happens after it.
- **Test/debug:** Find an ordering or indexing mistake and verify the final line.
- **Bounded AI role:** Check clarity but never author the conversation.
- **Prerequisite:** S04 functions and authored character text.
- **Self-review:** Name one creative choice, one Python change, and one test run.

### S06 — Build a Themed Collection

**Python-primary.**

- **Creative goal:** Populate the world with three related objects that tell a
  small environmental story.
- **Programming concept:** Dictionaries, lists of data, and `for` loops.
- **Python activity:** Represent three objects as dictionaries and loop over the
  collection to print a design inventory.
- **World activity:** Complete M06 by authoring the corresponding three objects.
- **Prediction:** Identify duplicate names, coordinates, or missing properties
  before validation.
- **Test/debug:** Validate the package and correct one deliberately malformed
  dictionary or package entry.
- **Bounded AI role:** Explain one loop iteration at a time after the student
  traces the first iteration.
- **Prerequisite:** S05 lists and S02 object properties.

### S07 — Create a Two-State Prop

- **Creative goal:** Create a switch, lamp, portal, or other object with two
  visually distinct states.
- **Programming concept:** Boolean values and changing state.
- **Python activity:** Assign and print `False` and `True` states with matching
  labels or colors.
- **World activity:** Complete M07 using the existing inline toggle model.
- **Prediction:** Trace state and color across several interactions.
- **Test/debug:** Confirm both colors appear and repeated interactions alternate.
- **Bounded AI role:** Check the student's state trace, not generate the object.
- **Prerequisite:** S02 types and S06 object authoring.

### S08 — Build an If/Else Guardian

- **Creative goal:** Make an NPC react differently to the prop's current state.
- **Programming concept:** `if`/`else` branching.
- **Python activity:** Select and print one of two responses from a Boolean value.
- **World activity:** Complete M08 by linking an NPC to the toggle and authoring
  both responses.
- **Prediction:** Predict both branches before running either case.
- **Test/debug:** Display each branch and reconcile output with the prediction.
- **Bounded AI role:** Compare prediction and result after the student explains
  the condition in plain language.
- **Prerequisite:** S07 Boolean state and S04 character authoring.

### S09 — Power Up a Device

- **Creative goal:** Turn repeated interactions into a visible charging story.
- **Programming concept:** Integer counters, updates, and simple loops.
- **Python activity:** Increment a count toward a goal and print every step.
- **World activity:** Complete M09 with a bounded goal and goal-reached message.
- **Prediction:** Identify the exact interaction on which success should appear.
- **Test/debug:** Diagnose an off-by-one example and add a basic assertion.
- **Bounded AI role:** Suggest one boundary case after the student's prediction.
- **Prerequisite:** S06 loops and S02 integer values.

### S10 — Check the Boundary

**Python-primary.**

- **Creative goal:** Make an NPC judge whether the device has enough power.
- **Programming concept:** `>=`, function return values, and boundary cases.
- **Python activity:** Define `at_goal(count, goal)` and test goal minus one, the
  exact goal, and goal plus one.
- **World activity:** Complete M13 with below-goal and at-or-above responses.
- **Prediction:** Complete the three boundary results before running the code.
- **Test/debug:** Use assertions to verify all three cases.
- **Bounded AI role:** Propose one additional edge case that the student must
  explain before using.
- **Prerequisite:** S09 counters and S04 functions.
- **Self-review:** Name one creative choice, one Python change, and one test run.

### S11 — Require Both Keys

**Python-primary.**

- **Creative goal:** Build a lock that opens only when two switches are on.
- **Programming concept:** Boolean `and`.
- **Python activity:** Define a two-parameter Boolean function and print its four
  truth-table cases.
- **World activity:** Complete M10 with the existing two-toggle AND response.
- **Prediction:** Fill the complete truth table before running it.
- **Test/debug:** Verify that only the both-on case succeeds.
- **Bounded AI role:** Review the completed truth table and flag one discrepancy.
- **Prerequisite:** S08 conditionals and S07 Boolean state.

### S12 — Allow Either Key

**Python-primary.**

- **Creative goal:** Create an alternate-route lock opened by either switch.
- **Programming concept:** Boolean `or`.
- **Python activity:** Reuse the two-parameter function shape with `or` and print
  all four cases.
- **World activity:** Complete M11 with the fixed either-toggle behavior.
- **Prediction:** Contrast every result with the S11 AND table.
- **Test/debug:** Verify both-off, first-only, second-only, and both-on behavior.
- **Bounded AI role:** Explain one student-selected AND/OR mismatch.
- **Prerequisite:** S11 truth tables and Boolean parameters.

### S13 — Turn the Rule Around

**Python-primary.**

- **Creative goal:** Make the special response happen while a switch is off.
- **Programming concept:** Boolean `not`.
- **Python activity:** Define a function that returns `not is_on` and test both
  Boolean inputs.
- **World activity:** Complete M12 using the existing one-toggle response model.
- **Prediction:** Fill the two-row truth table before running it.
- **Test/debug:** Explain why swapping authored responses models this lesson but
  does not introduce general negation syntax into the package.
- **Bounded AI role:** Challenge the student's explanation with one counterexample.
- **Prerequisite:** S08 conditionals and S11–S12 Boolean operators.

### S14 — Refactor a Shared Look

- **Creative goal:** Give multiple switches a recognizable shared visual style.
- **Programming concept:** Reusable named data, parameters, and decomposition.
- **Python activity:** Pass one style dictionary into two calls to a small
  object-description function.
- **World activity:** Complete M14 with exactly one named toggle style referenced
  by at least two objects.
- **Prediction:** Identify which objects should share each color change.
- **Test/debug:** Find an inline/reference conflict, duplicate style, or invalid
  reuse count using package validation.
- **Bounded AI role:** Identify duplicated data only after the student marks it.
- **Prerequisite:** S06 dictionaries, S07 toggles, and S04 functions.
- **Capstone bridge:** Optionally sketch the three-object story for S15; formal
  Mission 15 work remains in S15.

### S15 — Ship a Secret Sequence

**Python-primary.**

- **Creative goal:** Deliver a three-object puzzle with a clear story and payoff.
- **Programming concept:** Ordered data, functions, loops, decomposition,
  assertions, and systematic debugging.
- **Python activity:** Write small functions that check three distinct object IDs
  and compare expected and attempted order, then test them with assertions.
- **World activity:** Complete M15 using ordinary, toggle, and counter objects as
  desired, then validate the final package.
- **Prediction:** Trace the correct order, wrong authored members at each step,
  an unrelated object, and a completed sequence.
- **Test/debug:** Run those cases, read any validation errors, revise, and rerun.
- **Bounded AI role:** Suggest tests only; the student traces and explains every
  accepted line before committing it.
- **Prerequisite:** All earlier object, character, state, collection, function,
  Boolean, and testing work.
- **Self-review:** Name the creative intent, explain the decomposition, show the
  test evidence, and describe one revision.

## Python progression

The integrated strand progresses through:

`syntax and strings → variables and types → functions → lists, dictionaries,
and loops → state → conditionals → counters → comparisons → AND, OR, and NOT →
reuse → decomposition and testing`

Python is primary in S06, S10, S11, S12, S13, and S15. In those sessions the
package task applies and visualizes reasoning developed first in Python. In
other sessions, Python and package authoring share the session.

Student Python runs locally only. It may generate, transform, or validate
declarative package data, but it is never imported or executed by the shared
runtime. The validated Explorer Package remains the deterministic shared
artifact.

## AI pattern

Optional AI assistance always follows this sequence:

`explain intent → predict → ask one bounded question → test → revise → explain
accepted code`

AI may clarify an error, review names, compare predicted and observed behavior,
or suggest an edge case. It does not choose the creative premise or replace
truth-table, state-trace, testing, or debugging work. A student accepts AI code
only when they can explain what every line does and show the test that supports
it.

## Git and review pattern

Every session ends with:

`status → diff → descriptive commit`

The student checks which files changed, reads the relevant diff, and writes one
commit message describing the learning outcome. Sessions 05, 10, and 15 add a
self-review naming one creative decision, one Python change, and one test or
revision. Git records the work without becoming the subject of the course.

## Session 15 capstone outcome

By the end of S15, each student has a validated deterministic Explorer Package
that demonstrates authored identity and story text, an object collection,
stateful objects, counter logic, Boolean responses, reusable named style data,
and a fixed secret sequence. A companion local Python program generates,
transforms, or validates selected data and contains student-authored assertions.
The student can explain the package references, trace the sequence and Boolean
behavior, interpret validation failures, and justify accepted AI assistance.

## Scope boundary

This document defines the first half of the approved 30-session course. It does
not design Sessions 16–30. It adds no runtime behavior, package schema, Student
API, Trail contract, mission definition, persistence, teacher control,
authentication, deployment, or Phase E work. The deployment decision remains
parked.
