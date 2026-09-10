# Explore Studio — Project Management

## Development Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 0 | Active | Repository foundation and tooling |
| 1 | Planned | Core engine: rendering, input, world model |
| 2 | Planned | Lesson framework and first curriculum module |
| 3 | Planned | Teacher dashboard and student progress tracking |
| 4 | Planned | Community lesson marketplace |

## Contribution Guidelines

*To be defined. Will include:*

- Code style (Black, Ruff).
- Pull request process.
- Testing requirements.
- Documentation expectations.

## Durable Implementation Handoff

Every completed implementation slice follows the required publication boundary:

```
clean commit -> authenticated push -> GitHub branch/PR -> exact-head handoff
```

GitHub is the durable handoff across Mac, temporary Codex workspaces, connected
integrations, and iPhone-operated remote sessions. An unpushed completed commit
is a blocker: do not begin dependent work, independent review, or
cross-environment continuation until the branch is pushed and its exact-head
SHA is recorded in the canonical GitHub issue or pull request. See
[`development-handoff.md`](development-handoff.md) for the authentication,
publication, and failure-reporting procedure.

## Model Assignment Convention

Every implementation prompt should begin with:

```
Model Assignment

Primary Implementer: DeepSeek Pro
Reviewer: ChatGPT (architecture, scope, acceptance)
Optional Independent Review: Gemini Pro
```

This ensures consistent responsibility tracking across the project and
prevents context bleeding between unrelated projects.

Every implementation prompt must also require the implementer to stop after a
clean commit if it cannot authenticate and push from the current execution
context. Before independent review or any work in another environment, the
prompt must require a recorded branch, exact pushed head SHA, and GitHub
branch/PR or issue handoff. Prompts must never request, contain, or log
credentials or tokens.

## Issue Tracking

*GitHub Issues will be used. Labels and templates to be configured.*

---

*This document will be updated as processes are established.*
