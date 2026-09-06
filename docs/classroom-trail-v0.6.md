# Local Classroom Trail v0.6

> **Status:** Implemented additive local runtime contract. Student API and
> package-set v0.1 cardinality remain unchanged.

Classroom Trail v0.6 preserves the v0.5 toggle contract and adds one fixed,
declarative if/else response for an NPC. Packages without conditional metadata
retain their existing appearance, dialogue, interaction, targeting, ordering,
and progress behavior.

## Conditional declaration

A character may respond to one toggle object from the same package:

```yaml
name: "Portal Guide"
respond_to_toggle:
  object_id: "magic-switch"
  when_off: "The portal is sleeping."
  when_on: "The portal is glowing!"
```

`respond_to_toggle` contains exactly the three required keys shown above.
`object_id` is one unqualified package-local contribution ID. Both responses
must be nonblank. Conditional metadata cannot coexist with `greeting` or
`conversation`; unknown fields and malformed values fail closed.

The reference must resolve exactly once in the same package to a world object
with valid `toggle` metadata. Missing, duplicate, character, ordinary-object,
qualified, and cross-package references are rejected. The loader,
registration adapter, package-set planner, configuration boundary, Trail
planner, and runtime all retain typed immutable metadata and defensively
validate their inputs.

## Runtime and evidence

On a successful targeted interaction with a conditional NPC, the runtime reads
the referenced object's existing session-only current-on set. Absence selects
`when_off`; presence selects `when_on`. Exactly one response is displayed. The
NPC interaction does not toggle or mutate the object and does not alter
targeting or qualified-ID order.

Displayed branches are recorded monotonically as `(npc_qualified_id, is_on)`
pairs in session-only immutable evidence. Repeated displays are idempotent.
`ALL_CONDITIONAL_BRANCHES_DISPLAYED` completes after both pairs exist for every
conditional NPC. Ordinary greeting/conversation NPCs are excluded, and zero
conditional NPCs remains incomplete.

## Compatibility and deferred work

Mission 07 toggle state, rendering, changed evidence, and visit behavior remain
unchanged. Existing characters and packages without `respond_to_toggle` remain
unchanged. The canonical Trail planner emits exact contract version `0.6`, and
incompatible versions fail closed.

Nested conditions, expressions, cross-package references, generic actions or
state machines, scripting, sequencing, persistence, rewards, teacher controls,
deployment, authentication, and Phase E integration remain deferred.
