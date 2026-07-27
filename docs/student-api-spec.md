# Explore Studio — Student API Specification

> *The educational interface between students and the engine. Defines what
> students think about, interact with, and learn — not what the engine
> implements. A design specification, not a reference manual.*

---

## 1. Design Philosophy

### Educational-First API

The Student API is not a game development toolkit. It is a programming
curriculum expressed as an interface. Every capability exposed to students
exists because it teaches a specific programming concept — not because a game
engine "should" have that feature.

A feature that is useful for game development but teaches nothing is excluded.
A feature that is technically simple but teaches a rich programming concept is
prioritized.

### Simplicity

The API surface is intentionally small. Students should be able to hold the
entire available vocabulary in their heads. A student who says "I don't know
what I can do" has been given too much. A student who says "I know exactly what
I can do, and I want to combine those things in new ways" is in the sweet spot.

Fewer concepts, used deeply, is better than many concepts, used shallowly.

### Readability

Student code should read like a description of intent:

"My character says hello when the player approaches."

Not:

"Register an event listener on the interaction dispatcher with a callback that
modifies the dialogue component."

The API should make student code self-documenting. A teacher skimming a
student's file should immediately understand what the student intended —
even before running the code.

### Discoverability

Students discover capabilities through exploration, not through memorization.
The API should support a natural progression:

1. Student wonders: "Can my character wave?"
2. Student discovers the capability exists.
3. Student tries it.
4. Student sees the result immediately.
5. Student experiments with variations.

Every capability should be discoverable through this loop — not gated behind
documentation the student must read first.

### Consistency

Similar things work similarly. If one interaction uses a pattern, all
interactions use that pattern. If one entity has a property, similar entities
have the same property. Students should be able to predict how new capabilities
work based on what they already know.

Inconsistency is the enemy of learning. A student who must re-learn a new
pattern for every feature is a student who never builds confidence.

### Progressive Learning

The API reveals itself gradually. A student writing their first character
encounters perhaps three concepts. By the semester's end, the full API is
available — but students have arrived there through six sprints of incremental
expansion, not through a single overwhelming exposure.

No student ever sees "the entire API" on day one. They see what they need,
when they need it, and each new concept builds on concepts they have already
mastered.

---

## 2. Learning Progression

The API grows as students grow. Each stage introduces new programming concepts
through new capabilities, reinforcing what came before.

### Stage 1 — Observe and Modify

Students read and modify existing properties. They change a character's name,
adjust a position, alter a greeting. No new code is written from scratch.

**Programming concepts:** variables, values, assignment, observation.

### Stage 2 — Call and Invoke

Students call methods that already exist. They make their character move, say
something, play an animation. They learn that code produces action.

**Programming concepts:** functions, method calls, parameters, arguments,
return values.

### Stage 3 — Define and Override

Students write their own functions and override default behaviors. Instead of
calling a built-in movement function, they define how their character moves.
They learn that code expresses custom logic.

**Programming concepts:** function definition, control flow, conditionals,
loops.

### Stage 4 — Create and Compose

Students create new objects — a custom item, a unique interaction, a personal
quest. They learn to combine existing pieces into novel wholes.

**Programming concepts:** classes, objects, instantiation, composition,
encapsulation.

### Stage 5 — Interact and Coordinate

Student code interacts with other students' code. A character responds to
another character's dialogue. An object changes state when a quest is
completed. Cross-entity coordination becomes natural.

**Programming concepts:** events, state, inter-object communication, coupling
and cohesion.

### Stage 6 — Design and Refactor

Students own the full creative and technical stack. They design features,
structure their code, refactor for clarity, and maintain backward
compatibility. They think like software engineers.

**Programming concepts:** architecture, design patterns, refactoring, code
review, maintenance.

---

## 3. Core Student Concepts

These are the major concepts students interact with through the API. They
represent what students think about — not how the engine represents them
internally.

### Character

