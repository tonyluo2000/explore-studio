# S05 Task Card — Script a Conversation

**Mission:** M05 `write-a-short-conversation` — Write a Conversation

**Learning target:** Create an ordered list of 2–3 dialogue lines, retrieve its
first and final items, use `len(...)`, and debug order or indexing.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## The bridge to the world

| Local Python value | Declarative YAML field | Visible world result |
|---|---|---|
| ordered `dialogue` strings | ordered `conversation` lines | one line per E press |

YAML drives the runtime. Preserve the tested Python order when copying only the
spoken text into the package.

## Predict before running

Before testing, write the expected first line, final line, list length, and what
the Trail should do on the interaction after the final line.

## Core Python and debugging path

1. Replace both TODO strings in `starter.py` with an opening and ending. Add one
   optional middle line only if it improves the story.
2. Add expressions that print `dialogue[0]` and `dialogue[-1]`. Run Python.
3. Checkpoint: show the first line, final line, and length.
4. Before world work, temporarily change `dialogue[-1]` to `dialogue[3]`.
   Predict, run, read the `IndexError`, then restore `dialogue[-1]`.
5. Swap two strings, predict the story effect, run, and restore the intended
   beginning-to-ending order.

## Core world path

1. Copy the 2–3 spoken strings into the ordered YAML `conversation`.
2. Validate and launch:

   ```console
   explore-package validate lessons/sessions/s05/student/explorer-package
   explore-package trail \
     examples/explorer-packages/nova-character \
     examples/explorer-packages/crystal-lantern \
     lessons/sessions/s05/student/explorer-package \
     --player "nova-character:nova" \
     --mission-id "write-a-short-conversation" \
     --name "S05 Script a Conversation"
   ```

3. Press E once per line. Verify the final line and M05 completion. Press E one
   more time to test the restart prediction.

## Support path

Keep two dialogue lines. Label index 0 and index 1 on paper before adding the
print expressions. Ask the teacher to point to the list position.

## Extension path

Add one middle clue to a two-line conversation, staying within 2–3 lines.

## Required self-review

- Creative choice: “I chose ___ because ___.”
- Python change: “I changed ___, which made ___.”
- Test run: “I tested ___ and observed ___.”

## AI receipt

Record: intent; prediction; exact bounded question; suggestion tested;
accepted/rejected change; student explanation.

**Do not paste whole files or ask AI for a complete solution.**

## Git close

```console
git status --short
git diff
git add lessons/sessions/s05/student
git diff --staged
git commit -m "Write an ordered guide conversation"
```

Use the Quick Start for status meanings and recovery. If live setup ran long,
explain the diff now and finish this same commit after class.
