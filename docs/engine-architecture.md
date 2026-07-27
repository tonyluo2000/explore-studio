# Explore Studio — Engine Architecture Specification

> *The architectural reference for the educational game engine that powers
> Explorer World. Defines structure, responsibilities, boundaries, and
> philosophy — not implementation.*

---

## 1. Architectural Philosophy

### Why the Engine Exists

The Explore Studio engine exists to give students a canvas. It handles the
mechanical work of putting pixels on a screen, reading keyboard input, and
managing a world grid — so students can focus on the creative and intellectual
work of designing characters, writing dialogue, and building interactions.

The engine is not the product. The engine is the platform that makes the product
possible.

### Educational-First Architecture

Every architectural decision must answer one question: **"Does this help students
learn programming?"**

A feature that makes the engine more powerful but harder to understand is a bad
feature. A subsystem that simplifies student code at the cost of hiding important
concepts is poorly designed. The engine's job is to make learning visible, not to
make complexity disappear.

This principle overrides every other consideration — performance, elegance,
generality, and conventional wisdom included.

### Simplicity Over Flexibility

A flexible engine can do many things. A simple engine can be understood. For
Explore Studio, understanding matters more than flexibility.

When a choice exists between a general solution and a specific one, prefer the
specific one. A general solution introduces abstraction that students must
mentally navigate. A specific solution is concrete, visible, and debuggable.

Flexibility will be added later — when students are ready to understand why it
exists.

### Readability Over Cleverness

The engine's internal code should be readable by a teacher who is not a
professional software engineer. It should use plain patterns, descriptive naming,
and obvious control flow.

Clever optimizations, dense one-liners, and "Pythonic" trickery have no place in
an educational engine. The engine's source code is itself a teaching tool — it
models the code quality we expect from students.

### Gradual Reveal of Complexity

The engine must support a world that starts nearly empty and grows rich over six
sprints. This means the engine itself must reveal complexity gradually.

A student writing their first character should not need to understand the
animation system. A student implementing a dialogue tree in Sprint 3 should not
be exposed to the save/load subsystem. The engine's architecture must support
partial understanding — students engage with only the layer relevant to their
current task.

This is not about hiding internals. It is about not requiring knowledge before it
is needed. Every subsystem should be independently approachable.

---

## 2. Design Goals

| Goal | Description |
|------|-------------|
| **Easy to understand** | A teacher can read any engine subsystem and explain it. A motivated student can explore it. |
| **Modular** | Subsystems have clear boundaries. A change to rendering does not affect dialogue. A change to input does not break saving. |
| **Beginner friendly** | The student-facing surface exposes concepts, not machinery. A student thinks "place my character" — not "instantiate a sprite in the entity registry." |
| **Deterministic** | Given the same world state and input, the engine produces the same output every time. This makes debugging possible: bugs are reproducible. |
| **Easy to debug** | When something goes wrong, the engine provides clear, actionable information — not a stack trace twenty frames deep in unfamiliar code. |
| **Stable** | The interfaces students depend on do not change mid-semester. A character written in Sprint 1 still works in Sprint 6 without modification. |
| **Extensible** | The engine can grow from Explorer World into Builder Studio without architectural redesign. New subsystems can be added without restructuring existing ones. |

---

## 3. Design Non-Goals

The following are explicitly not goals for the Explore Studio engine:

| Non-Goal | Rationale |
|----------|-----------|
| **AAA game engine** | The engine does not need to compete with commercial products. It needs to teach programming. |
| **Unity or Godot replacement** | These are professional tools with decades of development. Explore Studio is an educational platform. |
| **Multiplayer** | Simultaneous real-time interaction introduces networking complexity that distracts from learning Python. Collaboration happens through Git. |
| **Networking** | No client-server architecture. No sockets. No message passing between machines. |
| **Entity-Component-System (ECS)** | ECS is powerful but abstract. It introduces terminology and patterns that obscure rather than reveal programming concepts for beginners. |
| **Advanced physics** | Simple grid-based movement and basic collision detection are sufficient. Gravity, momentum, and rigid bodies belong in a physics curriculum, not a programming curriculum. |
| **Scripting language** | Python is the scripting language. The engine does not embed or interpret a secondary language. |
| **Plugin marketplace** | The engine is not a platform for third-party extensions. Extensibility means students and teachers can extend their world — not that strangers can publish engine plugins. |
| **Cross-platform GUI toolkit** | The engine targets desktop environments. Web, mobile, and console are out of scope. |
| **High-performance rendering** | The engine renders a small, tile-based world. It does not need shaders, GPU acceleration, or frame-rate optimization beyond basic usability. |

