# Explorer World — Design Specification

> *The foundational product-design document for the semester-long shared world
> built by Explore Studio students. Defines what Explorer World is — not how it
> will be programmed.*
>
> **Contribution-model note:** The shared world is assembled from independently
> owned student repositories through Explorer Packages. See the
> [Student Contribution and Class-World Model](architecture/student-contribution-model.md).

---

## 1. Vision

**Explorer World** is a shared, student-built virtual world. Over the course of a
semester, an entire class collaboratively designs, codes, and evolves a single
living environment — a small, charming world that grows more detailed and
interactive with each passing week.

It exists because programming is best learned through building something that
matters. Traditional programming exercises — calculate a factorial, sort a list,
print a pyramid of asterisks — teach syntax but not craftsmanship. They offer no
audience, no legacy, and no reason to care about quality.

Explorer World flips that. Students are not completing assignments. They are
contributing to a shared creation that their classmates will explore, their
teacher will review, and future students may inherit as a starting point.

**Why one shared world instead of individual games?**

Individual projects isolate students. One student struggles alone with a bug;
another races ahead without helping. A shared world creates natural
collaboration: one student builds a bridge, another writes the character that
crosses it, a third debugs why the bridge collapsed. The interdependence is the
point.

Students learn that software is not written alone. It is negotiated, reviewed,
published through stable contracts, assembled, and maintained together.

---

## 2. Educational Goals

Explorer World is a programming curriculum disguised as a game studio. Every
design decision serves an educational purpose.

### Programming

Students write real Python — not a simplified drag-and-drop language — from their
first session. They encounter variables, control flow, functions, data
structures, and object-oriented concepts not through lectures but because their
world needs them.

### Creativity

The world rewards creative expression. Students decide what their character says,
how it behaves, what objects populate the village, and what secrets hide in the
forest. Technical constraints exist — as they do in all software — but within
those constraints, ownership is absolute.

### Collaboration

Each student uses Git in an independent repository. They create branches, make
commits, review changes, and publish versioned Explorer Packages for approval.
The class learns to resolve contract, namespace, and compatibility conflicts
without merging student repositories or committing to the official engine.
These are not abstract lessons about "teamwork." They are the practical
mechanics of building shared software.

### Debugging

Bugs are inevitable when thirty independently developed contributions meet in
one class world. Explorer World treats debugging not as failure but as a core
skill. Students learn to read errors, trace logic, write tests, and ask precise
questions — habits that distinguish effective programmers at every experience
level.

### Software Engineering

The semester mirrors professional practice: version control, code review,
incremental delivery, backward compatibility, documentation, and testing.
Students leave not just knowing Python syntax but understanding how software
teams operate.

### AI Collaboration

Students use AI assistants — including GitHub Copilot — throughout the semester.
The goal is not to ban AI or to rely on it blindly. Students learn to prompt
effectively, review AI-generated code critically, understand every line they
accept, debug when the AI is wrong, and improve what the AI produces. AI is a
junior collaborator; the student is the engineer.

---

## 3. Target Audience

Explorer Studio students are typically middle and high school learners,
approximately ages 12–18.

**Prior experience assumptions:**

- No programming experience required.
- Basic computer literacy (typing, file navigation, using a web browser).
- Familiarity with video games as a player, not a developer.

The curriculum accommodates mixed-experience classrooms. Students with prior
coding experience can take on more complex features while beginners build
foundational skills — all within the same shared world.

---

## 4. World Overview

Explorer World is a small, top-down, tile-based environment. It feels like a
cozy village in a storybook: warm, inviting, and full of small surprises.

The world begins nearly empty — a grassy field with a single structure — and
expands over six sprints as students add locations, characters, objects, and
interactions.

**Possible locations include:**

| Location | Character |
|----------|-----------|
| Village Square | The heart of the world. A central gathering place with a fountain, benches, and notice board. |
| Forest | A wooded area with winding paths, hidden clearings, and friendly woodland creatures. |
| River | A stream that winds through the world, crossed by bridges students build. |
| Playground | An open area for playful interactions — games, dances, and experiments. |
| Mountain | A rocky highland at the world's edge, home to secrets and late-semester challenges. |
| Library | A quiet building where characters can share knowledge, leave messages, and discover world lore. |
| Garden | A cultivated space where students plant and grow things that persist across sessions. |

*The final map is not predetermined. Locations emerge as students and the
teacher make creative decisions throughout the semester.*

---

## 5. Story

The world has a simple unifying narrative:

> **The Heart Crystal** — the source of the world's warmth, color, and
> connection — has fractured. The world has grown dim. Characters have become
> isolated. The land waits for someone to restore it.

