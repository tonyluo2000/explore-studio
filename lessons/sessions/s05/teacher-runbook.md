# S05 — Script a Conversation

**Canonical mission:** M05 `write-a-short-conversation` — Write a Conversation

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can create an ordered list of 2–3 dialogue
lines, retrieve the first and final items, use `len(...)`, and repair an
ordering or indexing mistake.

**Prerequisite:** S04 functions and authored character text.

## Before class

- Send `student/task-card.md` and confirm the shared Quick Start preflight.
- Run the Python starter and validate the conversation package.
- Prepare to model zero-based indexing with three visible cards or screen
  annotations. Do not introduce dialogue trees or branching.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 4–5 min | Ask for a tiny exchange with a beginning and an ending. | Describes a 2–3-beat story arc. |
| 0:05–0:12 | 6–8 min | Number list positions and require first/final/length/wrap predictions. | Records all four predictions. |
| 0:12–0:28 | 14–17 min | Students replace TODO lines, add `[0]`/`[-1]`, then complete indexing and order debugging before world work. | Correct output, repaired `IndexError`, and explained story order. |
| 0:28–0:38 | 9–11 min | Students transfer 2–3 ordered lines to YAML, validate, run M05, verify the final line, and test wraparound. | M05 completes and behavior matches prediction. |
| 0:38–0:42 | 3–5 min | Protect the three-part self-review and final evidence check. | Names creative choice, Python change, and test run. |
| 0:42–0:45 | 3–5 min | Inspect status, unstaged/staged diffs, then commit or schedule it. | Descriptive commit or documented plan. |

**Teacher cut line:** At 0:28, end Python wording changes and move to world
verification. At 0:38, stop relaunching and protect the canonical self-review.
Git may finish asynchronously, but the student must interpret the diff live.

## Student task and prediction

Students follow `student/task-card.md`. The starter intentionally contains two
TODO dialogue lines and leaves first/final indexing for the student.

Write two or three original dialogue lines. Before running, identify the exact
first line, final line, list length, and your prediction that the next world
interaction after the final line restarts the conversation.

```console
python lessons/sessions/s05/student/starter.py
explore-package validate lessons/sessions/s05/student/explorer-package
explore-package trail \
  examples/explorer-packages/nova-character \
  examples/explorer-packages/crystal-lantern \
  lessons/sessions/s05/student/explorer-package \
  --player "nova-character:nova" \
  --mission-id "write-a-short-conversation" \
  --name "S05 Script a Conversation"
```

Interact with the NPC once per line. Verify its final line and then interact one
more time to test the restart prediction.

## Deliberate debugging exercise

Complete this during the 0:12–0:28 Python block, before package/world work. For
a three-line list, predict what is wrong here:

```python
print(dialogue[3])
```

Repair it so it always selects the final line. Next, swap two list items,
predict the story effect, and restore the intended beginning-to-ending order.

## Expected output and behavior

Before student work, the runnable starter prints only `2`, the list length. A
student who chooses the sample package wording and adds both required print
expressions sees:

```text
Guide: The moon compass is awake.
Guide: Follow the silver lights home.
3
```

Index `3` raises `IndexError` because the three valid positions are 0, 1, and 2;
`dialogue[-1]` selects the final line. The package validates. Each interaction
shows the next authored line, M05 completes when the final line is displayed,
and the following interaction restarts at line one.

## Bounded AI assistance

Student sequence: explain intent → predict → ask one bounded question → test →
revise → explain accepted code. AI may check whether the student's existing
conversation is clear and explain one indexing error. It must never author or
reorder the conversation for the student.

## Git close and self-review

Before committing, complete aloud or in chat:

- Creative choice: “I chose ___ because ___.”
- Python change: “I changed ___, which made ___.”
- Test run: “I tested ___ and observed ___.”

```console
git status --short
git diff
git add lessons/sessions/s05/student
git diff --staged
git commit -m "Write an ordered guide conversation"
```

## Optional extension

If the conversation has two lines, add one middle line that raises tension or
adds a clue. Keep the package conversation within the validated 2–3-line limit.

## Teacher notes and answer key

- Correct final-line access: `print(dialogue[-1])` or, for the three-line sample,
  `print(dialogue[2])`. Prefer `[-1]` because it still works with two lines.
- A 2-line list has indices 0 and 1; a 3-line list has 0, 1, and 2.
- M05 evidence occurs when the final line is displayed. Later wraparound does
  not erase completion evidence.
- Accept any age-appropriate original exchange with 2–3 nonblank ordered lines.
  The student's explanation of order matters more than matching the sample.
- Use the shared Quick Start for launch, accessibility, Git interpretation,
  identity recovery, cancellation, and asynchronous completion.
