# S25 — Playable Prototype

**Role:** Project-primary production lesson

**Reference teacher exemplar:** Stormlight Rescue Trail

**World reuse:** M15 `complete-actions-in-order`

**Learning objective:** Students can define an observable vertical slice, predict
its valid and invalid paths, and complete a local Python data pipeline that maps
exactly three chosen route records into one validated, playable M15 adventure.

**Prerequisite:** S16–S24 nested data, validation, search/filter/count,
aggregation, stable sorting, transformation, testing, package validation, and Git.

## Before class

- Confirm the shared Quick Start, Python environment, package validator, Trail
  controls, Git identity, accessibility choices, and screen-sharing fallback.
- Keep `student/fixtures.py` unchanged so all five cases remain comparable.
- Validate `student/recovery-package` and prepare its text-only walkthrough.
- Present Stormlight Rescue Trail as a teacher exemplar, not a required premise.
  Students choose their own place, purpose, station names, object text, and keeper.
- Remind students that Python stays local and emits a preview; only reviewed,
  validated declarative YAML enters the existing Trail.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 4 min | State the vertical-slice goal; students name their premise and visitor payoff. | Creative choice plus 3–5 observable acceptance criteria. |
| 0:04–0:09 | 5 min | Gate execution on four written predictions. | Visitor path, invalid-data path, selected IDs/order, and total power. |
| 0:09–0:31 | 22 min | Complete the four student-owned functions and run the five focused cases. | Validation → filter → search → count → aggregate → stable sort → preview output. |
| 0:31–0:38 | 7 min | Validate and play the three-object recovery package, or the student's reviewed package. | Correct order completes M15; wrong authored member resets. |
| 0:38–0:42 | 4 min | Review tests, package output, criteria, and milestone evidence. | Five-case results and self-review. |
| 0:42–0:45 | 3 min | Use status → diff → staged diff → descriptive commit. | Reviewable prototype commit. |

**Teacher cut line:** Protect one validated, playable three-object vertical slice.
At 0:31 stop adding fields or objects and use the recovery package if needed. At
0:38 defer polish and optional station behavior. Preserve predictions, one
Python change, five-case test evidence, package validation, M15 play, self-review,
and Git understanding; a delayed commit may finish after class.

## Student task and prediction

Do not run Python until the student records: the visitor path; whether malformed
data reaches preview/package generation; the three expected selected IDs in
route order; and the expected total `signal_power`. Ask the student to point to
the stage responsible for each prediction.

Students write 3–5 observable acceptance criteria for their own premise. Keep
them visitor-visible or command-visible and achievable in this session. The
teacher may ask, “Which criterion could be deferred?” but does not author the
criteria.

## Deliberate debugging exercise

Use the five named fixtures without changing them: normal valid catalog,
exactly-three boundary, absent required ID, malformed coordinate/type, and a
stable-order regression with equal `route_order` values. Confirm invalid data
raises before `transform_preview`. Confirm an absent required ID also fails
closed. In the regression, stable sorting preserves the earlier selected record.

## Expected output and behavior

For the teacher exemplar, enabled filtering followed by required-ID search finds
exactly `harbor-drum`, `north-lantern`, and `summit-flare`. Stable sorting produces
that order and the total signal power is 12. The preview contains exactly three
current-contract world-object documents and the fixed three-ID keeper sequence.

The recovery package validates and plans with Nova using existing package and
Trail behavior. In M15, Harbor Drum → North Lantern → Summit Flare completes;
Harbor Drum → Summit Flare resets progress to zero without immediately treating
Summit Flare as step one. No Python, catalog-only fields, or new behavior enters
the runtime.

## Teacher exemplar acceptance criteria

1. Malformed station data fails before package generation.
2. Enabled stations are filtered and exactly three required IDs are found.
3. Selected stations are stably sorted by `route_order`.
4. Total `signal_power` is reported.
5. A valid package completes M15 only in the correct order.

These are the Stormlight exemplar criteria. Students must write 3–5 observable
criteria for their own premise rather than copying its names or content.

## Bounded AI assistance

Use the canonical receipt: intent; prediction; exact bounded question;
suggestion tested; accepted/rejected change; student explanation. AI may ask or
answer one bounded scope-critique question only, such as “Which criterion could
be deferred?” AI cannot invent the premise, acceptance criteria, pipeline,
function bodies, route solution, or test answers. Enforce the whole-file ban.

## Git close

The repository history must keep planning separate from implementation. The
lesson plan/task card commit comes first; the prototype code, fixtures, tests,
and package use a second descriptive commit. Students still perform status,
diff, intentional staging, staged diff, and commit for their own change. Explain
`M`, `??`, no output, identity recovery, and Control-C cancel/correct/retry.

## Support path

Use `EXACTLY_THREE_CATALOG`, the transformation scaffold, and the validated
`recovery-package`. The teacher can demonstrate the Trail as a spoken or
text-only trace: Harbor Drum → North Lantern → Summit Flare → keeper response.
The student still owns predictions and explains one completed function.

## Optional extension

Add one enabled or disabled non-route fourth station, then prove the required
selection and the fixed three-step M15 sequence do not change. Do not add a
fourth sequence member.

## Teacher notes and answer key

- Normal selected IDs/order: `harbor-drum`, `north-lantern`, `summit-flare`.
- Normal total power: `3 + 4 + 5 = 12`.
- Boundary: exactly three valid enabled records succeeds.
- Absent: `select_route` raises `ValueError` naming the absent ID before preview.
- Malformed: a text coordinate is rejected by `validate_station` before preview.
- Regression: equal order records stay in their selected/search order because
  Python's `sorted` is stable; do not add an ID tie-breaker.
- A complete solution validates every station before filtering, searches only
  enabled records, checks the selected count is exactly three, sums power, makes
  a sorted copy, and transforms only after all earlier gates succeed.
- Self-review answers must name: creative choice; Python change; test run; and
  one deliberately deferred item that kept the slice bounded.
