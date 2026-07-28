# Student API v0.1 — Design Specification

> *The first student-facing interface for Explore Studio. Defines what students
> write, think about, and learn — not what the engine implements.*
>
> **Status:** Approved for implementation (reviewed 2026-07-28).
> **Implementation:** Split across two milestones — M4B (Student Model
> Foundation) and M4C (World Adapter and Execution).

---

## 1. Purpose

This specification defines Student API v0.1 — the smallest API that allows a
beginner to reproduce the behaviour already proven inside the engine:

```
approach object  →  see "Press E to explore"
press E          →  see "You found a treasure!" (briefly)
```

The API must be:

- small enough that a student can hold it in their head;
- expressive enough to build a complete, runnable experience;
- educational — every capability teaches a programming concept;
- separated from engine internals — no Pygame, no lifecycle, no renderer.

---

## 2. Design Principles

### 2.1 Just enough to be magical

A student who writes 10–15 lines of Python and presses Run should see a window
open with their character inside. That moment — code becomes a world — is the
hook. Everything else follows from it.

### 2.2 Every concept earns its place

The API must not introduce capabilities "in case they're useful later." Every
concept exposed in v0.1 must be directly exercised by the proven engine
behaviour. Movement, proximity, interaction, feedback — these are the verbs.
Inventory, quests, events — those come later.

### 2.3 Hide the machine, show the world

Students should never type `pygame`, `renderer`, `dt`, `platform`, `clear_frame`,
or `event_loop`. Those exist behind the boundary. The student sees characters,
objects, messages, and actions.

### 2.4 Readable by a teacher

A teacher scanning a student's file should understand the student's intent
without running the code, without looking up engine documentation, and without
decoding framework machinery.

### 2.5 Deliberate constraints

The API should constrain students toward correct usage. If a colour must be
one of nine named values, the API should reject `"goldenrod"` with a clear
message. Errors should teach, not confuse.

### 2.6 Adapter, not a second engine

The `explore` package translates student intent into engine configuration. It
does not independently implement movement, proximity, interaction timing, event
polling, rendering, or lifecycle cleanup. It configures and launches the proven
engine behaviour.

```
Student program
      ↓
explore.World / Character / Object   ← validation and translation
      ↓
engine App / Scene / entities        ← proven behaviour
      ↓
Pygame                               ← platform boundary
```

---

## 3. What Students See

### 3.1 Import

```python
from explore import World, Character, Object
```

Three symbols. One import line. No nested packages, no engine references.

> **Note on `Object`:** `Object` is visually close to Python's built-in
> `object`. For a beginner-facing API, clarity matters more than avoiding
> every built-in-adjacent name. `Object` is retained for v0.1. If classroom
> testing shows confusion, alternatives such as `Thing` or `Prop` can be
> evaluated for v0.2.

### 3.2 World

```python
world = World("Treasure Island")
```

- **`World(name)`** — creates a named world. The name appears in the window
  title bar.
- `name` must be a non-empty string.
- The window is 960 × 640 pixels with a dark background.
- A world may contain **exactly one** `Character` and **exactly one** `Object`
  in v0.1.
- Calling `world.run()` starts the engine and blocks until the window is
  closed.
- `world.run()` raises a clear error if the required character or object is
  missing (§ 3.9).
- Calling `world.run()` a second time raises a clear error (§ 3.9).

### 3.3 Character

```python
explorer = Character(
    name="Explorer",
    x=430,
    y=270,
    color="gold",
)
```

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `name` | `str` | *(required)* | Non-empty, non-whitespace. |
| `x` | `int` | `430` | Left edge, ≥ 0. Booleans and floats rejected. |
| `y` | `int` | `270` | Top edge, ≥ 0. Booleans and floats rejected. |
| `color` | `str` | `"gold"` | One of the **named colours** (§ 3.6). |

The engine provides fixed defaults for size (100 × 100) and draws the
character as a filled rectangle. Students do not set `width`, `height`, or
RGB tuples.

The character moves with the arrow keys and WASD at a fixed speed (160 px/s).
Students do not configure speed.

