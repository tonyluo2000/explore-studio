# Student API Registration Adapter v0.1

> **Status:** Implemented local planning layer. Transactional application is
> implemented as a separate explicit-target boundary.

The Student API Registration Adapter converts one successfully loaded
`LoadedExplorerPackage` into a deterministic, immutable description of what a
future trusted application adapter could register. It is a compatibility and
mapping boundary, not a world mutation API.

## Boundary and flow

```text
validated package directory
        ↓
Local Explorer Package Loader
        ↓
immutable LoadedExplorerPackage
        ↓
Student API Registration Adapter
        ↓
immutable StudentAPIRegistrationPlan
        ↓
explicit transactional application
```

The primary API accepts only an in-memory `LoadedExplorerPackage`. It does not
accept a path, reread `manifest.yaml`, parse contribution YAML, inspect the
package repository, resolve dependencies, or access the network. Validation and
declarative loading must finish before registration planning begins.

Planning is deliberately separate from application. Building a plan does not:

- create or mutate an `explore.World`;
- instantiate Student API `Character` or `Object` runtime models;
- add an entity to a scene or engine collection;
- register a callback;
- materialize an image or audio asset;
- initialize Pygame, a renderer, or an event loop; or
- publish, approve, or assemble packages.

The separate
[Transactional Registration Plan Application v0.1](transactional-registration-application-v0.1.md)
consumes a completed plan and an explicitly supplied compatible target. It does
not change the planning contract or make planning itself stateful.

## Public API

```python
from explore.packages import (
    build_student_api_registration_plan,
    load_explorer_package,
)

load_result = load_explorer_package(
    "examples/explorer-packages/nova-character"
)
assert load_result.package is not None

result = build_student_api_registration_plan(load_result.package)
if result.is_planned:
    assert result.plan is not None
    for entry in result.plan.entries:
        print(entry.qualified_id)
else:
    for issue in result.issues:
        print(f"{issue.code}: {issue.location}: {issue.message}")
```

`build_student_api_registration_plan(loaded_package)` is the primary pure
adapter. Passing a path, `PackageLoadResult`, or another Python type violates
the function contract and raises `TypeError`.

`plan_loaded_explorer_package(load_result)` is a convenience boundary for
callers that already hold a `PackageLoadResult`. It requires
`load_result.is_loaded`, never repairs or partially consumes a failed load, and
retains the original validation and loading diagnostics in
`RegistrationPlanResult.loader_diagnostics`.

The public immutable value objects are:

- `RegistrationPlanResult`;
- `StudentAPIRegistrationPlan`;
- `CharacterRegistration` and `CharacterRegistrationSpec`;
- `WorldObjectRegistration` and `WorldObjectRegistrationSpec`; and
- `RegistrationPlanIssue` with `RegistrationPlanIssueCode`.

`StudentAPIRegistrationEntry` is the explicit character-or-world-object union.
All public dataclasses are frozen, and all exposed diagnostic and entry
collections are tuples.

## Character mapping

| Loaded character field | Registration field |
|---|---|
| `qualified_id` | `CharacterRegistration.qualified_id` |
| `contribution_id` | `CharacterRegistration.contribution_id` |
| `provenance` | `CharacterRegistration.provenance` |
| `name` | `character.name` |
| `x` | `character.x` |
| `y` | `character.y` |
| `color` | `character.color` |
| optional `image` | `CharacterRegistration.asset_reference` |

The detached specification matches the Student API v0.1 character
configuration. Engine-owned size, movement speed, health, inventory, dialogue,
animation, AI, and callbacks are not invented.

## World-object mapping

| Loaded world-object field | Registration field |
|---|---|
| `qualified_id` | `WorldObjectRegistration.qualified_id` |
| `contribution_id` | `WorldObjectRegistration.contribution_id` |
| `provenance` | `WorldObjectRegistration.provenance` |
| `name` | `world_object.name` |
| `x` | `world_object.x` |
| `y` | `world_object.y` |
| `color` | `world_object.color` |
| optional `image` | `WorldObjectRegistration.asset_reference` |
| optional `when_near` | `world_object.when_near` |
| optional `when_interacted` | `world_object.when_interacted` |

Interaction messages remain inert strings. Python-looking text is not evaluated,
imported, converted to a callable, or installed as a callback.

## Assets

An optional image remains the original immutable `PackageAssetReference`,
retaining its asset ID, type, and validator-approved package-relative path. The
adapter verifies that a retained appearance reference is still an image and has
non-empty identity. It does not open, decode, revalidate, canonicalize, or
convert the asset to a machine-specific path.

## Provenance and qualified identity

Every plan retains its containing `PackageProvenance`: package ID, package
version, and exact Student API version. Every entry retains that provenance, its
manifest-local contribution ID, and its loaded
`package-id:contribution-id` qualified identity.

The adapter checks that:

- the package targets Student API `0.1`;
- package metadata, compatibility, and provenance agree;
- contribution provenance matches the package;
- local identifiers remain valid;
- qualified identities match package provenance and local ID; and
- no qualified identity appears twice in one plan.

There is no global registry. The same local contribution ID in two independent
package plans is not a conflict. Cross-package collision policy belongs to a
future class-world package-set planner.

## Atomicity and deterministic diagnostics

Planning is all-or-nothing. The adapter may accumulate independent issues to
make one run useful, but any issue produces `plan=None`; successfully checked
neighbors are never returned as a partial plan.

Diagnostics are immutable and use structural locations such as
`contributions[1].color`, never source-machine absolute paths. Ordering is:

1. package and provenance compatibility;
2. contributions in loaded order;
3. contribution identity and provenance;
4. fields in character or world-object contract order; and
5. the current contribution's duplicate qualified-identity check.

Repeated planning of the same immutable input produces equality-comparable
identical results.

## Implementation status and deferred work

Implemented:

- deterministic Explorer Package validation;
- local declarative package loading;
- pure Student API registration planning; and
- explicit-target transactional registration application.

Not implemented:

- engine scene registration or asset materialization;
- planning across a set of packages or cross-package collision resolution;
- class-world assembly;
- authentication, online approval, publication, or registries;
- archive loading; or
- executable student extensions.

Successful planning is not publication, teacher approval, class-world inclusion,
or a released world.