---

## 4. High-Level Architecture

The engine is organized as a layered stack. Each layer depends only on the layer
directly beneath it. Higher layers are closer to students; lower layers are
closer to the machine.

```
┌──────────────────────────┐
│      Student Code         │  ← Students write this
├──────────────────────────┤
│      Student API          │  ← The engine's educational surface
├──────────────────────────┤
│      Course Engine        │  ← Core subsystems (scenes, entities, etc.)
├──────────────────────────┤
│      Pygame               │  ← Rendering, input, audio, windowing
├──────────────────────────┤
│      Operating System     │  ← Files, display, hardware
└──────────────────────────┘
```

### Layer Responsibilities

**Student Code**

What students write. Characters, dialogue, object behaviors, interaction logic.
This layer is creative, personal, and owned by individual students. It should
never touch Pygame directly. It should never manage the application lifecycle.
It should express intent — "when the player approaches, say hello" — not
mechanics.

**Student API**

The engine's educational surface. A curated set of capabilities exposed to
students through simple, discoverable interfaces. This layer translates
educational intent ("place my character") into engine operations. It is the
contract between the engine and the learner. It must remain stable across an
entire semester.

**Course Engine**

The core subsystems that make the world work: scene management, entity lifecycle,
interaction dispatch, world state, asset loading, save/load, animation, and UI.
This is the engine proper — the code that coordinates rendering, input, and world
logic. Students do not see this layer directly.

**Pygame**

The rendering, input, and audio library that talks to the operating system.
Pygame is an implementation detail. It is chosen because it is simple, stable,
well-documented, and has no opinion about how games should be structured. It
could be replaced without affecting any layer above it — though replacement is
not planned.

**Operating System**

The host environment. The engine runs on the student's machine. No servers, no
containers, no virtualization.

---

## 5. Core Engine Responsibilities

The engine owns the following responsibilities. Each is described in terms of
what it does, not how it is implemented.

### Application Lifecycle

The engine manages startup, the main loop, and shutdown. Students never write a
game loop. The engine calls student code at well-defined moments — setup, update,
teardown — and handles everything else.

### Rendering

The engine draws the world to the screen. It renders tiles, entities, UI
overlays, and visual effects. Students describe what should appear; the engine
handles when and how it is drawn.

Rendering order is deterministic. The world grid draws first, then entities, then
UI. This guarantees that a character always appears on top of the grass, and a
dialogue box always appears on top of a character.

### Input

The engine reads keyboard and mouse input and translates raw events into
meaningful actions: movement, interaction, menu navigation. Students receive
clean, interpreted input — "the player pressed the interact key near the
fountain" — not raw key codes.

### Scenes

The engine manages transitions between different views: the main world, a
dialogue screen, a menu, a splash screen. Each scene is a self-contained context.
Only one scene is active at a time. Scene transitions are explicit and
deterministic.

### Assets

The engine loads and manages images, sounds, and other media. Students reference
assets by name. The engine handles loading, caching, and cleanup. Asset formats
are simple and standard — PNG images, WAV sounds — and never require specialized
tools.

### World State

The engine maintains the current state of the world: which tiles exist at which
coordinates, which entities are present, what properties each entity has, and
what the global world variables are.

World state is the single source of truth. Rendering reads from world state.
Student code reads from and writes to world state. Save/load serializes world
state. There is no hidden state, no implicit side effects, and no state stored
outside the world model.

### Interactions

The engine dispatches interactions between entities. When a student character
approaches another character and presses the interact key, the engine determines
which interaction should fire and invokes it. Interaction dispatch is
deterministic: given the same world state and input, the same interaction always
fires.

