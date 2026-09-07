# Local Classroom Trail v0.11

> **Status:** Implemented additive local runtime contract.

Classroom Trail v0.11 preserves v0.10 behavior and adds one fixed three-object
sequence for Mission 15. A character may declare:

```yaml
respond_to_sequence:
  object_ids:
    - "first-object"
    - "second-object"
    - "third-object"
  when_incomplete: "The sequence is still locked."
  when_complete: "The secret is revealed!"
```

The mapping has exactly those three keys. `object_ids` is an ordered list of
exactly three distinct, unqualified lower-kebab-case contribution IDs. Each ID
resolves exactly once to a same-package world object. Ordinary, toggle, and
counter objects qualify. The response is mutually exclusive with greeting,
conversation, and every other `respond_to_*` field. Invalid structures and
missing, duplicate, qualified, cross-package, character, or unknown references
fail closed through loading, registration, package-set planning,
configuration, and runtime construction.

## Fixed runtime behavior

The scene owns an immutable session mapping from each qualifying NPC ID to a
matched-prefix length from 0 through 3. A successful targeted world-object
interaction updates every incomplete sequence independently:

- the expected next member advances progress by exactly one;
- another member of that triple resets progress to zero and is not reconsidered
  as the first step;
- an object outside the triple leaves progress unchanged; and
- progress 3 never regresses.

Existing visit, message, toggle, and counter effects still execute normally.
Talking to the NPC does not update sequence progress. It displays only
`when_incomplete` at progress 0–2 and only `when_complete` at progress 3.

Completed NPC IDs are retained in a separate immutable, monotonic session-only
set. Repeated interactions are idempotent. The one new completion rule,
`ALL_THREE_OBJECT_SEQUENCES_COMPLETED`, requires every qualifying NPC in the
scene to be complete; zero qualifying NPCs remains incomplete.

The Trail planner emits exact version `0.11`; incompatible versions fail
closed. Explorer Package remains v0.2, Student API remains v0.1, and Missions
01–14 retain their prior behavior.

## Deferred

Mission 16 adds content only and reuses the existing `ALL_OBJECTS_VISITED`
behavior. Mission 17+, variable-length or branching sequences, generalized
events, actions or state machines, loops, timers, persistence, rewards,
inventory, teacher controls, deployment, authentication, and Phase E
integration remain out of scope.
