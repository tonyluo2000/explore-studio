# Explore Studio — Curriculum Design

## Philosophy

The Explore Studio curriculum teaches programming through world-building.
Each lesson introduces a single concept and asks students to apply it by
modifying or extending their world.

## Curriculum Structure

The target online course contains 30 sessions. Missions may be grouped into the
six established Explorer World sprints so that teachers can retain sprint
showcases while students receive smaller, age-appropriate steps. Sessions and
Missions are not required to remain 1:1.

The canonical integrated first-half plan is
[Sessions 01–15 Curriculum](curriculum-sessions-01-15.md). It pairs every
implemented Mission 01–15 with progressive local Python practice while keeping
the Explorer Package as the deterministic shared artifact.

The canonical second-half plan is
[Sessions 16–30 Curriculum](curriculum-sessions-16-30.md). It makes Python
primary, reuses Missions 01–15 through S29, and culminates in an independently
designed S30 capstone framed by content-only Mission 16 without expanding the
runtime or package contract.

> **Everything is already built. Students gradually learn how to use it.**

The engine capabilities and world systems required by a cohort are implemented
and tested before the course begins. Mission progression controls which concepts
and experiences are introduced; it is not a source-code security boundary.
Students who inspect later capabilities locally are demonstrating curiosity.

Each student works in an independent repository, develops and tests locally
without login, and exports a versioned Explorer Package candidate for review.
The repository starts from the standalone template; before delivery, a teacher
adds the student-only S01–S30 course overlay through the
[Classroom Student Workspace](classroom-student-workspace.md) procedure. Online
course and shared-world services require authenticated identity. See the
[Student Contribution and Class-World Model](architecture/student-contribution-model.md)
for the canonical ownership workflow.

### Planned Module Areas

- **Foundations:** variables, types, functions, conditionals, loops.
- **Data:** lists, dictionaries, files, basic algorithms.
- **World Building:** terrain, entities, physics, events.
- **Interaction:** input handling, collision detection, UI.
- **Design:** state machines, game loops, polish.

## Lesson Format

Each lesson follows a consistent structure:

1. **Concept introduction** — what are we learning and why.
2. **Guided example** — step-by-step code with explanation.
3. **Challenge** — students apply the concept independently.
4. **Extension** — optional deeper exploration.
5. **Reflection** — students articulate what they learned.

## Assessment

*To be defined during Phase 2.*

---

*Curriculum sequencing is independent of whether the underlying capability has
already been implemented.*
