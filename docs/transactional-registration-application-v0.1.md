# Transactional Registration Plan Application v0.1

> **Status:** Implemented local application layer. Class-world assembly,
> cross-package orchestration, publishing, approval, authentication, and online
> services remain deferred.

Transactional Registration Plan Application v0.1 is the controlled mutation
boundary after immutable Student API registration planning:

```text
validated Explorer Package
        ↓
declarative package loading
        ↓
immutable StudentAPIRegistrationPlan
        ↓
explicit target preflight
        ↓
staging and transactional commit
        ↓
Student API Character and Object instances
```

Application consumes only an in-memory `StudentAPIRegistrationPlan` and an
explicit caller-supplied target. It does not discover a world through global
state and does not repeat validation, loading, parsing, publication, approval,
or release assembly.

For multiple packages, the upstream
[Package-Set Preflight and Selection Model v0.1](package-set-preflight-v0.1.md)
checks exact package pins, cross-package identities, and aggregate Student API
cardinality without applying any plan. This transactional adapter still applies
only one `StudentAPIRegistrationPlan`. The higher-level
[Transactional Package-Set Application v0.1](transactional-package-set-application-v0.1.md)
reuses its validation, staging, and target-operation primitives inside one
package-aware transaction spanning the full set.

## Explicit target boundary

The public `StudentAPIRegistrationTarget` protocol exposes only the operations
the transaction requires:

- inspect whether a qualified registration ID already exists;
- inspect whether the character slot is occupied;
- inspect whether the world-object slot is occupied;
- add and remove one exact `Character`; and
- add and remove one exact `Object`.

Each target add or remove operation must itself be atomic for one entry: if the
operation raises, that entry must be unchanged. Removal must use both qualified
ID and object identity so rollback cannot remove pre-existing or replacement
state.

`StudentAPIWorldRegistrationTarget` is the concrete adapter for an existing
Student API `World`. It owns the qualified-ID mapping for that explicit target
and observes direct entities already present in the wrapped world when checking
cardinality. Direct pre-existing entities have no package registration identity
and are never removed by the adapter. Callers should retain one adapter as the
registration target for the lifetime of its qualified-ID state.

The adapter does not expose the wrapped world as part of the target contract.
The Student API `World` supplies a private identity-checked removal hook solely
for transaction rollback; no new student-facing `world.remove()` operation is
introduced.

## v0.1 cardinality

The implemented Student API v0.1 `World` supports:

- at most one `Character`; and
- at most one `Object`.

Application formalizes that existing behavior. Preflight rejects a character
when the target character slot is already occupied, a world object when its slot
is occupied, and a plan containing more than one entry of either kind. Existing
entities are never silently replaced. This slice does not invent
multiple-character or multiple-object runtime support.

Qualified registration IDs are unique within one explicit target. Applying the
same plan a second time to the same target is a preflight failure, not an
idempotent success and not an overwrite.

## Public API

```python
from explore import World
from explore.packages import (
    StudentAPIWorldRegistrationTarget,
    apply_student_api_registration_plan,
)

world = World("Package Preview")
target = StudentAPIWorldRegistrationTarget(world)

result = apply_student_api_registration_plan(plan, target)
if result.is_applied:
    for registration in result.applied:
        print(registration.qualified_id)
else:
    for issue in result.issues:
        print(f"{issue.code}: {issue.location}: {issue.message}")
```

The intentional public surface is:

- `apply_student_api_registration_plan`;
- `StudentAPIRegistrationTarget`;
- `StudentAPIWorldRegistrationTarget`;
- `RegistrationApplicationResult`;
- `RegistrationApplicationState`;
- `RegistrationApplicationIssue`;
- `RegistrationApplicationIssueCode`;
- `AppliedRegistration`; and
- `RegistrationType`.

All result and diagnostic models are frozen dataclasses. Collections exposed by
the result are tuples. Mutable runtime `Character` and `Object` instances remain
owned by the target and are not returned as applied metadata.

## Transaction phases

### 1. Input and target validation

The function requires a `StudentAPIRegistrationPlan` and an explicit target.
Missing or incompatible values produce structured diagnostics.

Target compatibility is checked before any Student API instance is constructed.
The target must implement the complete narrow protocol and return Boolean state
from its inspection methods.

### 2. Plan and target preflight

Preflight verifies:

- the plan has valid package provenance;
- the exact Student API version is supported;
- entries are a non-empty immutable tuple;
- every entry has the same provenance as the plan;
- contribution and qualified identities are internally consistent;
- no qualified identity is duplicated in the plan;
- no qualified identity already exists in the target;
- target cardinality will not be exceeded;
- every entry uses an explicitly supported registration type;
- names, coordinates, colors, and interaction messages remain constructor
  compatible; and
