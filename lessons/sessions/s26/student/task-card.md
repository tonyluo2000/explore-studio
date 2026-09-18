# S26 Task Card — Capstone Blueprint

**Role:** Project-primary planning lesson

**Learning target:** Design a capstone you can actually finish — a premise of
your own, two to four supported mechanics that work together, a player flow
somebody could follow, and one bounded first slice for S27.

**Where this sits:** S25 proved *I can independently build and explain a small
working system.* Today proves the next sentence: *I can design a larger project
before I build it.* S27 proves *I can build the first working slice of my
design.*

> Playable Prototype → **Capstone Blueprint** → Core Build → Integration →
> Review → Premiere

**Nothing is built today.** No package, no pipeline, no YAML objects. Today's
deliverable is one file: `capstone-blueprint.yaml`. S27 opens it and starts
building.

Use the shared [`Student Quick Start`](../../student-quick-start.md).

## What "done" means (0:00–0:05)

Nine things. The blueprint checker asks for all nine, and it will tell you
which ones are still missing:

| # | The gate asks | Where it lives |
|---:|---|---|
| 1 | Your premise is specific, and it is **yours** | `project.premise` |
| 2 | The player goal is something you could watch happen | `project.player_goal` |
| 3 | Two to four mechanics, all of them real | `mechanics[].kind` |
| 4 | At least two of them are genuinely **connected** | `integration.connected_mechanics` |
| 5 | A concrete player flow, three to six steps | `world.player_flow` |
| 6 | Nothing needs a feature the runtime does not have | the whole file |
| 7 | One bounded S27 first slice | `build_plan.s27_target` |
| 8 | One named risk | `risk.biggest_risk` |
| 9 | One fallback you decided on in advance | `risk.fallback_if_time_runs_short` |

Run the gate whenever you want to know where you stand:

```console
python -m pytest -q lessons/sessions/s26/student/test_blueprint.py
```

It starts red. Nothing is broken — it is counting the decisions you have not
made yet, and every failure names the exact line.

## The size of a capstone

Your capstone runs from S27 to S30: four sessions, and S29 and S30 are review
and premiere. So the real build time is closer to two.

A capstone that finishes looks like this:

- two to four key objects or characters you author;
- two to four supported mechanics;
- one coherent experience, not three small ones;
- one package;
- **no new engine feature.**

Reuse beats novelty here. Everything impressive about your capstone will come
from how your mechanics fit together, not from how many you used.

Two examples are in `examples/`. Read both:

- `right-sized-blueprint.yaml` — the teacher's Stormlight Rescue Trail, at the
  size a finished blueprint really is. It is somebody else's premise; read it
  for scope, not for content.
- `too-big-blueprint.yaml` — The Sunken Archive. Every idea in it is good and
  none of it could be finished. Your teacher will show the checker refusing it.
  Name three things you would cut, and in what order.

## Choose your premise and player goal (0:05–0:10)

Open `capstone-blueprint.yaml` and fill in the `project:` block. Nothing else
yet.

The premise is yours. Not the teacher's, not the examples', not AI's. Two or
three sentences: what is this place, and why would a visitor come?

Then the player goal — and write it so somebody watching could tell the exact
moment it happened. "Explore the observatory" is a mood. "Align all three
mirrors so the astronomer can read the star chart" is a goal.

## Choose two to four mechanics (0:10–0:18)

You may choose only from mechanics the runtime already has. See the whole menu,
what each one needs, and which pairs really connect:

```console
python lessons/sessions/s26/student/mechanic_menu.py
```

Everything on that menu is something you have built before: responses,
dialogue, toggles, toggle styles, counters, the characters that read a toggle,
two toggles, either toggle, or a counter, and the three-object ordered
sequence.

What is **not** there, and never will be by S30: saved progress, an inventory,
collision or locked doors, health, currency or score, a variable you can set to
anything, timers, a second player, a second level. If your premise seems to
need one of those, change the wording of the premise. A toggle can mean "I have
the key". A counter can mean "the lamp is nearly charged".

For each mechanic, write `role_in_experience`: one sentence on what it does
**for the player**. "A counter" is not a role.

## Connect them (0:18–0:28)

This is the part that makes a capstone a system instead of a pile.

Name two of your mechanics in `integration.connected_mechanics`: one that
**changes** something, and one that **notices** the change. The checker accepts
only pairs the runtime can really connect — a counter and the character who
compares it to its goal, a switch and the character who answers differently
while it is on, an object and the keeper who watches it as part of an ordered
route. `mechanic_menu.py` prints every legal pair.