### Animation

The engine supports simple, frame-based animation: a character walking, a
campfire flickering, a fountain sparkling. Animations are defined as sequences of
frames with timing. Students trigger animations; the engine plays them.
Animation is always cosmetic — it does not affect world state.

### User Interface

The engine provides basic UI primitives: dialogue boxes, menus, status displays,
and text overlays. These are simple, readable, and consistent. UI is always
rendered on top of the world and never becomes part of the world state.

### Audio

The engine plays sounds and, optionally, background music. Audio is triggered by
events: a door opens, a character speaks, a treasure chest is found. Audio is
always optional — the world must be fully functional with sound disabled.

### Save and Load

The engine serializes the entire world state to a file and restores it later.
Saving is explicit — triggered by the student or teacher. Loading restores the
world to exactly the state it was in when saved. Save files are human-readable
where practical, so students and teachers can inspect them.

---

## 6. Student Responsibilities

Students are responsible for creative, behavioral, and interactive content. They
do not modify engine internals.

### What Students Own

| Responsibility | Description |
|---------------|-------------|
| **Character identity** | Name, appearance, personality — the creative definition of who the character is. |
| **Character behaviors** | What the character does: idle animations, wandering patterns, reactions to events. |
| **Dialogue** | Everything a character says, including conditional responses and multi-step conversations. |
| **Object interactions** | What happens when a character interacts with a world object: opening a chest, reading a book, lighting a campfire. |
| **World contributions** | Placing objects, designing areas, contributing to the shared environment. |
| **Creative direction** | Deciding what their corner of the world feels like, what stories their character participates in, what surprises they hide. |

### What Students Do Not Own

| Boundary | Rationale |
|----------|-----------|
| **Engine internals** | Rendering, input, audio, and scene management are the engine's job. Students should not need to understand them. |
| **Other students' characters** | Students can interact with classmates' characters through the engine's interaction system but cannot modify them directly. |
| **The application lifecycle** | Startup, shutdown, and the main loop belong to the engine. |
| **Asset pipeline** | Students provide assets; the engine loads and manages them. |
| **World serialization** | The engine handles saving and loading. Students express what should be saved; the engine handles how. |

### The Student Contract

The engine promises students: "Write your character here. The engine will put it
in the world, handle input, render it, save it, and load it. You focus on what
makes your character yours."

---

## 7. Teacher Responsibilities

Teachers own the educational experience. The engine supports them — it does not
replace their judgment.

### What Teachers Own

| Responsibility | Description |
|---------------|-------------|
| **Curriculum design** | What concepts are taught in which order, and how they map to engine features. |
| **World progression** | When new areas unlock, what the sprint deliverables are, how the world evolves over the semester. |
| **Sprint integration** | How student contributions are merged, reviewed, and integrated into the shared world each sprint. |
| **Code review** | Evaluating student work, providing feedback, ensuring code quality and world consistency. |
| **Classroom culture** | Setting expectations for collaboration, AI use, and code ownership. |
| **Pacing and adaptation** | Adjusting the curriculum to the class's needs — spending more time on difficult concepts, accelerating through familiar ones. |

### What Teachers Do Not Need to Do

- Modify engine source code to support a lesson.
- Debug engine internals when a student's code fails.
- Understand Pygame or windowing details.
- Manage asset formats or rendering pipelines.

### The Teacher Contract

The engine promises teachers: "Configure the world. Guide your students. Review
their work. The engine will handle the machinery."

---

## 8. Ownership Boundaries

Clear ownership prevents confusion, reduces debugging time, and teaches students
about software architecture through lived experience.

### Summary Table

| Concern | Engine | Student | Teacher |
|---------|--------|---------|---------|
| Rendering | ✓ | | |
| Input handling | ✓ | | |
| Application lifecycle | ✓ | | |
| Scene management | ✓ | | |
| Asset loading | ✓ | | |
| World state storage | ✓ | | |
| Save / Load | ✓ | | |
| Audio playback | ✓ | | |
| UI primitives | ✓ | | |
| Character appearance | | ✓ | |
| Character dialogue | | ✓ | |
| Character behaviors | | ✓ | |
| Object interactions | | ✓ | |
| World object placement | | ✓ | |
| Creative direction | | ✓ | |
| Curriculum design | | | ✓ |
| Sprint structure | | | ✓ |
| Code review | | | ✓ |
| Classroom pacing | | | ✓ |

