# Local Classroom Trail v0.2

> **Status:** Implemented additive local runtime contract. Explorer Package,
> Student API, and package-set v0.1 behavior remain unchanged.

Classroom Trail turns multiple independently owned, declarative Explorer
Packages into one local activity: exactly one player explores multiple
package-sourced world objects, reads their authored messages, and visits them
all.

## Contract boundary

`build_package_set_plan()` remains the v0.1 contract and still accepts at most
one character and one world object. `build_classroom_trail_plan()` is the
explicit v0.2 cardinality boundary. It validates every selection independently
through v0.1, then accepts exactly one aggregate character and one or more
aggregate world objects.

Packages and objects are retained by qualified identity. Canonical plan and
render order use package ID and qualified object ID respectively. The runtime
selects the in-range object with the smallest squared center distance; equal
distances are resolved by lexicographically smallest qualified ID.

## Session state and UI

The runtime retains an immutable `visited_qualified_ids` set for the current
process only. A valid E-key interaction adds the selected object's qualified ID.
Repeated interaction is idempotent. The UI always displays
`Visited N / total` and displays `Trail complete!` when every object has been
visited. Existing `when_near` and `when_interacted` messages are used unchanged,
including their established defaults when omitted.

## Local use

Validate and export each student package independently as usual. The local
runtime deliberately consumes the corresponding unpacked package roots because
safe archive ingestion remains a separate boundary:

```console
explore-package export student-a/explorer-package \
  --output dist/student-a-1.0.0.explorer-package.zip
explore-package export student-b/explorer-package \
  --output dist/student-b-1.0.0.explorer-package.zip

explore-package trail \
  player/explorer-package \
  student-a/explorer-package \
  student-b/explorer-package \
  --name "Our Classroom Trail"
```

The trail command validates and safely parses only declarative YAML through the
existing loader. It never imports or executes package Python.

## Deferred

Persistence, archive ingestion, multiple players, NPC dialogue, quests,
arbitrary triggers, cross-package mutation, multiplayer, authentication,
deployment, and Phase E integration remain out of scope.