Over six development sprints, students gradually restore the world. Each sprint
corresponds to a fragment of the Heart Crystal being recovered and returned to
the Village Square.

The story is intentionally simple. It provides:

- A reason for the world to start sparse and grow richer over time.
- A natural cadence for introducing new features each sprint.
- An emotional through-line: students are not just coding, they are healing a
  world.
- Room for student creativity — how each fragment is recovered is unique to each
  class.

The story never becomes complex lore. It is a gentle container, not a heavy
narrative burden.

---

## 6. Characters

Each student creates and owns one unique character for the entire semester.

### Character Identity

A character has:

- **Name** — chosen by the student.
- **Appearance** — simple visual customization (color, shape, size) within the
  world's art style.
- **Personality** — expressed through dialogue, default behaviors, and how the
  character responds to interactions.
- **Dialogue** — lines the character says when spoken to, which students write
  and revise throughout the semester.
- **Behaviors** — what the character does when idle (wandering, sitting, dancing,
  reading).
- **Friendships** — optional relationships with other student characters,
  expressed through special interactions.

### Character Evolution

Characters are not static. As students learn new programming concepts, they
enhance their characters:

- Early sprint: a character that stands still and says one line.
- Mid sprint: a character that wanders, responds to multiple interactions, and
  remembers state.
- Late sprint: a character with complex behaviors, conditional dialogue, and
  persistent relationships.

The character grows alongside the student's programming ability.

### Ownership

A student's character is theirs. Other students can interact with it but cannot
modify it without permission. This creates healthy boundaries and a sense of
personal investment.

---

## 7. World Objects

The world is populated with interactive objects — the nouns of the environment
that students place, configure, and program.

Objects range from simple to complex, matching the student's growing skill:

| Complexity | Examples |
|-----------|----------|
| **Static** | Trees, flowers, rocks, fences, signposts |
| **Interactive** | Treasure chests that open, doors that lead somewhere, campfires that glow, books that display text |
| **Stateful** | Gardens that grow, bridges that can be built or broken, fountains that change color, lamps that turn on at "night" |
| **Conditional** | Gates that open when a condition is met, puzzles that require multiple steps, objects that respond differently to different characters |

Objects are placed in the world by students. Every object placement is a
contribution to the shared environment. The world becomes richer as more objects
are added.

All objects follow the world's simple visual style: readable, charming, and
consistent. A tree added by one student should look like it belongs next to a
bench added by another.

---

## 8. Interactions

Characters interact with the world and with each other. Every interaction is
programmed by students, making interaction design a core part of the learning
experience.

### Character-to-Object Interactions

| Interaction | Educational Purpose |
|------------|-------------------|
| **Examine** | String handling, conditional messages |
| **Collect** | Variables, inventory, lists |
| **Use** | Functions, state changes |
| **Place** | World modification, coordinates |

### Character-to-Character Interactions

| Interaction | Educational Purpose |
|------------|-------------------|
| **Talk** | Strings, dialogue trees, conditionals |
| **Wave** | Simple animation triggers |
| **Give gift** | Inventory transfer, data between objects |
| **Dance** | Sequences, loops, timing |
| **Follow** | Pathfinding concepts, state machines |

### Design Principle

Every interaction teaches a programming concept. No interaction exists purely
for gameplay — it exists because implementing it requires students to learn
something specific and meaningful.

Interactions start simple (press a key, see a message) and grow complex
(conditional responses, multi-step puzzles, persistent state) as the semester
progresses.

---

## 9. Semester Progression

The semester is organized into six development sprints. Each sprint lasts
approximately two to three weeks and corresponds to recovering one fragment of
the Heart Crystal. The approved 30-mission course uses these sprints as
curriculum groupings; missions provide the smaller learning steps within them.

The platform capabilities needed for all 30 missions are implemented and tested
before the course begins. Sprints control when students encounter capabilities,
not when maintainers finish building them.

### Sprint Philosophy

Each sprint:

1. Introduces new programming concepts.
2. Asks students to build features that use those concepts.
3. Results in a visible, shareable expansion of the shared world.
4. Includes code review, debugging, and reflection.
5. Ends with a classroom showcase — students explore the world they built
   together.

### The Six Sprints

