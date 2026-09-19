# S26 — Capstone Blueprint

**Role:** Project-primary planning lesson

**Reference teacher exemplar:** Stormlight Rescue Trail
(`student/examples/right-sized-blueprint.yaml`)

**World reuse:** None today. S26 selects from the existing M03–M15 mechanics; it
builds none of them.

**Learning objective:** Students design a capstone they can finish — an original
premise, two to four supported mechanics with at least one real connection
between them, a three-to-six-step player flow, one bounded S27 first slice, and
a risk with a fallback they chose in advance.

**Student-owned decisions:** the premise, the player goal, which mechanics,
which two are connected, the key elements, the flow, the S27 target, the risk,
and the fallback.

**Prerequisite:** The student's finished S25 playable prototype, and the M03–M15
mechanics they have built across S03–S25.

**Arc note:** S26 is the hinge of the course. It introduces **design planning**
and no new programming syntax. Nothing is built today.

## Capstone purpose, and the S25/S27 bridge

Say this out loud at 0:00 and again at 0:45:

> S25 proved: **I can build a small working system.**
> S26 proves: **I can design a larger project before building it.**
> S27 proves: **I can build the first working slice of my design.**

> Playable Prototype → **Capstone Blueprint** → Core Build → Integration →
> Review → Premiere

Students reuse their S25 habits today — validate, compose mechanics, prove
behaviour, keep scope bounded, explain decisions — applied to a plan instead of
code. The one new skill is deciding what *not* to build.

## The one deliverable

`student/capstone-blueprint.yaml`. One file, ten minutes of writing spread over
forty, and a gate that reads it:

```console
python -m pytest -q lessons/sessions/s26/student/test_blueprint.py
```

There is no package, no pipeline, and no starter code to finish. If a student is
authoring YAML objects today, they are doing neither S26's work nor S27's — the
package itself is authored in S28 — and their blueprint will be the weakest in
the room. Stop them.

## Before class

- Confirm the shared Quick Start, Python environment, and `pytest`. **Trail is
  not needed today** — no session content depends on launching it.
- Read both shipped examples so you can quote them:
  `student/examples/right-sized-blueprint.yaml` (finished, three mechanics,
  three key elements, five flow steps) and
  `student/examples/too-big-blueprint.yaml` (The Sunken Archive — six mechanics,
  six key elements, nine steps, and two things the runtime cannot do).
- Run the mechanic menu once on the projector so the supported set is the first
  thing the room sees:

  ```console
  python lessons/sessions/s26/student/mechanic_menu.py
  ```

- Treat the student's premise as canonical from the moment they write it.
  Stormlight Rescue Trail is yours, not theirs.

## 45-minute runbook

| Clock anchor | Range | Teacher move | Student evidence |
|---:|---:|---|---|
| 0:00–0:05 | 5 min | Capstone framing: design first, build next. Show the nine-item gate and both examples. | Names the size boundary out loud. |
| 0:05–0:10 | 5 min | Choose premise and player goal. Push every "explore the X" into an observable goal. | `project:` block filled in. |
| 0:10–0:18 | 8 min | Choose two to four mechanics from the menu. Refuse anything not on it. | `mechanics[]` with a role for each. |
| 0:18–0:28 | 10 min | Map how the mechanics connect, then the player flow. | `integration:` plus a three-to-six-step flow. |
| 0:28–0:35 | 7 min | Choose the two to four key objects and characters. | `world.key_elements`. |
| 0:35–0:40 | 5 min | Define the S27 first slice, the validation plan, and the play-test plan. | One bounded, independently testable target. |
| 0:40–0:44 | 4 min | Name the risk and the fallback; run the scope-reduction ladder on anyone over. | `risk:` block, gate green. |
| 0:44–0:45 | 1 min | Blueprint handoff and exit check. | Reads the S27 target aloud to one other person. |

The 0:18–0:28 block is the one to protect. A student who leaves with four
mechanics and no connection between them has a list, not a design.

## Capstone size boundary

The default target, and the number to repeat:

- two to four key authored objects or characters;
- two to four supported mechanics;
- one coherent player experience;
- one package;
- **no new engine feature.**

S27–S30 is four sessions, and two of them are review and premiere. Prefer reuse
and composition over novelty.

What S26 is **not**: open-ended game design, engine-feature brainstorming,
multi-level architecture, persistence or inventory design, a large RPG or story
system, or a platform redesign. When a student drifts into one of those, the
question is always the same: "which two sessions is that, and what would you cut
to pay for it?"

## Supported mechanics only

`student/mechanic_menu.py` is the single source of truth, and the blueprint
checker imports it, so the menu and the gate cannot disagree. Every entry
already exists in the current contracts:

| Mechanic | From | Lives on |
|---|---|---|
| `response` | M03 | world object |
| `dialogue` | M04/M05 | character |
| `toggle` | M07 | world object |
| `toggle_style` | M14 | world object |
| `counter` | M09 | world object |
| `respond_to_toggle` | M08/M12 | character |
| `respond_to_two_toggles` | M10 | character |
| `respond_to_either_toggle` | M11 | character |
| `respond_to_counter` | M13 | character |
| `respond_to_sequence` | M15 | character |

Same bounds as S25: counters increment only and goals are whole numbers from 2
through 5; a toggle is a two-colour flag, not a state machine; a sequence is
exactly three objects; two-toggle and either-toggle responses are exactly two
toggles; one character carries at most one response mechanic, so a second
response mechanic needs a second character.

There is no persistence across sessions, no inventory, no collision or physical
locking, no health, currency, or general score, no arbitrary variable store, no
timers or self-starting behaviour, no networking or multiplayer, no
cross-package semantic reference, and no new mission or completion-rule
architecture. If a premise needs one of those, the fix is the wording of the
premise, not the engine. **Do not extend the engine for a blueprint.**

## What "connected" means

Two mechanics are connected when one of them can really read the other. The
checker accepts only these pairs, and `mechanic_menu.py` prints the same list:

```text
counter      + respond_to_counter
counter      + respond_to_sequence
response     + respond_to_sequence
toggle       + respond_to_toggle
toggle       + respond_to_two_toggles
toggle       + respond_to_either_toggle
toggle       + respond_to_sequence
toggle_style + respond_to_toggle
toggle_style + respond_to_two_toggles
toggle_style + respond_to_either_toggle
toggle_style + respond_to_sequence
```

Every pair on that list is one producer and one reader, because that is the only
thing the loader checks: a switch-watcher must point at a world object that
carries toggle metadata, and a counter-watcher at one that carries a counter.

`toggle + toggle_style` is **not** on the list, and this is the distinction worth
teaching. A named style is one switch appearance reused by several switches, so
a styled switch is still just a switch — nothing has been made to notice
anything. `toggle_style` reaches the gate the same way a plain `toggle` does, by
having a character who watches it; the loader fills the same toggle field from a
named style, so every switch-watcher reads a styled switch exactly as it reads
an inline one.

`dialogue + counter` is not a connection, and neither is `toggle + counter` with
nothing reading either one. Two characters that each read a different thing are
not connected to each other. The blueprint has to answer four questions: what
does the player do, what changes, what notices the change, and how does the
player know they succeeded.

Do **not** require every mechanic to reference every other one. One real
connection is the bar; a third mechanic may sit beside it and set the scene.

## Too big versus right-sized

Show both files side by side. The contrast is the lesson, not the content.

| | Right-sized | Too big |
|---|---|---|
| Mechanics | 3 | 6 |
| Key elements | 3 | 6 |
| Flow steps | 5 | 9 |
| S27 target | the modular core for one lantern-and-keeper exchange | "build the whole game" |
| Unsupported | none | an inventory, and pages carried between rooms |

Then run the gate on the over-scoped one on the projector, so the room watches
it be refused by name:

```console
BLUEPRINT=lessons/sessions/s26/student/examples/too-big-blueprint.yaml \
  python -m pytest -q lessons/sessions/s26/student/test_blueprint.py
```

Ask the room for three cuts and their order. The answer you are steering toward:
six mechanics → two, six elements → three, nine steps → four, and The Sunken
Archive is still The Sunken Archive.

## Student-owned decisions — and what you must not decide for them

The student owns: the premise; the player goal; which mechanics; which two are
connected; the key elements and their names; the flow; the S27 target; the risk;
the fallback; and the reflection.

You may: narrow scope, ask which part could be cut, point at the menu, refuse an
unsupported feature, and say "that is two projects".

You may **not** invent the core premise or make the major design decisions —
unless a student is genuinely stuck and degraded mode applies below.

## Paced scope reduction

One ladder, used in order, for any blueprint that is too large:

1. reduce the number of key objects and characters;
2. reduce mechanics — four, then three, then two;
3. remove optional story branches;
4. keep one coherent interaction loop;
5. preserve the student's core premise.

Never solve scope by inventing an unsupported engine feature, and never solve it
by taking the premise away. Step 5 is the whole reason the ladder is in this
order.

## Likely failure modes and recovery

- **"I want to make Minecraft."** Ask what the *first five minutes* of that
  feels like, then design only those five minutes. Scale is the cut, not the
  idea.
- **Four mechanics, no connection.** The most common real failure. Ask: which
  one changes something, and which one notices? If nothing notices anything, they
  have four decorations. Drop to two and connect them.
- **Premise needs saved progress or an inventory.** Offer the substitution
  directly: a toggle means "I have this"; a counter means "nearly charged". The
  checker gives the same advice by name.
- **A flow with nine steps.** Ask which step the player would be most sad to
  lose, keep that one, and rebuild around it.