### Boundary Enforcement

The engine enforces ownership boundaries through its design, not through
permission systems. Students physically cannot modify engine internals because
the engine is a separate package they import — not code they edit. Teachers do
not need to police boundaries; the architecture makes violations impossible.

---

## 9. Engine Growth Strategy

The engine is not built all at once. It grows incrementally, matching the
semester's six-sprint progression. Each version adds precisely the capabilities
needed for the next sprint — nothing more.

### Version Progression

| Version | Capability | What Students Can Now Do |
|---------|-----------|-------------------------|
| **0.1** | Window and grid | See the world. A window opens. A tile grid renders. The Village Square exists as colored tiles. |
| **0.2** | Entities and characters | Place characters in the world. Each student's character appears at a position. Characters have simple visual representation. |
| **0.3** | Movement and input | Characters respond to keyboard input. Students write simple movement behaviors. The world feels alive. |
| **0.4** | Interactions | Characters interact with objects and each other. Dialogue appears. Objects respond. The world becomes interactive. |
| **0.5** | State and persistence | The world remembers. Objects change state. Save and load work. Progress persists across sessions. |
| **0.6** | Scenes and UI | Menus, dialogue screens, splash screens. The world has structure beyond the main grid. |
| **1.0** | Semester complete | All subsystems integrated. The engine supports a full six-sprint semester. Stable, documented, tested. |

### Why Incremental

Building the full engine before the first student uses it risks building the
wrong thing. Building incrementally — one sprint's worth of capability at a
time — ensures every subsystem is validated by actual classroom use before the
next subsystem is designed.

It also mirrors the student experience: the engine grows in complexity at the
same pace as the students' abilities. No one — student, teacher, or engine
developer — is overwhelmed.

---

## 10. Dependency Philosophy

Dependencies flow in one direction: downward through the layers. Upper layers
depend on lower layers. Lower layers never depend on upper layers.

```
Student Code
    │
    ▼ depends on
Student API
    │
    ▼ depends on
Course Engine
    │
    ▼ depends on
Pygame
```

### Rules

1. **Student code imports only the Student API.** It never imports Pygame,
   engine internals, or operating system modules directly.

2. **The Student API imports only the Course Engine.** It does not import
   Pygame. It translates educational concepts into engine operations.

3. **The Course Engine imports Pygame.** This is the only layer that touches
   the rendering and input library. If Pygame is ever replaced, only this layer
   changes.

4. **No layer imports upward.** The engine never depends on student code. The
   Student API never depends on a specific curriculum.

### Why This Matters

One-directional dependencies make the system understandable. A student's import
statement tells the whole story: they import from the student API, and nothing
else. A teacher debugging a rendering issue knows to look in the Course Engine
layer. There is no spaghetti of cross-layer imports to untangle.

Pygame should not leak into student code. The moment a student writes
`import pygame`, the architecture has failed — the engine has not provided a
sufficient educational surface, and the student has been forced to reach past it.

---

## 11. Extensibility Philosophy

The engine is designed to grow without restructuring.

### How Features Are Added

A new feature — particle effects, weather, an inventory system — is added as a
new subsystem within the Course Engine layer. It does not modify existing
subsystems. It does not change the Student API unless the feature is exposed to
students. It does not break existing student code.

### Principles

| Principle | Description |
|-----------|-------------|
| **Minimal changes** | Adding a feature should add code, not restructure existing code. New files, new subsystems — not rewrites. |
| **Stable interfaces** | The Student API expands by addition. Existing capabilities are never removed or altered in a breaking way during a semester. |
| **Backward compatibility** | A world built in Sprint 1 must load and run correctly in Sprint 6. The engine evolves; the world format evolves with it — but old worlds remain valid. |
| **Opt-in complexity** | New features are available but not required. A student who mastered basic movement in Sprint 2 is not forced to learn particle effects in Sprint 5. |

