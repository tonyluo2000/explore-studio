# Local Classroom Trail v0.7

> **Status:** Implemented additive local runtime contract. Student API and
> package-set v0.1 cardinality remain unchanged.

Classroom Trail v0.7 preserves toggle and conditional behavior while adding a
bounded declarative interaction counter. Packages without counter metadata
retain their existing appearance, feedback, interaction, targeting, ordering,
and progress behavior.

## Counter declaration

A world object becomes a counter object when it declares:

```yaml
name: "Power Core"
when_interacted: "Pressed."
counter:
  goal: 3
  when_goal_reached: "The core is fully powered!"
```

`counter` contains exactly `goal` and `when_goal_reached`; both are required.
`goal` is a non-Boolean integer from 2 through 5. The message must be nonblank.
Unknown keys, missing keys, invalid types, and out-of-range goals fail closed.

Counter metadata is independent from appearance, ordinary interaction
messages, and toggle metadata. The loader, registration adapter, package-set
planner, configuration boundary, Trail planner, and runtime retain typed
immutable metadata and defensively validate their inputs.

## Session state and feedback

The scene initializes an immutable session-only mapping from every counter
object's qualified ID to zero. Each successful targeted object interaction
increments only that object's count exactly once. Counts continue beyond their
goals; there is no decrement, reset, or cap.

The interaction still records the ordinary object visit and independently
performs the existing toggle behavior when present. Counter feedback preserves
the existing `when_interacted` response (or its default), appends
`Count: current / goal.`, and appends `when_goal_reached` whenever the current
count is at least the goal. Objects without `counter` retain their existing
feedback exactly.

## Mission completion

`ALL_COUNTER_GOALS_REACHED` completes only when every counter object's current
count is at least its authored goal. Ordinary objects are excluded. A Trail
with no counter objects remains incomplete. This rule is independent from
ordinary visited-object progress.

## Compatibility and deferred work

Mission 07 toggle and Mission 08 conditional behavior remain unchanged. The
canonical Trail planner emits exact contract version `0.7`; incompatible
versions fail closed.

Mission 10, decrement/reset, arithmetic expressions, generic actions or state
machines, scripting, sequencing, persistence, rewards, teacher controls,
deployment, authentication, and Phase E integration remain deferred.
