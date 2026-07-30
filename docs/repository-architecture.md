# Explore Studio — Repository Architecture Specification

> *Defines how the codebase is organized, where responsibilities belong, and
> how dependencies flow between packages. The structural guardrails for all
> future implementation. An architecture document — not a directory listing.*
>
> **Contribution-model note:** This document describes the official platform
> repository. The approved multi-repository student workflow is defined by the
> [Student Contribution and Class-World Model](architecture/student-contribution-model.md)
> and [ADR-001](architecture/decisions/ADR-001-student-repositories-and-explorer-packages.md).
> Those documents supersede earlier assumptions that student work is kept in
> directories or branches of this repository.

---

## 1. Purpose

Repository organization is not cosmetic. It is the first thing a contributor
encounters, the map a developer uses to navigate, and the structure that
enforces — or fails to enforce — the project's architectural principles.

A well-organized repository makes several things true:

### Maintainability

A developer fixing a rendering bug knows exactly where to look. The file
structure tells them: rendering logic lives in one place, not scattered across
the codebase. When a subsystem needs to change, the change is localized.

### Discoverability

A new contributor — a teacher customizing lessons, a student exploring how
the engine works, an open-source contributor adding a feature — can find
what they need without asking. The directory names are the documentation.
The structure tells the story.

### Scalability

As the project grows from a single engine to a full educational platform,
the repository grows with it. New subsystems have obvious homes. New
top-level directories have clear criteria for when they should exist.
The structure accommodates growth without requiring reorganization.

### Educational Clarity

The repository itself teaches. A student who opens the project sees a
structure that mirrors what they have learned: the engine is separate from
student code, lessons are separate from examples, documentation stands
apart from implementation. The file tree reinforces the architecture they
are learning to understand.

---

## 2. Repository Principles

These principles govern every organizational decision:

| Principle | Meaning |
|-----------|---------|
| **Feature ownership** | Each top-level directory has a single, clear owner. No directory is shared between unrelated concerns. |
| **Separation of concerns** | Engine code, student code, lesson content, and documentation live in distinct areas. They do not intermingle. |
| **Predictable locations** | A contributor can predict where a new file belongs without reading documentation. The rules are consistent and obvious. |
| **Minimal coupling** | Directories depend on each other only through well-defined, intentionally narrow interfaces. Changes in one area do not cascade. |
| **Convention over configuration** | The repository follows consistent naming and layout conventions. Contributors do not make per-directory organizational decisions. |
| **One obvious way** | For any given file, there is exactly one correct place to put it. No contributor should debate between two equally valid locations. |
| **Flat where possible** | Deep directory hierarchies obscure relationships. The structure is as shallow as the organization's complexity allows. |
| **Stable boundaries** | The top-level directory structure changes rarely and deliberately. Reorganization is a breaking change that requires migration. |

---

## 3. Top-Level Structure

Each top-level directory has a defined purpose and ownership. The structure
is intentional — nothing exists at the root without a reason.

### Directory Purposes

| Directory | Purpose | Owned By |
|-----------|---------|----------|
| **`assets/`** | Visual and audio media: sprites, sounds, fonts, tile sets. Static resources consumed by the engine. | Shared — contributors provide assets; the art lead maintains coherence. |
| **`docs/`** | All project documentation: vision, architecture, curriculum, development guides, teaching materials. | Project maintainers. |
| **`engine/`** | The Explore Studio engine: application lifecycle, rendering, input, world state, interactions, audio, persistence. The platform. | Engine team. |
| **`examples/`** | Standalone, runnable demonstrations of engine capabilities. Each example is self-contained and illustrates exactly one concept. | Engine team (creates); teachers (use). |
| **`lessons/`** | Curriculum content: lesson plans, starter projects, completed solutions, exercise descriptions. Organized by sprint and topic. | Teachers and curriculum designers. |
| **`students/`** | Optional platform-owned fixtures or migration examples only. It is not the target home of student projects. | Engine team. |
| **`teacher/`** | Teacher tooling: dashboards, assessment helpers, world configuration, sprint management. | Teachers. |
| **`tests/`** | Automated tests: engine unit tests, integration tests, regression tests, example validation. | Engine team. |
| **`tools/`** | Development and operational scripts: build helpers, asset pipelines, world validators, migration tools. Not part of the runtime. | Engine team. |

### What Does Not Belong at the Root