### The Extension Test

To evaluate a proposed extension, ask:

1. Does it require changing existing engine subsystems?
2. Does it break existing student code?
3. Does it force complexity on students who do not need it?

If the answer to any of these is "yes," the extension needs redesign.

---

## 12. Error Philosophy

Errors are learning opportunities. The engine's error behavior should teach, not
frustrate.

### Principles

| Principle | Description |
|-----------|-------------|
| **Friendly error messages** | Errors are written in plain language, not stack-trace jargon. "Your character tried to move off the world grid at position (12, -1). The world grid goes from (0,0) to (30,20)." — not `IndexError: list index out of range`. |
| **Deterministic failures** | The same mistake produces the same error every time. Errors are reproducible, which makes them debuggable. No race conditions, no timing-dependent failures. |
| **Educational debugging** | Error messages suggest what might be wrong and where to look. They guide students toward the solution without giving it away. |
| **Visible mistakes** | When student code has a problem, the problem is visible. A character that fails to load appears as a placeholder — not as a silent absence. A broken interaction shows an error indicator — not nothing. |
| **No magic** | The engine never silently corrects student mistakes. It does not guess intent. It does not provide defaults that hide bugs. If the student wrote something wrong, the engine reports it — clearly, kindly, and immediately. |
| **Safe failures** | An error in one student's character does not crash the world. It does not prevent other characters from loading. It does not corrupt the save file. Errors are isolated. |

---

## 13. Testing Philosophy

The engine must be trustworthy. Teachers and students must be confident that when
something goes wrong, it is in their code — not in the engine.

### Engine Testing

Every engine subsystem has automated tests. These tests verify behavior, not
implementation. They ask: "When the engine is asked to do X, does it do X?" They
do not ask: "Does the engine use pattern Y internally?"

Tests are the engine's safety net. When a new feature is added, existing tests
confirm that nothing broke. When a bug is found, a test is added to prevent
regression.

### Regression Testing

The engine maintains a suite of tests that run on every change. These tests cover
every subsystem, every interaction pattern, and every edge case discovered during
development. A failing regression test blocks a change — no exceptions.

### Examples as Tests

Every example in the engine's documentation is also a test. If the documentation
says "to make a character wave, write this code," then that exact code is run as
part of the test suite. Documentation that does not match reality is caught
immediately.

### Reproducibility

All tests are deterministic. They do not depend on timing, random numbers, or
external resources. A test that passes on one machine passes on every machine. A
test that fails can be debugged by anyone, anywhere.

---

## 14. Performance Philosophy

Educational clarity is more important than optimization.

### What Matters

- The world renders smoothly at the target resolution and frame rate.
- Input responds without perceptible lag.
- Saving and loading complete in a reasonable time — seconds, not minutes.
- Thirty student characters on screen at once does not cause stuttering.

### What Does Not Matter

- Supporting hundreds of simultaneous entities.
- Rendering at resolutions beyond the target display.
- Frame rates beyond what the human eye can perceive.
- Memory usage below what modern machines provide in abundance.
- Startup time measured in milliseconds rather than seconds.

### The Readability Rule

If an optimization makes the engine's code harder for a teacher to understand,
the optimization is rejected. The engine's source code is teaching material. It
must remain readable even when a faster implementation exists.

Performance work is done only when a real, observable problem affects the
classroom experience — not when a benchmark suggests room for improvement.

---

## 15. Accessibility Philosophy

The engine should be usable by as many students as possible, regardless of
ability.

### Design Commitments

| Commitment | Description |
|------------|-------------|
| **Readable UI** | Text is large enough to read comfortably. Contrast is sufficient. Fonts are clear and legible. |
| **Keyboard-first** | Every action can be performed with a keyboard. Mouse input is supplemental, not required. This supports students with motor impairments and aligns with the programming focus — typing is the primary activity. |
| **Color considerations** | Color is never the sole indicator of meaning. Status indicators use shape and position in addition to color. The default palette is chosen for readability, not just aesthetics. |
| **Inclusive design** | The engine's visual style, example characters, and default content avoid stereotypes and represent diverse identities. Students can customize their characters to reflect themselves. |
| **Configurable** | Text size, sound volume, and input bindings are configurable. Students with different needs can adapt the engine without modifying source code. |

