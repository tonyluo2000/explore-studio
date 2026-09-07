# S15 Task Card — Ship a Secret Sequence

**Mission:** M15 `complete-actions-in-order` — Solve the Secret Sequence

**Learning target:** Build and test small helpers for exactly three distinct IDs
and attempted order, then ship a three-object first-half capstone puzzle.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## Predict and trace before running

Expected authored order: `star-map`, `moon-switch`, `echo-drum`. Start at 0 and
write progress after every interaction.

```text
Correct: star-map → moon-switch → echo-drum       0 → __ → __ → __
Wrong member: star-map → echo-drum                0 → __ → __
Unrelated: star-map → crystal-lantern             0 → __ → __
```

Predict in words:

- Correct sequence: __________________________________________
- Wrong authored member reset: _______________________________
- Unrelated-object interaction: ______________________________

Checkpoint: teacher initials all three traces before execution.

## Core Python path

1. Run `python lessons/sessions/s15/student/starter.py` only after prediction.
2. Repair `has_three_distinct_ids`: it must reject a length other than three and
   reject any repeated ID. Use one plain loop and a small `seen` list, or compare
   the three pairs; keep it readable.
3. Read `next_progress` one branch at a time. Explain how `compare_order` loops
   through attempted IDs. Replace the placeholder `if`/`pass` block with one
   line that saves `next_progress(expected_ids, progress, attempted_id)`.
4. Keep the normal assertion and author one reset assertion. Run them: passing
   assertions make no output. Compare all printed traces with your predictions.

## Local Python → declarative package → visible sequence

| Local ID/order idea | Package object | Visible role |
|---|---|---|
| `star-map` first | ordinary world object | Starts the star song |
| `moon-switch` second | toggle object | Changes state and advances |
| `echo-drum` third | counter object | Adds a beat and completes order |
| `crystal-lantern` local test label | `crystal-lantern:lantern` from the separate Crystal Lantern example package | Leaves sequence progress unchanged |

Python remains local and tests a model. Validated YAML
`respond_to_sequence.object_ids` is the Trail's source of truth; runtime never
executes `starter.py`.

## Package and world path

1. Personalize names/messages only; retain three distinct IDs and the mixed
   ordinary/toggle/counter object types.
2. Validate and launch with Nova and Crystal Lantern loaded as separate example
   packages:

   ```console
   explore-package validate lessons/sessions/s15/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     examples/explorer-packages/crystal-lantern \
     lessons/sessions/s15/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "complete-actions-in-order" \
     --name "S15 Ship a Secret Sequence"
   ```

3. Focus the window and use WASD/arrows plus E. Observe these paths:
   - correct order reaches the keeper's success response;
   - a wrong authored member resets progress to zero and is not immediately
     reconsidered as the first step;
   - unrelated Crystal Lantern interaction leaves progress unchanged.

Checkpoint: show M15 completion and describe all three results.

## Deliberate debugging exercise

Show that `["star-map", "star-map", "echo-drum"]` incorrectly passes the starter
validator. Repair distinctness, add an assertion rejecting it, then add and pass
the required wrong-member reset assertion.

## Support path

Use numbered object cards and move a progress marker from 0 to 3. The teacher may
provide the `seen`-list shape with blanks, but the student supplies the repeated-
ID check. For low bandwidth, use printed traces, validation, and a teacher demo.

## Extension path

After core evidence, add one assertion for an unrelated interaction or completed
progress. Do not create a fourth sequence member or branching sequence.

## First-half capstone checklist

- [ ] Exactly three distinct same-package IDs are validated.
- [ ] Normal and wrong-member reset assertions pass.
- [ ] Ordinary, toggle, and counter objects appear in one ordered story.
- [ ] Correct, wrong-member, and unrelated traces match Trail observations.
- [ ] Package validates and M15 completes.
- [ ] I can explain every accepted Python line and package reference.

## Required self-review and presentation

- Creative choice: “I chose ___ because ___.”
- Python change: “I changed ___, which made ___.”
- Test run: “I tested ___ and observed ___.”
- In 60 seconds, present the story, show one trace/test, and demonstrate or
  describe the visible success payoff. A text/chat presentation is valid.

## Required evidence/checkpoints

- Three predictions and state traces before execution.
- Exactly-three-distinct validator evidence.
- Passing normal and reset assertions.
- Package validation, three world-case observations, checklist, and self-review.

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution. AI may suggest
tests only; never ask it to write the sequence solution, order, trace, assertion,
or helper.** Predict each test before using it.

## Git close

```console
git status --short
git diff
git add lessons/sessions/s15/student
git diff --staged
git commit -m "Ship a three-part star song"
```

`M` means modified; `??` means untracked; no status output means no uncommitted
changes, and no diff output means no unstaged tracked changes. Inspect
`git diff --staged`. Recover repository Git identity if needed; Control-C,
correct, and retry a mistaken command. Understanding takes priority over a
rushed commit.