- Generated files, build artifacts, or caches — these go in `.gitignore`.
- Temporary scripts — these go in `tools/`.
- Personal configuration — these go in the developer's home directory.
- Deployment configuration — future concern; will have a dedicated location.
- Third-party code — vendored dependencies, if ever needed, belong in a
  dedicated directory, not scattered at the root.

---

## 4. Engine Package Organization

The engine is the largest and most complex package. Its internal organization
follows the same principles as the repository at large: one concept, one home.

### Conceptual Subsystems

The engine is organized around capabilities, not technical layers:

| Subsystem | Responsibility |
|-----------|---------------|
| **Application** | The main loop, window management, lifecycle events. Startup and shutdown. The entry point. |
| **World** | World state: the grid, entity positions, tile data, global variables. The single source of truth. |
| **Rendering** | Drawing the world: tiles, entities, UI overlays, visual effects. Translates world state into pixels. |
| **Scenes** | Scene management: transitions between views (world, menu, dialogue). Active scene tracking. |
| **Input** | Keyboard and mouse event collection and interpretation. Translates raw OS events into engine actions. |
| **Entities** | Entity lifecycle: characters, objects, their properties and behaviors. The "things" in the world. |
| **Interactions** | Interaction dispatch: detecting when interactions should fire, invoking the right handler, managing interaction state. |
| **Dialogue** | Dialogue rendering and progression: displaying text, managing choices, advancing conversation trees. |
| **Animation** | Frame-based animation: sprite sequences, timing, transitions. Cosmetic only — no effect on world state. |
| **Audio** | Sound playback: effects, ambient audio, optional music. Event-driven and optional. |
| **Persistence** | Save and load: world serialization, format migration, file management. |
| **UI** | User interface primitives: menus, dialogs, HUD elements, text displays. Always rendered above the world. |
| **Assets** | Asset management: loading, caching, and providing images, sounds, and fonts to other subsystems. |

### Organization Principles Within the Engine

- **One subsystem, one directory.** Rendering code does not live alongside
  input code. Collision detection does not share a directory with dialogue.

- **Public interface separate from implementation.** Each subsystem exposes
  what other subsystems may use. Implementation details are private to the
  subsystem.

- **No circular dependencies between subsystems.** The world subsystem may
  be imported by rendering, but rendering does not import back into world
  internals. Dependency graphs are acyclic.

- **The Student API is a distinct concern.** It is the boundary between the
  engine and student code. It may live within the engine package or as a
  sibling — the architectural relationship matters more than the physical
  location.

---

## 5. Student Workspace

The target student workspace is one independent repository per student, created
from a supported template. It is the student's territory, not a directory or
branch in the official engine repository. A student commits freely to that
repository and publishes selected work through a versioned Explorer Package.

### Design Requirements

| Requirement | Rationale |
|-------------|-----------|
| **Isolation** | Each student's work and Git history live in a distinct repository. Modifying one project cannot directly rewrite another's source. |
| **Ownership** | Repository ownership makes the student's code, assets, tests, and history clearly theirs. |
| **Simplicity** | The supported template emphasizes student work and hides operational complexity from the normal workflow. |
| **Discoverability** | Students can find their character file, their dialogue file, and their object definitions without guidance. |
| **Version-control friendly** | Commits and reviews occur in the student's repository. Publishing is separate from committing. |
| **Publishable** | The workspace can export a validated Explorer Package without copying the entire repository. |

### What Students See

Students see a workspace that contains:

- Their character definition.
- Their dialogue files.
- Their object and interaction definitions.
- Their assets and local tests.
- A way to run locally without login.
- A documented way to build and validate an Explorer Package.

### What Students Do Not See

- Operational secrets or privileged server credentials.
- Unapproved private source from other students.
- Class-world release controls unless their authenticated role permits them.

Students may have the complete open-source engine and may inspect future
capabilities. The template should keep the everyday path understandable without
pretending that source code is a security boundary.

### The Student Boundary

Student code uses the Student API rather than engine internals. Package
validation rejects unsupported contribution boundaries before shared-world
assembly. Local source access means students can still experiment; structural
conventions guide the supported path but do not make modification impossible.
Online authorization and approval are enforced by trusted services, not by
repository layout.

---

## 6. Lesson Organization

Lessons are the bridge between the curriculum and the codebase. They must be
organized so that teachers can find, sequence, and deliver them efficiently.

### Organizational Dimensions

Lessons are organized along multiple dimensions:

**By sprint.** Each of the six semester sprints has its own collection of
lessons. A teacher preparing Sprint 3 opens the Sprint 3 directory and
finds everything they need.

**By topic.** Within a sprint, lessons are grouped by programming concept:
variables, functions, conditionals, events. This allows teachers to see the
conceptual arc of a sprint at a glance.

**By difficulty.** Lessons are labeled with a difficulty indicator:
introductory, practice, challenge, extension. This supports mixed-experience
classrooms where students work at different paces.

### Lesson Contents

Each lesson directory contains:
- A teacher guide: objectives, prerequisites, estimated time, discussion
  points.
- A starter project: the world state and student workspace before the
  lesson begins.
- A completed solution: what the world should look like after the lesson
  is successfully completed.
- Exercise descriptions: step-by-step instructions for students.
- Assessment criteria: what teachers should look for when reviewing student
  work.

### Separation from Engine

Lessons do not contain engine code. They reference engine capabilities but
do not implement them. A lesson that teaches movement imports the Student
API — it does not modify the rendering subsystem. This separation ensures
that lessons remain valid as the engine evolves.

---

## 7. Example Projects

Examples are standalone demonstrations of engine capabilities. They are
distinct from lessons: lessons teach; examples illustrate.

### Types of Examples

| Type | Purpose | Audience |
|------|---------|----------|
| **Capability demonstrations** | Show that a specific engine feature works: "Here is a character that waves." | Engine developers (verification), teachers (reference). |
| **Reference implementations** | Show the recommended way to implement a common pattern: "Here is how to structure a dialogue tree." | Students (learning), teachers (teaching). |
| **Teaching aids** | Show a concept in isolation for classroom use: "Here is what a loop looks like in the world." | Teachers (classroom demonstration). |

### Example Requirements

- Every example is self-contained. Running an example requires no additional
  setup beyond what the base project provides.
- Every example illustrates exactly one concept. An example that demonstrates
  both movement and dialogue confuses both concepts.
- Every example is runnable. Broken examples are worse than no examples.
- Every example has a description: what it demonstrates, what concepts are
  involved, what students should observe.

### Examples vs. Tests

Examples are not tests, though they may serve a testing function. A test
asserts correctness; an example illustrates capability. Examples may be run
as part of the test suite to ensure they do not break, but their primary
purpose is educational, not verificational.

---

## 8. Testing Organization

The test suite mirrors the repository structure. A subsystem in the engine
has corresponding tests. An example has a corresponding validation. The
mapping is predictable.

### Testing Categories

| Category | Location Pattern | Purpose |
|----------|-----------------|---------|
| **Engine unit tests** | Alongside or mirroring engine subsystems | Verify individual engine components in isolation. |
| **Integration tests** | Dedicated integration test directories | Verify that subsystems work together correctly. |
| **Regression tests** | Alongside bug fixes | Prevent known bugs from recurring. |
| **Example validation** | Associated with example directories | Confirm that every example runs without error. |
| **World format tests** | Persistence test directory | Verify save/load round-trips and format migration. |
| **Student API contract tests** | Contract test directory | Verify that the Student API behaves as documented. |

### Testing Principles

- **Tests live near what they test.** A developer modifying the rendering
  subsystem finds rendering tests in an obvious, adjacent location.
- **Tests are part of the repository, not a separate project.** Running
  tests requires no external setup beyond the development environment.
- **Tests build confidence, not coverage metrics.** The goal is a trustworthy
  engine, not a percentage. Tests are written for behavior that matters,
  not to satisfy a metric.
- **Flaky tests are treated as bugs.** A test that passes sometimes and fails
  sometimes undermines confidence in the entire suite. Flaky tests are fixed
  or removed — never ignored.

---

## 9. Documentation Organization

Documentation is organized by audience and purpose, not by implementation
area. A teacher looking for lesson guidance should not need to navigate
through engine architecture documents.

### Documentation Categories

| Category | Audience | Content |
|----------|----------|---------|
| **Vision** | Everyone | Why Explore Studio exists, what it is, what it is not. |
| **Product Design** | Teachers, curriculum designers | Explorer World specification: world, characters, story, interactions. |
| **Architecture** | Engine developers, contributors | Engine architecture, repository organization, Student API specification. |
| **Decision records** | Maintainers, instructors | Accepted cross-cutting choices, consequences, alternatives, and follow-up work. |
| **Curriculum** | Teachers | Lesson plans, teaching guides, assessment strategies, classroom management. |
| **Development** | Contributors | Setup guides, contribution guidelines, coding standards, review process. |
| **Teaching** | Teachers | How to use Explore Studio in a classroom: first-day setup, troubleshooting, customizing content. |
| **Reference** | Students, teachers | Student API reference, engine capability reference, error message guide. |