A character is the student's presence in the world. Every student owns exactly
one character. A character has:

- **Identity** — name, appearance, personality description.
- **Position** — where the character is in the world grid.
- **Behavior** — what the character does: movement patterns, idle actions,
  reactions to events.
- **Dialogue** — what the character says in different situations.
- **Relationships** — how the character relates to other characters.

The character is the student's primary creative vehicle. It grows in complexity
as the student's programming ability grows.

### World Object

A world object is something that exists in the world: a tree, a treasure chest,
a signpost, a campfire. Objects are placed in the world grid and can be
interacted with. Objects differ from characters in that they do not have
autonomous behavior — they respond to interactions but do not initiate them.

### Scene

A scene is a distinct view or context within the world. The main world is a
scene. A dialogue screen is a scene. A menu is a scene. Students primarily
work within the world scene — placing entities and defining behaviors — but
may encounter scene transitions as consumers.

### Interaction

An interaction is something that happens when two entities meet. A character
talking to another character is an interaction. A character opening a treasure
chest is an interaction. A character entering a special area is an interaction.

Interactions are the verbs of the world. Students define what happens when
interactions occur.

### Event

An event is something that happens in the world that entities can respond to.
A key press is an event. A timer expiring is an event. Another character
entering the area is an event. The world advancing one frame is an event.

Events are how the world communicates to entities. Students write code that
responds to events.

### State

State is information that persists. A character's friendship level with
another character. Whether a treasure chest has been opened. How many
fragments of the Heart Crystal have been recovered. State is what makes the
world remember.

Students manage state through their characters and objects. State that
persists across save/load is the difference between a world that feels alive
and a world that resets every session.

### Inventory

An inventory is a collection of items a character carries. Items can be found,
given, used, and lost. Inventory teaches collection management — lists,
iteration, search, and modification.

### Quest

A quest is a multi-step objective. "Collect three flowers and bring them to
the librarian." Quests teach sequencing, condition checking, and state
management across multiple interactions.

### Animation

An animation is a visual sequence: walking, waving, dancing, a campfire
flickering. Animations are cosmetic — they make the world feel alive without
affecting world state. Students trigger animations; the engine plays them.

---

## 4. Public API Surface

The following capabilities are available to students. Each is described in
terms of what students can express, not how it is implemented.

### Character Customization

Students can customize:
- Their character's name, appearance, and description.
- Their character's default behavior — what the character does when not
  responding to a specific interaction.
- Their character's responses to events — movement on key press, reaction on
  collision, dialogue on approach.

### Dialogue

Students can define:
- What their character says in different situations.
- Multi-line conversations with branching choices.
- Conditional dialogue that changes based on world state, inventory, or
  relationship levels.
- Greeting dialogue, farewell dialogue, and context-specific dialogue.

### Interactions

Students can define:
- What happens when their character interacts with a world object.
- What happens when another character interacts with theirs.
- What happens when their character enters a special area.
- What happens when a world event occurs (a timer, a state change).

### Animation Control

Students can trigger:
- Simple animations: wave, dance, jump, spin.
- Movement animations: walk in a direction.
- State-based animations: idle, happy, sad, surprised.
- Composite animations: sequences and repetitions.

### Inventory Management

Students can:
- Add items to their character's inventory.
- Remove items.
- Check if an item is present.
- List all items.
- Transfer items to another character.

### World Modification

Students can:
- Place objects in the world (within their designated areas).
- Remove objects they placed.
- Change object properties (color, description, behavior).
- Query what objects exist at a position.

### State Management

Students can:
- Read and write character-specific state (friendship levels, quest progress).
- Read and write object-specific state (opened, collected, activated).
- Read global world state (Heart Crystal fragments recovered).
- Persist state across save/load automatically.

### Quests

Students can:
- Define multi-step quests with objectives and completion conditions.
- Track quest progress per character.
- Trigger events on quest completion.
- Chain quests together.