Unknown keyword arguments raise a `TypeError` naming the unexpected argument.

### 3.4 Object

```python
chest = Object(
    name="Treasure Chest",
    x=60,
    y=480,
    color="brown",
)
```

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `name` | `str` | *(required)* | Non-empty, non-whitespace. |
| `x` | `int` | *(required)* | Left edge, ≥ 0. Booleans and floats rejected. |
| `y` | `int` | *(required)* | Top edge, ≥ 0. Booleans and floats rejected. |
| `color` | `str` | `"brown"` | One of the **named colours** (§ 3.6). |

Objects are stationary and drawn as filled rectangles (80 × 60). Students do
not set `width` or `height`.

Unknown keyword arguments raise a `TypeError` naming the unexpected argument.

### 3.5 World registration and cardinality

```python
world.add(explorer)
world.add(chest)
```

- `world.add(entity)` registers a character or object with the world.
- **Exactly one `Character`** and **exactly one `Object`** are permitted.
- Adding a second character raises:

  ```
  This world already has a character.
  Student API v0.1 supports one character at a time.
  ```

- Adding a second object raises an equivalent message.
- Entities are not silently replaced.
- Entities store student-facing configuration. `world.run()` translates the
  complete configuration into engine-owned objects at launch time.

**Configuration may occur before or after `world.add()`.** Both of these are
valid and produce identical results:

```python
# Option A: configure first
chest.when_near("Press E to explore")
world.add(chest)

# Option B: register first
world.add(chest)
chest.when_near("Press E to explore")
```

### 3.6 Named colours

Students use colour names, not RGB tuples. The v0.1 palette:

| Name | RGB |
|------|-----|
| `"red"` | `(220, 50, 50)` |
| `"orange"` | `(240, 140, 50)` |
| `"yellow"` | `(240, 210, 50)` |
| `"green"` | `(50, 180, 50)` |
| `"blue"` | `(50, 80, 220)` |
| `"purple"` | `(140, 50, 180)` |
| `"pink"` | `(240, 140, 180)` |
| `"brown"` | `(139, 90, 43)` |
| `"gold"` | `(255, 200, 50)` |

The internal colour registry is easy to extend without changing the public
API. If future milestones add text or background colour controls, `"white"`
and `"black"` can be added to the registry at that time.

Invalid colour names raise:

```
"goldenrod" is not a valid colour.
Choose from: red, orange, yellow, green, blue, purple, pink, brown, gold.
```

**Rationale:** RGB tuples are confusing for beginners. Named colours are
immediately meaningful, teach vocabulary, and constrain the palette so
teachers can predict what students will see.

### 3.7 Interaction messages (optional)

```python
chest.when_near("Press E to explore")
chest.when_interacted("You found a treasure!")
```

Two optional methods on `Object`:

| Method | Meaning |
|--------|---------|
| `chest.when_near(message)` | Show *message* while the character is within 120 px (center-to-center) of this object. |
| `chest.when_interacted(message)` | Show *message* for 2 seconds after the player presses E while near this object. |

- `message` must be a non-empty string.
- Calling either method replaces any previous message for that trigger.
- Messages use white text, 28 pt, near the bottom-center of the window.

**Each message is individually optional:**

| Configuration | Behaviour |
|---------------|-----------|
| No `when_near()` and no `when_interacted()` | No text ever appears. Interaction is harmless. |
| Only `when_near()` set | Prompt appears when near. Pressing E produces no visible message (but still causes no error). |
| Only `when_interacted()` set | No proximity prompt. Success message appears briefly after E near the object. |
| Both set | Full behaviour: prompt when near → success message on E. |

An object may define either, both, or neither message. No message is ever
forced merely because an object exists.

### 3.8 Running the world

```python
world.run()
```

- Opens the window.
- Enters the main loop (movement, interaction, rendering).
- Returns when the user closes the window.
- All engine cleanup happens automatically.

Students never write a game loop. They never call `tick()`, `clear()`, or
`present()`. `world.run()` is the only lifecycle method.

### 3.9 Run-time validation