### Documentation Principles

- **Documentation lives with the project, not in a wiki.** The `docs/`
  directory is the single source of truth. External documentation is a
  mirror, not an authority.
- **Documentation is versioned.** When the engine changes, documentation
  changes in the same commit. Outdated documentation is a bug.
- **Every architectural decision is documented.** Why a choice was made
  matters as much as what was chosen. Future contributors need context.
- **Canonical documents are linked, not copied.** Cross-document summaries
  point to the detailed design and ADR so contracts do not drift.
- **Documentation is written for humans.** It is not generated from code
  comments. It tells a story, provides context, and answers "why."

---

## 10. Dependency Rules

Dependencies flow in one direction: downward through a well-defined stack.
Upper layers depend on lower layers. Lower layers never depend on upper
layers. This is the single most important structural rule in the repository.

### Dependency Hierarchy

```
┌──────────────────┐
│     Lessons       │  ← Depend on: Student API, Examples
├──────────────────┤
│   Student Code    │  ← Depends on: Student API
├──────────────────┤
│   Student API     │  ← Depends on: Engine
├──────────────────┤
│     Engine        │  ← Depends on: Platform libraries
├──────────────────┤
│    Platform       │  ← External: Pygame, Python stdlib, OS
└──────────────────┘
```

### Explicit Dependency Rules

1. **Lessons may import from the Student API and reference examples.**
   They may not import from engine internals.

2. **Student code may import only from the Student API.**
   It may not import from engine internals, other students' code directly,
   or platform libraries.

3. **The Student API may import from the engine.**
   It exposes engine capabilities through an educational interface.

4. **The engine may import from platform libraries.**
   It may not import from the Student API, student code, or lessons.

5. **No layer may import upward.**
   The engine never imports from student code. The Student API never
   imports from lessons.

6. **No circular dependencies anywhere.**
   If A imports B, B does not import A — directly or transitively.

7. **Tests may import from the layer they test.**
   Engine tests import from the engine. Student API tests import from the
   Student API. Tests do not cross layer boundaries unnecessarily.

### Enforcing Dependency Rules

The repository structure makes violations visible. An import that crosses
a forbidden boundary should be obvious in code review. Tooling may enforce
these rules automatically — but the structure itself should make violations
feel unnatural before a tool catches them.

---

## 11. Import Philosophy

Imports are the concrete expression of dependencies. The repository's import
conventions make architectural intent visible in every file.

### Acceptable Import Patterns

| Pattern | Example Intent | Allowed |
|---------|---------------|---------|
| **Downward, within layer** | Rendering subsystem imports from world subsystem | Yes |
| **Downward, across layer** | Student API imports from engine | Yes |
| **Same-layer, sibling** | Dialogue subsystem imports from interaction subsystem | Yes, if acyclic |
| **Upward, any** | Engine imports from Student API | No |
| **Circular, any** | A imports B, B imports A | No |
| **Student code imports engine internals** | Student file imports rendering | No |
| **Lesson imports engine internals** | Lesson file imports input subsystem | No |

### Import Conventions

- **Public interfaces are explicit.** Each subsystem defines what other
  subsystems may import. Everything else is private by default.

- **Wildcard imports are forbidden.** Every import names exactly what it
  uses. This makes dependencies visible and reviewable.

- **Relative imports within a package, absolute imports between packages.**
  This convention makes it clear whether an import crosses a package boundary.

- **Third-party imports are centralized.** If the engine depends on an
  external library, that dependency is declared in one place and re-exported.
  Other subsystems import from the engine, not from the third-party library
  directly.

---

## 12. Ownership Matrix

Clear ownership prevents conflict, ensures accountability, and makes
contribution straightforward. Every area of the repository has an owner.

### Ownership by Area