---

## 5. Lifecycle

From a student's perspective, the world follows a predictable sequence:

### Startup

1. The world is created or loaded from a save file.
2. All entities — characters, objects — are placed in their positions.
3. Each entity's setup code runs: characters take their initial poses, objects
   initialize their state.
4. The world begins updating.

### Main Loop

The main loop runs continuously while the world is active:

1. **Input** — the engine collects keyboard and mouse events.
2. **Update** — each entity's update code runs. Characters move. Animations
   advance. Timers tick.
3. **Interaction check** — the engine checks whether any interaction should
   fire (a character near an object, two characters adjacent).
4. **Render** — the engine draws the world: tiles, entities, UI overlays.

Students write code for steps 2 and 3 — update and interactions. The engine
handles steps 1 and 4.

### Interaction Flow

When an interaction occurs:

1. The engine detects the interaction condition (character near object,
   interaction key pressed).
2. The engine invokes the appropriate interaction code.
3. The interaction code may modify world state, trigger dialogue, change
   inventory, or start an animation.
4. The engine reflects all changes in the next render.

### Shutdown

1. The student or teacher triggers save.
2. The engine serializes all world state — entity positions, properties,
   inventories, quest progress.
3. The world file is written.
4. The engine closes the window and exits.

### Load

1. The student or teacher selects a save file.
2. The engine deserializes the world state.
3. All entities are restored to their saved positions and states.
4. The world resumes exactly where it left off.

---

## 6. Events

Events are how the world communicates that something happened. Students write
code that responds to events. The engine guarantees that events are delivered
deterministically — the same situation always produces the same events in the
same order.

### Event Categories

| Category | Examples | What Students Learn |
|----------|----------|-------------------|
| **Lifecycle events** | World starts, world stops, entity created | Program structure, initialization |
| **Input events** | Key pressed, key released, mouse clicked | Input handling, event-driven programming |
| **Collision events** | Character enters area, entities overlap | Conditions, spatial reasoning |
| **Interaction events** | Talk initiated, item collected, object used | Event dispatch, handler registration |
| **Timer events** | Countdown expired, interval elapsed | Time-based logic, scheduling |
| **State events** | Quest completed, relationship changed, item acquired | State observation, reactive programming |
| **Custom events** | Student-defined events for their own logic | Event design, decoupling |

### Event Response

Students respond to events by defining handler code. A handler is a piece of
student code associated with an event type. When the event fires, the handler
runs.

Students learn to:
- Register handlers for events they care about.
- Write handler code that reads event details.
- Modify world state in response to events.
- Avoid infinite event loops (an event that triggers another event that
  triggers the first).

### Determinism

Events are deterministic. Given the same inputs and world state, the same
sequence of events fires every time. This makes debugging possible: a bug
that occurs can be reproduced by replaying the same inputs.

---

## 7. State

State is what the world remembers. It is the difference between a static
diorama and a living environment.

### Types of State Students Manage

| State Type | Examples | Educational Value |
|-----------|----------|-------------------|
| **Character state** | Friendship levels, mood, personal quest progress | Variables, data associated with identity |
| **Object state** | Opened/closed, lit/unlit, collected/uncollected | Boolean and enumerated state |
| **Inventory state** | Items carried, item quantities | Lists, collections, search |
| **Quest state** | Objectives completed, current step | Multi-variable tracking, progress |
| **World state** | Global variables, Heart Crystal fragments | Shared state, coordination |
| **Relationship state** | Character A's opinion of Character B | Graph concepts, mutual state |

### State and Save/Load

All state that students manage is automatically saved and loaded. Students
do not write serialization code. They declare what state exists; the engine
handles persistence.

This means a student who adds a "happiness" variable to their character does
not also need to learn file I/O. The engine hides that complexity until later
in the curriculum — if at all.

### State Visibility

