# Local Classroom Trail v0.10

> **Status:** Implemented additive local runtime contract.

Classroom Trail v0.10 preserves v0.9 behavior and adds one fixed declarative
counter comparison for Mission 13. A character may retain:

```yaml
respond_to_counter:
  object_id: "power-core"
  when_below_goal: "It needs more power."
  when_at_or_above_goal: "The power level is ready!"
```

The mapping has exactly those three required keys. Responses are nonblank and
`object_id` is one unqualified contribution ID resolving exactly once to a
same-package world object with valid `counter` metadata. It is mutually
exclusive with greeting, conversation, `respond_to_toggle`,
`respond_to_two_toggles`, and `respond_to_either_toggle`. Missing, duplicate,
qualified, cross-package, character, ordinary-object, and non-counter targets
fail closed throughout loading, registration, package-set planning,
configuration, and runtime construction.

Runtime reads the current session count and the referenced object's authored
counter goal, then evaluates exactly `count >= goal`. False displays only
`when_below_goal`; True displays only `when_at_or_above_goal`. NPC interaction
does not increment or otherwise change the counter, object visits, toggles,
targeting, conversations, or earlier conditional evidence.

The separate session-only immutable evidence set contains
`(npc_qualified_id, at_or_above_goal)` pairs. Evidence is monotonic and repeated
displays are idempotent. `ALL_COUNTER_COMPARISON_BRANCHES_DISPLAYED` is the one
new completion rule: it requires both False and True for every qualifying NPC,
and zero qualifying NPCs is incomplete.

The Trail planner emits exact version `0.10`; incompatible versions fail
closed. Missions 01–12 and all v0.9 semantics remain unchanged.

## Deferred

Mission 14+, editable thresholds, arithmetic or ranges, decrement/reset,
general predicates or actions, cross-package references, scripting,
persistence, sequencing, rewards, teacher controls, deployment,
authentication, and Phase E integration remain out of scope.