| Area | Primary Owner | Contributors | Review Required By |
|------|--------------|--------------|-------------------|
| Engine core | Engine team | Approved contributors | Engine lead |
| Student API | Engine team + curriculum team | Approved contributors | Engine lead + Curriculum lead |
| Student repository | Individual student | Classmates (with permission) | Student; teacher approval for publication |
| Explorer Package contract | Engine team + curriculum team | Approved contributors | Engine lead + curriculum lead |
| Package approval | Teacher and automated policy | Student author | Teacher/course team |
| Class-world configuration and release | Course team | Teachers | Course lead |
| Lessons | Curriculum team | Teachers, contributors | Curriculum lead |
| Examples | Engine team | Teachers, contributors | Engine lead |
| Teacher tools | Engine team | Teachers, contributors | Engine lead |
| Documentation | Project maintainers | Anyone | Documentation lead |
| Tests | Engine team | Contributors | Engine lead |
| Assets | Art lead | Contributors | Art lead |
| Build and tooling | Engine team | Contributors | Engine lead |

### What Ownership Means

- **Primary owner** — responsible for the quality, stability, and direction
  of the area. Has final say on changes.
- **Contributors** — may propose changes through pull requests. Changes must
  be reviewed by the primary owner or designated reviewer.
- **Review required by** — the person or role that must approve changes
  before they merge.

### Ownership Boundaries in Practice

Ownership is not about permission. It is about responsibility. A teacher
who wants to add a lesson does not need the engine team's approval — but
the engine team is responsible if a student's code breaks due to an engine
change. Ownership boundaries make these responsibilities explicit.

Student publication is a special case: the student owns the source and package,
while the teacher and automated policy decide whether a particular package
version enters a shared class configuration.

---

## 13. Versioning Strategy

The repository evolves. Versioning communicates the stability of each area
and sets expectations for compatibility.

### Stability Tiers

| Tier | Label | Meaning | Example |
|------|-------|---------|---------|
| **Stable** | `stable` | Backward compatible. Changes are additive or bug-fix only. Breaking changes require a migration plan and deprecation period. | Student API, world save format. |
| **Maturing** | `maturing` | Mostly stable. Minor breaking changes possible with notice and migration guidance. | Lesson format, teacher tooling. |
| **Experimental** | `experimental` | Under active development. May change without notice. Use at your own risk. | New engine subsystems, unreleased features. |
| **Deprecated** | `deprecated` | Will be removed. Migration path documented. Scheduled for removal in a future release. | Old APIs being replaced. |
| **Internal** | `internal` | Not part of the public interface. May change at any time. No compatibility guarantees. | Engine implementation details. |

### Compatibility Expectations

- **Stable interfaces are protected.** A change that breaks a stable
  interface is treated as a serious bug — not a feature request.
- **Deprecation precedes removal.** No stable interface is removed without
  at least one full semester of deprecation notice.
- **Experimental features are clearly marked.** Students and teachers
  should never accidentally depend on experimental behavior.
- **Internal code has no compatibility contract.** Engine internals can
  change freely — that is why they are internal.

---

## 14. Growth Strategy

The repository is designed to grow without restructuring. New capabilities
should slot into existing organizational patterns.

### Adding a New Engine Subsystem

When a new engine capability is needed — weather effects, particle systems,
a pet system — it:

1. Is created as a new directory within the engine package.
2. Follows the existing subsystem pattern: public interface, private
   implementation, associated tests.
3. Integrates with existing subsystems through well-defined interfaces.
4. Does not require restructuring existing subsystems.

### Adding a New Top-Level Directory

A new top-level directory is created only when a new concern emerges that:

1. Does not belong in any existing directory.
2. Has a distinct owner and audience.
3. Justifies the overhead of a new organizational boundary.

Most growth happens within existing directories, not by adding new ones.
The top-level structure is intentionally conservative.

### Adding a New Lesson Module

A new lesson module — a collection of related lessons — is:

1. Placed within the existing lesson structure, under the appropriate
   sprint and topic.
2. Self-contained: includes teacher guide, starter project, solution,
   and assessment criteria.
3. Independent of other lesson modules. A teacher can use it or skip it
   without affecting other lessons.

### Growth That Should Trigger Reconsideration

If growth requires:
- Breaking the dependency hierarchy.
- Creating circular dependencies.
- Splitting a subsystem across multiple directories.
- Duplicating functionality across areas.
- Violating the one-obvious-place principle.

Then the growth is heading in the wrong direction. The repository structure
should be reconsidered before the growth continues.

---

## 15. Architecture Guardrails

These rules protect the repository's integrity. They are absolute — not
guidelines, not preferences, not "usually."

### Structural Guardrails

1. **Engine code never imports from lessons.** The engine is a platform,
   not a consumer of curriculum content.

