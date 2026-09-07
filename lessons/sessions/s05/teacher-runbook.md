# S05 — Script a Conversation

**Canonical mission:** M05 `write-a-short-conversation` — Write a Conversation

**Audience and format:** Ages 10–14, online, 45 minutes

**Learning objective:** Students can create an ordered list of 2–3 dialogue
lines, retrieve the first and final items, use `len(...)`, and repair an
ordering or indexing mistake.

**Prerequisite:** S04 functions and authored character text.

## Before class

- Run the Python starter and validate the conversation package.
- Prepare to model zero-based indexing with three visible cards or screen
  annotations. Do not introduce dialogue trees or branching.

## 45-minute runbook

| Time | Teacher move | Student evidence |
|---:|---|---|
| 0:00–0:05 | Ask for a tiny exchange with a beginning and an ending. | Describes a 2–3-beat story arc. |
| 0:05–0:12 | Number three lines as list positions 0, 1, 2. Ask students to predict first, final, length, and what happens after the final world line. | Records all four predictions. |
| 0:12–0:24 | Students write 2–3 original list strings and inspect `[0]`, `[-1]`, and `len(...)`. | Correct first line, final line, and length. |
| 0:24–0:37 | Students copy only their spoken text into the ordered declarative conversation, validate, run M05, and advance through its final line. | Lines appear in authored order; M05 completes on the final line. |
| 0:37–0:42 | Give the ordering/index bug below. Students predict, repair, and retest the final line. | Explains zero-based indexing or uses `[-1]`. |
| 0:42–0:45 | Lead the three-part self-review and Git close. | Names one creative choice, one Python change, and one test run; commits. |

## Student task and prediction

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

For a three-line list, predict what is wrong here:

```python
print(dialogue[3])
```

Repair it so it always selects the final line. Next, swap two list items,
predict the story effect, and restore the intended beginning-to-ending order.

## Expected output and behavior

The sample output is:

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