### Version 1 Scope

Version 1 focuses on the commitments above. Comprehensive accessibility —
screen-reader support, full remapping, internationalization — is deferred to
future versions. The architecture does not prevent these additions; it simply
does not implement them in the initial release.

---

## 16. Long-Term Evolution

The engine architecture is designed for a future beyond Explorer World.

### Explorer Studio → Builder Studio

After a class completes the structured six-sprint semester, the same engine
should support **Builder Studio** — an open-ended creative environment.

Builder Studio removes the sprint structure and lets students build freely:
custom worlds, persistent projects, community sharing. The engine architecture
supports this because:

- The world model is general, not specific to the Heart Crystal story.
- The Student API is capability-based, not curriculum-locked.
- Save/load is format-versioned, allowing worlds to persist across engine
  versions.
- Scene management supports arbitrary world layouts, not just the six-sprint
  progression.

### Future Educational Products

The engine's layered architecture means the Course Engine — rendering, input,
entities, interactions — could support entirely different educational products:

- A physics simulation environment.
- A data visualization playground.
- An algorithm animation studio.
- A collaborative storytelling platform.

These would replace the Student API and student code layers while reusing the
Course Engine underneath. The architecture separates "how the world works" from
"what students do with it" — and that separation enables reuse.

### What Will Not Change

Even as the engine evolves, the core principles remain:

- The engine serves education, not the other way around.
- Students own their creations.
- Complexity is revealed gradually.
- Errors teach, not frustrate.
- Readability beats optimization.
- Stable interfaces protect student work.

---

## Architecture Principles Summary

These principles guided every decision in this document and should guide every
future implementation decision:

| Principle | Meaning |
|-----------|---------|
| **Separation of concerns** | Each layer has one job. Rendering does not handle input. Dialogue does not manage save files. |
| **Composition over complexity** | Complex behavior emerges from composing simple pieces. The engine provides simple pieces; students compose them. |
| **Progressive disclosure** | Students see only what they need at their current level. The full engine is revealed gradually across six sprints. |
| **Stable educational interfaces** | What students learn in Sprint 1 still works in Sprint 6. The engine grows but does not break its promises. |
| **Clear ownership** | Engine, student, and teacher responsibilities are explicit and non-overlapping. |
| **Simplicity first** | The simplest solution that meets the educational need is always chosen. Complexity is added only when proven necessary. |
| **Convention over configuration** | The engine provides sensible defaults. Students can customize, but they never must configure before they can create. |
| **The engine serves the curriculum** | This is the overriding principle. Every subsystem, every interface, every design tradeoff is evaluated against it. |

---

## Open Questions

*For resolution before or during Phase 1 engine implementation:*

1. **World grid size.** What is the target world dimension? 30×20 tiles? 40×30?
   This affects rendering, memory, and the complexity of world-building lessons.

2. **Entity limit.** Is there a practical limit on simultaneous entities? Thirty
   students × one character each, plus world objects — what is the engine's
   comfortable capacity?

3. **Asset pipeline.** How do students provide sprite sheets, sound files, and
   other assets? Is there a standard directory layout, or does the engine
   provide a simple asset manager?

4. **Dialogue system depth.** How complex can dialogue trees become? Simple
   linear conversations? Branching trees? State-dependent responses? The
   interaction system's complexity ceiling should be established early.

5. **Save file format.** Human-readable (JSON, YAML) or binary? Readable is
   preferred for educational transparency, but the tradeoffs need evaluation.

6. **Error display mechanism.** How are errors surfaced to students? In-world
   indicators? A console panel? Both? The mechanism affects the Student API
   design.

7. **Configuration system.** How do teachers configure the world — sprint
   unlocks, enabled features, class-specific settings? A configuration file?
   A teacher dashboard? Both?

---

*This document is the architectural reference for the Explore Studio engine. It
should remain stable through Version 1. Implementation decisions should be
traceable back to principles defined here.*