`world.run()` performs final validation before launching the engine:

| Condition | Error |
|-----------|-------|
| No `Character` added | `Add one Character and one Object before running the world.` |
| No `Object` added | `Add one Character and one Object before running the world.` |
| Both missing | `Add one Character and one Object before running the world.` |
| `run()` called twice | `This world is already running. Create a new World to start again.` |
| `world.add()` called after `run()` | `Cannot add entities after the world has started. Call world.add() before world.run().` |

---

## 4. Complete Student Program (v0.1)

```python
from explore import World, Character, Object

# Create the world
world = World("Treasure Island")

# Create the Explorer (movable character)
explorer = Character(
    name="Explorer",
    x=430,
    y=270,
    color="gold",
)

# Create the Treasure Chest (stationary object)
chest = Object(
    name="Treasure Chest",
    x=60,
    y=480,
    color="brown",
)

# Place them in the world
world.add(explorer)
world.add(chest)

# Define what happens near and on interaction
chest.when_near("Press E to explore")
chest.when_interacted("You found a treasure!")

# Start the world
world.run()
```

This program:
- opens a 960 × 640 window titled "Treasure Island";
- displays a gold Explorer rectangle near the center;
- displays a brown Treasure Chest rectangle;
- shows "Press E to explore" when the Explorer approaches;
- shows "You found a treasure!" briefly when E is pressed near the chest;
- lets the Explorer move with arrow keys / WASD;
- closes cleanly when the window is closed.

---

## 5. What Students Do NOT See

The following engine concepts are **excluded** from v0.1:

| Hidden concept | Why |
|----------------|-----|
| `pygame` / `import pygame` | Implementation detail. Students never touch it. |
| `Renderer`, `Platform`, `App` | Engine lifecycle. Handled by `world.run()`. |
| `dt` (delta time) | Frame timing. Movement speed is fixed. |
| RGB colour tuples | Replaced by named colours. |
| `width` / `height` on entities | Fixed defaults. Students focus on position and identity. |
| `DirectionalInput`, `InteractionInput` | Engine input models. Hidden behind movement and E key. |
| `is_character_near_object` | Engine proximity. Students express intent: "when near." |
| `did_interact_this_frame` | Engine pulse. Students express intent: "when interacted." |
| `feedback_remaining` | Engine timer. The 2-second duration is automatic. |
| `interaction_range` | Engine constant (120 px). Not configurable in v0.1. |
| Movement speed | Engine constant (160 px/s). Not configurable in v0.1. |
| Event loop / `while running:` | Engine-owned. `world.run()` is the only entry point. |
| `Scene`, lifecycle states | Engine-owned. Single-scene world only in v0.1. |

---

## 6. Error Handling

### 6.1 Two categories of error

The implementation must distinguish two kinds of failure:

**Student errors** — predictable mistakes a beginner might make:

- invalid colour name;
- negative or Boolean coordinate;
- duplicate entity;
- missing entity at `run()`;
- calling `run()` twice;
- adding entities after `run()`;
- unknown keyword argument.

These produce concise, friendly messages. The student sees only the message —
no traceback, no engine internals.

**Unexpected internal failures** — defects in the engine itself:

- Pygame initialization failure;
- rendering error;
- event-polling failure.

These must preserve diagnostic information for developers. The original
exception remains chained or logged. During classroom use the visible message
may be friendly, but the implementation must never silently swallow these
errors:

```python
# WRONG — hides all failures, makes debugging impossible
except Exception:
    print("Something went wrong")

# RIGHT — friendly message for students, original exception preserved
except SomeEngineError as exc:
    raise StudentAPIError("The window could not open.") from exc
```

The chained exception ensures developers can inspect the root cause while
students see an age-appropriate message.

### 6.2 Style guide

- Use plain English, not stack traces.
- Name the value the student provided.
- Suggest the valid range or options.
- Use conversational sentence structure.
- Never expose engine internals (file paths, Pygame errors, tracebacks).

### 6.3 Validation rules

Student-facing constructors must reject:

| Input | Example | Error style |
|-------|---------|-------------|
| Boolean coordinate | `x=True` | `Character x must be a whole number of 0 or greater. You gave: True` |
| Float coordinate | `x=1.5` | `Character x must be a whole number of 0 or greater. You gave: 1.5` |
| Negative position | `x=-20` | `Character x must be a whole number of 0 or greater. You gave: -20` |
| Empty / blank name | `name=""` | `name must not be empty` |
| Unknown colour | `color="goldenrod"` | `"goldenrod" is not a valid colour. Choose from: red, orange, …` |
| Unknown keyword | `speed=10` | `Character() got an unexpected keyword argument 'speed'` |
| Duplicate character | second `world.add(char)` | `This world already has a character. Student API v0.1 supports one character at a time.` |
| Duplicate object | second `world.add(obj)` | `This world already has an object. Student API v0.1 supports one object at a time.` |
| Missing entity at `run()` | no character added | `Add one Character and one Object before running the world.` |
| `run()` called twice | `world.run(); world.run()` | `This world is already running. Create a new World to start again.` |
| `add()` after `run()` | `world.run(); world.add(...)` | `Cannot add entities after the world has started. Call world.add() before world.run().` |

### 6.4 Validation order

When multiple validations could fail on a single constructor call, report the
first one encountered in parameter order. This keeps error messages predictable.

### 6.5 Mutation after `world.run()`

Once `world.run()` has been called, student-facing entities become immutable.
Calling `world.add()`, `chest.when_near()`, or any configuration method raises
a clear error. The entity configuration is frozen at launch time.

---

## 7. Boundary: Declarative Setup vs Python Functions

### 7.1 Declarative setup (v0.1)

The v0.1 API is purely **declarative**. Students describe what they want:

```python
chest.when_near("Press E to explore")
```

They do not write functions, conditionals, or loops. Every student program is
a flat sequence of:

1. Create the world.
2. Create one character.
3. Create one object.
4. Optionally set interaction messages.
5. Add entities to the world.
6. Run.

This matches the **Stage 1 — Observe and Modify** learning level from the
curriculum design.

### 7.2 Function boundary (v0.2+)

When the API introduces custom behaviour, it will cross into function-based
definitions:

```python
@chest.when_interacted
def on_open():
    world.say("You found a treasure!")
    world.say("The chest is now empty.")
```

This requires students to understand function definitions, decorators, and
possibly control flow. That boundary is intentionally deferred to v0.2 or
later.

### 7.3 Why not decorators in v0.1?

| Concern | Reasoning |
|---------|-----------|
| **Decorator syntax (`@`)** | Not typically taught in week 1–2 of a Python course. |
| **Function definition** | Requires understanding `def`, indentation, scope. |
| **Callback semantics** | "When does this function run?" — confusing without an event model. |
| **Multiple interactions** | What happens with two `@when_interacted` decorators? Requires ordering rules. |

Object-owned string messages avoid all of these. The student writes:
`chest.when_interacted("message")` — one method call, one string argument. That
is the full conceptual load.

---

## 8. Lesson Examples

### 8.1 Starter — "Hello World"

The minimal program every student writes on day one:

```python
from explore import World, Character

world = World("My First World")
me = Character(name="Me")
world.add(me)
world.run()
```

Concepts: import, variable assignment, function/method calls.

### 8.2 Guided — "The Treasure Chest"

The complete v0.1 example (reproduced in § 4). Students type this with teacher
guidance and then modify it.

### 8.3 Challenge — "Make It Yours"

Students modify the guided example:

- Change the world name.
- Move the chest to a different position.
- Change the Explorer's colour.
- Change the interaction message.
- Make the chest a different colour.

Concepts: values, assignment, observation of cause and effect.

### 8.4 Extension — "Two Messages"

Advanced students can be challenged to think about what else could happen:

- "What if the chest said something different when you're near?"
- "What if the success message was longer?"
- "Could you add a second object?" (Answer: not yet — but the question plants
  the seed for v0.2.)

---

## 9. Resolved Design Questions

All open questions from the initial draft have been resolved through review:

| # | Question | Resolution |
|---|----------|------------|
| 1 | Constructor vs `world.add()`? | `world.add()` — explicit, extensible, and matched to the learning progression. |
| 2 | Interaction on Object or World? | Object-owned — `chest.when_near(...)`. Re-evaluate decorators and World-owned callbacks in v0.2. |
| 3 | Reject or default unknown colours? | Reject with a helpful message listing valid colours. |
| 4 | Single file or multiple files? | One file for v0.1. |
| 5 | `explore` package location? | Top-level `explore/` — separate from `engine/`. |
| 6 | Window size configurable? | Fixed 960 × 640 for v0.1. |
| 7 | Proximity range configurable? | Fixed 120 px for v0.1. |
| 8 | `Object` name conflict with `object`? | Retain `Object`. Revisit only if classroom testing shows confusion. |
| 9 | Configuration before or after `world.add()`? | Both permitted — entities store configuration, `world.run()` translates at launch. |
| 10 | Messages optional or required? | Individually optional. Either, both, or neither may be set. |
| 11 | Decorators in v0.1? | Deferred. String-owned messages are adequate for single-object v0.1. |

## 10. Implementation Sequence

The API is implemented across two milestones to keep failures easy to diagnose
and to prevent API design from becoming tangled with engine orchestration.

### M4B — Student Model Foundation

Implement the data model — no engine launch:

- `explore` package scaffolding (`__init__.py`, `_colors.py`);
- `explore.Character` — validation, named-colour translation, immutable config;
- `explore.Object` — validation, named-colour translation, immutable config,
  `when_near()` and `when_interacted()` message storage;
- unit tests for construction, validation, and colour mapping;
- all 299 existing engine tests continue to pass.

**Deliverable:** a tested student-facing entity model that validates cleanly
but does not yet open a window.

### M4C — World Adapter and Execution

Implement the world container and engine launch:

- `explore.World` — entity registration, cardinality enforcement, run-time
  validation;
- configuration translation: student entities → engine `Character` /
  `WorldObject` / `DefaultScene` / `App` / interaction messages;
- `world.run()` — constructs and launches the engine, blocks until close;
- student-error boundary: friendly messages for predictable mistakes,
  preserved diagnostics for internal failures;
- end-to-end integration tests using the SDL dummy driver;
- the complete student program (§ 4) runs and produces the expected behaviour;
- documentation updated with the final API reference.

**Deliverable:** a student can write the program in § 4, run it with
`python main.py`, and experience the full interaction loop.

## 11. Implementation Notes

These notes are for the engine team, not for students.

### 11.1 Package structure

```
explore/
    __init__.py       # exports World, Character, Object
    _world.py         # World class (wraps App + DefaultScene)
    _character.py     # Character wrapper (student-facing config)
    _object.py        # Object wrapper (student-facing config + messages)
    _colors.py        # Named colour → RGB mapping
```

The `explore` package imports from `engine` internally. Students never import
from `engine` directly.

### 11.2 Adapter pattern

The `explore` package is an adapter, not a second engine:

```
Student program
      ↓
explore.World / Character / Object   ← validation, translation
      ↓
engine Config / App / DefaultScene   ← proven behaviour
      ↓
Pygame                               ← platform boundary
```

The `explore` package must not independently implement movement, proximity,
interaction timing, event polling, rendering, or lifecycle cleanup. It
configures and launches the proven engine behaviour.

### 11.3 World implementation sketch

```python
class World:
    def __init__(self, name: str):
        self._name = name
        self._character: StudentCharacter | None = None
        self._object: StudentObject | None = None
        self._has_run = False

    def add(self, entity):
        if self._has_run:
            raise RuntimeError(
                "Cannot add entities after the world has started. "
                "Call world.add() before world.run()."
            )
        if isinstance(entity, StudentCharacter):
            if self._character is not None:
                raise ValueError(
                    "This world already has a character. "
                    "Student API v0.1 supports one character at a time."
                )
            self._character = entity
        elif isinstance(entity, StudentObject):
            if self._object is not None:
                raise ValueError(
                    "This world already has an object. "
                    "Student API v0.1 supports one object at a time."
                )
            self._object = entity

    def run(self):
        if self._has_run:
            raise RuntimeError(
                "This world is already running. "
                "Create a new World to start again."
            )
        if self._character is None or self._object is None:
            raise RuntimeError(
                "Add one Character and one Object before running the world."
            )
        self._has_run = True
        # Translate student config → engine objects
        # Build engine Config, App, DefaultScene
        # Launch App.start()
        ...
```