2. **Engine code never imports arbitrary student modules.** Contributions
   cross the maintained Student API and Explorer Package boundary.

3. **Student code never imports from engine internals.** Students import
   only from the Student API.

4. **Lessons never modify engine code.** Lessons reference engine
   capabilities; they do not alter them.

5. **No file imports upward through the dependency hierarchy.** Upward
   imports are always a mistake.

6. **No circular dependencies between any two modules or subsystems.**
   The dependency graph must remain acyclic.

7. **Every top-level directory has a documented purpose and owner.** No
   directory exists at the root without justification.

8. **Public interfaces are explicit and documented.** Nothing is public
   by accident. If it is not documented as public, it is private.

9. **Tests live with or near what they test.** A developer can find the
   tests for a subsystem by looking in a predictable location.

10. **Documentation is versioned alongside code.** A documentation change
    and the code change it documents are part of the same commit.

11. **Breaking changes to stable interfaces require deprecation.** No
    stable interface is removed without notice and migration guidance.

12. **Examples must run.** A broken example is a bug and is treated with
    the same urgency as a failing test.

13. **Flaky tests are bugs.** A test that does not pass reliably is either
    fixed or removed.

14. **The repository root stays clean.** Only configuration files with
    a project-wide purpose belong at the root. Everything else has a home.

15. **New top-level directories require explicit justification.** The bar
    for a new root directory is high — the concern must not fit anywhere
    existing and must have a distinct owner and audience.

---

## 16. Future Evolution

The repository is organized for the project Explore Studio will become, not
just the project it is today.

### Explorer Studio → Builder Studio

When Explorer Studio evolves into Builder Studio, the repository supports
the transition without restructuring:

- **Engine** — unchanged. Builder Studio uses the same engine.
- **Student API** — unchanged. Builder Studio uses the same API, with all
  capabilities unlocked from the start.
- **Student workspace** — grows. Students have persistent workspaces that
  span multiple semesters in independently owned repositories. The supported
  template and package contract support long-lived projects.
- **Lessons** — supplemented. Builder Studio adds open-ended project ideas,
  challenge prompts, and community-contributed content alongside the
  structured curriculum.
- **Teacher tools** — expanded. Builder Studio adds project review,
  portfolio management, and community moderation tools.
- **Examples** — expanded. Builder Studio showcases community creations as
  examples alongside engine demonstrations.

### Additional Educational Products

The layered repository architecture means the engine and Student API can
support entirely different educational products:

- A physics simulation environment.
- A data visualization playground.
- An interactive storytelling platform.

These would add new top-level directories (for their specific content,
lessons, and examples) while reusing the `engine/`, `tests/`, and `docs/`
directories unchanged.

### What Must Not Change

Even as the repository grows:

- The dependency hierarchy remains one-directional.
- The Student API remains the only interface for student code.
- Engine internals remain private.
- The top-level structure remains recognizable.
- Documentation remains the single source of truth.
- Tests remain reliable and deterministic.

---

## Open Questions

*For resolution as the repository matures:*

1. **Monorepo vs. multi-repo.** Should the engine, curriculum, and teacher
   tools eventually live in separate repositories? A monorepo simplifies
   coordination; separate repos enforce boundaries. At what scale does the
   tradeoff shift?

2. **Package distribution.** How should the engine be distributed to
   students? As a pip-installable package? As a cloned repository? As a
   pre-packaged environment? The distribution model affects repository
   organization.

3. **Student repository provisioning.** Will independent repositories be
   created through GitHub Classroom or another system, and are they private by
   default? The architecture fixes the repository boundary but not its provider
   or access policy.

4. **Third-party lesson ecosystem.** If third-party teachers create and
   share lessons, where do they live? A separate repository? A `contrib/`
   directory? A marketplace external to the repository?

5. **Asset pipeline.** How are assets (sprites, sounds) managed as the
   project grows? Are they in the repository, or fetched separately? Large
   binary assets strain Git; alternative storage may be needed.

6. **Internationalization.** When lessons and documentation are translated,
   where do translations live? Alongside originals? In a parallel directory
   structure? A dedicated `i18n/` directory?

7. **CI/CD structure.** As the repository grows, should CI be organized by
   layer (engine tests, student API tests, example validation) or by change
   (run only what is affected)? The CI structure should mirror the
   repository structure.

---

*This document defines the structural foundation of the Explore Studio
repository. It should guide all organizational decisions and remain stable
as the project grows from Explorer Studio through Builder Studio and beyond.*
