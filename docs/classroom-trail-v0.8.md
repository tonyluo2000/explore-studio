# Local Classroom Trail v0.8

> **Status:** Implemented additive local runtime contract. Student API and
> package-set v0.1 cardinality remain unchanged.

Classroom Trail v0.8 preserves existing Trail behavior while adding one fixed
Boolean `and` response for a character and exactly two same-package toggle
objects. Packages without this metadata behave unchanged.

## Two-toggle response declaration

```yaml
respond_to_two_toggles:
  object_ids: ["first-switch", "second-switch"]
  when_not_all_on: "The secret is still locked."
  when_all_on: "The secret is revealed!"
```

The mapping contains exactly these three required keys. `object_ids` is an
ordered list of exactly two distinct unqualified contribution IDs. Both
responses are nonblank. The metadata cannot coexist with `greeting`,
`conversation`, or `respond_to_toggle`. Unknown, missing, malformed, qualified,
or duplicate values fail closed.

Each ID must resolve exactly once within the character's package to a world
object with valid `toggle` metadata. Missing, cross-package, non-object, and
ordinary-object references fail closed at every boundary. Metadata remains
immutable and lossless through loading, registration, package-set planning,
configuration validation, Trail planning, and runtime projection.

## Runtime and evidence

On a successful targeted interaction, the runtime evaluates only:

```text
first_toggle_is_on and second_toggle_is_on
```

True displays only `when_all_on`; false displays only `when_not_all_on`.
Normal spoken-NPC evidence is recorded. The interaction does not mutate toggle
state, object visits, counters, targeting/order, or Mission 08 branch evidence.

The scene separately retains a session-only immutable set of
`(npc_qualified_id, all_on)` evidence. Repeated branch displays are idempotent,
and evidence is monotonic.

## Mission completion

`ALL_TWO_TOGGLE_BRANCHES_DISPLAYED` completes only when fallback and success
evidence exist for every two-toggle NPC. Ordinary characters are excluded. A
Trail with no qualifying NPC remains incomplete. Other completion rules and
ordinary object progress remain independent.

## Compatibility and deferred work

Mission 07 toggles, Mission 08 conditionals, Mission 09 counters, greetings,
conversations, targeting, ordering, and progress behavior remain unchanged.
The canonical Trail planner emits exact version `0.8`; incompatible versions
fail closed.

Mission 11+, `or`, `not`, nested or arbitrary expressions, cross-package
references, generic actions or state machines, scripting, sequencing,
persistence, rewards, teacher controls, deployment, authentication, and Phase E
integration remain deferred.