### 11.4 Colour mapping

The `_colors.py` module maps named colours to RGB tuples. It is an
engine-internal helper used by the student wrappers. The registry is a
simple dictionary, easy to extend without changing the public API.

### 11.5 Validation sharing

The student-facing `Character` and `Object` should validate at construction
time using shared helpers from the engine where appropriate (name validation,
colour validation) before storing configuration. Student-facing error messages
are the responsibility of the `explore` package — engine validation errors
should never reach the student directly.

### 11.6 Test strategy

Student API tests should verify:
- Valid programs produce the expected engine configuration.
- Invalid inputs produce clear, student-friendly error messages.
- The full end-to-end program (§ 4) runs and exits cleanly.
- Named colours map correctly.
- Interaction messages are forwarded to the right engine hooks.
- Cardinality rules are enforced (one character, one object).
- Optional messages behave correctly (any combination works).
- `run()` twice raises; `add()` after `run()` raises.
- Internal failures preserve chained exceptions.

Tests should use the SDL dummy driver (same as engine tests).

---

## 12. Out of Scope (v0.1)

The following are explicitly deferred to v0.2 or later:

- Multiple characters or objects;
- Custom width / height on entities;
- Custom movement speed or proximity range;
- Decorator-based interaction callbacks;
- `world.say()` / `world.ask()` dialogue API;
- Inventory, items, rewards;
- Object state mutation (opened chest, collected item);
- Save / load;
- Custom font size, colour, or position for feedback text;
- Multiple interaction messages per object;
- Timer / cooldown configuration;
- Event system;
- Student-authored Python functions in interaction handlers;
- Teacher dashboard integration;
- Lesson runner;
- Configurable window size;
- `"white"` / `"black"` colours (add to registry when needed for text/background).

---

## 13. Success Criteria

### M4B — Student Model Foundation

- [ ] `explore.Character` constructs with valid inputs and rejects invalid ones.
- [ ] `explore.Object` constructs with valid inputs and rejects invalid ones.
- [ ] All nine named colours map to correct RGB tuples.
- [ ] `when_near()` and `when_interacted()` store messages correctly.
- [ ] Boolean, float, and negative coordinates are rejected with friendly messages.
- [ ] Unknown keyword arguments are rejected.
- [ ] All 299 existing engine tests continue to pass.
- [ ] Black and Ruff pass.

### M4C — World Adapter and Execution

- [ ] A student can write the program in § 4 and run it with `python main.py`.
- [ ] The window opens with the correct title.
- [ ] The Explorer appears at the correct position and colour.
- [ ] The Treasure Chest appears at the correct position and colour.
- [ ] Arrow keys and WASD move the Explorer.
- [ ] "Press E to explore" appears when the Explorer is near the chest.
- [ ] "You found a treasure!" appears briefly when E is pressed near the chest.
- [ ] The prompt disappears when the Explorer moves away.
- [ ] Cardinality rules: duplicate entities raise clear errors.
- [ ] Missing entity at `run()` raises a clear error.
- [ ] `run()` called twice raises a clear error.
- [ ] Configuration works before or after `world.add()`.
- [ ] Optional messages: any combination of set/unset works correctly.
- [ ] All student errors produce friendly messages (no tracebacks, no engine internals).
- [ ] Internal failures preserve chained exceptions for developers.
- [ ] All engine tests continue to pass.
- [ ] Black, Ruff, and pytest pass on the full repository.
- [ ] A teacher can read a student's file and understand it without documentation.

---

*Specification approved. Implementation proceeds via M4B → M4C.*