State is visible. Students can inspect their character's state (and, with
permission, other characters' state). The engine provides a state inspector
for debugging — students can see every variable and its current value.

---

## 8. Interaction Model

Students think about interactions in three simple categories:

### Character ↔ Object

A character approaches an object and presses the interact key. What happens
depends on what the object's creator defined:

- A treasure chest opens and reveals an item.
- A signpost displays a message.
- A campfire lights up.
- A book opens a readable page.

The character initiates. The object responds. This is the simplest interaction
pattern and the first one students learn.

### Character ↔ Character

Two characters meet. One initiates interaction. Both can respond:

- A conversation begins — dialogue is exchanged.
- A gift is given — inventory transfers.
- A friendship gesture is made — relationship state changes.
- A quest is shared — quest state updates for both characters.

Character-to-character interactions are richer because both sides can have
complex behavior. This is where students learn that code written by different
people must cooperate.

### Character ↔ World

A character interacts with the environment itself:

- Entering a special area triggers an effect.
- Stepping on a tile changes the tile.
- Crossing a bridge that another student built.
- Discovering a hidden clearing.

World interactions teach spatial reasoning and environment design. The world
is not just a backdrop — it is an active participant.

---

## 9. Progressive Disclosure

Not all API capabilities are available from day one. The API reveals itself
in layers, matching the curriculum.

### Semester Beginning — Basic Presence

Available: character identity, position, simple dialogue, basic movement.

Hidden: complex interactions, inventory, quests, custom events, animation
control, world modification.

A student's first experience is: "Here is my character. It has a name. It
stands here. When someone talks to it, it says this."

### Early Middle — Interaction and Response

Available: dialogue with choices, object interactions, simple event response,
basic state.

Hidden: multi-step quests, complex state management, composition patterns,
custom events.

A student's mid-semester experience: "My character has conversations. It
remembers who it has talked to. It reacts differently based on friendship."

### Late Middle — State and Persistence

Available: inventory, quests, relationship state, world modification, timer
events.

Hidden: advanced composition, custom event systems, cross-entity coordination
patterns.

A student's late-middle experience: "My character carries items, completes
quests, and changes the world. Progress persists across sessions."

### Semester End — Full Ownership

Available: everything. Custom events, advanced composition, full state
management, world modification, animation sequences.

A student's final experience: "My character is a complete entity with
personality, history, relationships, inventory, quests, and custom behaviors
that interact with the entire world."

### Why Progressive Disclosure Matters

If every capability is available on day one, students are paralyzed by choice.
They do not know what to do first, what matters, or how capabilities relate.

Progressive disclosure solves this: each sprint unlocks a small, coherent set
of new capabilities. Students master what they have before they receive more.
Confidence builds incrementally.

---

## 10. Naming Philosophy

Names in the Student API are chosen with extreme care. A name is the first
thing a student encounters — and the thing they will remember.

### Principles

| Principle | Good Example | Avoid |
|-----------|-------------|-------|
| **Friendly** | `say("Hello!")` | `dispatch_dialogue_event(DialogueType.GREETING, ...)` |
| **Descriptive** | `move_toward(target)` | `mv(target)` |
| **Beginner-readable** | `when_talked_to` | `on_interact_callback` |
| **No abbreviations** | `inventory` | `inv` |
| **No jargon** | `friendship_level` | `affinity_score` |

### The Read-Aloud Test

A student should be able to read their code aloud and have it sound like
English:

> "When my character is talked to, if the friendship level is high, say
> 'Hello friend!' Otherwise, say 'Who are you?'"

If the code reads like that sentence, the names are right. If it reads like
technical documentation, they need work.

### Consistency Within Categories

All dialogue-related names share a pattern. All movement-related names share
a pattern. All inventory-related names share a pattern. Students learn the
pattern once and apply it everywhere within that category.

---

## 11. Error Philosophy

Errors in the Student API are teaching moments, not punishments.

### What Students Should Experience