- optional image metadata remains a valid package-relative PNG reference.

All predictable issues are collected in deterministic order before mutation.
An invalid later entry therefore prevents construction and mutation of an
earlier valid entry.

### 3. Runtime instance staging

Only after preflight succeeds does the application layer construct Student API
instances. The current `Character` and `Object` constructors and interaction
message setters are pure configuration operations: they validate and store
ordinary Python values without engine launch, Pygame initialization, or asset
materialization.

If construction unexpectedly rejects a value, application returns
`INSTANCE_CONSTRUCTION_FAILED` and the target remains unchanged.

### 4. Commit

Staged entries are added in plan order. The target receives the qualified ID and
the compatible Student API instance. Successful applied metadata follows the
same order.

Application stops after the first target add failure. It never reports partial
successful metadata.

### 5. Reverse rollback

After a commit failure, successfully committed entries are removed in reverse
commit order. Rollback records the exact qualified ID and instance from this
transaction. It does not enumerate or remove pre-existing target state.

Rollback continues after an individual removal failure so every remaining
committed entry gets its deterministic removal attempt.

### 6. Result construction

`RegistrationApplicationState` has four values:

| State | Meaning |
|---|---|
| `NOT_APPLIED` | Input, preflight, or staging failed before target mutation. |
| `APPLIED` | Every planned entry committed successfully. |
| `ROLLED_BACK` | Commit failed and every earlier commit was removed. |
| `ROLLBACK_INCOMPLETE` | Commit failed and at least one earlier commit could not be removed. |

`RegistrationApplicationResult.unreverted_qualified_ids` identifies entries
whose removal failed, in reverse rollback-attempt order.
`target_may_be_partially_modified` is true only for
`ROLLBACK_INCOMPLETE`. The original add issue is retained before all rollback
issues.

## Student API mapping

### Character

`CharacterRegistrationSpec` maps directly to:

```python
Character(
    name=spec.name,
    x=spec.x,
    y=spec.y,
    color=spec.color,
)
```

No size, speed, behavior, image, or engine field is fabricated.

### World object

`WorldObjectRegistrationSpec` maps directly to:

```python
world_object = Object(
    name=spec.name,
    x=spec.x,
    y=spec.y,
    color=spec.color,
)
```

Present `when_near` and `when_interacted` values are passed to the existing
Student API string setters. They remain literal message text. Python-looking
text is never evaluated, compiled, imported, or converted to a callback.

### Asset metadata

An optional `PackageAssetReference` remains associated with
`AppliedRegistration`. Application validates its detached metadata but does not
open the path, decode the image, create a Pygame surface, or attach a runtime
asset to the Student API entity.

## Diagnostics and determinism

Issues contain a stable code, message, structural location, and optional
qualified and local contribution identities. They do not include raw exception
representations, memory addresses, or machine-specific paths.

Ordering is deterministic:

1. input issues;
2. target compatibility;
3. plan provenance and compatibility;
4. entries in plan order;
5. the first commit failure; and
6. rollback failures in reverse rollback-attempt order.

Given equal plan values and equivalent initial target state, preflight results,
commit ordering, rollback ordering, and applied metadata ordering are equal.

## Concurrency limitation

Application is atomic relative to its own preflight, staging, commit, and
rollback sequence. v0.1 introduces no global lock and does not claim
multi-threaded transaction safety. Callers must provide exclusive access to the
explicit target for the full application attempt. A future target contract may
add locking if concurrent assembly becomes a requirement.

## Safety and scope

Transactional application performs no:

- filesystem reads or package-directory inspection;
- YAML parsing;
- package loading or package validation;
- Python module loading from a package;
- `eval`, `exec`, or student-code execution;
- asset opening or media decoding;
- Pygame display, sound, renderer, scene, or event-loop initialization;
- network access;
- global registry mutation or hidden target lookup;
- package publication, approval, or authentication; or
- class-world or cross-package assembly.

The implemented pipeline status is:

- Explorer Package validation: implemented;
- declarative package loading: implemented;
- immutable registration planning: implemented;
- transactional application to one explicit target: implemented;
- multi-package package-set preflight: implemented;
- transactional package-set application: implemented;
- class-world assembly: not implemented;
- cross-package policy beyond current identity and cardinality checks: not
  implemented;
- publication, approval, authentication, registries, and online services: not
  implemented.

## Deferred work

- class-world orchestration using package-set application;
- cross-package namespace and collision policy;
- asset materialization and rendering integration;
- online approval, publishing, authentication, and registry services;
- target locking or another concurrency contract;
- persistent transaction and audit records;
- recovery after process termination;
- archive loading; and
- executable extension support and its required security design.
