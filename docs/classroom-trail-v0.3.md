# Local Classroom Trail v0.3

> **Status:** Implemented additive local runtime contract. Student API and
> package-set v0.1 cardinality remain unchanged.

Classroom Trail v0.3 adds classmate characters to the existing object trail.
One loaded character is explicitly selected as the movable player. Every other
loaded character is a stationary NPC for that trail only; packages do not
declare player or NPC roles.

## Contract boundary

`build_classroom_trail_plan()` and `plan_local_classroom_trail()` accept a
`player_qualified_id`. It must identify exactly one loaded character by its
`package-id:contribution-id` identity. All remaining characters are retained as
NPCs in qualified-ID order. Existing world objects remain required and retain
their v0.2 behavior.

Character declarations may add one optional nonblank `greeting` string:

```yaml
name: "Nova"
x: 430
y: 270
color: "gold"
greeting: "Welcome to our classroom world!"
```

Omitting `greeting` is backward compatible. A character without a greeting is
still rendered when contextualized as an NPC, but is not an interactable target
and cannot mask a nearby object interaction.

## Targeting and session state

World objects and NPCs with greetings share one deterministic interaction
targeting rule: choose the in-range entity with the smallest squared center
distance, then break an equal-distance tie by lexicographically smallest
qualified ID. Pressing E on an NPC displays `Name: greeting`.

Only world-object interactions update `visited_qualified_ids`. `Visited N / total`
and `Trail complete!` continue to count the required world objects only, and
remain process-local and idempotent.

## Local use

```console
explore-package trail \
  examples/explorer-packages/nova-character \
  examples/explorer-packages/forest-guide \
  examples/explorer-packages/crystal-lantern \
  examples/explorer-packages/river-fountain \
  --player "nova-character:nova" \
  --name "Example Classroom Trail"
```

The trail continues to parse only validated declarative YAML and never imports
or executes package Python.

## Deferred

Dialogue trees, choices, conditions, memory, quests, persistence, mission
progression, teacher controls, archive ingestion, multiplayer, authentication,
deployment, and Phase E integration remain out of scope.