When a student makes a mistake, the API should:

1. **Detect it immediately.** Errors surface at the point of the mistake, not
   twenty steps later in an unrelated subsystem.

2. **Explain what went wrong.** "Your character tried to move to position
   (15, -3), but the world grid only goes from (0,0) to (30,20). Check your
   coordinates."

3. **Suggest what to do.** "Did you mean (15, 3)?"

4. **Be reproducible.** The same mistake always produces the same error.

5. **Not crash the world.** One student's error does not prevent other
   students' characters from functioning.

6. **Be visible.** Errors appear as in-world indicators or clear console
   messages — not as silent failures.

### What Students Should Not Experience

- Stack traces twenty frames deep in engine code they did not write.
- "Something went wrong" with no further detail.
- Errors that appear intermittently based on timing.
- Silent failures where the world ignores their code with no explanation.
- Errors that require understanding Pygame internals to diagnose.

### The Debugging Loop

The API should support a natural debugging loop:

1. Student runs the world.
2. Something doesn't work as expected.
3. The API reports what went wrong and where.
4. Student reads the error, forms a hypothesis.
5. Student makes a change.
6. Student runs again.
7. Loop until it works.

Each iteration should be fast — seconds, not minutes. Fast feedback makes
debugging a game; slow feedback makes it a chore.

---

## 12. AI Collaboration

The Student API is designed for an era where AI assistants are available to
every student. This is a feature, not a threat — if the API is designed well.

### What the API Enables

**Readable AI output.** Because the API uses friendly, descriptive names and
simple patterns, AI-generated code looks like code a human would write. A
Copilot suggestion using this API should be readable by a beginner.

**Reviewable AI output.** The API's simplicity makes AI-generated code easy to
verify. "Does this code actually make my character wave?" — a student can
answer that by reading two or three lines.

**Modifiable AI output.** AI-generated code is a starting point, not a final
answer. The API's consistency means students can modify AI output without
breaking hidden assumptions. Changing one line does not cascade into failures
elsewhere.

**Explainable AI output.** Because the API concepts map directly to
programming concepts, a student can explain what AI-generated code does:
"This part sets my character's dialogue. This part checks the friendship
level. This part responds differently based on the check."

### What the Student Must Do

The API does not change the student's responsibility:

1. **Understand** every line they accept.
2. **Review** for correctness and style.
3. **Test** in the actual world.
4. **Improve** — rename, restructure, refine.
5. **Explain** to the teacher or a peer.

The API makes these responsibilities achievable. It does not make them
optional.

### API Design for AI

The API is designed so that AI tools produce good code by default — not
because the AI is smart, but because the API is constrained. Small surface.
Consistent patterns. Descriptive names. No hidden state. No magic. These
properties make AI-generated code predictably reasonable, which makes it
easier for students to review and improve.

---

## 13. Stability

The Student API is a promise. When a student writes code in Sprint 1, that
code must still work in Sprint 6.

### Compatibility Goals

| Goal | Description |
|------|-------------|
| **No breaking changes within a semester** | A capability that exists in Sprint 1 is never removed or altered in a way that breaks existing student code during that semester. |
| **Additive changes only** | New capabilities are added. Existing capabilities are not removed or renamed. |
| **Deprecation before removal** | If a capability must eventually change, it is deprecated for a full semester before removal. Students and teachers receive clear migration guidance. |
| **World format compatibility** | A world saved in Sprint 3 loads correctly in Sprint 6. The engine handles format migration transparently. |
| **Documentation stability** | Screenshots, examples, and tutorials remain accurate. Nothing teaches a pattern that later stops working. |

### What Stability Enables

Stable APIs enable:
- Teachers to prepare materials once and reuse them.
- Students to build incrementally without rebuilding.
- Curriculum designers to plan a full semester confidently.
- Community contributors to share examples that remain valid.

### Breaking Change Bar

