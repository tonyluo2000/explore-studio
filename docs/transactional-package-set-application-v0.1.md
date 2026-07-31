# Transactional Package-Set Application v0.1

> **Status:** Implemented explicit-target package-set transaction. Class-world
> configuration, assembly, release artifacts, publication, approval,
> authentication, registries, and online services remain deferred.

Transactional Package-Set Application v0.1 is the controlled mutation boundary
after package-set preflight:

```text
immutable PackageSetPlan
        ↓
package-set structure and target preflight
        ↓
stage every Student API runtime instance
        ↓
commit in package order, then plan-entry order
        ↓
global reverse rollback on the first add failure
```

Application consumes one successful in-memory `PackageSetPlan` and one explicit
caller-supplied `StudentAPIRegistrationTarget`. It does not accept manifests,
package directories, selections, loader results, or failed planning results. It
does not repeat package validation, loading, single-package planning, or
package-set planning.

## Explicit target boundary

```python
from explore import World
from explore.packages import (
    StudentAPIWorldRegistrationTarget,
    apply_package_set_plan,
)

world = World("Package Set Preview")
target = StudentAPIWorldRegistrationTarget(world)
result = apply_package_set_plan(package_set_plan, target)
```

The caller owns the target and must provide exclusive access for the complete
attempt. No active world, default target, global identity registry, or hidden
target lookup exists.

`StudentAPIWorldRegistrationTarget` retains qualified identities in the adapter.
Callers should therefore keep one adapter per `World` for the lifetime of that
world's package registrations. Package-set application uses the supplied target
instance throughout and never constructs another wrapper.

## Planning and application are separate

[Package-Set Preflight and Selection Model v0.1](package-set-preflight-v0.1.md)
combines ordered exact package selections and returns an immutable
`PackageSetPlan` only when package, provenance, identity, compatibility, and
aggregate cardinality checks pass.

Package-set application defensively revalidates that public value, but does not
rebuild it or choose among conflicts. Invalid or manually inconsistent plans
return `NOT_APPLIED`; no package or entry is silently omitted.

## Public API

```python
from explore.packages import apply_package_set_plan

result = apply_package_set_plan(package_set_plan, target)
if result.is_applied:
    for registration in result.applied:
        print(
            registration.package_id,
            registration.package_version,
            registration.qualified_id,
        )
else:
    for issue in result.issues:
        print(issue.code, issue.location, issue.package_id)
```

The intentional package-set application surface is:

- `apply_package_set_plan`;
- `PackageSetApplicationResult`;
- `PackageSetApplicationIssue`;
- `PackageSetApplicationIssueCode`; and
- `AppliedPackageSetRegistration`.

The existing `RegistrationApplicationState` and `RegistrationType` models are
reused because package-set transactions have the same state and registration
kind semantics as single-plan transactions.

All public result models are frozen dataclasses. Collections are tuples.
Mutable runtime `Character` and `Object` instances remain owned by the target
and are never returned as public metadata.

## Complete preflight

Before runtime construction or target mutation, application checks:

- the input is a `PackageSetPlan`;
- the target satisfies the complete registration-target protocol;
- target inspection methods return deterministic Boolean state;
- the package-set Student API version is exactly `0.1`;
- package and flattened-entry collections are non-empty tuples;
- every selected package agrees with its exact ID, version, provenance, and
  nested registration plan;
- nested entries flatten exactly to `PackageSetPlan.entries`;
- flattened count and order match package order and nested plan-entry order;
- every nested plan and entry retains valid provenance and qualified identity;
- qualified identities are unique across the complete set;
- entry types, detached values, and optional image metadata remain valid;
- aggregate cardinality remains at most one character and one world object;
- no selected qualified identity already exists in the target; and
- the target has capacity for the aggregate set.

All predictable issues are returned before mutation. Invalid later packages do
not allow valid earlier packages to apply partially.

## Deterministic ordering

Commit order is exactly:

1. `PackageSetPlan.packages` order; then
2. each selected package's `registration_plan.entries` order.

The nested sequence must exactly equal `PackageSetPlan.entries`. Application
does not sort by package ID, version, registration type, or qualified identity.

Applied metadata follows commit order. Rollback follows the exact reverse of
the global successful-commit sequence, not merely reverse package order.

## Runtime staging