| Sprint | Heart Crystal Fragment | World Expands With |
|--------|----------------------|-------------------|
| **1** | Fragment of Presence | First characters appear. Students learn to place their character in the world and give it a single line of dialogue. The world has a Village Square and the first characters inhabit it. |
| **2** | Fragment of Motion | Characters learn to move. Students add wandering behaviors, simple animations, and basic object interactions. The Village gains objects: benches, trees, a fountain. |
| **3** | Fragment of Connection | Characters begin to interact with each other. Students implement dialogue trees, friendship mechanics, and the first multi-step interactions. The Forest and River areas open. |
| **4** | Fragment of Memory | The world remembers. Students implement state — objects that change, characters that recall past interactions, environments that evolve. The Playground and Garden appear. |
| **5** | Fragment of Wonder | Complex, conditional behaviors. Students build puzzles, quest chains, and surprising interactions. The Mountain and Library open. |
| **6** | Fragment of Wholeness | The Heart Crystal is restored. Students polish, document, and reflect. The world becomes a complete, living environment — a portfolio piece for every student. |

The sprint structure is flexible. A teacher may adjust pacing, swap a location,
or add a class-specific theme. The progression from simple to complex is the
constant.

---

## 10. Student Ownership

Explorer World is **student-owned** from the first day.

### What Ownership Means

- Every student has a character that is uniquely theirs.
- Every object, interaction, and area is credited to its creator.
- The world's Git history is a record of every student's contributions.
- At semester end, each student can point to specific, named features they built.
- The class decides collectively: which locations to add, which features to
  prioritize, what the world's personality becomes.

### Not Isolated Homework

Independent repositories do not mean isolated or throwaway homework. Every
Explorer publishes a versioned package. After validation and teacher approval, a
specific package version is selected for a class-world release that classmates
experience. A commit alone does not publish or release a contribution.

This changes the psychology of programming assignments. Students are not
satisfying a rubric. They are contributing to something their peers will see,
interact with, and build upon.

### The Git Record

Each student's repository history tells a story: a first commit adding their
character, a mid-semester commit implementing dialogue, and a final commit
polishing an interaction. Published package versions connect selected source
states to class releases. The student's history remains a portfolio and a source
of pride without mixing every student's commits into one repository.

---

## 11. Teacher Role

The teacher in Explorer Studio is not a lecturer delivering programming facts.
The teacher is three things:

### Mentor

Students hit walls. They encounter bugs they cannot explain. They feel stuck. The
teacher's role is not to provide answers but to teach the process of finding
them: reading error messages, searching documentation, asking precise questions,
isolating problems, testing hypotheses. The goal is to make students
self-sufficient debuggers.

### Technical Lead

The teacher sets technical direction: which packages are approved for a release,
what quality standards the class maintains, how validation or namespace
conflicts are resolved, and when a contribution is "done." The teacher models
the practices of a professional engineering lead — code review, architecture
decisions, prioritization — in a way students can observe and learn from.

### Creative Director

The teacher shapes the world's creative vision without dictating it. They ask
questions: "What should the Forest feel like?" "What kind of character would
live in the Library?" They guide without controlling, ensuring the world feels
coherent while remaining student-owned.

### Not a Lecturer

The teacher does not stand at the front of the room explaining syntax for forty
minutes. Programming concepts are introduced in context — when the world needs
them — and students learn by building, not by listening.

---

## 12. AI Philosophy

Explorer Studio embraces AI as a teaching tool — and teaches students to use it
responsibly.

### AI as Collaborator

GitHub Copilot and similar AI assistants are available to students throughout
the semester. They are treated as junior collaborators: helpful, fast, often
correct, sometimes wrong, and never authoritative.

### The Student's Responsibility

Every line of AI-generated code must be:

1. **Understood.** The student can explain what it does and why.
2. **Reviewed.** The student has read it critically and verified it does what
   was intended.
3. **Tested.** The student has confirmed it works in the actual world.
4. **Improved.** The student has refined variable names, simplified logic, and
   ensured it matches the world's style and standards.

### Avoiding Over-Reliance

The curriculum is designed so that AI cannot do the work for the student.
Creative decisions — what should my character say here? — cannot be delegated to
an AI. Debugging a world where thirty students' code interacts requires human
judgment. The AI is a tool; the student is the creator.

### Age-Appropriate Guidance

Younger students receive more structured AI guidance: prompts provided by the
teacher, explicit review checklists, pair-programming with AI. Older students are
expected to develop their own prompting and review practices. The goal is to
graduate students who can collaborate effectively with AI in any professional
context.

---

## 13. Non-Goals (Version 1)

The following are explicitly out of scope for Explorer World Version 1:

- **Multiplayer.** The world is shared through Git, not through simultaneous
  real-time interaction. Students explore locally or through an approved online
  class environment, and contributions are assembled from packages.
- **Unmoderated social services.** Unrestricted public chat and public
  publishing are not part of the core Explorer Package model.