A breaking change to the Student API requires:
1. A documented educational justification — what concept does the change teach
   better?
2. A migration plan for all affected student code.
3. A full semester of deprecation notice.
4. Approval from both curriculum and engine teams.

This bar is intentionally high. Breaking changes should be rarer than new
features.

---

## 14. Extension Philosophy

The Student API grows by addition, not by modification.

### How New Capabilities Arrive

A new capability — weather effects, pets, a sound system — follows this path:

1. **Design.** The capability is designed as a standalone addition to the
   existing API surface. It uses existing patterns and naming conventions.

2. **Prototype.** The capability is implemented behind a feature flag.
   Teachers can enable it for advanced students.

3. **Validate.** The capability is tested with real students. Does it teach
   something valuable? Is it discoverable? Does it confuse beginners?

4. **Graduate.** If validated, the capability becomes part of the stable API
   in the next semester. Documentation, examples, and curriculum are updated.

5. **Default.** After one semester as an opt-in feature, the capability may
   become available by default — but never required.

### What Extension Must Not Do

- Break existing student code.
- Change the behavior of existing capabilities.
- Force complexity on students who do not need the new capability.
- Require changes to the engine architecture.
- Introduce new dependencies.

### The Extension Test

To evaluate a proposed extension:

1. Can a student who ignores it continue exactly as before?
2. Does it use the same patterns as existing capabilities?
3. Does it teach a clear programming concept?
4. Can it be explained in one paragraph?

If the answer to any of these is "no," the extension needs redesign.

---

## 15. Example Learning Journey

The following traces a hypothetical student — call her Maya — through a
semester with the Student API. It illustrates how the API grows as she grows.

### Sprint 1 — "My character exists."

Maya writes a few lines that give her character a name, a color, and a
position in the Village Square. Her character says "Hi!" when interacted
with. Maya has used variables and assignment. She runs the world and sees
her character standing in the village. It feels real.

### Sprint 2 — "My character moves."

Maya adds movement: her character wanders the Village Square. She discovers
she can control where it goes and how fast. She uses functions for the first
time — a function that describes where to move next. She experiments with
different patterns: circles, random walks, following paths.

### Sprint 3 — "My character has conversations."

Maya writes a dialogue tree. Her character greets other characters
differently based on their names. She learns conditionals: "If the other
character is named Leo, say this. Otherwise, say that." Her character starts
to feel like it has a personality.

### Sprint 4 — "My character remembers."

Maya adds state: a friendship level that increases each time her character
talks to Leo. She uses variables that persist across interactions. Her
dialogue now changes based on friendship: strangers get a formal greeting;
friends get an inside joke. She has learned about state and persistence.

### Sprint 5 — "My character gives quests."

Maya designs a quest: "Bring me three flowers from the Garden, and I will
tell you a secret." She defines objectives, tracks progress, and triggers
a special dialogue when the quest is complete. She has learned about
multi-step logic, collections, and event chaining.

### Sprint 6 — "My character is part of the world."

Maya's character interacts with five other students' characters, gives two
quests, responds to world events, changes its behavior based on the global
Heart Crystal state, and has a fully developed personality expressed through
branching dialogue and conditional animations. Maya's character is no longer
a programming exercise — it is a creation she is proud of.

### After the Semester

Maya can explain every line of her character's code. She can debug it when
something breaks. She can extend it with new features. She understands
variables, functions, conditionals, loops, classes, events, state, and
composition — not because she memorized definitions, but because she used
every one of those concepts to build something that mattered to her.

---

## 16. Future Evolution

The Student API is the stable foundation on which Explore Studio evolves.

### Explorer Studio → Builder Studio

When a class completes the structured semester, the same API supports
Builder Studio — an open-ended creative environment.

In Builder Studio:
- The sprint structure is removed. All API capabilities are available.
- Students build persistent worlds without curriculum constraints.
- Worlds can be shared, forked, and remixed across classes.
- Advanced students create custom events, interaction types, and world
  mechanics.

