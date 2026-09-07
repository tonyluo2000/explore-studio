# Session Materials v2

These production materials support 45-minute online Explore Studio sessions for
ages 10–14. Every session uses the same student-readable structure:

```text
sNN/
├── teacher-runbook.md
└── student/
    ├── task-card.md
    ├── starter.py
    ├── debug.py           # optional isolated debugging activity
    └── explorer-package/  # optional validated declarative world content
```

Teachers deliver from `teacher-runbook.md`. Students work from `task-card.md`
and `starter.py`. All students use the shared
[`student-quick-start.md`](student-quick-start.md) for setup, controls,
accessibility choices, troubleshooting, AI evidence, and Git recovery.

## Shared 45-minute rhythm

The course duration remains 45 minutes. The clock markers are anchors, not a
promise that every computer operation takes exactly the same time.

| Clock anchor | Typical range | Activity |
|---:|---:|---|
| 0:00–0:05 | 4–5 min | Creative hook |
| 0:05–0:12 | 6–8 min | Concept introduction and prediction |
| 0:12–0:24 | 11–15 min | Local Python activity |
| 0:24–0:37 | 9–13 min | Explorer Package and visible world activity |
| 0:37–0:42 | 4–6 min | Test and deliberate debugging |
| 0:42–0:45 | 3–5 min | Review and descriptive Git close |

Each runbook names a **cut line**: the minimum evidence to protect when launch,
audio, screen sharing, or setup takes longer. Git understanding takes priority
over a rushed commit. A student may finish the same descriptive commit after
the live session when operational problems use the closing minutes.

## Learning boundary

Student Python runs only on the student's computer for concept practice. It is
never placed in an Explorer Package and is never executed by the shared
runtime. Explorer Packages contain validated declarative YAML. The package
loader validates that data before Classroom Trail consumes it.

The recurring bridge is made explicit in every relevant task card:

```text
local Python value → declarative package field → visible world result
```

The bridge is a learning comparison, not automatic code generation. Students
copy only the intended values into supported YAML fields, validate, then test
the visible behavior.

## Three paths

- **Core path:** produces the required session evidence.
- **Support path:** reduces typing or supplies one recovery example without
  changing the learning objective.
- **Extension path:** adds creative depth only after core evidence is complete.

Teachers may move students between paths. The mission, validation boundary,
and expected explanation remain the same.

## Canonical habits

AI: explain intent → predict → bounded question → test → revise → explain
accepted code.

Git: status → diff → stage intentionally → inspect staged diff → descriptive
commit.