- **"Build the whole game" as the S27 target.** Ask what they could show a
  classmate at the end of one session. That sentence is the target.
- **No premise at all.** See degraded mode.
- **Started authoring YAML.** Close the editor. S27 writes Python, not YAML, and
  the package is authored in S28 — so that work is early twice over, and it is
  being paid for with their design time.

## Degraded mode

Only for a student who would otherwise leave with nothing:

- offer a **choice of three** narrow premises drawn from what that student has
  already enjoyed building, and let them pick and rename. They still own the
  player goal, the flow, and the S27 target;
- if they cannot choose mechanics, hand them one connected pair from the menu
  (`toggle` + `respond_to_toggle` is the cheapest) and have them write the roles;
- if the blueprint is still incomplete at 0:44, complete items 1, 2, 4 and 7 of
  the blueprint completion gate — premise, player goal, the connected pair, and
  the S27 target — with them out loud and write those four lines down.

Degraded mode reduces the student's scope. It does not replace their authorship,
and it is not the default for a quiet student.

## Blueprint completion gate

The blueprint is complete only when all nine hold:

1. the premise is specific;
2. the player goal is observable;
3. two to four supported mechanics are selected;
4. at least two mechanics have a meaningful connection;
5. the player flow is concrete, three to six steps;
6. no unsupported runtime feature is required;
7. the S27 first slice is bounded and independently testable;
8. one major risk is named;
9. one fallback or simplification is named.

The checker enforces all nine structurally. It never scores creativity, requires
a particular premise, enforces exact prose, or requires specific object names.
Where it cannot check reliably it does not guess — judging whether a premise is
genuinely the student's own is **your** review, not the gate's.

## Teacher cut line

Protect, in order:

1. premise and player goal;
2. two connected supported mechanics;
3. a concrete player flow;
4. the S27 first slice;
5. the risk and the fallback.

Cut: extra mechanics, extra key elements, optional story detail, polish.

**Never let a student leave S26 without a usable S27 target.** Everything else
can be repaired next session; that one cannot, because S27 opens with it.

## S26/S27 boundary

S26 is planning only. The single permitted experiment is running
`mechanic_menu.py` to confirm a mechanic does what the student thinks — a probe,
explicitly not capstone implementation, and two minutes at most. Do not let it
consume the session, and do not pre-build S27 deliverables in S26 files. There
are deliberately no starter modules, no fixtures, and no student package in S26
for exactly this reason.

## S27 handoff

S26 hands S27 exactly two things: `capstone-blueprint.yaml`, and the bounded
first slice named in `build_plan.s27_target`. That is the whole handoff. S26
produces no responsibility map, no function contracts, and no project record —
**S27 derives all three from the blueprint in its own opening minutes**, and its
task card and runbook say so. Do not tell students those artefacts already exist.

Because S27 is a modular-core Python session — it builds deterministic in-memory
dictionaries and never writes YAML, which is S28's work — a usable `s27_target`
names the modular core of one interaction, not a file to author. The shape to
steer towards:

> Define the modular core for the lantern-switch and keeper interaction,
> including the responsibilities and the function contracts, then implement one
> tested helper.

At 0:44, have each student read that one line aloud to one other person; if the
listener could not start on it, it is not bounded yet. The mechanics chosen today
are the ones the capstone turns into real contributions once S28 authors the
package, and `mechanic_menu.py` already lists what each of them will require.

Collect nothing. Review the blueprint on screen with the student.

## Bounded AI assistance

AI may ask or answer **one bounded scope question only**, such as "which part of
this could be cut?" or "is this one project or two?". AI may not invent the
premise, choose the mechanics, write the player flow, decide the S27 target, or
fill in any blueprint field. The student records the question, the answer,
whether they accepted it, and why. Enforce the whole-file ban.

## Git close

**ZIP classes:** Skip this step for classes still on the ZIP distribution that have not started the Git lesson yet; use it once the class has a Git-managed course folder. See [Student Quick Start → Later: Git](../student-quick-start.md#later-git-optional-teacher-managed).

One file changes today, so one commit covers it: status → diff → staged diff →
descriptive commit on `student/capstone-blueprint.yaml`. Explain `M`, `??`, no
output, identity recovery, and Control-C cancel/correct/retry. Staging only the
blueprint is the point — there is nothing else to stage.

## Teacher notes

- The checker needs only `pytest` and `pyyaml`. It imports nothing from the
  engine or `explore/`, so a blueprint review works on a machine that cannot run
  Trail at all.
- `BLUEPRINT=<path>` points the checker at any blueprint file. Use it for the
  over-scoped demonstration; students never need it.
- The gate's word-count floors (a premise of ten words, a flow step of four) are
  completeness checks, not quality scores. A student who hits them has written a
  fragment, not a bad idea.
- Do not add S27+ materials, runtime, schema, or API behaviour, Trail or Mission
  mechanics, deployment, authentication, or Phase E work.