- **Databases.** World state is stored in code and simple files. No SQL, no
  persistent server-side storage.
- **Advanced physics.** Simple movement and collision only. No gravity
  simulation, no rigid body dynamics.
- **Complex AI.** No NPC pathfinding algorithms, no behavior trees, no machine
  learning. Character behaviors are simple, deterministic, and
  student-programmed.
- **Large RPG systems.** No inventory management, no combat, no leveling, no
  quest logs, no experience points.
- **Professional game engine features.** No particle effects, no shaders, no
  skeletal animation, no audio mixing, no localization framework.
- **Mobile client.** Mobile delivery is deferred. Local desktop execution and an
  authenticated online mode are the approved execution models; the exact online
  client and hosting platform remain open.
- **Accessibility beyond basic keyboard input.** Future versions should address
  accessibility comprehensively; Version 1 focuses on core functionality.

These non-goals keep Explorer World achievable within a single semester and
prevent the project from becoming a game development exercise rather than a
programming curriculum.

---

## 14. Future Vision

Explorer World is designed to evolve.

### Builder Studio

After the structured semester ends, Explorer World can become **Builder
Studio** — a more open-ended creative environment where students who have
completed the core curriculum continue building without the constraints of the
six-sprint structure.

Builder Studio would:

- Remove the fixed sprint progression, letting students build freely.
- Allow persistent worlds that carry forward across semesters.
- Enable student-designed locations, themes, and narrative arcs.
- Support community sharing of worlds, characters, and interaction patterns.
- Provide a platform for advanced students to mentor beginners.

### Design Decisions That Enable Evolution

Explorer World's simple foundation — tile-based world, student-owned characters,
Git-based collaboration, Python scripting — is chosen specifically because it can
grow. A more complex initial design would constrain future possibilities. A
simpler design can become anything.

The same character a student builds in their first week can still exist in
Builder Studio two years later, enhanced with everything they have learned since.
The world is designed for continuity, not disposability.

### What Does Not Change

Even as Explorer World evolves, the core principles remain:

- Students own their creations.
- Contributions are reviewed, published, and assembled — not submitted and
  forgotten.
- AI is a tool, not an author.
- Programming is learned by building things that matter to other people.

---

## Open Questions

*For discussion before Phase 1 engine work begins:*

1. **Tile size and world dimensions.** How large should the initial world be?
   How many tiles per screen? This affects visual design and asset creation.

2. **Art style.** Pixel art? Vector-style? Abstract shapes? The style affects
   asset complexity and student accessibility.

3. **Student onboarding.** What does a student's first five minutes look like?
   How quickly do they see their character in the world?

4. **Assessment model.** How should teachers evaluate student contributions?
   What does a rubric for a validated, publishable Explorer Package look like?

5. **Cross-class sharing.** Should classes be able to visit each other's worlds?
   Should there be a gallery of example worlds from past semesters?

6. **Accessibility baseline.** What is the minimum accessibility standard for
   Version 1, and what is deferred to future versions?

7. **Localization.** Should the world support multiple human languages from the
   start, or is English-only acceptable for Version 1?

---

## Design Rationale

### Why a shared world instead of individual projects?

Individual projects create isolation. A shared world creates interdependence.
Students learn collaboration not as a soft skill but as a technical requirement:
their code must work with other people's code. This mirrors professional software
development more accurately than any solo project can.

### Why the Heart Crystal story?

A minimal narrative provides emotional stakes without becoming a creative burden.
The story serves the curriculum — each sprint has a thematic anchor — without
requiring students to be writers. It also explains why the world starts sparse
and grows richer: the world is literally being restored.

### Why student-owned characters?

Ownership drives engagement. A student who has invested in a character they
designed, named, and programmed over weeks cares about code quality and world
coherence in a way that a student completing exercises does not.

### Why six sprints?

Six roughly maps to a standard academic semester (12–16 weeks, with 2–3 weeks
per sprint). It provides enough checkpoints for visible progress without
fragmenting the work into too many small deliverables. It also maps cleanly to
the six Heart Crystal fragments.

### Why Git?

Git is the industry standard for collaborative software development. Learning it
in an educational context — where stakes are low and support is high — prepares
students for internships, open-source contribution, and professional work. Each
student's repository provides a clear history and natural framework for review
and feedback. Publishing an Explorer Package then teaches the separate
professional concepts of packaging, approval, and release.

---

*This specification will guide engine architecture, curriculum design, lesson
planning, and asset creation. It should remain stable through Version 1 and
serve as the primary reference for all product decisions.*
