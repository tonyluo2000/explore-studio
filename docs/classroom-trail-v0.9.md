# Local Classroom Trail v0.9

> **Status:** Implemented additive local runtime contract. Student API and
> package-set v0.1 cardinality remain unchanged.

Classroom Trail v0.9 preserves v0.8 behavior and adds one fixed, declarative
Boolean `or` response for a character and exactly two same-package toggles.

## Either-toggle response

```yaml
respond_to_either_toggle:
  object_ids: ["first-switch", "second-switch"]
  when_both_off: "The door is locked."
  when_either_on: "The door is open!"
```

The mapping contains exactly these required keys. `object_ids` is an ordered
list of exactly two distinct, unqualified contribution IDs. Both responses are
nonblank. This metadata cannot coexist with `greeting`, `conversation`,
`respond_to_toggle`, or `respond_to_two_toggles`.

Each ID must resolve exactly once within the character's package to a world
object with valid toggle metadata. Missing, duplicate, qualified,
cross-package, character, and ordinary-object references fail closed at every
boundary. Metadata remains immutable and lossless through loading,
registration, package-set planning, configuration validation, Trail planning,
and runtime projection.

## Runtime and evidence

The runtime evaluates only:

```text
first_toggle_is_on or second_toggle_is_on
```

Both off selects `when_both_off`; either or both on selects `when_either_on`.
NPC interaction does not mutate toggles, visits, counters, target selection,
ordering, or earlier conditional evidence.

The scene records session-only immutable `(npc_qualified_id, first_on,
second_on)` cases monotonically. Repeated displays are idempotent.
`ALL_EITHER_TOGGLE_CASES_DISPLAYED` requires both off, first only, and second
only for every either-toggle NPC. Both-on evidence is retained but is not a
fourth completion requirement. A Trail with no qualifying NPC remains
incomplete.

## Compatibility and deferred work

Mission 10 Boolean `and` and all v0.8 behavior remain unchanged. The canonical
Trail planner emits exact version `0.9`; incompatible versions fail closed.

Mission 12+, more than two operands, `not`, nested or arbitrary expressions,
generic actions or state machines, scripting, persistence, sequencing,
rewards, teacher controls, deployment, authentication, and Phase E integration
remain deferred.
