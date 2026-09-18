# S24 — Fast Ranger Index

**Role:** Python-primary software fluency

**World reuse:** M15 `complete-actions-in-order`

**Learning objective:** Students can compare repeated linear scans with one
ID→record dictionary by counting inspections, defining duplicate failure, and
proving equivalent ordered results — and can improve working code for clarity,
duplication, naming, or player-facing text while proving with recorded evidence
that its behavior is unchanged.

**Student-owned action:** The student records `behavior_signature()`, names one
improvement, rewrites the copy-pasted `route_briefing`, and shows the signature
is identical afterwards.

**Prerequisite:** S16–S23 lists/dictionaries, searching, validation, and tests.

**Arc note:** Final session of the **S21–S24 Build Quality / Systems Practice**
mini-arc, and the last step before S25 Milestone B. In this arc "optimize" means
clarity, maintainability, determinism, and player experience — not speed. The
only cost claim the session makes is counted record inspections, because that is
the only quantity it measures. Do not let "faster" enter the room: nothing here
is timed, so nothing here can be called faster.

## Before class

- Confirm Quick Start repository/venv/package command, Trail focus/controls,
  screen sharing, Git identity, accessibility, and low-bandwidth route.
- Prepare paper/tally versions of the 6- and 12-record catalogs.
- Validate the M15 package and paste complete commands in chat.
- Do not introduce timing benchmarks or Big-O terminology as requirements.
- Run `starter.py` once and read `route_briefing` aloud so the duplication is
  obvious before anyone edits. Keep a clean copy for shared machines.
- Decide in advance how students will record their signature — chat message,
  comment, or a scratch file. The recording must exist before the edit.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:04 | 3–4 min | Hook: help rangers stop rereading the whole clue catalog. | Names repeated work. |
| 0:04–0:10 | 5–6 min | Trace small counts; ask what doubling changes. | Two count predictions. |
| 0:10–0:28 | 16–18 min | Run scans/index; assert equivalence and duplicate failure. | Counts and passing tests. |
| 0:28–0:35 | 6–7 min | Validate/play the resolved M15 route. | Three IDs visited in order. |
| 0:35–0:42 | 6–7 min | Record signature, improve `route_briefing`, prove it unchanged; reorder `ROUTE` to show a failed proof. | Named improvement; identical signature; one "did not claim" sentence. |
| 0:42–0:45 | 2–3 min | Inspect code+tests; commit or schedule. | Descriptive Git close. |

**Teacher cut line:** At 0:28, stop optional missing-ID work. At 0:35, accept
validator PASS plus a teacher M15 demonstration. At 0:40, if the improvement is
unfinished, accept renaming `r0`/`t0`/`out` alone — a smaller honest improvement
with a matching signature beats a larger one without evidence. Protect both count
predictions, equivalence, duplicate failure, and the before/after signature. The
recorded-before-editing signature is this session's ownership evidence and is cut
last. Git may finish asynchronously.

## Student task and prediction

Require hand-counted 6 and 12 predictions before execution. Ask “what happens
when data doubles?” and request a sentence about repeated work, not vocabulary.

## Deliberate debugging exercise

Use duplicate IDs to require `ValueError`, a missing ID to check aligned `None`,
and an accidental set/sort conversion to expose route-order loss.

For the improvement step, reorder `ROUTE` and rerun `behavior_signature()`. The
comparison fails. Make the point explicitly: this is what a refactor that
silently changed behavior looks like, and the only reason anyone noticed is that
the signature was recorded *before* the edit.

## Expected output and behavior

Observable evidence for this session:

- Small comparison is `(15, 6, [...])`; larger is `(33, 12, [...])`. Both
  methods return identical ordered records.
- Duplicate index construction fails closed with `ValueError`.
- `starter.py` prints the three briefing lines in route order.
- The student's recorded `behavior_signature()` exists **before** any edit to
  `route_briefing`.
- After the improvement, `route_briefing` is one loop over `ROUTE` with readable
  names, and `behavior_signature()` equals the recorded value exactly.
- The student states one thing their improvement did not claim — most often
  "this is not faster, I did not measure time."
- The package validates and M15 completes Signal Map → River Token →
  Summit Bell.

## Likely failure modes and recovery

| Failure mode | What you will see | Recovery |
|---|---|---|
| Signature recorded after the edit | Comparison trivially passes and proves nothing | Revert with `git diff`/the clean copy, record first, redo the edit |
| Student claims the code is now faster | An unmeasured performance claim | Ask what was timed; nothing was, so the claim comes out |
| Improvement changes the briefing wording | Signature differs on the third element | Wording changes are a content change, not a refactor; revert or record a new signature deliberately and say so |
| Improvement reorders the output | Signature differs; M15 route intent lost | Order is behavior here; restore `ROUTE` order |
| Student rewrites `compare`/`build_id_index` too | Several changes at once, no isolated evidence | One improvement per signature comparison |
| Student adds a class or a new module | Scope creep past a 45-minute session | The fixture is six lines; the improvement is smaller than the original |

## Bounded AI assistance

Use the canonical workflow. AI may ask one comparison question after predictions;
it may not calculate the table, generate a generalized algorithm, rewrite
`route_briefing`, or choose the student's improvement.

## Git close

**ZIP classes:** Skip this step for classes still on the ZIP distribution that have not started the Git lesson yet; use it once the class has a Git-managed course folder. See [Student Quick Start → Later: Git](../student-quick-start.md#later-git-optional-teacher-managed).

Use status, diff, intentional stage, `git diff --staged`, and a descriptive
code-with-tests commit. Interpret `M`, `??`, no output, identity failure, and
cancel/retry. Understanding takes priority over a rushed commit.

## Optional extension

Move targets earlier and explain changed scan counts without formal notation.
Or improve one `when_near`/`when_interacted` line in the package for clarity and
confirm the M15 route still completes in the same order — the same rule applied
to player-facing text.

## Teacher notes and answer key

- Size 6 targets positions 4+5+6 = 15; one index build = 6.
- Size 12 targets positions 10+11+12 = 33; one index build = 12.
- Doubling increases the one-time build proportionally; repeated late searches
  redo much more inspection work. This is a statement about counted
  inspections, not about elapsed time.
- Equality must preserve list order. Duplicate IDs raise before use.
- This local dictionary never becomes a Trail cache or package field.
- Expected `route_briefing` improvement:

  ```python
  def route_briefing():
      return [f"Visit {stop['name']} {stop['position']}." for stop in ROUTE]
  ```

  A plain `for` loop with an appended f-string is equally correct. Both remove
  the duplication and both leave `behavior_signature()` identical.
- No engine, schema, mission, or package-contract change occurs in this session.
  The improvement is entirely inside local student Python, plus optional
  player-facing text in the existing package fields.
