# Session Materials

This directory contains production teaching materials for the 45-minute online
Explore Studio sessions. Each session uses the same small, reusable layout:

```text
sNN/
├── teacher-runbook.md
└── student/
    ├── starter.py
    └── explorer-package/   # present when students author package content
```

The teacher runbook is the delivery source of truth. Every runbook includes the
learning objective, prerequisites, canonical timing, world task, prediction,
deliberate debugging exercise, expected behavior, bounded AI workflow, Git
close, optional extension, and an answer key.

Student Python is local practice. Explorer Package YAML is declarative content:
validate it with `explore-package validate` and load it through the package
workflow. Never copy Python into an Explorer Package or import package YAML as
code.

## Shared lesson rhythm

| Time | Activity |
|---:|---|
| 0:00–0:05 | Creative hook |
| 0:05–0:12 | Concept introduction and prediction |
| 0:12–0:24 | Local Python activity |
| 0:24–0:37 | Explorer Package and world activity |
| 0:37–0:42 | Test and deliberate debugging |
| 0:42–0:45 | Review and descriptive Git commit |

## Student commands

Run these from the repository root, replacing `sNN` with the session number:

```console
python lessons/sessions/sNN/student/starter.py
explore-package validate lessons/sessions/sNN/student/explorer-package
git status --short
git diff
git add lessons/sessions/sNN/student
git commit -m "Describe the story or code change"
```

The validation command applies only when the session includes an
`explorer-package` directory. The teacher chooses the local package set and
player when launching the corresponding canonical mission in Classroom Trail.

## AI boundary

Every session uses one workflow:

1. Explain your intent in your own words.
2. Predict the code or world behavior before running it.
3. Ask one bounded question about one line, error, or mismatch.
4. Test the suggestion locally.
5. Revise only what you understand.
6. Explain every accepted line of code.

AI may explain a concept, traceback, or validation message. It must not write a
student's story, complete the whole activity, edit engine internals, invent
schema fields, or replace the student's prediction and explanation.