The API does not change between Explorer Studio and Builder Studio. The
same code Maya wrote in Sprint 1 still runs in Builder Studio. The API is
designed for this continuity.

### Advanced Projects

Beyond Builder Studio, the API supports independent student projects:

- A student builds a complete adventure game with puzzles and narrative.
- A student creates an interactive art installation.
- A student designs a simulation: an ecosystem, a economy, a social network.
- A student prototypes a game mechanic and writes a design document.

The API provides the primitives — entities, interactions, events, state.
Students compose them into anything they can imagine.

### What Evolves

| Evolves | Does Not Evolve |
|---------|-----------------|
| New capabilities added | Existing capabilities remain stable |
| New event types | Existing events keep their behavior |
| New interaction patterns | Existing interactions are unchanged |
| New entity types | Existing entity types are backward compatible |
| Performance improvements | API surface remains consistent |
| Engine internals | Student-facing interface is preserved |

### The Decade Test

A student who completes Explorer Studio in 2026 should be able to open their
world in 2036 and have it run. The engine may have evolved dramatically. The
API may have expanded significantly. But the code they wrote — their
character, their dialogue, their quests — should still work.

This is the ultimate stability goal. It is aspirational. It guides every
decision about what to expose and how to expose it.

---

## Design Rationale

### Why a small API surface?

A large API surface overwhelms beginners and encourages shallow usage. A small
surface forces deep engagement with each concept. Students who master ten
capabilities thoroughly are better programmers than students who dabble in
fifty.

### Why concepts before code?

Students learn programming concepts — variables, functions, events — through
the API. The API is designed so that each concept maps naturally to a
capability. The student does not learn "this is how you define a function in
Python" in isolation; they learn "this is how you make your character move"
and discover that functions are the tool for that job.

### Why progressive disclosure?

Revealing the full API on day one would be like handing a student a dictionary
and saying "learn English." Progressive disclosure provides vocabulary in
usable chunks, each building on the last. Students are never asked to use a
concept they have not been taught.

### Why no Pygame exposure?

Pygame is an implementation detail. It is complex, inconsistently documented,
and oriented toward game developers — not programming beginners. Exposing
Pygame to students would force them to learn surface management, event queues,
and rendering loops before they can make a character say "hello." The Student
API exists specifically to prevent that.

### Why stable across semesters?

A moving target cannot be taught. If the API changes between semesters,
teacher materials become obsolete, student examples break, and the curriculum
requires constant revision. Stability is not a luxury — it is a prerequisite
for an educational platform.

---

## Open Questions

*For resolution before or during Student API implementation:*

1. **Dialogue system complexity ceiling.** How deep should dialogue trees
   go? Two levels? Unlimited? Should there be a complexity cap to prevent
   students from getting lost in their own dialogue logic?

2. **Permission model.** Should students be able to read other students'
   character state? Modify it? What is the default permission and how is it
   configured?

3. **Error display mechanism.** Should errors appear as in-world speech
   bubbles, a console panel, or both? What is most accessible to beginners?

4. **Animation authoring.** Do students define animations frame-by-frame, or
   select from a library of pre-built animations? A frame-by-frame system
   teaches sequencing but may be too complex for beginners.

5. **World modification permissions.** Which areas can students modify? The
   entire world? Designated zones? Only objects they created?

6. **Cross-character communication.** When Character A interacts with
   Character B, whose code runs first? Who has the final say? The interaction
   model needs clear ordering guarantees.

7. **Save file inspection.** Should students be able to open and read save
   files? This teaches data formats but risks save corruption. What is the
   right balance?

8. **Testing student code.** Should the API include testing utilities so
   students can verify their character behaves correctly without running the
   full world?

---

*This document defines the educational contract between the engine and the
student. It should guide all Student API implementation decisions and remain
stable across multiple semesters of Explorer Studio.*