Then answer four questions in `how_mechanics_connect` and `observable_success`:

1. What does the player **do**?
2. What **changes** because of that?
3. What **notices** the change?
4. How does the player **know** they succeeded?

"They are both in my package" is not a connection, and the checker says so.

Not every mechanic has to touch every other one. One real connection is the
requirement; a third mechanic is allowed to sit beside it and set the scene.

## Map the player flow and the world (0:28–0:35)

Write `world.player_flow`: three to six steps, in order, ending with something
the player can see. Use the mechanics you actually chose — a step the runtime
cannot do is not a step.

A flow usually reads like this:

1. the player reads or approaches something and learns what to do;
2. the player interacts with an object;
3. something changes;
4. the player uses that change to continue;
5. success is visible.

Then `world.key_elements`: the two to four things a visitor meets. Every one of
them is a file you will author later, so this list is a promise about your own
workload.

## Name the S27 first slice (0:35–0:40)

The most important line in the file.

`build_plan.s27_target` names **one** thing you could finish and test in a
single session. Good targets:

- author the first two world objects;
- implement the primary mechanic pair;
- make one interaction loop validate and play;
- produce the first valid package slice.

"Build the whole game" is not a target, and the checker refuses it. The slice
has to be testable on its own — otherwise you will not know in S27 whether you
are on track.

Then say how you will check it (`validation_plan`) and who will play it
(`play_test_plan`).

## Name the risk and the fallback (0:40–0:44)

`risk.biggest_risk` — the one thing most likely to go wrong or run long. Every
real plan has one; naming it is not pessimism.

`risk.fallback_if_time_runs_short` — what you would cut **first**. Decide it
now, while you are calm and it is cheap. Cut in this order:

1. fewer key elements;
2. fewer mechanics — four, then three, then two;
3. drop the optional story branches;
4. keep one interaction loop that works end to end.

Your premise survives all four. That is the point of deciding now.

## Blueprint handoff (0:44–0:45)

```console
python -m pytest -q lessons/sessions/s26/student/test_blueprint.py
```

Green means S27 can start from this file tomorrow. Read your `s27_target` out
loud to one other person; if they could not start on it, it is not bounded yet.

Then fill in `reflection:` — why this project, and which design decision was
hardest.

## Cut line

If time runs short, protect these in order:

1. premise and player goal;
2. two connected supported mechanics;
3. a concrete player flow;
4. the S27 first slice;
5. the risk and the fallback.

Cut extra mechanics first, then extra key elements, then optional story detail,
then polish. Do **not** leave today without an S27 target — that is the one
thing tomorrow cannot start without.

## Optional feasibility probe

If you genuinely cannot tell whether a mechanic does what you think, run
`mechanic_menu.py` and read what that mechanic needs. That is the probe. It is
not capstone implementation, and it takes two minutes — if you find yourself
authoring YAML today, stop: that is S27's work and you are spending your
design time on it.

## AI receipt

AI may ask or answer **one bounded scope question only**, for example "Which
part of this could be cut?" or "Is this one project or two?".

AI may **not** invent your premise, choose your mechanics, write your player
flow, decide your S27 target, or fill in any field of the blueprint.

- question asked: ___
- answer given: ___
- accepted/rejected: ___
- why: ___

Do not paste whole files or ask AI to design your capstone.

## Git close

**ZIP path check:** Do this section only if your course folder is Git-managed (the Derived student repository path) or your class has already started the Git lesson. On the ZIP path before that lesson, skip it — see [Student Quick Start → Later: Git](../../student-quick-start.md#later-git-optional-teacher-managed).

Your blueprint is a change worth reviewing. Use status → diff → staged diff →
descriptive commit:

```console
git status --short
git diff
git add lessons/sessions/s26/student/capstone-blueprint.yaml
git diff --staged
git commit -m "Design my capstone blueprint"
```

Interpret `M`, `??`, and no output. Use identity recovery and Control-C
cancel/correct/retry. Stage only the blueprint; there is nothing else to stage
today.

## Support path

If you are stuck on a premise, the teacher can help you narrow one you already
have — a place you like, a thing you wish existed, one mechanic you enjoyed
building. The teacher may help you make a project smaller. The teacher does not
choose your premise or make your design decisions for you.
