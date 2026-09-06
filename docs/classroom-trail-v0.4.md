# Local Classroom Trail v0.4

> **Status:** Implemented additive local runtime contract. Student API and
> package-set v0.1 cardinality remain unchanged.

Classroom Trail v0.4 adds short, deterministic NPC conversations to v0.3. One
loaded character remains the explicitly selected movable player. Every other
loaded character remains a stationary NPC for that trail only; packages do not
declare player or NPC roles.

## Character conversation contract

A character may declare one ordered `conversation` containing exactly two or
three nonblank lines:

```yaml
name: "Forest Guide"
x: 430
y: 270
color: "green"
conversation:
  - "Welcome to the forest trail!"
  - "The lantern marks the safest path."
  - "Come back whenever you want to hear this again."
```

The existing optional nonblank `greeting` remains supported and behaves as a
one-line conversation. A declaration cannot contain both `greeting` and
`conversation`, avoiding ambiguous authored order. Omitting both leaves the NPC
visible but non-interactable.

## Advancement and session state

Each E press on the targeted NPC displays `Name: line` and advances that NPC's
position. Lines retain their declared order. After the final line, the next
interaction restarts at line one. Positions are independent per NPC, exist only
in the running scene, and are never written to a package or persistent store.

NPCs with conversations and world objects retain the unified v0.3 targeting
rule: smallest squared center distance, then lexicographically smallest
qualified ID. NPC interaction never changes `visited_qualified_ids`, progress,
or Trail completion. Object behavior remains unchanged.

## Deferred

Branching, choices, conditions, memory, quests, missions, persistence, teacher
controls, archive ingestion, multiplayer, authentication, deployment, and
Phase E integration remain out of scope.