After complete preflight, every Student API instance is constructed and retained
in memory before the first target add. A construction failure in a later package
returns `NOT_APPLIED`, includes package and entry location, and leaves the target
unchanged even if earlier entries staged successfully.

Character and world-object mapping is identical to the single-plan application
layer. Interaction strings remain literal text. Optional asset references
remain package-relative metadata; no asset is opened, decoded, or attached to a
runtime object.

## Commit and cross-package rollback

Staged entries are added sequentially. The transaction records an entry only
after its target add succeeds. The first add failure stops commit, preserves the
original failure diagnostic, and begins rollback.

Rollback:

- spans every package with a successful earlier commit;
- runs in global reverse commit order;
- removes only the exact qualified ID and runtime instance added by this
  transaction;
- never enumerates, replaces, or removes pre-existing target state; and
- continues remaining removal attempts after one removal failure.

The target contract requires each individual add or remove operation to be
atomic for its entry. A failed add is never treated as committed and is not
removed.

## Result states

| State | Meaning |
|---|---|
| `NOT_APPLIED` | Input, target inspection, structure preflight, entry preflight, or staging failed before mutation. |
| `APPLIED` | Every selected entry remains committed. |
| `ROLLED_BACK` | Commit began, a later add failed, and all successful earlier adds were removed. |
| `ROLLBACK_INCOMPLETE` | Commit began and at least one successful earlier add could not be removed. |

`applied` is populated only for `APPLIED`. It is empty after either rollback
state, so partial work is never represented as success.

For `ROLLBACK_INCOMPLETE`, `unreverted` contains immutable package-aware metadata
for each failed removal in reverse rollback-attempt order. Each item identifies
the package ID and version, package and entry positions, qualified and local
identities, provenance, registration type, and optional asset metadata.

## Package-aware diagnostics and metadata

Issues contain a stable code, structural location, and optional:

- package ID;
- package index;
- entry index;
- qualified identity; and
- local contribution identity.

Messages never expose raw exception text, memory addresses, absolute paths, or
runtime object representations. The original add failure precedes rollback
issues, which follow reverse rollback-attempt order.

Successful `AppliedPackageSetRegistration` values preserve:

- selected package ID and exact version;
- package position and nested entry position;
- qualified and local contribution identities;
- package provenance;
- registration type; and
- optional package-relative asset metadata.

## Target cardinality and idempotency

Student API v0.1 supports at most one character and one world object. The
package-set plan and current target must both satisfy those limits. Existing
entities are never replaced.

Applying a valid package set once to an empty compatible target succeeds.
Applying the same plan again to that target fails preflight because its
qualified identities and target slots are occupied; the second attempt performs
no mutation. The same immutable plan may apply to a different empty target.

## Atomicity and concurrency limits

The transaction is sequential and rollback is best-effort. Callers must provide
exclusive target access. v0.1 introduces no global lock and makes no thread-safe
or database-grade atomicity claim.

Target changes after inspection can appear as an add failure and trigger
rollback. Process termination during commit cannot be recovered because no
durable transaction log exists.

## Safety boundary

Package-set application performs no:

- filesystem reads or directory inspection;
- YAML parsing;
- package validation or loading;
- single-package or package-set planning;
- package data import or student-code execution;
- interaction-string evaluation or compilation;
- asset opening, decoding, or materialization;
- Pygame, renderer, scene, lifecycle, or event-loop initialization;
- network access;
- global target or registry mutation;
- package publication, approval, authentication, or authorization; or
- class-world configuration, assembly, manifest, or artifact generation.

## Implementation status

- Explorer Package validation: implemented;
- declarative package loading: implemented;
- immutable single-package registration planning: implemented;
- transactional single-plan application: implemented;
- multi-package package-set preflight: implemented;
- transactional package-set application: implemented;
- class-world configuration and assembly: not implemented;
- release artifacts and reproducible release manifests: not implemented;
- publication, approval, authentication, registries, and online services: not
  implemented.

## Deferred work

- class-world configuration and assembly;
- reproducible release manifests and artifact hashing;
- package approval, publication, authentication, and registry services;
- persistent transaction and audit records;
- target locking or another concurrency contract;
- process-crash recovery;
- cross-target application;
- asset materialization and rendering integration;
- archive loading and dependency resolution; and
- executable extension isolation.
